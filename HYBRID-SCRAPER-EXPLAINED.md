# Hybrid Scraper - Best of Both Worlds

## The Problem We Solved

You were right - we need BOTH approaches:
- ✅ **Web scraping** = Fast, free, but some pages aren't structured consistently
- ✅ **PDF extraction** = Reliable, always works, but costs AI credits (~$0.10-0.15 per subject)

## The Solution: Hybrid Scraper

The `aqa_hybrid_scraper.py` intelligently combines both methods:

```
For each subject:
├─ Step 1: Try WEB SCRAPING
│   └─ Navigate to subject-content pages
│   └─ Parse HTML for topics
│   └─ Extract hierarchical structure
│   └─ Cost: $0 (free!)
│   └─ Time: ~30 seconds
│   
├─ If web scraping succeeds:
│   └─ ✓ Upload to Supabase
│   └─ ✓ Mark as complete
│   └─ ✓ Move to next subject
│   
├─ If web scraping fails:
│   └─ Step 2: FALLBACK to PDF EXTRACTION
│       └─ Find PDF on specification page
│       └─ Download PDF
│       └─ Extract with AI (Claude)
│       └─ Cost: ~$0.10-0.15
│       └─ Time: ~2-3 minutes
│       └─ ✓ Upload to Supabase
│       └─ ✓ Mark as complete
```

## URL Patterns (Your Documentation)

### 1. Specification Page
```
https://www.aqa.org.uk/subjects/{subject}/{qual}/{subject}-{code}/specification
```
**Example:**
- Accounting A-Level: https://www.aqa.org.uk/subjects/accounting/a-level/accounting-7127/specification
- Economics A-Level: https://www.aqa.org.uk/subjects/economics/a-level/economics-7136/specification

**PDF is ALWAYS on this page!**

### 2. Subject Content Page
```
https://www.aqa.org.uk/subjects/{subject}/{qual}/{subject}-{code}/specification/subject-content
```
**Example:**
- Geography: https://www.aqa.org.uk/subjects/geography/a-level/geography-7037/specification/subject-content

**This page has numbered sections (3.1, 3.2) or option codes (1A, 1B)**

### 3. Individual Topic Pages
```
https://www.aqa.org.uk/subjects/{subject}/{qual}/{subject}-{code}/specification/subject-content/{topic-slug}
```
**Example:**
- Geography Physical: https://www.aqa.org.uk/subjects/geography/a-level/geography-7037/specification/subject-content/physical-geography

## How The Hybrid Scraper Works

### Web Scraping (Primary Method)

Your existing `aqa_web_scraper.py`:
1. Navigates to subject-content page
2. Detects pattern:
   - **Numbered sections**: "3.1 Financial Statements", "3.2 Cost Accounting"
   - **Option codes**: "1A Crusades", "1B Spain", "2A Stuart Britain"
3. Scrapes each content page
4. Extracts:
   - Topic code & title
   - Key questions
   - Study areas (h3 headings)
   - Sections (h4 headings)
   - Content points (bullet lists)
   - Periods (e.g., "1469-1598")

**Works great for:** Geography, Economics, Biology, Chemistry, Physics, etc.

**May fail for:** Subjects with inconsistent HTML structure

### PDF Extraction (Backup Method)

When web fails:
1. Navigate to specification page
2. Find PDF link (looks for `cdn.sanity.io` or `.pdf` links)
3. Download PDF
4. Use AI (Claude) to extract:
   - Specification metadata
   - Component structure (with selection rules!)
   - Selection constraints (geographic diversity, prohibited combos)
   - Topic options with codes
   - Subject vocabulary

**Always works** because PDF format is consistent

**Costs:** ~$0.10-0.15 per subject (Claude API)

## Cost Estimation

### Best Case (All subjects work with web scraping)
- **Cost:** $0
- **Time:** 74 subjects × 30 seconds = ~40 minutes

