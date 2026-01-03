# Physical Education Hierarchy Fix - November 24, 2025

## Executive Summary

**Issue**: OCR GCSE Physical Education (J587) was missing Level 2 and Level 3 topics in the database. The data viewer showed only Level 4 topics (214 total), but the intermediate hierarchical levels were absent.

**Root Cause**: The AI extraction prompt was not explicit enough about numbering format, causing the AI to output `1.1.1.` for Level 2 topics instead of `1.1.`, which shifted all topics one level too deep.

**Solution**: Enhanced the AI prompt with explicit CORRECT vs WRONG examples, clear numbering rules, and additional filtering to prevent incorrect hierarchy creation.

**Result**: Physical Education now has proper hierarchical structure:
- Level 0: 2 topics (Components)
- Level 1: 5 topics (Sections)
- Level 2: 19 topics (Topic Areas)
- Level 3: 104 topics (Learners must items)
- Level 4: 66 topics (Sub-items)
- Level 5: 18 topics (Nested sub-items)
- **Total: 214 topics** (same count but now properly organized!)

## Files Changed

### 1. `scrapers/OCR/GCSE/topics/ocr-physical-education-manual.py`

**Changes:**
- Enhanced AI prompt (lines ~262-331) with explicit numbering examples
- Added CORRECT vs WRONG format examples
- Emphasized that Topic Areas should use `1.1.` not `1.1.1.`
- Updated exclusion patterns to filter out component-level topics
- Added filters for `r'^component\s+\d+:'` and `r'^j587/\d+'`

**Key Improvement:**
```python
# BEFORE (implied but not explicit):
"Use numbered format (1., 1.1., 1.1.1.)"

# AFTER (explicit with examples):
"""
CORRECT EXAMPLE:
1. Section Title (Level 1)
1.1. Topic Area (Level 2)
1.1.1. Learning objective (Level 3)

WRONG EXAMPLE (DO NOT DO THIS):
1. Section Title
1.1.1. Topic Area  <-- WRONG! Should be 1.1.
1.1.1.1. Learning objective  <-- WRONG! Should be 1.1.1.
"""
```

### 2. `scrapers/OCR/GCSE/topics/PHYSICAL-EDUCATION-FIX-SUMMARY.md` (NEW)

Comprehensive documentation of:
- What was wrong
- What was fixed
- Test results
- How to verify the fix
- Impact on other scrapers

### 3. `scrapers/OCR/GCSE/topics/CHECKING-OTHER-SUBJECTS-GUIDE.md` (NEW)

User guide for:
- How to check if other subjects have similar issues
- Step-by-step instructions for applying the fix to other subjects
- List of all manual scrapers that might need checking
- Red flags to watch for
- Testing procedures

### 4. `PHYSICAL-EDUCATION-HIERARCHY-FIX-2025-11-24.md` (NEW, this file)

Executive summary for quick reference.

## Before vs After Comparison

### Before Fix

**AI Output:**
```
1. Section 1.1: Applied anatomy and physiology         (Level 1)
1.1.1. Topic Area: The structure and function...       (Level 3 - WRONG!)
1.1.1.1. know the name and location of...              (Level 4 - WRONG!)
```

**Database Distribution:**
- 51 topics total (incomplete extraction from universal scraper)
- OR 214 topics all at Level 4 (from old manual scraper)
- Missing Level 2 and Level 3 completely

**User Experience:**
- Data viewer shows only Level 4 topics
- No intermediate structure visible
- Difficult to navigate
- Content appears "flat" instead of hierarchical

### After Fix

**AI Output:**
```
1. Applied anatomy and physiology                      (Level 1)
1.1. The structure and function of the skeletal system (Level 2)
1.1.1. know the name and location of...                (Level 3)
1.1.1.1. sub-items (if nested bullets)                 (Level 4)
```

**Database Distribution:**
- 214 topics total (complete extraction)
- Properly distributed across 6 levels (0-5)
- All intermediate levels present
- Correct parent-child relationships

**User Experience:**
- Data viewer shows proper hierarchy
- Easy to navigate from sections → topics → learning objectives
- Content is properly organized
- Matches the PDF specification structure

## Testing Performed

1. ✅ Ran the scraper: `python ocr-physical-education-manual.py`
2. ✅ Verified topic count: 214 topics extracted
3. ✅ Verified level distribution: All levels 0-5 present
4. ✅ Checked debug output: Correct numbering format (1., 1.1., 1.1.1.)
5. ✅ Verified database upload: All topics uploaded successfully
6. ✅ Checked parent-child links: 212 relationships linked correctly
7. ✅ No linter errors: Code is clean

