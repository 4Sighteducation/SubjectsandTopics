-- Check what constraints exist on staging_aqa_topics

-- 1. Primary key
SELECT 
  'Primary Key' as constraint_type,
  conname as constraint_name,
  pg_get_constraintdef(oid) as definition
FROM pg_constraint
WHERE conrelid = 'staging_aqa_topics'::regclass
  AND contype = 'p';

-- 2. Unique constraints
SELECT 
  'Unique Constraint' as constraint_type,
  conname as constraint_name,
  pg_get_constraintdef(oid) as definition
FROM pg_constraint
WHERE conrelid = 'staging_aqa_topics'::regclass
  AND contype = 'u';

-- 3. Foreign keys
SELECT 
  'Foreign Key' as constraint_type,
  conname as constraint_name,
  pg_get_constraintdef(oid) as definition
FROM pg_constraint
WHERE conrelid = 'staging_aqa_topics'::regclass
  AND contype = 'f';

-- 4. Check for actual duplicates in staging
SELECT 
  'Duplicate Check' as check_type,
  subject_id,
  topic_name,
  topic_level,
  COUNT(*) as duplicate_count
FROM staging_aqa_topics
GROUP BY subject_id, topic_name, topic_level
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC
LIMIT 10;

-- 5. Show the duplicate "Stakeholder conflicts" entries
SELECT 
  'Stakeholder conflicts duplicates' as check_type,
  st.id,
  st.subject_id,
  s.subject_name,
  s.exam_board,
  st.topic_code,
  st.topic_name,
  st.topic_level,
  st.created_at
FROM staging_aqa_topics st
JOIN staging_aqa_subjects s ON st.subject_id = s.id
WHERE st.topic_name = 'Stakeholder conflicts'
  AND st.topic_level = 3
ORDER BY s.subject_name, st.created_at;

