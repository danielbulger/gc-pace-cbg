import datetime as dt
import math
from typing import List, Dict, Any, Tuple

from cbg import config
from cbg.patients import Patient
from enum import Enum

_day_names = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
_time_slot_interval = None

# For determining patient preferences, define what the midday day-part is here.
_midday_start_time = dt.time(hour=10, minute=0, second=0)
_midday_end_time = dt.time(hour=11, minute=59, second=59)


def _get_time_slot_interval():
    """
    Gets the amount of minutes that each time-slot should run for.
    :return: The time-slot duration.
    """
    global _time_slot_interval
    if not _time_slot_interval:
        _time_slot_interval = config.get_int('SCHEDULE', 'TimeslotInterval')
    return _time_slot_interval


class DayPart(Enum):
    MORNING = 1
    MIDDAY = 2
    AFTERNOON = 3


class LocationSchedule:

    @staticmethod
    def get_time_slot_day_part(time_slot) -> DayPart:
        if time_slot['slot'] < _midday_start_time:
            return DayPart.MORNING
        if time_slot['slot'] > _midday_end_time:
            return DayPart.AFTERNOON
        return DayPart.MIDDAY

    @staticmethod
    def _get_required_slots(patient: Patient) -> int:
        return math.ceil(patient['estimated_time'] / _get_time_slot_interval())

    @staticmethod
    def _get_time_slots(open_str: str, close_str: str) -> List[Dict[str, Any]]:
        if open_str is None or close_str is None:
            return []

        minutes = LocationSchedule._get_total_minutes_open(open_str, close_str)
        num_slots = math.ceil(minutes / _get_time_slot_interval())

        open_time = dt.datetime.strptime(open_str, "%H:%M")

        slots = []
        current_time = open_time
        for x in range(num_slots):
            slots.append({
                'slot': current_time.time(),
                'patient': None
            })
            current_time = current_time + dt.timedelta(minutes=_get_time_slot_interval())

        return slots

    @staticmethod
    def _get_total_minutes_open(open_str: str, close_str: str) -> int:
        """
        Gets the number of minutes between the closing and opening time.
        :param open_str: The opening time formatted as HH:MM in 24 hour time.
        :param close_str: The closing time formatted as HH:MM in 24 hour time.
        :return: The number of minutes between.
        """
        if open_str is None or close_str is None:
            return 0

        close_time = dt.datetime.strptime(close_str, "%H:%M")
        open_time = dt.datetime.strptime(open_str, "%H:%M")

        difference = close_time - open_time

        minutes = int(difference.total_seconds() / 60)

        assert minutes >= 0

        return minutes

    def __init__(self, location_id: int, day: int, open_time: str, close_time: str):
        """
        Represents a single daily schedule for a machine.
        :param location_id: The id of the location that this schedule is for.
        :param day: The day of the week identifier for this schedule.
        :param open_time: The time of the day formatted as HH:MM in 24 hour time that the location schedule opens.
        :param close_time: The time of the day formatted as HH:MM in 24 hour time that the location schedule closes.
        """
        self.location_id = location_id
        self.day = day
        self.open_time = open_time
        self.close_time = close_time

        self.time_slots = self._get_time_slots(open_time, close_time)
        self.patients = []

    def get_percent_assigned(self):
        """
        Calculates how much of this schedule has already been allocated.
        :return: A percentage (between 0 and 1) that has been allocated.
        """
        total = len(self.time_slots)

        if total == 0:
            return 1

        assigned = 0

        for time_slot in self.time_slots:
            if time_slot['patient'] is not None:
                assigned += 1

        return assigned / total

    def reorder_time_slots(self, new_patients):
        """
        Updates the existing time slots and patients with the ones given.
        :param new_patients: The patients (sorted by appointment time in ascending order) to update with.
        """
        self.patients = new_patients

        # Clear all the patients from the current time slots.
        for slot in self.time_slots:
            slot['patient'] = None

        last_slot = 0

        # Reassign the time slots here.
        for patient in self.patients:
            required_slots = self._get_required_slots(patient)

            for x in range(required_slots):
                self.time_slots[last_slot]['patient'] = patient
                last_slot += 1

    def get_time_slots(self) -> List[Dict[str, Any]]:
        """
        Gets the time slots for this Schedule.
        :return:
        """
        return self.time_slots

    def get_open_time(self) -> str:
        """
        Gets the time that this Schedule opens at.
        :return: The time formatted as HH:MM.
        """
        return self.open_time

    def get_close_time(self) -> str:
        """
        Gets the time that this Schedule closes at.
        :return: The time formatted as HH:MM.
        """
        return self.close_time

    def schedule_time_slot(self, patient: Patient, time_slot):
        """
        Gets a patient into the given time slot.
        :param patient: The patient to schedule.
        :param time_slot: The time-slot to schedule into.
        """
        self.schedule(patient, self.time_slots.index(time_slot))

    def schedule(self, patient: Patient, index: int) -> None:
        """
        Schedules the given patient to this schedule.
        :param patient: The patient to schedule.
        :param index: The starting time-slot to schedule the Patient into.
        """

        self.patients.append(patient)
        slots_required = self._get_required_slots(patient)

        for x in range(slots_required):
            self.time_slots[index + x]['patient'] = patient

    def _look_forward_time_slots(self, num_slots: int, start_index: int) -> bool:
        """
        Looks ahead `num_slots` and checks if there are any patients assigned to those positions.
        :param num_slots: The number of time slots to look ahead.
        :param start_index: The index of the starting time slot.
        :return: True if all the time slots are clear of patients, False otherwise.
        """
        for x in range(num_slots):

            # Not enough time-slots available to schedule.
            if start_index + x >= len(self.time_slots):
                return False

            # Someone has already been assigned to this position, can't double up on this machine.
            if self.time_slots[start_index + x]['patient'] is not None:
                return False

        # All the required slots are free!
        return True

    def is_patient_already_scheduled(self, patient: Patient) -> bool:
        """
        Checks if the given patient has already been previously assigned to this schedule.
        :param patient: The patient to check.
        :return: True if the patient has a previous appointment, False otherwise.
        """
        for other in self.patients:
            if other['id'] == patient['id']:
                return True
        return False

    def can_schedule_time_slot(self, patient: Patient, time_slot) -> bool:
        """
        Checks whether the patient can be scheduled into the desired time-slot.
        :param patient: The patient to schedule.
        :param time_slot: The time-slot to check.
        :return: True if there are no issues scheduling for the time-slot, False otherwise.
        """
        if len(self.time_slots) == 0:
            return False

        if self.is_patient_already_scheduled(patient):
            return False

        if time_slot['patient'] is not None:
            return False

        slots_required = self._get_required_slots(patient)

        start_index = self.time_slots.index(time_slot)
        return self._look_forward_time_slots(slots_required, start_index)

    def can_schedule(self, patient: Patient) -> Tuple[bool, int]:
        """
        Checks whether the patient can be scheduled.
        :param patient: The patient to schedule.
        :return: True if there is enough time available to schedule, False otherwise.
        """

        # For now don't schedule a patient on the same day as an existing treatment.
        if self.is_patient_already_scheduled(patient):
            return False, -1

        slots_required = self._get_required_slots(patient)

        for index, slot in enumerate(self.time_slots):

            # Find the next empty slot and check the next `n` slots to see if they are available
            if slot['patient'] is None:
                if self._look_forward_time_slots(slots_required, index):
                    return True, index

        # Not enough unallocated slots have been found. We can't schedule this patient here.
        return False, -1

    def has_available_time(self) -> bool:
        """
        Check if this LocationSchedule has any time allocated to it.
        :return: True if there is at least one time slot for the day, False otherwise.
        """
        return len(self.time_slots) > 0

    def get_patients(self) -> List:
        """
        Gets the list of patients that have been scheduled to this location.
        :return: The list of patients.
        """
        return self.patients

    def has_patients(self) -> bool:
        """
        Check whether the schedule has any patients assigned.
        :return: True if there are any patients in the list, False otherwise.
        """
        return len(self.patients) > 0

    def get_location_id(self) -> int:
        """
        Gets the location id for this schedule.
        :return: The location id.
        """
        return self.location_id

    def get_day(self) -> int:
        """
        Gets the day identifier for the schedule, where 0=Sunday, 1=Monday..., Saturday=6
        :return: The day identifier
        """
        return self.day

    def get_day_name(self) -> str:
        """
        Gets the name of the day this schedule represents.
        :return: The day name as a string.
        """
        return _day_names[self.day]

    def __str__(self):
        return "LocationSchedule[day={}, location={}]".format(self.day, self.location_id)


