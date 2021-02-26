from cbg.location import LocationSchedule
from cbg.patients import Patient
from cbg.allocate import strategy
from typing import List, Tuple
import logging


class FullQuotaAllocationStrategy(strategy.AllocationStrategy):

    def allocate(self, patients: List[Patient]) -> None:
        """
        Allocates the patients by using the distance to a location as a metric.
        The patients are assigned to the closest available location until the location is full for the week, moving to
        the next closest location.
        This strategy is not good for machine utilisation.
        :param patients: The list of patients to schedule.
        """
        for patient in patients:
            if 'available_locations' not in patient:
                logging.info(f"Patients was not given any treatment locations: {patient}")
                continue

            if not patient['available_locations']:
                logging.info(f'No treatment locations found for {patient}')
                continue

            best, index = self.determine_best_schedule(patient)

            if best is None:
                logging.warning(f'Patient unable to be allocated to location Patient=[{patient}]')
                # TODO: If a patient can't be scheduled this needs to trigger some output to assist.
                continue

            best.schedule(patient, index)
            patient['assigned_location'] = best

    def determine_best_schedule(self, patient: Patient) -> Tuple[LocationSchedule, int]:
        """
        Determines the best location schedule to schedule the patient to.
        :param patient: The patient to schedule.
        :return: The most optional available LocationSchedule, or None in the event no location schedule is found.
        """
        # Search the best available locations for the patient
        for location in patient['available_locations']:
            # Search the location daily schedules to find a spot
            for schedule in location.get_schedules():

                available, index = schedule.can_schedule(patient)

                if available:
                    # Return the best result that is still available.
                    return schedule, index

        # Nothing can be found left. Fully booked?
        return None, -1
