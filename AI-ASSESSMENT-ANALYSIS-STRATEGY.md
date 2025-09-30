# AI Assessment Analysis Strategy

## Goal
Extract actionable insights from past papers, mark schemes, and examiner reports to dramatically improve flashcard quality and provide exam-focused feedback.

---

## The Value Proposition

### Current Flashcard Generation (Basic):
```
User: Generate cards for "History 1B Spain"
AI Prompt: "Generate history flashcards about Spain 1469-1598"
Result: Generic history questions
Quality: 6/10
```

### With Assessment Insights (Enhanced):
```
User: Generate cards for "History 1B Spain"

AI Prompt:
"Generate flashcards for History 1B: Spain in the Age of Discovery, 1469-1598

EXAM CONTEXT (from last 3 years):
- Common question types: Source analysis (30 marks), Essay (25 marks)
- Command words used: Explain, Evaluate, Assess
- Topics frequently tested: Opposition to Philip II, Spanish economy, Religious policy

MARK SCHEME PATTERNS:
- Good answers include: Specific dates, named individuals, cause-and-effect
- Point allocation: 12 marks knowledge, 12 marks analysis, 6 marks evaluation
- Examiners expect: Reference to historiography, balanced argument

COMMON MISTAKES (from examiner reports):
- Students confuse Charles V with Philip II
- Weak answers lack specific economic data
- Many write narrative instead of analysis

REAL EXAM QUESTIONS (examples):
1. 'Explain why Philip II faced opposition from the Netherlands' (30 marks)
2. 'To what extent was Spain a Great Power by 1598?' (25 marks)

Generate flashcards that:
- Match real exam question styles
- Test the content that's actually examined
- Use the same command words
- Help students avoid common mistakes
- Include mark scheme guidance for self-assessment"

Result: MUCH BETTER flashcards!
Quality: 9/10
```

---

## Implementation Strategy

### Step 1: Extract Text from PDFs (No AI cost)

```python
# extractors/pdf_text_extractor.py

import PyPDF2
from pathlib import Path

def extract_pdf_text(pdf_path: str) -> str:
    """Extract all text from a PDF."""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text
```

**Cost:** $0 (just PDF parsing)

---

### Step 2: AI Analysis of Mark Schemes

```python
# extractors/mark_scheme_analyzer.py

def analyze_mark_scheme(pdf_text: str, subject: str, year: int, 
                       paper_num: int) -> dict:
    """
    Use Claude to analyze a mark scheme and extract patterns.
    
    Returns insights about what examiners look for.
    """
    
    prompt = f'''Analyze this {subject} mark scheme from {year}.

Extract:

1. **QUESTION TYPES & MARKS:**
   - What types of questions? (MCQ, short answer, essay, source analysis, etc.)
   - Marks per question type?
   - How many of each type?

2. **COMMAND WORDS USED:**
   - List all command words (Explain, Evaluate, Assess, Compare, etc.)
   - How many marks typically for each?

3. **MARKING CRITERIA:**
   - What do Level 5 answers include?
   - What do Level 3 answers lack?
   - What gets full marks vs partial marks?

4. **COMMON MARKING POINTS:**
   - What specific content points appear frequently?
   - Any "must include" requirements?
   - Acceptable alternative answers?

5. **POINT ALLOCATIONS:**
   - How are marks distributed? (e.g., 10 for knowledge, 8 for analysis, 6 for evaluation)
   - Any patterns in mark allocation?

Return ONLY valid JSON:
{{
  "question_types": [
    {{"type": "source_analysis", "marks": 30, "count": 1}},
    {{"type": "essay", "marks": 25, "count": 2}}
  ],
  "key_command_words": ["Explain", "Evaluate", "Assess"],
  "marking_criteria": {{
    "top_level": "Detailed knowledge, sophisticated analysis, balanced evaluation",
    "mid_level": "Some knowledge, basic analysis, limited evaluation",
    "low_level": "Minimal knowledge, description only, no evaluation"
  }},
  "common_point_allocations": {{
    "knowledge": 12,
    "analysis": 12,
    "evaluation": 6
  }},
  "must_include_content": ["Specific dates", "Named individuals", "Evidence from sources"]
}}

MARK SCHEME TEXT:
{pdf_text[:12000]}'''
    
    # Call Claude
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Parse JSON response
    result = parse_ai_json(response.content[0].text)
    
    return result
```

