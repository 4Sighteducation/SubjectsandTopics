"""
Edexcel Mathematics (9MA0) - Table Column 3 Parser
Reads the "What students need to learn: Content" column:
  - Top statement after number = Level 2 (e.g., "1.1 Understand and use...")
  - Text below in same section = Level 3 (e.g., "Proof by deduction")

Structure:
  Level 0: Papers
  Level 1: Main Topics (1 Proof, 2 Algebra...)
  Level 2: Learning Objectives (1.1 Understand and use...)
  Level 3: Methods/Techniques (Proof by deduction, etc.)
"""

import os
import sys
import re
import requests
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv
from supabase import create_client
from pypdf import PdfReader

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT = {
    'code': '9MA0',
    'name': 'Mathematics',
    'qualification': 'A-Level',
    # Keep consistent with staging + other Edexcel scrapers
    'exam_board': 'EDEXCEL',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Mathematics/2017/specification-and-sample-assesment/a-level-l3-mathematics-specification-issue4.pdf'
}

def _looks_like_header_footer(line: str) -> bool:
    s = (line or '').strip()
    if not s:
        return True
    if 'Pearson Edexcel' in s or 'Advanced GCE' in s or 'Specification – Issue' in s:
        return True
    # page numbers (2+ digits). Don't treat single-digit topic numbers (1..9) as page numbers.
    if re.fullmatch(r'\d{2,3}', s):
        return True
    if s in {'Topics', 'Content', 'Guidance', 'Content Guidance', 'What students need to learn:', 'What students need to learn'}:
        return True
    return False


def _is_guidance_line(line: str) -> bool:
    s = (line or '').strip()
    if not s:
        return True
    # Strong signals this is Guidance column (not "Content")
    guidance_starts = (
        'Students ', 'Students\u00a0', 'Students\u2019', 'The notation', 'The equivalence',
        'A formal understanding', 'The formula', 'Hypotheses should', 'Use of ', 'Variables ',
        'Data may ', 'Change of variable', 'Understanding and use of coding', 'Measures of ',
    )
    if s.startswith(guidance_starts):
        return True
    if 'is not expected' in s or 'is not required' in s or 'are excluded' in s:
        return True
    if 'should be familiar with' in s or 'will be expected' in s:
        return True
    # "e.g." lines are usually examples/guidance
    if s.startswith('e.g') or s.startswith('Given'):
        return True
    return False


def _append_wrapped(lines_list: list[str], s: str) -> None:
    """Append a line, merging into previous item if it's a wrapped continuation."""
    if not s:
        return
    if not lines_list:
        lines_list.append(s)
        return
    # wrapped continuation: starts lowercase or is a short fragment
    if s[0].islower() or s.startswith(('and ', 'or ', 'including ', 'to ')):
        lines_list[-1] = f"{lines_list[-1]} {s}".strip()
    else:
        lines_list.append(s)


def download_pdf():
    """Download and extract PDF text."""
    print("[INFO] Downloading PDF...")
    try:
        response = requests.get(SUBJECT['pdf_url'], timeout=30)
        response.raise_for_status()
        
        pdf = PdfReader(BytesIO(response.content))
        print(f"[OK] Downloaded {len(pdf.pages)} pages")
        
        full_text = '\n'.join(page.extract_text() for page in pdf.pages)
        
        # Save debug
        Path('debug-maths-table.txt').write_text(full_text, encoding='utf-8')
        print(f"[OK] Saved debug file")
        
        return full_text
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return None


