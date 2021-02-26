import sqlite3
from collections import defaultdict
from typing import Dict, List, Any
from cbg import config
from cbg.location import Location
from cbg.patients import Patient

_database_file = None


def _get_database_file():
    """
    Gets the name of the database file that should be used.
    :return: The database file to use.
    """
    global _database_file
    if not _database_file:
        _database_file = config.get_config('DATABASE', 'BookingDatabase')
    return _database_file


def get_activity_names() -> Dict[int, str]:
    """
    Gets all the activities that are available in the database.
    :return: A Dictionary containing the id as keys and the activity as values.
    """
    with sqlite3.connect(_get_database_file()) as db:
        cursor = db.cursor().execute("SELECT id, code FROM activities")

        result = {}

        for row in cursor.fetchall():
            result[row[0]] = row[1]

        return result


def get_location_activities(location_id: int) -> List[int]:
    """
    Retrieves all the activity ids that the given location can treat.
    :param location_id: The location id.
    :return: A List of all the activity ids. An empty list if none are found.
    """
    with sqlite3.connect(_get_database_file()) as db:
        cursor = db.cursor().execute(
            "SELECT activity_id FROM location_activities WHERE location_id = ?",
            [location_id]
        )
        return [int(x) for x in cursor.fetchall()]


def get_all_location_activities() -> Dict[int, List[int]]:
    """
    Retrieves all the location and their corresponding activity ids.
    :return: A Dictionary containing the location id as the key, and a list of activity ids as the value.
    """
    with sqlite3.connect(_get_database_file()) as db:
        cursor = db.cursor().execute(
            'SELECT location_id, activity_id FROM location_activities'
        )

        results = defaultdict(lambda: [])

        for row in cursor.fetchall():
            results[row[0]].append(row[1])

        return results


def get_departments() -> Dict[int, Dict[str, Any]]:
    """
    Gets all the Departments available.
    :return: A Dictionary containing the department id as the key, and the department values.
    """
    locations = get_locations_by_department()
    with sqlite3.connect(_get_database_file()) as db:
        cursor = db.cursor().execute(
            'SELECT id, name, postcode FROM departments'
        )

        result = {}

        for row in cursor.fetchall():
            result[row[0]] = {
                'name': row[1],
                'postcode': row[2],
                'locations': locations[row[0]]
            }

        return result


def get_locations() -> Dict[int, Location]:
    """
    Gets all the locations available.
    :return: A Dictionary containing the location id as the key, and the Location as a value.
    """
    activities = get_all_location_activities()
    hours = get_location_hours()

    with sqlite3.connect(_get_database_file()) as db:
        cursor = db.cursor().execute(
            'SELECT locations.id, locations.name, department_id FROM locations '
            'INNER JOIN department_locations ON locations.id = location_id'
        )

        result = {}

        for row in cursor.fetchall():
            result[row[0]] = Location(row[0], row[1], row[2], activities[row[0]], hours[row[0]])

        return result


def get_locations_by_department() -> Dict[int, List[int]]:
    """
    Gets all the locations assigned to a department.
    :return: A Dictionary containing the department id as the key, and a list of location ids as the value.
    """
    with sqlite3.connect(_get_database_file()) as db:
        cursor = db.cursor().execute(
            'SELECT department_id, location_id FROM department_locations'
        )
        results = defaultdict(lambda: [])

        for row in cursor.fetchall():
            results[row[0]].append(row[1])

        return results


def get_location_hours() -> Dict[int, Dict[str, str]]:
    with sqlite3.connect(_get_database_file()) as db:
        db.row_factory = sqlite3.Row

        cursor = db.cursor().execute("""
        SELECT department_locations.location_id, department_hours.* FROM department_hours 
        INNER JOIN department_locations ON department_locations.department_id = department_hours.department_id
        ORDER BY department_id""")

        results = {}

        for row in cursor.fetchall():
            results[row['location_id']] = {}

            for key in row.keys():
                if key != 'department_id' and key != 'location_id':
                    results[row['location_id']][key] = row[key]

        return results


def get_patients(start_date: str, end_date: str) -> List[Patient]:
    """
    Gets a select group of historic patient data as a control group.
    :return: A list of patients.
    """
    with sqlite3.connect(_get_database_file()) as db:
        cursor = db.cursor().execute(
            'SELECT patient_id, activity_id, patients.postcode, treatment_time FROM bookings '
            'INNER JOIN patients ON patient_id = patients.id '
            'WHERE booking_datetime >= ? AND booking_datetime <= ?',
            [start_date, end_date]
        )
        patients = []

        for row in cursor.fetchall():
            patients.append({
                'id': row[0],
                'activity': row[1],
                'postcode': row[2],
                'treatment_time': row[3]
            })
        return patients


def get_patient_preferences() -> Dict[int, Dict[str, str]]:
    with sqlite3.connect(_get_database_file()) as db:
        db.row_factory = sqlite3.Row

        cursor = db.cursor().execute(
            "SELECT * FROM patient_preferences ORDER BY patient_id ASC"
        )

        results = {}

        for row in cursor.fetchall():
            results[row['patient_id']] = {}

            for key in row.keys():
                if key != 'patient_id':
                    if row[key] is not None:
                        results[row['patient_id']][key.lower()] = row[key].lower()

        return results
