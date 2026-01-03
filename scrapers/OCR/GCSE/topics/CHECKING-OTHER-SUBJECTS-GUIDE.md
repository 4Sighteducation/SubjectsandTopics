# Guide: Checking and Fixing Hierarchy Issues in Other OCR GCSE Subjects

## Date
November 24, 2025

## What We Fixed

Successfully fixed OCR GCSE Physical Education (J587) scraper to extract proper hierarchy:
- **Before**: 51 topics (incomplete extraction)
- **After**: 214 topics with proper Level 1, 2, 3, 4 structure

## How to Check If Other Subjects Have Similar Issues

### Step 1: View in Data Viewer

Open your data viewer and look at any OCR GCSE subject. Check:

1. **Are Level 2 and Level 3 topics missing?**
   - If you only see Level 0 (components/tiers) and Level 4 (detailed items), there's a hierarchy problem

2. **Is the topic count suspiciously low?**
   - Compare with the actual PDF specification
   - If the PDF has 10-20 pages of content tables but you only have 50-100 topics, something is missing

3. **Do topics appear at the wrong level?**
   - Look for patterns like: Level 0 → Level 4 (skipping Level 1, 2, 3)
   - This indicates incorrect numbering in the AI extraction

### Step 2: Check the Reports

Look in `scrapers/OCR/GCSE/topics/reports/` for the subject's JSON report:

```bash
cat reports/JXXX-report.json
```

Key indicators of issues:
- `"topics_extracted"` is suspiciously low (< 100 for complex subjects)
- `"success_grade"` is below 85
- `"issues"` mentions "Missing content" or "Incomplete extraction"
- Level distribution shows missing intermediate levels

### Step 3: Compare Manual vs Universal Scraper

For Physical Education:
- **Universal scraper**: 51 topics ❌
- **Manual scraper**: 214 topics ✓

If a subject has a manual scraper (e.g., `ocr-physical-education-manual.py`), use it instead of the universal scraper!

## Subjects with Manual Scrapers

These subjects have dedicated manual scrapers that may extract more thoroughly:

```
scrapers/OCR/GCSE/topics/
├── ocr-physical-education-manual.py      ✓ FIXED (214 topics)
├── ocr-religious-studies-manual.py       ? Check this
├── ocr-geography-a-manual.py             ? Check this
├── ocr-geography-b-manual.py             ? Check this
├── ocr-food-preparation-nutrition-manual.py ? Check this
├── ocr-economics-manual.py               ? Check this
├── ocr-media-studies-manual.py           ? Check this
├── ocr-history-a-manual.py               ? Check this
├── ocr-history-b-manual.py               ? Check this
├── ocr-mathematics-manual.py             ? Check this
├── ocr-drama-manual.py                   ? Check this
├── ocr-art-subjects-manual.py            ? Check this
├── ocr-classical-greek-manual.py         ? Check this
├── ocr-physics-a-manual.py               ? Check this
├── ocr-ancient-history-manual.py         ? Check this
├── ocr-chemistry-a-manual.py             ? Check this
└── ocr-biology-a-manual.py               ? Check this
```

## How to Fix a Subject with Hierarchy Issues

### Option 1: If the subject has a manual scraper

Apply the same fix we used for Physical Education:

1. **Update the AI prompt** to include explicit numbering examples:

```python
prompt = f"""...

OUTPUT FORMAT - EXACT NUMBERING REQUIRED:
   
   CORRECT EXAMPLE:
   1. Section Title (Level 1)
   1.1. Topic Area (Level 2)
   1.1.1. Learning objective (Level 3)
   1.1.1.1. Sub-item (Level 4)
   
   WRONG EXAMPLE (DO NOT DO THIS):
   1. Section Title
   1.1.1. Topic Area  <-- WRONG! Should be 1.1.
   1.1.1.1. Learning objective  <-- WRONG! Should be 1.1.1.
   
   KEY RULES:
   - Sections: Single number (1., 2., 3.)
   - Topic Areas: Two numbers (1.1., 1.2., 2.1.)
   - Learning items: Three numbers (1.1.1., 1.1.2.)
   - Sub-items: Four numbers (1.1.1.1., 1.1.1.2.)
...
"""
```

