-- SAFE CLEANUP - Only components and constraints (no topic deletion)

-- 1. Remove duplicate components (keep newest)
WITH ranked_components AS (
  SELECT id, 
         ROW_NUMBER() OVER (
           PARTITION BY spec_metadata_id, component_code 
           ORDER BY created_at DESC
         ) as rn
  FROM spec_components
)
DELETE FROM spec_components
WHERE id IN (
  SELECT id FROM ranked_components WHERE rn > 1
);

-- 2. Remove duplicate constraints (keep newest)
WITH ranked_constraints AS (
  SELECT id,
         ROW_NUMBER() OVER (
           PARTITION BY spec_metadata_id, constraint_type, description
           ORDER BY created_at DESC
         ) as rn
  FROM selection_constraints
)
DELETE FROM selection_constraints
WHERE id IN (
  SELECT id FROM ranked_constraints WHERE rn > 1
);

-- 3. SKIP topic cleanup - let UPSERT handle it during batch run

-- 4. Verify
SELECT 
  'Components' as item,
  COUNT(*) as total_count,
  COUNT(DISTINCT (spec_metadata_id, component_code)) as unique_count
FROM spec_components
WHERE spec_metadata_id IN (
  SELECT id FROM specification_metadata WHERE exam_board = 'AQA'
)
UNION ALL
SELECT 
  'Constraints',
  COUNT(*),
  COUNT(DISTINCT (spec_metadata_id, constraint_type, description))
FROM selection_constraints
WHERE spec_metadata_id IN (
  SELECT id FROM specification_metadata WHERE exam_board = 'AQA'
);







