-- Migration 004: Add OCR Vocational Qualification Types
-- Cambridge Technicals (Level 3) and Cambridge Nationals (Level 2)

INSERT INTO qualification_types (code, name)
VALUES
  ('CAMBRIDGE_TECHNICALS_L3', 'Cambridge Technicals (Level 3)'),
  ('CAMBRIDGE_NATIONALS_L2', 'Cambridge Nationals (Level 2)')
ON CONFLICT (code) DO UPDATE SET
  name = EXCLUDED.name;


