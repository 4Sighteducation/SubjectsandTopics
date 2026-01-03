-- EMERGENCY CLEANUP - Eduqas Computer Science Bad Data
-- Run this to remove the corrupted Computer Science data

-- Delete Eduqas Computer Science topics
DELETE FROM staging_aqa_topics 
WHERE subject_id IN (
    SELECT id FROM staging_aqa_subjects 
    WHERE subject_code = 'EDUQAS-CS' 
    AND exam_board = 'WJEC'
);

-- Delete Eduqas Computer Science subject
DELETE FROM staging_aqa_subjects 
WHERE subject_code = 'EDUQAS-CS' 
AND exam_board = 'WJEC';

-- Verify cleanup
SELECT COUNT(*) as remaining_topics 
FROM staging_aqa_topics 
WHERE exam_board = 'WJEC' 
AND subject_id IN (
    SELECT id FROM staging_aqa_subjects 
    WHERE subject_name = 'Computer Science'
);




















