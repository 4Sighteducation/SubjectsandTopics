# OCR Exam Paper Extractor - Implementation Plan

**Date**: December 2025  
**Exam Board**: OCR  
**Page**: https://www.ocr.org.uk/qualifications/past-paper-finder/  
**Status**: Planning Phase

---

## 🎯 OBJECTIVE

Build a scraper that extracts past papers (Question papers, Mark schemes, Examiner reports) from OCR's past paper finder page and uploads them to the database, grouped by year/series/paper.

---

## 📋 PAGE STRUCTURE ANALYSIS

### Filter System
1. **Type of Qualification** dropdown (e.g., "AS and A Level", "GCSE")
2. **Qualification** dropdown (e.g., "Ancient History - H007, H407 (from 2017)")
3. **Level** dropdown (e.g., "A Level", "AS Level")

### Results Display
- Once filters are selected, **series accordions** appear (closed by default)
- Each accordion represents a year/series (e.g., "2024 - June series")
- When expanded, shows list of documents:
  - Question papers
  - Mark schemes
  - Examiners' reports
- Each document has:
  - Title (e.g., "Question paper - Sparta and the Greek world")
  - File code (e.g., "H407/11")
  - PDF icon
  - Size (e.g., "PDF 1MB")
  - Direct PDF URL (e.g., `https://www.ocr.org.uk/Images/676714-question-paper-sparta-and-the-greek-world.pdf`)

---

## 🔍 SCRAPING APPROACH OPTIONS

### Option 1: Selenium (Recommended - Like Edexcel)
**Pros:**
- Can interact with dropdowns and expand accordions
- Handles JavaScript-rendered content
- Proven pattern (Edexcel scraper works this way)
- Can wait for dynamic content to load

**Cons:**
- Slower than Firecrawl
- Requires browser automation

**Implementation:**
- Use Selenium to:
  1. Navigate to past paper finder page
  2. Select filters (Type → Qualification → Level)
  3. Wait for accordions to appear
  4. Expand all accordions (click each one)
  5. Scrape all PDF links from expanded content
  6. Parse metadata from titles/URLs

### Option 2: Firecrawl (Alternative)
**Pros:**
- Faster than Selenium
- User has Firecrawl API
- Can scrape rendered HTML

**Cons:**
- May not handle dynamic accordions well
- Need to figure out how to trigger filter selection
- May need to construct URLs manually

**Implementation:**
- Try to scrape page with filters applied via URL parameters
- Or scrape page, then use Firecrawl to expand accordions
- Parse HTML for PDF links

### Option 3: Direct URL Construction (If Possible)
**Pros:**
- Fastest approach
- No browser automation needed

**Cons:**
- Need to reverse-engineer URL structure
- May not be possible if OCR uses complex JavaScript

**Implementation:**
- Analyze network requests when filters are selected
- Construct direct URLs to filtered results
- Scrape those URLs

---

## ✅ RECOMMENDED APPROACH: Selenium (Hybrid)

**Why:** OCR's page structure is similar to Edexcel's (accordions, dynamic content), and the Edexcel scraper pattern works well.

**Steps:**
1. **Initialize Selenium** (headless Chrome)
2. **Navigate** to past paper finder page
3. **Select filters** programmatically:
   - Find dropdowns by label/text
   - Select options matching subject
   - Wait for results to load
4. **Expand all accordions**:
   - Find all collapsed accordion elements
   - Click each one to expand
   - Wait for content to load
5. **Scrape PDF links**:
   - Find all `<a>` tags with `.pdf` hrefs
   - Extract title, URL, file code
6. **Parse metadata**:
   - Extract year from accordion title ("2024 - June series")
   - Extract paper number from file code ("H407/11" → paper 11)
   - Determine type from title ("Question paper" vs "Mark scheme" vs "Examiners' report")
7. **Group into sets**:
   - Group by: year + series + paper number
   - Combine question paper + mark scheme + examiner report URLs
8. **Upload to database**:
   - Use `upload_papers_to_staging.py` with `exam_board='OCR'`

---

## 📊 DATA STRUCTURE

### Input (Subject Configuration)
```javascript
{
  subject_code: "H407",           // e.g., "H407" for Ancient History
  subject_name: "Ancient History", // Full subject name
  qualification_type: "A-Level",   // "A-Level" or "GCSE"
  qualification_filter: "Ancient History - H007, H407 (from 2017)", // Exact text from dropdown
  level_filter: "A Level"          // "A Level" or "AS Level"
}
```

### Output (Paper Sets)
```javascript
[
  {
    year: 2024,
    exam_series: "June",
    paper_number: 11,              // Extracted from "H407/11"
    component_code: "11",          // Optional, for subjects with components
    tier: null,                    // Usually null for A-Level
    question_paper_url: "https://www.ocr.org.uk/Images/676714-question-paper-sparta-and-the-greek-world.pdf",
    mark_scheme_url: "https://www.ocr.org.uk/Images/666802-mark-scheme-sparta-and-the-greek-world.pdf",
    examiner_report_url: "https://www.ocr.org.uk/Images/...examiners-report-sparta.pdf"
  }
]
```

---

## 🔧 IMPLEMENTATION DETAILS

