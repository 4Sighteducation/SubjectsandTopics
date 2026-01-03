-- Migration 006: Add SQA Qualification Types
-- Scottish National Qualifications (stored explicitly rather than mapped to GCSE/A-Level)

INSERT INTO qualification_types (code, name)
VALUES
  ('NATIONAL_5', 'National 5'),
  ('HIGHER', 'Higher'),
  ('ADVANCED_HIGHER', 'Advanced Higher')
ON CONFLICT (code) DO UPDATE SET
  name = EXCLUDED.name;






