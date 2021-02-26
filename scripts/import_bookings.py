import sqlite3
import csv
from math import floor
from datetime import datetime
from collections import defaultdict
import codecs
import random

db = sqlite3.connect("../sql/gcpace.sqlite3")

cur = db.cursor()

with open('../sql/bookings_schema.sql', 'r') as schema_file:
    cur.executescript(schema_file.read())

patients = {}
activities = {}
locations = {}
departments = {}
department_locations = defaultdict(lambda: set())


def stripWhitespace(row: dict):
    # The dataset contains a lot of trailing whitespace for most of the fields. Strip that here.
    for key, value in row.items():
        if type(value) is str:
            row[key] = value.strip()


with codecs.open("schedule_v003.csv", "r", "utf-8-sig") as dataset:
    reader = csv.DictReader(dataset)

    for row in reader:
        stripWhitespace(row)
        patients[row['PatientID']] = row['PatientPostcode']
        activities[row['Activity']] = {
            'ActivityDefaultTime': row['ActivityDefaultTime']
        }
        locations[row['LocationID']] = {
            'LocationName': row['LocationName']
        }
        departments[row['DepartmentID']] = {
            'DepartmentName': row['DepartmentName'],
            'DepartmentPostcode': row['DepartmentPostcode']
        }

        department_locations[row['DepartmentID']].add(row['LocationID'])

for key, value in patients.items():
    cur.execute("INSERT INTO patients VALUES(?, ?)", [key, value])

for key, value in activities.items():
    cur.execute("INSERT INTO activities VALUES(NULL, ?, ?)", [key, value['ActivityDefaultTime']])

for key, value in departments.items():
    cur.execute("INSERT INTO departments VALUES(?, ?, ?)", [key, value['DepartmentName'], value['DepartmentPostcode']])

for key, value in locations.items():
    cur.execute("INSERT INTO locations VALUES(?, ?)", [key, value['LocationName']])

for key, value in department_locations.items():
    for locations in value:
        cur.execute("INSERT INTO department_locations VALUES(?, ?)", [key, locations])

db.commit()


def getTimeDifference(dt1, dt2):
    if dt2 < dt1:
        return -getTimeDifference(dt2, dt1)

    delta = dt2 - dt1
    # Round down and remove any decimal places. We only care about whole minutes
    return int(floor(delta.seconds / 60))


def insertBooking(row):
    booking_time = datetime.strptime(row['Booking'][row['Booking'].find(' ') + 1:-4], '%H:%M:%S')
    arrived = datetime.strptime(row['Arrived'], '%H:%M:%S')
    started = datetime.strptime(row['Started'], '%H:%M:%S')
    completed = datetime.strptime(row['Completed'], '%H:%M:%S')

    waiting_time = getTimeDifference(arrived, started)
    treatment_time = getTimeDifference(started, completed)
    delay_time = getTimeDifference(booking_time, started)
    cur.execute(
        "INSERT INTO bookings VALUES(?, ?, (SELECT id FROM activities WHERE code=?), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [row['Sch_ID'], row['PatientID'], row['Activity'], row['DepartmentID'], row['LocationID'],
         row['StatusAbbreviation'], row['Booking'], row['Arrived'], row['Started'], row['Completed'], waiting_time,
         treatment_time, delay_time])


def insertLocationActivities():
    cur.execute("""SELECT location_id, activity_id FROM bookings
                INNER JOIN activities ON activity_id = activities.id
                INNER JOIN locations ON locations.id = location_id
                GROUP BY location_id, activity_id
                ORDER BY location_id""")

    for row in cur.fetchall():
        cur.execute("INSERT INTO location_activities VALUES(?, ?)", row)
    db.commit()


def insertPatientPlan():
    cur.execute(
        """SELECT patient_id, strftime('%Y', booking_datetime) AS year, strftime('%W', booking_datetime) AS week_id,
        COUNT(strftime('%W', booking_datetime)) AS week_count FROM bookings
        GROUP BY patient_id, week_id
        ORDER BY patient_id, year, week_id""")

    for row in cur.fetchall():
        cur.execute("INSERT INTO patient_plan VALUES(?,?,?,?)", row)
    db.commit()


def insertPatientPref():
    preferences = ["morning", "midday", "afternoon"]

    cur.execute("SELECT id from patients")

    for row in cur.fetchall():
        choice = random.choice([True, True, False])
        if (choice):
            cur.execute(
                "INSERT INTO patient_preferences(patient_id, monday, tuesday, wednesday, thursday, friday, saturday,"
                "sunday) VALUES(?,?,?,?,?,?,?,?)", [row[0], random.choice(preferences), random.choice(preferences),
                                                    random.choice(preferences), random.choice(preferences),
                                                    random.choice(preferences),
                                                    random.choice(preferences), random.choice(preferences)])
        else:
            cur.execute(
                "INSERT INTO patient_preferences(patient_id) VALUES(?)", row)

    db.commit()


def insertGCBookingPredictions():
    cur.execute("SELECT * FROM bookings ORDER BY location_id, booking_datetime ASC")
    cur.row_factory = sqlite3.Row

    rows = cur.fetchall()
    previous = rows[0]

    for row in rows[1:]:
        # Not the same location, can't check :(
        if row['location_id'] != previous['location_id']:
            previous = row
            continue

        previous_dt = datetime.strptime(previous['booking_datetime'], '%Y-%m-%d %H:%M:%S.%f')
        current_dt = datetime.strptime(row['booking_datetime'], '%Y-%m-%d %H:%M:%S.%f')

        # Not the same day, can't check :(
        if previous_dt.date() != current_dt.date():
            previous = row
            continue

        prediction = getTimeDifference(previous_dt, current_dt)

        cur.execute("INSERT INTO booking_gc_predict VALUES(?, ?)", [previous['schedule_id'], prediction])
        previous = row
    db.commit()


def insertDepartmentHours():
    # For what ever reason, we couldn't get the opening/closing hours from GC.
    # Just take the min & max from the dataset and add them in for testing purposes.
    dayNames = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']

    cur.execute("""SELECT departments.name, strftime('%w', booking_datetime) AS DOW, 
        min(strftime('%H:%M', booking_datetime)) as MIN, 
        max(strftime('%H', completed, '+15 minutes')) AS MAX FROM bookings
    INNER JOIN departments ON departments.id = department_id
    GROUP BY departments.name, DOW""")

    hours = defaultdict(lambda: {})

    for row in cur.fetchall():
        name = dayNames[int(row[1])]
        hours[row[0]][f"{name}_open"] = row[2]
        hours[row[0]][f"{name}_close"] = row[3] + ":00"

    for key, values in hours.items():
        row_data = [key]

        for name in dayNames:
            open = f"{name}_open"
            close = f"{name}_close"

            row_data.append(None if open not in values else values[open])
            row_data.append(None if close not in values else values[close])

        cur.execute("""
        INSERT INTO department_hours VALUES(
        (SELECT id FROM departments WHERE name=?), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row_data)
    db.commit()


with codecs.open("schedule_v003.csv", "r", "utf-8-sig") as dataset:
    reader = csv.DictReader(dataset)

    for row in reader:
        stripWhitespace(row)
        try:
            insertBooking(row)
        except:
            pass
    db.commit()

# Must come after the first import since it uses the initial data to determine.
insertLocationActivities()
insertDepartmentHours()
insertGCBookingPredictions()
insertPatientPlan()
insertPatientPref()

db.close()
