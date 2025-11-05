# Edexcel A-Level Scraping - Session Handover
**Date:** November 5, 2025  
**Status:** 10/37 subjects complete (27%)  
**Achievement:** 2,813 topics + 248 verified paper sets

---

## 🎯 PROJECT OVERVIEW

**Goal:** Scrape topics and exam papers for all 37 Edexcel A-Level subjects

**Database:** Supabase tables
- `staging_aqa_subjects` (subject metadata)
- `staging_aqa_topics` (topic hierarchy with parent_topic_id)
- `staging_aqa_exam_papers` (past papers with URLs)

**Key Requirement:** Deep hierarchies (4-5 levels) for AI flashcard generation
- Levels 0-2: Shown to users by default
- Levels 3-4: Used by AI to generate granular flashcard questions

---

## ✅ COMPLETE SUBJECTS (10)

| Subject | Code | Topics | Hierarchy | Papers | Method |
|---------|------|--------|-----------|--------|--------|
| Arabic | 9AA0 | 55 | 4 levels | 21 | Manual (Arabic script) |
| Art and Design | 9AD0 | 96 | 3 levels | 8 | Manual (5 titles) |
| Business | 9BS0 | 613 | **5 levels** | 30 | Table scraper ⭐ |
| Chemistry | 9CH0 | 265 | 4 levels | 30 | Universal scraper |
| Chinese | 9CN0 | 36 | 4 levels | 21 | Manual (Chinese script) |
| Design & Tech | 9DT0 | 139 | 4 levels | 12 | Table scraper |
| Drama | 9DR0 | 36 | 3 levels | 0 | Manual (texts/practitioners) |
| Economics A | 9EC0 | 663 | **5 levels** | 48 | Table scraper ⭐ |
| Economics B | 9EB0 | 660 | **5 levels** | 48 | Table scraper ⭐ |
| Physics | 9PH0 | 250 | 3 levels | 30 | Universal scraper |

**TOTAL: 2,813 topics + 248 paper sets**

---

## 🔧 WORKING SCRAPERS

### **Topic Scrapers:**

1. **`scrape-business-improved.py`** ⭐ BEST - For table-structured subjects
   - Used for: Business, Design & Tech, Economics A, Economics B
   - Handles 2-3 column tables with "Subject content" and "What students need to learn"
   - Produces 5-level hierarchies (Themes → Sections → Content → Learning → Sub-points)
   - **Success rate: 100%**

2. **`scrape-edexcel-universal.py`** - For science subjects
   - Used for: Chemistry, Physics
   - Detects "Topic X:" patterns and sub-topics
   - Produces 3-4 level hierarchies

3. **Manual uploads** - For specialized subjects:
   - `upload-arabic-manual.py` - Template for Arabic script languages
   - `upload-chinese-manual.py` - Template for Chinese languages
   - `upload-art-design-manual.py` - Template for arts subjects
   - `upload-drama-manual.py` - Template for prescribed texts

### **Paper Scrapers:**

**ALWAYS use Selenium** - URL guessing doesn't work (gives false positives on redirect pages)

**Template:** `scrape-business-papers-selenium.py`
- Navigate → EXPAND ALL → Scroll → Scrape actual links
- **Success rate: ~95%** (some subjects have no papers published by Edexcel)

**Enhanced version:** `scrape-design-tech-papers-selenium-v2.py`
- Longer waits (15s initial, 10s after filter)
- Explicit filter clicking
- Multiple scroll rounds
- Use for problematic subjects

---

## 📋 SCRAPING PATTERNS DISCOVERED

### **Pattern 1: Table-Structured Subjects (Most Common)**

**Indicators:**
- "Knowledge, skills and understanding" section in Contents
- 2-3 column tables with headers "Subject content" and "What students need to learn"
- Numbered hierarchy: 1.1 → 1.1.1 → a) → o

