from typing import List

from cbg.patients import Patient
from cbg.sim import simulation
import matplotlib.pyplot as plt

import seaborn as sns


class DistanceSimulation(simulation.Simulation):

    def __init__(self, start_date: str, end_date: str):
        super().__init__(start_date, end_date)

    def run_sim(self, schedules: List[List[Patient]]):
        self.chart_distances(self.simulate_distance(schedules))

    def simulate_distance(self, schedules: List[List[Patient]]) -> List:
        distances = []

        for schedule in schedules:

            for patient in schedule:
                assigned = patient['assigned_location']

                for x in range(len(patient['available_locations'])):
                    if patient['available_locations'][x].get_location_id() == assigned.get_location_id():
                        distances.append(x + 1)

        return distances

    def chart_distances(self, distances: List):
        sns.set(style="whitegrid")

        sns.distplot(distances, norm_hist=False)

        plt.title("Patient Location Distances ({} - {})".format(self.start_date, self.end_date))
        plt.xlabel("Chosen Location Option")

        plt.show()
