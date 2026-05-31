-- ================================================
-- Cleanup deterministic seed data for CI fixtures
-- ================================================

DELETE FROM uber_activity_log_live
WHERE uuid IN (
  'uuid-in', 'uuid-out', 'uuid-old',
  'uuid-login-in', 'uuid-login-out', 'uuid-login-old',
  'uuid-delivery-in', 'uuid-delivery-out', 'uuid-delivery-old',
  'uuid-center-in', 'uuid-center-out', 'uuid-center-old'
);

DELETE FROM uber_warnings
WHERE driver_id IN (
  'uuid-in', 'uuid-out', 'uuid-old',
  'uuid-login-in', 'uuid-login-out', 'uuid-login-old',
  'uuid-delivery-in', 'uuid-delivery-out', 'uuid-delivery-old',
  'uuid-center-in', 'uuid-center-out', 'uuid-center-old'
);

DELETE FROM users
WHERE uuid_id IN (
  'uuid-in', 'uuid-out', 'uuid-old',
  'uuid-login-in', 'uuid-login-out', 'uuid-login-old',
  'uuid-delivery-in', 'uuid-delivery-out', 'uuid-delivery-old',
  'uuid-center-in', 'uuid-center-out', 'uuid-center-old'
);
