import math
from typing import Dict, Any, List

from cbg.trends import patient_history, global_history
import logging

"""
A patient is simply a dictionary of properties.
Simply because patient data is only ever used as a argument and never needs to modify its own state.
"""
Patient = Dict[str, Any]


def sort_patients(patients: List[Patient]) -> None:
    """
    Sort Patients by how many available locations they have in ASCENDING order.
    This is to ensure patients that have fewer options are processed first and as such limits the risk that a machine
    is not filled with patients who have much more options available to them.
    :param patients: The list of Patients that will be sorted.
    """
    patients.sort(key=lambda x: len(x['available_locations']))


def add_patient_preferences(patient: Patient, preferences: Dict[int, Dict[str, str]]) -> None:

    if patient['id'] not in preferences:
        return

    patient['preferences'] = preferences[patient['id']]


def add_estimated_treatment_time(patient: Patient) -> None:
    """
    Adds an `estimated_time` key to the patient dictionary that contains the predicted duration of the next treatment.
    :param patient: The patient to predict the duration for.
    """
    try:
        predict = patient_history.predict_next_duration(patient['id'], patient['activity'])
        # If the predicted score is not a multiple of 5 minutes, round to the next one.
        if predict % 5 != 0:
            predict = int(math.ceil(predict / 5)) * 5
    except ValueError:
        logging.exception(f"Error while predicting treatment duration for {patient}", exc_info=True)
        predict = 15

    patient['estimated_time'] = predict


def add_patient_treatment_locations(patient: Patient, departments, locations) -> None:
    """
    Adds an `available_locations` key to the patient dictionary that contains a list of all the locations that the
    patient can be treated at, sorted in ascending order by distance.
    :param patient: The patient to assign to.
    :param departments: A list of all the departments. Used to calculate the distance between the patient's postcode
    and the department.
    :param locations: A list of all the locations. Used to find which locations are able to treat the given patient.
    """
    # Patient postcode wasn't found, need to fallback on default.
    if type(patient['postcode']) is str and len(patient['postcode']) == 0:
        closest = [key for key, value in departments.items()]
        logging.warning(f'No postcode for patient {patient}')
    else:
        try:
            closest = global_history.get_closest_dept(patient['postcode'])
        except:
            logging.exception(f'Error retrieving closest departments for {patient}', exc_info=True)
            return

    if closest is None:
        # TODO Need to provide some sort of feedback that this patient wasn't able to be allocated to a machine.
        logging.warning(f'No locations available for Patient[{patient}]')
        return

    patient['available_locations'] = []

    for department in closest:
        department_locations = departments[department]['locations']

        for location_id in department_locations:
            location = locations[location_id]

            # Patient can be treated at this location.
            if location.is_allowed(patient['activity']):
                patient['available_locations'].append(location)

    assert len(patient['available_locations']) > 0