**Cost:** ~$0.05-0.08 per mark scheme

---

### Step 3: AI Analysis of Examiner Reports

```python
# extractors/examiner_report_analyzer.py

def analyze_examiner_report(pdf_text: str, subject: str, year: int,
                           paper_num: int) -> dict:
    """Extract insights from examiner reports."""
    
    prompt = f'''Analyze this {subject} examiner report from {year}.

Extract PRACTICAL INSIGHTS that will help students:

1. **COMMON MISTAKES:**
   - What did students get WRONG?
   - What misconceptions appeared?
   - What did weak answers do?

2. **WHAT STRONG ANSWERS DID:**
   - What separated top answers?
   - What techniques did they use?
   - What content did they include?

3. **AREAS NEEDING IMPROVEMENT:**
   - What does the examiner recommend students practice?
   - What skills were lacking?
   - What content was poorly understood?

4. **PERFORMANCE STATISTICS (if mentioned):**
   - Which questions were hardest?
   - Which questions were easiest?
   - Average marks per question?

Return ONLY valid JSON:
{{
  "common_mistakes": [
    "Students confused X with Y",
    "Weak answers lacked Z"
  ],
  "strong_answers_characteristics": [
    "Used specific evidence",
    "Clear structure"
  ],
  "areas_of_improvement": [
    "Better chronology understanding",
    "More source analysis practice"
  ],
  "statistical_performance": {{
    "q1_average": "18/30",
    "q2_hardest": true
  }}
}}

EXAMINER REPORT TEXT:
{pdf_text[:12000]}'''
    
    return call_claude_and_parse(prompt)
```

**Cost:** ~$0.04-0.06 per examiner report

---

### Step 4: Question Extraction

```python
# extractors/question_extractor.py

def extract_questions(question_paper_text: str, mark_scheme_text: str,
                     subject: str, year: int, paper_num: int,
                     topic_codes: list) -> list:
    """Extract individual questions for AI training."""
    
    prompt = f'''Extract individual exam questions from this {subject} paper ({year}).

For EACH question, extract:
1. Question number (e.g., "01", "02.1")
2. Full question text
3. Marks available
4. Command word (Explain, Evaluate, etc.)
5. Corresponding mark scheme points (from the mark scheme provided)

Return array of questions as JSON:
[
  {{
    "question_number": "01",
    "question_text": "With reference to...",
    "marks_available": 30,
    "command_word": "Explain",
    "mark_scheme_points": [
      "Must reference both sources",
      "Expect discussion of..."
    ]
  }}
]

QUESTION PAPER:
{question_paper_text[:8000]}

MARK SCHEME:
{mark_scheme_text[:8000]}'''
    
    questions = call_claude_and_parse(prompt)
    
    # Add context
    for q in questions:
        q['topic_codes'] = topic_codes
        q['year'] = year
        q['paper_number'] = paper_num
    
    return questions
```

**Cost:** ~$0.08-0.10 per paper

---

## Processing Pipeline

### Incremental Processing (Recommended):

```python
# process_assessment_insights.py

def process_subject_assessment_insights(subject: str, qualification: str):
    """Process all assessment resources for one subject."""
    
    # 1. Get exam_papers from Supabase
    papers = get_exam_papers(subject, qualification)
    
    # 2. For each paper:
    for paper in papers:
        # Download PDFs if not already downloaded
        qp_path = download_if_needed(paper.question_paper_url)
        ms_path = download_if_needed(paper.mark_scheme_url)
        er_path = download_if_needed(paper.examiner_report_url)
        
        # Extract text
        qp_text = extract_pdf_text(qp_path)
        ms_text = extract_pdf_text(ms_path)
        er_text = extract_pdf_text(er_path)
        
        # Analyze with AI
        mark_insights = analyze_mark_scheme(ms_text, subject, paper.year, paper.paper_number)
        examiner_insights = analyze_examiner_report(er_text, subject, paper.year, paper.paper_number)
        questions = extract_questions(qp_text, ms_text, subject, paper.year, paper.paper_number, [...])
        
        # Upload insights to Supabase
        upload_mark_scheme_insights(paper.id, mark_insights)
        upload_examiner_report_insights(paper.id, examiner_insights)
        upload_questions(paper.id, questions)
    
    return {
        'mark_insights_count': len(papers),
        'examiner_insights_count': len(papers),
        'questions_extracted': sum(len(q) for q in all_questions)
    }
```

