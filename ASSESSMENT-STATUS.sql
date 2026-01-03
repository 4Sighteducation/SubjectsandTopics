-- COMPLETE ASSESSMENT OF SUPABASE DATA
-- Run all these queries to see what we have

-- ========================================
-- 1. CURRICULUM DATA STATUS
-- ========================================

-- 1a. How many AQA subjects with metadata?
SELECT 
  'Total AQA subjects with metadata' as metric,
  COUNT(*) as count
FROM specification_metadata
WHERE exam_board = 'AQA';

-- 1b. Breakdown by qualification type
SELECT 
  qualification_type,
  COUNT(*) as subject_count
FROM specification_metadata
WHERE exam_board = 'AQA'
GROUP BY qualification_type
ORDER BY qualification_type;

-- 1c. How many have components defined?
SELECT 
  'Subjects with components' as metric,
  COUNT(DISTINCT spec_metadata_id) as count
FROM spec_components
WHERE spec_metadata_id IN (
  SELECT id FROM specification_metadata WHERE exam_board = 'AQA'
);

-- 1d. How many have constraints defined?
SELECT 
  'Subjects with constraints' as metric,
  COUNT(DISTINCT spec_metadata_id) as count
FROM selection_constraints
WHERE spec_metadata_id IN (
  SELECT id FROM specification_metadata WHERE exam_board = 'AQA'
);

-- 1e. Sample of subjects with full data
SELECT 
  sm.subject_name,
  sm.qualification_type,
  sm.subject_code,
  COUNT(DISTINCT sc.id) as components,
  COUNT(DISTINCT sel.id) as constraints,
  sm.created_at
FROM specification_metadata sm
LEFT JOIN spec_components sc ON sc.spec_metadata_id = sm.id
LEFT JOIN selection_constraints sel ON sel.spec_metadata_id = sm.id
WHERE sm.exam_board = 'AQA'
GROUP BY sm.id, sm.subject_name, sm.qualification_type, sm.subject_code, sm.created_at
ORDER BY sm.created_at DESC
LIMIT 20;

-- ========================================
-- 2. CURRICULUM TOPICS STATUS
-- ========================================

-- 2a. Total topics for AQA subjects
SELECT 
  'Total curriculum topics' as metric,
  COUNT(*) as count
FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
);

-- 2b. Topics by level
SELECT 
  topic_level,
  COUNT(*) as count,
  CASE 
    WHEN topic_level = 0 THEN 'Options/Modules'
    WHEN topic_level = 1 THEN 'Study Areas'
    WHEN topic_level = 2 THEN 'Content Points'
    ELSE 'Other'
  END as description
FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
)
GROUP BY topic_level
ORDER BY topic_level;

-- 2c. Topics with rich metadata (NEW vs OLD data)
SELECT 
  'Topics with component_code' as metric,
  COUNT(*) as count
FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
)
AND component_code IS NOT NULL;

SELECT 
  'Topics with periods' as metric,
  COUNT(*) as count
FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
)
AND chronological_period IS NOT NULL;

SELECT 
  'Topics with regions' as metric,
  COUNT(*) as count
FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
)
AND geographical_region IS NOT NULL;

-- ========================================
-- 3. ASSESSMENT RESOURCES STATUS
-- ========================================

-- 3a. Total exam papers uploaded
SELECT 
  'Total exam papers' as metric,
  COUNT(*) as count
FROM exam_papers
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
);

-- 3b. Papers by year
SELECT 
  year,
  COUNT(*) as paper_count,
  COUNT(DISTINCT exam_board_subject_id) as subject_count
FROM exam_papers
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
)
GROUP BY year
ORDER BY year DESC;

-- 3c. Papers with all 3 document types
SELECT 
  'Papers with question paper' as metric,
  COUNT(*) as count
FROM exam_papers
WHERE question_paper_url IS NOT NULL
AND exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
);

SELECT 
  'Papers with mark scheme' as metric,
  COUNT(*) as count
FROM exam_papers
WHERE mark_scheme_url IS NOT NULL
AND exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
);

SELECT 
  'Papers with examiner report' as metric,
  COUNT(*) as count
FROM exam_papers
WHERE examiner_report_url IS NOT NULL
AND exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
);

-- 3d. Which subjects have exam papers?
SELECT 
  ebs.subject_name,
  ebs.subject_code,
  qt.code as qualification,
  COUNT(ep.id) as paper_count,
  COUNT(CASE WHEN ep.question_paper_url IS NOT NULL THEN 1 END) as has_qp,
  COUNT(CASE WHEN ep.mark_scheme_url IS NOT NULL THEN 1 END) as has_ms,
  COUNT(CASE WHEN ep.examiner_report_url IS NOT NULL THEN 1 END) as has_er
FROM exam_board_subjects ebs
LEFT JOIN exam_papers ep ON ep.exam_board_subject_id = ebs.id
LEFT JOIN qualification_types qt ON qt.id = ebs.qualification_type_id
WHERE ebs.exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
GROUP BY ebs.subject_name, ebs.subject_code, qt.code
HAVING COUNT(ep.id) > 0
ORDER BY ebs.subject_name;

-- ========================================
-- 4. AI INSIGHTS STATUS
-- ========================================

-- 4a. How many papers have AI insights?
SELECT 
  'Papers with mark scheme insights' as metric,
  COUNT(*) as count
FROM mark_scheme_insights;

SELECT 
  'Papers with examiner report insights' as metric,
  COUNT(*) as count
FROM examiner_report_insights;

SELECT 
  'Total questions extracted' as metric,
  COUNT(*) as count
FROM question_bank;

-- 4b. Which subjects have AI insights?
SELECT 
  ebs.subject_name,
  COUNT(DISTINCT msi.id) as mark_insights,
  COUNT(DISTINCT eri.id) as examiner_insights,
  COUNT(DISTINCT qb.id) as questions
FROM exam_board_subjects ebs
JOIN exam_papers ep ON ep.exam_board_subject_id = ebs.id
LEFT JOIN mark_scheme_insights msi ON msi.exam_paper_id = ep.id
LEFT JOIN examiner_report_insights eri ON eri.exam_paper_id = ep.id
LEFT JOIN question_bank qb ON qb.exam_paper_id = ep.id
WHERE ebs.exam_board_id IN (SELECT id FROM exam_boards WHERE code = 'AQA')
GROUP BY ebs.subject_name
HAVING COUNT(DISTINCT msi.id) > 0
ORDER BY ebs.subject_name;




















