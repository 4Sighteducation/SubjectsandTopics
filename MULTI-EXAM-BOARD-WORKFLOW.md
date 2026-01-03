# Multi-Exam Board Staging & Production Workflow

**Date:** November 21, 2025  
**Status:** Architecture Document  
**Problem:** Need to scrape multiple exam boards + update continuously without breaking production

---

## 📊 CURRENT SITUATION

### Completed
- ✅ **Edexcel A-Level:** 33/37 subjects (89%)
- ✅ **Edexcel GCSE:** 28/35 subjects (80%)
- ✅ **Edexcel International GCSE:** Data scraped
- ✅ **Edexcel International A-Level:** Data scraped

### To Scrape
- ⏳ **AQA:** Already have some data in production
- ⏳ **OCR:** Partially done
- ⏳ **WJEC Eduqas:** Not started
- ⏳ **CCEA:** Not started (Northern Ireland)
- ⏳ **UAL:** Not started (Arts & Design)
- ⏳ **Cambridge International:** Partially done
- ⏳ **IB:** Not started

### The Challenge
> "I still need to scrape some other exam boards... And I will need to be able to update in future anyway. So what happens next??"

---

## 🎯 THE SOLUTION: CONTINUOUS STAGING PIPELINE

### Core Principle
**Staging tables = Safe testing ground, Production tables = Live app data**

```
┌─────────────────────────────────────────────────────┐
│                 SCRAPING PIPELINE                   │
│                                                     │
│  1. Scrape → staging_aqa_* tables                  │
│  2. Validate → Check data quality                  │
│  3. Review → Manual QA if needed                   │
│  4. Promote → Move to production tables            │
│  5. Deploy → App uses updated data                 │
└─────────────────────────────────────────────────────┘
```

---

## 🏗️ DATABASE ARCHITECTURE

### Staging Tables (Keep Forever!)

```sql
-- Universal staging tables for ALL exam boards
-- Note: Despite name "staging_aqa_*", these work for all boards

staging_aqa_subjects
├─ Used for: ALL exam boards during scraping
├─ Columns: code, name, qualification_type, exam_board
├─ Purpose: Temporary holding area
└─ Lifespan: Cleared/refreshed per scraping session

staging_aqa_topics
├─ Linked to: staging_aqa_subjects
├─ Purpose: Test topic hierarchies before production
└─ Columns: topic_code, topic_name, level, parent_topic_id

staging_aqa_exam_papers
├─ Linked to: staging_aqa_subjects
├─ Purpose: Store paper metadata + URLs
└─ Columns: paper_number, year, series, type, url
```

### Production Tables (App Uses These)

```sql
exam_boards (6+ boards)
├─ AQA, Edexcel, OCR, WJEC, CCEA, Cambridge, IB
└─ Columns: code, full_name, active

qualification_types (7+ types)
├─ GCSE, A-Level, International-GCSE, International-A-Level
├─ Foundation, BTEC, IB, AP
└─ Columns: code, full_name

exam_board_subjects
├─ Links: exam_board + qualification_type
├─ Example: "Biology GCSE" under Edexcel
└─ Columns: subject_name, subject_code, exam_board_id, qualification_type_id, is_current

curriculum_topics
├─ Links: exam_board_subjects
├─ Full hierarchy with parent_topic_id
└─ Columns: topic_name, topic_code, topic_level, parent_topic_id, exam_board_subject_id

exam_papers (NEW TABLE NEEDED)
├─ Links: exam_board_subjects
├─ Paper metadata + download URLs
└─ Columns: paper_number, year, series, type, url, title, marks
```

---

## 🔄 WORKFLOW FOR EACH EXAM BOARD

### Phase 1: Scraping (Per Exam Board)

```bash
# Example: Scraping WJEC Eduqas A-Level Biology
cd scrapers/WJEC/A-Level/topics
python scrape-biology.py

# Uploads to staging_aqa_subjects + staging_aqa_topics
# exam_board = 'WJEC'
# qualification_type = 'A-Level'
```

