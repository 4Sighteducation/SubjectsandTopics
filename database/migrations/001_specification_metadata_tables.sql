-- Migration 001: Add Specification Metadata Tables
-- Purpose: Capture complete specification context including constraints and component structure

-- 1. Specification Metadata (main overview)
CREATE TABLE IF NOT EXISTS specification_metadata (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  exam_board VARCHAR(50) NOT NULL,
  qualification_type VARCHAR(50) NOT NULL,
  subject_name VARCHAR(100) NOT NULL,
  subject_code VARCHAR(20),
  spec_version VARCHAR(50),
  
  -- Overview information
  subject_description TEXT,
  total_guided_learning_hours INTEGER,
  assessment_overview TEXT,
  
  -- URLs and source
  specification_url TEXT,
  specification_pdf_url TEXT,
  source_page_url TEXT,
  
  -- Metadata
  scraped_date TIMESTAMP DEFAULT NOW(),
  last_verified TIMESTAMP,
  is_active BOOLEAN DEFAULT true,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(exam_board, qualification_type, subject_name)
);

-- 2. Specification Components
CREATE TABLE IF NOT EXISTS spec_components (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  spec_metadata_id UUID REFERENCES specification_metadata(id) ON DELETE CASCADE,
  component_code VARCHAR(10) NOT NULL,  -- C1, C2, C3
  component_name VARCHAR(200) NOT NULL,
  component_type VARCHAR(50),           -- breadth_study, depth_study, coursework
  
  -- Selection rules
  selection_type VARCHAR(50),           -- choose_one, choose_multiple, required_all, custom
  count_required INTEGER,               -- How many to choose
  total_available INTEGER,              -- Total options available
  
  -- Assessment info
  assessment_weight VARCHAR(20),        -- "40%"
  assessment_format TEXT,               -- "2.5 hour written exam"
  assessment_description TEXT,
  
  sort_order INTEGER,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. Selection Constraints
CREATE TABLE IF NOT EXISTS selection_constraints (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  spec_metadata_id UUID REFERENCES specification_metadata(id) ON DELETE CASCADE,
  constraint_type VARCHAR(50) NOT NULL,  -- geographic_diversity, prohibited_combination, etc.
  constraint_rule JSONB NOT NULL,        -- Flexible JSON for different rule types
  description TEXT,
  applies_to_components VARCHAR[],       -- Which components this affects
  created_at TIMESTAMP DEFAULT NOW()
);

-- 4. Subject Vocabulary
CREATE TABLE IF NOT EXISTS subject_vocabulary (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  spec_metadata_id UUID REFERENCES specification_metadata(id) ON DELETE CASCADE,
  term VARCHAR(200) NOT NULL,
  definition TEXT,
  category VARCHAR(50),                  -- concept, skill, assessment_term, etc.
  importance VARCHAR(20),                -- high, medium, low
  created_at TIMESTAMP DEFAULT NOW()
);

-- 5. Assessment Guidance
CREATE TABLE IF NOT EXISTS assessment_guidance (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  component_id UUID REFERENCES spec_components(id) ON DELETE CASCADE,
  question_type VARCHAR(100),            -- essay, source_analysis, etc.
  marks INTEGER,
  time_allocation VARCHAR(50),
  guidance_text TEXT,
  example_questions TEXT[],
  created_at TIMESTAMP DEFAULT NOW()
);

-- 6. Enhance existing curriculum_topics table
-- Add these columns if they don't exist
ALTER TABLE curriculum_topics ADD COLUMN IF NOT EXISTS
  component_code VARCHAR(10);            -- Links to spec_components
ALTER TABLE curriculum_topics ADD COLUMN IF NOT EXISTS
  topic_code VARCHAR(20);                -- e.g., "1C", "2A"
ALTER TABLE curriculum_topics ADD COLUMN IF NOT EXISTS
  topic_type VARCHAR(50);                -- breadth_study, depth_study, etc.
ALTER TABLE curriculum_topics ADD COLUMN IF NOT EXISTS
  chronological_period VARCHAR(50);      -- e.g., "1485-1603"
ALTER TABLE curriculum_topics ADD COLUMN IF NOT EXISTS
  period_start_year INTEGER;             -- 1485
ALTER TABLE curriculum_topics ADD COLUMN IF NOT EXISTS
  period_end_year INTEGER;               -- 1603
ALTER TABLE curriculum_topics ADD COLUMN IF NOT EXISTS
  period_length_years INTEGER;           -- 118
ALTER TABLE curriculum_topics ADD COLUMN IF NOT EXISTS
  geographical_region VARCHAR(50);       -- British, European, American, etc.
ALTER TABLE curriculum_topics ADD COLUMN IF NOT EXISTS
  key_themes JSONB;                      -- Array of main themes
ALTER TABLE curriculum_topics ADD COLUMN IF NOT EXISTS
  assessment_focus TEXT;                 -- What's tested
ALTER TABLE curriculum_topics ADD COLUMN IF NOT EXISTS
  page_reference VARCHAR(50);            -- "page 18"

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_spec_metadata_board_qual_subject 
  ON specification_metadata(exam_board, qualification_type, subject_name);

CREATE INDEX IF NOT EXISTS idx_spec_components_metadata 
  ON spec_components(spec_metadata_id);

CREATE INDEX IF NOT EXISTS idx_curriculum_topics_component 
  ON curriculum_topics(component_code);

CREATE INDEX IF NOT EXISTS idx_curriculum_topics_region 
  ON curriculum_topics(geographical_region);

CREATE INDEX IF NOT EXISTS idx_curriculum_topics_period 
  ON curriculum_topics(period_start_year, period_end_year);

CREATE INDEX IF NOT EXISTS idx_curriculum_topics_code
  ON curriculum_topics(topic_code);

-- Create update trigger for specification_metadata
CREATE OR REPLACE FUNCTION update_specification_metadata_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_specification_metadata
  BEFORE UPDATE ON specification_metadata
  FOR EACH ROW
  EXECUTE FUNCTION update_specification_metadata_updated_at();

-- Create update trigger for spec_components
CREATE TRIGGER trigger_update_spec_components
  BEFORE UPDATE ON spec_components
  FOR EACH ROW
  EXECUTE FUNCTION update_specification_metadata_updated_at();

-- Enable Row Level Security (RLS) for new tables
ALTER TABLE specification_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE spec_components ENABLE ROW LEVEL SECURITY;
ALTER TABLE selection_constraints ENABLE ROW LEVEL SECURITY;
ALTER TABLE subject_vocabulary ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_guidance ENABLE ROW LEVEL SECURITY;

-- Create policies (allow authenticated users to read, service role to write)
CREATE POLICY "Allow authenticated users to read specification_metadata"
  ON specification_metadata FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Allow service role to manage specification_metadata"
  ON specification_metadata FOR ALL
  TO service_role
  USING (true);

-- Repeat for other tables
CREATE POLICY "Allow authenticated users to read spec_components"
  ON spec_components FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow service role to manage spec_components"
  ON spec_components FOR ALL TO service_role USING (true);

CREATE POLICY "Allow authenticated users to read selection_constraints"
  ON selection_constraints FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow service role to manage selection_constraints"
  ON selection_constraints FOR ALL TO service_role USING (true);

CREATE POLICY "Allow authenticated users to read subject_vocabulary"
  ON subject_vocabulary FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow service role to manage subject_vocabulary"
  ON subject_vocabulary FOR ALL TO service_role USING (true);

CREATE POLICY "Allow authenticated users to read assessment_guidance"
  ON assessment_guidance FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow service role to manage assessment_guidance"
  ON assessment_guidance FOR ALL TO service_role USING (true);
