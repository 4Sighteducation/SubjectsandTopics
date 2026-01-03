-- CHECK HISTORY DATA IN SUPABASE
-- Run these queries to see what uploaded

-- 1. Get the specification metadata for History
SELECT 
  id,
  exam_board,
  qualification_type,
  subject_name,
  subject_code,
  total_guided_learning_hours,
  specification_url,
  specification_pdf_url,
  created_at,
  updated_at
FROM specification_metadata
WHERE exam_board = 'AQA' 
AND subject_name = 'History'
AND qualification_type = 'a_level';

-- 2. Get components for History (should show Component 1, Component 2, etc.)
SELECT 
  component_code,
  component_name,
  component_type,
  selection_type,
  count_required,
  total_available,
  assessment_weight,
  assessment_format
FROM spec_components
WHERE spec_metadata_id = '6980f08d-71f8-48c6-a0ce-510d12794a7d'
ORDER BY sort_order;

-- 3. Get constraints (should show British/non-British rule, prohibited combos)
SELECT 
  constraint_type,
  description,
  constraint_rule,
  applies_to_components
FROM selection_constraints
WHERE spec_metadata_id = '6980f08d-71f8-48c6-a0ce-510d12794a7d';

-- 4. Get ALL topics for History (old + new)
SELECT 
  topic_code,
  topic_name,
  topic_level,
  component_code,
  chronological_period,
  period_start_year,
  period_end_year,
  geographical_region,
  key_themes,
  created_at,
  updated_at
FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE subject_name = 'History'
  AND exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
)
ORDER BY topic_code, topic_level;

-- 5. Count topics by level for History
SELECT 
  topic_level,
  COUNT(*) as count
FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE subject_name = 'History'
  AND exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
)
GROUP BY topic_level
ORDER BY topic_level;

-- 6. Show ONLY topics with rich metadata (newly scraped)
SELECT 
  topic_code,
  topic_name,
  topic_level,
  component_code,
  chronological_period,
  geographical_region,
  key_themes
FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE subject_name = 'History'
)
AND (
  component_code IS NOT NULL 
  OR geographical_region IS NOT NULL 
  OR chronological_period IS NOT NULL
)
ORDER BY topic_code;

-- 7. Compare old vs new topics
-- Old topics (from June, no metadata)
SELECT COUNT(*) as old_topics
FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects WHERE subject_name = 'History'
)
AND component_code IS NULL
AND geographical_region IS NULL;

-- New topics (from today, has metadata)
SELECT COUNT(*) as new_topics
FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects WHERE subject_name = 'History'
)
AND (component_code IS NOT NULL OR geographical_region IS NOT NULL);






