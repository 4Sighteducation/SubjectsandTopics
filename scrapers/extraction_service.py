"""
Production Paper Extraction Service
Handles extraction of questions, mark schemes, and examiner reports
Stores results in Supabase
"""

import os
import json
import requests
import base64
import io
from pathlib import Path
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Initialize clients (lazy - only when needed)
openai_client = None
supabase = None

def get_openai_client():
    global openai_client
    if openai_client is None:
        openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    return openai_client

def get_supabase_client():
    global supabase
    if supabase is None:
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_KEY')
        )
    return supabase

def extract_pages_as_images(pdf_content: bytes, skip_pages=1) -> dict:
    """Convert PDF pages to images"""
    import pdfplumber
    from pypdfium2._helpers.misc import PdfiumError
    
    page_images = []
    
    try:
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text() or ""
                
                # Detect end of questions
                if any(phrase in page_text for phrase in [
                    'END OF QUESTION PAPER',
                    'END OF QUESTIONS',
                    'EXTRA ANSWER SPACE',
                ]):
                    break
                
                # Skip cover pages
                if page_num <= skip_pages:
                    continue
                
                # Render page to image
                page_img = page.to_image(resolution=150)
                img_bytes = io.BytesIO()
                page_img.save(img_bytes, format='PNG')
                img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
                
                page_images.append({
                    'page': page_num,
                    'base64': img_base64,
                })
    except PdfiumError as e:
        # Some PDFs (notably from certain CDNs) fail under PDFium with "Unsupported security scheme".
        # Fallback to PyMuPDF rendering, which can handle more security/encryption schemes.
        print(f"[WARN] pdfplumber/pdfium failed ({e}); falling back to PyMuPDF renderer")
        import fitz  # PyMuPDF

        doc = fitz.open(stream=pdf_content, filetype="pdf")
        for idx in range(doc.page_count):
            page_num = idx + 1

            # Skip cover pages
            if page_num <= skip_pages:
                continue

            page = doc.load_page(idx)
            page_text = page.get_text("text") or ""

            if any(phrase in page_text for phrase in [
                'END OF QUESTION PAPER',
                'END OF QUESTIONS',
                'EXTRA ANSWER SPACE',
            ]):
                break

            # Render at approx 150dpi (72 is default). 150/72 ≈ 2.08.
            mat = fitz.Matrix(150/72, 150/72)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_base64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")
            page_images.append({'page': page_num, 'base64': img_base64})
    
    return {'page_images': page_images}

def copy_paper_to_production(staging_paper_id: str) -> str:
    """Copy paper from staging to production exam_papers table"""
    sb = get_supabase_client()
    
    # Get staging paper
    staging_paper = sb.table('staging_aqa_exam_papers').select('*').eq('id', staging_paper_id).single().execute()
    
    if not staging_paper.data:
        raise Exception('Staging paper not found')
    
    sp = staging_paper.data
    
    # Get staging subject to find production equivalent
    staging_subject = sb.table('staging_aqa_subjects').select('*').eq('id', sp['subject_id']).single().execute()
    ss = staging_subject.data
    
    # Find production subject
    prod_subject = sb.table('exam_board_subjects').select('id').eq('subject_code', ss['subject_code']).maybe_single().execute()
    
    if not prod_subject.data:
        raise Exception('Production subject not found')
    
    # Insert into production exam_papers (or update if exists)
    paper_data = {
        'exam_board_subject_id': prod_subject.data['id'],
        'year': sp['year'],
        'exam_series': sp['exam_series'],
        'paper_number': sp['paper_number'],
        'question_paper_url': sp['question_paper_url'],
        'mark_scheme_url': sp['mark_scheme_url'],
        'examiner_report_url': sp['examiner_report_url'],
    }
    
    # Use staging paper ID as production ID to maintain link
    result = sb.table('exam_papers').upsert({'id': staging_paper_id, **paper_data}).execute()
    
    return staging_paper_id

def extract_questions(question_url: str, paper_id: str) -> list:
    """Extract questions from question paper PDF"""
    
    # First, ensure paper exists in production table
    copy_paper_to_production(paper_id)
    
    # Download PDF
    response = requests.get(question_url)
    response.raise_for_status()
    pdf_content = response.content
    
    # Convert to images
    pdf_data = extract_pages_as_images(pdf_content, skip_pages=1)
    page_images = pdf_data['page_images']
    
    # Build GPT-4o Vision request
    content = [{
        'type': 'text',
        'text': '''Extract ALL questions from this exam paper as JSON.

For each question with marks, return:
{
  "full_question_number": "1(a)(i)",
  "main_question_number": 1,
  "question_text": "...",
  "context_text": "...",
  "marks": 4,
  "command_word": "Describe",
  "question_type": "short_answer",
  "has_image": true,
  "image_description": "...",
  "image_page": 5
}

Return as: {"questions": [...]}'''
    }]
    
    # Add page images
    for img in page_images:
        content.append({
            'type': 'image_url',
            'image_url': {'url': f"data:image/png;base64,{img['base64']}"}
        })
    
    # Call OpenAI
    client = get_openai_client()
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[{'role': 'user', 'content': content}],
        max_tokens=16000,
        response_format={'type': 'json_object'},
    )
    
    result = json.loads(response.choices[0].message.content)
    questions = result.get('questions', [])
    
    # Store in Supabase (upsert to avoid duplicates)
    for q in questions:
        q['paper_id'] = paper_id
        
    if questions:
        sb = get_supabase_client()
        # Check if questions already exist
        existing = sb.table('exam_questions').select('id').eq('paper_id', paper_id).execute()
        
        if existing.data and len(existing.data) > 0:
            print(f"[INFO] Questions already extracted for this paper, skipping insert")
        else:
            sb.table('exam_questions').insert(questions).execute()
            print(f"[INFO] Inserted {len(questions)} questions")
    
    return questions