**Subjects using this:** Business, Economics A/B, Design & Tech, Geography, Psychology (likely)

**Scraper:** `scrape-business-improved.py` (rename and update SUBJECT config)

**Structure:**
```
Level 0: Themes (from Contents index)
Level 1: Sections (1.1, 1.2, 1.3)
Level 2: Content codes (1.1.1, 1.1.2)
Level 3: Learning points (a), b), c))
Level 4: Sub-points (o markers)
```

**Example (Business):**
```
Theme 1: Marketing and people (L0)
  └─ 1.1 Meeting customer needs (L1)
      └─ 1.1.1 The market (L2)
          └─ a) Mass markets and niche markets (L3)
              └─ characteristics (L4)
              └─ market size and share (L4)
```

### **Pattern 2: Science Subjects**

**Indicators:**
- "Topic X:" headers
- Sub-topics with letters (Topic 2A, Topic 15B)
- Learning outcomes numbered 1., 2., 3.

**Subjects:** Chemistry, Physics, Biology B

**Scraper:** `scrape-edexcel-universal.py`

### **Pattern 3: Language Subjects**

**Indicators:**
- Components as Level 0
- Themes (Arabic style) or prescribed texts
- Cultural/linguistic content

**Subjects:** Arabic, Chinese, French, German, Spanish, etc.

**Method:** Manual upload (faster than building parsers)

### **Pattern 4: Arts/Performance Subjects**

**Indicators:**
- Endorsed titles or components
- Project-based assessment
- Prescribed texts/practitioners

**Subjects:** Art & Design, Drama, Music

**Method:** Manual upload with prescribed content lists

---

## 🚨 CRITICAL LESSONS LEARNED

### **1. URL Guessing DOESN'T WORK**
❌ **Don't do this:**
```python
for year in [2024, 2023...]:
    url = f"base_url/9bs0-01-que-{year}0522.pdf"
    if test_url(url):  # Returns 200 on redirect pages!
```

✅ **Always use Selenium:**
- Scrapes actual links from coursematerials page
- Verified URLs that work
- No false positives

**Example:** 
- URL guessing claimed: 72 Business papers ❌
- Selenium found: 30 actual papers ✅

### **2. PDF Structures Vary by Subject Type**
- **Don't** use Biology template for all subjects
- **Don't** assume "Topic X:" pattern exists everywhere
- **Do** check debug file first
- **Do** use subject-type specific scrapers

### **3. Windows Encoding Issues**
- ❌ Never use emojis in batch scripts
- ✅ Set `PYTHONIOENCODING=utf-8` in environment
- ✅ Force UTF-8 in scripts: `io.TextIOWrapper(...)`

### **4. Manual Upload is Often Faster**
For niche subjects (<50 topics), manual upload beats building complex parsers:
- Arabic: 10 mins manual vs hours scraping
- Chinese: 10 mins manual
- Art & Design: 15 mins manual

### **5. Multilingual Unicode Works Perfectly**
Database handles:
- Arabic: المحور الأول, الأسرة العربية
- Chinese: 當代華人社會變遷, 家庭
- No special configuration needed!

---

## 📁 KEY FILES CREATED

### **Working Topic Scrapers:**
```
scrapers/Edexcel/A-Level/topics/
├── scrape-business-improved.py ⭐ (Business, Econ A, Econ B, Design Tech)
├── scrape-economics-a-improved.py
├── scrape-economics-b-improved.py
├── scrape-design-tech-improved.py
├── scrape-edexcel-universal.py (Chemistry, Physics)
├── upload-arabic-manual.py (55 topics with Arabic)
├── upload-chinese-manual.py (36 topics with Chinese)
├── upload-art-design-manual.py (96 topics, 5 titles)
└── upload-drama-manual.py (36 topics, prescribed texts)
```

