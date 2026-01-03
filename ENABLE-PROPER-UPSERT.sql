-- ENABLE PROPER UPSERT FOR CURRICULUM_TOPICS
-- This tells Supabase: "If this combination exists, UPDATE it. Otherwise INSERT."

-- Create unique index on the combination that makes a topic unique
CREATE UNIQUE INDEX IF NOT EXISTS unique_topic_per_subject_code_level
ON curriculum_topics(exam_board_subject_id, topic_code, topic_level)
WHERE topic_code IS NOT NULL;

-- Verify it was created
SELECT 
  indexname,
  indexdef
FROM pg_indexes
WHERE tablename = 'curriculum_topics'
AND indexname = 'unique_topic_per_subject_code_level';

-- Test: Try to insert a duplicate (should fail with unique constraint error)
-- This proves the constraint is working
/*
INSERT INTO curriculum_topics (
  exam_board_subject_id, 
  topic_code, 
  topic_level,
  topic_name
) 
SELECT 
  exam_board_subject_id,
  topic_code,
  topic_level,
  topic_name
FROM curriculum_topics
WHERE topic_code = '1A'
LIMIT 1;
-- Should get error: "duplicate key value violates unique constraint"
*/




















