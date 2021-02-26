import math

import sqlite3
from typing import List

from cbg.trends import patient_history
from cbg.patients import Patient
from cbg.sim import simulation


class WaitTime2018(simulation.Simulation):

    def __init__(self, start_date: str, end_date: str):
        super().__init__(start_date, end_date)

    def run_sim(self, schedules: List[List[Patient]]):
        with sqlite3.connect("sql/gcpace.sqlite3") as db:
            cursor = db.cursor().execute("""
                SELECT patient_id, activity_id, treatment_time, booking_datetime FROM bookings
                WHERE treatment_time != 0 AND booking_datetime >= '2018-01-01'
            """)

            total = 0
            count = 0

            for row in cursor.fetchall():
                count += 1
                prediction = patient_history.predict_next_duration(row[0], row[1], row[3])
                prediction = math.ceil(prediction / 5) * 5
                wait_time = prediction - row[2]

                total += wait_time

            avg = total / count
            return avg


if __name__ == '__main__':
    from cbg import config

    config.read_config('config.ini')
    sim = WaitTime2018(None, None)
    print(sim.run_sim(None))