### File Structure
```
scrapers/OCR/
├─ A-Level/
│  └─ papers/
│     ├─ scrape-ocr-papers-universal.py    (Main scraper)
│     ├─ TEST-OCR-PAPERS.bat               (Test script)
│     └─ OCR-PAPER-SCRAPER-PLAN.md         (This file)
└─ GCSE/
   └─ papers/
      └─ (Same structure for GCSE)
```

### Key Functions

#### 1. `select_filters(driver, qualification, level)`
- Find and select "Type of Qualification" dropdown
- Find and select "Qualification" dropdown (match by text)
- Find and select "Level" dropdown
- Wait for accordions to appear

#### 2. `expand_all_accordions(driver)`
- Find all collapsed accordion elements
- Click each one
- Wait for content to load
- Return list of expanded sections

#### 3. `scrape_pdf_links(driver)`
- Parse HTML for all PDF links
- Extract metadata:
  - Title (from link text)
  - URL (from href)
  - File code (from title or nearby text)
  - Year/Series (from parent accordion)

#### 4. `parse_paper_metadata(link_element, accordion_title)`
- Extract year from accordion: "2024 - June series" → year=2024, series="June"
- Extract paper number from file code: "H407/11" → paper_number=11
- Determine type from title:
  - "Question paper" → question_paper_url
  - "Mark scheme" → mark_scheme_url
  - "Examiners' report" → examiner_report_url

#### 5. `group_papers(papers)`
- Group by: year + exam_series + paper_number
- Combine URLs into single paper set object

#### 6. `upload_papers(subject_code, qualification_type, paper_sets)`
- Call `upload_papers_to_staging()` with `exam_board='OCR'`

---

## 🧪 TESTING STRATEGY

### Test Subject: Ancient History (H407)
- **Qualification**: "Ancient History - H007, H407 (from 2017)"
- **Level**: "A Level"
- **Expected**: Multiple papers from different years

### Test Steps
1. Run scraper for H407
2. Verify:
   - Filters are selected correctly
   - Accordions expand
   - PDF links are found
   - Metadata is parsed correctly
   - Papers are grouped correctly
   - Database upload succeeds

### Debug Output
- Save HTML after filters selected
- Save HTML after accordions expanded
- Save list of found PDF links
- Save parsed paper metadata
- Save grouped paper sets

---

## 📝 EXAMPLE URL PATTERNS

From user's examples:
- Question paper: `https://www.ocr.org.uk/Images/676714-question-paper-sparta-and-the-greek-world.pdf`
- Mark scheme: `https://www.ocr.org.uk/Images/666802-mark-scheme-sparta-and-the-greek-world.pdf`
- Question paper: `https://www.ocr.org.uk/Images/666796-question-paper-athens-and-the-greek-world.pdf`

**Pattern Analysis:**
- Base URL: `https://www.ocr.org.uk/Images/`
- Filename format: `[NUMBER]-[TYPE]-[TOPIC].pdf`
- Types: `question-paper`, `mark-scheme`, `examiners-report` (likely)

**Note:** We don't need to construct URLs manually - we'll scrape them directly from the page.

---

## 🚀 NEXT STEPS

1. **Create base scraper** (`scrape-ocr-papers-universal.py`)
   - Selenium setup
   - Filter selection logic
   - Accordion expansion
   - PDF link scraping
   - Metadata parsing
   - Grouping logic
   - Database upload

2. **Test with Ancient History (H407)**
   - Verify all steps work
   - Check database output
   - Fix any issues

3. **Create test script** (`TEST-OCR-PAPERS.bat`)
   - Easy way to test single subject

4. **Scale to all subjects**
   - Create subject configuration file
   - Batch processing script
   - Error handling and retry logic

---

## 🔗 REFERENCES

- **Edexcel scraper**: `scrapers/Edexcel/A-Level/papers/scrape-edexcel-papers-universal.py`
- **AQA scraper**: `scrape-aqa-papers-improved.js`
- **Upload helper**: `upload_papers_to_staging.py`
- **Database schema**: `staging_aqa_exam_papers` table (supports `exam_board='OCR'`)

---

## ⚠️ POTENTIAL CHALLENGES

1. **Dynamic Filter Selection**
   - Dropdowns may be custom components
   - May need to use JavaScript execution to select options
   - Solution: Use Selenium's `Select` class or JavaScript execution

2. **Accordion Expansion**
   - May need to wait for each accordion to load
   - May need to scroll to accordion before clicking
   - Solution: Wait for elements, scroll into view, then click

3. **PDF Link Extraction**
   - Links may be in nested structures
   - May need to parse file codes from nearby text
   - Solution: Use BeautifulSoup to parse HTML structure

4. **Metadata Parsing**
   - File codes may vary in format
   - Paper numbers may need extraction from component codes
   - Solution: Use regex patterns, handle edge cases

5. **Component Codes**
   - Some subjects have components (e.g., H407/11, H407/12)
   - Need to extract component code correctly
   - Solution: Parse from file code (e.g., "11" from "H407/11")

---

## ✅ SUCCESS CRITERIA

- [ ] Successfully selects filters for a subject
- [ ] Expands all accordions and finds PDF links
- [ ] Parses metadata correctly (year, series, paper number, type)
- [ ] Groups papers into complete sets
- [ ] Uploads to database with `exam_board='OCR'`
- [ ] Works for multiple subjects (A-Level and GCSE)
- [ ] Handles edge cases (missing mark schemes, different series names)

---

**End of Plan**





















