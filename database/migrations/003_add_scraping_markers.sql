-- Migration 003: Add Scraping Version Markers
-- Allows distinguishing between old and new enhanced records

-- Add columns to curriculum_topics to track scraping source
ALTER TABLE curriculum_topics ADD COLUMN IF NOT EXISTS
  scraping_version VARCHAR(20) DEFAULT 'legacy';  -- 'legacy', 'v2_enhanced', 'v2_web'

ALTER TABLE curriculum_topics ADD COLUMN IF NOT EXISTS
  scraping_source VARCHAR(50);  -- 'manual_import', 'pdf_scraper', 'web_scraper', 'ai_enhanced'

ALTER TABLE curriculum_topics ADD COLUMN IF NOT EXISTS
  data_quality_score INTEGER;  -- 1-5, higher = more complete/accurate

ALTER TABLE curriculum_topics ADD COLUMN IF NOT EXISTS
  has_detailed_content BOOLEAN DEFAULT false;  -- True if has Level 1-2 children

ALTER TABLE curriculum_topics ADD COLUMN IF NOT EXISTS
  last_scraped TIMESTAMP;  -- When this was last updated by scraper

-- Add index for querying by version
CREATE INDEX IF NOT EXISTS idx_curriculum_topics_scraping_version 
  ON curriculum_topics(scraping_version);

CREATE INDEX IF NOT EXISTS idx_curriculum_topics_source
  ON curriculum_topics(scraping_source);

-- Create a view for enhanced topics only
CREATE OR REPLACE VIEW curriculum_topics_enhanced AS
SELECT * FROM curriculum_topics
WHERE scraping_version IN ('v2_enhanced', 'v2_web')
  AND is_active = true;

-- Create a view for legacy topics only  
CREATE OR REPLACE VIEW curriculum_topics_legacy AS
SELECT * FROM curriculum_topics
WHERE scraping_version = 'legacy' OR scraping_version IS NULL;

-- Function to calculate data quality score
CREATE OR REPLACE FUNCTION calculate_topic_quality_score(topic_id UUID)
RETURNS INTEGER AS $$
DECLARE
  score INTEGER := 1;
  topic RECORD;
BEGIN
  SELECT * INTO topic FROM curriculum_topics WHERE id = topic_id;
  
  -- Base score
  IF topic.topic_name IS NOT NULL THEN score := score + 1; END IF;
  
  -- Enhanced metadata
  IF topic.component_code IS NOT NULL THEN score := score + 1; END IF;
  IF topic.geographical_region IS NOT NULL THEN score := score + 1; END IF;
  IF topic.chronological_period IS NOT NULL THEN score := score + 1; END IF;
  IF topic.key_themes IS NOT NULL THEN score := score + 1; END IF;
  
  -- Hierarchical completeness
  IF topic.has_detailed_content THEN score := score + 2; END IF;
  
  RETURN LEAST(score, 5);  -- Cap at 5
END;
$$ LANGUAGE plpgsql;

-- Comment explaining the versioning
COMMENT ON COLUMN curriculum_topics.scraping_version IS 
  'Tracks which version of scraper created this: legacy (old import), v2_enhanced (PDF+AI), v2_web (website HTML)';

COMMENT ON COLUMN curriculum_topics.data_quality_score IS
  'Quality score 1-5: 1=basic, 5=complete with all metadata and hierarchical content';
