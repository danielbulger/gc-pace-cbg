import sqlite3
import csv
import codecs

pc_db = sqlite3.connect("../sql/postcode.sqlite3")

cur = pc_db.cursor()

with open('../sql/postcode_schema.sql', 'r') as schema_file:
    cur.executescript(schema_file.read())

postcode = []

with codecs.open("postcodes.csv", "r", "utf-8-sig") as dataset:
    reader = csv.DictReader(dataset)

    for row in reader:
        cur.execute("INSERT INTO pc VALUES(?, ?, ?)", [row['postcode'], row['lat'], row['lon']])

pc_db.commit()
pc_db.close()