## Debug Output Location

Check these files to see the AI's improved extraction:
- `scrapers/OCR/A-Level/debug-output/J587-01-ai-output.txt`
- `scrapers/OCR/A-Level/debug-output/J587-02-ai-output.txt`

These show the correct numbered hierarchy that the AI now produces.

## Next Steps for Other Subjects

If other OCR GCSE subjects show similar symptoms:

1. **Check data viewer** - Look for missing Level 2/3 topics
2. **Check topic count** - Compare with PDF to see if it's suspiciously low
3. **Review the guide** - See `CHECKING-OTHER-SUBJECTS-GUIDE.md`
4. **Apply same fix** - Use the prompt improvements from Physical Education
5. **Test thoroughly** - Verify all levels are present after fix

### Subjects to Prioritize:

These manual scrapers may benefit from the same fix:
- Religious Studies
- Geography A & B
- Computer Science (if using manual scraper)
- History A & B
- Sciences (Biology A, Chemistry A, Physics A)

## Technical Details

**Scraper Type**: Manual Python scraper with AI extraction
**AI Model**: OpenAI GPT-4o (primary) / Claude 3.5 Haiku (fallback)
**Database**: Supabase (staging_aqa_topics table)
**Extraction Method**: PDF download → pdfplumber text extraction → AI hierarchical parsing → Database upload

**Key Mechanism:**
1. Downloads PDF from OCR website
2. Extracts text using pdfplumber
3. Finds component sections using regex patterns
4. Sends each section to AI with detailed prompt
5. Parses AI's numbered output into hierarchy
6. Uploads to database with parent-child relationships

## Success Metrics

| Metric | Before | After | Status |
|--------|--------|-------|--------|
| Total Topics | 51 (universal) or 214 (wrong levels) | 214 (correct levels) | ✅ |
| Level 0 | 2 | 2 | ✅ |
| Level 1 | Missing/Wrong | 5 | ✅ |
| Level 2 | Missing | 19 | ✅ |
| Level 3 | Missing | 104 | ✅ |
| Level 4 | 214 (wrong) or 24 | 66 | ✅ |
| Level 5 | 0 | 18 | ✅ |
| Parent Links | Partial | 212/212 | ✅ |
| Upload Success | Partial | 100% | ✅ |

## Commit Message Suggestion

```
fix: Correct hierarchy extraction for OCR GCSE Physical Education

Enhanced AI prompt with explicit numbering examples to prevent level
misidentification. Physical Education now extracts proper 6-level
hierarchy (Level 0-5) instead of collapsing everything into Level 4.

Changes:
- Updated ocr-physical-education-manual.py with detailed prompt examples
- Added exclusion filters for component-level topics
- Created documentation for applying fix to other subjects

Result: 214 topics properly distributed across all levels with correct
parent-child relationships. Level 2 and Level 3 topics now visible in
data viewer.

Files:
- Modified: scrapers/OCR/GCSE/topics/ocr-physical-education-manual.py
- Added: scrapers/OCR/GCSE/topics/PHYSICAL-EDUCATION-FIX-SUMMARY.md
- Added: scrapers/OCR/GCSE/topics/CHECKING-OTHER-SUBJECTS-GUIDE.md
- Added: PHYSICAL-EDUCATION-HIERARCHY-FIX-2025-11-24.md
```

## Verification Commands

To verify the fix is working:

```bash
# Run the scraper
cd scrapers/OCR/GCSE/topics
python ocr-physical-education-manual.py

# Check debug output
cat ../../A-Level/debug-output/J587-01-ai-output.txt | head -20

# Verify correct numbering (should see 1., 1.1., 1.1.1.)
# NOT 1., 1.1.1., 1.1.1.1.

# Check database (using your data viewer)
# Verify Level 2 and Level 3 topics are now present
```

## Contact

If you need to apply this fix to other subjects or have questions:
- Review: `CHECKING-OTHER-SUBJECTS-GUIDE.md`
- Check: Debug output files in `scrapers/OCR/A-Level/debug-output/`
- Compare: Your PDF specification with the extracted topics

## Conclusion

The OCR GCSE Physical Education scraper now correctly extracts the full hierarchical structure from the specification. The fix is well-documented and can be applied to other subjects showing similar symptoms. All changes have been tested and verified to work correctly.

**Status**: ✅ COMPLETE AND TESTED




















