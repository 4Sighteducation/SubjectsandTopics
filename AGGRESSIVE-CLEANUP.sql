-- AGGRESSIVE CLEANUP - Delete OLD topics, keep only NEW ones from yesterday's batch
-- WARNING: This deletes all topics created before Sept 30, 2025

-- First, let's see what we'd be deleting
SELECT 
  'Topics created before 2025-09-30' as category,
  COUNT(*) as count
FROM curriculum_topics
WHERE created_at < '2025-09-30'
AND exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
)
UNION ALL
SELECT 
  'Topics created ON 2025-09-30',
  COUNT(*)
FROM curriculum_topics
WHERE created_at >= '2025-09-30'
AND exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
);

-- If you're happy with the counts above, run this to DELETE old topics:
/*
DELETE FROM curriculum_topics
WHERE created_at < '2025-09-30'
AND exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
);
*/

-- Then clean duplicates from yesterday's multiple runs:
/*
WITH ranked_topics AS (
  SELECT id,
         ROW_NUMBER() OVER (
           PARTITION BY exam_board_subject_id, topic_code, topic_level
           ORDER BY 
             CASE WHEN component_code IS NOT NULL THEN 0 ELSE 1 END,
             CASE WHEN geographical_region IS NOT NULL THEN 0 ELSE 1 END,
             created_at DESC
         ) as rn
  FROM curriculum_topics
  WHERE topic_code IS NOT NULL
  AND created_at >= '2025-09-30'
)
DELETE FROM curriculum_topics
WHERE id IN (
  SELECT id FROM ranked_topics WHERE rn > 1
);
*/

-- ========================================
-- ALTERNATIVE: Just show unique count
-- ========================================
-- Don't delete, just see what the CLEAN count would be
SELECT 
  'Unique topics (what it SHOULD be)' as metric,
  COUNT(DISTINCT (exam_board_subject_id, COALESCE(topic_code, topic_name), topic_level)) as count
FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
);




















