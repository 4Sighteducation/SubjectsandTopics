-- CHECK STAGING TABLE STRUCTURE FOR EDUQAS/WJEC
-- Run this in Supabase SQL Editor to verify table structure

-- 1. Check staging_aqa_subjects columns
SELECT 
  'staging_aqa_subjects' as table_name,
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_name = 'staging_aqa_subjects'
ORDER BY ordinal_position;

-- 2. Check staging_aqa_topics columns
SELECT 
  'staging_aqa_topics' as table_name,
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_name = 'staging_aqa_topics'
ORDER BY ordinal_position;

-- 3. Check if exam_board column exists and what values are in it
SELECT DISTINCT exam_board 
FROM staging_aqa_subjects 
ORDER BY exam_board;

-- 4. Check constraints on staging_aqa_subjects
SELECT 
  constraint_name,
  constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'staging_aqa_subjects';

-- 5. Sample data from staging_aqa_subjects (if any WJEC exists)
SELECT 
  id,
  subject_name,
  subject_code,
  qualification_type,
  exam_board,
  specification_url,
  specification_pdf_url
FROM staging_aqa_subjects
WHERE exam_board = 'WJEC' OR exam_board = 'Eduqas'
LIMIT 5;

-- 6. Sample data from staging_aqa_topics (if any WJEC exists)
SELECT 
  id,
  subject_id,
  topic_code,
  topic_name,
  topic_level,
  parent_topic_id,
  exam_board
FROM staging_aqa_topics
WHERE exam_board = 'WJEC' OR exam_board = 'Eduqas'
LIMIT 5;