### **Working Paper Scrapers:**
```
scrapers/Edexcel/A-Level/papers/
├── scrape-business-papers-selenium.py ⭐ (Template for most subjects)
├── scrape-chinese-papers-selenium.py
├── scrape-arabic-papers-selenium.py
├── scrape-art-papers-selenium.py
├── scrape-economics-a-papers-selenium.py
├── scrape-economics-b-papers-selenium.py
├── scrape-design-tech-papers-selenium-v2.py (Enhanced with longer waits)
└── scrape-history-papers-selenium.py (259 sets from previous session)
```

### **Configuration:**
```
scrapers/Edexcel/A-Level/
├── edexcel-alevel-subjects.json (36 subjects with URLs)
├── run-all-subjects.py (Batch runner - needs updating)
├── VERIFIED-SUBJECTS.md (Progress tracker)
└── SESSION-SUMMARY-NOV5.txt
```

### **Tools:**
```
data-viewer-v2.html
├── View all subjects/topics
├── Edit topics inline
├── Drag & drop to reorganize
└── 📋 MANUAL PAPER ENTRY ⭐ (paste URLs when Selenium fails)
```

---

## 🎓 HOW TO SCRAPE NEW SUBJECTS

### **Step 1: Identify Subject Type**

Download PDF and check structure:
```python
python -c "
import requests
from pypdf import PdfReader
from io import BytesIO

url = 'SUBJECT_PDF_URL'
pdf = PdfReader(BytesIO(requests.get(url).content))
text = ''.join(page.extract_text() for page in pdf.pages[:50])
open('debug-check.txt', 'w', encoding='utf-8').write(text)
"
```

Look for:
- **"Knowledge, skills and understanding"** in Contents → Use Business scraper
- **"Topic X:"** headers → Use Universal scraper
- **Prescribed texts/Themes** → Manual upload
- **"Qualification at a glance"** → Check if table-based

### **Step 2: Copy Appropriate Template**

**For table subjects (Business, Economics, Geography, Psychology):**
```bash
cp scrape-business-improved.py scrape-NEWSUBJECT-improved.py
```

Update these lines:
```python
SUBJECT = {
    'code': '9XX0',
    'name': 'Subject Name',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'PDF_URL_HERE'
}

# Update themes in parse function:
themes = [
    {'code': 'Theme1', 'title': 'Theme 1: Title from PDF', ...},
    # ... etc
]
```

**For science subjects:**
```bash
# Just run universal scraper with parameters
python scrape-edexcel-universal.py 9XX0 "Subject Name" "PDF_URL"
```

**For languages/specialized:**
- Copy `upload-arabic-manual.py` template
- Structure topics from PDF pages 8-12 (usually where themes are)
- Run it

### **Step 3: Run Topic Scraper**
```bash
python scrape-SUBJECT-improved.py
```

Check output:
- ✅ 100+ topics → Good!
- ⚠️ Only 3-4 topics → Only got Papers/Themes, check debug file
- ❌ Error → Check PDF structure, adjust parser

### **Step 4: Run Paper Scraper**

**Copy template:**
```bash
cp scrape-business-papers-selenium.py scrape-SUBJECT-papers-selenium.py
```

**Update URL and codes:**
```python
SUBJECT = {
    'code': '9XX0',
    'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/SUBJECT-YEAR.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
}

# Change all instances of subject code:
if '9xx0' not in href.lower(): continue
match = re.search(r'9xx0[-_](\d+)...', filename, re.IGNORECASE)
```

**Run it:**
```bash
python scrape-SUBJECT-papers-selenium.py
```

**If 0 papers found:**
- Use enhanced version with longer waits (`-v2.py`)
- Or use **Manual Paper Entry** in data viewer

---

## 📊 TABLE STRUCTURE PATTERNS

### **2-Column Tables (Business, Economics, Design & Tech)**

```
Subject content          | What students need to learn:
-------------------------|-----------------------------
1.1.1                   | a) Mass markets and niche markets:
The market              |    o characteristics
                        |    o market size and share
                        | b) Dynamic markets:
                        |    o online retailing
```

