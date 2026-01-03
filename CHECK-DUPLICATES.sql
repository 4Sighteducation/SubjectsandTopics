-- CHECK FOR DUPLICATE TOPICS

-- 1. For Biology - how many duplicates per topic?
SELECT 
  topic_code,
  topic_name,
  topic_level,
  COUNT(*) as duplicate_count,
  ARRAY_AGG(DISTINCT created_at::date) as creation_dates
FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects WHERE subject_name = 'Biology'
)
AND topic_code IS NOT NULL
GROUP BY topic_code, topic_name, topic_level
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC
LIMIT 20;

-- 2. How many total duplicates across ALL AQA subjects?
WITH duplicates AS (
  SELECT 
    exam_board_subject_id,
    topic_code,
    topic_name,
    topic_level,
    COUNT(*) as dup_count
  FROM curriculum_topics
  WHERE exam_board_subject_id IN (
    SELECT id FROM exam_board_subjects 
    WHERE exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
  )
  AND topic_code IS NOT NULL
  GROUP BY exam_board_subject_id, topic_code, topic_name, topic_level
  HAVING COUNT(*) > 1
)
SELECT 
  SUM(dup_count - 1) as total_duplicates  -- Subtract 1 because we want to keep one
FROM duplicates;

-- 3. What Biology SHOULD have (unique topics only)
SELECT 
  COUNT(DISTINCT (topic_code, topic_level)) as unique_topics
FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects WHERE subject_name = 'Biology'
)
AND topic_code IS NOT NULL;




















