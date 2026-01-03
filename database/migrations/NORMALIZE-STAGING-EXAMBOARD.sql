-- Normalize exam_board naming in staging tables to canonical uppercase codes
-- Canonical boards (per Tony): AQA, OCR, EDEXCEL, WJEC, EDUQAS, CCEA, SQA
-- Run in Supabase SQL editor *before* promoting staging -> production.

BEGIN;

-- 1) Normalize exam_board casing + known aliases
UPDATE staging_aqa_subjects
SET exam_board = UPPER(TRIM(exam_board))
WHERE exam_board IS NOT NULL;

UPDATE staging_aqa_topics
SET exam_board = UPPER(TRIM(exam_board))
WHERE exam_board IS NOT NULL;

UPDATE staging_aqa_exam_papers
SET exam_board = UPPER(TRIM(exam_board))
WHERE exam_board IS NOT NULL;

-- 2) Alias mapping
-- EDEXCEL
UPDATE staging_aqa_subjects
SET exam_board = 'EDEXCEL'
WHERE exam_board IN ('EDEXCEL', 'PEARSON EDEXCEL', 'PEARSON');

-- EDUQAS (sometimes stored under WJEC(Eduqas) wording)
UPDATE staging_aqa_subjects SET exam_board = 'EDUQAS' WHERE exam_board IN ('WJEC (EDUQAS)', 'WJEC EDUQAS', 'EDUQAS (WJEC)');

-- Apply mappings to topics/papers as well (match by subject_id to avoid desync)
UPDATE staging_aqa_topics t
SET exam_board = s.exam_board
FROM staging_aqa_subjects s
WHERE t.subject_id = s.id
  AND (t.exam_board IS DISTINCT FROM s.exam_board);

UPDATE staging_aqa_exam_papers p
SET exam_board = s.exam_board
FROM staging_aqa_subjects s
WHERE p.subject_id = s.id
  AND (p.exam_board IS DISTINCT FROM s.exam_board);

-- 3) Sanity check: list any non-canonical boards remaining
SELECT
  'NON_CANONICAL_EXAM_BOARDS' AS check_name,
  exam_board,
  COUNT(*) AS subjects
FROM staging_aqa_subjects
GROUP BY exam_board
HAVING exam_board NOT IN ('AQA','OCR','EDEXCEL','WJEC','EDUQAS','CCEA','SQA')
ORDER BY subjects DESC;

COMMIT;


