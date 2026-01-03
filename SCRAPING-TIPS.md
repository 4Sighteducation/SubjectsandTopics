# 📚 PDF SCRAPING TIPS & LESSONS LEARNED

**Critical rules and patterns discovered while scraping Edexcel specifications**

---

## 🚨 GOLDEN RULE #1: NEVER INVENT CONTENT

If the scraper fails or extracts incomplete data:
- ❌ **DO NOT** guess or fill in content
- ❌ **DO NOT** use "general knowledge" 
- ✅ **DO** save debug file and investigate
- ✅ **DO** ask user for help or use manual upload

---

## 🔍 MULTI-LINE TEXT BEFORE COLONS

### The Problem

**GCSE Business Issue (Nov 2024):** Learning outcomes were appearing as single words like "activity", "customers", "business", "objectives" instead of full sentences.

**Root Cause:** In PDF specifications, text before a colon often **spans multiple lines** due to page layout:

```
The role of business enterprise and the purpose of business
activity:
● bullet point 1
● bullet point 2
```

A naive forward-only parser would capture just `"activity:"` instead of the full text.

### The Solution ✅

**Look BACKWARDS from the colon** to collect preceding lines:

```python
# When you find a line with a colon
if ':' in line and current_content:
    # Extract text BEFORE the colon on current line
    current_line_text = line.split(':')[0].strip()
    
    # Look BACKWARDS to collect multi-line text
    outcome_lines = []
    j = i - 1
    consecutive_empty = 0
    
    while j >= 0 and len(outcome_lines) < 4:  # Max 4 lines back
        prev_line = lines[j].strip()
        
        # Stop at 2 consecutive empty lines
        if not prev_line:
            consecutive_empty += 1
            if consecutive_empty >= 2:
                break
            j -= 1
            continue
        
        consecutive_empty = 0
        
        # Stop at bullets (marks end of PREVIOUS outcome)
        if prev_line.startswith('●') or prev_line.startswith('•'):
            break
        
        # Stop at code patterns (Level 2 codes like "1.1.1")
        if re.match(r'^\d+\.\d+\.\d+\s*$', prev_line):
            break
        
        # Stop at section headers
        if prev_line in ['Subject content', 'What students need to learn']:
            break
        
        # Stop at page markers
        if any(term in prev_line for term in ['Pearson', '©', 'Topic ']):
            break
        
        # Add this line to the BEGINNING
        outcome_lines.insert(0, prev_line)
        j -= 1
    
    # Add current line
    outcome_lines.append(current_line_text)
    
    # Combine all lines
    full_outcome = ' '.join(outcome_lines).strip()
```

### Key Stop Conditions

When looking backwards, **STOP** at:
1. **Bullet points** (`●`, `•`, `-`) - marks end of previous learning outcome
2. **Empty lines** (2 consecutive) - section break
3. **Code patterns** (e.g., `1.1.1` alone on a line) - Level 2 heading
4. **Table headers** (`Subject content`, `What students need to learn`)
5. **Page markers** (`Pearson`, `©`, `Topic X.X`)

### Testing Your Fix

Run this SQL to find problematic entries:

```sql
-- Find very short or single-word entries (likely incomplete)
SELECT topic_level, topic_code, topic_name, LENGTH(topic_name) as length
FROM staging_aqa_topics
WHERE subject_id = 'YOUR_SUBJECT_ID'
AND (LENGTH(topic_name) < 15 OR topic_name IN ('activity', 'customers', 'business', 'objectives', 'element', 'appropriate'))
ORDER BY topic_level, topic_code;
```

---

## 🔍 MULTI-LINE TOPIC TITLES (FORWARD LOOKUP)

### The Problem

**GCSE Citizenship Issue (Nov 2024):** Level 2 topic titles were truncated, showing "5 Rights, duties" instead of "5 Rights, duties and values that underpin democracy".

**Root Cause:** Topic titles often span multiple lines in the PDF before bullet points begin:

```
5 Rights, duties
and values that
underpin democracy
● bullet point 1
● bullet point 2
```

A parser that only captures the first line gets "5 Rights, duties" instead of the full title.

### The Solution ✅

**Look FORWARD from the topic number** to collect all lines until you hit a bullet point:

```python
# When you find a numbered topic
numbered_match = re.match(r'^(\d+)\s+(.+)$', line)
if numbered_match:
    num = numbered_match.group(1)
    title_parts = [numbered_match.group(2).strip()]
    
    # Look FORWARD to collect multi-line title
    j = i + 1
    while j < len(lines) and len(title_parts) < 5:  # Max 5 lines
        next_line = lines[j].strip()
        
        # Stop at empty line
        if not next_line:
            break
        
        # Stop at bullet point (title is complete!)
        if next_line.startswith('●') or next_line.startswith('•'):
            break
        
        # Stop at next numbered topic
        if re.match(r'^\d+\s+', next_line):
            break
        
        # Stop at section headers
        if next_line.endswith('?') and len(next_line) > 20:
            break
        
        # Add this line to title
        title_parts.append(next_line)
        j += 1
    
    # Combine all title parts
    full_title = ' '.join(title_parts).strip()
```

### Key Differences: Forward vs Backward

| Scenario | Direction | Stop Condition |
|----------|-----------|----------------|
| **Text before colon** (Learning outcomes) | BACKWARD ← | Stop at bullet points or empty lines |
| **Topic titles** (Numbered topics) | FORWARD → | Stop at bullet points or next topic |

### When to Use Which

- **BACKWARD lookup:** When parsing "learning outcomes" or any text that ends with a colon
- **FORWARD lookup:** When parsing topic titles that come before bullet points

---

