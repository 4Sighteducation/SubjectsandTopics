# Edexcel A-Level - Verified Complete Subjects
**Updated:** November 5, 2025

## FULLY COMPLETE (6 subjects)

| Subject | Code | Topics | Hierarchy | Papers | Status |
|---------|------|--------|-----------|--------|--------|
| Arabic | 9AA0 | 55 | 4 levels | 21 | ✅ |
| Art and Design | 9AD0 | 96 | 3 levels | 8 | ✅ |
| Business | 9BS0 | 613 | 5 levels | 30 | ✅ |
| Chemistry | 9CH0 | 265 | 4 levels | 30 | ✅ |
| Chinese | 9CN0 | 36 | 4 levels | 21 | ✅ |
| Physics | 9PH0 | 250 | 3 levels | 30 | ✅ |

**TOTAL: 1,315 topics + 140 paper sets**

## TOPICS ONLY (1 subject)

| Subject | Code | Topics | Papers | Notes |
|---------|------|--------|--------|-------|
| Design and Technology | 9DT0 | 139 | 0 | Papers not found on coursematerials page |

## WORKING SCRAPERS

### Topic Scrapers
- `scrape-business-improved.py` - For table-structured subjects (Business, Economics, etc.)
- `scrape-edexcel-universal.py` - For science subjects (Chemistry, Physics, Biology B)
- `upload-arabic-manual.py` - Manual upload for Arabic with script
- `upload-chinese-manual.py` - Manual upload for Chinese with script
- `upload-art-design-manual.py` - Manual upload for Art and Design
- `scrape-design-tech-improved.py` - For Design and Technology

### Paper Scrapers (SELENIUM ONLY - URL guessing doesn't work!)
- `scrape-business-papers-selenium.py` - Verified working
- `scrape-chinese-papers-selenium.py` - Verified working
- `scrape-arabic-papers-selenium.py` - Verified working
- `scrape-art-papers-selenium.py` - Verified working (8 sets)
- `scrape-biology-a-papers.py` - Verified working (30 sets)
- `scrape-history-papers-selenium.py` - Verified working (259 sets from previous session)
- `scrape-edexcel-papers-universal.py` - Original universal (works for most)

## REMAINING SUBJECTS (29)

Need to verify/re-scrape from batch run:
- Biology B, Economics A, Economics B, English Language, English Lang&Lit, 
  English Literature, French, Geography, German, Greek, Gujarati,
  History of Art, Italian, Japanese, Mathematics, Music, Music Technology,
  Persian, Physical Education, Politics, Portuguese, Psychology,
  Religious Studies, Russian, Spanish, Statistics, Turkish, Urdu

Known structure issues (need manual upload):
- Drama and Theatre
- Music
- Music Technology

## NEXT STEPS

1. **Apply Business scraper to similar subjects:**
   - Economics A, Economics B
   - Geography, Psychology, Politics
   - English subjects (if similar table structure)

2. **Manual upload remaining languages** (use Arabic/Chinese templates)

3. **Investigate why some papers aren't showing:**
   - Design and Technology
   - Any others with 0 papers

4. **Don't aim for perfection** - focus on high-priority subjects for FLASH users

## LESSONS LEARNED

1. ✅ **Selenium ALWAYS for papers** - URL guessing gives false positives
2. ✅ **Manual upload is fast** for specialized/niche subjects
3. ✅ **Unicode works perfectly** - Arabic and Chinese scripts in database
4. ✅ **Deep hierarchies possible** - Business has 5 levels
5. ✅ **PDF structures vary** - need flexible or subject-specific scrapers

