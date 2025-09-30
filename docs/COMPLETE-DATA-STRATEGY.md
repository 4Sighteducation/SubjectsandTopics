# Complete Data Strategy - Curriculum + Assessment Resources

## The Complete Picture

You've discovered that we need **TWO types of data** for maximum accuracy:

### 1. Curriculum Content (What to Learn)
- ✅ Subject specifications
- ✅ Topic hierarchies  
- ✅ Selection rules
- ✅ Component structure

### 2. Assessment Resources (How It's Tested) 🆕
- 🆕 Past papers (last 3 years)
- 🆕 Mark schemes (what examiners look for)
- 🆕 Examiner reports (common mistakes, advice)

**Combined = PERFECT flashcard generation!**

---

## Data Architecture

```
For Each Subject (e.g., History A-Level AQA 7042):

CURRICULUM SIDE:
├─ specification_metadata
│   └─ Overview, GLH, assessment structure
├─ spec_components  
│   └─ Component 1, 2, 3 structure
├─ selection_constraints
│   └─ British+non-British, prohibited combos
└─ curriculum_topics (3 levels)
    ├─ Level 0: Options (1A, 1B, 1C...) [30 items]
    ├─ Level 1: Study areas (Part one, Part two) [~60 items]
    └─ Level 2: Content points (bullet points) [~200 items]

ASSESSMENT SIDE: 🆕
├─ exam_papers
│   ├─ 2024 June: Paper 1, Paper 2
│   ├─ 2023 June: Paper 1, Paper 2
│   └─ 2022 June: Paper 1, Paper 2
├─ mark_scheme_insights
│   └─ AI-extracted patterns from mark schemes
├─ examiner_report_insights
│   └─ Common mistakes, strong answer traits
└─ question_bank
    └─ Individual questions extracted for AI training
```

---

## How This Enhances Your App

### Current AI Generation (Limited Context):
```
User: Generate cards for "History 1B Spain"
AI prompt: "Generate history flashcards about Spain 1469-1598"
Result: Generic history questions
```

### With Complete Data (Rich Context):
```
User: Generate cards for "History 1B Spain"

AI gets:
✅ Topic hierarchy:
  - Part one: New Monarchy 1469-1556
    - The forging of a new state
    - The drive to Great Power status
  - Part two: Philip II's Spain 1556-1598
    
✅ Key questions:
  - "What were the political issues..."
  - "To what extent did Spain become a Great Power?"
  
✅ Recent exam questions (2022-2024):
  - "Explain the reasons for revolt in the Netherlands"
  - "To what extent was Philip II successful in his foreign policy?"
  
✅ Mark scheme criteria:
  - "Good answers should include: consolidation, opposition, empire..."
  - "Expect evaluation of success/failure with evidence"
  
✅ Common mistakes (from examiner reports):
  - "Students often confuse Charles and Philip"
  - "Weak answers lack specific dates"
  
AI generates:
🎯 Exam-style questions matching real AQA format
🎯 Uses exact terminology from mark schemes
🎯 Tests content that's actually examined
🎯 Avoids common mistake patterns
🎯 Provides marking guidance for feedback

Result: MUCH BETTER FLASHCARDS!
```

---

## Subject Codes Solution

You're right - the 4-digit codes are shown on AQA website!

### Where to Find Codes:

**Method 1: From Qualifications List** (easiest!)
```
https://www.aqa.org.uk/qualifications

Shows:
- A-level History → Click → See "7042" in URL
- GCSE History (8145)
- A-level Biology (7402)
```

**Method 2: From Subject Page**
The specification URL contains it:
```
/subjects/history/a-level/history-7042/specification
                              ^^^^
```

**Method 3: Scrape from Dropdown**
The dropdown shows: "History (8145)" for GCSE, "History (7042)" for A-Level

### Pattern:
- **GCSE codes:** 8xxx
- **A-Level codes:** 7xxx  
- **AS-Level codes:** 7xxx (same family as A-Level, different component)

---

## Complete Scraping Strategy

### Phase 1: Curriculum Content (What We're Doing Now)

```
For Each Subject:
├─ Step 1: Get specification PDF → Extract metadata & constraints (AI)
├─ Step 2: Navigate to /specification/subject-content
├─ Step 3: Detect pattern (numbered vs options)
├─ Step 4: Scrape all content pages (HTML parsing)
└─ Step 5: Upload levels 0, 1, 2 to Supabase
```

**Current Status:** Working for History! ✅

### Phase 2: Assessment Resources (NEW!)