## 📋 OTHER CRITICAL PATTERNS

### 1. Don't Truncate Content

❌ **Bad:** `title[:150]`  
✅ **Good:** `title[:500]` or no truncation

**Why:** Many topic names are long and important content gets cut off (e.g., Mathematics, PE failed because of this).

### 2. Handle Code Mismatches

Subject codes ≠ Paper codes:

**A-Level:**
- Physical Education: Subject `9PE1` → Papers `9pe0`
- Persian: Subject `9PE0` → Papers `9pn0`
- Portuguese: Subject `9PT0` → Papers `9pg0`

**GCSE:**
- All subjects use `1xxx` format (not `9xxx`)
- Drama: Subject `GCSE-Drama` → Papers `1dr0`

**Always check actual paper URLs** before assuming codes!

### 3. Try Multiple URL Years

If you find 0 papers, try different years:
- Arabic A-Level: `arabic-2017` = 0 papers, `arabic-2018` = 21 papers ✅
- GCSE French/German/Spanish: Use `2016` URLs for papers, not `2024`

### 4. Table-Based Subjects

For subjects with 2-3 column tables (Business, Economics, Geography, Psychology):

**Pattern:**
```
Topic X.X Header

Subject content          | What students need to learn
-------------------------|---------------------------
1.X.1                   | Learning outcome 1:
Content title           | ● bullet 1
                        | ● bullet 2
                        |
                        | Learning outcome 2:
                        | ● bullet 1
```

**Parsing Strategy:**
1. Find `Topic X.X` headers (Level 1)
2. Find `X.X.X` codes alone on a line
3. Collect following non-colon lines as content title (Level 2)
4. Find lines ending with `:` for learning outcomes (Level 3)
   - **Use backwards lookup for multi-line text!**
5. Skip bullet points (you usually only want the heading)

### 5. Save Debug Files

**Always** save the extracted PDF text:

```python
debug_path = Path(__file__).parent / f"debug-{subject_code}.txt"
debug_path.write_text(text, encoding='utf-8')
print(f"[OK] Saved to {debug_path.name}")
```

**Why:** You need to visually inspect the PDF structure to understand parsing issues.

---

## 🎯 DEBUGGING WORKFLOW

When a scraper produces bad results:

1. **Check the debug file** - look at raw PDF text structure
2. **Run SQL queries** - find short/incomplete entries
3. **Identify the pattern** - is it multi-line? nested tables? weird formatting?
4. **Fix incrementally** - test one section at a time
5. **Verify with SQL** - check the database, not just console output

### Useful SQL Queries

```sql
-- Count by level
SELECT topic_level, COUNT(*) as count
FROM staging_aqa_topics
WHERE subject_id = 'YOUR_SUBJECT_ID'
GROUP BY topic_level
ORDER BY topic_level;

-- Find short entries
SELECT topic_code, topic_name, LENGTH(topic_name) as len
FROM staging_aqa_topics
WHERE subject_id = 'YOUR_SUBJECT_ID'
AND LENGTH(topic_name) < 20
ORDER BY len;

-- Find entries ending oddly
SELECT topic_code, topic_name
FROM staging_aqa_topics
WHERE subject_id = 'YOUR_SUBJECT_ID'
AND (topic_name LIKE '% of' OR topic_name LIKE '% in')
ORDER BY topic_code;
```

---

## 🏆 PROVEN SCRAPERS

**Use these as templates:**

1. **Business Scraper** ⭐ - `scrapers/Edexcel/A-Level/topics/scrape-business-improved.py`
   - Best for table-based subjects
   - Handles deep hierarchies (5 levels)
   - Success rate: 100%

2. **Universal Science Scraper** - `scrapers/Edexcel/A-Level/topics/scrape-edexcel-universal.py`
   - For "Topic X:" pattern subjects
   - Good for Chemistry, Physics, Biology

3. **Manual Upload Template** - `scrapers/Edexcel/A-Level/topics/upload-*-manual.py`
   - When automation is too hard
   - 15-minute manual upload beats hours of debugging
   - Use for specialist subjects

---

## 📊 QUALITY CHECKS

Before considering a scrape complete:

- [ ] Topic counts reasonable for subject (20-200 typical)
- [ ] No single-word Level 3 entries (check with SQL)
- [ ] No truncated titles (nothing ending with `...`)
- [ ] Hierarchy makes sense (parents exist, no orphans)
- [ ] No duplicate codes
- [ ] Examined content only (skip coursework/NEA)

---

## 💡 QUICK WINS

1. **Start with debug file** - Download and save PDF text first
2. **Test on one section** - Don't process the whole PDF until pattern works
3. **Use regex sparingly** - Simple string matching often works better
4. **Console output lies** - Terminal width truncates - check database!
5. **When in doubt, go manual** - 50 topics × 20 seconds = 15 minutes

---

**Last Updated:** November 6, 2024  
**Latest Fix:** Multi-line backward lookup for GCSE Business learning outcomes

---

## 🎓 LESSONS LEARNED SUMMARY

| Issue | Symptom | Solution |
|-------|---------|----------|
| Multi-line text before colons | Single words like "activity", "business" | Look backwards from colon, stop at bullets/empty lines |
| Truncated titles | Topics end with `...` | Remove `.[:150]` truncation, use `.[:500]` or none |
| Code mismatches | 0 papers found | Check actual paper URLs, don't assume codes |
| Console looks wrong | Truncated display | Check database with SQL, not console output |
| Complex PDF layout | Parsing fails | Save debug file, inspect structure, or go manual |

---

**Remember:** 15 minutes of manual upload is better than 2 hours of debugging a scraper that keeps inventing content! 🎯

