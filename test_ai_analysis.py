#!/usr/bin/env python
"""
Test AI Analysis of Assessment Resources
Quick test with Accounting papers already in Supabase
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import PyPDF2
import anthropic

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

from database.supabase_client import SupabaseUploader

load_dotenv()


def extract_pdf_text(pdf_url: str) -> str:
    """Download and extract text from PDF."""
    import requests
    from io import BytesIO
    
    print(f"  Downloading PDF...")
    response = requests.get(pdf_url, timeout=60)
    
    pdf_file = BytesIO(response.content)
    reader = PyPDF2.PdfReader(pdf_file)
    
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    
    return text


def analyze_mark_scheme(text: str, subject: str, year: int, paper: int) -> dict:
    """Analyze mark scheme with AI."""
    
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    prompt = f'''Analyze this {subject} mark scheme from {year} Paper {paper}.

Extract exam patterns that will help generate better flashcards:

1. QUESTION TYPES: What types appear? (essay, source analysis, calculation, etc.)
2. COMMAND WORDS: List all (Explain, Evaluate, Calculate, etc.)
3. MARK ALLOCATION: How are marks distributed?
4. WHAT EXAMINERS LOOK FOR: What gets full marks vs partial?

Return ONLY valid JSON:
{{
  "question_types": [{{"type": "essay", "marks": 25}}],
  "key_command_words": ["Explain", "Evaluate"],
  "marking_criteria": "What top answers include",
  "common_point_allocations": {{"knowledge": 10, "analysis": 10}}
}}

MARK SCHEME (first 8000 chars):
{text[:8000]}'''
    
    print(f"  Analyzing with AI... (costs ~$0.06)")
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Parse JSON
    result_text = response.content[0].text.strip()
    
    # Extract JSON
    if '{' in result_text:
        start = result_text.find('{')
        end = result_text.rfind('}') + 1
        result_text = result_text[start:end]
    
    import json
    return json.loads(result_text)


def analyze_examiner_report(text: str, subject: str, year: int, paper: int) -> dict:
    """Analyze examiner report with AI."""
    
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    prompt = f'''Analyze this {subject} examiner report from {year} Paper {paper}.

Extract insights to help students improve:

1. COMMON MISTAKES: What did students get wrong?
2. STRONG ANSWERS: What did top students do?
3. EXAMINER ADVICE: What should students practice?

Return ONLY valid JSON:
{{
  "common_mistakes": ["Mistake 1", "Mistake 2"],
  "strong_answers_characteristics": ["Trait 1", "Trait 2"],
  "areas_of_improvement": ["Practice X", "Study Y"]
}}

EXAMINER REPORT (first 8000 chars):
{text[:8000]}'''
    
    print(f"  Analyzing with AI... (costs ~$0.05)")
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    
    result_text = response.content[0].text.strip()
    
    if '{' in result_text:
        start = result_text.find('{')
        end = result_text.rfind('}') + 1
        result_text = result_text[start:end]
    
    import json
    return json.loads(result_text)


def extract_questions(qp_text: str, ms_text: str, subject: str, year: int, paper: int) -> list:
    """Extract individual questions from question paper."""
    
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    prompt = f'''Analyze this {subject} exam paper from {year} Paper {paper}.

Extract EVERY question as a separate entry.

For EACH question, provide:
1. Question number (e.g., "01", "14.1")
2. Full question text
3. Marks available
4. Command word (Calculate, Explain, Evaluate, etc.)
5. Key mark scheme points (from mark scheme provided)

Return array of questions as JSON:
[
  {{
    "question_number": "14.1",
    "question_text": "Calculate the material usage variance...",
    "marks_available": 3,
    "command_word": "Calculate",
    "mark_scheme_points": ["Must flex budget", "Label as favorable/adverse"]
  }}
]

QUESTION PAPER (sending 40,000 chars to capture ALL questions):
{qp_text[:40000]}

MARK SCHEME (first 30,000 chars for complete mark points):
{ms_text[:30000]}'''
    
    print(f"  Extracting questions with AI... (costs ~$0.10)")
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=8192,  # Increased for more questions
        messages=[{"role": "user", "content": prompt}]
    )
    
    result_text = response.content[0].text.strip()
    
    if '{' in result_text or '[' in result_text:
        # Find JSON array
        if '[' in result_text:
            start = result_text.find('[')
            end = result_text.rfind(']') + 1
            result_text = result_text[start:end]
    
    import json
    return json.loads(result_text)


def main():
    """Test with Accounting papers."""
    
    print("=" * 80)
    print("COMPLETE AI ASSESSMENT ANALYSIS TEST - Accounting")
    print("=" * 80)
    
    uploader = SupabaseUploader()
    
    # Get Accounting exam papers from Supabase
    print("\n1. Getting Accounting papers from Supabase...")
    
    accounting_subject_id = uploader._get_or_create_exam_board_subject('AQA', 'Accounting', 'A-Level', '7127')
    
    # Get ALL Accounting papers (not just 1)
    papers = uploader.client.table('exam_papers').select('*').eq(
        'exam_board_subject_id', accounting_subject_id
    ).order('year', desc=True).execute()
    
    if not papers.data:
        print("ERROR: No papers found in Supabase")
        return 1
    
    print(f"\nFound {len(papers.data)} Accounting papers in Supabase")
    print("\nProcessing ALL papers...\n")
    
    total_questions = 0
    
    for idx, paper in enumerate(papers.data, 1):
        print("=" * 80)
        print(f"PAPER {idx}/{len(papers.data)}: {paper['year']} {paper['exam_series']} Paper {paper['paper_number']}")
        print("=" * 80)
    
        # Analyze mark scheme
        if paper.get('mark_scheme_url'):
            print("\n2. Analyzing mark scheme...")
            try:
                ms_text = extract_pdf_text(paper['mark_scheme_url'])
                print(f"  Extracted {len(ms_text)} characters")
                
                ms_insights = analyze_mark_scheme(ms_text, 'Accounting', paper['year'], paper['paper_number'])
                
                print("\n  INSIGHTS:")
                print(f"  - Question types: {ms_insights.get('question_types', [])}")
                print(f"  - Command words: {ms_insights.get('key_command_words', [])}")
                
                # Upload to Supabase
                print("\n3. Uploading mark scheme insights to Supabase...")
                uploader.client.table('mark_scheme_insights').insert({
                    'exam_paper_id': paper['id'],
                    'question_types': ms_insights.get('question_types'),
                    'key_command_words': ms_insights.get('key_command_words', []),
                    'marking_criteria': ms_insights.get('marking_criteria'),
                    'common_point_allocations': ms_insights.get('common_point_allocations'),
                    'ai_model_used': 'claude-3-5-sonnet'
                }).execute()
                
                print("  ✓ Uploaded!")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
    
        # Analyze examiner report
        if paper.get('examiner_report_url'):
            print("\n4. Analyzing examiner report...")
            try:
                er_text = extract_pdf_text(paper['examiner_report_url'])
                print(f"  Extracted {len(er_text)} characters")
                
                er_insights = analyze_examiner_report(er_text, 'Accounting', paper['year'], paper['paper_number'])
                
                print("\n  INSIGHTS:")
                print(f"  - Common mistakes: {len(er_insights.get('common_mistakes', []))} found")
                for mistake in er_insights.get('common_mistakes', [])[:3]:
                    print(f"    • {mistake}")
                
                # Upload to Supabase
                print("\n5. Uploading examiner report insights to Supabase...")
                uploader.client.table('examiner_report_insights').insert({
                    'exam_paper_id': paper['id'],
                    'common_mistakes': er_insights.get('common_mistakes', []),
                    'strong_answers_characteristics': er_insights.get('strong_answers_characteristics', []),
                    'areas_of_improvement': er_insights.get('areas_of_improvement', []),
                    'full_report_text': er_text[:5000],  # Store first 5000 chars
                    'ai_model_used': 'claude-3-5-sonnet'
                }).execute()
                
                print("  ✓ Uploaded!")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
    
        # Extract questions from question paper
        if paper.get('question_paper_url') and paper.get('mark_scheme_url'):
            print("\n6. Extracting individual questions...")
            try:
                qp_text = extract_pdf_text(paper['question_paper_url'])
                ms_text = extract_pdf_text(paper['mark_scheme_url'])
                
                print(f"  Question paper: {len(qp_text)} characters")
                print(f"  Mark scheme: {len(ms_text)} characters")
                
                questions = extract_questions(qp_text, ms_text, 'Accounting', paper['year'], paper['paper_number'])
                
                print(f"\n  EXTRACTED {len(questions)} QUESTIONS:")
                for i, q in enumerate(questions[:5], 1):
                    print(f"\n  Question {q.get('question_number')}:")
                    print(f"    Marks: {q.get('marks_available')}")
                    print(f"    Command: {q.get('command_word')}")
                    print(f"    Text: {q.get('question_text', '')[:100]}...")
                    if q.get('mark_scheme_points'):
                        print(f"    Mark points: {len(q.get('mark_scheme_points'))} points")
                
                if len(questions) > 5:
                    print(f"\n  ... and {len(questions) - 5} more questions")
                
                # Upload to Supabase
                print("\n7. Uploading questions to Supabase...")
                for q in questions:
                    try:
                        uploader.client.table('question_bank').insert({
                            'exam_paper_id': paper['id'],
                            'question_number': q.get('question_number'),
                            'question_text': q.get('question_text'),
                            'marks_available': q.get('marks_available'),
                            'command_word': q.get('command_word'),
                            'mark_scheme_points': q.get('mark_scheme_points', [])
                        }).execute()
                    except Exception as e:
                        print(f"  Error uploading Q{q.get('question_number')}: {e}")
                
                print(f"  ✓ Uploaded {len(questions)} questions!")
                total_questions += len(questions)
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                import traceback
                traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("ALL ACCOUNTING PAPERS ANALYZED!")
    print("=" * 80)
    print(f"Papers processed: {len(papers.data)}")
    print(f"Total questions extracted: {total_questions}")
    print(f"Total cost: ~${len(papers.data) * 0.21:.2f}")
    print("\nCheck Supabase:")
    print("SELECT COUNT(*) FROM mark_scheme_insights;")
    print("SELECT COUNT(*) FROM examiner_report_insights;")  
    print("SELECT COUNT(*) FROM question_bank;")
    print("\nAll insights are linked via exam_paper_id!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
