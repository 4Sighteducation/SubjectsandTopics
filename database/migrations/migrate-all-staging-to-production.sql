-- MIGRATE ALL STAGING DATA TO PRODUCTION
-- This migrates ALL exam boards from staging_aqa_* tables to production
-- Handles: AQA, Edexcel, OCR, WJEC, CCEA, SQA, CIE, EDUQAS
-- Run this in Supabase SQL Editor

BEGIN;

-- ========================================
-- STEP 1: Ensure ALL exam boards exist
-- ========================================
INSERT INTO exam_boards (code, full_name, active, country)
VALUES 
  ('AQA', 'Assessment and Qualifications Alliance', true, 'UK'),
  ('Edexcel', 'Pearson Edexcel', true, 'UK'),
  ('EDEXCEL', 'Pearson Edexcel', true, 'UK'),
  ('OCR', 'Oxford, Cambridge and RSA', true, 'UK'),
  ('WJEC', 'Welsh Joint Education Committee', true, 'UK'),
  ('EDUQAS', 'WJEC Eduqas', true, 'UK'),
  ('CCEA', 'Council for Curriculum, Examinations & Assessment', true, 'UK'),
  ('CIE', 'Cambridge International Examinations', true, 'International'),
  ('SQA', 'Scottish Qualifications Authority', true, 'UK')
ON CONFLICT (code) DO UPDATE SET
  full_name = EXCLUDED.full_name,
  active = EXCLUDED.active;

-- ========================================
-- STEP 2: Ensure ALL qualification types exist
-- ========================================
INSERT INTO qualification_types (code, name)
VALUES 
  ('A_LEVEL', 'A-Level'),
  ('GCSE', 'GCSE'),
  ('INTERNATIONAL_GCSE', 'International GCSE'),
  ('INTERNATIONAL_A_LEVEL', 'International A-Level'),
  ('CAMBRIDGE_TECHNICALS_L3', 'Cambridge Technicals (Level 3)'),
  ('CAMBRIDGE_NATIONALS_L2', 'Cambridge Nationals (Level 2)'),
  ('BTEC_NATIONALS_L3', 'BTEC Nationals (Level 3)'),
  ('NATIONAL_5', 'National 5'),
  ('HIGHER', 'Higher'),
  ('ADVANCED_HIGHER', 'Advanced Higher')
ON CONFLICT (code) DO UPDATE SET
  name = EXCLUDED.name;

-- ========================================
-- STEP 3: Get list of exam boards in staging
-- ========================================
DO $$
DECLARE
  exam_board_name TEXT;
BEGIN
  -- Loop through each unique exam board in staging
  FOR exam_board_name IN 
    SELECT DISTINCT exam_board 
    FROM staging_aqa_subjects 
    WHERE exam_board IS NOT NULL
  LOOP
    RAISE NOTICE 'Processing exam board: %', exam_board_name;
    
    -- Mark old subjects for this board as not current
    UPDATE exam_board_subjects
    SET is_current = false,
        updated_at = NOW()
    WHERE exam_board_id = (SELECT id FROM exam_boards WHERE code = exam_board_name)
      AND is_current = true;
      
  END LOOP;
END $$;

-- ========================================
-- STEP 4: Migrate ALL Subjects (staging → production)
-- ========================================

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
  eb.id as exam_board_id,
  qt.id as qualification_type_id,
  true,
  NOW(),
  NOW()
FROM staging_aqa_subjects ss
JOIN exam_boards eb ON eb.code = ss.exam_board
JOIN qualification_types qt ON qt.code = 
  CASE 
    WHEN ss.qualification_type = 'A-Level' THEN 'A_LEVEL'
    WHEN ss.qualification_type = 'GCSE' THEN 'GCSE'
    WHEN ss.qualification_type = 'International-GCSE' THEN 'INTERNATIONAL_GCSE'
    WHEN ss.qualification_type = 'International GCSE' THEN 'INTERNATIONAL_GCSE'
    WHEN ss.qualification_type = 'International-A-Level' THEN 'INTERNATIONAL_A_LEVEL'
    WHEN ss.qualification_type = 'International A Level' THEN 'INTERNATIONAL_A_LEVEL'
    WHEN ss.qualification_type = 'A_LEVEL' THEN 'A_LEVEL'
    WHEN ss.qualification_type = 'INTERNATIONAL_GCSE' THEN 'INTERNATIONAL_GCSE'
    WHEN ss.qualification_type = 'INTERNATIONAL_A_LEVEL' THEN 'INTERNATIONAL_A_LEVEL'
    WHEN ss.qualification_type = 'CAMBRIDGE_TECHNICALS_L3' THEN 'CAMBRIDGE_TECHNICALS_L3'
    WHEN ss.qualification_type = 'CAMBRIDGE_NATIONALS_L2' THEN 'CAMBRIDGE_NATIONALS_L2'
    WHEN ss.qualification_type = 'BTEC_NATIONALS_L3' THEN 'BTEC_NATIONALS_L3'
    WHEN ss.qualification_type = 'National 5' THEN 'NATIONAL_5'
    WHEN ss.qualification_type = 'Higher' THEN 'HIGHER'
    WHEN ss.qualification_type = 'Advanced Higher' THEN 'ADVANCED_HIGHER'
    ELSE 'A_LEVEL'
  END
