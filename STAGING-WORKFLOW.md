### Staging Tables Workflow

## Why Staging Tables?

**Problem:** Can't test scrapers without risking production data  
**Solution:** Scrape into staging first, validate, THEN promote to production

## Workflow:

### Phase 1: Scrape to Staging
```bash
# Scrape AQA into staging tables
python scraper.py --target staging --board AQA

# Result: All data goes to:
# - curriculum_topics_staging
# - specification_metadata_staging
# - spec_components_staging
# - selection_constraints_staging
```

### Phase 2: Validate Staging Data
```sql
-- Check what we got
SELECT * FROM staging_summary;

-- Compare with production
SELECT 
  'Production' as source,
  subject_name,
  COUNT(*) as topic_count
FROM curriculum_topics
WHERE exam_board = 'AQA'
GROUP BY subject_name
UNION ALL
SELECT 
  'Staging',
  subject_name,
  COUNT(*)
FROM curriculum_topics_staging  
WHERE exam_board = 'AQA'
GROUP BY subject_name
ORDER BY subject_name, source;

-- If staging has FEWER topics, scraper needs fixing!
-- If staging looks good, proceed to Phase 3
```

### Phase 3: Promote to Production (Only If Valid!)
```sql
-- Delete old AQA data
DELETE FROM curriculum_topics WHERE exam_board_subject_id IN (...);

-- Copy staging to production
INSERT INTO curriculum_topics (
  exam_board_subject_id, topic_code, topic_name, topic_level,
  component_code, chronological_period, geographical_region, ...
)
SELECT ...
FROM curriculum_topics_staging
WHERE scrape_run_id = 'run_20251001_120000';
```

## Benefits:

✅ **Safe testing** - Production data untouched  
✅ **Easy comparison** - See exactly what's different  
✅ **Rollback** - Just delete staging data and try again  
✅ **No pressure** - Can iterate until perfect  

## For Multiple Exam Boards:

```bash
# Test each board separately in staging
python scraper.py --target staging --board AQA
python scraper.py --target staging --board OCR  
python scraper.py --target staging --board Edexcel

# Validate all three
# Promote all three at once when ready
```




















