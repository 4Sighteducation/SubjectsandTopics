"""
Edexcel Biology A - Topic Scraper (Python + Local PDF)
Code: 9BN0

Downloads PDF and parses locally - MUCH faster and more reliable!
"""

import os
import sys
import re
import requests
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv
from supabase import create_client

# Try to import PDF library
try:
    from pypdf import PdfReader
    PDF_LIBRARY = 'pypdf'
except ImportError:
    try:
        import PyPDF2
        PdfReader = PyPDF2.PdfReader
        PDF_LIBRARY = 'PyPDF2'
    except ImportError:
        print(" No PDF library found! Install with: pip install pypdf")
        sys.exit(1)

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

print(f" Using {PDF_LIBRARY} for PDF parsing")

# ================================================================
# CONFIG
# ================================================================

SUBJECT = {
    'name': 'Art and Design',
    'code': '9AD0',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Art%20and%20Design/2015/specification-and-sample-assessment-materials/gce-a-level-art-and-design-specification-issue-4.pdf'
}

# ================================================================
# STEP 1: DOWNLOAD PDF
# ================================================================

def download_pdf():
    """Download PDF and extract text."""
    print(f" Downloading PDF...")
    print(f"   URL: {SUBJECT['pdf_url']}")
    
    try:
        response = requests.get(SUBJECT['pdf_url'], timeout=30)
        response.raise_for_status()
        
        print(f" Downloaded {len(response.content)} bytes")
        
        # Parse PDF
        print(" Extracting text from PDF...")
        pdf_file = BytesIO(response.content)
        reader = PdfReader(pdf_file)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        print(f" Extracted {len(text)} characters")
        
        # Save for debugging
        debug_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\debug-biology-a-spec.txt")
        debug_path.write_text(text, encoding='utf-8')
        print(f"   Saved to debug-biology-a-spec.txt")
        
        return text
        
    except Exception as e:
        print(f" Download failed: {e}")
        raise

# ================================================================
# STEP 2: PARSE TOPICS
# ================================================================