---

## Cost Analysis

### Per Subject (example: Biology with 9 papers):

| Task | Count | Cost Each | Total |
|------|-------|-----------|-------|
| Mark scheme analysis | 9 | $0.06 | $0.54 |
| Examiner report analysis | 9 | $0.05 | $0.45 |
| Question extraction | 9 | $0.09 | $0.81 |
| **Total per subject** | | | **$1.80** |

### For All 68 Subjects:
- **Optimistic:** $80-100 (if all have 6-9 papers)
- **Realistic:** $100-130 (some have more papers)

**Recommendation:** Start with **top 20 subjects** (~$35) to validate the approach.

---

## How This Improves Flashcards

### Enhanced AI Prompt Template:

```python
def generate_flashcard_prompt_with_assessment_insights(
    topic_code: str,
    topic_name: str,
    exam_board_subject_id: str
):
    """Build enhanced prompt with assessment insights."""
    
    # Get assessment insights from Supabase
    insights = get_assessment_insights(exam_board_subject_id, topic_code)
    
    prompt = f'''Generate 10 high-quality flashcards for {topic_name}.

CURRICULUM CONTEXT:
{get_curriculum_context(topic_code)}

EXAM INSIGHTS (from past 3 years):
Question Types:
{format_question_types(insights.mark_scheme.question_types)}

Command Words Used:
{insights.mark_scheme.key_command_words}

What Examiners Look For:
{insights.mark_scheme.marking_criteria}

COMMON MISTAKES TO AVOID:
{format_list(insights.examiner_report.common_mistakes)}

WHAT TOP ANSWERS INCLUDE:
{format_list(insights.examiner_report.strong_answers_characteristics)}

REAL EXAM QUESTIONS (examples):
{format_questions(insights.question_bank[:3])}

Generate flashcards that:
1. Match real exam question styles
2. Use the same command words  
3. Test content that's actually examined
4. Help students avoid common mistakes
5. Include self-assessment criteria from mark schemes

Format: Q&A with marking guidance.'''
    
    return prompt
```

---

## Implementation Phases

### Phase 1: Core Subjects (Week 1)
**Subjects:** History, Biology, Chemistry, Physics, Mathematics, English Lit
**Cost:** ~$12-15
**Benefit:** Validate approach, immediate quality improvement

### Phase 2: Popular Subjects (Week 2)
**Subjects:** Psychology, Sociology, Geography, Economics, Business
**Cost:** ~$10-12
**Benefit:** Cover 80% of user base

### Phase 3: Remaining Subjects (Week 3)
**Subjects:** All others
**Cost:** ~$40-50
**Benefit:** Complete coverage

### Phase 4: Annual Updates
**When:** September each year (new exams published)
**Process:** Just analyze NEW papers from latest year
**Cost:** ~$8-10/year (only new papers)

---

## Database Query Examples

### Get Insights for Flashcard Generation:

```sql
-- Get all insights for a topic
SELECT 
  ms.question_types,
  ms.key_command_words,
  ms.marking_criteria,
  er.common_mistakes,
  er.strong_answers_characteristics,
  qb.question_text,
  qb.marks_available
FROM exam_papers ep
LEFT JOIN mark_scheme_insights ms ON ms.exam_paper_id = ep.id
LEFT JOIN examiner_report_insights er ON er.exam_paper_id = ep.id
LEFT JOIN question_bank qb ON qb.exam_paper_id = ep.id
WHERE ep.exam_board_subject_id = (
  SELECT id FROM exam_board_subjects WHERE subject_name = 'History'
)
AND ep.year >= 2022
AND '1B' = ANY(qb.topic_codes)  -- Filter for Spain topic
ORDER BY ep.year DESC;
```

### Aggregate Patterns Across Years:

```sql
-- Find most common mistakes across all years
SELECT 
  unnest(common_mistakes) as mistake,
  COUNT(*) as frequency
FROM examiner_report_insights eri
JOIN exam_papers ep ON ep.id = eri.exam_paper_id
WHERE ep.exam_board_subject_id = (SELECT id FROM exam_board_subjects WHERE subject_name = 'History')
GROUP BY mistake
ORDER BY frequency DESC
LIMIT 10;
```

---

## Priority Ranking System

**Which subjects to analyze first?**

Based on:
1. **User demand** (which subjects students actually use)
2. **Complexity** (History needs this more than basic Maths)
3. **ROI** (subjects with most users get priority)

