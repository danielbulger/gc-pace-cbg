import sqlite3
import numpy as np
import pandas as pd
import operator
import logging
from cbg import config


def get_closest_dept(patient: int):
    """
    This will return the closest department
    """
    pcDict = {}
    sortedPC = []
    with sqlite3.connect(config.get_config('DATABASE', 'BookingDatabase')) as db:
        rows = db.cursor().execute("SELECT id,postcode FROM departments")
        for row in rows:
            pcDist = get_distance(get_latlon(patient), get_latlon(row[1]))
            pcDict[row[0]] = pcDist

        sortedPCList = sorted(pcDict.items(), key=operator.itemgetter(1))
        for i in sortedPCList:
            sortedPC.append(i[0])

    return sortedPC


def get_distance(postcode1, postcode2):
    """
    Haversine approximation of distance between two points on earth
    """
    lon1 = postcode1['lon']
    lat1 = postcode1['lat']
    lon2 = postcode2['lon']
    lat2 = postcode2['lat']
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2

    c = 2 * np.arcsin(np.sqrt(a))
    km = 6367 * c
    return km


def get_latlon(number):
    if type(number) is str and len(number) == 0:
        logging.warning('Invalid postcode input')
        return {
            'lat': 0,
            'lon': 0
        }

    with sqlite3.connect(config.get_config('DATABASE', 'PostcodeDatabase')) as db:
        cursor = db.cursor().execute("SELECT lat, lon FROM pc where postcode=?", [number])
        result = cursor.fetchone()
        if not result:
            logging.warning(f'No lat/lon found for postcode {number}')
            # If the postcode wasn't found just return a default empty value.
            return {
                'lat': 0,
                'lon': 0
            }
        lat = result[0]
        lon = result[1]

        latlon = {'lat': lat, 'lon': lon}

        return latlon


def get_act_quantile(qt: float, activityCode):
    """
    This function provides the average quantile minutes for a booking of that activity
    """
    with sqlite3.connect(config.get_config('DATABASE', 'BookingDatabase')) as db:
        cursor = db.cursor().execute("SELECT id,code FROM activities WHERE id=?", (activityCode,))
        result = cursor.fetchone()
        activity = [result[0], result[1]]
        data = []
        cursor = db.cursor().execute(
            "SELECT treatment_time AS C FROM bookings "
            "WHERE treatment_time > 0 AND completed > started and activity_id=?", [result[0]]
        )
        for row in cursor.fetchall():
            data.append([activity[1], int(row[0])])

        frame = pd.DataFrame(data, columns=['activity', 'time'])
        return frame["time"].quantile(qt)