class Location:

    @staticmethod
    def _make_schedule(location_id: int, open_hours: Dict[str, str]) -> List[LocationSchedule]:
        """
        Gets a List of schedules from the given opening hours for a Location.
        :param location_id: The location to make the schedules for.
        :param open_hours: The opening hours of the Schedule.
        :return: A List of Schedules.
        """
        schedules = []
        for index, day in enumerate(_day_names):
            day = day.lower()
            open_name = day + "_open"
            close_name = day + "_close"

            schedules.append(LocationSchedule(location_id, index, open_hours[open_name], open_hours[close_name]))

        return schedules

    def __init__(self, location_id: int, name: str, department: int, activities: List[int], open_hours: Dict[str, str]):
        """
        :param location_id: The unique id of this location.
        :param name: The given name of this location.
        :param department: The department id (as an integer) that this location is in.
        :param activities: A list of activities that are actionable by this location.
        :param open_hours: A dictionary that contains the opening and closing hours for a weeks Schedule.
        """
        self.location_id = location_id
        self.department = department
        self.name = name
        self.activities = activities
        self.schedules = self._make_schedule(self.location_id, open_hours)

    def get_location_id(self) -> int:
        return self.location_id

    def get_allowed_activities(self) -> List[int]:
        """
        Gets all the activities that are able to be actioned by this location.
        :return: A list of the activity ids.
        """
        return self.activities

    def is_allowed(self, activity_id: int) -> bool:
        """
        Checks if the given activity is actioned by this location.
        :param activity_id: The activity database id to check.
        :return: True if the activity id is in the list of ids, False otherwise.
        """
        return activity_id in self.activities

    def get_schedule(self, day: int) -> LocationSchedule:
        """
        Gets a LocationSchedule by a day id (Sunday=0, Monday=1, Tuesday=2 etc...).
        This WILL throw an AssertError if the day range is invalid.
        :param day: The day id to retrieve.
        :return: The LocationSchedule for the given day.
        """
        assert day < len(self.schedules), "Invalid day range"
        return self.schedules[day]

    def get_schedules(self) -> List[LocationSchedule]:
        """
        Gets all the LocationSchedules for this location.
        :return: A List of LocationSchedules.
        """
        return self.schedules

    def __str__(self):
        return "Location[id={},name={},department={}]".format(self.location_id, self.name, self.department)
