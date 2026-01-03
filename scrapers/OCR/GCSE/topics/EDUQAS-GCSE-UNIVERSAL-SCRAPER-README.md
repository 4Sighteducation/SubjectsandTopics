# Eduqas GCSE Universal Scraper

A universal scraper for ALL Eduqas GCSE courses that combines PDF URL finding with AI-powered content extraction.

## Overview

This scraper:
1. **Finds PDF URLs** - Uses the PDF URL scraper to locate specification PDFs
2. **Downloads PDFs** - Downloads specification PDFs from Eduqas website
3. **Analyzes Structure** - Detects Components, Tiers, Options, and Appendices
4. **Extracts Content** - Uses AI to extract hierarchical topic structure
5. **Handles Special Cases** - Properly handles Geography components, Maths tiers, English Literature appendices, etc.
6. **Uploads to Database** - Saves extracted topics to Supabase

## Workflow

### Step 1: Find PDF URLs (First Time Only)

Before running the universal scraper, you need to find all PDF URLs:

```bash
# Test on 5 subjects first
TEST-EDUQAS-PDF-URLS.bat

# Or full run
RUN-EDUQAS-PDF-URLS.bat
```

This creates `eduqas-pdf-urls.json` with all PDF URLs.

### Step 2: Run Universal Scraper

Once PDF URLs are available, run the universal scraper:

```bash
# Test on 3 subjects
TEST-EDUQAS-GCSE-UNIVERSAL.bat

# Or full run
RUN-EDUQAS-GCSE-UNIVERSAL.bat
```

## Special Cases Handled

### 1. Components (Geography A)

Geography A has **Component 1** and **Component 2**, each with:
- **Core themes** (required)
- **Options** (choose one, but extract ALL)

**Structure:**
```
1 Component 1: Changing Physical and Human Landscapes
  1.1 Core Theme 1: Landscapes and Physical Processes
    1.1.1 Key Idea 1.1: Distinctive landscapes of the UK
      1.1.1.1 Key questions and depth of study
  1.2 Option 3: Tectonic Landscapes and Hazards
    1.2.1 [Option content]
  1.3 Option 4: Coastal Hazards and their Management
    1.3.1 [Option content]
2 Component 2: Environmental and Development Issues
  [Similar structure]
```

### 2. Tiers (Mathematics)

Mathematics has **Foundation Tier** and **Higher Tier** with different content.

**Structure:**
```
1 Foundation Tier
  1.1 Number
    1.1.1 Structure and calculation
      1.1.1.1 FN1: Order positive and negative integers...
      1.1.1.2 FN2: Apply the four operations...
2 Higher Tier
  2.1 Number
    2.1.1 Structure and calculation
      2.1.1.1 HN1: Order positive and negative integers...
      2.1.1.2 HN2: Apply the four operations...
```

### 3. Appendices (English Literature)

English Literature has **Appendices** with prescribed texts.

**Structure:**
```
1 Component 1: Shakespeare and Poetry
  1.1 Section A: Shakespeare
    1.1.1 Prescribed Texts (from Appendix A)
      1.1.1.1 Romeo and Juliet
      1.1.1.2 Macbeth
      1.1.1.3 Othello
      [etc.]
  1.2 Section B: Poetry 1789 to present day
    1.2.1 Prescribed Poems (from Appendix B)
      1.2.1.1 The Manhunt - Simon Armitage
      1.2.1.2 Sonnet 43 - Elizabeth Barrett Browning
      [etc.]
2 Component 2: Post-1914 Prose/Drama and 19th Century Prose
  [Similar structure with texts from Appendix A]
```

### 4. Options (History, Geography)

Subjects with options extract **ALL options**, even though students choose one.

**Example - Geography Options:**
```
1 Component 1
  1.1 Core Theme 1: [Required]
  1.2 Option 3: Tectonic Landscapes (Extract ALL)
  1.3 Option 4: Coastal Hazards (Extract ALL)
```

## Output Format

### Individual Subject Report

