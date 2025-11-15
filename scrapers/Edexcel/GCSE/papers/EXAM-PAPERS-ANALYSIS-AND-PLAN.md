# Edexcel GCSE Exam Papers - Analysis & Action Plan

## Current Status

### Subjects Missing Papers

Based on database check (15 Nov 2025):

| Subject | Subject Code | Status | Papers | Issue |
|---------|--------------|--------|--------|-------|
| Biology | `1bi0` | ❌ | 0 | Subject exists, no papers |
| Chemistry | `1ch0` | ❌ | 0 | Subject exists, no papers |
| Combined Science | `1sc0` | ❌ | 0 | Subject exists, no papers |
| Design & Technology | `1dt0` | ❌ | 0 | Subject exists, no papers |
| English Language | `1en0` | ❌ | 0 | Subject exists, no papers |
| English Literature | `1et0` | ❌ | 0 | Subject exists, no papers |
| Geography A | `1ga0` | ⚠️ | N/A | **Subject not in database** |
| Geography B | `1gb0` | ⚠️ | N/A | **Subject not in database** |
| History | `1hi0` | ❌ | 0 | **Wrong code!** Uses `1hia` for papers |
| Mathematics | `1ma1` | ⚠️ | N/A | **Subject not in database** |
| Music | `1mu0` | ❌ | 0 | Subject exists, no papers |
| Physical Education | `1pe0` | ❌ | 0 | Subject exists, no papers |
| Physics | `1ph0` | ❌ | 0 | Subject exists, no papers |
| Religious Studies A | `1ra0` | ⚠️ | N/A | **Subject not in database** |
| Religious Studies B | `1rb0` | ⚠️ | N/A | **Subject not in database** |
| Statistics | `1st0` | ❌ | 0 | Subject exists, no papers |

---

## Key Complexities Identified

### 1. ⚠️ **CRITICAL: History Subject Code Mismatch**

**Example URL**: `https://qualifications.pearson.com/content/dam/pdf/GCSE/History/2016/exam-materials/1hia-p5-que-20220622.pdf`

- **Topic scraper uses**: `1hi0` 
- **Exam papers use**: `1hia` (with Paper variants: `1hia`, `1hib`, `1hic`)
- **Impact**: Universal scraper won't match History papers
- **Solution**: Update History subject code OR handle code variations in parser

### 2. 🎯 **History Has Multiple Paper Variants**

History papers come in different routes/options:
- **Paper format**: `1hia-pX-que-YYYYMMDD.pdf` where X = paper number (1-9+)
- **Multiple options**: Different historical periods/themes (e.g., p5 = specific option)
- **User note**: "History should have lots of papers from different combinations"

**Example papers:**
- `1hia-p1-que-20220622.pdf` (Paper 1)
- `1hia-p5-que-20220622.pdf` (Paper 5 - specific historical theme)
- `1hia-p9-que-20220622.pdf` (Paper 9 - another option)

### 3. 📚 **Combined Science Multi-Subject Format**

Combined Science (`1sc0`) has special naming: `1sc0-2bh-que-20220616.pdf`

**Format breakdown**:
- `1sc0` = Combined Science code
- `2` = Paper number
- `b` = Subject (b=Biology, c=Chemistry, p=Physics)
- `h` = Tier (f=Foundation, h=Higher)

**Good news**: Universal scraper **already handles** this (Pattern 0, line 303)!

### 4. 🎓 **Tiered Subjects**

Subjects with Foundation/Higher tiers:
- Mathematics (`1ma1`) - F/H
- Combined Science (`1sc0`) - F/H per science

Non-tiered subjects:
- Biology, Chemistry, Physics (separate subjects)
- English Language, English Literature
- History, Geography A/B
- Religious Studies A/B

### 5. 📄 **Document Types**

Each paper set typically has 3 documents:
- **Question Paper** (`que` or `qp`)
- **Mark Scheme** (`rms`, `ms`, `msc`)
- **Examiner Report** (`pef`, `er`)

### 6. 🗂️ **Missing Subjects from Topics Upload**

These need topics uploaded first:
- Geography A (`1ga0`)
- Geography B (`1gb0`)
- Mathematics (`1ma1`)
- Religious Studies A (`1ra0`)
- Religious Studies B (`1rb0`)

---

## Proposed Solution

