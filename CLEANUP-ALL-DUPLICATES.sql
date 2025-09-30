-- CLEANUP ALL DUPLICATES ACROSS ALL SUBJECTS
-- Run this before adding unique constraints

-- 1. Remove ALL duplicate components (keep newest for each)
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

-- 2. Remove ALL duplicate constraints
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

-- 3. Remove duplicate topics - Handle parent-child relationships first

-- Step 3a: Set parent_topic_id to NULL for topics we're about to delete
WITH duplicates_to_delete AS (
  SELECT id
  FROM (
    SELECT id,
           ROW_NUMBER() OVER (
             PARTITION BY exam_board_subject_id, COALESCE(topic_code, topic_name), topic_level
             ORDER BY created_at DESC
           ) as rn
    FROM curriculum_topics
  ) ranked
  WHERE rn > 1
)
UPDATE curriculum_topics
SET parent_topic_id = NULL
WHERE parent_topic_id IN (SELECT id FROM duplicates_to_delete);

-- Step 3b: Now delete the duplicates
WITH ranked_topics AS (
  SELECT id,
         ROW_NUMBER() OVER (
           PARTITION BY exam_board_subject_id, COALESCE(topic_code, topic_name), topic_level
           ORDER BY created_at DESC
         ) as rn
  FROM curriculum_topics
)
DELETE FROM curriculum_topics
WHERE id IN (
  SELECT id FROM ranked_topics WHERE rn > 1
);

-- 4. Verify cleanup across all AQA subjects
SELECT 
  'Total components' as item,
  COUNT(*) as count
FROM spec_components
WHERE spec_metadata_id IN (
  SELECT id FROM specification_metadata WHERE exam_board = 'AQA'
)
UNION ALL
SELECT 
  'Total constraints',
  COUNT(*)
FROM selection_constraints
WHERE spec_metadata_id IN (
  SELECT id FROM specification_metadata WHERE exam_board = 'AQA'
)
UNION ALL
SELECT 
  'Total AQA topics with codes',
  COUNT(*)
FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
)
AND topic_code IS NOT NULL;
