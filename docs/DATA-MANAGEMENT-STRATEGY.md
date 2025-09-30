# Data Management Strategy - Handling Old vs New Data

## Current Situation

**Existing in Supabase:**
- 22,770 curriculum_topics (from old CSV import)
- No enhanced metadata (no component_code, geographical_region, etc.)
- Working with your app currently

**What New Scraper Creates:**
- Enhanced curriculum_topics with rich metadata
- Hierarchical structure (levels 0, 1, 2)
- Component codes, constraints, vocabul

ary

---

## Solution: Version Markers ✅

After running migration `003_add_scraping_markers.sql`, every topic will have:

### New Columns:
```sql
scraping_version:     'legacy', 'v2_enhanced', or 'v2_web'
scraping_source:      'manual_import', 'pdf_scraper', 'web_scraper'
data_quality_score:   1-5 (higher = more complete)
has_detailed_content: true/false
last_scraped:         timestamp
```

### Marking Strategy:

**Old Topics (22,770):**
```sql
scraping_version = 'legacy'  (or NULL)
scraping_source = 'manual_import'
data_quality_score = 2  (basic data only)
```

**New Topics (from pipeline):**
```sql
scraping_version = 'v2_enhanced'
scraping_source = 'web_scraper'  
data_quality_score = 4-5  (rich metadata!)
has_detailed_content = true
last_scraped = now()
```

---

## Querying Data

### Get ONLY new enhanced topics:
```sql
SELECT * FROM curriculum_topics
WHERE scraping_version = 'v2_enhanced';
```

### Get ONLY old legacy topics:
```sql
SELECT * FROM curriculum_topics
WHERE scraping_version = 'legacy' OR scraping_version IS NULL;
```

### Use the convenient views:
```sql
-- Enhanced topics only
SELECT * FROM curriculum_topics_enhanced;

-- Legacy topics only
SELECT * FROM curriculum_topics_legacy;
```

---

## App Integration Options

### Option A: Use Both (Transition Period)
```typescript
// In your app, query both and merge
const legacy = await supabase.from('curriculum_topics_legacy').select('*');
const enhanced = await supabase.from('curriculum_topics_enhanced').select('*');

// Prefer enhanced if available, fallback to legacy
```

### Option B: Switch to Enhanced Only
```typescript
// Only use new enhanced topics
const topics = await supabase.from('curriculum_topics_enhanced').select('*');
```

### Option C: Gradual Migration
```typescript
// Check if enhanced version exists for this subject
// If yes, use enhanced
// If no, use legacy
```

---

## Timeline Strategy

### Tonight/Tomorrow: Coexistence
1. ✅ Run migration (add marker columns)
2. ✅ Mark all existing topics as 'legacy'
3. ✅ Run scraper - creates new 'v2_enhanced' records
4. ✅ Both exist side by side
5. ✅ App continues working with old data
6. ✅ You can test new data separately

### Next Week: Switch to Enhanced
1. Update app to use `curriculum_topics_enhanced` view
2. Test thoroughly
3. If working well, archive legacy data

### Later: Cleanup
1. Delete or archive legacy topics
2. Or keep permanently for comparison

---

## Exam Papers - Completely Separate! ✅

**Assessment resources are DIFFERENT tables:**
- `exam_papers` - Metadata about papers
- `mark_scheme_insights` - AI analysis of mark schemes
- `examiner_report_insights` - Common mistakes, advice
- `question_bank` - Individual questions

**These do NOT conflict with curriculum_topics!**

Separate scraper, separate tables, separate process.

---

## Immediate Actions

### 1. Run Migration (5 minutes)
```sql
-- In Supabase SQL Editor, run:
-- 003_add_scraping_markers.sql
```

### 2. Mark Existing Topics as Legacy (5 minutes)
```sql
-- Mark all current topics as legacy
UPDATE curriculum_topics
SET scraping_version = 'legacy',
    scraping_source = 'manual_import',
    data_quality_score = 2
WHERE scraping_version IS NULL;
```

### 3. Test Scraper WITHOUT Upload (30 mins)
```bash
python pipeline_complete_aqa.py --no-upload --test
```

Review JSON files in `data/processed/`

### 4. Run Full Scraper WITH Upload (2-3 hours)
```bash
python pipeline_complete_aqa.py --qualification a_level
```

New topics will have `scraping_version = 'v2_enhanced'`

### 5. Verify in Supabase
```sql
-- Count by version
SELECT scraping_version, COUNT(*) 
FROM curriculum_topics 
GROUP BY scraping_version;

-- Should show:
-- legacy: 22,770
-- v2_enhanced: ~1,500-2,000 (from new scraper)
```

---

## Benefits of This Approach

✅ **Safe:** Old data untouched, app keeps working  
✅ **Identifiable:** Can easily tell old vs new  
✅ **Flexible:** Can query either or both  
✅ **Testable:** Can test new data without disrupting users  
✅ **Reversible:** Can always go back to legacy  
✅ **Gradual:** Can migrate app feature by feature  

---

## Ready to Proceed?

1. Run migration 003 in Supabase
2. Mark existing topics as 'legacy'
3. Test scraper
4. Run full A-Level scrape

Want me to guide you through each step? 🚀




