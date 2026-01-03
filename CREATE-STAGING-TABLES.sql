-- CREATE STAGING TABLES FOR SAFE SCRAPING
-- Test scrapers here BEFORE touching production data

-- 1. Staging for curriculum topics
CREATE TABLE IF NOT EXISTS curriculum_topics_staging (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  exam_board TEXT NOT NULL,
  qualification_type TEXT NOT NULL,
  subject_name TEXT NOT NULL,
  subject_code TEXT,
  
  topic_code TEXT,
  topic_name TEXT NOT NULL,
  topic_level INTEGER,
  parent_topic_code TEXT,  -- Store code, not UUID (easier to work with)
  
  -- Rich metadata
  component_code TEXT,
  description TEXT,
  chronological_period TEXT,
  period_start_year INTEGER,
  period_end_year INTEGER,
  geographical_region TEXT,
  key_themes JSONB,
  
  -- Tracking
  scrape_run_id TEXT,  -- Track which batch run created this
  created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Staging for specification metadata
CREATE TABLE IF NOT EXISTS specification_metadata_staging (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  exam_board TEXT NOT NULL,
  qualification_type TEXT NOT NULL,
  subject_name TEXT NOT NULL,
  subject_code TEXT,
  
  total_guided_learning_hours INTEGER,
  assessment_overview TEXT,
  specification_url TEXT,
  specification_pdf_url TEXT,
  
  scrape_run_id TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Staging for components
CREATE TABLE IF NOT EXISTS spec_components_staging (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  exam_board TEXT,
  subject_name TEXT,
  
  component_code TEXT,
  component_name TEXT,
  selection_type TEXT,
  count_required INTEGER,
  total_available INTEGER,
  assessment_weight TEXT,
  
  scrape_run_id TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 4. Staging for constraints
CREATE TABLE IF NOT EXISTS selection_constraints_staging (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  exam_board TEXT,
  subject_name TEXT,
  
  constraint_type TEXT,
  description TEXT,
  constraint_rule JSONB,
  
  scrape_run_id TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for staging tables
CREATE INDEX IF NOT EXISTS idx_staging_topics_subject 
  ON curriculum_topics_staging(exam_board, subject_name, qualification_type);

CREATE INDEX IF NOT EXISTS idx_staging_topics_code 
  ON curriculum_topics_staging(topic_code);

CREATE INDEX IF NOT EXISTS idx_staging_topics_run 
  ON curriculum_topics_staging(scrape_run_id);

-- Helper view: See unique topics per scrape run
CREATE OR REPLACE VIEW staging_summary AS
SELECT 
  scrape_run_id,
  exam_board,
  subject_name,
  qualification_type,
  COUNT(DISTINCT topic_code) as unique_topics,
  COUNT(*) as total_records,
  MAX(created_at) as scraped_at
FROM curriculum_topics_staging
GROUP BY scrape_run_id, exam_board, subject_name, qualification_type
ORDER BY scraped_at DESC;




