**Key Point:** All scrapers write to same staging tables, differentiated by `exam_board` column.

### Phase 2: Validation

```sql
-- Check what was scraped
SELECT 
  exam_board,
  qualification_type,
  COUNT(DISTINCT s.id) as subjects,
  COUNT(t.id) as topics,
  MAX(t.topic_level) as max_depth
FROM staging_aqa_subjects s
LEFT JOIN staging_aqa_topics t ON s.id = t.subject_id
WHERE exam_board = 'WJEC'
GROUP BY exam_board, qualification_type;

-- Expected output:
-- WJEC | A-Level | 25 subjects | 3,500 topics | depth 4
```

**Validation Checks:**
- ✅ Subject count reasonable?
- ✅ Topics linked correctly?
- ✅ Hierarchy valid (no orphans)?
- ✅ Max depth appropriate (3-6 levels)?
- ✅ No duplicate subjects?

### Phase 3: Manual Review (Optional)

Use `data-viewer-v2.html`:
```
1. Open in browser
2. Filter by: WJEC + A-Level
3. Browse subjects
4. Click topics → verify hierarchy
5. Edit if needed (inline editing)
```

### Phase 4: Promotion to Production

```sql
-- Run promotion script
-- File: promote-staging-to-production.sql

BEGIN;

-- 1. Get or create exam board
INSERT INTO exam_boards (code, full_name, active)
VALUES ('WJEC', 'WJEC Eduqas', true)
ON CONFLICT (code) DO NOTHING;

-- 2. Promote subjects
INSERT INTO exam_board_subjects (
  subject_code,
  subject_name,
  exam_board_id,
  qualification_type_id,
  is_current,
  created_at,
  updated_at
)
SELECT 
  s.code,
  s.name,
  eb.id,
  qt.id,
  true,
  NOW(),
  NOW()
FROM staging_aqa_subjects s
JOIN exam_boards eb ON s.exam_board = eb.code
JOIN qualification_types qt ON s.qualification_type = qt.code
WHERE s.exam_board = 'WJEC'
  AND s.qualification_type = 'A-Level'
ON CONFLICT (subject_code, exam_board_id, qualification_type_id) 
DO UPDATE SET
  subject_name = EXCLUDED.subject_name,
  is_current = true,
  updated_at = NOW();

-- 3. Promote topics
INSERT INTO curriculum_topics (
  exam_board_subject_id,
  topic_code,
  topic_name,
  topic_level,
  parent_topic_id,
  sort_order,
  created_at,
  updated_at
)
SELECT 
  prod_subj.id,
  st.topic_code,
  st.topic_name,
  st.topic_level,
  -- Map parent_topic_id from staging to production
  (SELECT pt.id FROM curriculum_topics pt 
   WHERE pt.topic_code = staging_parent.topic_code 
   AND pt.exam_board_subject_id = prod_subj.id
   LIMIT 1),
  st.sort_order,
  NOW(),
  NOW()
FROM staging_aqa_topics st
JOIN staging_aqa_subjects ss ON st.subject_id = ss.id
JOIN exam_board_subjects prod_subj ON 
  prod_subj.subject_code = ss.code 
  AND prod_subj.exam_board_id = (SELECT id FROM exam_boards WHERE code = ss.exam_board)
LEFT JOIN staging_aqa_topics staging_parent ON st.parent_topic_id = staging_parent.id
WHERE ss.exam_board = 'WJEC'
  AND ss.qualification_type = 'A-Level'
ON CONFLICT (topic_code, exam_board_subject_id)
DO UPDATE SET
  topic_name = EXCLUDED.topic_name,
  topic_level = EXCLUDED.topic_level,
  parent_topic_id = EXCLUDED.parent_topic_id,
  sort_order = EXCLUDED.sort_order,
  updated_at = NOW();

COMMIT;
```

### Phase 5: Cleanup Staging (Optional)

```sql
-- Clear staging for next scrape
DELETE FROM staging_aqa_topics 
WHERE subject_id IN (
  SELECT id FROM staging_aqa_subjects 
  WHERE exam_board = 'WJEC'
);

DELETE FROM staging_aqa_subjects 
WHERE exam_board = 'WJEC';
```

