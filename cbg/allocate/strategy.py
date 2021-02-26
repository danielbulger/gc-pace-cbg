from abc import abstractmethod
from cbg.patients import Patient
from typing import List


class AllocationStrategy:

    @abstractmethod
    def allocate(self, patient: List[Patient]) -> None:
        """
        Prototype method for scheduling patients to locations.
        :param patient: The list of patients to schedule.
        """
        pass
