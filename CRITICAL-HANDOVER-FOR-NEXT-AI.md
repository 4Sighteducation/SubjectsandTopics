# 🚨 CRITICAL HANDOVER - EDEXCEL SCRAPING PROJECT

**Date:** November 6, 2025  
**Project:** Scraping topics and exam papers for Edexcel A-Level and GCSE subjects  
**Status:** A-Level 95% complete, GCSE 70% complete

---

## ⚠️ **CRITICAL RULE #1 - READ THIS FIRST**

### **NEVER INVENT OR GUESS TOPICS**

❌ **DO NOT:**
- Create topics based on "general knowledge" or "what should be there"
- Guess topic names if the scraper fails
- Fill in missing content with assumptions
- Use "typical" content from similar subjects

✅ **ONLY:**
- Extract topics EXACTLY as written in the PDF specification
- Use content the user provides by pasting
- Admit when scraper fails and ask for help
- Say "I cannot extract this automatically" rather than guessing

**If the scraper doesn't work, STOP and ask for help. Do NOT make up topics.**

---

## 📊 PROJECT STATUS

### **A-LEVEL: 35/37 subjects (95%)**

**Complete with Topics + Papers:**
- All 14 languages (636 topics with native scripts)
- Business, Economics A/B, Chemistry, Physics (deep hierarchies)
- English Language, English Literature, English Lang & Lit (papers only)
- Mathematics, Statistics, Physical Education, History of Art
- Politics, Religious Studies
- Arabic, Chinese, Drama, Art, Design & Tech

**Total A-Level: ~5,000 topics + ~680 paper sets**

### **GCSE: 28/35 subjects (80%)**

**Complete:**
- Drama, Art, Astronomy, Biblical Hebrew
- All 14 languages (universal template)
- 10 subjects from batch scraper (varying quality)

**Total GCSE: ~1,100 topics + ~250 paper sets**

---

## 🔧 PROVEN SCRAPERS THAT WORK

### **1. Business Scraper Template** ⭐ BEST for table-based subjects
**File:** `scrapers/Edexcel/A-Level/topics/scrape-business-improved.py`

**Use for:**
- Business, Economics, Geography, Psychology, Religious Studies
- Any subject with 2-3 column tables
- Numbered hierarchies (1.1 → 1.1.1 → a) → o)

**Success rate:** 100% for A-Level table subjects (produces 400-700 topics with 5 levels)

**How to adapt:**
1. Copy file
2. Update SUBJECT dict (code, name, PDF URL)
3. Update themes list (from PDF Contents section)
4. Run - it will extract tables automatically

### **2. Universal Science Scraper**
**File:** `scrapers/Edexcel/A-Level/topics/scrape-edexcel-universal.py`

**Use for:**
- Chemistry, Physics, Biology, Science subjects
- Pattern: "Topic X:" headers with numbered learning outcomes

**Success rate:** 95% (produces 200-300 topics with 3-4 levels)

### **3. Manual Language Upload Templates**
**Files:** `scrapers/Edexcel/A-Level/topics/upload-*-manual.py`

**Use for:**
- All language subjects (A-Level and GCSE)
- Preserves native scripts
- GCSE languages use universal template (6 themes + grammar categories)

**Success rate:** 100% (requires user to paste theme content)

---

## 🚨 CRITICAL LESSONS LEARNED

### **1. NEVER Truncate Content**
❌ Bad: `title[:150]`  
✅ Good: `title[:500]` or no truncation at all

Mathematics and PE failed multiple times because of truncation cutting off important content.

### **2. Code Mismatches Are Common**
**A-Level:**
- Physical Education: Subject `9PE1` → Papers `9pe0`
- Persian: Subject `9PE0` → Papers `9pn0`
- Portuguese: Subject `9PT0` → Papers `9pg0`

**GCSE:**
- All subjects: `1` prefix (e.g., `1dr0`, `1as0`) not `9`
- Drama: Subject `GCSE-Drama` → Papers `1dr0`
- Languages: Same pattern (`1fr0`, `1in0`, etc.)

**Always check actual paper URLs before assuming codes!**

### **3. URL Year Matters**
- Arabic A-Level: `arabic-2017` = 0 papers, `arabic-2018` = 21 papers
- GCSE French/German/Spanish: Use `2016` URLs for papers, not `2024`

### **4. Focus on EXAMINED Content ONLY**
GCSE subjects especially have non-examined components:
- Drama: Only Component 3 is written exam
- Art: Skip NEA/coursework
- PE: Skip practical components

### **5. Manual Upload is Often Faster**
For niche subjects (Biblical Hebrew, specialist arts), 15-minute manual upload beats hours of parser debugging.

---

## 📁 KEY FILES AND PATTERNS

### **Working Topic Scrapers:**
```
A-Level/topics/
├── scrape-business-improved.py ⭐ (Use for ANY table subject)
├── scrape-edexcel-universal.py (Sciences)
├── upload-*-manual.py (Languages - 14 files)
├── scrape-mathematics-final.py (Clean, no truncation)
├── scrape-statistics-improved.py (Full topic names)
├── scrape-pe-complete.py (4 levels, 143 topics)
└── upload-history-of-art-complete.py (Optional themes/periods)

GCSE/topics/
├── upload-gcse-drama-manual.py ⭐ (Component 3 only)
├── upload-universal-gcse-languages.py ⭐ (All 14 languages)
├── upload-gcse-art-manual.py (5 titles, different areas each)
├── scrape-gcse-astronomy.py (16 topics with names)
└── upload-gcse-biblical-hebrew-manual.py (Examined content)
```