**Parser handles:**
- Column 1: Content codes (1.1.1) and titles
- Column 2: Learning points (a, b, c) with sub-points (o)
- Multi-line content (combines continuation lines)

### **3-Column Tables (Some subjects)**

```
Topic | Content | What students learn
------|---------|-------------------
1     | 1.1     | a) Point 1
      | Woods   | b) Point 2
```

**Parser detects** both formats automatically.

### **Single-Column Lists (Sciences)**

```
Topic 1: Atomic Structure
  1. Know that atoms contain protons...
  2. Understand electron configuration...
  
Topic 2A: Bonding
  ...
```

---

## 🗂️ WHERE TO FIND CONTENT IN PDFs

### **Contents/Index Section (Pages 2-5)**

Look for:
1. **"Knowledge, skills and understanding"** - Lists components/themes
   - This tells you Level 0 topics
   - Table-structured subjects will say "Theme 1: Title"

2. **"Qualification at a glance"** - Overview of components
   - Shows exam structure
   - Identifies non-examined assessment (skip these!)

3. **"Prescribed texts"** - For Literature/Drama
   - Usually lists all texts students must study
   - Organize by component

### **Subject Content Section (Pages 10-40)**

**For table subjects:**
- Section starts with "Knowledge, skills and understanding"
- Then numbered sections (1.1, 1.2, etc.)
- Then tables with 2-3 columns

**For science subjects:**
- Sections start with "Topic X: Title"
- Then numbered learning outcomes
- Then sub-topics (Topic XA, XB)

### **What to IGNORE:**

