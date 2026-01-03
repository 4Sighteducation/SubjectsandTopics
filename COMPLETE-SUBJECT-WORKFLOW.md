# Complete Subject Scraping Workflow
## One Repeatable Process for Every AQA Subject

**Example: Biology (7402) - Template for All Subjects**

---

## 🎯 **The Complete Process (Per Subject)**

### **Phase 1: Topics (Firecrawl - Fast!)**
✅ **Script:** `crawl-aqa-biology-complete.js`  
✅ **Time:** 1-2 minutes  
✅ **Gets:** Full topic hierarchy (70 topics with 3 levels)  
✅ **Stores:** `staging_aqa_topics` table

**Run:**
```bash
node crawl-aqa-biology-complete.js
```

**Result:**
- 8 main sections (3.1-3.8)
- 39 subsections (3.1.1, 3.1.2...)
- 23 detailed topics (3.1.4.1, 3.1.5.1...)
- Parent-child relationships linked
- "A-level only" flags set

---

### **Phase 2: Past Papers (Python/Selenium - Thorough!)**
✅ **Script:** `scrape-biology-everything.py`  
✅ **Time:** 2-3 minutes  
✅ **Gets:** Question papers, mark schemes, examiner reports (last 5 years)  
✅ **Stores:** `staging_aqa_exam_papers` table

**Run:**
```bash
python scrape-biology-everything.py
```

**Result:**
- ~30-50 paper documents
- Question papers (Papers 1, 2, 3)
- Mark schemes for each paper
- Examiner reports for each paper
- Years: 2024, 2023, 2022, 2021, 2020

---

## 📋 **Step-by-Step for Biology (Test Subject)**

### **Step 1: Topics (Already Done! ✅)**

You already ran this and got 70 topics in `staging_aqa_topics`.

If you need to re-run:
```bash
node crawl-aqa-biology-complete.js
```

### **Step 2: Past Papers (Run Now)**

```bash
cd "C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline"
python scrape-biology-everything.py
```

**What it does:**
1. Opens Chrome (headless) via Selenium
2. Navigates to: `https://www.aqa.org.uk/subjects/biology/a-level/biology-7402/assessment-resources`
3. Scrolls through pagination
4. Extracts ALL PDF links (question papers, mark schemes, reports)
5. Parses year, series, paper number from titles
6. Uploads to `staging_aqa_exam_papers`

**Expected:**
- ~40-60 documents (Papers 1,2,3 × 5 years × 3 types)
- Organized into ~15-20 complete sets

---

## ✅ **What You'll Have After Both:**

**In `staging_aqa_subjects`:**
```
1 record: Biology (A-Level), code 7402
```

**In `staging_aqa_topics`:**
```
70 records: Full topic hierarchy
- 3.1 Biological molecules
  - 3.1.1 Monomers and polymers
  - 3.1.2 Carbohydrates
  - ...
```

**In `staging_aqa_exam_papers`:**
```
~15-20 records: Complete paper sets
2024 June Paper 1: question_url, mark_url, report_url
2024 June Paper 2: question_url, mark_url, report_url
2023 June Paper 1: ...
...
```

---

## 🔄 **Repeat for All Subjects**

Once Biology works, create a subject list and loop:

### **For Each Subject:**

```bash
# 1. Topics (Node)
node crawl-aqa-{subject}-complete.js

# 2. Papers (Python)
python scrape-{subject}-everything.py
```

**Or create batch scripts:**

```bash
# Batch all AQA A-Level subjects
node batch-scrape-all-aqa.js
```

---

## 📊 **Complete Dataset Per Subject:**

| What | Source | Time | Records |
|------|--------|------|---------|
| Topics | Firecrawl | 1-2 min | 50-100 |
| Papers | Selenium | 2-3 min | 15-30 |
| **Total** | **Combined** | **3-5 min** | **65-130** |

**For 77 AQA subjects:**
- Time: 4-6 hours
- Records: ~5,000-8,000 topics + ~1,200 paper sets
- Cost: ~$25 Firecrawl credits

---

## 🎯 **Why This Approach Works:**

**Firecrawl for Topics:**
- ✅ Fast (1-2 min per subject)
- ✅ Clean markdown parsing
- ✅ Handles hierarchical pages well
- ✅ Cheap ($0.30 per subject)

**Python/Selenium for Papers:**
- ✅ Handles JavaScript (Firecrawl can't)
- ✅ Scrolls pagination automatically
- ✅ Already built and tested
- ✅ Free (just time)

**Combined:**
- ✅ Complete dataset per subject
- ✅ Repeatable process
- ✅ One template for all subjects

---

## 🚀 **Next: Run the Papers Scraper!**

```bash
python scrape-biology-everything.py
```

This will complete the Biology dataset!

Then we can:
1. Validate Biology is perfect
2. Create batch scripts for all subjects
3. Run overnight
4. Wake up to complete AQA database!