2. **Add exclusion filters** to catch incorrect levels:

```python
excluded_patterns = [
    r'^subject\s+name$',
    r'^component\s+\d+:',
    r'^jXXX/\d+',  # Replace XXX with subject code
]
```

3. **Test the scraper**:

```bash
cd scrapers/OCR/GCSE/topics
python ocr-SUBJECT-manual.py
```

4. **Check the debug output**:

```bash
cat ../../A-Level/debug-output/JXXX-XX-ai-output.txt
```

Verify the numbering is correct (1., 1.1., 1.1.1., not 1., 1.1.1., 1.1.1.1.)

### Option 2: If using the universal scraper

The universal scraper is more complex because it handles many different structures. Consider:

1. **Create a manual scraper** for that specific subject if it's important
   - Copy `ocr-physical-education-manual.py` as a template
   - Adapt it to the subject's specific structure

2. **OR improve the universal scraper prompt** (more risky, affects all subjects):
   - Add explicit numbering examples to the universal scraper prompt
   - Test on multiple subjects to ensure it doesn't break anything

## Red Flags to Watch For

### 🚩 Missing Intermediate Levels
```
Level 0: 2 topics
Level 1: 0 topics  ❌ MISSING!
Level 2: 0 topics  ❌ MISSING!
Level 3: 0 topics  ❌ MISSING!
Level 4: 200 topics
```

### 🚩 Suspiciously Low Topic Count
- Physical Education PDF has ~30 pages of content tables
- Should have 150-250 topics minimum
- If you see 50 topics, something is wrong

### 🚩 Wrong Numbering in Debug Output
```
1. Section
1.1.1. Topic Area  ❌ Should be 1.1.
1.1.1.1. Item      ❌ Should be 1.1.1.
```

## Testing After Fix

After applying a fix, verify:

1. **Run the scraper** and check topic counts:
```
Level 0: 2 topics   (Components/Tiers)
Level 1: 3-10 topics (Sections)
Level 2: 10-30 topics (Topic Areas)
Level 3: 50-150 topics (Learning objectives)
Level 4: 30-100 topics (Sub-items)
```

2. **Check database**: Open data viewer and verify:
   - All levels are present
   - Hierarchy makes logical sense
   - No duplicate codes
   - Parent-child relationships are correct

3. **Compare with PDF**: Open the specification PDF and spot-check:
   - Are major sections extracted? ✓
   - Are table contents extracted? ✓
   - Are learning objectives extracted? ✓
   - Are sub-bullets extracted? ✓

## Priority Subjects to Check

Based on complexity and importance, check these first:

1. **Physical Education** - ✓ FIXED (214 topics now)
2. **Religious Studies** - Complex structure, check if manual scraper works well
3. **Computer Science** - Component-based, check hierarchy
4. **History A/B** - Options-based, check all options extracted
5. **Geography A/B** - Check if manual scrapers are better than universal

## When to Use Manual vs Universal Scraper

### Use Manual Scraper When:
- ✓ Subject has complex table structures
- ✓ Multiple "columns" need to be matched (e.g., "Topic area" + "Learners must:")
- ✓ Specific extraction logic is needed
- ✓ Universal scraper produces incomplete results

### Use Universal Scraper When:
- ✓ Subject has standard structure
- ✓ No special extraction requirements
- ✓ Manual scraper doesn't exist
- ✓ Universal scraper works well (grade > 85, good topic count)

## Summary

**The Fix**: Enhanced AI prompts with explicit numbering examples to prevent hierarchy level confusion

**Result**: Physical Education now has 214 topics with proper Level 1-5 structure instead of 51 incomplete topics

**Next Steps**: 
1. Check other subjects using the data viewer
2. Apply the same fix to subjects with similar issues
3. Consider creating manual scrapers for subjects where universal scraper underperforms
4. Test thoroughly after any changes

## Need Help?

Refer to:
- `PHYSICAL-EDUCATION-FIX-SUMMARY.md` - Detailed explanation of the fix
- Debug output files in `scrapers/OCR/A-Level/debug-output/`
- Report files in `scrapers/OCR/GCSE/topics/reports/`




