---

## 🔄 UPDATING EXISTING DATA

### Scenario: Edexcel Updates Their Specs

```bash
# 1. Re-run scrapers
cd scrapers/Edexcel/A-Level/topics
python scrape-business-improved.py

# 2. Staging tables now have NEW Edexcel data

# 3. Compare with production
SELECT 
  'Staging' as source,
  COUNT(*) as topics
FROM staging_aqa_topics st
JOIN staging_aqa_subjects ss ON st.subject_id = ss.id
WHERE ss.code = '9BS0' AND ss.exam_board = 'Edexcel'

UNION ALL

SELECT 
  'Production' as source,
  COUNT(*) as topics
FROM curriculum_topics ct
JOIN exam_board_subjects ebs ON ct.exam_board_subject_id = ebs.id
WHERE ebs.subject_code = '9BS0';

-- If difference found, re-promote to production
```

### Versioning Strategy

```sql
-- Add version tracking to subjects
ALTER TABLE exam_board_subjects
ADD COLUMN spec_version VARCHAR(20), -- e.g., '2024', '2025'
ADD COLUMN spec_start_year INT,     -- 2024
ADD COLUMN spec_end_year INT;       -- 2027 (null if current)

-- Mark old spec as inactive
UPDATE exam_board_subjects
SET is_current = false,
    spec_end_year = 2024
WHERE subject_code = '9BS0'
  AND spec_version = '2015';

-- Promote new spec as current
-- (promotion script from Phase 4)
```

---

## 📋 SCRAPING PRIORITY ORDER

### Immediate (Next 2 Weeks)
1. **Complete Edexcel** (4 A-Level + 7 GCSE subjects remaining)
2. **AQA Refresh** (Update existing data)
3. **OCR A-Level** (High priority - popular board)

### Short-term (Next Month)
4. **OCR GCSE** 
5. **WJEC Eduqas A-Level** (Wales)
6. **WJEC Eduqas GCSE**
7. **Cambridge International GCSE**
8. **Cambridge International A-Level**

### Medium-term (Next Quarter)
9. **CCEA A-Level** (Northern Ireland)
10. **CCEA GCSE**
11. **UAL** (Arts & Design - specialized)
12. **IB Diploma** (International)

---

## 🛠️ AUTOMATION TOOLS NEEDED

### 1. Batch Promotion Script

```python
# promote_batch.py
import sys
from database import supabase

def promote_exam_board(exam_board: str, qualification: str):
    """
    Promote all subjects for an exam board + qualification
    from staging to production
    """
    print(f"🚀 Promoting {exam_board} {qualification}...")
    
    # Run promotion SQL
    result = supabase.rpc('promote_staging_to_production', {
        'p_exam_board': exam_board,
        'p_qualification': qualification
    })
    
    print(f"✅ Promoted {result['subjects']} subjects, {result['topics']} topics")

if __name__ == '__main__':
    promote_exam_board(sys.argv[1], sys.argv[2])

# Usage:
# python promote_batch.py WJEC A-Level
```

### 2. Validation Report Generator

```python
# validate_staging.py
def generate_validation_report(exam_board: str):
    """
    Generate HTML report showing:
    - Subject count
    - Topic count per subject
    - Hierarchy depth
    - Orphaned topics
    - Missing data
    """
    # Query staging tables
    # Generate HTML report
    # Open in browser
    pass
```

### 3. Diff Tool (Staging vs Production)

```python
# diff_staging_production.py
def compare_versions(subject_code: str):
    """
    Show differences between staging and production
    for a specific subject
    """
    staging = get_staging_topics(subject_code)
    production = get_production_topics(subject_code)
    
    added = staging - production
    removed = production - staging
    modified = detect_changes(staging, production)
    
    print(f"Added: {len(added)} topics")
    print(f"Removed: {len(removed)} topics")
    print(f"Modified: {len(modified)} topics")
```

---

## 🔒 SAFETY MEASURES

