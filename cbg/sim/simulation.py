from typing import List
from cbg.patients import Patient
from abc import abstractmethod


class Simulation:

    def __init__(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date

    @abstractmethod
    def run_sim(self, schedules: List[List[Patient]]) -> None:
        """
        Prototype simulation that will run on the list of schedules.
        :param schedules: The schedules to simulate.
        """
        pass
