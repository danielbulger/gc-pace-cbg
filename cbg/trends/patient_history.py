import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import logging
from cbg import config
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.neighbors import KNeighborsRegressor

from cbg.trends.global_history import get_act_quantile


def recurring_patient(patientID: int, activityID: int, date: str):
    """
    Return true if patient has had treatment before
    """
    with sqlite3.connect(config.get_config('DATABASE', 'BookingDatabase')) as db:
        cursor = db.cursor().execute("""
        SELECT patient_id FROM bookings 
        WHERE patient_id=? AND activity_id=? AND booking_datetime < ?""",
                                     [patientID, activityID, date])
        if cursor.fetchone():
            return True
        else:
            return False


def predict_nearest_neighbor(patientID: int, activityID: int, date: str, show_chart=False, validate_model=False):
    noRows = no_patient_rows(patientID, activityID, date)

    with sqlite3.connect(config.get_config('DATABASE', 'BookingDatabase')) as db:
        cursor = db.cursor().execute(
            "SELECT treatment_time FROM bookings "
            "WHERE treatment_time > 0 AND patient_id = ? AND activity_id=? AND booking_datetime < ?",
            [patientID, activityID, date]
        )
        x = 1
        data = []

        result = cursor.fetchall()

        for row in result:
            data.append([x, row[0]])
            x += 1

        frame = pd.DataFrame(data, columns=['Number', 'TreatmentTime'])
        quantile = frame["TreatmentTime"].quantile(0.997)
        frame = frame[frame["TreatmentTime"] < quantile]

        if len(frame) < 3:
            # If after removing the outliers there are not enough to run the NN algorithm, we need a fallback.
            return get_act_quantile(0.5, activityID)

        datasetX = frame['Number']
        datasetY = frame['TreatmentTime']
        logging.info(f"{datasetY}")

        if validate_model:
            twentyPC = round(noRows * 0.2)

            # Split the treatment numbers into training/testing sets
            datasetX_train = np.asarray(datasetX[:-twentyPC])
            datasetX_test = np.asarray(datasetX[-twentyPC:])

            # Split the treatment durations into training/testing sets
            datasetY_train = np.asarray(datasetY[:-twentyPC])
            datasetY_test = np.asarray(datasetY[-twentyPC:])
        else:
            datasetX_train = np.asarray(datasetX)
            datasetY_train = np.asarray(datasetY)

        # Create linear regression object
        regr = KNeighborsRegressor(n_neighbors=3, weights='distance')

        logging.info(f"DataSets: {datasetX} {datasetY}", )
        # Train the model using the training sets
        regr.fit(datasetX_train.reshape(-1, 1), datasetY_train.reshape(-1, 1))

        if validate_model:
            # Make predictions using the testing set
            datasetY_pred = regr.predict(datasetX_test.reshape(-1, 1))
            logging.info(datasetY_pred)

            # The coefficients
            # print('Coefficients: \n', regr.coef_)
            # The mean squared error
            logging.info("Mean squared error: %.2f"
                         % mean_squared_error(datasetY_test, datasetY_pred))
            # Explained variance score: 1 is perfect prediction
            logging.info('Variance score: %.2f' % r2_score(datasetY_test, datasetY_pred))

            if show_chart:
                plt.scatter(datasetX_train, datasetY_train, color='black', label='Actual treatment duration')
                plt.scatter(datasetX_test, datasetY_test, color='red', linewidth=3,
                            label='Actual test treatment duration')
                plt.plot(datasetX_train, regr.predict(datasetX_train.reshape(-1, 1)), color='blue', linewidth=3)
                plt.plot(datasetX_test, datasetY_pred, color='green', linewidth=3,
                         label='Predicted test treatment duration')

                plt.legend()
                plt.title("Patient ID: " + str(patientID))
                plt.xlabel("Treatment number (sequential order)")
                plt.ylabel("Treatment duration (minutes)")

                plt.xticks(datasetX, fontsize=7)
                plt.yticks(np.arange(0, 150, step=10), fontsize=7)

                plt.show()

        # Predict the next appointment time.
        return regr.predict(np.asarray([x + 1]).reshape(1, -1))[0][0]


def no_patient_rows(patientID: int, activityID: int, date: str):
    """
    Return the amount of treatments a patient has had for an activity
    """
    with sqlite3.connect(config.get_config('DATABASE', 'BookingDatabase')) as db:
        cursor = db.cursor().execute(
            "SELECT COUNT(treatment_time) FROM bookings "
            "WHERE treatment_time > 0 AND patient_id = ? AND activity_id=? AND booking_datetime < ?",
            [patientID, activityID, date]
        )
        result = cursor.fetchone()
        return result[0]


def predict_next_duration(patientID: int, activityID: int, date: str = None):
    """
    Predict next appointment duration
    Could just get treatment code from bookings table also
    """
    globalLimit = 3

    if date is None:
        date = '2099-12-31'

    if recurring_patient(patientID, activityID, date):
        noRows = no_patient_rows(patientID, activityID, date)

        if (noRows < globalLimit):
            return get_act_quantile(0.5, activityID)

        return predict_nearest_neighbor(patientID, activityID, date)

    else:
        return get_act_quantile(0.5, activityID)
