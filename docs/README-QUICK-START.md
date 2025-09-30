# FLASH Curriculum Pipeline - Quick Start Guide

## 🚀 What This System Does

Automatically scrapes curriculum data from exam boards (AQA, Cambridge, IB, etc.) and uploads to Supabase for the FLASH app.

**What it scrapes:**
- ✅ Subject specifications and metadata
- ✅ Component structure (what students must study)
- ✅ Selection constraints (rules for choosing topics)
- ✅ Topic hierarchies (options → study areas → content points)
- ✅ Subject vocabulary
- 🔄 Past papers, mark schemes, examiner reports (coming soon)

## 📋 Prerequisites

1. **Python 3.8+** installed
2. **Environment variables** set in `.env`:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_KEY=your_service_key
   ANTHROPIC_API_KEY=your_claude_api_key
   ```
3. **Dependencies** installed:
   ```bash
   pip install -r requirements.txt
   ```

## 🎯 Quick Start (3 Steps)

### Step 1: Check What Data You Already Have

**Windows:**
```bash
RUN-CHECK-DATA.bat
```

**Command line:**
```bash
python check_existing_data.py
```

**Output:** Opens HTML report showing:
- How many subjects/topics already in database
- Which exam boards have data
- What's missing
- Recommendations for next steps

### Step 2: Test the Batch Processor (3 subjects only)

**Windows:**
```bash
RUN-BATCH-AQA.bat
# Choose option 1 (TEST MODE)
```

**Command line:**
```bash
python batch_processor.py --test
```

**Output:** Processes 3 subjects to verify everything works.

### Step 3: Run Full Batch (all 74 AQA subjects)

**Windows:**
```bash
RUN-BATCH-AQA.bat
# Choose option 2 (FULL RUN)
```

**Command line:**
```bash
python batch_processor.py
```

**Duration:** 2-4 hours  
**Output:** HTML report with success/failure for each subject

## 📁 File Structure

```
flash-curriculum-pipeline/
├── batch_processor.py           # Batch process all AQA subjects
├── check_existing_data.py       # Audit current database
├── RUN-BATCH-AQA.bat           # Easy batch runner
├── RUN-CHECK-DATA.bat          # Easy audit runner
│
├── scrapers/
│   ├── uk/
│   │   ├── aqa_scraper_enhanced.py      # AQA scraper
│   │   ├── ocr_scraper.py               # OCR scraper
│   │   └── ...
│   └── international/
│       ├── cambridge_scraper.py          # Cambridge IGCSE/A-Level
│       └── ib_scraper.py (coming)        # IB scraper
│
├── database/
│   ├── supabase_client.py               # Upload to Supabase
│   └── migrations/                      # Database schema
│       ├── 001_specification_metadata_tables.sql
│       ├── 002_assessment_resources_tables.sql
│       └── 003_add_scraping_markers.sql
│
├── extractors/
│   └── specification_extractor.py       # AI extraction logic
│
├── config/
│   └── aqa_subjects.yaml                # 74 AQA subjects
│
└── data/
    ├── raw/                             # Downloaded PDFs
    ├── processed/                       # Extracted JSON
    ├── logs/                            # Execution logs
    ├── state/                           # Resume state files
    └── reports/                         # HTML reports
```

## 🛠️ Common Commands

### Check Data Status
```bash
python check_existing_data.py
```

### Process Single Subject
```bash
# AQA
python -m scrapers.uk.aqa_scraper_enhanced --subject "History" --exam-type "A-Level"

# Cambridge
python -m scrapers.international.cambridge_scraper --subject "Mathematics" --qual "IGCSE"
```

### List Available Subjects
```bash
python -m scrapers.international.cambridge_scraper --list
```

### Process Without Uploading (Testing)
```bash
python batch_processor.py --test --no-upload
```

## 📊 Understanding the Output

### Batch Processor Report

Shows for each subject:
- ✅ **Completed:** Successfully scraped and uploaded
- ⚠️ **Partial:** Some data extracted but had issues
- ❌ **Failed:** Could not process

### Data Audit Report

Shows:
- **Core Tables:** exam_boards, subjects, topics counts
- **Specification Tables:** metadata, components, constraints
- **Assessment Tables:** past papers, mark schemes, reports
- **Recommendations:** What to do next

## 🐛 Troubleshooting

### "Missing environment variables"
- Check `.env` file exists
- Verify SUPABASE_URL, SUPABASE_SERVICE_KEY, ANTHROPIC_API_KEY are set

### "PDF download failed"
- AQA may have changed their website structure
- Check manual download from AQA website
- Update URL in `aqa_scraper_enhanced.py`

### "AI extraction failed"
- Check ANTHROPIC_API_KEY is valid
- Check API rate limits not exceeded
- Check PDF is not corrupted

### Batch processor stopped mid-run
- No problem! State is saved automatically
- Just run again - it will resume from where it stopped

## 📈 What's Next?

After running batch processor:

1. **Check the report** - review success/failures
2. **Verify in Supabase** - check data uploaded correctly
3. **International scrapers** - add Cambridge, IB
4. **Assessment resources** - add past papers scraper
5. **App integration** - implement pathway UI

## 🔗 Key Documents

- **COMPLETE-IMPLEMENTATION-PLAN.md** - Full strategy (4-5 week plan)
- **docs/COMPLETE-DATA-STRATEGY.md** - Why we need assessment resources
- **docs/TERMINOLOGY-AND-STRUCTURE-PLAN.md** - Database structure explained

## ⚡ Quick Reference

| Task | Command | Time |
|------|---------|------|
| Check data | `python check_existing_data.py` | 1 min |
| Test (3 subjects) | `python batch_processor.py --test` | 10 min |
| Full AQA (74 subjects) | `python batch_processor.py` | 2-4 hours |
| Single subject | `python -m scrapers.uk.aqa_scraper_enhanced --subject "X" --exam-type "Y"` | 3-5 min |
| Cambridge subject | `python -m scrapers.international.cambridge_scraper --subject "X" --qual "Y"` | 3-5 min |

## 💰 API Costs

- **Per subject:** ~$0.10-0.15 (AI extraction)
- **74 AQA subjects:** ~$7-12
- **30 Cambridge subjects:** ~$3-5
- **Assessment resources (later):** ~$200-300

## 🎓 Getting Help

1. Check log files in `data/logs/`
2. Check state files in `data/state/`
3. Review audit report
4. Re-run in test mode to isolate issues

---

**Ready to start?**

```bash
# Step 1: See what you have
python check_existing_data.py

# Step 2: Test with 3 subjects
python batch_processor.py --test

# Step 3: Run full batch
python batch_processor.py
```

Good luck! 🚀
