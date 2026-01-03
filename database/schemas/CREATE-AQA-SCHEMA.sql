-- AQA CURRICULUM DATABASE SCHEMA
-- Isolated tables for AQA exam board data
-- Clean, no duplicates, proper constraints

-- ========================================
-- 1. AQA SUBJECTS
-- ========================================
CREATE TABLE IF NOT EXISTS aqa_subjects (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  -- Core identification
  subject_name TEXT NOT NULL,
  subject_code TEXT NOT NULL,
  qualification_type TEXT NOT NULL CHECK (qualification_type IN ('A-Level', 'GCSE', 'AS-Level')),
  
  -- Specification metadata
  specification_url TEXT,
  specification_pdf_url TEXT,
  total_guided_learning_hours INTEGER,
  assessment_overview TEXT,
  
  -- Tracking
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  last_scraped TIMESTAMP,
  scraper_version TEXT DEFAULT 'v1.0',
  
  -- Enforce uniqueness
  UNIQUE(subject_code, qualification_type)
);

-- ========================================
-- 2. AQA TOPICS (Full Hierarchy)
-- ========================================
CREATE TABLE IF NOT EXISTS aqa_topics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  -- Foreign keys
  subject_id UUID NOT NULL REFERENCES aqa_subjects(id) ON DELETE CASCADE,
  parent_topic_id UUID REFERENCES aqa_topics(id) ON DELETE CASCADE,
  
  -- Core fields
  topic_code TEXT NOT NULL,
  topic_name TEXT NOT NULL,
  topic_level INTEGER NOT NULL CHECK (topic_level >= 0 AND topic_level <= 3),
  
  -- Content
  description TEXT,
  
  -- Rich metadata
  component_code TEXT,
  chronological_period TEXT,
  period_start_year INTEGER,
  period_end_year INTEGER,
  geographical_region TEXT CHECK (geographical_region IN ('British', 'European', 'American', 'Asian', 'African', 'Global', NULL)),
  key_themes JSONB,
  
  -- Tracking
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  -- Enforce uniqueness per subject
  UNIQUE(subject_id, topic_code)
);

-- ========================================
-- 3. AQA COMPONENTS (Selection Rules)
-- ========================================
CREATE TABLE IF NOT EXISTS aqa_components (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  subject_id UUID NOT NULL REFERENCES aqa_subjects(id) ON DELETE CASCADE,
  
  component_code TEXT NOT NULL,
  component_name TEXT NOT NULL,
  component_type TEXT,
  
  -- Selection rules
  selection_type TEXT CHECK (selection_type IN ('choose_one', 'choose_multiple', 'required_all')),
  count_required INTEGER,
  total_available INTEGER,
  
  -- Assessment info
  assessment_weight TEXT,
  assessment_format TEXT,
  assessment_description TEXT,
  
  sort_order INTEGER DEFAULT 0,
  
  created_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(subject_id, component_code)
);

-- ========================================
-- 4. AQA CONSTRAINTS (Validation Rules)
-- ========================================
CREATE TABLE IF NOT EXISTS aqa_constraints (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  subject_id UUID NOT NULL REFERENCES aqa_subjects(id) ON DELETE CASCADE,
  
  constraint_type TEXT NOT NULL CHECK (constraint_type IN (
    'geographic_diversity',
    'chronological_requirement',
    'prohibited_combination',
    'genre_requirement',
    'general'
  )),
  
  description TEXT NOT NULL,
  constraint_rule JSONB,  -- Flexible JSON for different rule types
  applies_to_components TEXT[],
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- ========================================
-- 5. AQA EXAM PAPERS
-- ========================================
CREATE TABLE IF NOT EXISTS aqa_exam_papers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  subject_id UUID NOT NULL REFERENCES aqa_subjects(id) ON DELETE CASCADE,
  
  year INTEGER NOT NULL,
  exam_series TEXT NOT NULL CHECK (exam_series IN ('June', 'November')),
  paper_number INTEGER NOT NULL,
  
  -- Document URLs
  question_paper_url TEXT,
  mark_scheme_url TEXT,
  examiner_report_url TEXT,
  
  created_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(subject_id, year, exam_series, paper_number)
);

-- ========================================
-- 6. AQA ASSESSMENT INSIGHTS
-- ========================================
CREATE TABLE IF NOT EXISTS aqa_mark_scheme_insights (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  exam_paper_id UUID NOT NULL REFERENCES aqa_exam_papers(id) ON DELETE CASCADE,
  
  question_types JSONB,
  key_command_words TEXT[],
  marking_criteria JSONB,
  common_point_allocations JSONB,
  
  extracted_date TIMESTAMP DEFAULT NOW(),
  ai_model_used TEXT
);

CREATE TABLE IF NOT EXISTS aqa_examiner_report_insights (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  exam_paper_id UUID NOT NULL REFERENCES aqa_exam_papers(id) ON DELETE CASCADE,
  
  common_mistakes TEXT[],
  strong_answers_characteristics TEXT[],
  areas_of_improvement TEXT[],
  statistical_performance JSONB,
  full_report_text TEXT,
  
  extracted_date TIMESTAMP DEFAULT NOW(),
  ai_model_used TEXT
);

