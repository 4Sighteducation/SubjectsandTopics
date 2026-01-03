-- Clone WJEC -> EDUQAS in *staging* for subjects where the spec is the same.
--
-- Why staging?
-- - Keeps your data viewer progress tracking accurate.
-- - You can still QA in staging before promoting to production.
-- - Production will only reflect this after you run your staging->production migration.
--
-- Safety rules:
-- - Only clones a fixed allowlist of overlap subjects (from your WJEC + EDUQAS lists).
-- - Only clones when the EDUQAS subject DOES NOT ALREADY exist in staging (won't overwrite real EDUQAS scrapes).
-- - Clones: subjects, topics (including hierarchy), and exam papers.
--
-- Run in Supabase SQL editor.

BEGIN;

-- NOTE: This script intentionally avoids TEMP tables for allowlists because some SQL runners
-- execute statements in a way that can lose TEMP context. We use inline VALUES CTEs instead.

-- ------------------------------------------------------------
-- 1) Identify WJEC subjects to clone (overlap allowlist only)
-- ------------------------------------------------------------
WITH allowlist(qualification_type, norm_subject_name) AS (
  VALUES
    -- GCSE overlap (18)
    ('GCSE','art and design'),
    ('GCSE','business'),
    ('GCSE','computer science'),
    ('GCSE','design and technology'),
    ('GCSE','electronics'),
    ('GCSE','english language'),
    ('GCSE','english literature'),
    ('GCSE','film studies'),
    ('GCSE','french'),
    ('GCSE','german'),
    ('GCSE','history'),
    ('GCSE','latin'),
    ('GCSE','mathematics'),
    ('GCSE','media studies'),
    ('GCSE','physical education'),
    ('GCSE','religious studies'),
    ('GCSE','sociology'),
    ('GCSE','spanish'),
    -- A-Level overlap (25)
    ('A-Level','art and design'),
    ('A-Level','biology'),
    ('A-Level','business'),
    ('A-Level','chemistry'),
    ('A-Level','computer science'),
    ('A-Level','design and technology'),
    ('A-Level','drama'),
    ('A-Level','economics'),
    ('A-Level','electronics'),
    ('A-Level','english language'),
    ('A-Level','english language and literature'),
    ('A-Level','english literature'),
    ('A-Level','extended project'),
    ('A-Level','film studies'),
    ('A-Level','french'),
    ('A-Level','geography'),
    ('A-Level','german'),
    ('A-Level','law'),
    ('A-Level','media studies'),
    ('A-Level','physical education'),
    ('A-Level','physics'),
    ('A-Level','psychology'),
    ('A-Level','religious studies'),
    ('A-Level','sociology'),
    ('A-Level','spanish')
),
wjec_candidates AS (
  SELECT
    s.*
  FROM staging_aqa_subjects s
  JOIN allowlist a
    ON a.qualification_type = s.qualification_type
   AND a.norm_subject_name = lower(regexp_replace(regexp_replace(s.subject_name, '\\([^)]*\\)', '', 'g'), '\\s+', ' ', 'g'))
  WHERE s.exam_board = 'WJEC'
),
missing_eduqas AS (
  SELECT
    w.*
  FROM wjec_candidates w
  LEFT JOIN staging_aqa_subjects e
    ON e.exam_board = 'EDUQAS'
   AND e.qualification_type = w.qualification_type
   AND lower(regexp_replace(regexp_replace(e.subject_name, '\\([^)]*\\)', '', 'g'), '\\s+', ' ', 'g'))
       = lower(regexp_replace(regexp_replace(w.subject_name, '\\([^)]*\\)', '', 'g'), '\\s+', ' ', 'g'))
  WHERE e.id IS NULL
),
inserted_eduqas AS (
  INSERT INTO staging_aqa_subjects (
    subject_name,
    subject_code,
    qualification_type,
    specification_url,
    exam_board
  )
  SELECT
    w.subject_name,
    w.subject_code,
    w.qualification_type,
    w.specification_url,
    'EDUQAS'
  FROM missing_eduqas w
  RETURNING id, subject_code, qualification_type, subject_name
)
SELECT
  'CLONED_SUBJECTS' AS check_name,
  qualification_type,
  COUNT(*) AS subjects_cloned
FROM inserted_eduqas
GROUP BY qualification_type
ORDER BY qualification_type;

-- ------------------------------------------------------------
-- 2) Build subject mapping (WJEC staging subject_id -> EDUQAS staging subject_id)
-- ------------------------------------------------------------
-- We inline subject_map in each subsequent statement to avoid TEMP table reliance.

