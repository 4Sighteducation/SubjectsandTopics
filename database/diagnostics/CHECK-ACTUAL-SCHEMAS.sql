-- CHECK ACTUAL TABLE SCHEMAS
-- Run this in Supabase to see what columns actually exist

-- 1. Check exam_boards columns
SELECT 
  'exam_boards columns' as table_name,
  column_name,
  data_type
FROM information_schema.columns
WHERE table_name = 'exam_boards'
ORDER BY ordinal_position;

-- 2. Check qualification_types columns
SELECT 
  'qualification_types columns' as table_name,
  column_name,
  data_type
FROM information_schema.columns
WHERE table_name = 'qualification_types'
ORDER BY ordinal_position;

-- 3. Check exam_board_subjects columns
SELECT 
  'exam_board_subjects columns' as table_name,
  column_name,
  data_type
FROM information_schema.columns
WHERE table_name = 'exam_board_subjects'
ORDER BY ordinal_position;

-- 4. Check curriculum_topics columns
SELECT 
  'curriculum_topics columns' as table_name,
  column_name,
  data_type
FROM information_schema.columns
WHERE table_name = 'curriculum_topics'
ORDER BY ordinal_position;

-- 5. Check staging_aqa_subjects columns
SELECT 
  'staging_aqa_subjects columns' as table_name,
  column_name,
  data_type
FROM information_schema.columns
WHERE table_name = 'staging_aqa_subjects'
ORDER BY ordinal_position;

-- 6. Check staging_aqa_topics columns
SELECT 
  'staging_aqa_topics columns' as table_name,
  column_name,
  data_type
FROM information_schema.columns
WHERE table_name = 'staging_aqa_topics'
ORDER BY ordinal_position;

