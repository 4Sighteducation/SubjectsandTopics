# Edexcel Scrapers - PDF-Based Topic Extraction

**Exam Board:** Edexcel (Pearson)  
**Method:** Firecrawl for PDF specifications + Selenium for past papers  
**Status:** 🧪 Testing (History, then Biology)

---

## 🎯 APPROACH

### **Differences from AQA:**
- ✅ AQA: Specifications on web pages (HTML scraping)
- ✅ Edexcel: Specifications in PDFs (PDF → Markdown scraping)
- ✅ Same database structure (added `exam_board` column)

### **Firecrawl PDF Scraping:**
```javascript
const result = await fc.scrapeUrl(pdfUrl, {
  formats: ['markdown'],
  onlyMainContent: true
});
// Returns PDF content as markdown!
```

---

## 📂 STRUCTURE

```
Edexcel/
├─ A-Level/
│  ├─ topics/          (PDF-based scrapers)
│  │  ├─ scrape-edexcel-history.js
│  │  └─ scrape-edexcel-biology.js (coming next)
│  │
│  └─ papers/          (Selenium scrapers)
│     ├─ scrape-history-papers.py
│     └─ scrape-biology-papers.py (coming next)
│
└─ GCSE/               (coming later)
```

---

## 🚀 TESTING SUBJECTS

### **Phase 1: History A-Level** 
- Code: 9HI0
- Why: Complex structure (options, pathways) - good test!
- Topics scraper: `scrape-edexcel-history.js`
- Papers scraper: `scrape-history-papers.py`

### **Phase 2: Biology A-Level**
- Code: 9BI0
- Why: Standard science structure - validate patterns
- Topics scraper: `scrape-edexcel-biology.js` (to be created)
- Papers scraper: `scrape-biology-papers.py` (to be created)

### **Phase 3: General Scrapers**
After testing History and Biology, create:
- Master topic scraper (all A-Level subjects)
- Master papers scraper (all A-Level subjects)
- Then GCSE versions

---

## 💾 DATABASE SETUP

### **IMPORTANT: Run this SQL first!**
```sql
-- In Supabase SQL Editor:
-- Run: add-exam-board-column.sql
```

This adds `exam_board` column to:
- `staging_aqa_subjects`
- `staging_aqa_topics`
- `staging_aqa_exam_papers`

All scrapers now filter by `exam_board` to prevent AQA/Edexcel mixing.

---

## 📝 HOW TO RUN

### **1. Topics Scraper (History):**
```bash
cd scrapers/Edexcel/A-Level/topics
node scrape-edexcel-history.js
```

**What it does:**
1. Finds specification PDF URL from Pearson website
2. Scrapes PDF with Firecrawl → markdown
3. Parses topics from markdown
4. Uploads to `staging_aqa_subjects` and `staging_aqa_topics`
5. Sets `exam_board = 'Edexcel'`

**Output:**
- Topics in database with `exam_board='Edexcel'`
- Debug file: `debug-edexcel-history-spec.md` (raw PDF content)

---

### **2. Papers Scraper (History):**
```bash
cd scrapers/Edexcel/A-Level/papers
python scrape-history-papers.py
```

**What it does:**
1. Uses Selenium to navigate Pearson website
2. Finds PDF links for past papers
3. Groups by year, series, component code
4. Uploads to `staging_aqa_exam_papers`
5. Sets `exam_board = 'Edexcel'`

**Output:**
- Paper sets in database with `exam_board='Edexcel'`

---

## 🔍 VERIFICATION

### **Check topics in Supabase:**
```sql
SELECT COUNT(*) as topic_count
FROM staging_aqa_topics
WHERE exam_board = 'Edexcel';

-- Sample topics
SELECT topic_code, topic_name, topic_level
FROM staging_aqa_topics
WHERE exam_board = 'Edexcel'
  AND subject_id = (
    SELECT id FROM staging_aqa_subjects 
    WHERE subject_code = '9HI0' 
      AND exam_board = 'Edexcel'
  )
ORDER BY topic_code
LIMIT 20;
```

