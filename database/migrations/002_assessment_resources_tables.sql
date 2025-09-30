-- Migration 002: Assessment Resources Tables
-- Store past papers, mark schemes, and examiner reports

-- 1. Exam Papers Table
CREATE TABLE IF NOT EXISTS exam_papers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  exam_board_subject_id UUID REFERENCES exam_board_subjects(id) ON DELETE CASCADE,
  
  -- Paper identification
  year INTEGER NOT NULL,
  exam_series VARCHAR(20) NOT NULL,  -- 'June', 'November'
  paper_number INTEGER,
  component_code VARCHAR(10),  -- 'Paper 1', 'Paper 2', etc.
  
  -- Paper details
  paper_title TEXT,
  tier VARCHAR(20),  -- 'Foundation', 'Higher', or NULL for A-Level
  
  -- Document URLs (on CDN)
  question_paper_url TEXT,
  mark_scheme_url TEXT,
  examiner_report_url TEXT,
  
  -- Metadata
  total_marks INTEGER,
  duration_minutes INTEGER,
  
  -- Tracking
  scraped_date TIMESTAMP DEFAULT NOW(),
  last_verified TIMESTAMP,
  is_active BOOLEAN DEFAULT true,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(exam_board_subject_id, year, exam_series, paper_number)
);

-- 2. Mark Scheme Analysis (AI-extracted insights from mark schemes)
CREATE TABLE IF NOT EXISTS mark_scheme_insights (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  exam_paper_id UUID REFERENCES exam_papers(id) ON DELETE CASCADE,
  
  -- AI-extracted patterns
  question_types JSONB,  -- Common question types in this paper
  key_command_words TEXT[],  -- "Explain", "Evaluate", "Calculate", etc.
  marking_criteria JSONB,  -- What examiners look for
  common_point_allocations JSONB,  -- Typical mark distributions
  
  -- Metadata
  extracted_date TIMESTAMP DEFAULT NOW(),
  ai_model_used VARCHAR(50)
);

-- 3. Examiner Report Insights (common mistakes, advice)
CREATE TABLE IF NOT EXISTS examiner_report_insights (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  exam_paper_id UUID REFERENCES exam_papers(id) ON DELETE CASCADE,
  
  -- Key insights
  common_mistakes TEXT[],  -- What students got wrong
  strong_answers_characteristics TEXT[],  -- What good answers included
  areas_of_improvement TEXT[],  -- Examiner recommendations
  statistical_performance JSONB,  -- Question-level stats if mentioned
  
  -- Full text for AI context
  full_report_text TEXT,  -- Complete examiner report text
  
  -- Metadata
  extracted_date TIMESTAMP DEFAULT NOW(),
  ai_model_used VARCHAR(50)
);

-- 4. Question Bank (extracted questions for AI training)
CREATE TABLE IF NOT EXISTS question_bank (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  exam_paper_id UUID REFERENCES exam_papers(id) ON DELETE CASCADE,
  
  -- Question details
  question_number VARCHAR(10),  -- "01", "02.1", etc.
  question_text TEXT NOT NULL,
  marks_available INTEGER,
  command_word VARCHAR(50),  -- "Explain", "Calculate", etc.
  
  -- Answer guidance
  mark_scheme_points JSONB,  -- Individual mark points
  example_answer TEXT,  -- If provided
  
  -- Links to curriculum
  topic_codes TEXT[],  -- Which topics this tests
  assessment_objectives TEXT[],  -- AO1, AO2, AO3
  
  -- Metadata
  difficulty_level VARCHAR(20),  -- 'foundation', 'higher', 'standard'
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_exam_papers_subject ON exam_papers(exam_board_subject_id);
CREATE INDEX IF NOT EXISTS idx_exam_papers_year ON exam_papers(year DESC);
CREATE INDEX IF NOT EXISTS idx_exam_papers_series ON exam_papers(exam_series);
CREATE INDEX IF NOT EXISTS idx_question_bank_paper ON question_bank(exam_paper_id);
CREATE INDEX IF NOT EXISTS idx_mark_scheme_insights_paper ON mark_scheme_insights(exam_paper_id);

-- Enable RLS
ALTER TABLE exam_papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE mark_scheme_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE examiner_report_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_bank ENABLE ROW LEVEL SECURITY;

-- RLS Policies (read for authenticated, write for service role)
CREATE POLICY "Allow authenticated read exam_papers" ON exam_papers FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow service role manage exam_papers" ON exam_papers FOR ALL TO service_role USING (true);

CREATE POLICY "Allow authenticated read mark_scheme_insights" ON mark_scheme_insights FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow service role manage mark_scheme_insights" ON mark_scheme_insights FOR ALL TO service_role USING (true);

CREATE POLICY "Allow authenticated read examiner_report_insights" ON examiner_report_insights FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow service role manage examiner_report_insights" ON examiner_report_insights FOR ALL TO service_role USING (true);

CREATE POLICY "Allow authenticated read question_bank" ON question_bank FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow service role manage question_bank" ON question_bank FOR ALL TO service_role USING (true);



