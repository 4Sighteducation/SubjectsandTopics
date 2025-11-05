# Edexcel Scraping Session - Handover Document
**Date:** November 4-5, 2025  
**Status:** 2 Subjects Complete, Batch Automation Needs Work  
**Next Session:** Fix PDF parsing for remaining subjects

---

## WHAT WORKED - BIG WINS! ✅

### **1. History (9HI0) - COMPLETE**
- ✅ **559 topics** with complex 4-level hierarchy:
  - Level 0: Routes (A-H) + Paper 3
  - Level 1: Options (40 options)
  - Level 2: Themes (117 themes)
  - Level 3: Content items (408 items)
- ✅ **259 paper sets** (2017-2024, all URLs working)
- ✅ **Scraper:** `scrapers/Edexcel/A-Level/topics/scrape-edexcel-history.js`
- ✅ **Papers:** `scrapers/Edexcel/A-Level/papers/scrape-history-papers-selenium.py`
- ✅ **Hierarchy:** Routes → Options → Themes → Content (perfect student pathway structure)

### **2. Biology A (9BN0) - COMPLETE**
- ✅ **189 topics** with simple 4-level hierarchy:
  - Level 0: Papers (3 papers)
  - Level 1: Topics (8 topics)
  - Level 2: Items (138 numbered items like 1.1, 1.2)
  - Level 3: Sub-items (40 roman numeral items like 1.4.i)
- ✅ **30 paper sets** (2017-2024)
- ✅ **Scraper:** `scrapers/Edexcel/A-Level/topics/scrape-biology-a-python.py`
- ✅ **Papers:** `scrapers/Edexcel/A-Level/papers/scrape-biology-a-papers.py`

### **3. Infrastructure - ALL WORKING**
- ✅ **Database migration:** Added `exam_board` column to all 3 staging tables
- ✅ **Data viewer updated:** 
  - Edexcel filter dropdown
  - Hierarchical tree view (not just flat list)
  - Collapse/expand functionality (click ▼ to collapse branches)
  - Routes before Papers in sort order
- ✅ **Upload helper updated:** Supports `exam_board` parameter

### **4. Total Database**
- ✅ **Edexcel: 748 topics** (559 History + 189 Biology A)
- ✅ **Edexcel: 289 paper sets** (259 History + 30 Biology A)
- ✅ **AQA: ~10,000 topics, ~900 paper sets** (from previous sessions)
- ✅ **Grand Total: ~10,750 topics across 81 subjects!**

---

## WHAT'S BROKEN ❌

### **1. PDF Parsing for Non-Biology Subjects**
**Problem:** Biology scraper only finds 3 topics (the Papers) when run on other subjects.

**Why:** The parser looks for "Topic X:" pattern which works for Biology but Chemistry doesn't use that format.

**Example:**
- Biology PDF: "Topic 1: Lifestyle, Health and Risk" ✅ (found)
- Chemistry PDF: Different structure ❌ (not found)

**Files affected:**
- All generated scrapers in `A-Level/topics/scrape-9*.py` (36 files)
- Based on Biology template but need subject-specific parsing

### **2. Batch Automation - Windows Encoding Hell**
**Problem:** Subprocess calls fail with charmap encoding errors on Windows.

**What we tried:**
- UTF-8 encoding on all file operations ❌ (still failing)
- Removed emojis from overnight scraper ❌ (still issues)
- Template file generation ❌ (encoding cascades)

**Files:**
- `run-overnight-edexcel-alevel.py` (complex, has encoding issues)
- `run-all-topics.bat` (simple batch file - better approach)

---

## FILES CREATED THIS SESSION

### **Working Scrapers:**
```
scrapers/Edexcel/
├─ A-Level/
│  ├─ topics/
│  │  ├─ scrape-edexcel-history.js ✅ WORKING
│  │  ├─ scrape-biology-a-python.py ✅ WORKING
│  │  ├─ scrape-9ch0.py (Chemistry) ⚠️ BROKEN (only finds 3 topics)
│  │  └─ scrape-9*.py × 35 more ⚠️ BROKEN (all based on Biology template)
│  │
│  └─ papers/
│     ├─ scrape-history-papers-selenium.py ✅ WORKING
│     ├─ scrape-biology-a-papers.py ✅ WORKING
│     ├─ scrape-history-papers-direct.py (URL construction - partially working)
│     └─ scrape-history-papers-v2.py (old version)
│
├─ edexcel-alevel-subjects-complete.json ✅ (38 subjects with PDF URLs)
├─ generate-topic-scrapers.py ✅ (generator script)
├─ run-overnight-edexcel-alevel.py ⚠️ (has encoding issues)
├─ run-all-topics.bat ⚠️ (simple but untested)
├─ scrape-all-subjects.py (auto-discovery - incomplete)
└─ README-OVERNIGHT-RUN.md ✅
```

### **Updated Files:**
```
data-viewer-v2.html ✅ (Edexcel filter, collapse/expand, tree sort)
upload_papers_to_staging.py ✅ (supports exam_board parameter)
add-exam-board-column.sql ✅ (database migration)
```

