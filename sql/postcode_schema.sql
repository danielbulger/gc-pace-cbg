CREATE TABLE pc (
  postcode INT,
  lat      FLOAT,
  lon      FLOAT
);

CREATE INDEX `postcode_idx`
  ON `pc` (
    `postcode`
  );

CREATE INDEX `lat_lon_idx`
  ON `pc` (
    `lat`, `lon`
  );