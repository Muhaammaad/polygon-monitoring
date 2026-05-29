-- ================================================
-- Cleanup deterministic seed data for login_check
-- ================================================

DELETE FROM uber_activity_log_live
WHERE uuid IN ('uuid-in', 'uuid-out', 'uuid-old');

DELETE FROM uber_warnings
WHERE driver_id IN ('uuid-in', 'uuid-out', 'uuid-old');

DELETE FROM users
WHERE uuid_id IN ('uuid-in', 'uuid-out', 'uuid-old');
