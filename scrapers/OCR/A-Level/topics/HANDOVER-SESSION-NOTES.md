# OCR A-Level & GCSE Scrapers - Session Handover Document

**Date**: Updated December 2025 (Latest: Classical Greek, Drama, Economics specialized scrapers)  
**User**: Tony D  
**Project**: Flash Curriculum Pipeline - OCR A-Level & GCSE Scrapers

---

## 🎯 SESSION SUMMARY

Successfully created and debugged **12+ OCR A-Level scrapers** for mathematics, sciences, and social sciences. Major debugging sessions to fix API connection issues, model configurations, and complex hierarchical structures.

**NEW**: Created **Universal GCSE Scraper** that can process ALL OCR GCSE courses with smart two-phase analysis and self-assessment reporting.

**LATEST (December 2025)**: Fixed **Biology A scraper** (now extracting hundreds of topics with proper depth), fixed **Art subjects scraper** (subject-specific filtering, duplicate prevention), and created **Chemistry A** and **Physics A scrapers** based on the Biology A structure.

**LATEST (December 2025 - Universal GCSE Scraper)**: Fixed multiple issues with Universal GCSE Scraper:
- Fixed Business (J204): Filtered out "Components" and "Content" section markers
- Fixed Computer Science (J277): Added Level 4 extraction emphasis
- Fixed Classical Civilisation (J199): Added assessment filtering, Prescribed Sources extraction, Level 4 depth
- Fixed Citizenship Studies (J270): Added section marker filtering ("Components", "Content Overview", "Assessment Overview", "Sections within Components")

**LATEST (December 2025 - Specialized GCSE Scrapers)**: Created specialized scrapers for complex subjects:
- Classical Greek (J292): Fixed Level 0 structure, integrated appendices, filtered assessment sections
- Drama (J316): Component 04 only, 3-column table extraction, proper depth
- Economics (J205): Components as Level 0, "Learners should be able to" extraction, markdown handling

---

## ✅ COMPLETED SCRAPERS

### Mathematics Scrapers (All Working ✅)

1. **Mathematics A (H240)** - `ocr-maths-a-manual.py`
   - Structure: 4 levels (Categories → Topics → Subject Content → OCR Ref items)
   - Categories: Pure Mathematics, Statistics, Mechanics
   - Content starts: Page 20
   - Status: ✅ **Working perfectly** - extracted 130+ topics

2. **Further Mathematics A (H245)** - `ocr-further-maths-a-manual.py`
   - Structure: 4 levels (Mandatory/Optional → Subject areas → Topics → OCR Ref items)
   - Numbering starts at 4 (4.01a, 4.02a, etc.)
   - Content starts: Page 15, tables page 17
   - Status: ✅ **Working perfectly** - extracted 348 topics

3. **Mathematics B (MEI) (H640)** - `ocr-maths-b-mei-manual.py`
   - Structure: 5 levels (Areas → Topics → Subsections (a)(b) → Spec items → Ref codes)
   - 3 Areas: Pure, Mechanics, Statistics
   - Ref codes: Mp1, p2, Ma1, Ma2, a3, a4, etc.
   - Status: ✅ **Created, ready to test**

4. **Further Mathematics B (MEI) (H645)** - `ocr-further-maths-b-mei-manual.py`
   - Structure: 5 levels (9 papers including Core pure Y420, majors, minors)
   - Similar to H640 with (a)(b) subsections
   - Status: ✅ **Created, ready to test**

### Other Subjects

5. **Physical Education (H555)** - `ocr-pe-manual.py`
   - Status: ✅ **Fixed and working** - extracted 742 topics (404 + 181 + 157)

6. **Media Studies (H409)** - `ocr-media-studies-manual.py`
   - Extracts subject content framework (theories, contexts, etc.)
   - Status: ✅ **Created, ready to test**

7. **Music (H543)** - `ocr-music-manual.py`
   - Structure: Core Content + 6 Areas of Study + Listening/appraising
   - Prescribed Works for Areas 1-2 (by year: 2025-2030)
   - Suggested Repertoire for Areas 3-6 (List A/B)
   - Status: ✅ **Created, ready to test**