### Option A: Run Universal Scraper with Fixes (RECOMMENDED)

**Advantages:**
- Already built and tested
- Handles most complexity (tiering, Combined Science, grouping)
- Can process all subjects in one run

**Required fixes:**
1. Fix History code mismatch (`1hi0` → `1hia`)
2. Handle History's multiple paper variants (p1-p9+)
3. Add support for codes like Geography, Maths, RS (if URLs exist)

### Option B: Create Specialized Scrapers per Subject

**Advantages:**
- Fine-grained control per subject
- Easier debugging

**Disadvantages:**
- 16 separate scripts to maintain
- Repetitive code
- Time-consuming

---

## Recommended Action Plan

### Phase 1: Quick Wins (Subjects Already in Database)

**Use Universal Scraper with fixes:**

```bash
# 1. Fix History code in universal-gcse-paper-scraper.py
# 2. Run for subjects already in database:

python universal-gcse-paper-scraper.py \
  GCSE-Biology \
  GCSE-Chemistry \
  GCSE-Science \
  GCSE-DesignTech \
  GCSE-EnglishLang \
  GCSE-EnglishLit \
  GCSE-Music \
  GCSE-PE \
  GCSE-Physics \
  GCSE-Statistics
```

### Phase 2: Fix & Upload Missing Subjects

**Step 1**: Upload topics for missing subjects (or verify codes are correct)
```bash
# Need to check if these subjects exist on Pearson with correct codes
- Geography A (1ga0)
- Geography B (1gb0)
- Mathematics (1ma1)
- Religious Studies A (1ra0)
- Religious Studies B (1rb0)
```

**Step 2**: Add to universal scraper and run

### Phase 3: Handle History Specially

**Option 1**: Update subject code to `GCSE-History-A` with code `1hia`
**Option 2**: Add code variation handling in parser

---

## URL Patterns Summary

### Standard Pattern
```
{code}-{paper}[-{tier}]-{doctype}-{YYYYMMDD}.pdf

Examples:
- 1bs0-01-que-20240516.pdf (Business Paper 1)
- 1ma1-1f-que-20230516.pdf (Maths Paper 1 Foundation)
- 1en0-02-ms-20240520.pdf (English Lang Paper 2 Mark Scheme)
```

### History Pattern
```
1hia-p{X}-{doctype}-{YYYYMMDD}.pdf

Examples:
- 1hia-p1-que-20220622.pdf
- 1hia-p5-que-20220622.pdf
- 1hia-p9-ms-20220622.pdf
```

### Combined Science Pattern
```
1sc0-{paper}{subject}{tier}-{doctype}-{YYYYMMDD}.pdf

Examples:
- 1sc0-1bf-que-20220616.pdf (Paper 1, Biology, Foundation)
- 1sc0-2ch-ms-20220616.pdf (Paper 2, Chemistry, Higher)
```

---

## Questions for User

1. **Do you want the URLs for each subject's Pearson page?**
   - Most are already in `universal-gcse-paper-scraper.py`
   - But need to verify Geography A/B, Maths, RS A/B codes

2. **How should we handle History?**
   - Option A: Change subject code from `GCSE-History` to `GCSE-History-A` (code `1hia`)
   - Option B: Keep current and add paper code mapping in scraper
   - Option C: Check if there's also a `1hib`, `1hic` for different History routes

3. **Priority order?**
   - Should we focus on getting all subjects working, or prioritize specific ones?

4. **Batch vs Individual?**
   - Run all 16 subjects in one go (`--all`)?
   - Or process individually for better error handling?

---

## Next Steps

**RECOMMENDED IMMEDIATE ACTION:**

1. ✅ Fix History code issue in `universal-gcse-paper-scraper.py`
2. ✅ Update History pattern parser to handle `p{X}` format
3. ✅ Verify Geography, Maths, RS subject codes/URLs
4. ✅ Run scraper for 10 subjects already in database
5. ✅ Upload missing subject topics
6. ✅ Run scraper for remaining subjects

**Estimated time**: 2-3 hours for all subjects (including debugging)

---

## File References

- **Universal Scraper**: `scrapers/Edexcel/GCSE/papers/universal-gcse-paper-scraper.py`
- **Upload Helper**: `upload_papers_to_staging.py` 
- **Database Table**: `staging_aqa_exam_papers`
- **Subject Table**: `staging_aqa_subjects`

