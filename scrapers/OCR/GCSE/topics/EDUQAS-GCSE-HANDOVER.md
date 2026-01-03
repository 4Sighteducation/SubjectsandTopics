# Eduqas GCSE Universal Scraper - Handover Document

**Date:** November 23, 2025  
**Status:** ✅ Working - Ready for A-Level Adaptation  
**Location:** `scrapers/OCR/GCSE/topics/`

---

## 📋 Executive Summary

Successfully developed a **universal scraper** for ALL Eduqas GCSE subjects that:
- ✅ Automatically finds PDF URLs from Eduqas website
- ✅ Downloads and analyzes PDF specifications
- ✅ Extracts topics using AI with deep Level 4+ extraction
- ✅ Handles special cases (Components, Tiers, Options, Appendices)
- ✅ Uploads to Supabase staging tables
- ✅ Generates detailed reports with self-assessment

**Current Status:**
- **Business**: ✅ Perfect (214 topics, Level 4+ extraction working)
- **Computer Science**: ✅ Perfect (144 topics, Level 4+ extraction working)
- **Other subjects**: Ready for batch processing with Level 4+ improvements

---

## 🗂️ Key Files

### **Main Scraper**
- **`eduqas-gcse-universal-scraper.py`** (1,165 lines)
  - Main universal scraper class
  - Handles all GCSE subjects automatically
  - AI-powered extraction with depth emphasis

### **Supporting Files**
- **`eduqas-pdf-url-scraper.py`**
  - Finds PDF URLs from Eduqas website using Selenium
  - Caches URLs in `eduqas-pdf-urls.json`

- **`Eduqas Qualifications - All.md`**
  - List of all Eduqas GCSE and A-Level subjects
  - Used to load subject list

- **`eduqas-pdf-urls.json`**
  - Cached PDF URLs (auto-generated)
  - Format: `{"Subject Name - GCSE": {"subject": "...", "level": "GCSE", "pdf_url": "..."}}`

### **Documentation**
- **`EDUQAS-GCSE-UNIVERSAL-SCRAPER-README.md`**
  - Detailed usage guide
  - Special cases documentation

- **`EDUQAS-PDF-URL-SCRAPER-README.md`**
  - PDF URL finder documentation

### **Batch Files**
- **`RUN-EDUQAS-GCSE-UNIVERSAL.bat`** - Full batch run (all subjects)
- **`TEST-EDUQAS-GCSE-UNIVERSAL.bat`** - Test run (3 subjects)
- **`TEST-COMPUTER-SCIENCE.bat`** - Test single subject
- **`RUN-EDUQAS-PDF-URLS.bat`** - Find all PDF URLs
- **`TEST-EDUQAS-PDF-URLS.bat`** - Test PDF URL finder

### **Reports**
- **`reports/`** folder contains:
  - Individual subject reports: `{Subject}-report.json`
  - Summary reports: `summary-{timestamp}.json`
  - Content section debug files: `{Subject}-content-section.txt`

---

## 🔧 How It Works

### **Workflow**

```
1. Load Subjects
   ↓
2. Find PDF URL (if not cached)
   ↓
3. Download PDF
   ↓
4. Extract PDF Text (pdfplumber)
   ↓
5. Analyze Structure (detect Components/Tiers/Options/Appendices)
   ↓
6. Build AI Prompt (with subject-specific instructions)
   ↓
7. Extract Topics via AI (GPT-4 or Claude)
   ↓
8. Parse Hierarchy (numbered format → topic dicts)
   ↓
9. Upload to Supabase (staging_aqa_subjects + staging_aqa_topics)
   ↓
10. Generate Report (with self-assessment)
```

### **Key Components**

#### **1. PDF URL Finding** (`eduqas-pdf-url-scraper.py`)
- Uses Selenium to navigate Eduqas website
- Finds subject pages: `https://www.eduqas.co.uk/ed/qualifications/{subject}-gcse/`
- Locates specification PDF links
- Caches URLs for future use

#### **2. Structure Analysis** (`_analyze_pdf_structure`)
Detects:
- **Components**: Component 1, Component 2, etc.
- **Tiers**: Foundation Tier, Higher Tier (Mathematics)
- **Options**: Optional units (Geography, History)
- **Appendices**: Prescribed texts (English Literature), vocabulary (Languages)

#### **3. AI Extraction** (`_extract_hierarchy`)
- Uses GPT-4o or Claude 3.5 Sonnet
- Two-phase approach:
  - **Phase 1**: Analyze PDF structure
  - **Phase 2**: Extract hierarchical topics
- Emphasizes **Level 4+ extraction** (bullet points, sub-bullets, examples)

#### **4. Prompt Engineering**
- **General instructions**: Apply to all subjects
- **Subject-specific instructions**: Business, Geography, Mathematics, Languages, etc.
- **Structure examples**: Shows expected hierarchy format
- **Critical rules**: Emphasizes depth extraction

