-- MIGRATE STAGING DATA TO PRODUCTION
-- This moves Edexcel data from staging_aqa_* tables to production exam_board_subjects and curriculum_topics
-- Run this in Supabase SQL Editor

BEGIN;

-- ========================================
-- STEP 1: Ensure Edexcel exam board exists
-- ========================================
INSERT INTO exam_boards (code, full_name, active, country)
VALUES ('Edexcel', 'Pearson Edexcel', true, 'UK')
ON CONFLICT (code) DO UPDATE SET
  full_name = EXCLUDED.full_name,
  active = EXCLUDED.active;

-- ========================================
-- STEP 2: Ensure qualification types exist
-- ========================================
INSERT INTO qualification_types (code, name)
VALUES 
  ('A_LEVEL', 'A-Level'),
  ('GCSE', 'GCSE'),
  ('INTERNATIONAL_GCSE', 'International GCSE'),
  ('INTERNATIONAL_A_LEVEL', 'International A-Level'),
  ('BTEC_NATIONALS_L3', 'BTEC Nationals (Level 3)')
ON CONFLICT (code) DO UPDATE SET
  name = EXCLUDED.name;

-- ========================================
-- STEP 3: Migrate Subjects (staging → production)
-- ========================================

-- First, mark old Edexcel subjects as not current (keep for history)
UPDATE exam_board_subjects
SET is_current = false,
    updated_at = NOW()
WHERE exam_board_id = (SELECT id FROM exam_boards WHERE code = 'Edexcel')
  AND is_current = true;

-- Insert/Update subjects from staging
INSERT INTO exam_board_subjects (
  subject_code,
  subject_name,
  exam_board_id,
  qualification_type_id,
  is_current,
  created_at,
  updated_at
)
SELECT 
  ss.subject_code,
  ss.subject_name,
  (SELECT id FROM exam_boards WHERE code = 'Edexcel'),
  (SELECT id FROM qualification_types WHERE code = 
    CASE ss.qualification_type
      WHEN 'A-Level' THEN 'A_LEVEL'
      WHEN 'GCSE' THEN 'GCSE'
      WHEN 'International-GCSE' THEN 'INTERNATIONAL_GCSE'
      WHEN 'International-A-Level' THEN 'INTERNATIONAL_A_LEVEL'
      WHEN 'BTEC_NATIONALS_L3' THEN 'BTEC_NATIONALS_L3'
      ELSE 'A_LEVEL'
    END
  ),
  true,
  NOW(),
  NOW()
FROM staging_aqa_subjects ss
WHERE ss.exam_board = 'Edexcel'
ON CONFLICT (subject_code, exam_board_id, qualification_type_id) 
DO UPDATE SET
  subject_name = EXCLUDED.subject_name,
  is_current = true,
  updated_at = NOW();

-- ========================================
-- STEP 4: Create temporary mapping table
-- ========================================

-- Map staging subject IDs to production subject IDs
CREATE TEMP TABLE subject_id_mapping AS
SELECT 
  ss.id as staging_id,
  ebs.id as production_id,
  ss.subject_code
FROM staging_aqa_subjects ss
JOIN exam_board_subjects ebs ON 
  ebs.subject_code = ss.subject_code 
  AND ebs.exam_board_id = (SELECT id FROM exam_boards WHERE code = 'Edexcel')
WHERE ss.exam_board = 'Edexcel';

-- ========================================
-- STEP 5: Delete old Edexcel topics (clean slate)
-- ========================================

-- Delete existing curriculum topics for Edexcel subjects
DELETE FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE exam_board_id = (SELECT id FROM exam_boards WHERE code = 'Edexcel')
    AND is_current = true
);

-- ========================================
-- STEP 6: Migrate Topics (staging → production)
-- ========================================

-- First pass: Insert all topics WITHOUT parent_topic_id (to avoid FK issues)
INSERT INTO curriculum_topics (
  id,
  exam_board_subject_id,
  topic_code,
  topic_name,
  topic_level,
  parent_topic_id,
  sort_order,
  created_at,
  updated_at
)
SELECT 
  st.id, -- Keep same UUID for easier parent mapping
  sim.production_id,
  st.topic_code,
  st.topic_name,
  st.topic_level,
  NULL, -- Will update in second pass
  st.sort_order,
  NOW(),
  NOW()
FROM staging_aqa_topics st
JOIN subject_id_mapping sim ON st.subject_id = sim.staging_id
ON CONFLICT (id) DO UPDATE SET
  exam_board_subject_id = EXCLUDED.exam_board_subject_id,
  topic_code = EXCLUDED.topic_code,
  topic_name = EXCLUDED.topic_name,
  topic_level = EXCLUDED.topic_level,
  sort_order = EXCLUDED.sort_order,
  updated_at = NOW();

-- Second pass: Update parent_topic_id relationships
UPDATE curriculum_topics ct
SET parent_topic_id = st.parent_topic_id,
    updated_at = NOW()
FROM staging_aqa_topics st
WHERE ct.id = st.id
  AND st.parent_topic_id IS NOT NULL;

-- ========================================
-- VERIFICATION QUERIES
-- ========================================

-- Count migrated subjects
SELECT 
  'Subjects Migrated' as metric,
  COUNT(*) as count
FROM exam_board_subjects
WHERE exam_board_id = (SELECT id FROM exam_boards WHERE code = 'Edexcel')
  AND is_current = true;

-- Count migrated topics by qualification
SELECT 
  qt.code as qualification,
  COUNT(ct.id) as topics,
  MAX(ct.topic_level) as max_depth
FROM curriculum_topics ct
JOIN exam_board_subjects ebs ON ct.exam_board_subject_id = ebs.id
JOIN qualification_types qt ON ebs.qualification_type_id = qt.id
WHERE ebs.exam_board_id = (SELECT id FROM exam_boards WHERE code = 'Edexcel')
  AND ebs.is_current = true
GROUP BY qt.code;

-- Check hierarchy integrity (orphaned topics)
SELECT 
  'Orphaned Topics' as issue,
  COUNT(*) as count
FROM curriculum_topics ct
WHERE ct.parent_topic_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM curriculum_topics parent 
    WHERE parent.id = ct.parent_topic_id
  )
  AND ct.exam_board_subject_id IN (
    SELECT id FROM exam_board_subjects 
    WHERE exam_board_id = (SELECT id FROM exam_boards WHERE code = 'Edexcel')
  );

-- Show sample subjects and topic counts
SELECT 
  ebs.subject_code,
  ebs.subject_name,
  COUNT(ct.id) as topics,
  MAX(ct.topic_level) as max_depth
FROM exam_board_subjects ebs
LEFT JOIN curriculum_topics ct ON ebs.id = ct.exam_board_subject_id
WHERE ebs.exam_board_id = (SELECT id FROM exam_boards WHERE code = 'Edexcel')
  AND ebs.is_current = true
GROUP BY ebs.id, ebs.subject_code, ebs.subject_name
ORDER BY topics DESC
LIMIT 10;

COMMIT;

-- ========================================
-- ROLLBACK IF NEEDED
-- ========================================
-- If something goes wrong, uncomment this:
-- ROLLBACK;

