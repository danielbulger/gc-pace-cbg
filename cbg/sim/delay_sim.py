import math

import sqlite3
from typing import List

from cbg.patients import Patient
from cbg.sim import simulation
import matplotlib.pyplot as plt
import pandas as pd

import seaborn as sns


class DelaySimulation(simulation.Simulation):

    def __init__(self, start_date: str, end_date: str):
        super().__init__(start_date, end_date)

    def run_sim(self, schedules: List[List[Patient]]):
        self.chart_delay_times(self.simulate_delay_times(schedules))

    def _get_gc_delay_times(self):
        with sqlite3.connect('sql/gcpace.sqlite3') as db:
            cursor = db.cursor().execute("""
            SELECT delay_time FROM bookings 
            WHERE booking_datetime >= ? and booking_datetime <= ?
            """, [self.start_date, self.end_date])

            results = []

            for x in cursor.fetchall():
                results.append(['GC', int(math.ceil(x[0] / 5) * 5)])

            return results

    def simulate_delay_times(self, schedules: List[List[Patient]]):
        delays = []

        for schedule in schedules:
            for patient in schedule:
                if patient['treatment_time'] == 0:
                    # The patient does not have an accurate treatment time and shouldn't be compared.
                    continue

                # Delay time is the difference between what we estimated and what actually happened.
                time = patient['treatment_time'] - patient['estimated_time']

                # Most likely due to bad data, skip this to not heavily skew the data
                if abs(time) > 100:
                    continue

                time = int(math.ceil(time / 5) * 5)

                delays.append(['CBG', time])

        size = len(delays)

        for index, x in enumerate(self._get_gc_delay_times()):
            if index >= size:
                break
            delays.append(x)

        return delays

    def chart_delay_times(self, delays):
        sns.set(style="whitegrid")
        sns.set(font_scale=1.5)
        fig, ax = plt.subplots(figsize=(20, 10))

        df = pd.DataFrame(delays, columns=['Who', 'DelayTime'])

        sns.countplot(x='DelayTime', hue='Who', data=df, palette='colorblind')

        plt.title("Treatment Delay Times ({} - {})".format(self.start_date, self.end_date))
        plt.xlabel("Delay Time (minutes)")

        plt.show()
