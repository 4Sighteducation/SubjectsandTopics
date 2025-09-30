# Action Plan for TODAY - AQA Scraping Only

## Goal
Get accurate, up-to-date AQA topic data into Supabase for your FLASH app.

---

## Step 1: Test the Scraper (10 minutes)

Run with TEST MODE (only 3 subjects):

```bash
cd "C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline"
python batch_processor.py --test
```

**What this does:**
- Processes 3 subjects (History, Mathematics, Biology A-Level)
- Downloads their specification PDFs
- Extracts topics with AI
- Uploads to Supabase
- Opens HTML report

**Expected output:**
```
Processing 3 subjects
[1/3] Processing History (A-Level)...
  ✓ Found specification URL
  ✓ Downloaded PDF
  ✓ Extracted: 30 topics, 3 components, 4 constraints
  ✓ Upload complete
✅ SUCCESS: History_A-Level

[2/3] Processing Mathematics (A-Level)...
...

Report: data/reports/batch_report_TIMESTAMP.html
```

---

## Step 2: Verify the Data (5 minutes)

After test completes, check the HTML report that opens. Look for:

✅ **Success section:** Should show 3 subjects
❌ **Failed section:** Should be empty (hopefully!)

Then **spot-check in Supabase**:

```sql
-- Check topics were added/updated
SELECT 
  topic_code,
  topic_name,
  component_code,
  geographical_region,
  chronological_period
FROM curriculum_topics
WHERE exam_board_subject_id = (
  SELECT id FROM exam_board_subjects 
  WHERE subject_name = 'History' 
  AND exam_board_id = (SELECT id FROM exam_boards WHERE code = 'AQA')
)
ORDER BY topic_code;

-- Should see: 1A, 1B, 1C... with regions, periods, etc.
```

```sql
-- Check components/rules were added
SELECT 
  component_code,
  component_name,
  selection_type,
  count_required,
  total_available
FROM spec_components
WHERE spec_metadata_id IN (
  SELECT id FROM specification_metadata 
  WHERE exam_board = 'AQA' AND subject_name = 'History'
);

-- Should see: Component 1 (choose_one, 1 from 11), Component 2 (choose_one, 1 from 20)
```

---

## Step 3: Decision Point

### Option A: Data Looks Good → Run Full Batch

If test results look accurate:

```bash
python batch_processor.py
```

This will process ALL 74 AQA subjects (2-4 hours).

**You can:**
- ✅ Let it run in background
- ✅ Stop anytime (Ctrl+C) and resume later
- ✅ Check progress in the log file

### Option B: Data Has Issues → Debug First

If topics look wrong or missing:

1. Check the log file: `data/logs/batch_TIMESTAMP.log`
2. Look for error messages
3. Try manual download of the PDF to check if URL is valid
4. Re-run single subject to debug:

```bash
python -m scrapers.uk.aqa_scraper_enhanced --subject "History" --exam-type "A-Level"
```

---

## Step 4: After Full Batch Completes

### Verify Coverage

```sql
-- How many subjects have topics?
SELECT 
  ebs.subject_name,
  ebs.subject_code,
  COUNT(ct.id) as topic_count
FROM exam_board_subjects ebs
LEFT JOIN curriculum_topics ct ON ct.exam_board_subject_id = ebs.id
WHERE ebs.exam_board_id = (SELECT id FROM exam_boards WHERE code = 'AQA')
GROUP BY ebs.subject_name, ebs.subject_code
ORDER BY topic_count DESC;

-- Should see 74 subjects with varying topic counts
```

```sql
-- How many subjects have specification metadata?
SELECT COUNT(*) 
FROM specification_metadata 
WHERE exam_board = 'AQA';

-- Should be close to 74 (some may fail)
```

### Check Failed Subjects

Look at HTML report → Failed section

For each failed subject:
1. Check log file for specific error
2. Try manual PDF download from AQA website
3. Re-run individually if needed

---

## Step 5: Enhance App UI (OPTIONAL - Later)

Your current app shows all topics as a flat list.

**Current flow:** Exam Board → Subject → Topics (checkboxes)

**Enhanced flow (with constraints):** Exam Board → Subject → Components → Options (validated)

### Example UI Enhancement:

```typescript
// Check if subject has selection rules
const hasRules = await checkForSelectionRules(subjectId);

if (hasRules) {
  // Show component-based selection
  navigation.navigate('PathwaySelection', { subjectId });
} else {
  // Show simple topic list (current behavior)
  navigation.navigate('TopicSelection', { subjectId });
}
```

**When to do this:**
- AFTER scraping is complete and verified
- AFTER you've tested with current app
- Estimated time: 1-2 weeks development

---

## What About Assessment Resources?

**Short answer:** Build this LATER (separate project).

**Current scraper = CURRICULUM DATA** (what to study)
- Topic options
- Component structure  
- Selection rules

**Assessment scraper = EXAM DATA** (how it's tested)
- Past papers
- Mark schemes
- Examiner reports

**Recommendation:**
1. Get curriculum scraping working first (TODAY)
2. Verify topics are accurate
3. Maybe enhance app UI for constraints
4. THEN build assessment scraper (if needed)

**Estimated additional time for assessment scraper:** 1-2 weeks

---

## Commands Cheat Sheet

```bash
# Test mode (3 subjects only)
python batch_processor.py --test

# Full run (all 74 subjects)
python batch_processor.py

# Single subject (for debugging)
python -m scrapers.uk.aqa_scraper_enhanced --subject "History" --exam-type "A-Level"

# Check what's in database (run this BEFORE scraping to compare)
python check_existing_data.py
```

---

## Expected Timeline

| Task | Time | When |
|------|------|------|
| Test scraper (3 subjects) | 10 mins | NOW |
| Verify results | 5 mins | NOW |
| Full batch (74 subjects) | 2-4 hours | TODAY (can run in background) |
| Spot-check data quality | 30 mins | AFTER batch |
| Fix any failed subjects | 30 mins | AFTER batch |
| **TOTAL for accurate AQA data** | **3-5 hours** | **TODAY** |

---

## Success Criteria

After today, you should have:

✅ All 74 AQA subjects in `specification_metadata`  
✅ Components defined for subjects with options (History, English, etc.)  
✅ Constraints defined where needed (geographic diversity, etc.)  
✅ Topics enriched with metadata (codes, periods, regions)  
✅ HTML report showing success/failure breakdown  
✅ **100% accurate, up-to-date AQA curriculum data**  

---

## If You Hit Issues

1. **"PDF download failed"**
   - Check if AQA website is accessible
   - Try manual download to verify URL
   - Update URL in `aqa_scraper_enhanced.py` if needed

2. **"AI extraction failed"**
   - Check ANTHROPIC_API_KEY is set
   - Check API rate limits
   - Try again (transient error)

3. **"Supabase upload failed"**
   - Check SUPABASE credentials
   - Check table permissions
   - Run migrations if tables missing

4. **"Batch processor crashes mid-run"**
   - No problem! State is saved
   - Just run again - it resumes automatically

---

## Ready to Start?

```bash
# Step 1: Test (10 mins)
python batch_processor.py --test

# Step 2: Check report that opens in browser

# Step 3: If good, run full batch
python batch_processor.py

# Step 4: Check final report after 2-4 hours
```

**Let's get accurate AQA data first, then we can talk about:**
- International scrapers (Cambridge, IB)
- Assessment resources (past papers)
- App UI enhancements (pathway selection)

One step at a time! 🚀