def parse_mathematics(text):
    """Parse Mathematics table - focusing on Column 3."""
    
    print("\n[INFO] Parsing Mathematics table content...")
    topics = []
    
    # Level 0: Papers
    topics.extend([
        {'code': 'Paper1', 'title': 'Paper 1: Pure Mathematics 1', 'level': 0, 'parent': None},
        {'code': 'Paper2', 'title': 'Paper 2: Pure Mathematics 2', 'level': 0, 'parent': None},
        {'code': 'Paper3', 'title': 'Paper 3: Statistics and Mechanics', 'level': 0, 'parent': None},
    ])
    
    # Level 1: Main topics
    main_topics = {
        '1': {'title': 'Proof', 'paper': 'Paper1'},
        '2': {'title': 'Algebra and functions', 'paper': 'Paper1'},
        '3': {'title': 'Coordinate geometry in the (x, y) plane', 'paper': 'Paper1'},
        '4': {'title': 'Sequences and series', 'paper': 'Paper1'},
        '5': {'title': 'Trigonometry', 'paper': 'Paper1'},
        '6': {'title': 'Exponentials and logarithms', 'paper': 'Paper1'},
        '7': {'title': 'Differentiation', 'paper': 'Paper1'},
        '8': {'title': 'Integration', 'paper': 'Paper1'},
        '9': {'title': 'Numerical methods', 'paper': 'Paper2'},
        '10': {'title': 'Vectors', 'paper': 'Paper2'},
    }
    
    for num, info in main_topics.items():
        topics.append({
            'code': f'T{num}',
            'title': f'{num} - {info["title"]}',
            'level': 1,
            'parent': info['paper']
        })
    
    print(f"[OK] Created {len(main_topics)} main topics")
    
    # Parse the table content
    lines = text.split('\n')
    
    # -------------------------------------------------------------------------
    # Paper 1 & Paper 2: Pure Mathematics
    # Important: stop before the Paper 3 table, otherwise Paper 3 rows like 2.1/3.1
    # get incorrectly attached under Paper 1 topics (e.g. T2_1).
    # -------------------------------------------------------------------------
    in_pure = False
    current_pure_topic_num = None  # 1..10
    current_pure_l2_code = None
    current_pure_l2_text = ''
    current_pure_l3_items: list[str] = []
    expecting_pure_l2_main = False
    skipped_guidance_wrap = False

    def flush_pure_l2():
        nonlocal current_pure_l2_code, current_pure_l2_text, current_pure_l3_items, expecting_pure_l2_main
        if current_pure_l2_code and current_pure_l2_text and current_pure_topic_num:
            topics.append({
                'code': current_pure_l2_code,
                'title': current_pure_l2_text,
                'level': 2,
                'parent': f'T{current_pure_topic_num}'
            })
            for idx, item in enumerate(current_pure_l3_items, 1):
                topics.append({
                    'code': f'{current_pure_l2_code}_{idx}',
                    'title': item,
                    'level': 3,
                    'parent': current_pure_l2_code
                })
        current_pure_l2_code = None
        current_pure_l2_text = ''
        current_pure_l3_items = []
        expecting_pure_l2_main = False

    def _is_paper3_header_line(line: str) -> bool:
        s = (line or '').strip()
        if not s.startswith('Paper 3: Statistics and Mechanics'):
            return False
        # Exclude change-log mentions like "Paper 3: ... , Section 2.2 – ..."
        if ',' in s or 'Section' in s:
            return False
        return True

    # Start when we hit the *actual* Paper 1/2 content table (not contents page)
    for i, raw in enumerate(lines):
        s = (raw or '').strip()

        if not in_pure:
            if 'Paper 1 and Paper 2: Pure Mathematics' in s:
                window = '\n'.join(lines[i:i+90])
                if 'What students need to learn' in window and 'Topics' in window:
                    in_pure = True
            continue

        # Stop at Paper 3 (standalone header), appendices, or admin section
        if _is_paper3_header_line(s):
            flush_pure_l2()
            break
        if s.startswith('Appendix') or 'Administration and general' in s:
            flush_pure_l2()
            break

        if _looks_like_header_footer(s):
            continue

        # Topic number (1..10) appears as standalone line
        if re.fullmatch(r'(?:10|[1-9])', s):
            flush_pure_l2()
            current_pure_topic_num = int(s)
            continue

        # Content code row: "n.m ..." (sometimes code and text split across lines)
        m = re.match(r'^(\d{1,2})\.(\d{1,2})(?:\s+(.+))?$', s)
        if m:
            major = int(m.group(1))
            minor = int(m.group(2))
            rest = (m.group(3) or '').strip()
            if major < 1 or major > 10:
                continue
            # lock current topic if not yet set
            if current_pure_topic_num is None:
                current_pure_topic_num = major
            if major != current_pure_topic_num:
                # Table sometimes continues without repeating topic number; trust the code's major.
                current_pure_topic_num = major

            flush_pure_l2()
            current_pure_l2_code = f'T{major}_{minor}'
            current_pure_l2_text = f'{major}.{minor} {rest}'.strip() if rest else ''
            current_pure_l3_items = []
            expecting_pure_l2_main = True
            skipped_guidance_wrap = False
            continue

        if current_pure_l2_code and s:
            # drop obvious guidance
            if _is_guidance_line(s):
                skipped_guidance_wrap = True
                continue
            if skipped_guidance_wrap and (s[0].islower() or s.startswith(('on ', 'and ', 'or ', 'including '))):
                # wrapped continuation of guidance we skipped
                continue
            skipped_guidance_wrap = False

            # If we have completed the main statement and see a new verb-led statement, treat as L3
            if expecting_pure_l2_main and current_pure_l2_text and current_pure_l2_text.rstrip().endswith('.') and s.startswith(start_verbs):
                expecting_pure_l2_main = False

            if expecting_pure_l2_main:
                if not current_pure_l2_text:
                    # if code was on its own line earlier
                    current_pure_l2_text = s
                else:
                    current_pure_l2_text = f'{current_pure_l2_text} {s}'.strip()
                if current_pure_l2_text.endswith('.'):
                    expecting_pure_l2_main = False
                continue

            # L3 statements (optional) - one per verb-led line; merge wrapped continuations
            _append_wrapped(current_pure_l3_items, s)
    
    # -------------------------------------------------------------------------
    # Paper 3: Statistics and Mechanics
    # The PDF extraction interleaves Content and Guidance lines; we keep Content
    # and drop obvious Guidance lines using heuristics.
    # -------------------------------------------------------------------------
    in_paper3 = False
    current_p3_topic_num = None  # 1..9
    current_p3_topic_code = None  # P3T1..P3T9
    current_p3_topic_title_parts: list[str] = []

    current_p3_l2_code = None
    current_p3_l2_text = ''
    current_p3_l3_items: list[str] = []
    expecting_p3_l2_main = False

    def flush_p3_l2():
        nonlocal current_p3_l2_code, current_p3_l2_text, current_p3_l3_items, expecting_p3_l2_main
        if current_p3_l2_code and current_p3_l2_text and current_p3_topic_code:
            topics.append({
                'code': current_p3_l2_code,
                'title': current_p3_l2_text,
                'level': 2,
                'parent': current_p3_topic_code
            })
            for idx, item in enumerate(current_p3_l3_items, 1):
                topics.append({
                    'code': f'{current_p3_l2_code}_{idx}',
                    'title': item,
                    'level': 3,
                    'parent': current_p3_l2_code
                })
        current_p3_l2_code = None
        current_p3_l2_text = ''
        current_p3_l3_items = []
        expecting_p3_l2_main = False

    def flush_p3_topic():
        nonlocal current_p3_topic_num, current_p3_topic_code, current_p3_topic_title_parts
        if current_p3_topic_num is None or current_p3_topic_code is None:
            current_p3_topic_title_parts = []
            return
        title = re.sub(r'\s+', ' ', ' '.join(current_p3_topic_title_parts)).strip()
        title = re.sub(r'\s+continued$', '', title, flags=re.IGNORECASE).strip()
        if title and not any(t['code'] == current_p3_topic_code for t in topics):
            topics.append({
                'code': current_p3_topic_code,
                'title': f'{current_p3_topic_num} - {title}',
                'level': 1,
                'parent': 'Paper3'
            })
        current_p3_topic_title_parts = []

    start_verbs = (
        'Use ', 'Understand ', 'Select ', 'Interpret ', 'Apply ', 'Conduct ', 'Connect ', 'Estimate ',
        'Calculate ', 'Represent ', 'Model ', 'Critique ', 'Compare ', 'Test '
    )

    skipped_guidance_wrap = False
    for i, raw in enumerate(lines):
        s = (raw or '').strip()

        if not in_paper3:
            # Avoid the change-log mentions like "Paper 3: ... Section 2.2 – ...".
            if s.strip() == 'Paper 3: Statistics and Mechanics':
                in_paper3 = True
            continue

        # Stop when we clearly leave Paper 3 section
        if s.startswith('Assessment Objectives') or s.startswith('3 Administration and general'):
            flush_p3_l2()
            flush_p3_topic()
            break

        # New Paper 3 topic number (1..9) appears as a standalone digit line
        if re.fullmatch(r'[1-9]', s):
            # finish previous state
            flush_p3_l2()
            flush_p3_topic()
            current_p3_topic_num = int(s)
            current_p3_topic_code = f'P3T{current_p3_topic_num}'
            current_p3_topic_title_parts = []
            continue
        
        if _looks_like_header_footer(s):
            continue

        # Collect Paper 3 topic title until we hit the first content code (e.g., 1.1)
        if current_p3_topic_num is not None and current_p3_l2_code is None:
            if re.fullmatch(rf'{current_p3_topic_num}\.\d{{1,2}}', s) or re.match(rf'^{current_p3_topic_num}\.\d{{1,2}}\s+', s):
                # We've hit first content row; ensure L1 topic row exists
                flush_p3_topic()
                # fall through to content parsing below
            else:
                # ignore stray blank/continued markers already handled above
                current_p3_topic_title_parts.append(s)
                continue

        # Paper 3 content item: "n.m" (sometimes the text is on the next line)
        content_match = re.match(r'^([1-9])\.(\d{1,2})(?:\s+(.+))?$', s)
        if content_match:
            major = int(content_match.group(1))
            minor = int(content_match.group(2))
            rest = (content_match.group(3) or '').strip()
            if current_p3_topic_num is None or major != current_p3_topic_num:
                # Ignore accidental matches outside the current table row context
                continue

            flush_p3_l2()
            current_p3_l2_code = f'P3T{major}_{minor}'
            current_p3_l2_text = f'{major}.{minor} {rest}'.strip() if rest else ''
            current_p3_l3_items = []
            # The "main statement" for the row often wraps across multiple lines,
            # even when the first line includes some text after the code.
            expecting_p3_l2_main = True
            continue

        # Collect content / level 3 for current paper3 content item
        if current_p3_l2_code and s:
            if _is_guidance_line(s):
                skipped_guidance_wrap = True
                continue
            if skipped_guidance_wrap and (s[0].islower() or s.startswith(('on ', 'and ', 'or ', 'including '))):
                # Continuation of a Guidance row we skipped (PDF wraps guidance onto next line)
                continue
            skipped_guidance_wrap = False

            # If we've already completed the main L2 sentence, and this looks like a new statement,
            # treat it as Level 3.
            if expecting_p3_l2_main and current_p3_l2_text and current_p3_l2_text.rstrip().endswith('.') and s.startswith(start_verbs):
                expecting_p3_l2_main = False

            if expecting_p3_l2_main:
                # Build the (possibly wrapped) main statement for L2
                if not current_p3_l2_text:
                    current_p3_l2_text = f'{current_p3_l2_code.replace("P3T", "").replace("_", ".")} {s}'.strip()
                else:
                    current_p3_l2_text = f'{current_p3_l2_text} {s}'.strip()
                # Once we end a sentence, allow subsequent statements to become L3
                if current_p3_l2_text.endswith('.'):
                    expecting_p3_l2_main = False
                continue

            # After L2 main statement, treat subsequent content statements as L3, merging wrapped lines
            _append_wrapped(current_p3_l3_items, s)

    # Paper 1/2 items are flushed inside the loop (via flush_pure_l2()) and Paper 3
    # items are flushed on section change (via flush_p3_l2()).
    
    # Deduplicate
    unique = []
    seen = set()
    for t in topics:
        if t['code'] not in seen:
            unique.append(t)
            seen.add(t['code'])
    
    print(f"[OK] Extracted {len(unique)} topics (deduplicated)")
    
    return unique


