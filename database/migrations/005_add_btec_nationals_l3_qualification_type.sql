-- Migration 005: Add Edexcel Vocational Qualification Type
-- BTEC Nationals (Level 3)

INSERT INTO qualification_types (code, name)
VALUES
  ('BTEC_NATIONALS_L3', 'BTEC Nationals (Level 3)')
ON CONFLICT (code) DO UPDATE SET
  name = EXCLUDED.name;


