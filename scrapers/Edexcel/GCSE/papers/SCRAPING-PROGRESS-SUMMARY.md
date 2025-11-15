# Edexcel GCSE Exam Papers - Scraping Progress Summary

**Date**: 15 November 2025  
**Status**: 🔄 IN PROGRESS

---

## ✅ Completed Tasks

### 1. Universal Scraper Updates

**Fixed & Added:**
- ✅ **History Code Fixed**: Changed from `1hi0` to `1hia` (papers use this code)
- ✅ **History Parser**: Added special pattern for `1hia-p{X}-que-...` format
- ✅ **Biology Added**: Code `1bi0` (Foundation/Higher)
- ✅ **Chemistry Added**: Code `1ch0` (Foundation/Higher)
- ✅ **Physics Added**: Code `1ph0` (Foundation/Higher)
- ✅ **Geography A Added**: Code `1ga0`
- ✅ **Geography B Added**: Code `1gb0`
- ✅ **Religious Studies A Short**: Code `3ra0` (short course variant)
- ✅ **Religious Studies B Short**: Code `3rb0` (short course variant)
- ✅ **RS Parser**: Added pattern for paper options (e.g., `1ra0-3c-que-...`)
- ✅ **Unicode Fix**: Removed emoji characters causing Windows encoding errors

### 2. Test Results

**History Test (Successful):**
- ✅ Found 337 PDF links on Pearson website
- ✅ Parsed 58 History papers successfully
- ✅ Grouped into 27 complete paper sets
- ✅ **Uploaded to database**: 27 paper sets
  - 2022: 21 papers (19 with marks, 20 with reports)
  - 2021: 6 papers (0 with marks, 0 with reports)

---

## 🔄 Currently Running

### Batch Scraper for All 18 Subjects

**Command**: `python run-missing-papers-batch.py`  
**Start Time**: ~10:51 AM  
**Estimated Duration**: 30-60 minutes  
**Output Log**: `batch-scraping-log.txt`

**Subjects Being Scraped:**

| # | Subject Code | Subject Name | Expected Papers |
|---|--------------|--------------|-----------------|
| 1 | `GCSE-Biology` | Biology | ~50+ (F/H tiers) |
| 2 | `GCSE-Chemistry` | Chemistry | ~50+ (F/H tiers) |
| 3 | `GCSE-Physics` | Physics | ~50+ (F/H tiers) |
| 4 | `GCSE-Science` | Combined Science | ~100+ (3 subjects × tiers) |
| 5 | `GCSE-DesignTech` | Design & Technology | ~30+ |
| 6 | `GCSE-EnglishLang` | English Language | ~30+ |
| 7 | `GCSE-EnglishLit` | English Literature | ~30+ |
| 8 | `GCSE-GeographyA` | Geography A | ~30+ |
| 9 | `GCSE-GeographyB` | Geography B | ~30+ |
| 10 | `GCSE-History` | History | 27 (already done ✓) |
| 11 | `GCSE-Mathematics` | Mathematics | ~60+ (F/H tiers, 3 papers) |
| 12 | `GCSE-Music` | Music | ~20+ |
| 13 | `GCSE-PE` | Physical Education | ~30+ |
| 14 | `GCSE-Statistics` | Statistics | ~20+ |
| 15 | `GCSE-ReligiousStudiesA` | Religious Studies A | ~30+ |
| 16 | `GCSE-ReligiousStudiesA-Short` | RS A (Short Course) | ~20+ |
| 17 | `GCSE-ReligiousStudiesB` | Religious Studies B | ~30+ |
| 18 | `GCSE-ReligiousStudiesB-Short` | RS B (Short Course) | ~20+ |

**Expected Total**: ~600-800+ paper sets across all subjects

---

## 📊 What's Being Collected

For each subject, the scraper will:

1. **Navigate** to Pearson exam materials page
2. **Expand** all sections and load all PDFs (via scrolling)
3. **Extract** PDF links (Question Papers, Mark Schemes, Examiner Reports)
4. **Parse** filenames to identify:
   - Year and exam series (June/November)
   - Paper number
   - Tier (Foundation/Higher where applicable)
   - Component code (for History options, RS options, etc.)
   - Document type
5. **Group** into complete paper sets (QP + MS + ER)
6. **Upload** to database table `staging_aqa_exam_papers`

---

## 🎯 Special Handling

### Combined Science (`1sc0`)
- Format: `1sc0-{paper}{subject}{tier}-{type}-{date}`
- Example: `1sc0-2bh-que-20220616.pdf`
  - Paper 2, Biology, Higher
- Will create separate entries for each Biology/Chemistry/Physics paper

### History (`1hia`)
- Format: `1hia-p{X}-{type}-{date}`
- Example: `1hia-p5-que-20220622.pdf`
  - Paper 5 (specific historical option)
- Multiple paper options (p1-p9+) for different themes/periods

### Religious Studies (`1ra0`, `3ra0`, `1rb0`, `3rb0`)
- Format: `{code}-{paper}{option}-{type}-{date}`
- Example: `1ra0-3c-que-20220609.pdf`
  - Paper 3, Option C
- Separate full course (1-prefix) and short course (3-prefix) variants

### Mathematics (`1ma1`)
- Foundation and Higher tiers
- 3 papers per tier (Paper 1, 2, 3)
- ~60 total paper sets expected

---

## 📁 Database Structure

Papers are uploaded to: `staging_aqa_exam_papers`

**Fields:**
```sql
- subject_id (UUID) - Links to staging_aqa_subjects
- year (INTEGER) - e.g., 2022
- exam_series (TEXT) - 'June' or 'November'
- paper_number (INTEGER) - 1, 2, 3, etc.
- tier (TEXT) - 'F', 'H', or NULL
- component_code (TEXT) - e.g., '3C', '2BH', 'P5'
- question_paper_url (TEXT)
- mark_scheme_url (TEXT)
- examiner_report_url (TEXT)
- exam_board (TEXT) - 'Edexcel'
```

---

## 🔍 Monitoring Progress

To check progress:

```bash
# View live log
tail -f batch-scraping-log.txt

# Count uploaded papers
tail -100 batch-scraping-log.txt | grep "Uploaded"

# Check for errors
grep -i error batch-scraping-log.txt
```

---

## ⏳ Next Steps

1. ⏳ **Wait for batch completion** (~30-60 minutes)
2. 📊 **Verify uploads** in database
3. 📝 **Generate summary report** with counts by subject
4. 🔧 **Fix any issues** (missing subjects, failed uploads)
5. ✅ **Commit and push** all changes to GitHub

---

## 🐛 Known Issues & Notes

### Handled
- ✅ Windows Unicode encoding (emojis removed)
- ✅ History code mismatch fixed
- ✅ Religious Studies short course codes added

### Potential Issues
- ⚠️ Some subjects may not be in database yet (Geography A/B, Maths, RS)
  - Scraper will skip these with warning
  - Need to upload topics first
- ⚠️ Combined Science may have many papers (3 sciences × 2 tiers × 2 papers × years)
- ⚠️ History has many optional papers (different historical periods)

---

## 📈 Success Metrics

**Target**: Get as many papers as possible (user request: "don't limit the numbers")

**Expected Results:**
- Minimum: 400+ paper sets
- Target: 600-800+ paper sets
- Ideal: 1000+ paper sets (if older years available)

**Quality Checks:**
- Each set should have Question Paper (mandatory)
- Most sets should have Mark Scheme
- Most sets should have Examiner Report
- Papers should span multiple years (2018-2024)

---

*Last Updated: 15 Nov 2025, 10:52 AM*

