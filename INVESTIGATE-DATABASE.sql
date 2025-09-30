-- INVESTIGATE SUPABASE DATABASE
-- Run these queries in Supabase SQL Editor

-- 1. Check if AQA exam board exists
SELECT * FROM exam_boards WHERE code = 'AQA';

-- 2. Check all exam_board_subjects for AQA
SELECT 
  ebs.id,
  ebs.subject_name,
  ebs.subject_code,
  qt.code as qualification_code,
  qt.name as qualification_name,
  COUNT(ct.id) as topic_count
FROM exam_board_subjects ebs
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
LEFT JOIN qualification_types qt ON ebs.qualification_type_id = qt.id
LEFT JOIN curriculum_topics ct ON ct.exam_board_subject_id = ebs.id
WHERE eb.code = 'AQA'
GROUP BY ebs.id, ebs.subject_name, ebs.subject_code, qt.code, qt.name
ORDER BY ebs.subject_name, qt.code;

-- 3. Check specifically for Accounting
SELECT * FROM exam_board_subjects ebs
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
WHERE eb.code = 'AQA' 
AND ebs.subject_name LIKE '%Account%';

-- 4. Check for Art and Design subjects
SELECT * FROM exam_board_subjects ebs
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
WHERE eb.code = 'AQA' 
AND ebs.subject_name LIKE '%Art%';

-- 5. Check what topics we just added (from today's scraping)
SELECT 
  ct.topic_code,
  ct.topic_name,
  ct.topic_level,
  ct.created_at,
  ct.updated_at,
  ebs.subject_name
FROM curriculum_topics ct
JOIN exam_board_subjects ebs ON ct.exam_board_subject_id = ebs.id
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
WHERE eb.code = 'AQA'
AND DATE(ct.created_at) = CURRENT_DATE
ORDER BY ebs.subject_name, ct.topic_code;

-- 6. Count topics by subject for AQA
SELECT 
  ebs.subject_name,
  ebs.subject_code,
  COUNT(ct.id) as topic_count,
  MAX(ct.updated_at) as last_updated
FROM exam_board_subjects ebs
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
LEFT JOIN curriculum_topics ct ON ct.exam_board_subject_id = ebs.id
WHERE eb.code = 'AQA'
GROUP BY ebs.subject_name, ebs.subject_code
ORDER BY topic_count DESC;

-- 7. Check qualification types
SELECT * FROM qualification_types ORDER BY code;

-- 8. Find which subjects are MISSING from exam_board_subjects
-- (Compare with config file - you have 74 subjects but maybe not all in DB)

-- 9. Check if we can create a missing subject
-- First, get the IDs we need:
SELECT id, code FROM exam_boards WHERE code = 'AQA';
SELECT id, code FROM qualification_types WHERE code = 'A_LEVEL';

-- 10. Sample curriculum_topics to see structure
SELECT 
  topic_code,
  topic_name,
  topic_level,
  component_code,
  chronological_period,
  geographical_region,
  key_themes,
  created_at
FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects WHERE subject_name = 'History'
)
LIMIT 20;
