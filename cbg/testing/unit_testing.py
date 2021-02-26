import unittest
import sqlite3
from random import randint
from cbg.trends.patient_history import predict_next_duration


class testPrediction(unittest.TestCase):


    def setUp(self):
        pass

    def test_prediction_accuracy(self):
        con = sqlite3.connect("sql/gcpace.sqlite3")
        cur_db = con.cursor()
        cur_db.execute("SELECT patient_id FROM bookings")
        result = cur_db.fetchone()
        number_of_rows = result[0]

        for row in cur_db.fetchall():


        self.assertTrue(predict_next_duration())

    def test_strings_a_3(self):
        self.assertEqual(multiply('a', 3), 'aaa')


if __name__ == '__main__':
    unittest.main()