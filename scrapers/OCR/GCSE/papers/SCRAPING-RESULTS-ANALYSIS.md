# OCR GCSE Papers Scraping - Results Analysis

## Summary

12 subjects had no papers scraped. Analysis of debug HTML files reveals the following issues:

## Issues Found

### 1. Wrong Subject Codes
- **Ancient History**: Batch script used `J051` but dropdown only has `J198`
- **Geography A**: Batch script used `J382` but dropdown has `J383`

### 2. Wrong Qualification Filter Names
The qualification filter names in the batch script don't match the dropdown exactly. They need to include:
- "(9-1)" designation
- Full qualification suite names (e.g., "Gateway Science Suite - Biology A")
- Exact text as it appears in dropdown

### 3. Subjects with Empty Results (6 found so far)
These subjects have empty `.finder-results` divs in debug HTML:
1. **J203** - Sociology (listed as "Psychology" in dropdown)
2. **J625** - Religious Studies (Level dropdown enabled but not selected)
3. **J730** - French
4. **J731** - German
5. **J732** - Spanish
6. **J814** - Dance

**Possible reasons:**
- Qualification filter name mismatch (most likely)
- Level dropdown needs to be selected (for some subjects)
- No papers available from 2019+ (less likely)

## Fixes Applied

### 1. Updated Batch Script (`RUN-FULL-GCSE-PAPERS-BATCH.bat`)
- Fixed Ancient History code: `J051` → `J198`
- Fixed Geography A code: `J382` → `J383`
- Updated all qualification filter names to match dropdown exactly
- Added "(9-1)" designation where needed
- Added full suite names (e.g., "Gateway Science Suite - Biology A")

### 2. Updated Scraper (`scrape-ocr-gcse-papers-universal.py`)
- Improved qualification matching with multiple strategies:
  1. Exact/contains match
  2. Match by subject code
  3. Partial match by subject name + code
- Added Level dropdown selection when enabled
- Better error messages showing available options

## Correct Qualification Filters

All qualification filters have been updated in the batch script. Key examples:

- Ancient History: `"Ancient History (9-1) - J198 (from 2017)"` (code: J198)
- Biology A: `"Gateway Science Suite - Biology A (9-1) - J247 (from 2016)"`
- Geography A: `"Geography A (Geographical Themes) (9-1) - J383 (from 2016)"` (code: J383)
- Religious Studies: `"Religious Studies (9-1) - J625, J125 (from 2016)"`
- Sociology: `"Psychology (9-1) - J203 (from 2017)"` (listed as Psychology but code is J203)

## Next Steps

1. **Re-run the batch script** with corrected qualification names
2. **Check debug HTML files** for the 6 subjects with empty results to verify:
   - Qualification was selected correctly
   - Level dropdown was selected (if needed)
   - Whether papers genuinely exist

3. **If still failing**, check:
   - Are papers available from 2019+ for these subjects?
   - Do these subjects require different filter combinations?
   - Are there any OCR website-specific requirements?

## Files Created

- `SCRAPING-ISSUES-SUMMARY.md` - Detailed issues breakdown
- `SUBJECTS-NO-PAPERS-ANALYSIS.md` - Analysis of subjects with no papers
- `SUBJECTS-WITH-NO-PAPERS.md` - Quick reference list
- `ANALYZE-SCRAPING-RESULTS.py` - Python script to analyze results (requires Python)
- `EXTRACT-GCSE-QUALIFICATIONS.py` - Script to extract qualification names

## Debug Files Location

All debug HTML files are saved in: `debug-output/ocr-gcse-{SUBJECT_CODE}-after-filters.html`

These files show:
- Whether qualification was selected
- Whether Level dropdown is enabled/selected
- Content of `.finder-results` div (empty = no papers found)

