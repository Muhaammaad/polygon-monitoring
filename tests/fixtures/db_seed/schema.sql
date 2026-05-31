-- Minimal schema for CI / integration tests (matches production table names)

CREATE TABLE IF NOT EXISTS uber_activity_log_live (
  uuid VARCHAR(255) NOT NULL,
  latitude DOUBLE NOT NULL,
  longitude DOUBLE NOT NULL,
  location VARCHAR(50) NOT NULL,
  status VARCHAR(50) NOT NULL,
  ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_location_status_ts (location, status, ts),
  INDEX idx_uuid_location_ts (uuid, location, ts)
);

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  uuid_id VARCHAR(255) NOT NULL,
  first_name VARCHAR(255),
  prefix VARCHAR(10),
  phone VARCHAR(255),
  telegram_id VARCHAR(255),
  telegram_language VARCHAR(50),
  UNIQUE KEY idx_uuid_id (uuid_id)
);

CREATE TABLE IF NOT EXISTS uber_warnings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  driver_id VARCHAR(255),
  note VARCHAR(255),
  counter INT DEFAULT NULL,
  ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