-- ------------------------------------------------------------
-- 3) Clone topics (structure)
-- ------------------------------------------------------------
-- Insert all EDUQAS topics as copies of WJEC topics (parent pointers fixed in step 4)
INSERT INTO staging_aqa_topics (
  subject_id,
  topic_code,
  topic_name,
  topic_level,
  parent_topic_id,
  exam_board
)
WITH allowlist(qualification_type, norm_subject_name) AS (
  VALUES
    ('GCSE','art and design'),('GCSE','business'),('GCSE','computer science'),('GCSE','design and technology'),
    ('GCSE','electronics'),('GCSE','english language'),('GCSE','english literature'),('GCSE','film studies'),
    ('GCSE','french'),('GCSE','german'),('GCSE','history'),('GCSE','latin'),('GCSE','mathematics'),
    ('GCSE','media studies'),('GCSE','physical education'),('GCSE','religious studies'),('GCSE','sociology'),
    ('GCSE','spanish'),
    ('A-Level','art and design'),('A-Level','biology'),('A-Level','business'),('A-Level','chemistry'),
    ('A-Level','computer science'),('A-Level','design and technology'),('A-Level','drama'),('A-Level','economics'),
    ('A-Level','electronics'),('A-Level','english language'),('A-Level','english language and literature'),
    ('A-Level','english literature'),('A-Level','extended project'),('A-Level','film studies'),('A-Level','french'),
    ('A-Level','geography'),('A-Level','german'),('A-Level','law'),('A-Level','media studies'),
    ('A-Level','physical education'),('A-Level','physics'),('A-Level','psychology'),('A-Level','religious studies'),
    ('A-Level','sociology'),('A-Level','spanish')
),
subject_map AS (
  SELECT
    w.id AS wjec_subject_id,
    e.id AS eduqas_subject_id
  FROM staging_aqa_subjects w
  JOIN allowlist a
    ON a.qualification_type = w.qualification_type
   AND a.norm_subject_name = lower(regexp_replace(regexp_replace(w.subject_name, '\\([^)]*\\)', '', 'g'), '\\s+', ' ', 'g'))
  JOIN staging_aqa_subjects e
    ON e.exam_board = 'EDUQAS'
   AND e.subject_code = w.subject_code
   AND e.qualification_type = w.qualification_type
  WHERE w.exam_board = 'WJEC'
    AND NOT EXISTS (SELECT 1 FROM staging_aqa_topics t2 WHERE t2.subject_id = e.id)
)
SELECT
  m.eduqas_subject_id AS subject_id,
  t.topic_code,
  t.topic_name,
  t.topic_level,
  NULL AS parent_topic_id,
  'EDUQAS' AS exam_board
FROM subject_map m
JOIN staging_aqa_topics t
  ON t.subject_id = m.wjec_subject_id;

-- ------------------------------------------------------------
-- 4) Fix EDUQAS parent_topic_id links using topic_code mapping
-- ------------------------------------------------------------
WITH allowlist(qualification_type, norm_subject_name) AS (
  VALUES
    ('GCSE','art and design'),('GCSE','business'),('GCSE','computer science'),('GCSE','design and technology'),
    ('GCSE','electronics'),('GCSE','english language'),('GCSE','english literature'),('GCSE','film studies'),
    ('GCSE','french'),('GCSE','german'),('GCSE','history'),('GCSE','latin'),('GCSE','mathematics'),
    ('GCSE','media studies'),('GCSE','physical education'),('GCSE','religious studies'),('GCSE','sociology'),
    ('GCSE','spanish'),
    ('A-Level','art and design'),('A-Level','biology'),('A-Level','business'),('A-Level','chemistry'),
    ('A-Level','computer science'),('A-Level','design and technology'),('A-Level','drama'),('A-Level','economics'),
    ('A-Level','electronics'),('A-Level','english language'),('A-Level','english language and literature'),
    ('A-Level','english literature'),('A-Level','extended project'),('A-Level','film studies'),('A-Level','french'),
    ('A-Level','geography'),('A-Level','german'),('A-Level','law'),('A-Level','media studies'),
    ('A-Level','physical education'),('A-Level','physics'),('A-Level','psychology'),('A-Level','religious studies'),
    ('A-Level','sociology'),('A-Level','spanish')
),
subject_map AS (
  SELECT
    w.id AS wjec_subject_id,
    e.id AS eduqas_subject_id
  FROM staging_aqa_subjects w
  JOIN allowlist a
    ON a.qualification_type = w.qualification_type
   AND a.norm_subject_name = lower(regexp_replace(regexp_replace(w.subject_name, '\\([^)]*\\)', '', 'g'), '\\s+', ' ', 'g'))
  JOIN staging_aqa_subjects e
    ON e.exam_board = 'EDUQAS'
   AND e.subject_code = w.subject_code
   AND e.qualification_type = w.qualification_type
  WHERE w.exam_board = 'WJEC'
    AND NOT EXISTS (SELECT 1 FROM staging_aqa_topics t2 WHERE t2.subject_id = e.id)
)
UPDATE staging_aqa_topics child
SET parent_topic_id = parent.id
FROM subject_map m
JOIN staging_aqa_topics src_child
  ON src_child.subject_id = m.wjec_subject_id
