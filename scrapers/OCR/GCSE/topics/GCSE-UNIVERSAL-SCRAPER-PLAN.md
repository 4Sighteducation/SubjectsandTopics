# OCR GCSE Universal Scraper - Design Plan

## Overview

A smart, universal scraper that can process ALL OCR GCSE courses with a two-phase approach: **Analyze → Extract → Assess**.

## Architecture

### Three-Phase Process

1. **PHASE 1: ANALYSIS** - Understand PDF structure before extraction
2. **PHASE 2: EXTRACTION** - Build hierarchy based on analysis
3. **PHASE 3: SELF-ASSESSMENT** - Generate quality report

### Key Features

#### 1. Smart Analysis Phase
- Finds "Content Overview" section first
- Identifies structure type (table-based, chapter-based, etc.)
- Detects tiers (Foundation/Higher)
- Identifies optional units
- Finds text lists (English, Drama, etc.)
- Matches known patterns from A-Level scrapers

#### 2. Intelligent Extraction Phase
- Uses analysis to build appropriate extraction prompt
- Handles tiers: Creates separate Level 0 for Foundation/Higher
- Extracts ALL options (doesn't skip optional content)
- Handles texts: Separate hierarchy or incorporated
- Adapts to different PDF structures
- Focuses ONLY on externally examined content (ignores coursework)

#### 3. Self-Assessment Phase
- Generates quality report for each subject
- Counts topics per level
- Identifies issues and warnings
- Provides success grade (%)
- Saves individual reports + summary report

## Handling Complications

### A. Tiers (Foundation/Higher)
**Problem**: Same specification, different content for different grade ranges.

**Solution**:
- Create TWO Level 0 topics: "Foundation Tier" and "Higher Tier"
- Each tier has similar Level 1 structure
- Level 2-4 content differs based on tier
- Shared content appears in BOTH tiers

**Example**:
```
1 Foundation Tier
1.1 Component 01: Biology
1.1.1 [Foundation content]
2 Higher Tier
2.1 Component 01: Biology
2.1.1 [Higher content]
```

### B. Options
**Problem**: Some subjects have optional units that must ALL be extracted.

**Solution**:
- Analysis phase identifies ALL optional units
- Extraction phase explicitly instructed to extract ALL options
- No skipping of optional content
- Options clearly marked in hierarchy

### C. Texts (English, Drama, Art)
**Problem**: Prescribed texts need special handling.

**Solution**:
- Analysis phase detects text lists
- Two strategies:
  - **Separate hierarchy**: "1. Prescribed Texts" as Level 1
  - **Incorporated**: Texts added as sub-items under relevant topics
- Strategy chosen based on PDF structure

### D. Different PDF Structures
**Problem**: GCSE PDFs vary significantly in structure.

**Solution**:
- Analysis phase identifies structure type
- Matches known patterns from A-Level scrapers:
  - Mathematics (table with ref codes)
  - Sociology (Key questions, Content, Learners should)
  - Religious Studies (Topic, Content, Key Knowledge)
  - PE (Topic Area, Content with bullets)
  - Law (Content, Guidance)
- Adapts extraction prompt accordingly

## Output Format

### Individual Subject Report (JSON)
```json
{
  "subject_code": "J260",
  "subject_name": "Combined Science B",
  "success": true,
  "topics_extracted": 450,
  "levels": {
    "0": 2,
    "1": 20,
    "2": 100,
    "3": 200,
    "4": 128
  },
  "issues": [],
  "warnings": ["Some topics may span pages"],
  "success_grade": 92,
  "analysis": {
    "tiers": {"has_tiers": true, ...},
    "options": {"has_options": false, ...},
    "structure_type": "chapter-based"
  },
  "duration_seconds": 45.2
}
```

### Summary Report
- Total subjects processed
- Success/fail counts
- Success rate
- All individual reports

## Usage

### Process All Subjects
```bash
python ocr-gcse-universal-scraper.py
```

### Process One Subject (Testing)
```bash
python ocr-gcse-universal-scraper.py --subject-code J260
```

### Process First N Subjects
```bash
python ocr-gcse-universal-scraper.py --limit 5
```

## File Structure

```
scrapers/OCR/GCSE/
├── topics/
│   ├── ocr-gcse-universal-scraper.py  # Main scraper
│   └── TEST-GCSE-UNIVERSAL.bat         # Test script
└── reports/
    ├── J260-report.json                # Individual reports
    ├── J247-report.json
    └── summary-20250101-120000.json    # Summary report
```

## Known Patterns from A-Level

The scraper leverages knowledge from A-Level scrapers:

1. **Mathematics**: Table-based with reference codes
2. **Sociology**: 3-column tables (Key questions, Content, Learners should)
3. **Religious Studies**: 3-column tables (Topic, Content, Key Knowledge)
4. **PE**: 2-column tables (Topic Area, Content with bullets)
5. **Law**: 2-column tables (Content, Guidance)
6. **Psychology**: Component-based with sections
7. **Classical Civ**: Table-based with prescribed texts

## Success Criteria

A successful extraction should:
- ✅ Extract all externally examined content
- ✅ Handle tiers correctly (if present)
- ✅ Extract all options (if present)
- ✅ Handle texts appropriately (if present)
- ✅ Maintain correct hierarchy
- ✅ Match expected structure from Content Overview
- ✅ Generate quality report with grade > 70%

## Error Handling

- PDF download failures → Skip subject, log error
- Analysis failures → Use fallback extraction
- Extraction failures → Log error, continue to next subject
- Database upload failures → Log warning, continue
- Rate limiting → 5 second delay between subjects

## Performance

- Expected time per subject: 30-90 seconds
- Total subjects: ~32
- Estimated total time: 1-2 hours
- Can be interrupted and resumed (re-run with --subject-code)

## Future Enhancements

1. Resume capability (check existing reports)
2. Parallel processing (multiple subjects simultaneously)
3. Progress bar/visual feedback
4. HTML report generation
5. Comparison with previous runs