### **Check papers in Supabase:**
```sql
SELECT year, exam_series, paper_number, component_code
FROM staging_aqa_exam_papers
WHERE exam_board = 'Edexcel';
```

---

## 🎨 PDF PARSING PATTERNS

### **Edexcel History PDF Structure:**
Based on actual PDF analysis:
- Section: "Knowledge, skills and understanding: Papers 1 and 2"
- Tables with "Themes | Content" columns
- Options listed as large headings above tables

### **Hierarchy (4 Levels):**
```
Level 0: Papers
  Paper 1
  Paper 2
  Paper 3

Level 1: Options (large headings above tables)
  Option 1A: The crusades, c1095–1204
  Option 2C.2: Russia in revolution, 1894–1924
  Option 35.2: The British experience of warfare, c1790–1918

Level 2: Themes (from "Themes" column in tables)
  1 Reasons for the crusades, 1095–1192
  2 Leadership of the crusades, 1095–1192

Level 3: Content items (from "Content" column, UP TO COLON ONLY)
  Religious motives
  Political motives
  Geography and economy
```

### **Example Hierarchy:**
```
Paper 1 (L0)
├─ Option 1A: The crusades, c1095–1204 (L1)
│  ├─ 1 Reasons for the crusades, 1095–1192 (L2)
│  │  ├─ Religious motives (L3)
│  │  ├─ Political motives (L3)
│  │  └─ Geography and economy (L3)
│  └─ 2 Leadership of the crusades, 1095–1192 (L2)
│     └─ The First Crusade (L3)
Paper 2 (L0)
├─ Option 2C.2: Russia in revolution, 1894–1924 (L1)
Paper 3 (L0)
└─ Option 35.2: The British experience of warfare, c1790–1918 (L1)
```

### **Key Parsing Rules:**
1. ✅ Extract Papers (Paper 1, 2, 3) as Level 0
2. ✅ Extract Options (large headings) as Level 1
3. ✅ Parse table "Themes" column as Level 2
4. ✅ Parse table "Content" bullets as Level 3 (UP TO COLON ONLY!)
5. ✅ Ignore all text after the colon in Content items

---

## ⚙️ ENVIRONMENT VARIABLES

Required in `.env`:
```env
FIRECRAWL_API_KEY=fc-...
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=eyJ...
```

---

## 📊 COST ESTIMATE

### **Firecrawl API:**
- Cost per PDF: ~$0.30-0.50 (varies by page count)
- Edexcel History spec: ~100 pages = ~$0.40
- **Cheaper than AQA!** (1 PDF vs 10-20 web pages)

### **For all Edexcel A-Level (~30 subjects):**
- Estimated cost: ~$12-15 for all topics
- Much cheaper than AQA!

---

## 🐛 DEBUGGING

If topics scraper fails:
1. Check `debug-edexcel-history-spec.md` for raw PDF content
2. Verify PDF URL is accessible
3. Check Firecrawl API key is valid

If papers scraper fails:
1. Run with `headless=False` to see browser
2. Check if Pearson site structure has changed
3. Verify Selenium ChromeDriver is installed

---

## 📈 SUCCESS CRITERIA

### **History (Test 1):**
- [ ] Topics scraped from PDF ✅
- [ ] ~50-100 topics expected
- [ ] Papers scraped (5 years × ~10 papers = ~50 documents)
- [ ] All data in Supabase with `exam_board='Edexcel'`

### **Biology (Test 2):**
- [ ] Similar results to History
- [ ] Validates PDF scraping pattern
- [ ] Ready to build general scraper

---

## 🚀 NEXT STEPS

1. ✅ Run History scrapers (topics + papers)
2. ✅ Review in data-viewer-v2.html
3. ✅ Run Biology scrapers
4. ✅ Compare patterns
5. 🎯 Build master scrapers for all subjects

---

**Status:** Ready to test! 🚀

Run History scrapers first, review results in Supabase, then proceed to Biology.