JOIN staging_aqa_topics src_parent
  ON src_parent.id = src_child.parent_topic_id
JOIN staging_aqa_topics parent
  ON parent.subject_id = m.eduqas_subject_id
 AND parent.topic_code = src_parent.topic_code
WHERE child.subject_id = m.eduqas_subject_id
  AND child.exam_board = 'EDUQAS'
  AND src_child.topic_code = child.topic_code
  AND src_child.parent_topic_id IS NOT NULL;

-- ------------------------------------------------------------
-- 5) Clone exam papers (if present)
-- ------------------------------------------------------------
INSERT INTO staging_aqa_exam_papers (
  subject_id,
  year,
  exam_series,
  paper_number,
  tier,
  component_code,
  question_paper_url,
  mark_scheme_url,
  examiner_report_url,
  exam_board
)
WITH allowlist(qualification_type, norm_subject_name) AS (
  VALUES
    ('GCSE','art and design'),('GCSE','business'),('GCSE','computer science'),('GCSE','design and technology'),
    ('GCSE','electronics'),('GCSE','english language'),('GCSE','english literature'),('GCSE','film studies'),
    ('GCSE','french'),('GCSE','german'),('GCSE','history'),('GCSE','latin'),('GCSE','mathematics'),
    ('GCSE','media studies'),('GCSE','physical education'),('GCSE','religious studies'),('GCSE','sociology'),
    ('GCSE','spanish'),
    ('A-Level','art and design'),('A-Level','biology'),('A-Level','business'),('A-Level','chemistry'),
    ('A-Level','computer science'),('A-Level','design and technology'),('A-Level','drama'),('A-Level','economics'),
    ('A-Level','electronics'),('A-Level','english language'),('A-Level','english language and literature'),
    ('A-Level','english literature'),('A-Level','extended project'),('A-Level','film studies'),('A-Level','french'),
    ('A-Level','geography'),('A-Level','german'),('A-Level','law'),('A-Level','media studies'),
    ('A-Level','physical education'),('A-Level','physics'),('A-Level','psychology'),('A-Level','religious studies'),
    ('A-Level','sociology'),('A-Level','spanish')
),
subject_map AS (
  SELECT
    w.id AS wjec_subject_id,
    e.id AS eduqas_subject_id
  FROM staging_aqa_subjects w
  JOIN allowlist a
    ON a.qualification_type = w.qualification_type
   AND a.norm_subject_name = lower(regexp_replace(regexp_replace(w.subject_name, '\\([^)]*\\)', '', 'g'), '\\s+', ' ', 'g'))
  JOIN staging_aqa_subjects e
    ON e.exam_board = 'EDUQAS'
   AND e.subject_code = w.subject_code
   AND e.qualification_type = w.qualification_type
  WHERE w.exam_board = 'WJEC'
    AND NOT EXISTS (SELECT 1 FROM staging_aqa_topics t2 WHERE t2.subject_id = e.id)
)
SELECT
  m.eduqas_subject_id AS subject_id,
  p.year,
  p.exam_series,
  p.paper_number,
  p.tier,
  p.component_code,
  p.question_paper_url,
  p.mark_scheme_url,
  p.examiner_report_url,
  'EDUQAS' AS exam_board
FROM subject_map m
JOIN staging_aqa_exam_papers p
  ON p.subject_id = m.wjec_subject_id;

-- ------------------------------------------------------------
-- 6) Verification summary
-- ------------------------------------------------------------
SELECT
  'EDUQAS staging subjects after clone' AS check_name,
  qualification_type,
  COUNT(*) AS subjects,
  SUM(topic_count) AS topics
FROM (
  SELECT
    s.qualification_type,
    s.id,
    (SELECT COUNT(*) FROM staging_aqa_topics t WHERE t.subject_id = s.id) AS topic_count
  FROM staging_aqa_subjects s
  WHERE s.exam_board = 'EDUQAS'
) x
GROUP BY qualification_type
ORDER BY qualification_type;

COMMIT;


