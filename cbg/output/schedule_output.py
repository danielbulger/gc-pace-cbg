import csv
import os
import logging
from typing import List, Optional, Any, Dict

from cbg import config
from cbg.location import LocationSchedule
from abc import abstractmethod


class ScheduleOutput:

    @abstractmethod
    def write_schedule(self, schedule: LocationSchedule, time_slots: List[Dict[str, Any]]) -> None:
        """
        Prototype method for writing a schedule to some location in some format.
        :param schedule: The LocationSchedule that is been written.
        :param time_slots: The actual schedule data.
        """
        pass


class CSVScheduleOutput(ScheduleOutput):

    def __init__(self, activities):
        self.activities = activities

    @staticmethod
    def _get_directory_path(schedule: LocationSchedule) -> Optional[str]:
        """
        Gets the directory path to write the CSV file to.
        :param schedule: The LocationSchedule that is been written to CSV.
        :return: The relative directory path to write the file to.
        None if the directory does not exist and was not able to be created.
        """
        output_path = config.get_config('OUTPUT', 'OutputDirectory')
        directory_path = os.path.join('{}', '{}').format(output_path, schedule.get_location_id())

        # Check if the directory path exists.
        if not os.path.isdir(directory_path):
            # Create it if not.
            try:
                os.mkdir(directory_path)
            except:
                logging.exception("Unable to write {} to directory {}".format(schedule, directory_path), exc_info=True)
                return None
        return directory_path

    def write_schedule(self, schedule: LocationSchedule, time_slots: List[Dict[str, Any]]) -> None:
        # Nothing to write if there aren't any patients assigned.
        if len(schedule.get_patients()) == 0:
            return

        directory_path = self._get_directory_path(schedule)

        if directory_path is None:
            logging.warning(f"Unable to write {schedule} as the directory path couldn't be created")
            return

        file_path = (os.path.join('{}', '{}') + ' - {}.csv').format(
            directory_path,
            schedule.get_day(),
            schedule.get_day_name()
        )

        with open(file_path, 'w') as output_file:
            csv_writer = csv.DictWriter(output_file, fieldnames=['Time', 'PatientID', 'Activity', 'TreatmentTime'])

            # Write the header rows.
            csv_writer.writeheader()

            for time_slot in time_slots:
                patient = time_slot['patient']

                # No patient assigned to the time slot
                if patient is None:
                    csv_writer.writerow({
                        'Time': time_slot['slot'],
                        'PatientID': None,
                        'Activity': None,
                        'TreatmentTime': None
                    })
                else:
                    csv_writer.writerow({
                        'Time': time_slot['slot'],
                        'PatientID': patient['id'],
                        'Activity': self.activities[patient['activity']],
                        'TreatmentTime': patient['estimated_time']
                    })