❌ **Non-examined assessment** - Coursework sections (can't make flashcards from projects)
❌ **Assessment Objectives** - AO1, AO2, AO3 details (not content)
❌ **Appendices** - Admin info, sample assessments
❌ **"Students will explore..."** narrative - Focus on actual content points

---

## 🚀 QUICK START GUIDE

### **To scrape a new table-structured subject:**

1. **Download PDF** (or use existing from batch run)

2. **Copy Business scraper:**
   ```bash
   cd scrapers/Edexcel/A-Level/topics
   cp scrape-business-improved.py scrape-NEWSUBJECT.py
   ```

3. **Update SUBJECT dict** (lines 42-48):
   ```python
   SUBJECT = {
       'code': '9XX0',
       'name': 'New Subject',
       # ... update all fields
   }
   ```

4. **Update themes** (lines 69-76):
   ```python
   themes = [
       {'code': 'Theme1', 'title': 'Theme 1: From PDF Contents', ...},
       # Count themes in PDF Contents section
   ]
   ```

5. **Run it:**
   ```bash
   python scrape-NEWSUBJECT.py
   ```

6. **Check results:**
   - Should get 200-700 topics depending on subject
   - 5 levels usually
   - If only 4 topics → Check themes list, check if PDF has tables

7. **Get papers:**
   ```bash
   cd ../papers
   cp scrape-business-papers-selenium.py scrape-NEWSUBJECT-papers.py
   # Update subject code and URL
   python scrape-NEWSUBJECT-papers.py
   ```

---

## 🎯 REMAINING SUBJECTS (27)

### **High Priority (Likely Easy Wins with Business Scraper):**
- Geography (9GE0) - Likely table-structured
- Psychology (9PS0) - Likely table-structured
- Politics (9PL0) - Likely table-structured
- Religious Studies (9RS0) - Check structure
- English Language (9EN0) - 3 components
- English Language and Literature (9EL0) - Prescribed texts
- English Literature (9ET0) - LOTS of prescribed texts

### **Languages (Manual Upload Like Arabic/Chinese):**
- French (9FR0)
- German (9GN0)
- Spanish (9SP0)
- Italian (9IN0)
- Japanese (9JA0)
- Russian (9RU0)
- Portuguese (9PT0)
- Greek (9GK0)
- Gujarati (9GU0)
- Persian (9PE0)
- Turkish (9TU0)
- Urdu (9UR0)

### **Sciences (Universal Scraper):**
- Biology B (9BI0) - Similar to Chemistry

### **Others (Check Structure):**
- Mathematics (9MA0)
- Statistics (9ST0)
- Music (9MU0)
- Music Technology (9MT0)
- Physical Education (9PE1)
- History of Art (9HT0)

---

## 🛠️ TOOLS & HELPERS

### **Data Viewer** (`data-viewer-v2.html`)

**Features:**
- Filter by exam board (AQA/Edexcel) and qualification
- View all topics with hierarchy
- Click to edit code/level/name inline
- Drag & drop to reorganize
- **📋 Manual Paper Entry** - Paste URLs when Selenium fails

**Manual Paper Entry:**
1. Click subject
2. Click "📋 Manual Paper Entry (Paste URLs)"
3. Paste paper URLs (one per line)
4. Click "🚀 Parse & Upload Papers"
5. Auto-parses and uploads

**Supported URL patterns:**
- `9xx0-01-que-20240522.pdf` (question)
- `9XX0_02_rms_20230817.pdf` (mark scheme)
- `9dr0-03-msc-20201217.pdf` (alternative mark scheme - Drama)
- `9ph0-01-pef-20220610.pdf` (examiner report)

**Auto-detects:**
- Year, series (June/October/January)
- Paper number
- Document type
- Groups into sets

### **Upload Helper** (`upload_papers_to_staging.py`)

Used by all paper scrapers:
```python
upload_papers_to_staging(
    subject_code='9BS0',
    qualification_type='A-Level',
    papers_data=sets,  # List of paper set dicts
    exam_board='Edexcel'
)
```

---

## 📝 TEMPLATE CODE SNIPPETS

### **Minimal Topic Scraper (Table-based)**

```python
SUBJECT = {
    'code': '9XX0',
    'name': 'Subject Name',
    'pdf_url': 'PDF_URL'
}

# Add themes from Contents
themes = [
    {'code': 'Theme1', 'title': 'Theme 1: Title', 'level': 0, 'parent': None},
    # ... more themes
]
topics.extend(themes)

# Parse tables (Business scraper logic)
# Looks for: 1.1, 1.1.1, a), o patterns
```

### **Minimal Paper Scraper (Selenium)**

```python
from selenium import webdriver
from bs4 import BeautifulSoup

driver = webdriver.Chrome(options=chrome_options)
driver.get(EXAM_MATERIALS_URL)
time.sleep(5)

# EXPAND ALL
expand = driver.find_elements(By.XPATH, "//*[contains(text(), 'EXPAND ALL')]")
if expand: driver.execute_script("arguments[0].click();", expand[0])

# Scroll
for _ in range(20):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(0.5)

# Scrape
soup = BeautifulSoup(driver.page_source, 'html.parser')
pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$'))

# Parse filenames: 9xx0-01-que-20240522.pdf
```

---

## 🎯 NEXT SESSION STRATEGY

### **Recommended Order:**

**1. Quick Wins (Use Business Scraper):**
- Geography
- Psychology  
- Politics
- Biology B (might work with Universal)

**2. English Subjects (3 subjects):**
- English Language - 3 components, skill-based
- English Language & Literature - Prescribed texts
- English Literature - LOTS of prescribed texts
- **Note:** May need manual upload for prescribed text lists

**3. Batch Languages (Manual Upload):**
- Copy Arabic/Chinese template
- Structure themes from PDF
- 10-15 mins each
- 12 languages × 15 mins = 3 hours total

**4. Remaining:**
- Mathematics, Statistics (check structure)
- Music, Music Tech (likely manual)
- Physical Education, History of Art

### **Efficiency Tips:**

1. **Download all PDFs first** (parallel)
2. **Quick check** each PDF structure (5 mins)
3. **Group by pattern** (table vs science vs manual)
4. **Process in batches** of same type
5. **Don't overthink** - if manual is faster, do manual

---

## 🐛 TROUBLESHOOTING

### **Papers scraper finds 0 papers:**

**Check:**
1. Does Edexcel actually publish papers for this subject?
2. Try enhanced version with longer waits (`-v2.py`)
3. Check coursematerials URL is correct
4. Use Manual Paper Entry in data viewer

**Drama Mystery:** Same code works for Design Tech (21 papers) but Drama (0 papers)
- Likely Angular/JavaScript issue specific to Drama page
- **Solution:** Use manual entry in data viewer

### **Topics scraper only finds 3-4 topics:**

**Reasons:**
1. Only found Papers/Themes (Level 0)
2. PDF has different structure than expected
3. Wrong parser template used

**Fix:**
1. Check `debug-SUBJECT-spec.txt`
2. Look for actual content structure
3. Use appropriate scraper or manual upload

### **Encoding errors:**

```
UnicodeEncodeError: 'charmap' codec can't encode character
```

**Fix:** Remove ALL emojis, use `[OK]` `[FAIL]` instead

---

## 📈 SUCCESS METRICS

**What "Complete" Looks Like:**

✅ **Good hierarchy:**
- Minimum 3 levels
- Ideally 4-5 levels (for AI)
- Clear parent-child relationships

✅ **Good topic count:**
- Sciences: 200-300 topics
- Humanities/Business: 500-700 topics
- Languages: 30-60 topics (themes-based)
- Arts: 30-100 topics (discipline-based)

✅ **Good paper coverage:**
- Minimum: 2017-2024 (8 years)
- 2-3 papers per subject
- Each set has QP + MS + ER ideally

**Don't aim for perfection:**
- Some subjects might only need Papers as Level 0
- Some papers might not exist on Edexcel site
- Manual entry is acceptable for edge cases

---

## 🎉 TODAY'S ACHIEVEMENTS

### **Subjects Completed: 10**
1. Arabic (55 topics, Arabic script!)
2. Art and Design (96 topics, 5 titles)
3. Business (613 topics, 5 levels!)
4. Chemistry (265 topics)
5. Chinese (36 topics, Chinese script!)
6. Design & Technology (139 topics, 12 papers)
7. Drama (36 topics, prescribed texts)
8. Economics A (663 topics, 5 levels!)
9. Economics B (660 topics, 5 levels!)
10. Physics (250 topics)

### **Key Innovations:**
- ✅ Multilingual Unicode support (Arabic + Chinese)
- ✅ Deep 5-level hierarchies (perfect for AI flashcards)
- ✅ Manual paper entry tool (bypass Selenium issues)
- ✅ Flexible parsers for different table structures
- ✅ Proven Selenium approach (no URL guessing)

### **Infrastructure:**
- ✅ Database with exam_board column
- ✅ Data viewer with Edexcel filter
- ✅ Upload helpers
- ✅ Debug files for all subjects

---

## 🔮 NEXT SESSION

**Continue from Economics B (9EB0 - done) → English subjects**

**Target:** Get to 20 subjects (54%)

**Estimated time:**
- English subjects (3): ~1 hour (may need manual for texts)
- Geography, Psychology, Politics (3): ~30 mins (Business scraper)
- Biology B (1): ~10 mins (Universal scraper)
- 3-4 languages: ~1 hour (manual upload)

**Total:** 20 subjects = ~3 hours work

---

**Tony's Vision:** Show users top 2-3 levels, use Level 4 for AI-generated flashcard questions. ✨

**Session Quality:** Productive! Fixed URL guessing mistake, added manual entry, proved table scraper pattern works brilliantly.

**Next AI:** Don't overthink PDF structures - use Business scraper for most, manual for edge cases. Focus on speed!

---

END OF SESSION - November 5, 2025