def parse_topics(text):
    """Parse Biology topics from PDF text."""
    print("\n Parsing topics...")
    
    topics = []
    lines = text.split('\n')
    
    # Create Papers
    topics.append({'code': 'Paper1', 'title': 'Paper 1: Natural Environment and Species Survival', 'level': 0, 'parent': None})
    topics.append({'code': 'Paper2', 'title': 'Paper 2: Energy, Exercise and Co-ordination', 'level': 0, 'parent': None})
    topics.append({'code': 'Paper3', 'title': 'Paper 3: General and Practical Applications', 'level': 0, 'parent': None})
    
    # Topic to Paper mapping
    topic_papers = {
        'Topic1': 'Paper1', 'Topic2': 'Paper1', 'Topic3': 'Paper1',
        'Topic4': 'Paper1', 'Topic5': 'Paper1', 'Topic6': 'Paper1',
        'Topic7': 'Paper2', 'Topic8': 'Paper2'
    }
    
    current_topic = None
    current_item = None
    
    i = 0
    while i < len(lines):
        line = lines[i]
        line = line.strip()
        if not line or len(line) < 5:
            i += 1
            continue
        
        # Skip unwanted sections
        if any(skip in line for skip in ['CORE PRACTICAL', 'Appendix', 'Assessment Objectives', '']):
            i += 1
            continue
        
        # Pattern 1: Topic X:
        topic_match = re.match(r'Topic\s+(\d+):\s+(.+)', line)
        if topic_match:
            num = topic_match.group(1)
            title = topic_match.group(2).strip()
            code = f'Topic{num}'
            
            current_topic = code
            current_item = None
            
            topics.append({
                'code': code,
                'title': f'Topic {num}: {title}',
                'level': 1,
                'parent': topic_papers.get(code, 'Paper1')
            })
            print(f"   Found {code}")
            i += 1
            continue
        
        if not current_topic:
            i += 1
            continue
        
        # Pattern 2: X.Y Item (multi-line - continue reading until next pattern)
        item_match = re.match(r'(\d+)\.(\d+)\s+(.+)', line)
        if item_match:
            major = item_match.group(1)
            minor = item_match.group(2)
            content = [item_match.group(3).strip()]
            code = f'{major}.{minor}'
            
            # Continue reading subsequent lines until we hit another pattern
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                
                # Stop if we hit another numbered item, topic, or sub-item
                if re.match(r'(\d+)\.(\d+)\s+', next_line):
                    break
                if re.match(r'Topic\s+\d+:', next_line):
                    break
                if re.match(r'[ivx]+\)\s+', next_line, re.IGNORECASE):
                    break
                if re.match(r'CORE PRACTICAL', next_line):
                    break
                if not next_line or len(next_line) < 3:
                    j += 1
                    continue
                
                # Add to content
                content.append(next_line)
                j += 1
                i = j - 1  # Update outer loop index
                
                # Safety: max 5 continuation lines
                if len(content) >= 6:
                    break
            
            current_item = code
            full_content = ' '.join(content)
            
            topics.append({
                'code': code,
                'title': full_content,
                'level': 2,
                'parent': current_topic
            })
            i = j  # Jump to where we stopped reading
            continue
        
        # Pattern 3: i), ii), iii) sub-items (multi-line)
        sub_match = re.match(r'([ivx]+)\)\s+(.+)', line, re.IGNORECASE)
        if sub_match and current_item:
            roman = sub_match.group(1).lower()
            content = [sub_match.group(2).strip()]
            
            # Continue reading until next pattern
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                
                # Stop if we hit another pattern
                if re.match(r'(\d+)\.(\d+)\s+', next_line):
                    break
                if re.match(r'[ivx]+\)\s+', next_line, re.IGNORECASE):
                    break
                if re.match(r'CORE PRACTICAL|Topic\s+\d+', next_line):
                    break
                if not next_line or len(next_line) < 3:
                    j += 1
                    continue
                
                content.append(next_line)
                j += 1
                i = j - 1
                
                # Safety: max 5 lines
                if len(content) >= 6:
                    break
            
            roman_map = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5}
            sub_num = roman_map.get(roman, 1)
            code = f'{current_item}.{sub_num}'
            full_content = ' '.join(content)
            
            topics.append({
                'code': code,
                'title': full_content,
                'level': 3,
                'parent': current_item
            })
            i = j  # Jump to where we stopped reading
            continue
        
        # No pattern matched - advance
        i += 1
    
    # Deduplicate by code (PDF has multiple TOCs)
    unique = []
    seen = set()
    for t in topics:
        if t['code'] not in seen:
            unique.append(t)
            seen.add(t['code'])
    
    print(f" Parsed {len(unique)} unique topics (removed {len(topics) - len(unique)} duplicates)")
    
    # Show distribution
    levels = {}
    for t in unique:
        levels[t['level']] = levels.get(t['level'], 0) + 1
    
    print("   Distribution:")
    for l in sorted(levels.keys()):
        print(f"   Level {l}: {levels[l]} topics")
    
    return unique

# ================================================================
# STEP 3: UPLOAD
# ================================================================

def upload_topics(topics):
    """Upload to Supabase."""
    print("\n Uploading to database...")
    
    # Get/create subject
    subject_result = supabase.table('staging_aqa_subjects').upsert({
        'subject_name': f"{SUBJECT['name']} ({SUBJECT['qualification']})",
        'subject_code': SUBJECT['code'],
        'qualification_type': SUBJECT['qualification'],
        'specification_url': SUBJECT['pdf_url'],
        'exam_board': SUBJECT['exam_board']
    }, on_conflict='subject_code,qualification_type,exam_board').execute()
    
    subject_id = subject_result.data[0]['id']
    print(f" Subject: {subject_result.data[0]['subject_name']}")
    
    # Clear old
    supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
    print(" Cleared old topics")
    
    # Insert
    to_insert = [{
        'subject_id': subject_id,
        'topic_code': t['code'],
        'topic_name': t['title'],
        'topic_level': t['level'],
        'exam_board': SUBJECT['exam_board']
    } for t in topics]
    
    inserted_result = supabase.table('staging_aqa_topics').insert(to_insert).execute()
    print(f" Uploaded {len(inserted_result.data)} topics")
    
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
    
    print(f" Linked {linked} relationships")
    
    return subject_id

# ================================================================
# MAIN
# ================================================================

def main():
    # Force UTF-8 output for Windows console
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print(">> EDEXCEL BIOLOGY A - PYTHON PDF SCRAPER")
    print("=" * 60)
    print(f"Subject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}\n")
    
    try:
        # Download and parse
        text = download_pdf()
        
        # Parse topics
        topics = parse_topics(text)
        
        # Upload
        upload_topics(topics)
        
        print("\n" + "=" * 60)
        print(" BIOLOGY A COMPLETE!")
        print("=" * 60)
        print(f"\nNext: Run papers scraper!")
        
    except Exception as e:
        print(f"\n Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

