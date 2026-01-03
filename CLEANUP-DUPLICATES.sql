-- CLEANUP DUPLICATE DATA IN SUPABASE
-- Run this before the full batch to start clean

-- 1. Remove duplicate components (keep the newest for each component_code)
WITH ranked_components AS (
  SELECT id, 
         ROW_NUMBER() OVER (
           PARTITION BY spec_metadata_id, component_code 
           ORDER BY created_at DESC
         ) as rn
  FROM spec_components
  WHERE spec_metadata_id = '6980f08d-71f8-48c6-a0ce-510d12794a7d'
)
DELETE FROM spec_components
WHERE id IN (
  SELECT id FROM ranked_components WHERE rn > 1
);

-- 2. Remove duplicate constraints (keep the newest for each type+description combo)
WITH ranked_constraints AS (
  SELECT id,
         ROW_NUMBER() OVER (
           PARTITION BY spec_metadata_id, constraint_type, description
           ORDER BY created_at DESC
         ) as rn
  FROM selection_constraints
  WHERE spec_metadata_id = '6980f08d-71f8-48c6-a0ce-510d12794a7d'
)
DELETE FROM selection_constraints
WHERE id IN (
  SELECT id FROM ranked_constraints WHERE rn > 1
);

-- 3. Remove duplicate Level 0 topics (keep the one WITH component_code if exists, otherwise newest)
WITH ranked_topics AS (
  SELECT id,
         topic_code,
         component_code,
         ROW_NUMBER() OVER (
           PARTITION BY exam_board_subject_id, topic_code
           ORDER BY 
             CASE WHEN component_code IS NOT NULL THEN 0 ELSE 1 END,
             created_at DESC
         ) as rn
  FROM curriculum_topics
  WHERE exam_board_subject_id IN (
    SELECT id FROM exam_board_subjects WHERE subject_name = 'History'
  )
  AND topic_level = 0
)
DELETE FROM curriculum_topics
WHERE id IN (
  SELECT id FROM ranked_topics WHERE rn > 1
);

-- 4. Verify cleanup
SELECT 'Components after cleanup:' as status, COUNT(*) as count
FROM spec_components
WHERE spec_metadata_id = '6980f08d-71f8-48c6-a0ce-510d12794a7d'
UNION ALL
SELECT 'Constraints after cleanup:', COUNT(*)
FROM selection_constraints
WHERE spec_metadata_id = '6980f08d-71f8-48c6-a0ce-510d12794a7d'
UNION ALL
SELECT 'Level 0 topics after cleanup:', COUNT(*)
FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects WHERE subject_name = 'History'
)
AND topic_level = 0;