8. **Physics B (Advancing Physics) (H557)** - `ocr-physics-b-manual.py`
   - Structure: 5 levels (Modules → Topics → Child topics → Learning outcomes → Lettered items)
   - 6 Modules with hierarchical topics
   - **Key fix**: Filters out "Learning outcomes" as a topic (it's just a section marker)
   - Adjusts child levels when "Learning outcomes" is skipped
   - Status: ✅ **Working** - extracted topics successfully

9. **Psychology (H567)** - `ocr-psychology-manual.py`
   - Structure: 3 components with different structures
   - Component 01: Research methods (4-5 levels)
   - Component 02: Core Studies table + Sections B & C
   - Component 03: Applied psychology (table-based, 5 levels)
   - **Key fixes**: 
     - Component 03 structure fixed (one Level 0, sections as Level 1)
     - Markdown handling in parser (handles bullets, bold markers)
     - Duplicate detection before database insert
     - Filters "Learners should..." headings
   - Status: ✅ **Working** - extracted 369 topics

10. **Psychology (2026+) (H569)** - `ocr-psychology-2026-manual.py`
    - Structure: Similar to H567 but adapted for new specification
    - Component 1: Research methods (6 topics instead of 4)
    - Component 2: Core studies in psychology (similar structure)
    - Component 3: Applied psychology (2 compulsory + 3 optional sections)
    - **Key differences**: Uses "3.1", "3.2", "3.3" section numbering in PDF
    - Status: ✅ **Working** - Component 3 extracted 150 topics, Components 1 & 2 need section finding fixes

11. **Religious Studies (H573)** - `ocr-religious-studies-manual.py`
    - Structure: 7 components (01-02, 03-07 for different religions)
    - Component 01: Philosophy of religion
    - Component 02: Religion and ethics
    - Components 03-07: Developments in religious thought (Christianity, Islam, Judaism, Buddhism, Hinduism)
    - **Key features**: 
      - 3-column tables (Topic, Content, Key Knowledge)
      - Contextual References extracted as L2 children of L1 topics
      - Key Knowledge matched to Content parents
    - Status: ✅ **Created, ready to test**

12. **Sociology (H580)** - `ocr-sociology-manual.py`
    - Structure: 3 components
    - Component 01: Socialisation, culture and identity (Section A + Section B options)
    - Component 02: Researching and understanding social inequalities
    - Component 03: Debates in contemporary society (Section A compulsory + Section B options)
    - **Key features**:
      - 3-column tables (Key questions, Content, Learners should)
      - "Learners should:" items matched to Content parents
      - Topics can span multiple pages (handles "cont." indicators)
    - Status: ✅ **Created, ready to test**

---

## 🔧 CRITICAL CONFIGURATION THAT WORKS

After extensive debugging, found the **winning configuration**:

```python
# AI Provider Setup
AI_PROVIDER = None
if openai_key:
    from openai import OpenAI
    openai_client = OpenAI(api_key=openai_key)
    AI_PROVIDER = "openai"
    
if not AI_PROVIDER and anthropic_key:
    import anthropic
    claude = anthropic.Anthropic(api_key=anthropic_key)
    AI_PROVIDER = "anthropic"

# API Call Settings
if AI_PROVIDER == "openai":
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=16000,
        temperature=0,
        timeout=240  # 4 minutes
    )
else:  # anthropic
    response = claude.messages.create(
        model="claude-3-5-haiku-20241022",  # NOT sonnet!
        max_tokens=8192,  # Haiku max is 8192
        messages=[{"role": "user", "content": prompt}],
        timeout=240
    )

# Content Size
content_text[:80000]  # For large specs like Maths A
content_text[:120000]  # For very large specs like Further Maths
content_text[:150000]  # For Music (needs sections 5c and 5d)

# Retry Logic
max_retries = 3
wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
```

---

## ⚠️ CRITICAL LESSONS LEARNED

### API Connection Issues
- **OpenAI** was having intermittent "Connection error" issues with large prompts
- Simple test (`test-openai.py`) worked fine, but large scraper prompts timed out
- **Solution**: Reduced content size from 60k → 80k chars, increased timeout to 240s

### Model Configuration Issues Encountered
- ❌ `claude-3-5-sonnet-20241022` - Returns 404 (doesn't exist)
- ❌ `claude-3-5-sonnet-20240620` - Returns 404 (doesn't exist)
- ✅ `claude-3-5-haiku-20241022` - **WORKS** (max_tokens: 8192)
- ✅ `gpt-4o` - **WORKS** (max_tokens: 16000)

### Content Size vs Extraction Quality
- Too small (25k): AI stops partway and asks "Would you like me to continue?"
- Too large (60k+): Connection timeouts
- **Sweet spot**: 80-120k chars depending on spec size

### Prompt Engineering
- MUST include: "Do NOT ask for confirmation. Do NOT ask questions. Extract EVERYTHING NOW."
- Otherwise AI asks permission instead of extracting

### Database Management
- **Changed approach**: Clear old topics AFTER successful extraction (not before)
- Prevents data loss if scraper fails
- PE scraper previously deleted all topics then crashed, losing data
- **Duplicate detection**: Added duplicate code removal before database insert
- Prevents unique constraint violations when same topic appears multiple times

### Markdown Handling
- AI sometimes returns markdown formatting (bullets, bold markers)
- **Solution**: Parser handles multiple formats:
  - Plain numbered: "1.1 Title"
  - Markdown bold: "**1.1 Title**"
  - Bullets: "- 1.1.1 Title" or "  - 1.1.1 Title"
- Clean titles by stripping markdown markers

### Section Marker Filtering
- Some PDFs have section markers that aren't actual topics
- **Examples**: "Learning outcomes", "Learners should...", "Content"
- **Solution**: Filter these out in `_parse_hierarchy()` with excluded headers list
- Adjust child levels when parent is filtered (e.g., Physics B "Learning outcomes")

### Component Structure Fixes
- **Psychology H567 Component 03**: Was creating multiple Level 0 entries
- **Fix**: Create Level 0 once, extract sections starting from Level 1, adjust levels
- **Psychology H569**: Uses "3.1", "3.2", "3.3" format instead of "Component 1/2/3"
- **Fix**: Added section number patterns to `_find_section()`

---

## 📋 CURRENT STATUS

### Working Scrapers ✅
1. Mathematics A (H240) - 130+ topics
2. Further Mathematics A (H245) - 348 topics
3. Physical Education (H555) - 742 topics
4. Physics B (Advancing Physics) (H557) - Working
5. Psychology (H567) - 369 topics
6. Psychology (2026+) (H569) - Component 3 working (150 topics), Components 1 & 2 need fixes

### Ready to Test
1. Mathematics B (MEI) H640
2. Further Mathematics B (MEI) H645  
3. Media Studies H409
4. Music H543

### Files Created/Updated This Session

**A-Level Scrapers:**
```
ocr-maths-a-manual.py              (rewritten from scratch)
ocr-further-maths-a-manual.py      (new)
ocr-maths-b-mei-manual.py          (new)
ocr-further-maths-b-mei-manual.py  (new)
ocr-media-studies-manual.py        (new)
ocr-music-manual.py                (new)
ocr-pe-manual.py                   (fixed timeout/content size)
ocr-physics-b-manual.py            (new - with Learning outcomes filtering)
ocr-psychology-manual.py           (new - with Component 03 fix)
ocr-psychology-2026-manual.py      (new - adapted from H567)
ocr-religious-studies-manual.py    (new)
ocr-sociology-manual.py            (new)
test-openai.py                     (diagnostic tool)

TEST-MATHS-A.bat
TEST-FURTHER-MATHS-A.bat
TEST-MATHS-B-MEI.bat
TEST-FURTHER-MATHS-B-MEI.bat
TEST-MEDIA-STUDIES.bat
TEST-MUSIC.bat
TEST-PHYSICS-B.bat
TEST-PSYCHOLOGY.bat
TEST-PSYCHOLOGY-2026.bat
TEST-RELIGIOUS-STUDIES.bat
TEST-SOCIOLOGY.bat
```

**GCSE Universal Scraper:**
```
scrapers/OCR/GCSE/topics/ocr-gcse-universal-scraper.py  (new - universal scraper)
scrapers/OCR/GCSE/topics/TEST-GCSE-UNIVERSAL.bat        (test script)
scrapers/OCR/GCSE/topics/RUN-FULL-GCSE-BATCH.bat        (full batch script)
scrapers/OCR/GCSE/topics/GCSE-UNIVERSAL-SCRAPER-PLAN.md (design docs)
scrapers/OCR/A-Level/topics/OCR GCSE.md                 (subject list - updated)
```

**GCSE Gateway Science Scrapers (Fixed/Created December 2025):**
```
scrapers/OCR/GCSE/topics/ocr-biology-a-manual.py        (fixed - now working perfectly)
scrapers/OCR/GCSE/topics/ocr-chemistry-a-manual.py      (new - based on Biology A)
scrapers/OCR/GCSE/topics/ocr-physics-a-manual.py        (new - based on Biology A)
scrapers/OCR/GCSE/topics/ocr-art-subjects-manual.py     (fixed - subject-specific filtering)
scrapers/OCR/GCSE/topics/TEST-BIOLOGY-A.bat             (test script)
scrapers/OCR/GCSE/topics/TEST-CHEMISTRY-A.bat           (test script)
scrapers/OCR/GCSE/topics/TEST-PHYSICS-A.bat             (test script)
scrapers/OCR/GCSE/topics/TEST-ART-MANUAL.bat            (test script)
scrapers/OCR/GCSE/topics/RUN-ALL-ART-SUBJECTS.bat      (batch script for all Art subjects)
```

**GCSE Specialized Scrapers (Created December 2025):**
```
scrapers/OCR/GCSE/topics/ocr-classical-greek-manual.py  (new - 3 Level 0s, appendix integration)
scrapers/OCR/GCSE/topics/ocr-drama-manual.py            (new - Component 04 only, table extraction)
scrapers/OCR/GCSE/topics/ocr-economics-manual.py        (new - components as Level 0, markdown handling)
scrapers/OCR/GCSE/topics/TEST-CLASSICAL-GREEK.bat       (test script)
scrapers/OCR/GCSE/topics/TEST-DRAMA.bat                 (test script)
scrapers/OCR/GCSE/topics/TEST-ECONOMICS.bat             (test script)
```

---

## 🚀 NEXT STEPS

1. **Test new Gateway Science scrapers**:
   - `.\TEST-CHEMISTRY-A.bat` - Verify Chemistry A extraction
   - `.\TEST-PHYSICS-A.bat` - Verify Physics A extraction
   - Both should extract hundreds of topics with proper depth (Level 2-4)

2. **Test Art subjects scraper**:
   - `.\RUN-ALL-ART-SUBJECTS.bat` - Process all 7 Art subjects
   - Verify each subject extracts only its own content
   - Check for no duplicates

3. **Fix Psychology H569 Components 1 & 2** (if still needed):
   - Section finding needs to handle "3.1 Research methods (H569/01)" format
   - May need to look for actual content section after TOC entry
   - Check debug output to see what patterns match

4. **Test remaining A-Level scrapers**:
   - `.\TEST-MATHS-B-MEI.bat`
   - `.\TEST-FURTHER-MATHS-B-MEI.bat`
   - `.\TEST-MEDIA-STUDIES.bat`
   - `.\TEST-MUSIC.bat`

5. **Verify all extractions** look correct in the database

6. **Commit and push to GitHub** (user prefers this workflow)
   ```bash
   git add scrapers/OCR/GCSE/topics/ocr-biology-a-manual.py
   git add scrapers/OCR/GCSE/topics/ocr-chemistry-a-manual.py
   git add scrapers/OCR/GCSE/topics/ocr-physics-a-manual.py
   git add scrapers/OCR/GCSE/topics/ocr-art-subjects-manual.py
   git add scrapers/OCR/GCSE/topics/TEST-*.bat
   git add scrapers/OCR/GCSE/topics/RUN-ALL-ART-SUBJECTS.bat
   git commit -m "Fix Biology A scraper (proper depth extraction); Create Chemistry A and Physics A scrapers; Fix Art subjects scraper (subject-specific filtering, duplicate prevention)"
   git push
   ```

---

## 📊 EXTRACTION STATISTICS

| Subject | Code | Topics Extracted | Status |
|---------|------|------------------|--------|
| Mathematics A | H240 | 130+ | ✅ Working |
| Further Maths A | H245 | 348 | ✅ Working |
| Maths B (MEI) | H640 | TBD | Ready to test |
| Further Maths B (MEI) | H645 | TBD | Ready to test |
| Physical Education | H555 | 742 | ✅ Working |
| Media Studies | H409 | TBD | Ready to test |
| Music | H543 | TBD | Ready to test |
| Physics B (Advancing Physics) | H557 | TBD | ✅ Working |
| Psychology | H567 | 369 | ✅ Working |
| Psychology (2026+) | H569 | 150 (Component 3 only) | 🔄 Components 1 & 2 need fixes |

---

## 🔍 DEBUGGING TIPS

### If Scraper Fails

1. **Check debug output**: `scrapers/OCR/A-Level/debug-output/[CODE]-ai-output.txt`
2. **Check PDF snippet**: `scrapers/OCR/A-Level/debug-output/[CODE]-pdf-snippet.txt`
3. **Common issues**:
   - AI asking for permission → Strengthen prompt with "Extract EVERYTHING NOW"
   - Connection error → Reduce content size or increase timeout
   - Wrong model → Check model name matches available models
   - No topics extracted → Check AI output format matches regex in `_parse_hierarchy()`
   - Section not found → Check `_find_section()` patterns match PDF format (may use "3.1" instead of "Component 1")
   - Duplicate key error → Add duplicate detection before database insert
   - Markdown in output → Parser handles it, but strengthen prompt to forbid markdown

### If AI Stops Partway

Look for in AI output:
- "Would you like me to continue?"
- "(Continued with the rest...)"
- Stopping at low topic counts

**Solution**: Increase `max_tokens` or reduce `content_text` size to fit more in output

---

## 📁 FILE LOCATIONS

- **A-Level Scrapers**: `C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\scrapers\OCR\A-Level\topics\`
- **GCSE Universal Scraper**: `C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\scrapers\OCR\GCSE\topics\`
- **Debug output**: `scrapers\OCR\A-Level\debug-output\`
- **GCSE Reports**: `scrapers\OCR\GCSE\topics\reports\`
- **Subject List**: `scrapers\OCR\A-Level\topics\OCR GCSE.md`
- **Environment**: `C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env`

---

## 🗝️ KEY INSIGHTS

### OCR Specification Patterns

1. **Table-based specs** (Maths, PE, Law, Geography):
   - Structured tables with ref codes
   - Clear hierarchical levels
   - Easy to extract

2. **Narrative specs** (Media Studies):
   - Descriptive content
   - Flexible student choices
   - Subject content framework separate from assessment content

3. **Hybrid specs** (Music):
   - Focus for learning (bold text + bullets)
   - Prescribed works organized differently per area
   - Areas 1-2: By year (2025-2030)
   - Areas 3-6: By List A/B

4. **Multi-component specs** (Psychology):
   - Different components have different structures
   - Component 03 often has multiple sections (compulsory + optional)
   - Need to create Level 0 once, then extract sections as Level 1
   - Some PDFs use section numbers (3.1, 3.2, 3.3) instead of "Component 1/2/3"

### User Preferences
- Always offer to commit and push to GitHub
- Keep trying until it works - user has patience for complex tasks
- Prefers working code over explanations

---

## 💡 REMEMBER

- **Test simple requests first** (`test-openai.py`) to isolate issues
- **Match working scrapers** - if one works, copy its config exactly
- **Don't delete data before scraping** - only clear after successful extraction
- **User is experienced** - trust their specifications and structure descriptions
- **OpenAI preferred** but Anthropic as backup for connection issues
- **Filter section markers** - "Learning outcomes", "Learners should..." are NOT topics
- **Handle markdown** - AI sometimes returns markdown, parser handles it but forbid in prompts
- **Component structure** - If multiple sections under one component, create Level 0 once, sections as Level 1
- **Section finding** - PDFs may use "3.1 Title" format instead of "Component 1: Title"
- **Duplicate detection** - Always check for duplicate codes before database insert

---

## 🔧 RECENT FIXES & IMPROVEMENTS

### Physics B (H557)
- Added filtering for "Learning outcomes" section marker
- Adjusts child levels when parent is filtered out
- Maintains correct parent-child relationships

### Psychology (H567)
- Fixed Component 03 structure (one Level 0, sections as Level 1)
- Added markdown handling in parser
- Added duplicate detection before database insert
- Filters "Learners should..." headings

### Psychology (2026+) (H569)
- Adapted from H567 for new specification
- Component 1 has 6 topics (vs 4 in H567)
- Component 3 has 2 compulsory + 3 optional sections
- Section finding needs improvement for "3.1", "3.2", "3.3" format

---

## 🎓 GCSE UNIVERSAL SCRAPER (NEW)

### Overview
Created a smart, universal scraper (`ocr-gcse-universal-scraper.py`) that can process ALL OCR GCSE courses with a two-phase approach: **Analyze → Extract → Assess**.

### Key Features

1. **Three-Phase Process**:
   - **Phase 1: Analysis** - Understands PDF structure before extraction
   - **Phase 2: Extraction** - Builds hierarchy based on analysis
   - **Phase 3: Self-Assessment** - Generates quality report with grade (%)

2. **Smart Handling**:
   - **Tiers**: Creates separate Level 0 for Foundation/Higher (e.g., Combined Science)
   - **Options**: Extracts ALL optional units/components
   - **Texts**: Handles prescribed texts (English, Drama, Art)
   - **Shared PDFs**: Groups subjects by PDF URL, scrapes once, creates multiple entries

3. **Self-Assessment Reports**:
   - Individual JSON reports per subject
   - Topic counts per level
   - Issues and warnings
   - Success grade (%)
   - Summary report with success rates

### Files Created

- `scrapers/OCR/GCSE/topics/ocr-gcse-universal-scraper.py` - Main scraper (1173 lines)
- `scrapers/OCR/GCSE/topics/TEST-GCSE-UNIVERSAL.bat` - Test script
- `scrapers/OCR/GCSE/topics/RUN-FULL-GCSE-BATCH.bat` - Full batch script
- `scrapers/OCR/GCSE/topics/GCSE-UNIVERSAL-SCRAPER-PLAN.md` - Design documentation

### Subject Configuration

**Markdown File**: `scrapers/OCR/A-Level/topics/OCR GCSE.md`

**Special Cases**:
- **Art strands (J170-J176)**: 7 separate subjects sharing 1 PDF
  - Art, Craft and Design (J170)
  - Fine Art (J171)
  - Graphic Communication (J172)
  - Photography (J173)
  - Textile Design (J174)
  - Three-Dimensional Design (J175)
  - Critical and Contextual Studies (J176)

- **Religious Studies**: 2 subjects sharing 1 PDF
  - Religious Studies (J625) - Full course
  - Religious Studies Short Course (J125)

**Excluded Subjects** (already perfect):
- J260: Science B, Combined
- J383: Geography A

### Usage

```bash
# Test one subject
.\TEST-GCSE-UNIVERSAL.bat --subject-code J170

# Test first 5 subjects
.\TEST-GCSE-UNIVERSAL.bat --limit 5

# Full batch (all subjects)
.\RUN-FULL-GCSE-BATCH.bat
```

### Output

- **Individual reports**: `scrapers/OCR/GCSE/topics/reports/JXXX-report.json`
- **Summary report**: `scrapers/OCR/GCSE/topics/reports/summary-YYYYMMDD-HHMMSS.json`
- **Debug output**: `scrapers/OCR/A-Level/debug-output/JXXX-*.txt`

### Success Examples

- **J260 (Science B, Combined)**: 324 topics extracted, 85% grade, tiers handled correctly
- **J383 (Geography A)**: Successfully extracted

### Known Patterns Handled

The scraper adapts to different PDF structures:
- Mathematics (table with ref codes)
- Sociology (Key questions, Content, Learners should)
- Religious Studies (Topic, Content, Key Knowledge)
- PE (Topic Area, Content with bullets)
- Law (Content, Guidance)
- Chapter-based (Combined Science)
- Component-based (Psychology)

### Status

✅ **Working** - Successfully tested on J260 and J383
🔄 **Running** - Full batch processing all subjects

---

---

## ✅ RECENTLY FIXED SCRAPERS (December 2025)

### Biology A (J247) - ✅ FIXED AND WORKING
**Previous Problem**: Only extracting ~8 topics with no depth. AI was refusing to extract content.

**Fixes Applied**:
1. **Fixed section finding** - Distinguishes TOC entries from actual content pages
   - TOC entries have page numbers after them
   - Actual content has "Topic B1:" followed by "B1.1" nearby
   - Verifies context before extracting
2. **Increased extraction sizes**:
   - Content section: 500k chars (was 300k)
   - Topic sections: 200k chars (was 100k)
   - Passes up to 250k chars to AI
3. **Simplified AI prompt** - Less verbose, more direct to avoid refusals
4. **Better topic detection** - Uses stored content_section, verifies sub-topics exist
5. **Improved filtering** - Filters out "Content Overview", "Assessment Overview", and other non-topic sections

**Current Status**: ✅ **WORKING PERFECTLY**
- Extracts hundreds of topics with proper depth (Level 2-4)
- Properly extracts Level 2 (sub-topics), Level 3 (learning outcomes), Level 4 ("To include" items)
- File: `scrapers/OCR/GCSE/topics/ocr-biology-a-manual.py`
- Test: `.\TEST-BIOLOGY-A.bat`

### Art Subjects (J170-J176) - ✅ FIXED AND WORKING
**Previous Problem**: Extracting all Art content instead of subject-specific content. Duplicate Level 0 topics appearing as children.

**Fixes Applied**:
1. **Subject-specific filtering** - AI prompt explicitly tells it to extract ONLY current subject's content
2. **Duplicate filtering** - Three layers:
   - AI prompt tells it not to extract Level 0 topic names as headings
   - Parser filters out any topics matching Level 0 names
   - Post-extraction filter removes duplicates before adding to list
3. **Improved section finding** - Better detection of "Areas of Study", "Skills", "Knowledge and Understanding" headings
4. **Content filtering** - Filters out other subject codes and generic OCR support content

**Current Status**: ✅ **WORKING**
- Each subject extracts only its own content
- Proper 3 Level 0 structure: Areas of Study, Skills, Knowledge and Understanding
- No duplicates
- File: `scrapers/OCR/GCSE/topics/ocr-art-subjects-manual.py`
- Test: `.\TEST-ART-MANUAL.bat` or `.\RUN-ALL-ART-SUBJECTS.bat`

### Chemistry A (J248) - ✅ CREATED
**Status**: ✅ **CREATED AND READY TO TEST**
- Based on Biology A scraper structure
- Topics: C1-C6 + C7 (practical skills)
- Same extraction logic as Biology A
- File: `scrapers/OCR/GCSE/topics/ocr-chemistry-a-manual.py`
- Test: `.\TEST-CHEMISTRY-A.bat`

### Physics A (J249) - ✅ CREATED
**Status**: ✅ **CREATED AND READY TO TEST**
- Based on Biology A scraper structure
- Topics: P1-P6 + P7 (practical skills)
- Same extraction logic as Biology A
- File: `scrapers/OCR/GCSE/topics/ocr-physics-a-manual.py`
- Test: `.\TEST-PHYSICS-A.bat`

### Ancient History (J198) - PARTIALLY WORKING
**Status**: ✅ Better than before, but had level issues
- Fixed level assignment (L3→L2, L4→L3)
- Fixed duplicate title issue
- Still needs verification that table content is being extracted properly

---

## 🔧 UNIVERSAL GCSE SCRAPER FIXES (December 2025)

### Business (J204) - ✅ FIXED
**Issues Fixed**:
1. **Section markers as topics**: "Components" and "Content" were being extracted as topics
   - **Fix**: Added filtering for exact matches of "components", "component", "content" (not "Component 01:" which are real topics)
   - Filter only exact matches to avoid filtering legitimate topics like "Component 01: Business 1"
2. **Thin scrape**: Missing Level 4 depth
   - **Fix**: Strengthened Level 4 extraction instructions in component-based structure prompt

**Current Status**: ✅ **WORKING**
- Filters out section markers correctly
- Extracts proper depth (Level 0-4)
- File: `scrapers/OCR/GCSE/topics/ocr-gcse-universal-scraper.py`
- Test: `.\TEST-GCSE-UNIVERSAL.bat --subject-code J204`

### Computer Science (J277) - ✅ FIXED
**Issues Fixed**:
1. **Missing Level 4 depth**: Only extracting up to Level 3
   - **Fix**: Strengthened component-based structure instructions to emphasize Level 4 extraction
   - Added explicit examples of Level 4 items (e.g., "The fetch-execute cycle", "ALU (Arithmetic Logic Unit)")
   - Added rule to extract ALL bullet points, sub-items, and detailed learning points as Level 4

**Current Status**: ✅ **WORKING**
- Extracts Level 4 content items from tables and bullet points
- File: `scrapers/OCR/GCSE/topics/ocr-gcse-universal-scraper.py`
- Test: `.\TEST-GCSE-UNIVERSAL.bat --subject-code J277`

### Classical Civilisation (J199) - ✅ FIXED
**Issues Fixed**:
1. **Assessment sections being extracted**: "Assessment of GCSE", "Admin: what you need to know", "Appendices" were being extracted
   - **Fix**: Added comprehensive assessment/admin filtering list
   - Filters topics that start with or equal assessment section names
2. **Missing Level 4 depth**: Only extracting up to Level 2
   - **Fix**: Strengthened Level 4 extraction with examples (e.g., splitting comma-separated lists like "Zeus, Hera, Demeter" into separate Level 4 items)
3. **Prescribed Sources not extracted**: "Prescribed Literary Sources" and "Prescribed Visual/Material Sources" sections were not being extracted with their content
   - **Fix**: Added specific instructions to extract Prescribed Sources as Level 2 topics under Content Sections
   - Extract each prescribed source as Level 3, specific sections as Level 4
   - Extract learning objectives under "When studying..." sections as Level 4

**Current Status**: ✅ **WORKING**
- Filters out assessment/admin/appendices sections
- Extracts Prescribed Sources with full content
- Extracts Level 4 depth properly
- File: `scrapers/OCR/GCSE/topics/ocr-gcse-universal-scraper.py`
- Test: `.\TEST-GCSE-UNIVERSAL.bat --subject-code J199`

### Citizenship Studies (J270) - ⚠️ NEEDS INVESTIGATION
**Issues Fixed**:
1. **Section markers as topics**: "Components", "Content Overview", "Assessment Overview", "Sections within Components" were being extracted
   - **Fix**: Added filtering for "sections within components", "sections within component", "sections within", "sections"
   - Already had filtering for "components", "content overview", "assessment overview"

**Current Status**: ⚠️ **NEEDS INVESTIGATION**
- Filtering appears to work (section markers filtered out)
- Extracts 89 topics with Level 4 depth (64 Level 4 topics)
- User reports "terrible fail" - may need to check:
  - Structure correctness (components vs sections organization)
  - Missing topics compared to specification
  - Level assignment accuracy
- File: `scrapers/OCR/GCSE/topics/ocr-gcse-universal-scraper.py`
- Test: `.\TEST-GCSE-UNIVERSAL.bat --subject-code J270`
- Debug: Check `scrapers/OCR/A-Level/debug-output/J270-ai-output.txt` and `scrapers/OCR/GCSE/topics/reports/J270-report.json`

**Key Code Changes**:
- `_parse_hierarchy()`: Added filtering for section markers and assessment sections
- `_get_structure_instructions()`: Strengthened Level 4 extraction for component-based structures
- `_build_extraction_prompt()`: Added rules for Prescribed Sources extraction and assessment filtering

---

## 🔍 KEY LESSONS LEARNED

1. **Content Section Extraction**: Must extract large chunks (200k+ chars), not small sections
2. **TOC vs Content Distinction**: Critical to distinguish table of contents entries from actual content
   - TOC entries have page numbers after them
   - Actual content has topic headings followed by sub-topics nearby
   - Always verify context before extracting (look for descriptive text like "For this component" or "Learners should")
3. **AI Prompts**: Need to be concise and direct - overly verbose prompts can trigger refusals
4. **Subject Filtering**: For shared PDFs, need strong filtering instructions and multiple filter layers
5. **Section Finding**: Must be careful with end markers - "Version" appears in headers, use "Appendix" or "2d. Prior knowledge" instead
6. **Content Section Storage**: Store the content section once found, reuse it for all topic extractions (don't search entire PDF each time)
7. **Duplicate Prevention**: Multiple filter layers needed - AI prompt, parser filter, and post-extraction filter
8. **Level 0 Structure**: Some subjects need components as Level 0 (not subject name)
   - Economics: Components are Level 0
   - Classical Greek: 3 specific Level 0s (Language, Prose/Verse, Culture)
   - Drama: Component 04 only as Level 0
9. **Markdown Format Handling**: AI sometimes outputs markdown instead of numbered format
   - Parser must handle both: `### 3. Topic` (Level 1), `#### 3.1 Sub-topic` (Level 2), `- 3.1.1. Item` (Level 3)
   - Prompt should explicitly request numbered format, but parser should handle markdown as fallback
10. **Parent Assignment**: Level 1 topics need explicit parent assignment to Level 0
    - Use `parent_code = base_code` when `level == 1 and parent_code is None`
    - Level 2 topics may need to find/create Level 1 parent if missing
11. **Table Structure Extraction**: Multi-column tables need careful parsing
    - Drama: 3 columns → Level 1, 2, 3, 4
    - Economics: 2 columns → Level 2 (Topic), Level 3 (Learners should be able to)
    - Must extract ALL items from "Learners should be able to" column
12. **Component Filtering**: Some subjects have non-exam components that should be excluded
    - Drama: Components 01/02/03 are non-exam assessment, only Component 04 is examined
    - Must filter these out in section finding and extraction

---

## 📋 NEXT STEPS FOR BIOLOGY A

1. **Investigate PDF Structure**:
   - Check if tables are actually in the extracted text
   - May need to use `pdfplumber` table extraction instead of text extraction
   - Verify content section contains the actual table data

2. **Alternative Approach**:
   - Extract tables directly using pdfplumber
   - Parse table structure programmatically
   - Then use AI to format/organize the extracted data

3. **Debug Current Approach**:
   - Save the actual section_text being passed to AI
   - Check if it contains table data
   - Verify AI is receiving enough context

---

---

## ✅ RECENTLY CREATED SPECIALIZED SCRAPERS (December 2025)

### Classical Greek (J292) - ✅ FIXED AND WORKING
**Previous Problem**: Incorrect Level 0 structure, assessment sections being extracted, missing appendix content.

**Fixes Applied**:
1. **Correct Level 0 structure**: Creates exactly 3 Level 0 topics:
   - Language (J292/01)
   - Prose Literature and Verse Literature (contains 4 Level 1s: Prose A, Prose B, Verse A, Verse B)
   - Literature and Culture (J292/06)
2. **Parent assignment fix**: Level 1 topics now correctly get `parent = base_code` (the Level 0 component)
3. **Appendix integration**: Appendices 5d and 5e are integrated into Language content, not separate topics
4. **Assessment filtering**: Filters out "Forms of assessment", "Assessment objectives", and other admin sections
5. **Section finding**: Distinguishes TOC entries from actual content sections

**Current Status**: ✅ **WORKING**
- File: `scrapers/OCR/GCSE/topics/ocr-classical-greek-manual.py`
- Test: `.\TEST-CLASSICAL-GREEK.bat`
- Extracts proper 3 Level 0 structure with full depth

### Drama (J316) - ✅ CREATED AND WORKING
**Requirements**: Extract only Component 04 (examined component), exclude Components 01/02/03 (non-exam assessment).

**Features**:
1. **Component filtering**: Extracts ONLY Component 04 "Drama: Performance and response"
2. **Table structure extraction**:
   - Level 1: From "Learners should:" column (main sections)
   - Level 2: Solid bullets from "Learners must know and understand:" column
   - Level 3: Open bullets (indented) from "Learners must know and understand:" column
   - Level 4: Synthesized from "Learners should be able to:" column
3. **Section finding**: Distinguishes TOC entries from actual content (looks for descriptive text like "For this component")
4. **Performance texts**: Extracted as Level 1 topic with individual texts as Level 2

**Current Status**: ✅ **WORKING**
- File: `scrapers/OCR/GCSE/topics/ocr-drama-manual.py`
- Test: `.\TEST-DRAMA.bat`
- Extracts Component 04 with proper depth from 3-column table

### Economics (J205) - ✅ CREATED AND WORKING
**Previous Problem**: Subject name as Level 0, missing "Learners should be able to" content, incorrect level assignment.

**Fixes Applied**:
1. **Level 0 structure**: Components are Level 0 (not subject name)
   - Component 01: Introduction to Economics
   - Component 02: National and International Economics
2. **Table extraction**:
   - Level 1: Main topics (e.g., "3. Economic objectives and the role of government")
   - Level 2: Sub-topics from "Topic" column (e.g., "3.1 Economic growth")
   - Level 3: ALL items from "Learners should be able to" column (every bullet point)
3. **Markdown handling**: Parser handles both numbered format and markdown format from AI:
   - `### 3. Topic` → Level 1
   - `#### 3.1 Sub-topic` → Level 2
   - `- 3.1.1. Item` → Level 3
4. **Parent assignment**: Level 1 topics get `parent = base_code`, Level 2 topics find/create Level 1 parent
5. **Error handling**: Improved batch insertion with detailed error reporting

**Current Status**: ✅ **WORKING**
- File: `scrapers/OCR/GCSE/topics/ocr-economics-manual.py`
- Test: `.\TEST-ECONOMICS.bat`
- Extracts both components with full depth including all "Learners should be able to" items

**Key Code Patterns**:
- Section finding: Distinguishes TOC (has page numbers) from content (has descriptive text)
- Markdown parsing: Handles `###`, `####` headers and `-` bullet points
- Parent stack: Maintains parent relationships across parsing
- Level adjustment: Creates missing parent levels when needed

---

**End of Handover Document**