Each subject generates a JSON report in the `reports/` folder:

```json
{
  "subject_name": "Geography A",
  "level": "GCSE",
  "pdf_url": "https://www.eduqas.co.uk/media/...",
  "success": true,
  "topics_extracted": 450,
  "levels": {
    "0": 2,
    "1": 8,
    "2": 30,
    "3": 150,
    "4": 260
  },
  "issues": [],
  "warnings": [],
  "success_grade": 92,
  "analysis": {
    "has_components": true,
    "components": [
      {"number": "1", "name": "Changing Physical and Human Landscapes"},
      {"number": "2", "name": "Environmental and Development Issues"}
    ],
    "has_options": true,
    "structure_type": "component-based"
  }
}
```

### Summary Report

A summary report is generated with all subjects:

```json
{
  "timestamp": "20250101-120000",
  "total_subjects": 25,
  "success_count": 23,
  "fail_count": 2,
  "success_rate": 92.0,
  "reports": [...]
}
```

## Command Line Options

```bash
python eduqas-gcse-universal-scraper.py [OPTIONS]

Options:
  --subject SUBJECT    Filter by subject name (partial match)
  --limit N           Limit number of subjects to process
```

**Examples:**
```bash
# Test on Geography A only
python eduqas-gcse-universal-scraper.py --subject "Geography A"

# Test on first 5 subjects
python eduqas-gcse-universal-scraper.py --limit 5

# Full run
python eduqas-gcse-universal-scraper.py
```

## Requirements

- Python 3.7+
- Selenium (for PDF URL scraper)
- pdfplumber (for PDF text extraction)
- OpenAI API key OR Anthropic API key
- Supabase credentials

**Install dependencies:**
```bash
pip install requests pdfplumber openai anthropic selenium beautifulsoup4 supabase python-dotenv
```

## Troubleshooting

### PDF URLs Not Found

If you get "PDF URL not found" errors:
1. Run `RUN-EDUQAS-PDF-URLS.bat` first to generate `eduqas-pdf-urls.json`
2. Check that the file exists and contains your subject

### Extraction Fails

If extraction fails:
1. Check the report JSON for specific errors
2. Verify the PDF URL is correct and accessible
3. Check AI API keys are set correctly
4. Review the analysis section to see what was detected

### Missing Components/Options

If components or options are missing:
1. Check the analysis section in the report
2. The PDF structure may have changed
3. Review the extraction prompt for that subject type

## Performance

- **Expected time per subject**: 30-90 seconds
- **Total GCSE subjects**: ~25
- **Estimated total time**: 1-2 hours
- **Can be interrupted and resumed** (re-run with `--subject` filter)

## File Structure

```
scrapers/OCR/GCSE/topics/
├── eduqas-pdf-url-scraper.py          # PDF URL finder
├── eduqas-gcse-universal-scraper.py   # Universal scraper
├── Eduqas Qualifications - All.md     # Subject list
├── eduqas-pdf-urls.json               # PDF URLs (generated)
├── reports/                            # Individual reports
│   ├── Geography-A-report.json
│   ├── Mathematics-report.json
│   └── summary-20250101-120000.json
├── TEST-EDUQAS-PDF-URLS.bat
├── RUN-EDUQAS-PDF-URLS.bat
├── TEST-EDUQAS-GCSE-UNIVERSAL.bat
└── RUN-EDUQAS-GCSE-UNIVERSAL.bat
```

## Success Criteria

A successful extraction should:
- ✅ Extract all externally examined content
- ✅ Handle components correctly (if present)
- ✅ Handle tiers correctly (if present)
- ✅ Extract all options (if present)
- ✅ Extract appendices content (if present)
- ✅ Maintain correct hierarchy
- ✅ Generate quality report with grade > 70%

## Notes

- The scraper includes delays between requests to be polite to servers
- Some subjects may fail - check the failed list in the summary report
- PDF URLs are cached in `eduqas-pdf-urls.json` to avoid re-scraping
- Results are saved incrementally, so partial results are available even if interrupted



