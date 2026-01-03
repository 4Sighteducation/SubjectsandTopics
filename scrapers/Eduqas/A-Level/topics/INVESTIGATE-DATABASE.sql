-- INVESTIGATION QUERIES - Check what's in the staging database
-- Run these queries one by one in Supabase SQL Editor

-- 1. Check all Eduqas/WJEC subjects
SELECT 
    id,
    subject_name,
    subject_code,
    qualification_type,
    exam_board,
    (SELECT COUNT(*) FROM staging_aqa_topics WHERE subject_id = staging_aqa_subjects.id) as topic_count
FROM staging_aqa_subjects
WHERE exam_board = 'WJEC'
ORDER BY subject_name;

-- 2. Check Computer Science specifically
SELECT 
    id,
    subject_name,
    subject_code,
    qualification_type,
    exam_board,
    created_at
FROM staging_aqa_subjects
WHERE subject_name LIKE '%Computer Science%'
ORDER BY created_at DESC;

-- 3. Check Computer Science topics by level
SELECT 
    s.subject_code,
    s.subject_name,
    t.topic_level,
    COUNT(*) as count
FROM staging_aqa_topics t
JOIN staging_aqa_subjects s ON t.subject_id = s.id
WHERE s.subject_name LIKE '%Computer Science%'
GROUP BY s.subject_code, s.subject_name, t.topic_level
ORDER BY s.subject_code, t.topic_level;

-- 4. Check sample Computer Science topics
SELECT 
    t.id,
    t.topic_code,
    t.topic_name,
    t.topic_level,
    t.parent_topic_id,
    s.subject_code,
    s.exam_board
FROM staging_aqa_topics t
JOIN staging_aqa_subjects s ON t.subject_id = s.id
WHERE s.subject_name LIKE '%Computer Science%'
ORDER BY t.topic_code
LIMIT 20;

-- 5. Check for orphaned topics (topics without valid parent)
SELECT 
    t.id,
    t.topic_code,
    t.topic_name,
    t.topic_level,
    t.parent_topic_id,
    s.subject_name
FROM staging_aqa_topics t
JOIN staging_aqa_subjects s ON t.subject_id = s.id
WHERE t.parent_topic_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM staging_aqa_topics parent
    WHERE parent.id = t.parent_topic_id
)
AND s.exam_board = 'WJEC'
LIMIT 20;

-- 6. Count all topics by exam board
SELECT 
    exam_board,
    COUNT(*) as total_topics
FROM staging_aqa_topics
GROUP BY exam_board;




















