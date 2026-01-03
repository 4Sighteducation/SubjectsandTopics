-- Clean up Paper 2 B options (delete ALL B option topics to start fresh)

-- First, get the History subject ID
-- Then delete all topics with codes starting with Paper2_OptB

DELETE FROM staging_aqa_topics
WHERE subject_id = (
    SELECT id FROM staging_aqa_subjects 
    WHERE subject_code = 'GCSE-History' 
    AND qualification_type = 'GCSE' 
    AND exam_board = 'Edexcel'
    LIMIT 1
)
AND (
    topic_code LIKE 'Paper2_OptB1%'
    OR topic_code LIKE 'Paper2_OptB2%'
    OR topic_code LIKE 'Paper2_OptB3%'
    OR topic_code LIKE 'Paper2_OptB4%'
);

-- This will delete the L1 options AND all their children
-- Then you can re-run upload-history-structure.py to recreate just the L1 options
-- Then run upload-history-paper2-B-options.py to add the details


