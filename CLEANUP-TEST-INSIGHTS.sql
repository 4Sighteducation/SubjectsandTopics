-- Delete test/duplicate insights for Accounting before re-running
-- This clears out the previous test data so we can start fresh

-- 1. Delete mark scheme insights for Accounting
DELETE FROM mark_scheme_insights
WHERE exam_paper_id IN (
  SELECT id FROM exam_papers 
  WHERE exam_board_subject_id = '2eeb6b00-1030-4d15-92d7-6c34285d8069'
);

-- 2. Delete examiner report insights for Accounting
DELETE FROM examiner_report_insights
WHERE exam_paper_id IN (
  SELECT id FROM exam_papers
  WHERE exam_board_subject_id = '2eeb6b00-1030-4d15-92d7-6c34285d8069'
);

-- 3. Delete questions for Accounting
DELETE FROM question_bank
WHERE exam_paper_id IN (
  SELECT id FROM exam_papers
  WHERE exam_board_subject_id = '2eeb6b00-1030-4d15-92d7-6c34285d8069'
);

-- 4. Verify cleanup
SELECT 
  'Mark scheme insights' as table_name,
  COUNT(*) as remaining_count
FROM mark_scheme_insights
UNION ALL
SELECT 'Examiner report insights', COUNT(*)
FROM examiner_report_insights
UNION ALL
SELECT 'Question bank', COUNT(*)
FROM question_bank;
