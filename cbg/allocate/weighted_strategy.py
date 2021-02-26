import logging
from typing import List

from cbg.allocate import strategy
from cbg.location import LocationSchedule
from cbg.patients import Patient


class WeightedAllocationStrategy(strategy.AllocationStrategy):

    def __init__(self, distance_weight=1.25, load_weight=0.15, preference_weight=2):
        super().__init__()
        self.distance_weight = distance_weight
        self.load_weight = load_weight
        self.preference_weight = preference_weight

    def allocate(self, patients: List[Patient]) -> None:

        for patient in patients:
            if 'available_locations' not in patient:
                logging.info(f"Patients was missed in assigning locations {patient}")
                continue

            if len(patient['available_locations']) == 0:
                logging.info(f'No treatment locations found for {patient}')
                continue

            costs = self._get_patient_costs(patient)
            if len(costs) == 0:
                logging.warning(f'Unable to find suitable time slot for {patient}')
                continue

            best = costs[0]

            best[1].schedule_time_slot(patient, best[2])
            patient['assigned_location'] = best[1]

    def _determine_schedule_cost(self, patient: Patient, schedule: LocationSchedule, location_pos: int) -> float:
        cost = 0.0
        # Adjust the cost based on the preference this location is to the patient.
        # Ie: First closest = 0, Second =1 and so on.
        cost += (location_pos * self.distance_weight)

        # Favour machines that are not highly congested.
        cost += (schedule.get_percent_assigned() * self.load_weight)
        return cost

    def _determine_time_slot_cost(self, patient: Patient, schedule: LocationSchedule, time_slot, cost: float) -> float:

        if 'preferences' not in patient or len(patient['preferences']) == 0:
            # Patient doesn't have any preferences at all.
            cost += self.preference_weight
            return cost

        day_name = schedule.get_day_name()

        if day_name not in patient['preferences'] or patient['preferences'][day_name] is None:
            # Patient doesn't have any preferences for this particular day.
            cost += self.preference_weight
            return cost

        this_day_part = LocationSchedule.get_time_slot_day_part(time_slot).name.lower()

        if patient['preferences'][day_name] != this_day_part:
            cost += self.preference_weight

        return cost

    def _get_patient_costs(self, patient: Patient):
        costs = []

        for index, location in enumerate(patient['available_locations']):
            for schedule in location.get_schedules():

                if not schedule.has_available_time():
                    continue

                # Check to see patient is already scheduled for this day, if so, skip it completely!
                if schedule.is_patient_already_scheduled(patient):
                    continue

                # To speed up process, assign cost to each schedule day
                # Which is run once per schedule and add time slots cost onto this.
                schedule_cost = self._determine_schedule_cost(patient, schedule, index)

                for time_slot in schedule.get_time_slots():

                    # Pre-check to see if this time slot is even available to the Patient.
                    if not schedule.can_schedule_time_slot(patient, time_slot):
                        continue

                    cost = self._determine_time_slot_cost(patient, schedule, time_slot, schedule_cost)
                    costs.append([cost, schedule, time_slot])

        # Sort the costs by best (Lower cost = better solution)
        costs.sort(key=lambda x: x[0])

        return costs
