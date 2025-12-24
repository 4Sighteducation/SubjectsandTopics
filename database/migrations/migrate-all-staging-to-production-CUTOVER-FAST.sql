-- MIGRATE ALL STAGING DATA TO PRODUCTION (FAST CUTOVER - NO LIVE USERS)
-- ================================================================
-- Use this when you have NO LIVE USERS and want a reliable cutover
-- that won't time out in the Supabase SQL editor.
--
-- Key differences vs migrate-all-staging-to-production-FIXED.sql:
-- - Uses TRUNCATE curriculum_topics CASCADE instead of large DELETE
--   (avoids long-running deletes/timeouts; embeddings are restored separately)
-- - Uses TEMP mapping table (doesn't persist if anything fails)
--
-- IMPORTANT:
-- - This will remove curriculum_topics (and cascade-delete topic_ai_metadata etc).
--   Use FLASH/supabase/CUTOVER-PRESERVE-EMBEDDINGS.sql to backup + restore metadata.
-- ================================================================

BEGIN;

-- ================================================================
-- IMPORTANT (psql + Supabase pooler):
-- Some environments have a low default statement_timeout which can
-- abort long-running TRUNCATE ... CASCADE / bulk INSERT operations.
-- Disable timeouts for this cutover transaction to avoid rollbacks.
-- ================================================================
SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;

-- ========================================
-- STEP 1: Ensure exam boards exist
-- ========================================
INSERT INTO exam_boards (code, full_name, active, country)
VALUES
  ('AQA', 'Assessment and Qualifications Alliance', true, 'UK'),
  ('OCR', 'Oxford, Cambridge and RSA', true, 'UK'),
  ('WJEC', 'Welsh Joint Education Committee', true, 'UK'),
  ('EDUQAS', 'WJEC Eduqas', true, 'UK'),
  ('CCEA', 'Council for Curriculum, Examinations & Assessment', true, 'UK'),
  ('SQA', 'Scottish Qualifications Authority', true, 'UK'),
  ('EDEXCEL', 'Pearson Edexcel', true, 'UK')
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
  ('CAMBRIDGE_TECHNICALS_L3', 'Cambridge Technicals (Level 3)'),
  ('CAMBRIDGE_NATIONALS_L2', 'Cambridge Nationals (Level 2)'),
  ('BTEC_NATIONALS_L3', 'BTEC Nationals (Level 3)'),
  ('NATIONAL_5', 'National 5'),
  ('HIGHER', 'Higher'),
  ('ADVANCED_HIGHER', 'Advanced Higher'),
  ('LEVEL_3_EXTENDED_PROJECT', 'Level 3 Extended Project')
ON CONFLICT (code) DO UPDATE SET
  name = EXCLUDED.name;

-- ========================================
-- STEP 3: Mark old subjects as archived (for boards present in staging)
-- ========================================
DO $$
DECLARE
  exam_board_name TEXT;
BEGIN
  FOR exam_board_name IN
    SELECT DISTINCT
      CASE
        WHEN UPPER(TRIM(exam_board)) IN ('WJEC (EDUQAS)', 'WJEC EDUQAS', 'EDUQAS (WJEC)') THEN 'EDUQAS'
        WHEN UPPER(TRIM(exam_board)) = 'EDEXCEL' THEN 'EDEXCEL'
        ELSE UPPER(TRIM(exam_board))
      END AS exam_board
    FROM staging_aqa_subjects
    WHERE exam_board IS NOT NULL
  LOOP
    UPDATE exam_board_subjects
    SET is_current = false,
        updated_at = NOW()
    WHERE exam_board_id = (SELECT id FROM exam_boards WHERE code = exam_board_name)
      AND is_current = true;
  END LOOP;
END $$;

-- ========================================
-- STEP 4: Upsert ALL Subjects (staging → production)
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
  eb.id AS exam_board_id,
  qt.id AS qualification_type_id,
  true,
  NOW(),
  NOW()
FROM staging_aqa_subjects ss
JOIN exam_boards eb ON eb.code =
  CASE
    WHEN UPPER(TRIM(ss.exam_board)) IN ('WJEC (EDUQAS)', 'WJEC EDUQAS', 'EDUQAS (WJEC)') THEN 'EDUQAS'
    WHEN UPPER(TRIM(ss.exam_board)) = 'EDEXCEL' THEN 'EDEXCEL'
    ELSE UPPER(TRIM(ss.exam_board))
  END
JOIN qualification_types qt ON qt.code =
  CASE
    WHEN ss.qualification_type = 'A-Level' THEN 'A_LEVEL'
    WHEN ss.qualification_type = 'GCSE' THEN 'GCSE'
    WHEN ss.qualification_type IN ('International-GCSE', 'International GCSE') THEN 'INTERNATIONAL_GCSE'
    WHEN ss.qualification_type IN ('International-A-Level', 'International A Level', 'International A Level ') THEN 'INTERNATIONAL_A_LEVEL'
    WHEN ss.qualification_type = 'A_LEVEL' THEN 'A_LEVEL'
    WHEN ss.qualification_type = 'INTERNATIONAL_GCSE' THEN 'INTERNATIONAL_GCSE'
    WHEN ss.qualification_type = 'INTERNATIONAL_A_LEVEL' THEN 'INTERNATIONAL_A_LEVEL'
    WHEN ss.qualification_type = 'CAMBRIDGE_TECHNICALS_L3' THEN 'CAMBRIDGE_TECHNICALS_L3'
    WHEN ss.qualification_type = 'CAMBRIDGE_NATIONALS_L2' THEN 'CAMBRIDGE_NATIONALS_L2'
    WHEN ss.qualification_type = 'BTEC_NATIONALS_L3' THEN 'BTEC_NATIONALS_L3'
    WHEN ss.qualification_type = 'National 5' THEN 'NATIONAL_5'
    WHEN ss.qualification_type = 'Higher' THEN 'HIGHER'
    WHEN ss.qualification_type = 'Advanced Higher' THEN 'ADVANCED_HIGHER'
    WHEN ss.qualification_type = 'Level 3 Extended Project' THEN 'LEVEL_3_EXTENDED_PROJECT'
    ELSE 'A_LEVEL'
  END
WHERE ss.exam_board IS NOT NULL
ON CONFLICT (subject_code, exam_board_id, qualification_type_id)
DO UPDATE SET
  subject_name = EXCLUDED.subject_name,
  is_current = true,
  updated_at = NOW();

-- ========================================
-- STEP 5: TEMP subject id mapping (staging → production)
-- ========================================
CREATE TEMP TABLE temp_subject_id_mapping AS
SELECT
  ss.id AS staging_id,
  ebs.id AS production_id,
  ss.subject_code,
  ss.exam_board,
  ss.qualification_type
FROM staging_aqa_subjects ss
JOIN exam_boards eb ON eb.code =
  CASE
    WHEN UPPER(TRIM(ss.exam_board)) IN ('WJEC (EDUQAS)', 'WJEC EDUQAS', 'EDUQAS (WJEC)') THEN 'EDUQAS'
    WHEN UPPER(TRIM(ss.exam_board)) = 'EDEXCEL' THEN 'EDEXCEL'
    ELSE UPPER(TRIM(ss.exam_board))
  END
JOIN qualification_types qt ON qt.code =
  CASE
    WHEN ss.qualification_type = 'A-Level' THEN 'A_LEVEL'
    WHEN ss.qualification_type = 'GCSE' THEN 'GCSE'
    WHEN ss.qualification_type IN ('International-GCSE', 'International GCSE') THEN 'INTERNATIONAL_GCSE'
    WHEN ss.qualification_type IN ('International-A-Level', 'International A Level', 'International A Level ') THEN 'INTERNATIONAL_A_LEVEL'
    WHEN ss.qualification_type = 'A_LEVEL' THEN 'A_LEVEL'
    WHEN ss.qualification_type = 'INTERNATIONAL_GCSE' THEN 'INTERNATIONAL_GCSE'
    WHEN ss.qualification_type = 'INTERNATIONAL_A_LEVEL' THEN 'INTERNATIONAL_A_LEVEL'
    WHEN ss.qualification_type = 'CAMBRIDGE_TECHNICALS_L3' THEN 'CAMBRIDGE_TECHNICALS_L3'
    WHEN ss.qualification_type = 'CAMBRIDGE_NATIONALS_L2' THEN 'CAMBRIDGE_NATIONALS_L2'
    WHEN ss.qualification_type = 'BTEC_NATIONALS_L3' THEN 'BTEC_NATIONALS_L3'
    WHEN ss.qualification_type = 'National 5' THEN 'NATIONAL_5'
    WHEN ss.qualification_type = 'Higher' THEN 'HIGHER'
    WHEN ss.qualification_type = 'Advanced Higher' THEN 'ADVANCED_HIGHER'
    WHEN ss.qualification_type = 'Level 3 Extended Project' THEN 'LEVEL_3_EXTENDED_PROJECT'
    ELSE 'A_LEVEL'
  END
JOIN exam_board_subjects ebs ON
  ebs.subject_code = ss.subject_code
  AND ebs.exam_board_id = eb.id
  AND ebs.qualification_type_id = qt.id
WHERE ss.exam_board IS NOT NULL;

-- ========================================
-- STEP 6: FAST RESET topics
-- ========================================
-- This is the key: avoids a huge DELETE that often times out in Supabase SQL editor.
TRUNCATE TABLE curriculum_topics CASCADE;

-- ========================================
-- STEP 7: Migrate ALL Topics (staging → production)
-- ========================================
WITH topics_normalized AS (
  SELECT
    st.id,
    sim.production_id AS exam_board_subject_id,
    st.topic_code,
    st.topic_level,
    st.subject_id,
    regexp_replace(coalesce(st.topic_name, ''), E'\\s+', ' ', 'g') AS norm_name
  FROM staging_aqa_topics st
  JOIN temp_subject_id_mapping sim ON st.subject_id = sim.staging_id
),
topics_capped AS (
  SELECT
    id,
    exam_board_subject_id,
    topic_code,
    topic_level,
    subject_id,
    CASE
      WHEN length(norm_name) > 350 THEN left(norm_name, 350) || '…'
      ELSE norm_name
    END AS base_name
  FROM topics_normalized
),
duplicate_check AS (
  -- Detect duplicates AFTER normalization + capping (these are the names that hit the unique index)
  SELECT
    exam_board_subject_id,
    base_name,
    topic_level,
    COUNT(*) AS dup_count
  FROM topics_capped
  GROUP BY exam_board_subject_id, base_name, topic_level
),
topics_with_unique_names AS (
  SELECT
    tc.id,
    tc.exam_board_subject_id,
    tc.topic_code,
    CASE
      WHEN dc.dup_count > 1 THEN tc.base_name || ' [' || tc.topic_code || ']'
      ELSE tc.base_name
    END AS topic_name,
    tc.topic_level,
    ROW_NUMBER() OVER (PARTITION BY tc.subject_id ORDER BY tc.topic_level, tc.topic_code, tc.id) AS sort_order
  FROM topics_capped tc
  LEFT JOIN duplicate_check dc ON
    dc.exam_board_subject_id = tc.exam_board_subject_id
    AND dc.base_name = tc.base_name
    AND dc.topic_level = tc.topic_level
)
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
  id,
  exam_board_subject_id,
  topic_code,
  topic_name,
  topic_level,
  NULL,
  sort_order,
  NOW()
FROM topics_with_unique_names;

-- Second pass: Update parent_topic_id relationships
UPDATE curriculum_topics ct
SET parent_topic_id = st.parent_topic_id
FROM staging_aqa_topics st
WHERE ct.id = st.id
  AND st.parent_topic_id IS NOT NULL;

-- ========================================
-- VERIFICATION QUICK CHECKS
-- ========================================
SELECT
  'CUTOVER SUMMARY' AS metric,
  COUNT(DISTINCT ebs.id) AS total_subjects,
  COUNT(ct.id) AS total_topics,
  COUNT(DISTINCT eb.code) AS exam_boards_count
FROM exam_board_subjects ebs
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
LEFT JOIN curriculum_topics ct ON ebs.id = ct.exam_board_subject_id
WHERE ebs.is_current = true;

SELECT
  'ORPHAN TOPICS' AS metric,
  COUNT(*) AS orphaned_count
FROM curriculum_topics ct
WHERE ct.parent_topic_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM curriculum_topics parent
    WHERE parent.id = ct.parent_topic_id
  );

COMMIT;


