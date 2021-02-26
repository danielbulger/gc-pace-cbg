import operator
import array
import logging
from typing import List

import numpy

from cbg import config
from deap import algorithms, base, creator, tools

from collections import namedtuple

from cbg.location import Location
from cbg.patients import Patient

OptimiseConfig = namedtuple('OptimiseConfig', [
    # The probability of 2 individuals mating.
    'mate_prob',
    # The number of generations to run through.
    'num_generations',
    # The probability an individual will be mutated
    'mutate_prob',
    # The probability that an individual's gene will be mutated
    'mutate_bit_prob',
    # The total size of the tournament.
    'tourn_size',
    # The number of individuals in each population.
    'population_size',
    # Whether eaSimple should be verbose in the logging or not.
    'verbose'
])


def get_optimise_config():
    """
    Reads the optimiser config as a OptimiseConfig object.
    :return: The resulting OptimiseConfig.
    """
    return OptimiseConfig(
        config.get_float('GA', 'MateProb'),
        config.get_int('GA', 'NumGenerations'),
        config.get_float('GA', 'MutateProb'),
        config.get_float('GA', 'MutateBitProb'),
        config.get_int('GA', 'TournSize'),
        config.get_int('GA', 'PopulationSize'),
        config.get_bool('GA', 'Verbose'),
    )


creator.create(
    'FitnessMin',
    base.Fitness,
    weights=(-1.0,)
)

creator.create(
    'Individual',
    array.array,
    typecode='i',
    fitness=creator.FitnessMin
)


def optimise_location_schedules(locations: List[Location]) -> List[List[Patient]]:
    outputs = []
    for location in locations:
        for schedule in location.get_schedules():

            if not schedule.has_patients():
                # If the schedule doesn't have any time available, not having patients assigned it not an issue.
                # Otherwise, this needs to flagged as it may indicate an issue with the algorithm
                if schedule.has_available_time():
                    logging.warning(f"LocationSchedule[{schedule}] does not have any patients assigned")
                continue

            best = schedule.get_patients() if len(schedule.get_patients()) <= 2 else optimise_schedule(schedule)

            outputs.append(best)
            # Not enough to optimise.
            if len(schedule.get_patients()) <= 2:
                logging.info(f'Not enough patients to optimise {schedule}')

            # Ensure that all patients have been scheduled and none has been missed out in the optimisation process.
            assert (len(best) == len(schedule.get_patients()))

            # Reorder the Location Schedule based on the newly optimised one.
            schedule.reorder_time_slots(best)

    return outputs


def optimise_schedule(schedule) -> List[Patient]:
    patients = schedule.get_patients()
    config = get_optimise_config()

    def create_schedule(individual):
        """
        Converts an individual into a LocationSchedule.
        :param individual: The individual to convert.
        :return: The List of patients in the Schedule order.
        """
        return [patients[x] for x in individual]

    def _evaluate(individual):
        """
        Determines the cost of the individual.
        Currently, this based on how much machine calibrations will be required through the day.
        :param individual: The individual schedule to evaluate.
        :return: The weighted cost of the individual.
        """
        this_schedule = create_schedule(individual)

        previous = this_schedule[0]['activity']
        changes = 0

        for encoding in this_schedule[1:]:

            activity = encoding['activity']

            # For now a better schedule is defined by how few machine calibrations are required.
            if activity != previous:
                changes += 1

            previous = activity

        # Return a tuple, don't remove the trailing command it is required.
        return float(changes),

    def find_best_schedule():
        """
        Runs a genetic algorithm on the LocationSchedule.
        :return: The final, most optimal schedule.
        """
        toolbox = base.Toolbox()
        toolbox.register(
            'indices',
            numpy.random.permutation,
            len(patients)
        )

        toolbox.register(
            'individual',
            tools.initIterate,
            creator.Individual,
            toolbox.indices
        )

        toolbox.register(
            'population',
            tools.initRepeat,
            list,
            toolbox.individual
        )

        toolbox.register('evaluate', _evaluate)
        toolbox.register('mate', tools.cxOrdered)

        toolbox.register(
            'mutate',
            tools.mutShuffleIndexes,
            indpb=getattr(config, 'mutate_bit_prob')
        )

        toolbox.register(
            'select',
            tools.selTournament,
            tournsize=getattr(config, 'tourn_size')
        )

        fame = tools.HallOfFame(1)
        pop = toolbox.population(n=getattr(config, 'population_size'))

        fit_stats = tools.Statistics(key=operator.attrgetter('fitness.values'))
        fit_stats.register('mean', numpy.mean)
        fit_stats.register('min', numpy.min)
        fit_stats.register('std', numpy.std)

        algorithms.eaSimple(
            pop,
            toolbox,
            cxpb=getattr(config, 'mate_prob'),
            mutpb=getattr(config, 'mutate_prob'),
            ngen=getattr(config, 'num_generations'),
            halloffame=fame,
            verbose=getattr(config, 'verbose'),
            stats=fit_stats
        )

        return create_schedule(fame[0])

    return find_best_schedule()
