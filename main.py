import argparse

from cbg import db, config
from cbg.optimise.schedule import optimise_location_schedules
from cbg.patients import *
from cbg.sim import simulations

from cbg.allocate.weighted_strategy import WeightedAllocationStrategy
from cbg.output.schedule_output import CSVScheduleOutput


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('start_date', help='Start schedule date formatted as YYYY-MM-DD')
    parser.add_argument('end_date', help='End schedule date formatted as YYYY-MM-DD')
    parser.add_argument('--sims', help='Flags that simulations should be run', action='store_true')
    parser.add_argument('--prod', help='Flags that this is run in production mode', action='store_true')

    return parser.parse_args()


def setup_logging(prod: bool):
    """
    Iniitialise's the logging systems.
    :param prod: Whether the system will be run as production or not.
    """
    if prod:
        logging.basicConfig(level=logging.WARNING)
        # Add file handler to the root logger - ensures all children write to the same location.
        logging.getLogger('').addHandler(logging.FileHandler(config.read_config('LOGGING', 'LoggingFile')))
    else:
        logging.basicConfig(level=logging.INFO)


if __name__ == '__main__':
    args = get_args()

    # Load the required config.
    config.read_config('config.ini')

    setup_logging(args.prod)

    # Prefetch the required data from the database to limit the N+1 issue.
    departments = db.get_departments()
    locations = db.get_locations()
    activity_names = db.get_activity_names()
    preferences = db.get_patient_preferences()

    output = CSVScheduleOutput(activity_names)
    allocation = WeightedAllocationStrategy(
        config.get_float('WEIGHT', 'DistanceWeight'),
        config.get_float('WEIGHT', 'LoadWeight'),
        config.get_float('WEIGHT', 'PreferenceWeight')
    )

    # Get a sample set of patients to schedule.
    patients = db.get_patients(args.start_date, args.end_date)

    for patient in patients:
        # Adds the required generated data to the patient.
        add_estimated_treatment_time(patient)
        add_patient_treatment_locations(patient, departments, locations)
        add_patient_preferences(patient, preferences)

    sort_patients(patients)

    # Allocates patients to a schedule using the provided Allocation Strategy.
    allocation.allocate(patients)

    # Runs the optimisation process across all locations.
    all_schedules = optimise_location_schedules(list(locations.values()))

    # Write the location schedules to some Output here.
    for location in list(locations.values()):
        for schedule in location.get_schedules():
            output.write_schedule(schedule, schedule.get_time_slots())

    if args.sims:
        for simulation in simulations:
            simulation(args.start_date, args.end_date).run_sim(all_schedules)
