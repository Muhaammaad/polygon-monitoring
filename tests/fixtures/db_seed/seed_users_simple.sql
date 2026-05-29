-- ================================================
-- Seed users for deterministic zone-check testing
-- (login_check + delivery_check + center_check)
-- Same telegram_id for all
-- ================================================

DELETE FROM users
WHERE uuid_id IN (
  -- login_check
  'uuid-login-in', 'uuid-login-out', 'uuid-login-old',
  -- delivery_check
  'uuid-delivery-in', 'uuid-delivery-out', 'uuid-delivery-old',
  -- center_check
  'uuid-center-in', 'uuid-center-out', 'uuid-center-old'
);

INSERT INTO users (uuid_id, first_name, prefix, phone, telegram_id, telegram_language)
VALUES
-- login_check
('uuid-login-in',   'LoginInsideUser',  '41', '0790000101', '1899074076', 'FR'),
('uuid-login-out',  'LoginOutsideUser', '41', '0790000102', '1899074076', 'FR'),
('uuid-login-old',  'LoginOldUser',     '41', '0790000103', '1899074076', 'FR'),

-- delivery_check
('uuid-delivery-in',  'DeliveryInsideUser',  '41', '0790000201', '1899074076', 'FR'),
('uuid-delivery-out', 'DeliveryOutsideUser', '41', '0790000202', '1899074076', 'FR'),
('uuid-delivery-old', 'DeliveryOldUser',     '41', '0790000203', '1899074076', 'FR'),

-- center_check (ONLINE/PAUSED)
('uuid-center-in',   'CenterInsideUser',  '41', '0790000301', '1899074076', 'FR'),
('uuid-center-out',  'CenterOutsideUser', '41', '0790000302', '1899074076', 'FR'),
('uuid-center-old',  'CenterOldUser',     '41', '0790000303', '1899074076', 'FR');
