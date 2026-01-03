-- DIAGNOSTIC (FLASH DB): Find where embeddings (pgvector) live
-- Paste into Supabase SQL editor and run.
--
-- NOTE: This project’s embeddings are expected to be in public.topic_ai_metadata.embedding (vector(1536)),
-- but this query will also find any other vector columns if they exist.

-- 1) Verify pgvector extension
SELECT
  'pgvector extension' AS check_name,
  extname,
  extversion
FROM pg_extension
WHERE extname = 'vector';

-- 2) List all vector-typed columns
SELECT
  n.nspname AS schema_name,
  c.relname AS table_name,
  a.attname AS column_name,
  pg_catalog.format_type(a.atttypid, a.atttypmod) AS column_type
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE a.attnum > 0
  AND NOT a.attisdropped
  AND pg_catalog.format_type(a.atttypid, a.atttypmod) LIKE 'vector(%'
ORDER BY schema_name, table_name, column_name;

-- 3) Indexes on topic_ai_metadata (if present)
SELECT
  indexname,
  indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename = 'topic_ai_metadata'
ORDER BY indexname;

-- 4) Row counts + breakdown
SELECT COUNT(*) AS topic_ai_metadata_rows
FROM public.topic_ai_metadata;

SELECT
  exam_board,
  qualification_level,
  COUNT(*) AS rows
FROM public.topic_ai_metadata
GROUP BY exam_board, qualification_level
ORDER BY exam_board, qualification_level;