#### **5. Database Upload** (`_upload_topics`)
- Upserts subject to `staging_aqa_subjects`
- Inserts topics in batches (500 per batch)
- Links parent-child relationships (individual updates - 2000+ individual updates)
- Uses `exam_board='WJEC'` (Eduqas is part of WJEC)

---

## 🎯 Key Features

### **1. Level 4+ Extraction (Critical Improvement)**

**Problem:** Other subjects weren't extracting deep enough (only Level 0-3)

**Solution:** Enhanced prompt to emphasize Level 4+ extraction:
- Bullet points → Level 4
- Sub-bullets → Level 5
- Numbered lists (a), b), i), ii)) → Level 4+
- Examples and case studies → Level 4+
- Detailed clarifications → Level 4+

**Result:** Business extracts 159 Level 4 topics (vs 0 before)

### **2. Automatic PDF URL Finding**

- Scraper automatically finds PDF URLs if not cached
- Uses Selenium to navigate Eduqas website
- Caches URLs in `eduqas-pdf-urls.json`
- Falls back gracefully if URL finding fails

### **3. Structure Detection**

Automatically detects and handles:
- **Components**: Geography A (Component 1 & 2)
- **Tiers**: Mathematics (Foundation/Higher)
- **Options**: History/Geography options
- **Appendices**: English Literature prescribed texts

### **4. Subject-Specific Handling**

Special instructions for:
- **Business**: Two-column format (Content/Amplification)
- **Geography**: Components with Core themes + Options
- **Mathematics**: Foundation/Higher tier separation
- **Languages**: Vocabulary integration from appendices
- **English Literature**: Prescribed texts from appendices

### **5. Self-Assessment**

Generates quality reports:
- Topic count validation
- Level depth checking
- Component/tier completeness
- Success grade (0-100)
- Issues and warnings

### **6. Exclusion System**

- Automatically excludes **Business** and **Computer Science** when running all subjects
- Can still test individual subjects explicitly
- Prevents re-scraping perfect subjects

---

## 📊 Current Status

### **Completed Subjects**
- ✅ **Business** (214 topics, Level 4+ working perfectly)
- ✅ **Computer Science** (144 topics, Level 4+ working perfectly)
- ✅ **Art and Design** (48 topics)
- ✅ **Design and Technology** (90 topics)
- ✅ **Drama** (63 topics)

### **Ready for Batch Processing**
- 25 GCSE subjects total
- 2 excluded (Business, Computer Science)
- **23 subjects ready** for batch processing

### **Expected Results**
- Most subjects: 100-400 topics
- Sciences: 200-500 topics
- Languages: 50-150 topics
- Arts: 30-100 topics

---

## 🔑 Critical Code Sections

### **1. Level 4+ Extraction Prompt** (Lines 771-810)

```python
STRUCTURE TO CREATE (MUST GO TO LEVEL 4+):
1. Component/Tier Name (Level 0)
   1.1 Core Theme/Topic Name (Level 1)
       1.1.1 Sub-topic name (Level 2)
           1.1.1.1 Specific content point (Level 3)
               1.1.1.1.1 Detailed explanation (Level 4)
               1.1.1.1.2 Another detailed explanation (Level 4)

CRITICAL RULES FOR DEPTH:
- **CRITICAL: DRILL DOWN TO LEVEL 4+**
- **DO NOT STOP at Level 3**
- Level 4+ = Bullet points, sub-bullets, numbered lists, examples
```

### **2. Subject Exclusion** (Lines 192-207)

```python
# Exclude subjects that are already perfect
if not subject_filter:
    excluded_subjects = ['Business', 'Computer Science']
    self.subjects = [s for s in self.subjects if s['name'] not in excluded_subjects]
```

### **3. Structure Analysis** (Lines 439-559)

```python
def _analyze_pdf_structure(self, subject: Dict, pdf_text: str) -> Dict:
    # Detects Components, Tiers, Options, Appendices
    # Returns analysis dict with structure_type
```

### **4. Database Upload** (Lines 930-1074)

```python
def _upload_topics(self, subject: Dict, topics: List[Dict]) -> bool:
    # Upserts subject
    # Inserts topics in batches (500 per batch)
    # Links parent relationships (individual updates)
```

---

## 🚀 Usage Examples

### **Test Single Subject**
```bash
cd scrapers/OCR/GCSE/topics
python eduqas-gcse-universal-scraper.py --subject "Geography A" --limit 1
```

### **Test Multiple Subjects**
```bash
python eduqas-gcse-universal-scraper.py --limit 5
```

### **Full Batch Run**
```bash
RUN-EDUQAS-GCSE-UNIVERSAL.bat
```

### **Find PDF URLs**
```bash
RUN-EDUQAS-PDF-URLS.bat
```

---

## 📝 Important Notes

### **Database Tables**
- **`staging_aqa_subjects`**: Subject metadata
- **`staging_aqa_topics`**: Topic hierarchy
- Uses `exam_board='WJEC'` (Eduqas is part of WJEC)
- Uses `qualification_type='GCSE'`

