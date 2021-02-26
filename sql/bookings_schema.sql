PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;
CREATE TABLE `activities` (
  `id`           INTEGER PRIMARY KEY AUTOINCREMENT,
  `code`         TEXT UNIQUE,
  `default_time` INTEGER
);
CREATE TABLE `bookings` (
  `schedule_id`      INTEGER PRIMARY KEY,
  `patient_id`       INTEGER,
  `activity_id`      INTEGER,
  `department_id`    INTEGER,
  `location_id`      INTEGER,
  `status`           TEXT,
  `booking_datetime` TEXT,
  `arrived`          TEXT,
  `started`          TEXT,
  `completed`        TEXT,
  `waiting_time`     INTEGER,
  `treatment_time`   INTEGER,
  `delay_time`       INTEGER,

  FOREIGN KEY (patient_id) REFERENCES patients (id),
  FOREIGN KEY (activity_id) REFERENCES activities (id),
  FOREIGN KEY (department_id) REFERENCES departments (id),
  FOREIGN KEY (location_id) REFERENCES locations (id)
);
CREATE TABLE `departments` (
  `id`       INTEGER PRIMARY KEY,
  `name`     TEXT UNIQUE,
  `postcode` INTEGER
);
CREATE TABLE `locations` (
  `id`   INTEGER PRIMARY KEY,
  `name` TEXT UNIQUE
);
CREATE TABLE `department_locations` (
  `department_id` INTEGER,
  `location_id`   INTEGER,
  PRIMARY KEY (`department_id`, `location_id`),
  FOREIGN KEY (department_id) REFERENCES departments (id),
  FOREIGN KEY (location_id) REFERENCES locations (id)
);
CREATE TABLE `patients` (
  `id`       INTEGER,
  `postcode` INTEGER,
  PRIMARY KEY (`id`)
);
CREATE TABLE `patient_plan` (
  `patient_id`      INTEGER,
  `year`            INTEGER,
  `week_id`         INTEGER,
  `treatment_count` INTEGER,
  PRIMARY KEY (`patient_id`, `year`, `week_id`),
  FOREIGN KEY (patient_id) REFERENCES patients (id)
);
CREATE TABLE `patient_preferences` (
  `patient_id` INTEGER PRIMARY KEY,
  `monday`     TEXT,
  `tuesday`    TEXT,
  `wednesday`  TEXT,
  `thursday`   TEXT,
  `friday`     TEXT,
  `saturday`   TEXT,
  `sunday`     TEXT,
  FOREIGN KEY (patient_id) REFERENCES patients (id)
);
CREATE TABLE `location_activities` (
  'location_id' INTEGER,
  'activity_id' INTEGER,
  PRIMARY KEY (`location_id`, `activity_id`),
  FOREIGN KEY (activity_id) REFERENCES activities (id),
  FOREIGN KEY (location_id) REFERENCES locations (id)
);
CREATE TABLE `department_hours` (
  'department_id'   INTEGER PRIMARY KEY,
  'sunday_open'     TEXT,
  'sunday_close'    TEXT,
  'monday_open'     TEXT,
  'monday_close'    TEXT,
  'tuesday_open'    TEXT,
  'tuesday_close'   TEXT,
  'wednesday_open'  TEXT,
  'wednesday_close' TEXT,
  'thursday_open'   TEXT,
  'thursday_close'  TEXT,
  'friday_open'     TEXT,
  'friday_close'    TEXT,
  'saturday_open'   TEXT,
  'saturday_close'  TEXT,
  FOREIGN KEY (department_id) REFERENCES departments (id)
);
CREATE TABLE `booking_gc_predict` (
  'schedule_id' INTEGER PRIMARY KEY,
  'prediction'  INTEGER,
  FOREIGN KEY (schedule_id) REFERENCES bookings (schedule_id)
);
DELETE
FROM sqlite_sequence;
CREATE INDEX `patient_idx`
  ON `bookings` (
    `patient_id`
  );
CREATE INDEX `activity_idx`
  ON `bookings` (
    `activity_id`
  );
CREATE INDEX `location_idx`
  ON `bookings` (
    `location_id`
  );
CREATE INDEX `department_location_department_idx`
  ON `department_locations` (
    `department_id`
  );
CREATE INDEX `department_location_location_idx`
  ON `department_locations` (
    `location_id`
  );
COMMIT;
