"""
Production Paper Extraction Service
Handles extraction of questions, mark schemes, and examiner reports
Stores results in Supabase
"""

import os
import json
import re
import requests
import base64
import io
from urllib.parse import urlparse
from pathlib import Path
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Initialize clients (lazy - only when needed)
openai_client = None
supabase = None

def normalize_question_number(s: str) -> str:
    """
    Normalize question identifiers so GCSE formats like '01.1' match '1.1'.
    Also removes whitespace and a leading 'Question' label.
    """
    if not s:
        return ''
    s = str(s).strip()
    s = re.sub(r'^(question)\s*', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\s+', '', s)
    # Remove leading zeros in numeric groups (e.g. 01.1 -> 1.1)
    s = re.sub(r'^0+(\d)', r'\1', s)
    s = re.sub(r'(?<=\D)0+(\d)', r'\1', s)
    return s

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


def _download_pdf_bytes(url: str, *, timeout: int = 60, retries: int = 4) -> bytes:
    """
    Download PDFs in a way that survives common exam-board anti-bot rules.
    CCEA in particular can return 403 unless we look like a normal browser.
    """
    last_err: Exception | None = None
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    host = (parsed.netloc or "").lower()

    # Browser-like headers (keep minimal, but enough for most WAFs)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf;q=0.8,*/*;q=0.7",
        "Accept-Language": "en-GB,en;q=0.9",
        "Referer": base + "/",
        "Connection": "keep-alive",
        # Some WAFs behave better when the client advertises modern encoding support.
        "Accept-Encoding": "gzip, deflate, br",
    }

    sess = requests.Session()
    sess.headers.update(headers)

    def _validate_pdf_bytes(content: bytes, status_code: int) -> bytes:
        if content[:4] != b"%PDF":
            snippet = content[:200].decode("utf-8", errors="ignore")
            raise RuntimeError(f"Downloaded content is not a PDF (got {status_code}). Snippet: {snippet}")
        return content

    def _download_with_cloudscraper() -> bytes:
        """
        CCEA commonly sits behind Cloudflare and blocks datacenter IPs / non-browser clients.
        cloudscraper can sometimes solve the challenge and return the actual PDF.
        """
        try:
            import cloudscraper  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "CCEA download blocked (403). cloudscraper is not installed on the server. "
                "Add 'cloudscraper' to scrapers/requirements.txt and redeploy Railway."
            ) from e

        scraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "desktop": True,
            }
        )
        scraper.headers.update(headers)

        # Warm-up request: some CF setups issue cookies on the homepage.
        try:
            scraper.get(base + "/", timeout=timeout, allow_redirects=True)
        except Exception:
            # Non-fatal: proceed to direct PDF request
            pass

        resp2 = scraper.get(url, timeout=timeout, allow_redirects=True)
        if resp2.status_code == 403:
            # Include a tiny header sample for debugging in Railway logs
            cf_ray = resp2.headers.get("cf-ray")
            server = resp2.headers.get("server")
            raise RuntimeError(
                f"403 Forbidden (source site blocked download): {url}"
                + (f" [server={server} cf-ray={cf_ray}]" if (server or cf_ray) else "")
            )
        resp2.raise_for_status()
        return _validate_pdf_bytes(resp2.content, resp2.status_code)

    for attempt in range(1, retries + 1):
        try:
            resp = sess.get(url, timeout=timeout, allow_redirects=True)
            # If blocked, surface a clearer error message for the app.
            if resp.status_code == 403:
                # CCEA is frequently Cloudflare-protected; try a Cloudflare-aware client before failing.
                if "ccea.org.uk" in host:
                    print(f"[WARN] 403 from CCEA, trying Cloudflare-aware downloader: {url}")
                    return _download_with_cloudscraper()
                raise RuntimeError(f"403 Forbidden (source site blocked download): {url}")
            resp.raise_for_status()
            return _validate_pdf_bytes(resp.content, resp.status_code)
        except Exception as e:
            last_err = e
            # exponential backoff (caps at 20s)
            import time

            time.sleep(min(2**attempt, 20))

    raise RuntimeError(f"PDF download failed after retries: {url} ({last_err})") from last_err

