# GCSE PROPER SCRAPING PLAN - Applying A-Level Lessons

## **What I Learned From Last Night's Failure:**

❌ **Don't** use generic pattern matching  
❌ **Don't** truncate content  
❌ **Don't** ignore table structures  
❌ **Don't** include non-examined components  

✅ **DO** use proven Business scraper for tables  
✅ **DO** preserve full content (500+ chars)  
✅ **DO** parse multi-column tables properly  
✅ **DO** focus ONLY on examined content  

---

## **GCSE Subject Categories & Approach:**

### **Category 1: Table-Based (Use Business Template)** - 8 subjects
→ **Business, Geography A, Geography B, Psychology, Religious Studies A/B, Citizenship**

**Approach:**
- Copy `scrape-business-improved.py`
- Update subject code + PDF URL
- Parse 2-3 column tables
- Extract themes from Contents
- Build 4-5 level hierarchies
- **NO truncation**

**Expected:** 200-500 topics each

---

### **Category 2: Sciences (Use Universal Template)** - 2 subjects
→ **Combined Science, Astronomy**

**Approach:**
- Copy `scrape-edexcel-universal.py`
- Adapt for "Topic X:" pattern
- 3-4 level hierarchies

**Expected:** 100-200 topics each

---

### **Category 3: Languages (Manual Upload)** - 14 subjects
→ **All languages (Arabic through Urdu)**

**Approach:**
- Copy A-Level language manual templates
- GCSE languages have simpler structure (fewer themes)
- Preserve native text + English
- 3-4 level hierarchies

**Expected:** 20-40 topics each

---

### **Category 4: Examined Components Only (Manual)** - 6 subjects
→ **Drama, Art, Music, English Lang, English Lit, Design & Tech**

**Approach:**
- Manual upload focusing ONLY on examined content
- Drama GCSE: Component 3 only (12 prescribed texts)
- English Lit: Prescribed texts only
- Art/Music: Components structure

**Expected:** 15-50 topics each

---

### **Category 5: Maths & Computer Science (Special)** - 2 subjects

**Approach:**
- Maths: Similar to A-Level but simpler
- CompSci: Table-based, use Business template

**Expected:** 50-100 topics each

---

## **Immediate Action Plan:**

**Phase 1 (30 mins): Fix The Worst Offenders**
1. Re-scrape Geography A using Business template → 300+ topics
2. Re-scrape Geography B using Business template → 300+ topics  
3. Re-scrape Business using Business template → 200+ topics
4. Re-scrape Psychology using Business template → 200+ topics

**Phase 2 (1 hour): Sciences & Maths**
5. Science using universal scraper
6. Astronomy using universal scraper
7. Maths using adapted A-Level approach
8. Computer Science using Business template

**Phase 3 (1 hour): Quick Manual Uploads**
9. Drama (Component 3 with 12 texts)
10. Religious Studies A/B
11. Citizenship
12. Statistics

**Phase 4 (2 hours): Languages**
13. Adapt A-Level language templates for GCSE structure
14. Upload all 14 languages

**Total: 4-5 hours for QUALITY GCSE dataset**

---

## **Ready to Start?**

I'll now:
1. Create proper Business-template scrapers for table subjects
2. Run them with FULL content extraction
3. Build deep hierarchies
4. Show you real results

**Shall I continue and fix this properly?**

