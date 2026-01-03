-- QUICK CHECK: What's in Staging Tables?
-- Run this BEFORE migrating to see what data is ready

-- ========================================
-- 1. COUNT EVERYTHING IN STAGING
-- ========================================
SELECT 
  'Staging Overview' as check_name,
  COUNT(DISTINCT s.id) as subjects,
  COUNT(t.id) as topics,
  COUNT(DISTINCT s.exam_board) as exam_boards,
  COUNT(DISTINCT s.qualification_type) as qualifications
FROM staging_aqa_subjects s
LEFT JOIN staging_aqa_topics t ON s.id = t.subject_id;

-- ========================================
-- 2. BREAKDOWN BY EXAM BOARD
-- ========================================
SELECT 
  'Staging by Exam Board' as check_name,
  s.exam_board,
  s.qualification_type,
  COUNT(DISTINCT s.id) as subjects,
  COUNT(t.id) as topics,
  MAX(t.topic_level) as max_depth,
  MIN(s.created_at) as first_scraped,
  MAX(s.updated_at) as last_updated
FROM staging_aqa_subjects s
LEFT JOIN staging_aqa_topics t ON s.id = t.subject_id
GROUP BY s.exam_board, s.qualification_type
ORDER BY s.exam_board, s.qualification_type;

-- ========================================
-- 3. SAMPLE SUBJECTS IN STAGING
-- ========================================
SELECT 
  'Sample Staging Subjects' as check_name,
  s.exam_board,
  s.qualification_type,
  s.subject_code,
  s.subject_name,
  COUNT(t.id) as topics
FROM staging_aqa_subjects s
LEFT JOIN staging_aqa_topics t ON s.id = t.subject_id
GROUP BY s.id, s.exam_board, s.qualification_type, s.subject_code, s.subject_name
ORDER BY s.exam_board, s.qualification_type, s.subject_name
LIMIT 30;

-- ========================================
-- 4. SAMPLE TOPICS IN STAGING
-- ========================================
SELECT 
  'Sample Staging Topics' as check_name,
  s.exam_board,
  s.subject_name,
  t.topic_code,
  t.topic_name,
  t.topic_level,
  CASE WHEN t.parent_topic_id IS NULL THEN 'Root' ELSE 'Child' END as hierarchy
FROM staging_aqa_topics t
JOIN staging_aqa_subjects s ON t.subject_id = s.id
ORDER BY s.exam_board, s.subject_name, t.topic_level, t.topic_code
LIMIT 50;

-- ========================================
-- 5. CHECK FOR ORPHANED TOPICS IN STAGING
-- ========================================
SELECT 
  'Orphaned Topics in Staging' as check_name,
  COUNT(*) as orphaned_count
FROM staging_aqa_topics t
WHERE t.parent_topic_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM staging_aqa_topics parent 
    WHERE parent.id = t.parent_topic_id
  );

-- ========================================
-- 6. TOPIC DEPTH DISTRIBUTION
-- ========================================
SELECT 
  'Topic Depth Distribution' as check_name,
  t.topic_level,
  COUNT(*) as count
FROM staging_aqa_topics t
GROUP BY t.topic_level
ORDER BY t.topic_level;

-- ========================================
-- 7. EXAM BOARDS LIST
-- ========================================
SELECT 
  'Exam Boards in Staging' as check_name,
  DISTINCT exam_board
FROM staging_aqa_subjects
ORDER BY exam_board;

-- ========================================
-- 8. QUALIFICATION TYPES LIST
-- ========================================
SELECT 
  'Qualification Types in Staging' as check_name,
  DISTINCT qualification_type
FROM staging_aqa_subjects
ORDER BY qualification_type;

-- ========================================
-- 9. RECENT SCRAPING ACTIVITY
-- ========================================
SELECT 
  'Recent Scraping Activity' as check_name,
  DATE(s.created_at) as scrape_date,
  s.exam_board,
  COUNT(DISTINCT s.id) as subjects_added,
  COUNT(t.id) as topics_added
FROM staging_aqa_subjects s
LEFT JOIN staging_aqa_topics t ON s.id = t.subject_id
WHERE s.created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(s.created_at), s.exam_board
ORDER BY scrape_date DESC, s.exam_board;

-- ========================================
-- 10. SUBJECTS WITHOUT TOPICS
-- ========================================
SELECT 
  'Subjects Missing Topics' as check_name,
  s.exam_board,
  s.qualification_type,
  s.subject_code,
  s.subject_name
FROM staging_aqa_subjects s
LEFT JOIN staging_aqa_topics t ON s.id = t.subject_id
GROUP BY s.id, s.exam_board, s.qualification_type, s.subject_code, s.subject_name
HAVING COUNT(t.id) = 0
ORDER BY s.exam_board, s.subject_name
LIMIT 20;

