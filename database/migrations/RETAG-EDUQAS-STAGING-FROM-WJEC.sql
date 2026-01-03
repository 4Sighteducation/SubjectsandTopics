-- Retag legacy Eduqas staging rows that were stored under exam_board='WJEC'
-- Goal: make the data viewer + progress tracking reflect EDUQAS explicitly.
--
-- This does NOT duplicate content; it re-tags rows when we have strong evidence they are Eduqas:
-- - subject.exam_board = 'WJEC'
-- - specification_url contains 'eduqas'
--
-- Run in Supabase SQL editor.

BEGIN;

-- 1) Retag subjects
UPDATE staging_aqa_subjects
SET exam_board = 'EDUQAS'
WHERE exam_board = 'WJEC'
  AND specification_url ILIKE '%eduqas%';

-- 2) Retag topics for those subjects (by subject_id to avoid false positives)
UPDATE staging_aqa_topics t
SET exam_board = 'EDUQAS'
FROM staging_aqa_subjects s
WHERE t.subject_id = s.id
  AND s.exam_board = 'EDUQAS';

-- 3) Retag exam papers for those subjects
UPDATE staging_aqa_exam_papers p
SET exam_board = 'EDUQAS'
FROM staging_aqa_subjects s
WHERE p.subject_id = s.id
  AND s.exam_board = 'EDUQAS';

-- 4) Sanity check: what did we retag?
SELECT
  'EDUQAS subjects now in staging' AS check_name,
  qualification_type,
  COUNT(*) AS subjects
FROM staging_aqa_subjects
WHERE exam_board = 'EDUQAS'
GROUP BY qualification_type
ORDER BY qualification_type;

COMMIT;






