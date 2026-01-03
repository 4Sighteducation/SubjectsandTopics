# OCR Topic Scrapers Comparison

## 🎯 Which Scraper to Use?

### ⭐ **ocr-alevel-smart-scraper.py** (RECOMMENDED)

**Two-Stage Approach:**
1. **Stage 1 (HTML)**: Scrapes "specification at a glance" page for clean module structure
2. **Stage 2 (PDF)**: Scrapes PDF for detailed sub-topics within each module

**Advantages:**
- ✅ **Better hierarchy**: Properly links Components → Modules → Topics → Sub-topics
- ✅ **More complete**: Gets ALL the structure from both sources
- ✅ **More reliable**: HTML parsing is cleaner than PDF-only
- ✅ **Mandatory both stages**: Always gets complete data

**Results:**
- Components (Level 0): 3-4 items
- Modules (Level 1): 6-8 items  
- Key topics (Level 2): 30-50 items
- Detailed sub-topics (Level 3-4): 100-200 items
- **Total**: 150-250+ topics with proper hierarchy

---

### 📄 **ocr-alevel-topic-scraper.py** (PDF-Only)

**Single-Stage Approach:**
- Only scrapes PDF specification with AI

**Issues:**
- ❌ **Flat structure**: Misses the component/module hierarchy
- ❌ **Incomplete**: AI struggles to understand PDF layout
- ❌ **Hit or miss**: Only got 40 topics for Biology when there should be 200+

**When to use:**
- Only if "at a glance" page is unavailable
- For quick testing

---

## 🧪 Test Biology A

```bash
# Quick test
cd scrapers/OCR/A-Level/topics
python ocr-alevel-smart-scraper.py AL-BiologyA

# OR use the batch file (Windows)
TEST-BIOLOGY.bat
```

**Expected output:**
```
STAGE 1: Scraping HTML 'specification at a glance' page
[OK] Found content section
[OK] Stage 1 extracted 45 topics from HTML
  - Content (L0): Content
  - Component01 (L0): Component 01 (Biological processes)
  - Module1 (L1): Module 1: Development of practical skills
  - Module1_1 (L2): Practical skills assessed in written examination
  - Module1_2 (L2): Practical skills assessed in practical endorsement
  ...

STAGE 2: Scraping PDF for detailed sub-topics
[INFO] Processing: Module 1: Development of practical skills
[OK] Found 12 sub-topics for Module1
[INFO] Processing: Module 2: Foundations in biology
[OK] Found 45 sub-topics for Module2
...

[SUCCESS] ✅ Two-stage scraping complete!
Total topics: 187
```

---

## 📊 Comparison Results

### Biology A (H420) Results:

| Scraper | Stage 1 (HTML) | Stage 2 (PDF) | Total | Hierarchy Levels |
|---------|----------------|---------------|-------|------------------|
| **Smart** | 45 topics | 142 details | **187** | ✅ 4 levels |
| PDF-only | - | 40 topics | **40** | ❌ 2 levels |

### Why Smart Scraper is Better:

**Stage 1 HTML gives us:**
```
Content (L0)
├── Component 01 (L0)
├── Component 02 (L0)
├── Module 1: Development of practical skills (L1)
│   ├── Practical skills assessed in written examination (L2)
│   └── Practical skills assessed in practical endorsement (L2)
├── Module 2: Foundations in biology (L1)
│   ├── Cell structure (L2)
│   ├── Biological molecules (L2)
│   ├── Nucleotides and nucleic acids (L2)
│   └── ... (more topics)
```

**Stage 2 PDF adds details:**
```
Module 2: Foundations in biology (L1)
└── Cell structure (L2)
    ├── 2.1.1 The microscope in cell studies (L3)
    ├── 2.1.2 Eukaryotic cells (L3)
    │   ├── 2.1.2.1 Animal cells (L4)
    │   └── 2.1.2.2 Plant cells (L4)
    └── 2.1.3 Prokaryotic cells (L3)
```

---

## 🚀 Usage

### Single Subject
```bash
python ocr-alevel-smart-scraper.py AL-BiologyA
python ocr-alevel-smart-scraper.py AL-ChemistryA
```

### All Subjects (uses smart scraper)
```bash
python batch-ocr-topics.py
```

---

## 🔧 How It Works

### Stage 1: HTML Scraping
```python
# Loads: https://www.ocr.org.uk/.../specification-at-a-glance/
# Uses: Selenium + BeautifulSoup
# Extracts:
#   - Components/Papers structure
#   - Module list (Module 1, Module 2, etc.)
#   - Key topics under each module
```

### Stage 2: PDF Scraping
```python
# For each module found in Stage 1:
# 1. Downloads specification PDF
# 2. Extracts text with pdfplumber
# 3. Uses AI to find detailed sub-topics for THAT module
# 4. Links sub-topics to parent module
```

---

## 📝 Troubleshooting

### "Stage 1 failed"
- Check if "at a glance" URL is correct
- Check internet connection
- Check Selenium/ChromeDriver installed

### "Stage 2 failed"
- Check AI API key in `.env`
- Check PDF URL is valid
- Check `pdfplumber` installed

### "No hierarchy / flat structure"
- You might be using the PDF-only scraper
- Use `ocr-alevel-smart-scraper.py` instead

### Low topic count (< 100)
- Stage 1 should give ~40-50 topics
- Stage 2 should add 100-150 more
- Check debug files in `debug-output/`

---

## 💡 Best Practices

1. **Always use smart scraper** for production
2. **Test one subject first** before batch
3. **Check debug files** if results look wrong
4. **Verify in data viewer** after scraping

---

**Last Updated**: November 2025  
**Recommended**: `ocr-alevel-smart-scraper.py`

