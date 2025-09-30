# Running Complete AQA Scraper

## Quick Start

### Test with 3 Subjects First (RECOMMENDED)
```bash
cd "C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline"

# Test A-Level (first 3 subjects)
python pipeline_complete_aqa.py --qualification a_level --no-upload

# Review the data in data/processed/ folder
# If it looks good, run with upload
```

### Run Specific Subject
```bash
# Just History
python pipeline_complete_aqa.py --subject History --qualification a_level

# Just Mathematics  
python pipeline_complete_aqa.py --subject Mathematics --qualification a_level
```

### Run All A-Level Subjects (~37 subjects)
```bash
python pipeline_complete_aqa.py --qualification a_level

# This will:
# - Scrape all 37 A-Level subjects
# - Extract metadata, components, constraints (AI)
# - Scrape detailed content from web (HTML)
# - Upload to Supabase
# - Take ~2-3 hours
# - Cost ~$15 in AI calls
```

### Run All GCSE Subjects (~37 subjects)
```bash
python pipeline_complete_aqa.py --qualification gcse
```

### Run EVERYTHING (A-Level + GCSE = ~74 subjects!)
```bash
python pipeline_complete_aqa.py --qualification both

# This is the FULL RUN:
# - All AQA subjects
# - Both GCSE and A-Level
# - Complete hierarchical data
# - ~4-6 hours
# - ~$30 in AI calls
# - Complete AQA coverage!
```

### Resume from Specific Subject (if interrupted)
```bash
python pipeline_complete_aqa.py --qualification a_level --start-from Psychology
```

---

## What Gets Extracted

For EACH subject:

### From PDF (AI):
- Specification metadata
- Component structure
- Selection constraints  
- Subject vocabulary

### From Website (HTML parsing):
- Complete topic hierarchy
  - Level 0: Options/Modules
  - Level 1: Study areas
  - Level 2: Content points
- Key questions (for subjects that have them)

### Uploaded to Supabase:
- `specification_metadata` table
- `spec_components` table
- `selection_constraints` table
- `curriculum_topics` table (all levels)
- `subject_vocabulary` table

---

## Progress Tracking

Logs saved to: `data/logs/complete_aqa_YYYYMMDD_HHMMSS.log`

Progress saved to: `data/state/aqa_progress_YYYYMMDD_HHMMSS.json`

Processed data saved to: `data/processed/{subject}_{qualification}.json`

---

## Expected Results

### After A-Level Run:
- ~37 subjects processed
- ~1,500-2,000 curriculum_topics records added
- ~37 specification_metadata records
- ~110 components records (3 per subject avg)
- ~50-100 constraints records

### After GCSE Run:
- ~37 more subjects
- ~1,500-2,000 more topics
- ~37 more metadata records

### TOTAL:
- ~74 subjects
- ~3,000-4,000 new curriculum topics
- Complete AQA coverage for major qualifications!

---

## Monitoring

Watch the logs in real-time:
```bash
# In another terminal:
tail -f data/logs/complete_aqa_*.log
```

Or check progress file:
```bash
cat data/state/aqa_progress_*.json
```

---

## If Something Fails

The scraper will:
- ✅ Continue with next subject
- ✅ Save progress
- ✅ Log errors
- ✅ Allow resume from failure point

To resume:
```bash
python pipeline_complete_aqa.py --qualification a_level --start-from {failed_subject}
```

---

## Estimated Time & Cost

### A-Level Only:
- Time: 2-3 hours
- AI Cost: ~$15
- Subjects: 37

### GCSE Only:
- Time: 2-3 hours
- AI Cost: ~$15  
- Subjects: 37

### Both:
- Time: 4-6 hours
- AI Cost: ~$30
- Subjects: 74

**Can run overnight!**

---

## Next Steps After Complete

1. Verify data in Supabase
2. Test with your FLASH app
3. Add OCR subjects (similar process)
4. Add assessment resources scraping
5. International expansion

Ready to run? Start with `--test` flag!