def extract_mark_scheme(mark_scheme_url: str, paper_id: str) -> list:
    """Extract mark scheme from PDF"""
    
    # Download PDF
    response = requests.get(mark_scheme_url)
    response.raise_for_status()
    
    # Convert to images
    pdf_data = extract_pages_as_images(response.content, skip_pages=1)
    page_images = pdf_data['page_images']
    
    # Build request
    content = [{
        'type': 'text',
        'text': '''Extract mark schemes as JSON.

For each question return:
{
  "question_number": "1(a)(i)",
  "max_marks": 1,
  "marking_points": [
    {"answer": "Ribosome", "marks": 1, "keywords": ["ribosome"]}
  ]
}

Return as: {"mark_schemes": [...]}'''
    }]
    
    for img in page_images:
        content.append({
            'type': 'image_url',
            'image_url': {'url': f"data:image/png;base64,{img['base64']}"}
        })
    
    # Call OpenAI
    client = get_openai_client()
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[{'role': 'user', 'content': content}],
        max_tokens=16000,
        response_format={'type': 'json_object'},
    )
    
    result = json.loads(response.choices[0].message.content)
    mark_schemes = result.get('mark_schemes', [])
    
    # Link to questions and store
    sb = get_supabase_client()
    questions = sb.table('exam_questions').select('*').eq('paper_id', paper_id).execute()
    question_map = {q['full_question_number']: q['id'] for q in questions.data}
    
    for ms in mark_schemes:
        q_num = ms.pop('question_number')  # Remove from dict, get value
        if q_num in question_map:
            # Build clean insert object matching schema
            insert_data = {
                'question_id': question_map[q_num],
                'max_marks': ms.get('max_marks'),
                'marking_points': ms.get('marking_points'),  # Already JSONB
                'levels': ms.get('levels'),  # Already JSONB if present
                'examiner_notes': ms.get('examiner_notes'),
                'common_errors': ms.get('common_errors', []),
            }
            sb.table('mark_schemes').insert(insert_data).execute()
    
    return mark_schemes

def mark_answer(question_id: str, user_answer: str, user_id: str, time_taken_seconds: int = 0) -> dict:
    """Mark a student's answer using AI + mark scheme"""
    
    # Get question and mark scheme
    sb = get_supabase_client()
    question = sb.table('exam_questions').select('*').eq('id', question_id).single().execute()
    mark_scheme_result = sb.table('mark_schemes').select('*').eq('question_id', question_id).maybe_single().execute()
    
    if not question.data:
        raise Exception('Question not found')
    
    q_data = question.data
    ms_data = mark_scheme_result.data if mark_scheme_result and mark_scheme_result.data else None
    
    # Build marking prompt
    prompt = f'''You are an expert examiner marking a student's answer.

Question: {q_data['question_text']} ({q_data['marks']} marks)

{f"Mark Scheme: {ms_data['marking_points']}" if ms_data else "No official mark scheme - use your expert judgment"}

Student's Answer:
{user_answer}

Award marks and provide feedback as JSON:
{{
  "marks_awarded": 0-{q_data['marks']},
  "max_marks": {q_data['marks']},
  "feedback": "Overall feedback...",
  "strengths": ["What student did well"],
  "improvements": ["How to improve"],
  "matched_points": ["Which marking points achieved"]
}}'''
    
    client = get_openai_client()
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=2000,
        response_format={'type': 'json_object'},
    )
    
    marking = json.loads(response.choices[0].message.content)
    
    # Store attempt
    sb = get_supabase_client()
    sb.table('student_attempts').insert({
        'user_id': user_id,
        'question_id': question_id,
        'user_answer': user_answer,
        'marks_awarded': marking['marks_awarded'],
        'max_marks': marking['max_marks'],
        'ai_feedback': marking['feedback'],
        'strengths': marking.get('strengths', []),
        'improvements': marking.get('improvements', []),
        'time_taken_seconds': time_taken_seconds,  # Save timer data!
    }).execute()
    
    return marking

