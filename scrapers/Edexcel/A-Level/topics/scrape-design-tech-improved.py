"""
Edexcel Design and Technology - Product Design (9DT0) - Improved Topic Scraper
Targets the 3-column table structure in Subject Content section

Structure:
- Level 0: Component 1 (Principles of Design and Technology)
- Level 1: Topics (1-12: Materials, Performance, Processes, etc.)
- Level 2: Sub-topics (1.1, 1.2, 1.3: Woods, Metals, Polymers, etc.)
- Level 3: Details (a), b), c): specific types like hardwoods, softwoods)

Ignores: Component 2 (Non-examined assessment)
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

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT = {
    'code': '9DT0',
    'name': 'Design and Technology - Product Design',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Design%20and%20Technology%20-%20Product%20Design/2017/specification-and-sample-assessments/Pearson_Edexcel_Level_3_GCE_in_Design_and_Technology_Specification_issue2.pdf'
}


def download_pdf():
    """Download PDF and extract text."""
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
        
        # Save debug
        debug_path = Path(__file__).parent / "debug-design-tech-spec.txt"
        debug_path.write_text(text, encoding='utf-8')
        print(f"[OK] Saved to {debug_path.name}")
        
        return text
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        raise


def parse_design_tech_topics(text):
    """Parse Design Tech topics from 3-column table."""
    print("\n[INFO] Parsing Design and Technology topics...")
    
    topics = []
    lines = text.split('\n')
    
    # Level 0: Component 1 (examined component)
    topics.append({
        'code': 'Component1',
        'title': 'Component 1: Principles of Design and Technology',
        'level': 0,
        'parent': None
    })
    print("[OK] Added Component 1 (Level 0)")
    
    # Level 1: The 12 main topics from "Qualification at a glance"
    main_topics = [
        {'code': 'Topic1', 'title': 'Topic 1: Materials', 'level': 1, 'parent': 'Component1'},
        {'code': 'Topic2', 'title': 'Topic 2: Performance characteristics of materials', 'level': 1, 'parent': 'Component1'},
        {'code': 'Topic3', 'title': 'Topic 3: Processes and techniques', 'level': 1, 'parent': 'Component1'},
        {'code': 'Topic4', 'title': 'Topic 4: Digital technologies', 'level': 1, 'parent': 'Component1'},
        {'code': 'Topic5', 'title': 'Topic 5: Factors influencing the development of products', 'level': 1, 'parent': 'Component1'},
        {'code': 'Topic6', 'title': 'Topic 6: Effects of technological developments', 'level': 1, 'parent': 'Component1'},
        {'code': 'Topic7', 'title': 'Topic 7: Potential hazards and risk assessment', 'level': 1, 'parent': 'Component1'},
        {'code': 'Topic8', 'title': 'Topic 8: Features of manufacturing industries', 'level': 1, 'parent': 'Component1'},
        {'code': 'Topic9', 'title': 'Topic 9: Designing for maintenance and the cleaner environment', 'level': 1, 'parent': 'Component1'},
        {'code': 'Topic10', 'title': 'Topic 10: Current legislation', 'level': 1, 'parent': 'Component1'},
        {'code': 'Topic11', 'title': 'Topic 11: Information handling, Modelling and forward planning', 'level': 1, 'parent': 'Component1'},
        {'code': 'Topic12', 'title': 'Topic 12: Further processes and techniques', 'level': 1, 'parent': 'Component1'}
    ]
    topics.extend(main_topics)
    print(f"[OK] Added 12 main topics (Level 1)")
    
    # State tracking
    current_topic = None
    current_subtopic = None
    
    # Now parse the detailed content from tables
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # Skip non-examined assessment sections
        if 'non-examined' in line.lower() or 'Component 2' in line:
            # Skip ahead
            i += 1
            continue
        
        # Pattern 1: Main topic number (just "1", "2", etc. in Topic column)
        # This helps us track which topic we're in
        topic_num_match = re.match(r'^(\d+)$', line)
        if topic_num_match and int(topic_num_match.group(1)) <= 12:
            num = topic_num_match.group(1)
            current_topic = f'Topic{num}'
            current_subtopic = None
            i += 1
            continue
        
        # Pattern 2: Topic with title (e.g., "1 Materials")
        topic_title_match = re.match(r'^(\d+)\s+(.+)', line)
        if topic_title_match and int(topic_title_match.group(1)) <= 12:
            num = topic_title_match.group(1)
            current_topic = f'Topic{num}'
            current_subtopic = None
            i += 1
            continue
        
        # Pattern 3: Sub-topics (1.1, 1.2, 1.3, etc.)
        subtopic_match = re.match(r'^(\d+)\.(\d+)\s*$', line)
        if subtopic_match and current_topic:
            # Code only - title on next line(s)
            major = subtopic_match.group(1)
            minor = subtopic_match.group(2)
            code = f'{major}.{minor}'
            
            # Get title from next line(s)
            title_lines = []
            j = i + 1
            while j < len(lines) and len(title_lines) < 3:
                next_line = lines[j].strip()
                # Stop if we hit another pattern
                if re.match(r'^\d+\.\d+', next_line) or re.match(r'^[a-c]\)', next_line):
                    break
                if next_line and len(next_line) > 2 and not next_line.endswith(':'):
                    title_lines.append(next_line)
                    j += 1
                elif next_line and next_line.endswith(':'):
                    title_lines.append(next_line)
                    j += 1
                    break
                else:
                    j += 1
            
            if title_lines:
                title = ' '.join(title_lines)
                current_subtopic = code
                
                topics.append({
                    'code': code,
                    'title': title,
                    'level': 2,
                    'parent': current_topic
                })
                print(f"   Level 2: {code} - {title[:50]}")
                i = j
                continue
        
        # Alternative Pattern 3: Sub-topic with title on same line (e.g., "1.1 Woods:")
        subtopic_match2 = re.match(r'^(\d+)\.(\d+)\s+(.+)', line)
        if subtopic_match2 and current_topic:
            major = subtopic_match2.group(1)
            minor = subtopic_match2.group(2)
            title = subtopic_match2.group(3).strip()
            code = f'{major}.{minor}'
            current_subtopic = code
            
            topics.append({
                'code': code,
                'title': title,
                'level': 2,
                'parent': current_topic
            })
            print(f"   Level 2: {code} - {title[:50]}")
            i += 1
            continue
        
        # Pattern 4: Detail items (a), b), c))
        detail_match = re.match(r'^([a-c])\)\s+(.+)', line)
        if detail_match and current_subtopic:
            letter = detail_match.group(1)
            content = detail_match.group(2).strip()
            
            # Multi-line continuation
            full_content = [content]
            j = i + 1
            while j < len(lines) and len(full_content) < 4:
                next_line = lines[j].strip()
                # Stop on next pattern
                if re.match(r'^[a-c]\)', next_line) or re.match(r'^\d+\.\d+', next_line):
                    break
                if next_line and len(next_line) > 2:
                    full_content.append(next_line)
                    j += 1
                else:
                    break
            
            code = f'{current_subtopic}.{letter}'
            title = ' '.join(full_content)
            
            topics.append({
                'code': code,
                'title': title,
                'level': 3,
                'parent': current_subtopic
            })
            i = j
            continue
        
        i += 1
    
    # Deduplicate
    unique = []
    seen = set()
    for t in topics:
        if t['code'] not in seen:
            unique.append(t)
            seen.add(t['code'])
    
    print(f"\n[OK] Parsed {len(unique)} unique topics")
    
    # Show distribution
    levels = {}
    for t in unique:
        levels[t['level']] = levels.get(t['level'], 0) + 1
    
    print("\n   Level distribution:")
    for l in sorted(levels.keys()):
        print(f"   Level {l}: {levels[l]} topics")
    
    return unique


def upload_topics(topics):
    """Upload to Supabase."""
    print("\n[INFO] Uploading to database...")
    
    # Get/create subject
    subject_result = supabase.table('staging_aqa_subjects').upsert({
        'subject_name': f"{SUBJECT['name']} (A-Level)",
        'subject_code': SUBJECT['code'],
        'qualification_type': 'A-Level',
        'specification_url': SUBJECT['pdf_url'],
        'exam_board': 'Edexcel'
    }, on_conflict='subject_code,qualification_type,exam_board').execute()
    
    subject_id = subject_result.data[0]['id']
    print(f"[OK] Subject ID: {subject_id}")
    
    # Clear old
    supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
    print("[OK] Cleared old topics")
    
    # Insert
    to_insert = [{
        'subject_id': subject_id,
        'topic_code': t['code'],
        'topic_name': t['title'],
        'topic_level': t['level'],
        'exam_board': 'Edexcel'
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
    
    return subject_id


def main():
    """Main execution."""
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 80)
    print("EDEXCEL DESIGN AND TECHNOLOGY (9DT0) - IMPROVED TOPIC SCRAPER")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    
    try:
        # Download
        text = download_pdf()
        
        # Parse
        topics = parse_design_tech_topics(text)
        
        if len(topics) <= 13:  # Only Component + 12 topics
            print("\n[WARN] Only found main topics - detailed subtopics not captured")
            print("   Check debug-design-tech-spec.txt for structure")
        
        # Upload
        upload_topics(topics)
        
        print("\n" + "=" * 80)
        print("[OK] DESIGN AND TECHNOLOGY COMPLETE!")
        print("=" * 80)
        print(f"\nTotal: {len(topics)} topics")
        
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

