# Edexcel A-Level Overnight Scraper

**Status:** Ready for automated overnight runs!

---

## ✅ IMPROVEMENTS MADE:

1. **No more Chrome noise** - Suppressed GPU/GCM warnings
2. **No manual input** - Runs fully automated (no "Press Enter")
3. **Headless by default** - Runs in background
4. **Error handling** - Continues even if one subject fails

---

## 🚀 CURRENT STATUS:

### **Tested & Working:**
- ✅ **History (9HI0)** - 559 topics, 259 paper sets
- ✅ **Biology A (9BN0)** - 189 topics, 30 paper sets

### **Ready to Test:**
- Biology B, Chemistry, Physics, Mathematics (+ 30+ more subjects)

---

## 📋 HOW TO RUN INDIVIDUAL SUBJECTS:

### **Topics:**
```bash
cd scrapers/Edexcel/A-Level/topics

# History (custom scraper)
node scrape-edexcel-history.js

# Biology A, Chemistry, Physics, etc. (Python scraper)
python scrape-biology-a-python.py
```

### **Papers:**
```bash
cd scrapers/Edexcel/A-Level/papers

# Any subject (same Selenium approach)
python scrape-history-papers-selenium.py    # History
python scrape-biology-a-papers.py           # Biology A
```

---

## 🌙 OVERNIGHT BATCH RUN:

### **Option 1: Run subjects one-by-one** (RECOMMENDED for now)

Create a batch script with all subjects:

```batch
@echo off
echo Starting Edexcel A-Level scraping...
echo %date% %time%

cd scrapers\Edexcel\A-Level\topics

echo.
echo === Biology A Topics ===
python scrape-biology-a-python.py

echo.
echo === Chemistry Topics ===
REM python scrape-chemistry-python.py

echo.
echo === Physics Topics ===
REM python scrape-physics-python.py

cd ..\papers

echo.
echo === Biology A Papers ===
python scrape-biology-a-papers.py

echo.
echo DONE!
echo %date% %time%
pause
```

### **Option 2: Master scraper** (COMING SOON)

```bash
python run-all-edexcel-alevel.py --all
```

This will automatically run all subjects and generate a report.

---

## 🔧 FOR TOMORROW:

### **To add a new subject:**

1. **Add to** `edexcel-alevel-subjects.json`:
```json
{
  "name": "Chemistry",
  "code": "9CH0",
  "pdf_url": "https://qualifications.pearson.com/content/dam/pdf/...",
  "exam_materials_url": "https://qualifications.pearson.com/en/qualifications/...",
  "scraper_type": "simple",
  "status": "untested"
}
```

2. **Copy Biology scraper**, update SUBJECT config
3. **Run it!**

---

## 📊 EXPECTED RESULTS PER SUBJECT:

### **Simple Sciences (Biology, Chemistry, Physics):**
- Topics: ~150-200 (Papers → Topics → Items)
- Papers: ~24-30 (3 papers × 8 years)
- Time: ~2-3 minutes total

### **Complex Subjects (History, etc.):**
- Topics: ~500-600 (Routes → Options → Themes → Content)
- Papers: ~200-300 (40 components × multiple years)
- Time: ~5-10 minutes total

---

## 💡 TIPS:

1. **Run topics first, check in Supabase, then run papers**
2. **Biology scraper works for most sciences** (just change config)
3. **History scraper is unique** (don't reuse for other subjects unless they have Routes)
4. **Check data-viewer-v2.html** after each subject
5. **Collapse sections** in viewer for big subjects (click ▼)

---

## 🐛 TROUBLESHOOTING:

### **If topics fail:**
- Check debug file: `debug-edexcel-{subject}-spec.txt`
- PDF might be protected/encrypted
- Try different PDF URL

### **If papers fail:**
- Check if EXPAND ALL button worked
- Some subjects might have different page structure
- 2020-2021 COVID years may have gaps

---

**Ready for overnight scaling!** 🚀

