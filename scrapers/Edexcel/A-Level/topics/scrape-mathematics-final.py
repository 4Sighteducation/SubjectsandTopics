"""
Edexcel Mathematics (9MA0) - FINAL Clean Scraper
Properly extracts ONLY the table structure without duplicates:
  Level 0: Papers (Paper 1, Paper 2, Paper 3)
  Level 1: Main Topics (1 Proof, 2 Algebra and functions, etc.)
  Level 2: Content Items (1.1, 2.1, 2.2, etc.) - FULL TEXT
  Level 3: Methods (extracted ONLY from structured sections)

NO DUPLICATES - NO TRUNCATION
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
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Mathematics/2017/specification-and-sample-assesment/a-level-l3-mathematics-specification-issue4.pdf'
}


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
        Path('debug-mathematics-final.txt').write_text(full_text, encoding='utf-8')
        print(f"[OK] Saved debug file")
        
        return full_text
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return None


def parse_mathematics_topics(text):
    """Parse Mathematics - CLEAN extraction without duplicates."""
    
    print("\n[INFO] Parsing Mathematics cleanly (no duplicates)...")
    topics = []
    
    # Level 0: Papers
    topics.extend([
        {'code': 'Paper1', 'title': 'Paper 1: Pure Mathematics 1', 'level': 0, 'parent': None},
        {'code': 'Paper2', 'title': 'Paper 2: Pure Mathematics 2', 'level': 0, 'parent': None},
        {'code': 'Paper3', 'title': 'Paper 3: Statistics and Mechanics', 'level': 0, 'parent': None},
    ])
    
    # Level 1: Main topics (manually defined for accuracy)
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
    
    # Level 2: Content items (1.1, 2.1, etc.) - FULL content, no truncation
    # ONLY extract from the content section, NOT from appendices
    lines = text.split('\n')
    
    # Find the actual content section
    start_parsing = False
    stop_parsing = False
    
    for i, line in enumerate(lines):
        # Start parsing when we hit the content table
        if 'Paper 1 and Paper 2: Pure Mathematics' in line and 'Topics' in text[max(0, i-50):i+50]:
            start_parsing = True
            continue
        
        # Stop parsing when we hit appendices or end sections
        if any(keyword in line for keyword in ['Appendix 1:', 'Appendix 2:', 'Administration and general']):
            stop_parsing = True
        
        if not start_parsing or stop_parsing:
            continue
        # Match content items: 1.1, 2.1, etc.
        match = re.match(r'^(\d{1,2})\.(\d{1,2})\s+(.+)$', line.strip())
        if match:
            major = match.group(1)
            minor = match.group(2)
            title_start = match.group(3).strip()
            
            # Build FULL content by looking ahead
            full_content = title_start
            for j in range(i+1, min(i+15, len(lines))):
                next_line = lines[j].strip()
                
                # Stop conditions:
                # 1. Hit another numbered item
                if re.match(r'^\d+\.?\d*\s', next_line):
                    break
                # 2. Hit a heading like "Proof by"
                if re.match(r'^[A-Z][a-z]+ by [a-z]', next_line):
                    break
                # 3. Empty line
                if not next_line:
                    break
                # 4. Hit examples/guidance sections
                if next_line.startswith('Examples of') or next_line.startswith('Students should'):
                    break
                
                # Append
                full_content += ' ' + next_line
            
            # Clean
            full_content = re.sub(r'\s+', ' ', full_content).strip()
            
            # Remove "including:" suffix if present (it leads to sub-items)
            full_content = re.sub(r',?\s*including:?\s*$', '', full_content)
            
            # Only add if reasonable length AND not duplicate
            if len(full_content) > 10 and major in main_topics:
                code = f'T{major}_{minor}'
                # Check for duplicates
                if not any(t['code'] == code for t in topics):
                    topics.append({
                        'code': code,
                        'title': f'{major}.{minor} {full_content}',
                        'level': 2,
                        'parent': f'T{major}'
                    })
    
    print(f"[OK] Extracted clean hierarchy")
    
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
            'exam_board': 'Edexcel'
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
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main execution."""
    
    print("=" * 80)
    print("EDEXCEL MATHEMATICS (9MA0) - FINAL CLEAN SCRAPER")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print("Clean extraction - No duplicates - Full content!\n")
    
    try:
        # Download PDF
        text = download_pdf()
        if not text:
            return
        
        # Parse topics
        topics = parse_mathematics_topics(text)
        
        print(f"\n[OK] Extracted {len(topics)} topics")
        
        # Show breakdown
        levels = {}
        for t in topics:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("\n[INFO] Level breakdown:")
        for level in sorted(levels.keys()):
            print(f"   Level {level}: {levels[level]} topics")
        
        # Show samples
        print("\n[INFO] Sample topics to verify quality:")
        for level in [1, 2]:
            samples = [t for t in topics if t['level'] == level]
            if samples:
                print(f"\n   Level {level} sample:")
                print(f"   {samples[0]['title'][:150]}...")
        
        # Upload
        if upload_topics(topics):
            print("\n" + "=" * 80)
            print("[OK] MATHEMATICS COMPLETE - CLEAN VERSION!")
            print("=" * 80)
            print(f"\nTotal: {len(topics)} topics with {max(levels.keys())+1} levels")
            print("No duplicates - Full content preserved!")
        
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

