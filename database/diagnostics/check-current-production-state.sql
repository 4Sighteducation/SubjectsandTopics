-- DIAGNOSTIC: Check Current Production Database State
-- Run this in Supabase SQL Editor to see what's currently there

-- ========================================
-- 1. CHECK EXAM BOARDS
-- ========================================
SELECT 
  'Exam Boards' as check_name,
  code,
  name as full_name,
  active,
  id
FROM exam_boards
ORDER BY code;

-- ========================================
-- 2. CHECK QUALIFICATION TYPES
-- ========================================
SELECT 
  'Qualification Types' as check_name,
  code,
  name as full_name,
  id
FROM qualification_types
ORDER BY code;

-- ========================================
-- 3. CHECK ALL SUBJECTS (Count by Board + Qualification)
-- ========================================
SELECT 
  'Subject Counts' as check_name,
  eb.code as exam_board,
  qt.code as qualification,
  COUNT(*) as subject_count,
  COUNT(*) FILTER (WHERE ebs.is_current = true) as current_subjects,
  COUNT(*) FILTER (WHERE ebs.is_current = false) as archived_subjects
FROM exam_board_subjects ebs
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
JOIN qualification_types qt ON ebs.qualification_type_id = qt.id
GROUP BY eb.code, qt.code
ORDER BY eb.code, qt.code;

-- ========================================
-- 4. CHECK TOPICS (Count per Subject)
-- ========================================
SELECT 
  'Topic Counts per Subject' as check_name,
  eb.code as exam_board,
  qt.code as qualification,
  ebs.subject_name,
  ebs.subject_code,
  ebs.is_current,
  COUNT(ct.id) as topic_count,
  MAX(ct.topic_level) as max_depth
FROM exam_board_subjects ebs
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
JOIN qualification_types qt ON ebs.qualification_type_id = qt.id
LEFT JOIN curriculum_topics ct ON ebs.id = ct.exam_board_subject_id
GROUP BY eb.code, qt.code, ebs.subject_name, ebs.subject_code, ebs.is_current
HAVING COUNT(ct.id) > 0 OR ebs.is_current = true
ORDER BY eb.code, qt.code, ebs.subject_name;

-- ========================================
-- 5. CHECK ACCOUNTING SPECIFICALLY
-- ========================================
SELECT 
  'Accounting Subject Detail' as check_name,
  ebs.id,
  ebs.subject_code,
  ebs.subject_name,
  ebs.is_current,
  eb.code as exam_board,
  qt.code as qualification,
  COUNT(ct.id) as topics
FROM exam_board_subjects ebs
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
JOIN qualification_types qt ON ebs.qualification_type_id = qt.id
LEFT JOIN curriculum_topics ct ON ebs.id = ct.exam_board_subject_id
WHERE ebs.subject_name ILIKE '%accounting%'
GROUP BY ebs.id, ebs.subject_code, ebs.subject_name, ebs.is_current, eb.code, qt.code
ORDER BY eb.code, qt.code;

-- ========================================
-- 6. CHECK FOR ORPHANED TOPICS
-- ========================================
SELECT 
  'Orphaned Topics' as check_name,
  COUNT(*) as orphaned_count
FROM curriculum_topics ct
WHERE ct.parent_topic_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM curriculum_topics parent 
    WHERE parent.id = ct.parent_topic_id
  );

-- ========================================
-- 7. SAMPLE OF CURRENT TOPICS (First 20)
-- ========================================
SELECT 
  'Sample Topics' as check_name,
  eb.code as exam_board,
  ebs.subject_name,
  ct.topic_code,
  ct.topic_name,
  ct.topic_level,
  ct.parent_topic_id,
  ct.id
FROM curriculum_topics ct
JOIN exam_board_subjects ebs ON ct.exam_board_subject_id = ebs.id
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
WHERE ebs.is_current = true
ORDER BY eb.code, ebs.subject_name, ct.topic_level, ct.sort_order
LIMIT 20;

-- ========================================
-- 8. CHECK WHAT'S IN STAGING (Ready to migrate)
-- ========================================
SELECT 
  'Staging Data Overview' as check_name,
  s.exam_board,
  s.qualification_type,
  COUNT(DISTINCT s.id) as subjects,
  COUNT(t.id) as topics,
  MAX(t.topic_level) as max_depth
FROM staging_aqa_subjects s
LEFT JOIN staging_aqa_topics t ON s.id = t.subject_id
GROUP BY s.exam_board, s.qualification_type
ORDER BY s.exam_board, s.qualification_type;

-- ========================================
-- 9. COMPARE: Accounting in Production vs Staging
-- ========================================

-- Accounting in Production
SELECT 
  'Accounting in PRODUCTION' as location,
  ebs.subject_code,
  ebs.subject_name,
  eb.code as exam_board,
  qt.code as qualification,
  COUNT(ct.id) as topics
FROM exam_board_subjects ebs
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
JOIN qualification_types qt ON ebs.qualification_type_id = qt.id
LEFT JOIN curriculum_topics ct ON ebs.id = ct.exam_board_subject_id
WHERE ebs.subject_name ILIKE '%accounting%'
GROUP BY ebs.subject_code, ebs.subject_name, eb.code, qt.code

UNION ALL

-- Accounting in Staging
SELECT 
  'Accounting in STAGING' as location,
  s.subject_code,
  s.subject_name,
  s.exam_board,
  s.qualification_type,
  COUNT(t.id) as topics
FROM staging_aqa_subjects s
LEFT JOIN staging_aqa_topics t ON s.id = t.subject_id
WHERE s.subject_name ILIKE '%accounting%'
GROUP BY s.subject_code, s.subject_name, s.exam_board, s.qualification_type;

-- ========================================
-- 10. CHECK USER'S SELECTED SUBJECTS (Why no topics showing?)
-- ========================================
SELECT 
  'User Subjects & Topics' as check_name,
  us.user_id,
  ebs.subject_name,
  COUNT(ut.id) as selected_topics
FROM user_subjects us
JOIN exam_board_subjects ebs ON us.subject_id = ebs.id
LEFT JOIN user_topics ut ON ut.user_id = us.user_id
GROUP BY us.user_id, ebs.subject_name
ORDER BY us.user_id, ebs.subject_name;