def extract_questions(question_url: str, paper_id: str) -> list:
    """Extract questions from question paper PDF"""
    
    # First, ensure paper exists in production table
    copy_paper_to_production(paper_id)
    
    # Download PDF
    pdf_content = _download_pdf_bytes(question_url, timeout=90, retries=4)
    
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

    def _sanitize_string(s: str) -> str:
        # Postgres TEXT cannot contain null bytes; PDFs sometimes yield them.
        s = s.replace('\x00', '')
        # Also strip other invisible control chars (keep \n, \t, \r)
        s = re.sub(r'[\x01-\x08\x0B\x0C\x0E-\x1F\x7F]', '', s)
        return s

    def sanitize(obj):
        if obj is None:
            return None
        if isinstance(obj, str):
            return _sanitize_string(obj)
        if isinstance(obj, list):
            return [sanitize(x) for x in obj]
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        return obj

    # Sanitize all extracted content before inserting into Supabase
    questions = sanitize(questions)
    
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
            try:
                sb.table('exam_questions').insert(questions).execute()
            except Exception as e:
                # Add a tiny bit of debugging to pinpoint problematic rows if sanitization ever misses something
                bad = [q for q in questions if any(isinstance(v, str) and '\x00' in v for v in q.values())]
                if bad:
                    print(f"[WARN] Found {len(bad)} question rows still containing null bytes after sanitize")
                raise
            print(f"[INFO] Inserted {len(questions)} questions")
    
    return questions

def extract_mark_scheme(mark_scheme_url: str, paper_id: str) -> list:
    """Extract mark scheme from PDF"""
    
    # Download PDF
    pdf_content = _download_pdf_bytes(mark_scheme_url, timeout=90, retries=4)
    
    # Convert to images
    pdf_data = extract_pages_as_images(pdf_content, skip_pages=1)
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
    # Build maps with normalized keys to handle GCSE formats like 01.1 vs 1.1
    question_map = {q['full_question_number']: q['id'] for q in questions.data}
    question_map_norm = {}
    for q in questions.data:
        key = normalize_question_number(q.get('full_question_number'))
        if key and key not in question_map_norm:
            question_map_norm[key] = q['id']
    
    for ms in mark_schemes:
        q_num = ms.pop('question_number')  # Remove from dict, get value
        matched_id = None
        if q_num in question_map:
            matched_id = question_map[q_num]
        else:
            q_norm = normalize_question_number(q_num)
            matched_id = question_map_norm.get(q_norm)

        if matched_id:
            # Build clean insert object matching schema
            insert_data = {
                'question_id': matched_id,
                'max_marks': ms.get('max_marks'),
                'marking_points': ms.get('marking_points'),  # Already JSONB
                'levels': ms.get('levels'),  # Already JSONB if present
                'examiner_notes': ms.get('examiner_notes'),
                'common_errors': ms.get('common_errors', []),
            }
            sb.table('mark_schemes').insert(insert_data).execute()
        else:
            # Helpful debug for cases where numbering formats don't match
            print(f"[WARN] Mark scheme question_number did not match any extracted question: {q_num}")
    
    return mark_schemes