### **Working Paper Scrapers:**
```
A-Level/papers/
├── scrape-all-languages-papers-selenium.py ⭐ (14 languages in ONE file!)
├── scrape-english-*-papers-selenium.py (3 English subjects)
├── scrape-pe-papers-try-multiple-urls.py (Code mismatch fixes)
└── scrape-final-three-papers.py (Drama, Persian, Portuguese)

GCSE/papers/
├── scrape-gcse-drama-papers.py (Code: 1DR0)
├── scrape-all-gcse-language-papers.py (14 languages)
├── scrape-gcse-astronomy-papers.py (Code: 1AS0)
└── scrape-gcse-biblical-hebrew-papers.py (Code: 1BH0)
```

---

## 🎯 WHAT TO DO NEXT

### **Remaining A-Level (2 subjects):**
1. Biology B - Use universal scraper
2. Music/Music Tech - Manual upload

### **Remaining GCSE (7 subjects):**
1. **Business** - USER MUST PASTE CONTENT - scraper failed, do NOT invent!
2. Citizenship - Try table scraper or manual
3. Design & Technology - Table-based
4. English Language - Manual (examined content only)
5. English Literature - Manual (prescribed texts)
6. Mathematics - Adapt A-Level scraper
7. Music - Manual

### **Papers Needed:**
- A-Level: 7 subjects need papers
- GCSE: 15+ subjects need papers (run scrapers with correct codes)

---

## 💡 WORKFLOW FOR NEW SUBJECTS

### **Step 1: Identify Subject Type**
- **Table-based?** (Business, Geography, Psychology) → Business template
- **Science?** (Topic X: pattern) → Universal scraper
- **Language?** → Manual template
- **Arts/Specialist?** → Manual upload

### **Step 2: Extract Topics**
**DO:**
- Download PDF and save debug file
- Try proven scraper for subject type
- Check if topics extracted match PDF content

**DON'T:**
- Invent topics if scraper fails
- Guess structure
- Fill in gaps with assumptions

### **Step 3: Verify Quality**
- Check topic names aren't truncated
- Verify hierarchy makes sense
- Ensure no duplicate codes
- Confirm content is from examined sections only

### **Step 4: Papers**
- Use code from actual paper URL (not assumed!)
- Check for code mismatches (9→1 for GCSE, variations like 9PE1→9PE0)
- Try multiple URL years if needed (2016, 2017, 2018)

---

## 🐛 COMMON ISSUES & FIXES

### **Issue: Scraper finds 0 topics**
**Fix:** Check debug file - might be wrong section of PDF or pattern mismatch

### **Issue: Truncated titles**
**Fix:** Remove ALL `.[:150]` truncation, use `.[:500]` or remove entirely

### **Issue: Duplicate code errors**
**Fix:** Add deduplication before upload:
```python
unique = []
seen = set()
for t in topics:
    if t['code'] not in seen:
        unique.append(t)
        seen.add(t['code'])
```

### **Issue: 0 papers found**
**Fix:** 
1. Check actual paper URL for real code
2. Try different year URLs (2016, 2017, 2018)
3. Check for code mismatches (subject code ≠ paper code)

---

## 📋 CODE MISMATCH REFERENCE

**A-Level:**
| Subject Code | Paper Code | Notes |
|-------------|------------|-------|
| 9PE1 | 9pe0 | Physical Education |
| 9PE0 | 9pn0 | Persian |
| 9PT0 | 9pg0 | Portuguese |

**GCSE:**
| Subject Code | Paper Code | Notes |
|-------------|------------|-------|
| All subjects | 1xxx | Replace 9 with 1 |
| GCSE-Drama | 1dr0 | Not 9dr0 |
| GCSE-Art | 1ad0 | Non-standard filenames |
| GCSE-Astronomy | 1as0 | Standard format |
| GCSE-BiblicalHebrew | 1bh0 | Uses underscores |

---

## 🎓 COMPLETED SUBJECTS - DO NOT REDO

### **A-Level (Complete):**
Arabic, Art, Business, Chemistry, Chinese, Design & Tech, Drama, Economics A, Economics B, English Language (papers), English Literature (papers), English Lang & Lit (papers), French, German, Greek, Gujarati, History of Art, Italian, Japanese, Mathematics, Persian, Physics, Politics, Portuguese, Religious Studies, Russian, Spanish, Statistics, Turkish, Urdu, Physical Education

### **GCSE (Complete):**
Drama, Art and Design, Astronomy, Biblical Hebrew, All 14 Languages (Arabic, Chinese, French, German, Greek, Gujarati, Italian, Japanese, Persian, Portuguese, Russian, Spanish, Turkish, Urdu)

---

## ⚡ QUICK REFERENCE

**Best Practices:**
- ✅ Use proven templates (Business, Universal, Manual)
- ✅ Save debug files for every PDF
- ✅ Preserve full content (no truncation)
- ✅ Focus on examined content only
- ✅ Check actual paper URLs for codes
- ❌ NEVER invent topics
- ❌ NEVER guess structure
- ❌ NEVER truncate at 150 chars

**When Stuck:**
1. Save debug file
2. Ask user to paste content
3. Or suggest manual upload
4. Do NOT make up topics!

---

## 📞 NEED HELP?

**User has:**
- data-viewer-v2.html (view/edit all topics)
- Manual paper entry tool (paste URLs when Selenium fails)
- All working scrapers in project folders

**User wants:**
- Deep hierarchies (3-5 levels)
- No truncation
- Examined content only
- Actual content from specs, NOT invented

---

**END OF HANDOVER**

**Remember: When in doubt, ask the user. Never invent content.**

