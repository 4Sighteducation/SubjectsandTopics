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

# Initialize clients
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)

def extract_pages_as_images(pdf_content: bytes, skip_pages=1) -> dict:
    """Convert PDF pages to images"""
    import pdfplumber
    
    page_images = []
    
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
    
    return {'page_images': page_images}

def extract_questions(question_url: str, paper_id: str) -> list:
    """Extract questions from question paper PDF"""
    
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
    response = openai_client.chat.completions.create(
        model='gpt-4o',
        messages=[{'role': 'user', 'content': content}],
        max_tokens=16000,
        response_format={'type': 'json_object'},
    )
    
    result = json.loads(response.choices[0].message.content)
    questions = result.get('questions', [])
    
    # Store in Supabase
    for q in questions:
        q['paper_id'] = paper_id
        
    if questions:
        supabase.table('exam_questions').insert(questions).execute()
    
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
    response = openai_client.chat.completions.create(
        model='gpt-4o',
        messages=[{'role': 'user', 'content': content}],
        max_tokens=16000,
        response_format={'type': 'json_object'},
    )
    
    result = json.loads(response.choices[0].message.content)
    mark_schemes = result.get('mark_schemes', [])
    
    # Link to questions and store
    questions = supabase.table('exam_questions').select('*').eq('paper_id', paper_id).execute()
    question_map = {q['full_question_number']: q['id'] for q in questions.data}
    
    for ms in mark_schemes:
        q_num = ms['question_number']
        if q_num in question_map:
            ms['question_id'] = question_map[q_num]
            ms['marking_points'] = json.dumps(ms['marking_points'])
            supabase.table('mark_schemes').insert(ms).execute()
    
    return mark_schemes

def mark_answer(question_id: str, user_answer: str, user_id: str) -> dict:
    """Mark a student's answer using AI + mark scheme"""
    
    # Get question and mark scheme
    question = supabase.table('exam_questions').select('*').eq('id', question_id).single().execute()
    mark_scheme = supabase.table('mark_schemes').select('*').eq('question_id', question_id).maybeSingle().execute()
    
    if not question.data:
        raise Exception('Question not found')
    
    q_data = question.data
    ms_data = mark_scheme.data if mark_scheme.data else None
    
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
    
    response = openai_client.chat.completions.create(
        model='gpt-4o',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=2000,
        response_format={'type': 'json_object'},
    )
    
    marking = json.loads(response.choices[0].message.content)
    
    # Store attempt
    supabase.table('student_attempts').insert({
        'user_id': user_id,
        'question_id': question_id,
        'user_answer': user_answer,
        'marks_awarded': marking['marks_awarded'],
        'max_marks': marking['max_marks'],
        'ai_feedback': marking['feedback'],
        'strengths': marking.get('strengths', []),
        'improvements': marking.get('improvements', []),
    }).execute()
    
    return marking

