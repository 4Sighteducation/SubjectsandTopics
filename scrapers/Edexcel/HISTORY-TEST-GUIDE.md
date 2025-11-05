# Edexcel History A-Level - Test Guide

**Subject:** History  
**Code:** 9HI0  
**Exam Board:** Edexcel  
**PDF URL:** https://qualifications.pearson.com/content/dam/pdf/A%20Level/History/2015/Specification%20and%20sample%20assessments/9781446914366-gce-2015-a-hist.pdf

---

## 📊 EXPECTED HIERARCHY

Based on your requirements:

```
Level 0: Papers
  Paper 1
  Paper 2  
  Paper 3

Level 1: Options (from large headings above tables)
  Option 1A: The crusades, c1095–1204
  Option 1B: England, 1509–1603: authority, nation and religion
  Option 2C.2: Russia in revolution, 1894–1924
  Option 35.2: The British experience of warfare, c1790–1918
  ... etc.

Level 2: Themes (from "Themes" column in tables)
  1 Reasons for the crusades, 1095–1192
  2 Leadership of the crusades, 1095–1192
  ... etc.

Level 3: Content items (from "Content" column, UP TO COLON ONLY!)
  Religious motives
  Political motives
  Geography and economy
  ... etc.
```

---

## 📋 PARSING RULES

### **What Gets Extracted:**

1. **Papers** → Level 0
   - Source: Headings like "Paper 1", "Paper 2", "Paper 3"
   - Code: `Paper1`, `Paper2`, `Paper3`

2. **Options** → Level 1
   - Source: Large headings above tables
   - Format: "Option 1A: The crusades, c1095–1204"
   - Code: `Option1A`, `Option2C.2`, `Option35.2`
   - Parent: Papers

3. **Themes** → Level 2
   - Source: Left column of "Themes | Content" tables
   - Format: "1 Reasons for the crusades, 1095–1192"
   - Code: `Option1A.1`, `Option1A.2`
   - Parent: Options

4. **Content Items** → Level 3
   - Source: Right column ("Content") of tables
   - Format: Bullet points with colons
   - **EXTRACT ONLY UP TO COLON!**
   - Example: "Geography and economy: Edessa, Tripoli..." → "Geography and economy"
   - Code: `Option1A.1.1`, `Option1A.1.2`
   - Parent: Themes

---

## 🎯 EXAMPLE

### **From PDF:**
```
Option 1A: The crusades, c1095–1204

| Themes                                      | Content                                    |
|---------------------------------------------|--------------------------------------------|
| 1 Reasons for the crusades, 1095–1192      | • Religious motives: the concept of       |
|                                             |   'just war'; the impact of the papal...  |
|                                             | • Political motives: threats to the...    |
|                                             | • Geography and economy: Edessa, Tripoli..|
```

### **Extracted Topics:**
```
Paper 1 (Level 0)
└─ Option 1A: The crusades, c1095–1204 (Level 1)
   └─ 1 Reasons for the crusades, 1095–1192 (Level 2)
      ├─ Religious motives (Level 3)
      ├─ Political motives (Level 3)
      └─ Geography and economy (Level 3)
```

---

## 🚀 HOW TO RUN

### **Prerequisites:**

1. **Run SQL migration first:**
   ```sql
   -- In Supabase SQL Editor, run:
   -- flash-curriculum-pipeline/add-exam-board-column.sql
   ```

2. **Check .env file:**
   ```env
   FIRECRAWL_API_KEY=fc-...
   SUPABASE_URL=https://...
   SUPABASE_SERVICE_KEY=eyJ...
   ```

---

### **Step 1: Topics Scraper**

```bash
cd "C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\scrapers\Edexcel\A-Level\topics"
node scrape-edexcel-history.js
```

**Expected Output:**
```
🚀 EDEXCEL HISTORY A-LEVEL - TOPIC SCRAPER (PDF)
============================================================

Subject: History
Code: 9HI0
Exam Board: Edexcel

Expected hierarchy:
  Level 0: Papers (Paper 1, Paper 2, Paper 3)
  Level 1: Options (Option 1A, Option 2C.2, etc.)
  Level 2: Themes (from table "Themes" column)
  Level 3: Content items (up to colon only)

📄 Using direct PDF URL...
   URL: https://qualifications.pearson.com/content/dam/pdf/A%20Level/History/...

📄 Scraping PDF specification...
   This may take 30-60 seconds...

✅ PDF scraped successfully!
   Content length: 250000 characters
   Saved raw markdown to debug-edexcel-history-spec.md

📋 Parsing History topics from PDF...
   Found Paper 1
   Found Option 1A: The crusades, c1095–1204
   Found Option 1B: England, 1509–1603...
   ...

✅ Parsed 150 unique topics
   Distribution:
   Level 0: 3 topics
   Level 1: 24 topics
   Level 2: 60 topics
   Level 3: 63 topics

💾 Uploading to staging database...
✅ Subject: History (A-Level) [Edexcel]
✅ Cleared old topics (prevents duplicates)
✅ Uploaded 150 topics
✅ Linked 147 parent-child relationships

============================================================
✅ EDEXCEL HISTORY - TOPICS COMPLETE!
   Total topics: 150
   Exam board: Edexcel
```

---

### **Step 2: Check in Supabase**

```sql
-- Check subject
SELECT * FROM staging_aqa_subjects 
WHERE exam_board = 'Edexcel' AND subject_code = '9HI0';

-- Check topics (first 20)
SELECT topic_code, topic_name, topic_level, parent_topic_id
FROM staging_aqa_topics
WHERE exam_board = 'Edexcel'
  AND subject_id = (
    SELECT id FROM staging_aqa_subjects 
    WHERE subject_code = '9HI0' AND exam_board = 'Edexcel'
  )
ORDER BY topic_code
LIMIT 20;

-- Check distribution by level
SELECT topic_level, COUNT(*) as count
FROM staging_aqa_topics
WHERE exam_board = 'Edexcel'
GROUP BY topic_level
ORDER BY topic_level;
```

---

### **Step 3: Papers Scraper (after verifying topics)**

```bash
cd "C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\scrapers\Edexcel\A-Level\papers"
python scrape-history-papers.py
```

---

## 🐛 DEBUGGING

### **If topics look wrong:**

1. **Check debug file:**
   ```
   debug-edexcel-history-spec.md
   ```
   This shows the raw PDF content converted to markdown

2. **Look for:**
   - Are "Paper 1", "Paper 2", "Paper 3" visible?
   - Are "Option" headings visible?
   - Are tables formatted correctly?
   - Are bullets with colons present?

3. **Common issues:**
   - PDF didn't scrape properly (check Firecrawl API key)
   - Table format different than expected
   - Headings use different markdown levels

---

## ✅ SUCCESS CRITERIA

After running, you should see in Supabase:

- ✅ **3 Level 0 topics** (Paper 1, Paper 2, Paper 3)
- ✅ **~20-30 Level 1 topics** (Options like 1A, 2C.2, etc.)
- ✅ **~50-80 Level 2 topics** (Themes from tables)
- ✅ **~60-100 Level 3 topics** (Content items, up to colon)
- ✅ All topics have `exam_board='Edexcel'`
- ✅ Hierarchy correctly linked (parent_topic_id)

---

## 📞 NEXT STEPS

1. ✅ Run History topics scraper
2. ✅ Review in Supabase
3. ✅ Check hierarchy in data-viewer-v2.html
4. ✅ If looks good → run papers scraper
5. ✅ If issues → check debug file and adjust parsing

---

**Ready to test!** 🚀

