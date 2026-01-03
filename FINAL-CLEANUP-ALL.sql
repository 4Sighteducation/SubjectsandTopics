-- COMPREHENSIVE CLEANUP OF ALL DUPLICATES
-- WARNING: This will delete thousands of duplicate records
-- Run this to get clean data before using in your app

-- ========================================
-- 1. CLEAN COMPONENTS (keep newest)
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
-- 2. CLEAN CONSTRAINTS (keep newest)
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
-- 3. CLEAN TOPICS (KEEP BEST VERSION)
-- ========================================
-- Priority: Keep version WITH component_code if exists, otherwise newest
WITH ranked_topics AS (
  SELECT id,
         ROW_NUMBER() OVER (
           PARTITION BY exam_board_subject_id, topic_code, topic_level
           ORDER BY 
             CASE WHEN component_code IS NOT NULL THEN 0 ELSE 1 END,
             CASE WHEN geographical_region IS NOT NULL THEN 0 ELSE 1 END,
             CASE WHEN chronological_period IS NOT NULL THEN 0 ELSE 1 END,
             created_at DESC
         ) as rn
  FROM curriculum_topics
  WHERE topic_code IS NOT NULL
)
DELETE FROM curriculum_topics
WHERE id IN (
  SELECT id FROM ranked_topics WHERE rn > 1
);

-- ========================================
-- VERIFY CLEANUP
-- ========================================
SELECT 
  'Components (should be ~200)' as item,
  COUNT(*) as count
FROM spec_components
UNION ALL
SELECT 
  'Constraints (should be ~150)',
  COUNT(*)
FROM selection_constraints
UNION ALL
SELECT
  'Topics with codes (should be ~2000)',
  COUNT(*)
FROM curriculum_topics
WHERE topic_code IS NOT NULL
UNION ALL
SELECT
  'History topics (should be ~150)',
  COUNT(*)
FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects WHERE subject_name = 'History'
);




















