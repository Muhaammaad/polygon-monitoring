-- ===================================================
-- Seed activity log for deterministic zone checks test
-- MySQL version (no INTERVAL quotes, NOW() - INTERVAL N MINUTE)
-- login_check + delivery_check + center_check
-- ===================================================

DELETE FROM uber_activity_log_live
WHERE uuid IN (
  -- login_check
  'uuid-login-in', 'uuid-login-out', 'uuid-login-old',
  -- delivery_check
  'uuid-delivery-in', 'uuid-delivery-out', 'uuid-delivery-old',
  -- center_check (waiting/online)
  'uuid-center-in', 'uuid-center-out', 'uuid-center-old'
);

-- ---------------------------------------------------
-- LOGIN CHECK (time_window_minutes = 3)
-- status_group = login_candidates = ["login_event"]
-- target_zone  = login_zone
-- ---------------------------------------------------

-- uuid-login-in: NEW login inside login_zone
-- Expected warning: login_inside_zone
INSERT INTO uber_activity_log_live (uuid, latitude, longitude, location, status, ts)
VALUES
('uuid-login-in', 46.5200, 6.6200, 'TEST', 'LOGIN_EVENT', NOW() - INTERVAL 1 MINUTE);

-- uuid-login-out: NEW login outside login_zone
-- Expected warning: login_outside_zone
INSERT INTO uber_activity_log_live (uuid, latitude, longitude, location, status, ts)
VALUES
('uuid-login-out', 46.5200, 6.7000, 'TEST', 'LOGIN_EVENT', NOW() - INTERVAL 1 MINUTE);

-- uuid-login-old: NOT a new login (must be excluded)
-- Must have an older record within the last 2 hours + fresh record within last 3 minutes.
-- Expected: ignored (no warning)
INSERT INTO uber_activity_log_live (uuid, latitude, longitude, location, status, ts)
VALUES
('uuid-login-old', 46.5200, 6.6200, 'TEST', 'ONLINE',      NOW() - INTERVAL 30 MINUTE),
('uuid-login-old', 46.5200, 6.6200, 'TEST', 'LOGIN_EVENT', NOW() - INTERVAL 1 MINUTE);


-- ---------------------------------------------------
-- DELIVERY CHECK (time_window_minutes = 6)
-- status_group = delivery_candidates = ["delivering"]
-- target_zone  = delivery_zone
-- ---------------------------------------------------

-- uuid-delivery-in: NEW delivering inside delivery_zone
-- Expected warning: delivery_inside_zone (or "ok"/no warning depending on your policy)
INSERT INTO uber_activity_log_live (uuid, latitude, longitude, location, status, ts)
VALUES
('uuid-delivery-in', 46.5200, 6.6200, 'TEST', 'DELIVERING', NOW() - INTERVAL 2 MINUTE);

-- uuid-delivery-out: NEW delivering outside delivery_zone
-- Expected warning: delivery_outside_zone
INSERT INTO uber_activity_log_live (uuid, latitude, longitude, location, status, ts)
VALUES
('uuid-delivery-out', 46.5200, 6.7000, 'TEST', 'DELIVERING', NOW() - INTERVAL 2 MINUTE);

-- uuid-delivery-old: NOT a new delivering event (must be excluded)
-- Older record within last 2 hours + fresh within last 6 minutes.
-- Expected: ignored (no warning)
INSERT INTO uber_activity_log_live (uuid, latitude, longitude, location, status, ts)
VALUES
('uuid-delivery-old', 46.5200, 6.6200, 'TEST', 'ONLINE',     NOW() - INTERVAL 25 MINUTE),
('uuid-delivery-old', 46.5200, 6.6200, 'TEST', 'DELIVERING', NOW() - INTERVAL 2 MINUTE);


-- ---------------------------------------------------
-- CENTER CHECK (time_window_minutes = 10)
-- status_group  = waiting_candidates = ["online","paused"]
-- allowed_zones = ["waiting_zone"]  (your "center")
-- ---------------------------------------------------

-- uuid-center-in: NEW online inside waiting_zone
-- Expected warning: center_inside_zone (or "ok"/no warning depending on your policy)
INSERT INTO uber_activity_log_live (uuid, latitude, longitude, location, status, ts)
VALUES
('uuid-center-in', 46.5200, 6.6200, 'TEST', 'ONLINE', NOW() - INTERVAL 3 MINUTE);

-- uuid-center-out: NEW online outside waiting_zone
-- Expected warning: center_outside_zone
INSERT INTO uber_activity_log_live (uuid, latitude, longitude, location, status, ts)
VALUES
('uuid-center-out', 46.5200, 6.6300, 'TEST', 'ONLINE', NOW() - INTERVAL 3 MINUTE);
-- 6.6300 is inside login_zone but outside waiting_zone (waiting zone is ~6.6167..6.6233)

-- uuid-center-old: NOT a new waiting-candidate event (must be excluded)
-- Older record within the last 2 hours + fresh within last 10 minutes.
-- Expected: ignored (no warning)
INSERT INTO uber_activity_log_live (uuid, latitude, longitude, location, status, ts)
VALUES
('uuid-center-old', 46.5200, 6.6200, 'TEST', 'OFFLINE', NOW() - INTERVAL 40 MINUTE),
('uuid-center-old', 46.5200, 6.6200, 'TEST', 'ONLINE',  NOW() - INTERVAL 3 MINUTE);

