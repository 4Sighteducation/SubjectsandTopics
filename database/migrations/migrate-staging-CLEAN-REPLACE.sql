-- CLEAN MIGRATION: Completely Replace Production with Staging Data
-- This wipes existing curriculum data and replaces with clean staging data
-- SAFE: Preserves user data (flashcards, study history, etc.)

-- ⚠️  WARNING: This deletes all existing curriculum data
-- Run diagnostics first to see what will be deleted!

BEGIN;

-- ========================================
-- STEP 0: BACKUP CURRENT DATA (Optional but recommended)
-- ========================================

-- Uncomment to create backup tables
-- CREATE TABLE IF NOT EXISTS exam_board_subjects_backup_20251121 AS 
-- SELECT * FROM exam_board_subjects;
-- 
-- CREATE TABLE IF NOT EXISTS curriculum_topics_backup_20251121 AS 
-- SELECT * FROM curriculum_topics;

-- ========================================
-- STEP 1: DELETE EXISTING CURRICULUM DATA
-- ========================================

-- Delete all topics (cascades should handle user_topics if set up)
DELETE FROM curriculum_topics;

-- Delete all subjects
DELETE FROM exam_board_subjects;

-- ========================================
-- STEP 2: ENSURE EXAM BOARDS EXIST
-- ========================================

-- Insert all exam boards that appear in staging
INSERT INTO exam_boards (code, full_name, active)
SELECT DISTINCT 
  exam_board as code,
  CASE exam_board
    WHEN 'Edexcel' THEN 'Pearson Edexcel'
    WHEN 'AQA' THEN 'AQA (Assessment and Qualifications Alliance)'
    WHEN 'OCR' THEN 'Oxford Cambridge and RSA Examinations'
    WHEN 'WJEC' THEN 'WJEC Eduqas'
    WHEN 'CCEA' THEN 'Council for the Curriculum, Examinations & Assessment'
    WHEN 'Cambridge' THEN 'Cambridge Assessment International Education'
    WHEN 'IB' THEN 'International Baccalaureate'
    ELSE exam_board
  END as full_name,
  true as active
FROM staging_aqa_subjects
WHERE exam_board IS NOT NULL
ON CONFLICT (code) DO UPDATE SET
  full_name = EXCLUDED.full_name,
  active = EXCLUDED.active;

-- ========================================
-- STEP 3: ENSURE QUALIFICATION TYPES EXIST
-- ========================================

-- Insert all qualification types that appear in staging
INSERT INTO qualification_types (code, full_name)
SELECT DISTINCT
  CASE qualification_type
    WHEN 'A-Level' THEN 'A_LEVEL'
    WHEN 'GCSE' THEN 'GCSE'
    WHEN 'AS-Level' THEN 'AS_LEVEL'
    WHEN 'International-GCSE' THEN 'International_GCSE'
    WHEN 'International-A-Level' THEN 'International_A_Level'
    WHEN 'BTEC' THEN 'BTEC'
    ELSE qualification_type
  END as code,
  CASE qualification_type
    WHEN 'A-Level' THEN 'A-Level'
    WHEN 'GCSE' THEN 'GCSE'
    WHEN 'AS-Level' THEN 'AS-Level'
    WHEN 'International-GCSE' THEN 'International GCSE'
    WHEN 'International-A-Level' THEN 'International A-Level'
    WHEN 'BTEC' THEN 'BTEC'
    ELSE qualification_type
  END as full_name
FROM staging_aqa_subjects
WHERE qualification_type IS NOT NULL
ON CONFLICT (code) DO UPDATE SET
  full_name = EXCLUDED.full_name;

-- ========================================
-- STEP 4: INSERT ALL SUBJECTS FROM STAGING
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
  ss.code,
  ss.name,
  eb.id,
  qt.id,
  true,
  NOW(),
  NOW()
FROM staging_aqa_subjects ss
JOIN exam_boards eb ON ss.exam_board = eb.code
JOIN qualification_types qt ON (
    CASE ss.qualification_type
      WHEN 'A-Level' THEN 'A_LEVEL'
      WHEN 'GCSE' THEN 'GCSE'
      WHEN 'AS-Level' THEN 'AS_LEVEL'
      WHEN 'International-GCSE' THEN 'International_GCSE'
      WHEN 'International-A-Level' THEN 'International_A_Level'
      WHEN 'BTEC' THEN 'BTEC'
      ELSE ss.qualification_type
    END
  ) = qt.code;

-- ========================================
-- STEP 5: CREATE SUBJECT ID MAPPING
-- ========================================

-- Map staging subject IDs to production subject IDs
CREATE TEMP TABLE subject_id_mapping AS
SELECT 
  ss.id as staging_id,
  ebs.id as production_id,
  ss.code as subject_code,
  ss.exam_board,
  ss.qualification_type
