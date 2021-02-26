import sqlite3
from typing import List
import pandas as pd

from cbg.patients import Patient
from cbg.sim import simulation
import matplotlib.pyplot as plt

import seaborn as sns


class ActivityChangeSimulation(simulation.Simulation):

    def __init__(self, start_date: str, end_date: str):
        super().__init__(start_date, end_date)

    def run_sim(self, schedules: List[List[Patient]]):
        self.chart_activity_changes(self.simulate_activity_change(schedules))

    def _gc_activity_changes(self):
        with sqlite3.connect('sql/gcpace.sqlite3') as db:
            cursor = db.cursor().execute("""
                SELECT strftime('%Y-%m-%d', booking_datetime) AS BDATE, activity_id, location_id FROM bookings
                WHERE booking_datetime >= ? AND booking_datetime <= ?
                ORDER BY location_id, booking_datetime
            """, [self.start_date, self.end_date])

            results = []
            rows = cursor.fetchall()
            previous = rows[0]
            count = 0
            for row in rows[1:]:

                if row[0] != previous[0] or row[2] != previous[2]:
                    results.append(['GC', count])
                    count = 0
                    previous = row
                    continue

                if row[1] != previous[1]:
                    count += 1

                previous = row
        return results

    def simulate_activity_change(self, schedules: List[List[Patient]]) -> List:
        changes = []
        gc = self._gc_activity_changes()

        for schedule in schedules:

            previous = schedule[0]['activity']
            num_changes = 0

            for patient in schedule[1:]:
                if previous != patient['activity']:
                    num_changes += 1
                previous = patient['activity']

            changes.append(['CBG', num_changes])

        for x in gc:
            changes.append(x)

        return changes

    def chart_activity_changes(self, changes: List):
        sns.set(style="whitegrid")
        sns.set(font_scale=2)
        fig, ax = plt.subplots(figsize=(20, 10))

        df = pd.DataFrame(changes, columns=['Who', 'NumChanges'])
        sns.countplot(x='NumChanges', hue='Who', data=df, palette='colorblind', ax=ax)

        plt.title("Treatment Activity Changes ({} - {})".format(self.start_date, self.end_date))
        plt.xlabel("Num Changes")

        plt.show()
