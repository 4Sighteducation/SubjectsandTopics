"""
Edexcel Physical Education (9PE1) - Complete Deep Hierarchy Scraper
Extracts 5 levels: Components → Topics → Subtopics → Learning Points → Details

Structure:
Level 0: Components (Component 1, 2, 3, 4)
Level 1: Topics (1.1 Muscular, 1.2 Cardio-respiratory)
Level 2: Subtopics (1.1.1, 1.1.2, 1.1.3)
Level 3: Learning points (from embedded tables and bullets)
Level 4: Specific details (table rows, sub-bullets)
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
    'code': '9PE1',
    'name': 'Physical Education',
    'qualification': 'A-Level',
    # Keep consistent with staging (we standardise this to uppercase elsewhere)
    'exam_board': 'EDEXCEL',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Physical%20Education/2016/Specification%20and%20sample%20assessments/a-level-pe-specification.pdf'
}

def _looks_like_footer_or_header(line: str) -> bool:
    s = (line or '').strip()
    if not s:
        return True
    if 'Pearson Edexcel' in s or 'Advanced GCE' in s:
        return True
    if s in {'Content', 'Subject content', 'What students need to learn'}:
        return True
    if re.fullmatch(r'\d{1,3}', s):
        return True
    return False


def _is_new_topic_line(line: str) -> bool:
    return bool(re.match(r'^[1-4]\.\d{1,2}\s+\S', (line or '').strip()))


def _is_new_subtopic_line(line: str) -> bool:
    return bool(re.match(r'^[1-4]\.\d{1,2}\.\d{1,2}\s+\S', (line or '').strip()))


def _is_learning_or_bullet_line(line: str) -> bool:
    s = (line or '').strip()
    return bool(re.match(r'^[a-z]\)\s+\S', s) or re.match(r'^o\s+\S', s))


def _collect_continuation_lines(lines, start_idx: int, max_lines: int = 12) -> str:
    """
    Join wrapped title lines from the PE spec table.
    Stop when we hit a new topic/subtopic/bullet marker, a component header, or obvious header/footer noise.
    """
    parts = []
    for j in range(start_idx, min(start_idx + max_lines, len(lines))):
        nxt = (lines[j] or '').strip()
        if _looks_like_footer_or_header(nxt):
            break
        if nxt.startswith('Component '):
            break
        if _is_new_subtopic_line(nxt) or _is_new_topic_line(nxt) or _is_learning_or_bullet_line(nxt):
            break
        if nxt.lower() in {'subject content', 'what students need to learn'}:
            break
        parts.append(nxt)
    return ' '.join(parts).strip()


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
        Path('debug-pe-complete.txt').write_text(full_text, encoding='utf-8')
        print(f"[OK] Saved debug file")
        
        return full_text
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return None


def parse_pe_topics(text):
    """Parse PE topics with COMPLETE deep hierarchy."""
    
    print("\n[INFO] Parsing Physical Education with deep hierarchy...")
    topics = []

    # Bullet code generation must be stable across re-scrapes so diffs are meaningful.
    # We assign bullet codes per subtopic (not globally), in the order encountered.
    bullet_index_by_subtopic = {}
    
    # Level 0: Components (from Contents or headers)
    components = [
        {'code': 'Comp1', 'title': 'Component 1: Scientific Principles of Physical Education', 'level': 0, 'parent': None},
        {'code': 'Comp2', 'title': 'Component 2: Psychological and Social Principles of Physical Education', 'level': 0, 'parent': None},
        {'code': 'Comp3', 'title': 'Component 3: Practical Performance', 'level': 0, 'parent': None},
        {'code': 'Comp4', 'title': 'Component 4: Performance Analysis and Performance Development Programme', 'level': 0, 'parent': None},
    ]
    topics.extend(components)
    
    lines = text.split('\n')
    
    # Track current context
    current_component = None
    current_topic = None
    current_subtopic = None
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Level 1: Topics (1.1 Muscular..., 1.5 Newton’s..., etc.)
        # IMPORTANT:
        # Do NOT over-restrict the title charset; PE headings include punctuation like apostrophes/colons.
        # We only require: "X.Y<space><non-empty>", and we avoid matching subtopics (X.Y.Z) because those have a dot.
        topic_match = re.match(r'^([1-4])\.(\d{1,2})\s+(.+?)$', line_stripped)
        if topic_match:
            comp_num = topic_match.group(1)
            topic_num = topic_match.group(2)
            raw_title = topic_match.group(3).strip()

            # Some PDF-extracted lines incorrectly merge the next subtopic onto the same line, e.g.:
            # "2.4 Linear motion 2.4.1 Knowledge and understanding..."
            # Keep ONLY the "2.4 <title>" part on the Level-1 row, and emit the embedded "2.4.1 ..." as a Level-2 row.
            embedded_subtopic = re.search(r'\b([1-4])\.(\d{1,2})\.(\d{1,2})\s+(.+)$', raw_title)
            embedded_subtopic_obj = None
            title = raw_title
            if embedded_subtopic:
                # Only split if the embedded subtopic matches this topic's comp/topic prefix
                if embedded_subtopic.group(1) == comp_num and embedded_subtopic.group(2) == topic_num:
                    split_at = embedded_subtopic.start()
                    title = raw_title[:split_at].strip()
                    sub_num = embedded_subtopic.group(3)
                    sub_rest = embedded_subtopic.group(4).strip()
                    if sub_rest:
                        embedded_subtopic_obj = {
                            'sub_num': sub_num,
                            'title': sub_rest
                        }
            
            # Clean title
            title = re.sub(r'\s+', ' ', title)
            
            # Allow longer headings (they're meaningful); continuation lines may add more.
            if len(title) > 2 and len(title) < 200:
                parent_comp = f'Comp{comp_num}'
                topic_code = f'C{comp_num}T{topic_num}'
                
                # Look ahead for wrapped titles (common in the "Subject content" table).
                # Previous heuristic was too strict (<40 chars), causing truncation like
                # "2.1 Diet and nutrition and" without the continuation line(s).
                continuation = _collect_continuation_lines(lines, i + 1, max_lines=12)
                if continuation:
                    title = f'{title} {continuation}'
                
                topics.append({
                    'code': topic_code,
                    'title': f'{comp_num}.{topic_num} {title}',
                    'level': 1,
                    'parent': parent_comp
                })
                current_topic = topic_code
                current_subtopic = None

                # Emit embedded subtopic if present and not already created elsewhere.
                if embedded_subtopic_obj:
                    sub_num = embedded_subtopic_obj['sub_num']
                    subtopic_code = f'C{comp_num}T{topic_num}S{sub_num}'
                    subtopic_title = embedded_subtopic_obj['title']
                    subtopic_title = re.sub(r'\s+', ' ', subtopic_title)
                    if len(subtopic_title) > 500:
                        subtopic_title = subtopic_title[:497] + '...'
                    if not any(t.get('code') == subtopic_code for t in topics):
                        topics.append({
                            'code': subtopic_code,
                            'title': f'{comp_num}.{topic_num}.{sub_num} {subtopic_title}',
                            'level': 2,
                            'parent': topic_code
                        })
                        current_subtopic = subtopic_code
        
        # Level 2: Subtopics (1.1.1, 1.1.2, 1.2.1, etc.)
        subtopic_match = re.match(r'^([1-4])\.(\d{1,2})\.(\d{1,2})\s+(.+?)$', line_stripped)
        if subtopic_match and current_topic:
            comp_num = subtopic_match.group(1)
            topic_num = subtopic_match.group(2)
            sub_num = subtopic_match.group(3)
            title = subtopic_match.group(4).strip()
            
            # Look ahead for continuation lines (multi-line topics)
            full_title = title
            for j in range(i+1, min(i+5, len(lines))):
                next_line = lines[j].strip()
                # If next line is lowercase or continues sentence, append it
                if next_line and len(next_line) > 0:
                    if next_line[0].islower() or next_line.startswith('and ') or next_line.startswith('or '):
                        full_title += ' ' + next_line
                    elif not re.match(r'^[0-9]', next_line) and len(full_title) < 300:
                        # Keep adding if it's not a new section and we're under limit
                        full_title += ' ' + next_line
                    else:
                        break
                else:
                    break
            
            # Clean title
            full_title = re.sub(r'\s+', ' ', full_title)
            # Don't truncate - keep full content (up to 500 chars for database)
            if len(full_title) > 500:
                full_title = full_title[:497] + '...'
            
            if len(full_title) > 5:
                subtopic_code = f'C{comp_num}T{topic_num}S{sub_num}'
                
                topics.append({
                    'code': subtopic_code,
                    'title': f'{comp_num}.{topic_num}.{sub_num} {full_title}',
                    'level': 2,
                    'parent': current_topic
                })
                current_subtopic = subtopic_code
        
        # Level 3: Learning points (a), b), c), or 'o' bullets)
        learning_match = re.match(r'^([a-z])\)\s+(.+?)$', line_stripped)
        if learning_match and current_subtopic:
            letter = learning_match.group(1)
            title = learning_match.group(2).strip()
            
            # Clean title - no truncation
            title = re.sub(r'\s+', ' ', title)
            if len(title) > 500:
                title = title[:497] + '...'
            
            if len(title) > 3:
                learning_code = f'{current_subtopic}_{letter}'
                if not any(t['code'] == learning_code for t in topics):
                    topics.append({
                        'code': learning_code,
                        'title': f'{letter}) {title}',
                        'level': 3,
                        'parent': current_subtopic
                    })
        
        # Level 3/4: Bullet points ('o' markers - often table content like Region/Joint)
        bullet_match = re.match(r'^o\s+(.+?)$', line_stripped)
        if bullet_match and current_subtopic:
            title = bullet_match.group(1).strip()
            
            # Clean title - no truncation for table content
            title = re.sub(r'\s+', ' ', title)
            
            if len(title) > 5:
                # Skip generic descriptions but keep specific table entries
                if not any(skip in title.lower() for skip in ['components are those', 'aspects of performance']):
                    if len(title) > 500:
                        title = title[:497] + '...'
                    
                    bullet_index_by_subtopic[current_subtopic] = bullet_index_by_subtopic.get(current_subtopic, 0) + 1
                    bullet_code = f'{current_subtopic}_b{bullet_index_by_subtopic[current_subtopic]}'
                    topics.append({
                        'code': bullet_code,
                        'title': f'• {title}',
                        'level': 3,
                        'parent': current_subtopic
                    })
    
    return topics


def upload_topics(topics):
    """Upload to Supabase."""
    
    print(f"\n[INFO] Uploading {len(topics)} topics to database...")
    
    try:
        # Get/create subject
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT['name']} (A-Level)",
            'subject_code': SUBJECT['code'],
            'qualification_type': 'A-Level',
            'specification_url': SUBJECT['pdf_url'],
            'exam_board': SUBJECT['exam_board']
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        # Clear old topics
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared old topics")
        
        # Insert topics
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'exam_board': SUBJECT['exam_board']
        } for t in topics]
        
        inserted_result = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted_result.data)} topics")
        
        # Link hierarchy
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
    """Main execution."""
    
    print("=" * 80)
    print("EDEXCEL PHYSICAL EDUCATION (9PE1) - COMPLETE DEEP HIERARCHY")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print("Target: 4-5 level hierarchy with table content\n")
    
    try:
        # Download PDF
        text = download_pdf()
        if not text:
            return
        
        # Parse topics
        topics = parse_pe_topics(text)
        
        print(f"\n[OK] Extracted {len(topics)} topics")
        
        # Show breakdown
        levels = {}
        for t in topics:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("\n[INFO] Level breakdown:")
        for level in sorted(levels.keys()):
            print(f"   Level {level}: {levels[level]} topics")
        
        # Upload
        if upload_topics(topics):
            print("\n" + "=" * 80)
            print("[OK] PHYSICAL EDUCATION COMPLETE!")
            print("=" * 80)
            print(f"\nTotal: {len(topics)} topics with {max(levels.keys())+1} levels")
        
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

