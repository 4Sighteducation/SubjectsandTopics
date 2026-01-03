-- SAFE CLEANUP - Handles parent-child relationships
-- This version won't break the topic hierarchy

-- ========================================
-- 1. CLEAN COMPONENTS (safe - no dependencies)
-- ========================================
WITH ranked_components AS (
  SELECT id,
         ROW_NUMBER() OVER (
           PARTITION BY spec_metadata_id, component_code
           ORDER BY created_at DESC
         ) as rn
  FROM spec_components
)
DELETE FROM spec_components
WHERE id IN (
  SELECT id FROM ranked_components WHERE rn > 1
);

-- ========================================
-- 2. CLEAN CONSTRAINTS (safe - no dependencies)
-- ========================================
WITH ranked_constraints AS (
  SELECT id,
         ROW_NUMBER() OVER (
           PARTITION BY spec_metadata_id, constraint_type, description
           ORDER BY created_at DESC
         ) as rn
  FROM selection_constraints
)
DELETE FROM selection_constraints
WHERE id IN (
  SELECT id FROM ranked_constraints WHERE rn > 1
);

-- ========================================
-- 3. CLEAN TOPICS - DIFFERENT APPROACH
--    Instead of deleting, let's just use VIEWS
-- ========================================

-- Create a view that shows only the BEST version of each topic
CREATE OR REPLACE VIEW curriculum_topics_clean AS
SELECT DISTINCT ON (exam_board_subject_id, topic_code, topic_level)
  *
FROM curriculum_topics
WHERE topic_code IS NOT NULL
ORDER BY 
  exam_board_subject_id,
  topic_code,
  topic_level,
  CASE WHEN component_code IS NOT NULL THEN 0 ELSE 1 END,
  CASE WHEN geographical_region IS NOT NULL THEN 0 ELSE 1 END,
  created_at DESC;

-- Now use this VIEW in your app instead of the table directly
-- This gives you clean data without deleting anything!

-- ========================================
-- VERIFY WHAT THE VIEW SHOWS
-- ========================================
SELECT 
  'Topics in view (should be ~2000)' as item,
  COUNT(*) as count
FROM curriculum_topics_clean
UNION ALL
SELECT
  'History topics in view (should be ~150)',
  COUNT(*)
FROM curriculum_topics_clean
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects WHERE subject_name = 'History'
  AND exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
);




