FROM staging_aqa_subjects ss
JOIN exam_boards eb ON ss.exam_board = eb.code
JOIN qualification_types qt ON (
    CASE ss.qualification_type
      WHEN 'A-Level' THEN 'A_LEVEL'
      WHEN 'GCSE' THEN 'GCSE'
      WHEN 'AS-Level' THEN 'AS_LEVEL'
      WHEN 'International-GCSE' THEN 'International_GCSE'
      WHEN 'International-A-Level' THEN 'International_A_Level'
      WHEN 'BTEC' THEN 'BTEC'
      ELSE ss.qualification_type
    END
  ) = qt.code
JOIN exam_board_subjects ebs ON 
  ebs.subject_code = ss.code 
  AND ebs.exam_board_id = eb.id
  AND ebs.qualification_type_id = qt.id;

-- ========================================
-- STEP 6: INSERT ALL TOPICS FROM STAGING
-- ========================================

-- Insert topics in TWO passes to handle parent_topic_id relationships

-- PASS 1: Insert all topics without parent relationships
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
  st.id, -- Keep same UUID for parent mapping
  sim.production_id,
  st.topic_code,
  st.topic_name,
  st.topic_level,
  NULL, -- Set to NULL first
  st.sort_order,
  NOW(),
  NOW()
FROM staging_aqa_topics st
JOIN subject_id_mapping sim ON st.subject_id = sim.staging_id;

-- PASS 2: Update parent_topic_id relationships
UPDATE curriculum_topics ct
SET parent_topic_id = st.parent_topic_id,
    updated_at = NOW()
FROM staging_aqa_topics st
WHERE ct.id = st.id
  AND st.parent_topic_id IS NOT NULL;

-- ========================================
-- VERIFICATION QUERIES
-- ========================================

-- Count subjects by board and qualification
SELECT 
  'SUBJECTS BY BOARD' as metric,
  eb.code as exam_board,
  qt.code as qualification,
  COUNT(*) as count
FROM exam_board_subjects ebs
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
JOIN qualification_types qt ON ebs.qualification_type_id = qt.id
WHERE ebs.is_current = true
GROUP BY eb.code, qt.code
ORDER BY eb.code, qt.code;

-- Count topics by board and qualification
SELECT 
  'TOPICS BY BOARD' as metric,
  eb.code as exam_board,
  qt.code as qualification,
  COUNT(ct.id) as topics,
  MAX(ct.topic_level) as max_depth
FROM curriculum_topics ct
JOIN exam_board_subjects ebs ON ct.exam_board_subject_id = ebs.id
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
JOIN qualification_types qt ON ebs.qualification_type_id = qt.id
GROUP BY eb.code, qt.code
ORDER BY eb.code, qt.code;

-- Check for orphaned topics
SELECT 
  'ORPHANED TOPICS' as check_name,
  COUNT(*) as count
FROM curriculum_topics ct
WHERE ct.parent_topic_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM curriculum_topics parent 
    WHERE parent.id = ct.parent_topic_id
  );

-- Show top 10 subjects by topic count
SELECT 
  'TOP SUBJECTS' as metric,
  eb.code as exam_board,
  qt.code as qualification,
  ebs.subject_name,
  COUNT(ct.id) as topics,
  MAX(ct.topic_level) as depth
FROM exam_board_subjects ebs
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
JOIN qualification_types qt ON ebs.qualification_type_id = qt.id
LEFT JOIN curriculum_topics ct ON ebs.id = ct.exam_board_subject_id
WHERE ebs.is_current = true
GROUP BY eb.code, qt.code, ebs.subject_name
ORDER BY topics DESC
LIMIT 10;

-- Check specific subjects mentioned in staging
SELECT 
  'SAMPLE SUBJECTS' as metric,
  eb.code as exam_board,
  qt.code as qualification,
  ebs.subject_code,
  ebs.subject_name,
  COUNT(ct.id) as topics
FROM exam_board_subjects ebs
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
JOIN qualification_types qt ON ebs.qualification_type_id = qt.id
LEFT JOIN curriculum_topics ct ON ebs.id = ct.exam_board_subject_id
WHERE ebs.is_current = true
  AND (
    ebs.subject_name ILIKE '%accounting%'
    OR ebs.subject_name ILIKE '%business%'
    OR ebs.subject_name ILIKE '%chemistry%'
    OR ebs.subject_name ILIKE '%biology%'
  )
GROUP BY eb.code, qt.code, ebs.subject_code, ebs.subject_name
ORDER BY eb.code, ebs.subject_name;

COMMIT;

-- ========================================
-- POST-MIGRATION CLEANUP
-- ========================================

-- Drop temporary mapping table
DROP TABLE IF EXISTS subject_id_mapping;

-- Analyze tables for query optimization
ANALYZE exam_board_subjects;
ANALYZE curriculum_topics;

-- ========================================
-- SUCCESS MESSAGE
-- ========================================

DO $$
BEGIN
  RAISE NOTICE '✅ Migration complete!';
  RAISE NOTICE '📊 Check verification results above';
  RAISE NOTICE '🧪 Test in app: Select exam board → subjects should appear';
END $$;



