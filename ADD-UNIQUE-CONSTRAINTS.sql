-- ADD UNIQUE CONSTRAINTS TO PREVENT DUPLICATES

-- 1. Unique constraint on spec_components (one component per code per spec)
ALTER TABLE spec_components
ADD CONSTRAINT unique_spec_component 
UNIQUE (spec_metadata_id, component_code);

-- 2. Unique constraint on curriculum_topics (one topic per code per subject)
ALTER TABLE curriculum_topics
ADD CONSTRAINT unique_topic_per_subject
UNIQUE (exam_board_subject_id, topic_code)
WHERE topic_code IS NOT NULL;

-- 3. For constraints, we can't easily add unique since description might vary
-- But we can add index to help with queries
CREATE INDEX IF NOT EXISTS idx_constraints_type_spec
ON selection_constraints(spec_metadata_id, constraint_type);





