"""
sim package should contain any simulations on generated schedules that need to be done to validate performance increases.

Anything that can assist in determining that our generated schedules are actually an improvement should be in here.
"""
from typing import List
from cbg.sim import simulation, activity_change_sim, delay_sim, distance_sim

SimulationList = List[simulation.Simulation]

"""
Store all available Simulations and make it accessible to all.
"""
simulations: SimulationList = [
    activity_change_sim.ActivityChangeSimulation,
    delay_sim.DelaySimulation,
    distance_sim.DistanceSimulation
]
