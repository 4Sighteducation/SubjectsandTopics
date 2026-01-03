"""
Edexcel Mathematics (9MA0) - Improved Topic Scraper
Extracts full topic hierarchy: Papers → Topics → Subtopics → Learning Points
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
        Path('debug-mathematics-spec.txt').write_text(full_text, encoding='utf-8')
        print(f"[OK] Saved debug file")
        
        return full_text
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return None


def parse_mathematics_topics(text):
    """Parse Mathematics topics with full hierarchy."""
    
    print("\n[INFO] Parsing Mathematics topics...")
    topics = []
    
    # Level 0: Papers
    topics.extend([
        {'code': 'Paper1', 'title': 'Paper 1: Pure Mathematics 1', 'level': 0, 'parent': None},
        {'code': 'Paper2', 'title': 'Paper 2: Pure Mathematics 2', 'level': 0, 'parent': None},
        {'code': 'Paper3', 'title': 'Paper 3: Statistics and Mechanics', 'level': 0, 'parent': None},
    ])
    
    # Find sections in "Paper 1 and Paper 2: Pure Mathematics"
    # Pattern: Look for topic headers before numbered sections
    
    lines = text.split('\n')
    current_topic = None
    current_topic_num = None
    
    for i, line in enumerate(lines):
        # Match topic numbers like "1", "2", etc. followed by topic name on next lines
        # Look for pattern: number alone, then title
        if re.match(r'^\d{1,2}$', line.strip()) and i < len(lines) - 2:
            num = line.strip()
            next_line = lines[i+1].strip()
            
            # Check if next line looks like a topic title (capital letter, reasonable length)
            if next_line and len(next_line) > 3 and len(next_line) < 80 and next_line[0].isupper():
                # This might be a topic
                if 'Proof' in next_line or 'Algebra' in next_line or 'functions' in next_line or \
                   'Coordinate' in next_line or 'Sequences' in next_line or 'Trigonometry' in next_line or \
                   'Exponential' in next_line or 'Differentiation' in next_line or 'Integration' in next_line or \
                   'Numerical' in next_line or 'Vectors' in next_line:
                    current_topic_num = num
                    current_topic = next_line
        
        # Match subtopics (1.1, 2.1, etc.)
        subtopic_match = re.match(r'^(\d{1,2})\.(\d{1,2})\s+(.+?)$', line)
        if subtopic_match:
            major = subtopic_match.group(1)
            minor = subtopic_match.group(2)
            title = subtopic_match.group(3).strip()
            
            # Clean title - preserve full content
            title = re.sub(r'\s+', ' ', title)
            if len(title) > 500:
                title = title[:497] + '...'
            
            if len(title) > 5:
                # Determine parent paper
                major_int = int(major)
                if major_int <= 8:
                    parent_paper = 'Paper1'  # Pure Math 1
                    parent_prefix = 'PM1'
                elif major_int <= 16:
                    parent_paper = 'Paper2'  # Pure Math 2  
                    parent_prefix = 'PM2'
                else:
                    parent_paper = 'Paper3'  # Stats & Mechanics
                    parent_prefix = 'SM'
                
                # Create topic if we don't have it yet
                topic_code = f'{parent_prefix}T{major}'
                if not any(t['code'] == topic_code for t in topics):
                    # Infer topic name from number
                    topic_names = {
                        '1': 'Proof',
                        '2': 'Algebra and Functions',
                        '3': 'Coordinate Geometry',
                        '4': 'Sequences and Series',
                        '5': 'Trigonometry',
                        '6': 'Exponential and Logarithms',
                        '7': 'Differentiation',
                        '8': 'Integration',
                        '9': 'Numerical Methods',
                        '10': 'Vectors',
                    }
                    topic_name = topic_names.get(major, f'Topic {major}')
                    
                    topics.append({
                        'code': topic_code,
                        'title': f'{major} - {topic_name}',
                        'level': 1,
                        'parent': parent_paper
                    })
                
                # Add subtopic with globally unique code
                subtopic_code = f'{parent_prefix}_{major}_{minor}'
                if not any(t['code'] == subtopic_code for t in topics):
                    topics.append({
                        'code': subtopic_code,
                        'title': f'{major}.{minor} {title}',
                        'level': 2,
                        'parent': topic_code
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
    print("EDEXCEL MATHEMATICS (9MA0) - IMPROVED TOPIC SCRAPER")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}\n")
    
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
        
        # Upload
        if upload_topics(topics):
            print("\n" + "=" * 80)
            print("[OK] MATHEMATICS COMPLETE!")
            print("=" * 80)
            print(f"\nTotal: {len(topics)} topics with {max(levels.keys())+1} levels")
        
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