### **AI Provider**
- Supports both OpenAI GPT-4o and Anthropic Claude 3.5 Sonnet
- Auto-detects available API key
- Uses GPT-4o if both available

### **Rate Limiting**
- 5 second delay between subjects
- Respects API rate limits
- Can be interrupted and resumed

### **Error Handling**
- Graceful fallbacks for PDF URL finding
- Individual topic insert fallback if batch fails
- Detailed error reporting in JSON reports

### **Known Limitations**
- Parent relationship updates are individual (not batched)
  - This is normal - all scrapers do this
  - Works fine, just slower (1000+ individual PATCH requests)
  - Optional SQL stored procedure available for true batching

---

## 🎓 Adapting for A-Level

### **Key Differences Expected**

1. **More Complex Structures**
   - A-Level subjects may have more components
   - More options/optional units
   - Deeper hierarchies

2. **Subject List**
   - Use A-Level section from `Eduqas Qualifications - All.md`
   - Filter by `level == 'A-Level'` or `'A'` in level field

3. **PDF URLs**
   - A-Level URLs: `https://www.eduqas.co.uk/ed/qualifications/{subject}-as-a-level/`
   - May need URL pattern adjustments

4. **Prompt Adjustments**
   - May need A-Level specific instructions
   - Deeper hierarchies expected
   - More complex component structures

### **Files to Create/Modify**

1. **`eduqas-alevel-universal-scraper.py`**
   - Copy from GCSE scraper
   - Change `level` filter to 'A-Level'
   - Update URL patterns
   - Adjust prompt for A-Level depth

2. **Update `eduqas-pdf-url-scraper.py`**
   - Add A-Level URL pattern support
   - Update `find_subject_page_url` for A-Level

3. **Subject List**
   - Extract A-Level subjects from `Eduqas Qualifications - All.md`
   - Filter: `level == 'A'` or contains 'A-Level'

### **Quick Start for A-Level**

```python
# In load_gcse_subjects() → rename to load_alevel_subjects()
# Change filter:
if level_part == "A" or "A-Level" in level_part:
    # Add A-Level subjects
```

---

## 📈 Success Metrics

### **Quality Indicators**
- **Success Grade**: Should be > 70%
- **Topic Count**: Varies by subject (see Expected Results above)
- **Level Depth**: Should have Level 4+ topics
- **Component Coverage**: All components extracted

### **Report Structure**
```json
{
  "subject_name": "Geography A",
  "success": true,
  "topics_extracted": 450,
  "levels": {
    "0": 2,    // Components
    "1": 8,    // Themes
    "2": 30,   // Sub-topics
    "3": 150,  // Content points
    "4": 260   // Detailed examples (Level 4+)
  },
  "success_grade": 92,
  "issues": [],
  "warnings": []
}
```

---

## 🐛 Troubleshooting

### **PDF URL Not Found**
- Run `RUN-EDUQAS-PDF-URLS.bat` first
- Check `eduqas-pdf-urls.json` exists
- Verify subject name matches Eduqas website

### **Low Topic Count**
- Check report JSON for specific errors
- Review `{Subject}-content-section.txt` debug file
- Verify PDF structure matches expected patterns

### **Missing Level 4+ Topics**
- Check prompt includes Level 4+ emphasis
- Review AI output in reports
- Verify PDF has nested content (bullet points, etc.)

### **Database Upload Issues**
- Check Supabase credentials in `.env`
- Verify staging tables exist
- Check for duplicate topic codes

---

## 📚 Related Documentation

- **`EDUQAS-GCSE-UNIVERSAL-SCRAPER-README.md`** - Detailed usage guide
- **`EDUQAS-PDF-URL-SCRAPER-README.md`** - PDF URL finder docs
- **`reports/summary-*.json`** - Batch run summaries
- **`reports/{Subject}-report.json`** - Individual subject reports

---

## ✅ Checklist for A-Level Adaptation

- [ ] Copy `eduqas-gcse-universal-scraper.py` → `eduqas-alevel-universal-scraper.py`
- [ ] Update subject loading to filter A-Level subjects
- [ ] Update PDF URL patterns for A-Level
- [ ] Test on 1-2 A-Level subjects
- [ ] Verify Level 4+ extraction works
- [ ] Create A-Level batch files
- [ ] Update exclusion list if needed
- [ ] Test full batch run

---

## 🎯 Key Takeaways

1. **Universal scraper works** - One scraper handles all subjects
2. **Level 4+ extraction critical** - Enhanced prompts ensure depth
3. **Automatic PDF URL finding** - No manual URL collection needed
4. **Structure detection** - Handles Components, Tiers, Options automatically
5. **Self-assessment** - Quality reports help identify issues
6. **Exclusion system** - Prevents re-scraping perfect subjects
7. **Ready for A-Level** - Same approach should work with minor adjustments

---

**Last Updated:** November 23, 2025  
**Status:** ✅ Production Ready  
**Next Steps:** Adapt for A-Level subjects





