---

## THE CORE PROBLEM

**The Biology topic parser is too specific to Biology's PDF structure:**

```python
# This works for Biology:
topic_match = re.match(r'Topic\s+(\d+):\s+(.+)', line)

# But Chemistry has different headers!
# Need to check Chemistry's actual structure
```

**Chemistry likely has:**
- Different topic headers (not "Topic 1:")
- Different numbering schemes
- Different content organization

---

## WHAT TO DO NEXT SESSION

### **Option 1: Quick Fix (30 mins)**
1. **Open Chemistry debug file** (`debug-biology-a-spec.txt` - last run overwrote it)
2. **Find the actual topic structure** (search for numbered items, content sections)
3. **Update Biology parser** to handle both formats
4. **Test on 3-4 subjects** (Chemistry, Physics, one language, one humanity)
5. **If all similar, run batch**

### **Option 2: Subject-Type Approach (1 hour)**
1. **Manually test 1 subject from each type:**
   - Science: Chemistry ✅ (already have Biology pattern)
   - Language: French
   - Humanity: Psychology or Geography
   - Arts: Art and Design
2. **Create 3-4 parser templates** (one per subject type)
3. **Assign subjects to templates** in JSON
4. **Run batch with appropriate template per subject**

### **Option 3: Use What Works (FASTEST)**
1. **Just manually run Chemistry and Physics** (likely same as Biology)
2. **That gives you 4 complete subjects** (History, Bio A, Chem, Physics)
3. **Prove the pattern works**
4. **Then tackle batch automation fresh**

---

## RECOMMENDED NEXT STEPS

**IMMEDIATE (5 mins):**
1. Download Chemistry PDF manually
2. Look at pages 30-50 (where content usually starts)
3. See if it has "Topic 1:", "Topic 2:" or something different
4. Tell next AI the actual format

**THEN:**
- If same as Biology → Fix parser, run batch
- If different → Create Chemistry-specific parser

---

## KEY LESSONS LEARNED

### **What Worked Brilliantly:**
- ✅ **Python + pypdf** for local PDF parsing (fast, reliable)
- ✅ **Selenium with EXPAND ALL** for papers (works every time)
- ✅ **Firecrawl for some PDFs** (History worked great)
- ✅ **Individual scrapers** per subject (maintainable)
- ✅ **Database with exam_board column** (scales to all boards)

### **What Needs Work:**
- ⚠️ **PDF structure varies by subject** (need templates per subject type)
- ⚠️ **Windows encoding** (subprocess + emojis + Unicode = pain)
- ⚠️ **Batch automation** (works in theory, encoding hell in practice)

### **What to Avoid:**
- ❌ Assuming all subjects have same PDF structure
- ❌ Complex subprocess orchestration on Windows
- ❌ Emojis in any automation scripts (Windows hates them)

---

## CURRENT DATABASE STATE

**Supabase staging tables:**

```sql
-- Check what's actually there
SELECT exam_board, COUNT(*) as subject_count
FROM staging_aqa_subjects
GROUP BY exam_board;

-- Should show:
-- AQA: 79 subjects
-- Edexcel: 3 subjects (History, Biology A, Chemistry with 3 topics)
```

**All working URLs:**
- History: 259 paper sets with QP, MS, ER all working ✅
- Biology A: 30 paper sets all working ✅

---

## FOR TOMORROW'S AI

**User (Tony) wants:**
- ✅ Get batch topic scraping working for all 36 remaining Edexcel A-Levels
- ✅ Understand why Chemistry parser only found 3 topics (structure difference)
- ✅ Fix or rebuild to handle different PDF structures
- ✅ Run overnight batch successfully

**Priority:**
1. **FIX CHEMISTRY PARSING** (most important - unlocks all other sciences)
2. Test Physics (should be same as Chemistry)
3. Test one language (French)
4. Build working batch runner
5. Run overnight on all subjects

**Don't:**
- ❌ Overcomplicate with dynamic file generation
- ❌ Use emojis anywhere
- ❌ Assume all PDFs have same structure

**Do:**
- ✅ Check actual PDF structure before writing parser
- ✅ Create simple, direct scripts
- ✅ Test individually before batch
- ✅ Keep it simple!

---

## QUICK WINS AVAILABLE

**Chemistry debug file exists:** `debug-biology-a-spec.txt`
- Open it
- Search for topic numbers (1.1, 1.2, etc.)
- See actual structure
- Fix parser in 10 minutes

**Then:**
- Run Chemistry ✅
- Run Physics ✅
- Run Biology B ✅
- Proves pattern works
- Batch run the rest!

---

**END OF SESSION**

**Tony's frustration is valid** - we spent hours on automation that should have been simpler. But we DO have 2 complete subjects with 748 topics and 289 paper sets, plus proven patterns. Just need to fix the PDF parsing for subject type variations.

**Communication style for next session:**
- Get straight to fixing Chemistry parser
- Test quickly
- Don't overthink it
- Show results, not process