def upload_topics(topics):
    """Upload to Supabase."""
    
    print(f"\n[INFO] Uploading to database...")
    
    try:
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT['name']} (A-Level)",
            'subject_code': SUBJECT['code'],
            'qualification_type': 'A-Level',
            'specification_url': SUBJECT['pdf_url'],
            'exam_board': SUBJECT['exam_board']
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared old topics")
        
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'exam_board': SUBJECT['exam_board']
        } for t in topics]
        
        inserted_result = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted_result.data)} topics")
        
        code_to_id = {t['topic_code']: t['id'] for t in inserted_result.data}
        linked = 0
        
        for topic in topics:
            if topic['parent']:
                parent_id = code_to_id.get(topic['parent'])
                child_id = code_to_id.get(topic['code'])
                if parent_id and child_id:
                    supabase.table('staging_aqa_topics').update({
                        'parent_topic_id': parent_id
                    }).eq('id', child_id).execute()
                    linked += 1
        
        print(f"[OK] Linked {linked} relationships")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    # Force UTF-8 output for Windows console
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    print("=" * 80)
    print("EDEXCEL MATHEMATICS (9MA0) - TABLE COLUMN 3 PARSER")
    print("=" * 80)
    print("Extracts: Top statement = Level 2, Items below = Level 3\n")
    
    try:
        text = download_pdf()
        if not text:
            return
        
        topics = parse_mathematics(text)
        
        levels = {}
        for t in topics:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("\n[INFO] Level breakdown:")
        for level in sorted(levels.keys()):
            print(f"   Level {level}: {levels[level]} topics")
        
        print("\n[INFO] Sample topics:")
        for level in [1, 2, 3]:
            samples = [t for t in topics if t['level'] == level]
            if samples:
                print(f"   Level {level}: {samples[0]['title'][:100]}...")
        
        if upload_topics(topics):
            print("\n" + "=" * 80)
            print("[OK] MATHEMATICS COMPLETE!")
            print("=" * 80)
            print(f"Total: {len(topics)} topics, {max(levels.keys())+1} levels")
        
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()










