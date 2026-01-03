-- ================================================================
-- ADD EXAM_BOARD COLUMN TO STAGING TABLES
-- ================================================================
-- Run this in Supabase SQL Editor to support multi-board scraping
-- (AQA, Edexcel, OCR, WJEC, CCEA)
--
-- Date: November 4, 2025
-- ================================================================

-- 1. Add exam_board column to staging_aqa_subjects
ALTER TABLE staging_aqa_subjects 
  ADD COLUMN IF NOT EXISTS exam_board TEXT DEFAULT 'AQA';

-- 2. Add exam_board column to staging_aqa_topics
ALTER TABLE staging_aqa_topics 
  ADD COLUMN IF NOT EXISTS exam_board TEXT DEFAULT 'AQA';

-- 3. Add exam_board column to staging_aqa_exam_papers
ALTER TABLE staging_aqa_exam_papers 
  ADD COLUMN IF NOT EXISTS exam_board TEXT DEFAULT 'AQA';

-- 4. Update existing AQA data (set exam_board = 'AQA' where NULL)
UPDATE staging_aqa_subjects 
SET exam_board = 'AQA' 
WHERE exam_board IS NULL;

UPDATE staging_aqa_topics 
SET exam_board = 'AQA' 
WHERE exam_board IS NULL;

UPDATE staging_aqa_exam_papers 
SET exam_board = 'AQA' 
WHERE exam_board IS NULL;

-- 5. Add indexes for faster filtering by exam_board
CREATE INDEX IF NOT EXISTS idx_subjects_exam_board 
ON staging_aqa_subjects(exam_board);

CREATE INDEX IF NOT EXISTS idx_topics_exam_board 
ON staging_aqa_topics(exam_board);

CREATE INDEX IF NOT EXISTS idx_papers_exam_board 
ON staging_aqa_exam_papers(exam_board);

-- 6. Update unique constraints to include exam_board
-- Drop old constraint
ALTER TABLE staging_aqa_subjects 
DROP CONSTRAINT IF EXISTS staging_aqa_subjects_subject_code_qualification_type_key;

-- Add new constraint with exam_board
ALTER TABLE staging_aqa_subjects 
ADD CONSTRAINT staging_aqa_subjects_code_qual_board_unique 
UNIQUE (subject_code, qualification_type, exam_board);

-- ================================================================
-- VERIFICATION QUERIES
-- ================================================================

-- Count subjects by exam board
SELECT exam_board, COUNT(*) as subject_count
FROM staging_aqa_subjects
GROUP BY exam_board
ORDER BY exam_board;

-- Count topics by exam board
SELECT exam_board, COUNT(*) as topic_count
FROM staging_aqa_topics
GROUP BY exam_board
ORDER BY exam_board;

-- Count papers by exam board
SELECT exam_board, COUNT(*) as paper_count
FROM staging_aqa_exam_papers
GROUP BY exam_board
ORDER BY exam_board;

-- ================================================================
-- SUCCESS!
-- ================================================================
-- ✅ exam_board column added to all tables
-- ✅ Existing AQA data marked as exam_board = 'AQA'
-- ✅ Indexes created for performance
-- ✅ Unique constraints updated
--
-- Ready for Edexcel scraping! 🚀
-- ================================================================

