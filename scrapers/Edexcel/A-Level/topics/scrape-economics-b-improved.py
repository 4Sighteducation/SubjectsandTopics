"""
Edexcel Economics B (9EB0) - Improved Topic Scraper
Same table structure as Business/Economics A
"""

import os
import sys
import re
import requests
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv
from supabase import create_client

try:
    from pypdf import PdfReader
    PDF_LIBRARY = 'pypdf'
except ImportError:
    import PyPDF2
    PdfReader = PyPDF2.PdfReader
    PDF_LIBRARY = 'PyPDF2'

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT = {
    'code': '9EB0',
    'name': 'Economics B',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Economics/2015/specification-and-sample-assessment-materials/9781446914410_GCE2015_A_ECOB_WEB%20spec.PDF'
}


def download_pdf():
    print(f"\n[INFO] Downloading PDF...")
    
    try:
        response = requests.get(SUBJECT['pdf_url'], timeout=60)
        response.raise_for_status()
        
        print(f"[OK] Downloaded {len(response.content):,} bytes")
        
        pdf_file = BytesIO(response.content)
        reader = PdfReader(pdf_file)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        print(f"[OK] Extracted {len(text):,} characters from {len(reader.pages)} pages")
        
        debug_path = Path(__file__).parent / "debug-economics-b-spec.txt"
        debug_path.write_text(text, encoding='utf-8')
        print(f"[OK] Saved to {debug_path.name}")
        
        return text
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        raise


def parse_economics_topics(text):
    """Parse Economics B topics."""
    print("\n[INFO] Parsing Economics B topics...")
    
    topics = []
    lines = text.split('\n')
    
    # Detect themes from content
    themes = []
    for i, line in enumerate(lines[:500]):
        if re.match(r'^Theme\s+\d+:', line):
            match = re.match(r'^(Theme\s+\d+):\s+(.+)', line)
            if match:
                theme_num = match.group(1).replace('Theme ', '').strip()
                theme_title = match.group(2).strip()
                themes.append({'code': f'Theme{theme_num}', 'title': f'Theme {theme_num}: {theme_title}', 'level': 0, 'parent': None})
    
    topics.extend(themes)
    print(f"[OK] Added {len(themes)} themes (Level 0)")
    
    current_theme = None
    current_section = None
    current_content = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # Section headers (1.1, 1.2, etc.)
        section_match = re.match(r'^(\d+)\.(\d+)\s+(.+)', line)
        if section_match:
            major = section_match.group(1)
            minor = section_match.group(2)
            title = section_match.group(3).strip()
            
            theme_map = {'1': 'Theme1', '2': 'Theme2', '3': 'Theme3', '4': 'Theme4'}
            current_theme = theme_map.get(major)
            
            section_code = f'{major}.{minor}'
            current_section = section_code
            
            topics.append({
                'code': section_code,
                'title': f'{section_code} {title}',
                'level': 1,
                'parent': current_theme
            })
            print(f"[OK] Level 1: {section_code} {title[:50]}")
            i += 1
            continue
        
        # Content codes (1.1.1, 1.1.2)
        content_match = re.match(r'^(\d+)\.(\d+)\.(\d+)\s*$', line)
        if content_match and current_section:
            code = f'{content_match.group(1)}.{content_match.group(2)}.{content_match.group(3)}'
            
            title_lines = []
            j = i + 1
            while j < len(lines) and len(title_lines) < 3:
                next_line = lines[j].strip()
                if re.match(r'^\d+\.\d+\.\d+', next_line) or re.match(r'^[a-z]\)', next_line):
                    break
                if next_line and len(next_line) > 2:
                    title_lines.append(next_line)
                j += 1
            
            if title_lines:
                title = ' '.join(title_lines)
                current_content = code
                
                topics.append({
                    'code': code,
                    'title': title,
                    'level': 2,
                    'parent': current_section
                })
                print(f"   Level 2: {code} - {title[:40]}")
                i = j
                continue
        
        # Content with title on same line
        content_match2 = re.match(r'^(\d+\.\d+\.\d+)\s+(.+)', line)
        if content_match2 and current_section:
            code = content_match2.group(1)
            title = content_match2.group(2).strip()
            current_content = code
            
            topics.append({
                'code': code,
                'title': title,
                'level': 2,
                'parent': current_section
            })
            print(f"   Level 2: {code} - {title[:40]}")
            i += 1
            continue
        
        # Learning points (a), b), c))
        learning_match = re.match(r'^([a-z])\)\s+(.+)', line)
        if learning_match and current_content:
            letter = learning_match.group(1)
            content = learning_match.group(2).strip()
            
            full_content = [content]
            j = i + 1
            while j < len(lines) and len(full_content) < 3:
                next_line = lines[j].strip()
                if re.match(r'^[a-z]\)', next_line) or re.match(r'^\d+\.\d+', next_line):
                    break
                if next_line and len(next_line) > 2 and not next_line.startswith('o'):
                    full_content.append(next_line)
                    j += 1
                else:
                    break
            
            code = f'{current_content}.{letter}'
            title = ' '.join(full_content)
            
            topics.append({
                'code': code,
                'title': title,
                'level': 3,
                'parent': current_content
            })
            i = j
            continue
        
        # Sub-points (o)
        subpoint_match = re.match(r'^o\s+(.+)', line)
        if subpoint_match and current_content:
            content = subpoint_match.group(1).strip()
            
            recent_l3 = None
            for t in reversed(topics):
                if t['level'] == 3 and t['parent'] == current_content:
                    recent_l3 = t['code']
                    break
            
            if recent_l3:
                subpoint_count = sum(1 for t in topics if t.get('parent') == recent_l3)
                code = f'{recent_l3}.{subpoint_count + 1}'
                
                topics.append({
                    'code': code,
                    'title': content,
                    'level': 4,
                    'parent': recent_l3
                })
        
        i += 1
    
    unique = []
    seen = set()
    for t in topics:
        if t['code'] not in seen:
            unique.append(t)
            seen.add(t['code'])
    
    print(f"\n[OK] Parsed {len(unique)} unique topics")
    
    levels = {}
    for t in unique:
        levels[t['level']] = levels.get(t['level'], 0) + 1
    
    print("\n   Level distribution:")
    for l in sorted(levels.keys()):
        print(f"   Level {l}: {levels[l]} topics")
    
    return unique


def upload_topics(topics):
    print("\n[INFO] Uploading to database...")
    
    subject_result = supabase.table('staging_aqa_subjects').upsert({
        'subject_name': f"{SUBJECT['name']} (A-Level)",
        'subject_code': SUBJECT['code'],
        'qualification_type': 'A-Level',
        'specification_url': SUBJECT['pdf_url'],
        'exam_board': 'Edexcel'
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
        'exam_board': 'Edexcel'
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


def main():
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 80)
    print("EDEXCEL ECONOMICS B (9EB0) - IMPROVED TOPIC SCRAPER")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    
    try:
        text = download_pdf()
        topics = parse_economics_topics(text)
        upload_topics(topics)
        
        print("\n" + "=" * 80)
        print("[OK] ECONOMICS B COMPLETE!")
        print("=" * 80)
        print(f"\nTotal: {len(topics)} topics")
        
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