WHERE ss.exam_board IS NOT NULL
ON CONFLICT (subject_code, exam_board_id, qualification_type_id) 
DO UPDATE SET
  subject_name = EXCLUDED.subject_name,
  is_current = true,
  updated_at = NOW();

-- ========================================
-- STEP 5: Create temporary mapping table for ALL boards
-- ========================================

DROP TABLE IF EXISTS temp_subject_id_mapping;

CREATE TABLE temp_subject_id_mapping AS
SELECT 
  ss.id as staging_id,
  ebs.id as production_id,
  ss.subject_code,
  ss.exam_board
FROM staging_aqa_subjects ss
JOIN exam_boards eb ON eb.code = ss.exam_board
JOIN exam_board_subjects ebs ON 
  ebs.subject_code = ss.subject_code 
  AND ebs.exam_board_id = eb.id
WHERE ss.exam_board IS NOT NULL;

-- ========================================
-- STEP 6: Delete old topics for all migrated subjects
-- ========================================

DELETE FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT production_id FROM temp_subject_id_mapping
);

-- ========================================
-- STEP 7: Migrate ALL Topics (staging → production)
-- ========================================

-- First pass: Insert all topics WITHOUT parent_topic_id
INSERT INTO curriculum_topics (
  id,
  exam_board_subject_id,
  topic_code,
  topic_name,
  topic_level,
  parent_topic_id,
  sort_order,
  created_at
)
SELECT 
  st.id,
  sim.production_id,
  st.topic_code,
  st.topic_name,
  st.topic_level,
  NULL, -- Will update in second pass
  st.sort_order,
  NOW()
FROM staging_aqa_topics st
JOIN temp_subject_id_mapping sim ON st.subject_id = sim.staging_id
ON CONFLICT (id) DO UPDATE SET
  exam_board_subject_id = EXCLUDED.exam_board_subject_id,
  topic_code = EXCLUDED.topic_code,
  topic_name = EXCLUDED.topic_name,
  topic_level = EXCLUDED.topic_level,
  sort_order = EXCLUDED.sort_order;

-- Second pass: Update parent_topic_id relationships
UPDATE curriculum_topics ct
SET parent_topic_id = st.parent_topic_id
FROM staging_aqa_topics st
WHERE ct.id = st.id
  AND st.parent_topic_id IS NOT NULL;

-- ========================================
-- VERIFICATION QUERIES
-- ========================================

-- Count migrated subjects by exam board
SELECT 
  'Subjects Migrated by Board' as metric,
  eb.code as exam_board,
  qt.code as qualification,
  COUNT(*) as count
FROM exam_board_subjects ebs
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
JOIN qualification_types qt ON ebs.qualification_type_id = qt.id
WHERE ebs.is_current = true
GROUP BY eb.code, qt.code
ORDER BY eb.code, qt.code;

-- Count migrated topics by exam board and qualification
SELECT 
  'Topics Migrated by Board' as metric,
  eb.code as exam_board,
  qt.code as qualification,
  COUNT(ct.id) as topics,
  MAX(ct.topic_level) as max_depth
FROM curriculum_topics ct
JOIN exam_board_subjects ebs ON ct.exam_board_subject_id = ebs.id
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
JOIN qualification_types qt ON ebs.qualification_type_id = qt.id
WHERE ebs.is_current = true
GROUP BY eb.code, qt.code
ORDER BY eb.code, qt.code;

-- Check for orphaned topics
SELECT 
  'Orphaned Topics Check' as metric,
  COUNT(*) as count
FROM curriculum_topics ct
WHERE ct.parent_topic_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM curriculum_topics parent 
    WHERE parent.id = ct.parent_topic_id
  );

-- Show top subjects by topic count
SELECT 
  'Top Subjects by Topics' as metric,
  eb.code as exam_board,
  qt.code as qualification,
  ebs.subject_code,
  ebs.subject_name,
  COUNT(ct.id) as topics,
  MAX(ct.topic_level) as max_depth
FROM exam_board_subjects ebs
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
JOIN qualification_types qt ON ebs.qualification_type_id = qt.id
LEFT JOIN curriculum_topics ct ON ebs.id = ct.exam_board_subject_id
WHERE ebs.is_current = true
GROUP BY eb.code, qt.code, ebs.id, ebs.subject_code, ebs.subject_name
ORDER BY topics DESC
LIMIT 20;

-- Summary totals
SELECT 
  'MIGRATION SUMMARY' as metric,
  COUNT(DISTINCT ebs.id) as total_subjects,
  COUNT(ct.id) as total_topics,
  COUNT(DISTINCT eb.code) as exam_boards_count
FROM exam_board_subjects ebs
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
LEFT JOIN curriculum_topics ct ON ebs.id = ct.exam_board_subject_id
WHERE ebs.is_current = true;

COMMIT;

-- ========================================
-- ROLLBACK IF NEEDED
-- ========================================
-- If something goes wrong, uncomment this:
-- ROLLBACK;