```
For Each Subject:
├─ Step 1: Navigate to /assessment-resources
├─ Step 2: Get last 3 exam series (2024 June, 2023 June, 2022 June)
├─ Step 3: For each series, download:
│   ├─ Question Papers (all components)
│   ├─ Mark Schemes (all components)
│   └─ Examiner Reports (all components)
├─ Step 4: Extract insights with AI:
│   ├─ Question types and patterns
│   ├─ Mark scheme criteria
│   ├─ Common mistakes from reports
│   └─ Individual questions for bank
└─ Step 5: Upload to exam_papers, insights tables
```

**Status:** Schema created, scraper next!

---

## Database Schema for Assessment Resources

I just created `002_assessment_resources_tables.sql` with:

### Tables:
1. **exam_papers** - Stores metadata about each paper
   - year, series, paper_number, component
   - URLs to question paper, mark scheme, examiner report
   - Links to exam_board_subject

2. **mark_scheme_insights** - AI-extracted patterns
   - Question types used
   - Key command words
   - Marking criteria
   - Point allocations

3. **examiner_report_insights** - Gold for feedback!
   - Common mistakes students make
   - What strong answers include
   - Areas needing improvement
   - Performance statistics

4. **question_bank** - Individual questions
   - Question text
   - Marks available
   - Mark scheme points
   - Topic coverage

---

## How AI Will Use This

### Generating Questions:
```python
# AI prompt with assessment resources:
f"""
Generate flashcards for History 1B Spain.

CURRICULUM CONTEXT:
- Study areas: {study_areas}
- Content points: {content_points}

EXAM PATTERN ANALYSIS (from past 3 years):
- Common question types: {question_types}
- Typical command words: {command_words}
- Mark allocation: {mark_distribution}

REAL EXAM QUESTIONS (examples):
{sample_questions_from_papers}

MARKING CRITERIA (from mark schemes):
{marking_criteria}

COMMON MISTAKES TO AVOID:
{common_mistakes_from_reports}

Generate questions that:
1. Match the real exam style
2. Test the content points
3. Use the same command words
4. Follow the marking criteria
"""
```

### Providing Feedback:
```python
# When student answers a question:
f"""
Assess this answer using examiner standards.

Question: {question}
Student Answer: {student_answer}

MARKING CRITERIA (from mark scheme):
{relevant_marking_criteria}

COMMON MISTAKES (from examiner reports):
{relevant_common_mistakes}

STRONG ANSWER TRAITS:
{strong_answer_characteristics}

Provide feedback that:
1. Matches examiner expectations
2. Highlights if they made common mistakes
3. Shows what would improve their answer
"""
```

---

## Implementation Priority

### THIS WEEK: Complete Curriculum Scraping

**Day 1-2:**
- ✅ Test web scraper with History (done!)
- ⬜ Test with Accounting (numbered pattern 3.1, 3.2)
- ⬜ Verify both patterns work
- ⬜ Upload complete hierarchical content

**Day 3-4:**
- ⬜ Scrape 10-15 major AQA subjects
- ⬜ Both GCSE and A-Level
- ⬜ Verify data quality

**Day 5-7:**
- ⬜ Add OCR scraper (similar structure)
- ⬜ Test with 5-10 OCR subjects
- ⬜ Compare with AQA data

### NEXT WEEK: Assessment Resources

**Day 8-10:**
- ⬜ Build assessment resources scraper
- ⬜ Scrape past 3 years for 5 subjects
- ⬜ Test PDF download and storage

**Day 11-14:**
- ⬜ Build AI extractors for:
  - Mark scheme analysis
  - Examiner report insights
  - Question extraction
- ⬜ Process assessment resources for all subjects

---

## Cost Estimation

### Curriculum Scraping (Web - NO AI!)
- **Cost:** $0 (pure HTML parsing!)
- **Time:** ~2 minutes per subject
- **40 subjects:** ~2 hours total

### Assessment Resources
**Download PDFs:**
- **Cost:** $0 (just bandwidth)
- **Time:** ~5 minutes per subject (3 years × 2-3 papers each)
- **Storage:** ~100MB per subject

**AI Analysis:**
- **Mark schemes:** ~$0.10 per paper
- **Examiner reports:** ~$0.05 per report
- **Total for 40 subjects:** ~$15-20

**TOTAL COST:** ~$15-20 for complete data!
**TOTAL TIME:** ~1 week of automated running

---

## Next Immediate Steps

Want me to:

**Option A: Verify Complete History Data** ⭐️
- Save full History extraction to file
- Check we got ALL levels properly
- Upload complete hierarchy to Supabase
- Show you example in database

**Option B: Test Accounting Pattern**
- Run scraper on Accounting (3.1, 3.2 pattern)
- Verify numbered sections work
- Prove both patterns handled

**Option C: Build Assessment Resources Scraper**
- Create scraper for past papers
- Download question papers, mark schemes, reports
- Test with one subject

**Which excites you most?** We can do all eventually, but which first? 🚀
