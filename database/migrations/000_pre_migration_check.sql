-- Pre-Migration Check
-- Run this FIRST to verify your database is ready

-- 1. Check required tables exist
DO $$
BEGIN
  -- Check exam_boards exists
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'exam_boards') THEN
    RAISE EXCEPTION 'Table exam_boards not found - run main FLASH schema first';
  END IF;
  
  -- Check curriculum_topics exists
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'curriculum_topics') THEN
    RAISE EXCEPTION 'Table curriculum_topics not found - run main FLASH schema first';
  END IF;
  
  RAISE NOTICE 'Pre-migration check passed - ready to add enhanced metadata tables';
END $$;

-- 2. Show current curriculum_topics columns
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'curriculum_topics'
ORDER BY ordinal_position;

-- 3. Count existing data
SELECT 
  'exam_boards' as table_name, 
  COUNT(*) as record_count 
FROM exam_boards
UNION ALL
SELECT 'curriculum_topics', COUNT(*) FROM curriculum_topics
UNION ALL
SELECT 'exam_board_subjects', COUNT(*) FROM exam_board_subjects;

-- 4. Sample curriculum topics to verify structure
SELECT 
  id,
  topic_name,
  topic_level,
  exam_board_subject_id
FROM curriculum_topics
LIMIT 5;