def extract_examiner_report(examiner_report_url: str, paper_id: str) -> dict:
    """Extract examiner report insights and store them in examiner_insights."""
    if not examiner_report_url:
        return {'inserted': 0, 'skipped': True, 'reason': 'no_url'}

    sb = get_supabase_client()

    # Skip if insights already exist (avoid duplicate inserts)
    existing = sb.table('examiner_insights').select('id').eq('paper_id', paper_id).limit(1).execute()
    if existing.data and len(existing.data) > 0:
        print("[INFO] Examiner insights already exist for this paper, skipping insert")
        return {'inserted': 0, 'skipped': True, 'reason': 'already_exists'}

    # Download PDF
    pdf_content = _download_pdf_bytes(examiner_report_url, timeout=90, retries=4)

    # Convert pages to images (skip cover)
    pdf_data = extract_pages_as_images(pdf_content, skip_pages=1)
    page_images = pdf_data['page_images']

    client = get_openai_client()
    content = [
        {
            'type': 'text',
            'text': """You are an expert at analyzing examiner reports.

Extract insights from this examiner report.

Examiner reports contain:
- General commentary on how students performed
- Question-by-question analysis
- Common errors students made
- Examples of good answers
- Advice for future students

For each question mentioned in the report, extract:
1. question_number: "1(a)(i)", "2(b)", etc.
2. average_performance: "poor", "satisfactory", "good", "excellent"
3. common_errors: Array of mistakes students commonly made
4. good_practice: Array of things strong students did well
5. advice_for_students: Actionable advice for improving
6. examiner_comments: Key quotes/summaries from the report

Return JSON:
{
  "general_comments": "Overall students performed...",
  "question_insights": [
    {
      "question_number": "1(a)(i)",
      "average_performance": "good",
      "common_errors": [],
      "good_practice": [],
      "advice_for_students": "",
      "examiner_comments": ""
    }
  ]
}

I'm providing full-page images of the examiner report."""
        }
    ]

    for page_img in page_images:
        content.append({
            'type': 'image_url',
            'image_url': {'url': f"data:image/png;base64,{page_img['base64']}"}
        })

    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[{'role': 'user', 'content': content}],
        max_tokens=16000,
        response_format={'type': 'json_object'},
    )

    insights = json.loads(response.choices[0].message.content)
    question_insights = insights.get('question_insights', []) or []
    general_comments = insights.get('general_comments')

    # Build question map
    questions = sb.table('exam_questions').select('id, full_question_number').eq('paper_id', paper_id).execute()
    question_map_norm = {}
    for q in questions.data or []:
        key = normalize_question_number(q.get('full_question_number'))
        if key and key not in question_map_norm:
            question_map_norm[key] = q['id']

    inserts = []
    if general_comments:
        inserts.append({
            'paper_id': paper_id,
            'question_id': None,
            'examiner_comments': general_comments,
        })

    for qi in question_insights:
        qnum = qi.get('question_number')
        qid = question_map_norm.get(normalize_question_number(qnum))
        if not qid:
            print(f"[WARN] Examiner report insight question_number did not match any extracted question: {qnum}")
            continue
        perf = (qi.get('average_performance') or '').strip().lower()
        inserts.append({
            'paper_id': paper_id,
            'question_id': qid,
            'average_mark': None,
            'common_errors': qi.get('common_errors') or [],
            'good_practice_examples': qi.get('good_practice') or [],
            'advice_for_students': qi.get('advice_for_students'),
            'examiner_comments': (f"Performance: {perf}\n" if perf else "") + (qi.get('examiner_comments') or ''),
        })

    if inserts:
        sb.table('examiner_insights').insert(inserts).execute()

    return {'inserted': len(inserts), 'skipped': False}

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

    # If we don't have a mark scheme and this looks like a tick-box/MCQ/diagram question,
    # do NOT guess. Return an explicit self-mark instruction.
    q_text = (q_data.get('question_text') or '')
    is_mcq_like = bool(re.search(r"tick\s*\(?.*?\)?\s*one\s*box|tick\s+one\s+box|multiple\s+choice", q_text, re.IGNORECASE))
    is_diagram_like = bool(q_data.get('has_image')) and not q_data.get('image_url')
    if ms_data is None and (is_mcq_like or is_diagram_like):
        max_marks = int(q_data.get('marks') or 0)
        marking = {
            'marks_awarded': 0,
            'max_marks': max_marks,
            'feedback': 'Unable to mark accurately for this tick-box/diagram question without an extracted mark scheme. Please self-mark using the PDF/mark scheme.',
            'strengths': [],
            'improvements': [],
            'matched_points': [],
            'needs_self_mark': True,
        }
        # Store attempt as 0 marks to ensure attempt exists; user can overwrite by self-mark in the app.
        sb.table('student_attempts').insert({
            'user_id': user_id,
            'question_id': question_id,
            'user_answer': user_answer,
            'marks_awarded': marking['marks_awarded'],
            'max_marks': marking['max_marks'],
            'ai_feedback': marking['feedback'],
            'strengths': [],
            'improvements': [],
            'time_taken_seconds': time_taken_seconds,
        }).execute()
        return marking
    
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

