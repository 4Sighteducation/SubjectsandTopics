-- Check what constraints exist on staging_aqa_exam_papers
SELECT conname AS constraint_name, 
       pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE conrelid = 'staging_aqa_exam_papers'::regclass
  AND conname LIKE '%unique%' OR conname LIKE '%key%';
