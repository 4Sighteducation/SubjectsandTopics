# AQA Curriculum Database - Quick Start

## What This Is

**Isolated database tables for AQA exam board data.**

Completely separate from your main FLASH app database, so you can:
- ✅ Test and iterate safely
- ✅ Perfect the data without risk
- ✅ Integrate when ready

## Setup (5 Minutes)

### Step 1: Create Tables in Supabase

Run this SQL in your Supabase SQL Editor:

```bash
# File location:
database/schemas/CREATE-AQA-SCHEMA.sql
```

This creates:
- `aqa_subjects` (subject metadata)
- `aqa_topics` (full hierarchy with parent-child relationships)
- `aqa_components` (selection rules)
- `aqa_constraints` (validation rules)
- `aqa_exam_papers` (past papers)
- Plus views and helper functions

**Verify:**
```sql
SELECT tablename FROM pg_tables 
WHERE tablename LIKE 'aqa%' 
ORDER BY tablename;
```

Should show 8 tables.

---

## Test (Proof of Concept)

### Run Law Test:

```bash
python test_aqa_database_proof.py
```

**This will:**
1. Scrape Law A-Level from AQA website
2. Extract ~56 topics with 2-level hierarchy
3. Upload to `aqa_*` tables
4. Verify parent-child relationships work

**Expected output:**
```
✓ Scraped 56 raw topics
✓ Organized into levels:
  Level 0: 5 topics
  Level 1: 51 topics
✓ Uploaded to AQA database:
  Subject ID: [UUID]
  Topics: 56
  Components: 3
  Constraints: 1
✓ Hierarchy: Working!
```

### Check in Supabase:

```sql
-- See subject
SELECT * FROM aqa_subjects WHERE subject_code = '7162';

-- See topic breakdown
SELECT * FROM aqa_subject_stats WHERE subject_name = 'Law';

-- See full hierarchy
SELECT * FROM get_aqa_topic_hierarchy('7162');

-- See sample parent-child relationships
SELECT 
  topic_code,
  topic_name,
  topic_level,
  parent_topic_id
FROM aqa_topics
WHERE subject_id IN (SELECT id FROM aqa_subjects WHERE subject_code = '7162')
ORDER BY topic_level, topic_code
LIMIT 20;
```

---

## How the Scraper Works

### Recursive Web Scraping (FREE!)

**For subjects with tables (Law, Physical Education):**
1. Finds main sections (3.1, 3.2, 3.3)
2. Visits each section's detail page
3. Extracts table rows (all content)
4. Organizes by classification numbers

**For subjects with headings (Psychology):**
1. Finds main sections
2. Extracts h3/h4 headings as topics
3. Captures bullet points as content

**Result:** 50-200 topics per subject depending on complexity.

### Topic Organization

**Smart number parsing:**
- "3.1" → Level 0 (main unit)
- "3.1.1 Applied anatomy" → Level 1 (parent: 3.1)
- "Cardiovascular drift" (no number) → Level 2 (child of previous numbered topic)

**Builds proper parent_topic_id relationships automatically!**

---

## Current Status

✅ **Working:**
- Law: 56 topics with hierarchy
- Psychology: 30+ topics with hierarchy  
- Physical Education: 174 topics
- Schema with proper constraints

⚠️ **Needs Work:**
- Some subjects have different formats
- English Literature needs text list extraction
- Some topics might need AI for complex PDFs

**Good enough for proof of concept!**

---

## Files Created

```
flash-curriculum-pipeline/
├── database/
│   ├── schemas/
│   │   └── CREATE-AQA-SCHEMA.sql          ← Run this in Supabase
│   └── uploaders/
│       └── aqa_uploader.py                ← Handles AQA database uploads
│
├── scrapers/uk/
│   └── aqa_recursive_web_scraper.py       ← Scrapes with hierarchy
│
├── organize_topics_by_numbers.py          ← Determines levels from codes
├── test_aqa_database_proof.py             ← Complete test workflow
│
└── docs/
    ├── COMPLETE-DATABASE-ARCHITECTURE.md  ← Full architecture
    └── SEPARATE-DATABASES-ARCHITECTURE.md ← Strategy overview
```

---

## Next Steps

### Today (Before Returning to App):

1. **Run schema** in Supabase (2 min)
2. **Run test** with Law (5 min)
3. **Verify** in Supabase (3 min)
4. **Commit to GitHub** (5 min)

**Total: 15 minutes**, then you're done!

### When You Return to Scrapers (Weeks/Months Later):

1. **Improve scraper** for remaining subjects
2. **Add OCR** database and scraper
3. **Add Edexcel** database and scraper
4. **Perfect data quality** for all boards

### When Ready to Integrate:

1. **Create unified view:**
```sql
CREATE VIEW curriculum_unified AS
SELECT * FROM aqa_topics
UNION ALL
SELECT * FROM ocr_topics;
```

2. **Update app** to query view
3. **Test thoroughly**
4. **Roll out to users**

---

## Cost Summary

**AQA Database (This approach):**
- Scraping: FREE (web scraping, no AI)
- Testing: FREE (isolated database)
- Iteration: FREE (can re-scrape anytime)

**Per subject:**
- Web scraping: $0 (FREE!)
- AI only if needed for complex layouts: ~$0.20

**Total for 68 AQA subjects:** ~$0-15 (depending on how many need AI)

---

## Support

**If you need to:**

**Delete AQA database:**
```sql
DROP TABLE IF EXISTS aqa_question_bank CASCADE;
DROP TABLE IF EXISTS aqa_examiner_report_insights CASCADE;
DROP TABLE IF EXISTS aqa_mark_scheme_insights CASCADE;
DROP TABLE IF EXISTS aqa_exam_papers CASCADE;
DROP TABLE IF EXISTS aqa_constraints CASCADE;
DROP TABLE IF EXISTS aqa_components CASCADE;
DROP TABLE IF EXISTS aqa_topics CASCADE;
DROP TABLE IF EXISTS aqa_subjects CASCADE;
DROP VIEW IF EXISTS aqa_topics_with_subject CASCADE;
DROP VIEW IF EXISTS aqa_subject_stats CASCADE;
DROP FUNCTION IF EXISTS get_aqa_topic_hierarchy CASCADE;
```

**Re-scrape one subject:**
```bash
python test_aqa_database_proof.py --subject "Biology" --code "7402"
```

**Check data quality:**
```sql
-- See all subjects
SELECT * FROM aqa_subject_stats;

-- See hierarchy for one subject
SELECT * FROM get_aqa_topic_hierarchy('7162');
```

---

## Success Criteria

**The proof of concept is successful if:**

✅ Law uploads with no errors  
✅ 50+ topics in aqa_topics table  
✅ Parent-child relationships working (check parent_topic_id not null)  
✅ Components show proper selection rules  
✅ Can query data easily in Supabase  

**If all true:** Architecture validated, ready for production use later!

---

**Ready? Run the test!**

```bash
python test_aqa_database_proof.py
```

















