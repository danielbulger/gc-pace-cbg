import math

import sqlite3
from typing import List

from cbg.trends import patient_history
from cbg.patients import Patient
from cbg.sim import simulation
import matplotlib.pyplot as plt
import pandas as pd

import seaborn as sns


class PatientPlanSim(simulation.Simulation):

    def __init__(self, start_date: str, end_date: str):
        super().__init__(start_date, end_date)

    def run_sim(self, schedules: List[List[Patient]]):
        self.chart_treatments(self.sim_data())

    def sim_data(self):
        predictions = []

        with sqlite3.connect('sql/gcpace.sqlite3') as db:
            cursor = db.cursor().execute("""
                    SELECT patient_id, activity_id, treatment_time, prediction, booking_datetime FROM bookings
                    INNER JOIN booking_gc_predict p on bookings.schedule_id = p.schedule_id
                    WHERE treatment_time != 0 AND patient_id = '63495'
                    """)

            for index, x in enumerate(cursor.fetchall()):
                predictions.append(['Actual', index, x[2]])
                predictions.append(['GC', index, x[3]])
                predictions.append(['CBG', index, patient_history.predict_next_duration(x[0], x[1], x[4])])

        return predictions

    def chart_treatments(self, predictions):
        sns.set(style="whitegrid")
        sns.set(font_scale=2)
        fig, ax = plt.subplots(figsize=(20, 10))

        df = pd.DataFrame(predictions, columns=['Who', 'TreatmentNum', 'Time'])

        sns.lineplot(x='TreatmentNum', y='Time', hue='Who', data=df, palette='colorblind')

        plt.title("John Smith Patient Plan")
        plt.xlabel("Treatment Number")
        plt.ylabel("Treatment Time (minutes)")

        plt.show()


if __name__ == '__main__':
    from cbg import config

    config.read_config('config.ini')
    plan = PatientPlanSim(None, None)
    plan.run_sim(None)