**Suggested order:**
1. History (complex, benefits hugely from exam insights)
2. English Literature (text-specific guidance valuable)
3. Sciences (exam technique matters)
4. Social Sciences (Psychology, Sociology - essay-heavy)
5. Others as usage dictates

---

## Code Structure

```
extractors/
├── pdf_text_extractor.py           # Extract text from PDFs
├── mark_scheme_analyzer.py         # AI analysis of mark schemes
├── examiner_report_analyzer.py     # AI analysis of examiner reports
└── question_extractor.py           # Extract individual questions

processors/
└── assessment_insights_processor.py # Orchestrates extraction + upload

batch_process_insights.py           # Batch process all subjects
```

---

## Example Usage in FLASH App

### When Generating Cards:

```typescript
// In your flashcard generation API
const generateFlashcards = async (topicId: string) => {
  // Get topic details
  const topic = await supabase
    .from('curriculum_topics')
    .select('*')
    .eq('id', topicId)
    .single();
  
  // Get assessment insights
  const insights = await supabase
    .from('exam_papers')
    .select(`
      *,
      mark_scheme_insights (*),
      examiner_report_insights (*),
      question_bank (*)
    `)
    .eq('exam_board_subject_id', topic.exam_board_subject_id)
    .gte('year', 2022);
  
  // Build enhanced prompt
  const prompt = buildEnhancedPrompt(topic, insights);
  
  // Generate with Claude
  const flashcards = await generateWithClaude(prompt);
  
  return flashcards;
};
```

### When Providing Feedback:

```typescript
// When student answers a flashcard
const provideFeedback = async (question: string, answer: string, topicId: string) => {
  // Get examiner insights for this topic
  const insights = await getExaminerInsights(topicId);
  
  const prompt = `
Assess this student answer using examiner standards.

Question: ${question}
Student Answer: ${answer}

EXAMINER CRITERIA:
${insights.marking_criteria}

COMMON MISTAKES TO CHECK FOR:
${insights.common_mistakes}

WHAT STRONG ANSWERS INCLUDE:
${insights.strong_answers}

Provide feedback that:
1. Uses examiner language
2. Highlights if they made common mistakes
3. Shows what would improve their answer
4. References mark scheme expectations
`;
  
  return await getClaude(prompt);
};
```

---

## Testing & Validation

### Quality Checks:

1. **Manual Review:** Sample 10 AI-extracted insights, compare with actual PDFs
2. **Accuracy:** Do extracted command words match what's in mark scheme?
3. **Completeness:** Are we missing key insights?
4. **Usefulness:** Do flashcards actually improve?

### A/B Testing:

- **Control group:** Flashcards without assessment insights
- **Test group:** Flashcards with assessment insights
- **Measure:** Student performance, engagement, satisfaction

---

## Recommended Next Steps

### This Week (After Batches Complete):

1. **Choose 3 test subjects** (e.g., History, Biology, Psychology)
2. **Process their assessment resources** with AI
3. **Generate sample flashcards** with and without insights
4. **Compare quality** - is it actually better?

### If Successful:

1. **Process top 20 subjects** (~$35)
2. **Update flashcard generation** to use insights
3. **Measure user feedback**
4. **Expand to all subjects** if validated

---

## Cost-Benefit Analysis

**Investment:**
- One-time: $100-130 for all subjects
- Annual: $8-10 to update with new exams

**Return:**
- **Better flashcards** → Higher user satisfaction
- **Exam-focused content** → Better student results
- **Competitive advantage** → "Our cards match real exam questions!"
- **Premium feature** → Could charge extra for "Exam-targeted cards"

**ROI:** If this increases user retention by even 10%, easily worth it!

---

## My Recommendation

**Start Small, Validate, Then Scale:**

**Phase 1 (This Week):**
- Process 3 subjects (History, Biology, English Lit)
- Cost: ~$5-6
- Generate sample flashcards both ways
- See if it's actually better

**Phase 2 (Next Week):**
- If validated, process top 20 subjects
- Cost: ~$35
- Roll out to beta users
- Measure engagement/satisfaction

**Phase 3 (Month 2):**
- Process all 68 subjects
- Cost: ~$100
- Full production release
- Annual updates automated

---

**Want me to build the AI extraction pipeline?** I can have Phase 1 (3 subjects) ready in 30 minutes!