### 1. Backup Before Promotion

```sql
-- Automatic backup
CREATE TABLE curriculum_topics_backup_20250121 AS
SELECT * FROM curriculum_topics
WHERE exam_board_subject_id IN (
  SELECT id FROM exam_board_subjects 
  WHERE exam_board_id = (SELECT id FROM exam_boards WHERE code = 'Edexcel')
);
```

### 2. Rollback Procedure

```sql
-- If something goes wrong
BEGIN;

-- Restore from backup
DELETE FROM curriculum_topics 
WHERE exam_board_subject_id IN (...);

INSERT INTO curriculum_topics 
SELECT * FROM curriculum_topics_backup_20250121;

COMMIT;
```

### 3. Phased Rollout

```sql
-- Add flag to control which data app uses
ALTER TABLE exam_board_subjects
ADD COLUMN live_in_app BOOLEAN DEFAULT false;

-- Promote to production but don't show in app yet
UPDATE exam_board_subjects
SET live_in_app = false
WHERE exam_board_id = (SELECT id FROM exam_boards WHERE code = 'WJEC');

-- Test thoroughly, then flip switch
UPDATE exam_board_subjects
SET live_in_app = true
WHERE exam_board_id = (SELECT id FROM exam_boards WHERE code = 'WJEC');
```

---

## 📊 STAGING WORKFLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────┐
│                    SCRAPING WORKFLOW                    │
└─────────────────────────────────────────────────────────┘

Step 1: SCRAPE
├─ Run scraper for exam board
├─ Writes to staging_aqa_subjects
├─ Writes to staging_aqa_topics
└─ Writes to staging_aqa_exam_papers

Step 2: VALIDATE
├─ Check counts
├─ Verify hierarchy
├─ Run validation report
└─ Manual review in data viewer

Step 3: PROMOTE (if valid)
├─ Run promotion SQL script
├─ staging → production tables
├─ Backup old data first
└─ Mark new data as live_in_app = false

Step 4: TEST IN APP
├─ Connect app to new data
├─ Test topic selection
├─ Test flashcard generation
└─ Verify no broken links

Step 5: GO LIVE
├─ Flip live_in_app = true
├─ Users see new exam board
├─ Monitor for issues
└─ Clear staging if successful

┌─────────────────────────────────────────────────────────┐
│  CONTINUOUS LOOP: Repeat for each exam board           │
│  UPDATES: Re-run for same board to refresh data        │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ RECOMMENDATIONS

### For Tony

1. **Keep Staging Tables Forever**
   - Don't delete them
   - They're your safe testing ground
   - Cost is minimal (few MB)

2. **Automate Promotion**
   - Build simple Python script
   - One command: `promote.py WJEC A-Level`
   - Includes validation + backup

3. **Scrape in Batches**
   - Do one exam board at a time
   - Validate before moving to next
   - Don't rush - quality over speed

4. **Version Everything**
   - Track spec versions (2024, 2025, etc.)
   - Keep old specs if students still studying them
   - Mark as "archived" not deleted

5. **Monitor Production**
   - Add analytics: which subjects/topics used most
   - Track errors: broken hierarchies, missing data
   - User feedback: wrong topics shown?

---

## 🎯 NEXT IMMEDIATE STEPS

1. **This Week: Complete Edexcel**
   - Finish remaining 11 subjects
   - Promote to production
   - Test in app

2. **Next Week: Refresh AQA**
   - Re-scrape all AQA subjects
   - Use improved scrapers
   - Replace old data in production

3. **Week 3: Start OCR**
   - Build/adapt scrapers
   - Scrape A-Level first
   - Validate and promote

4. **Week 4: WJEC + Cambridge**
   - Popular in Wales + International
   - Same workflow as above

---

**The staging workflow is your superpower.** You can:
- ✅ Test any exam board risk-free
- ✅ Update specs without breaking production
- ✅ Roll back if something goes wrong
- ✅ Continuously improve data quality

**Don't overthink it - the workflow is simple, just repeat it for each board.** 🚀