### Realistic Case (60 web, 14 PDF)
- **Web:** 60 subjects × $0 = $0
- **PDF:** 14 subjects × $0.12 = $1.68
- **Total:** ~$1.70
- **Time:** ~1.5 hours

### Worst Case (All subjects need PDF)
- **PDF:** 74 subjects × $0.12 = $8.88
- **Time:** 74 subjects × 2.5 minutes = ~3 hours

**Expected actual cost:** $2-5 for all 74 subjects

## What Gets Uploaded to Supabase

### From Web Scraping:
```sql
curriculum_topics:
- topic_code: "3.1" or "1A"
- topic_name: "Financial Statements"
- topic_level: 0 (main), 1 (study area)
- description: Full title
- key_themes: ["theme1", "theme2"]
- chronological_period: "1469-1598"
```

### From PDF Extraction:
```sql
specification_metadata:
- exam_board, subject, qualification
- total_guided_learning_hours
- assessment_overview

spec_components:
- component_code: "C1", "C2"
- selection_type: "choose_one", "required_all"
- count_required: 1
- total_available: 11

selection_constraints:
- constraint_type: "geographic_diversity"
- constraint_rule: {"must_include": ["British", "non-British"]}

curriculum_topics:
- topic_code: "1B"
- topic_name: "Spain in the Age of Discovery, 1469-1598"
- geographical_region: "European"
- chronological_period: "1469-1598"
- key_themes: JSON array
```

## Running The Hybrid Scraper

### Test Mode (3 subjects)
```bash
cd "C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline"
python batch_processor.py --test
```

### Full Run (all 74 subjects)
```bash
python batch_processor.py
```

### What You'll See In Logs:
```
[1/74] Processing: Accounting (A-Level)
Step 1: Attempting web scraping...
✓ Web scraping SUCCESS - Found 18 content items
SUCCESS: Accounting_A-Level (method: web)

[2/74] Processing: Drama (GCSE)  
Step 1: Attempting web scraping...
✗ Web scraping returned no content - will try PDF
Step 2: Falling back to PDF extraction...
✓ Found PDF: https://cdn.sanity.io/files/.../drama.pdf
✓ Downloaded PDF
📊 Extracting with AI (this costs ~$0.10-0.15)...
✓ PDF extraction SUCCESS
SUCCESS: Drama_GCSE (method: pdf)
```

## Final Report

After processing, you get an HTML report showing:
- ✅ **Completed**: Subject list + method used (web/pdf)
- ⚠️ **Partial**: Had issues but got some data
- ❌ **Failed**: Both methods failed (rare!)

## Why This is Better

### Old Approach (PDF only):
- ❌ Costs: $8-12 for all subjects
- ❌ Time: 2-4 hours
- ✅ Always works

### Old Approach (Web only):
- ✅ Cost: $0
- ✅ Fast: 40 minutes
- ❌ Fails on some subjects
- ❌ No component rules/constraints

### NEW Hybrid Approach:
- ✅ Cost: $2-5 for all subjects
- ✅ Time: 1-2 hours
- ✅ Always gets data (web or PDF)
- ✅ Gets component rules when available
- ✅ Smart fallback
- ✅ Logs which method worked

## For Your App

The hybrid scraper gives you:

1. **Accurate topic lists** (from web or PDF)
2. **Component structure** (when available from PDF)
3. **Selection rules** (geographic diversity, etc.)
4. **Hierarchical data** (Level 0, Level 1, Level 2)
5. **Chronological periods** (for History, etc.)
6. **Key themes** (for better flashcard generation)

**Everything your app needs to show users accurate, constraint-aware topic selection!**

## Ready to Run?

```bash
# Test with 3 subjects first
python batch_processor.py --test

# If that works, run all 74
python batch_processor.py
```

The hybrid scraper will automatically:
- ✅ Try web first
- ✅ Fall back to PDF if needed
- ✅ Upload to Supabase
- ✅ Log which method worked
- ✅ Generate report

**No more manual intervention needed!** 🚀
