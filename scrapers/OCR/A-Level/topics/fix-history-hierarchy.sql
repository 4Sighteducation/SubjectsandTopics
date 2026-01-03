-- Check orphaned topics in History A
-- Find topics with parent_topic_id = NULL but should have parents

-- 1. See the orphaned topics
SELECT topic_code, topic_name, topic_level, parent_topic_id
FROM staging_aqa_topics
WHERE subject_id = (SELECT id FROM staging_aqa_subjects WHERE subject_code = 'H505')
  AND parent_topic_id IS NULL
  AND topic_level > 0
ORDER BY topic_code
LIMIT 50;

-- 2. Check Unit3 topics specifically
SELECT topic_code, topic_name, topic_level, parent_topic_id
FROM staging_aqa_topics
WHERE subject_id = (SELECT id FROM staging_aqa_subjects WHERE subject_code = 'H505')
  AND topic_code LIKE 'Unit3_%'
ORDER BY topic_code;

-- 3. See if Unit3_8, Unit3_9, etc exist
SELECT topic_code, topic_name, topic_level
FROM staging_aqa_topics
WHERE subject_id = (SELECT id FROM staging_aqa_subjects WHERE subject_code = 'H505')
  AND topic_code IN ('Unit3_8', 'Unit3_9', 'Unit3_10', 'Unit3_11', 'Unit3_12')
ORDER BY topic_code;