CREATE TABLE IF NOT EXISTS aqa_question_bank (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  exam_paper_id UUID NOT NULL REFERENCES aqa_exam_papers(id) ON DELETE CASCADE,
  
  question_number TEXT NOT NULL,
  question_text TEXT,
  marks_available INTEGER,
  command_word TEXT,
  mark_scheme_points JSONB,
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- ========================================
-- INDEXES FOR PERFORMANCE
-- ========================================
CREATE INDEX IF NOT EXISTS idx_aqa_topics_subject ON aqa_topics(subject_id);
CREATE INDEX IF NOT EXISTS idx_aqa_topics_parent ON aqa_topics(parent_topic_id);
CREATE INDEX IF NOT EXISTS idx_aqa_topics_level ON aqa_topics(topic_level);
CREATE INDEX IF NOT EXISTS idx_aqa_topics_code ON aqa_topics(topic_code);

CREATE INDEX IF NOT EXISTS idx_aqa_components_subject ON aqa_components(subject_id);
CREATE INDEX IF NOT EXISTS idx_aqa_constraints_subject ON aqa_constraints(subject_id);
CREATE INDEX IF NOT EXISTS idx_aqa_papers_subject ON aqa_exam_papers(subject_id);
CREATE INDEX IF NOT EXISTS idx_aqa_papers_year ON aqa_exam_papers(year DESC);

-- ========================================
-- HELPER VIEWS
-- ========================================

-- View: Topics with full subject context
CREATE OR REPLACE VIEW aqa_topics_with_subject AS
SELECT 
  t.*,
  s.subject_name,
  s.subject_code,
  s.qualification_type
FROM aqa_topics t
JOIN aqa_subjects s ON s.id = t.subject_id;

-- View: Topic hierarchy for one subject
CREATE OR REPLACE FUNCTION get_aqa_topic_hierarchy(subject_code_param TEXT)
RETURNS TABLE (
  topic_id UUID,
  topic_code TEXT,
  topic_name TEXT,
  topic_level INTEGER,
  parent_code TEXT,
  full_path TEXT
) AS $$
BEGIN
  RETURN QUERY
  WITH RECURSIVE topic_tree AS (
    -- Level 0 (roots)
    SELECT 
      t.id as topic_id,
      t.topic_code,
      t.topic_name,
      t.topic_level,
      NULL::TEXT as parent_code,
      t.topic_code as full_path
    FROM aqa_topics t
    JOIN aqa_subjects s ON s.id = t.subject_id
    WHERE s.subject_code = subject_code_param
    AND t.parent_topic_id IS NULL
    
    UNION ALL
    
    -- Children (recursive)
    SELECT
      t.id,
      t.topic_code,
      t.topic_name,
      t.topic_level,
      p.topic_code as parent_code,
      p.full_path || ' > ' || t.topic_code as full_path
    FROM aqa_topics t
    JOIN topic_tree p ON t.parent_topic_id = p.topic_id
  )
  SELECT * FROM topic_tree
  ORDER BY full_path;
END;
$$ LANGUAGE plpgsql;

-- View: Summary statistics per subject
CREATE OR REPLACE VIEW aqa_subject_stats AS
SELECT 
  s.id,
  s.subject_name,
  s.qualification_type,
  COUNT(DISTINCT t.id) as total_topics,
  COUNT(DISTINCT t.id) FILTER (WHERE t.topic_level = 0) as level_0_count,
  COUNT(DISTINCT t.id) FILTER (WHERE t.topic_level = 1) as level_1_count,
  COUNT(DISTINCT t.id) FILTER (WHERE t.topic_level = 2) as level_2_count,
  COUNT(DISTINCT t.id) FILTER (WHERE t.topic_level = 3) as level_3_count,
  COUNT(DISTINCT c.id) as component_count,
  COUNT(DISTINCT con.id) as constraint_count,
  COUNT(DISTINCT ep.id) as exam_paper_count,
  MAX(t.updated_at) as last_topic_update
FROM aqa_subjects s
LEFT JOIN aqa_topics t ON t.subject_id = s.id
LEFT JOIN aqa_components c ON c.subject_id = s.id
LEFT JOIN aqa_constraints con ON con.subject_id = s.id
LEFT JOIN aqa_exam_papers ep ON ep.subject_id = s.id
GROUP BY s.id, s.subject_name, s.qualification_type
ORDER BY s.subject_name, s.qualification_type;

-- ========================================
-- COMMENTS
-- ========================================
COMMENT ON TABLE aqa_subjects IS 'AQA exam board subjects with specification metadata';
COMMENT ON TABLE aqa_topics IS 'Complete topic hierarchy with 4 levels (0-3) and proper parent-child relationships';
COMMENT ON TABLE aqa_components IS 'Assessment components with selection rules (e.g., choose 1 from 11)';
COMMENT ON TABLE aqa_constraints IS 'Selection constraints (British+non-British, prohibited combos, chronological requirements)';
COMMENT ON TABLE aqa_exam_papers IS 'Past papers with links to question papers, mark schemes, examiner reports';

-- ========================================
-- VERIFICATION QUERIES
-- ========================================

-- Check schema created successfully
SELECT 
  tablename,
  CASE 
    WHEN tablename LIKE 'aqa_%' THEN '✓ AQA table'
    ELSE 'Other'
  END as category
FROM pg_tables
WHERE schemaname = 'public'
AND tablename LIKE 'aqa%'
ORDER BY tablename;

-- Check constraints
SELECT 
  conname as constraint_name,
  contype as type,
  conrelid::regclass as table_name
FROM pg_constraint
WHERE conrelid::regclass::text LIKE 'aqa%'
ORDER BY conrelid::regclass::text, conname;

















