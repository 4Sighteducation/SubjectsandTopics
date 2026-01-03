"""
Edexcel Mathematics (9MA0) - COMPLETE Topic Scraper
Properly extracts 4-level hierarchy from table structure:
  Level 0: Papers
  Level 1: Main Topics (1 Proof, 2 Algebra and functions)
  Level 2: Content Items (1.1, 2.1, etc.)
  Level 3: Methods/Techniques (Proof by deduction, etc.)

NO TRUNCATION - preserves full mathematical content
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
        Path('debug-mathematics-complete.txt').write_text(full_text, encoding='utf-8')
        print(f"[OK] Saved debug file")
        
        return full_text
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return None


def parse_mathematics_topics(text):
    """Parse Mathematics with COMPLETE hierarchy - NO truncation."""
    
    print("\n[INFO] Parsing Mathematics with complete content...")
    topics = []
    
    # Level 0: Papers
    topics.extend([
        {'code': 'Paper1', 'title': 'Paper 1: Pure Mathematics 1', 'level': 0, 'parent': None},
        {'code': 'Paper2', 'title': 'Paper 2: Pure Mathematics 2', 'level': 0, 'parent': None},
        {'code': 'Paper3', 'title': 'Paper 3: Statistics and Mechanics', 'level': 0, 'parent': None},
    ])
    
    lines = text.split('\n')
    
    # Manual topic names from PDF table structure
    main_topics = {
        '1': 'Proof',
        '2': 'Algebra and functions',
        '3': 'Coordinate geometry in the (x, y) plane',
        '4': 'Sequences and series',
        '5': 'Trigonometry',
        '6': 'Exponentials and logarithms',
        '7': 'Differentiation',
        '8': 'Integration',
        '9': 'Numerical methods',
        '10': 'Vectors',
        # Add more as found in Stats/Mechanics section
    }
    
    created_topics = set()
    current_topic_code = None
    current_subtopic_code = None
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Match content items: 1.1, 2.1, etc. (Level 2)
        # Use greedy matching to capture FULL content
        content_match = re.match(r'^(\d{1,2})\.(\d{1,2})\s+(.+)$', line_stripped)
        if content_match:
            major = content_match.group(1)
            minor = content_match.group(2)
            title = content_match.group(3).strip()
            
            # Build FULL title by looking ahead for continuation lines
            full_title = title
            for j in range(i+1, min(i+10, len(lines))):
                next_line = lines[j].strip()
                
                # Stop if we hit another numbered section or empty line
                if re.match(r'^\d+\.?\d*\s', next_line) or not next_line:
                    break
                
                # Stop if we hit keywords indicating new section
                if any(keyword in next_line for keyword in ['Proof by', 'Examples of', 'Students should', 'The notation']):
                    break
                
                # Append continuation
                full_title += ' ' + next_line
                
                # Stop if getting too long
                if len(full_title) > 800:
                    break
            
            # Clean but don't truncate
            full_title = re.sub(r'\s+', ' ', full_title).strip()
            
            # Ensure main topic exists (Level 1)
            if major not in created_topics:
                topic_name = main_topics.get(major, f'Topic {major}')
                parent_paper = 'Paper1' if int(major) <= 8 else 'Paper2' if int(major) <= 10 else 'Paper3'
                topic_code = f'T{major}'
                
                topics.append({
                    'code': topic_code,
                    'title': f'{major} - {topic_name}',
                    'level': 1,
                    'parent': parent_paper
                })
                created_topics.add(major)
                current_topic_code = topic_code
            else:
                current_topic_code = f'T{major}'
            
            # Add content item (Level 2) with paper prefix for uniqueness
            parent_paper = 'Paper1' if int(major) <= 8 else 'Paper2' if int(major) <= 10 else 'Paper3'
            parent_prefix = 'PM1' if parent_paper == 'Paper1' else 'PM2' if parent_paper == 'Paper2' else 'SM'
            
            subtopic_code = f'{parent_prefix}_T{major}_{minor}'
            
            # Only add if not duplicate
            if not any(t['code'] == subtopic_code for t in topics):
                topics.append({
                    'code': subtopic_code,
                    'title': f'{major}.{minor} {full_title}',
                    'level': 2,
                    'parent': current_topic_code
                })
                current_subtopic_code = subtopic_code
        
        # Match Level 3 items (like "Proof by deduction", "Proof by exhaustion")
        # These appear as standalone lines with capital letters after content items
        # Look for lines that are techniques/methods
        if current_subtopic_code and line_stripped:
            # Match lines that look like technique names (capital letter, short-ish, no numbers at start)
            if (line_stripped[0].isupper() and 
                not re.match(r'^\d', line_stripped) and 
                len(line_stripped) > 5 and 
                len(line_stripped) < 200 and
                not line_stripped.startswith('Students') and
                not line_stripped.startswith('The ') and
                not line_stripped.startswith('This ') and
                not line_stripped.startswith('Examples')):
                
                # Check if this looks like a method/technique name
                if any(keyword in line_stripped for keyword in [
                    'Proof by', 'Disproof by', 'including', 'Solution of', 
                    'Completing the square', 'Factorisation', 'formula',
                    'using', 'Work with', 'Understand', 'Know', 'Use', 'Sketch'
                ]):
                    
                    # This is a Level 3 technique
                    technique_code = f'{current_subtopic_code}_{len(topics)}'
                    topics.append({
                        'code': technique_code,
                        'title': line_stripped,
                        'level': 3,
                        'parent': current_subtopic_code
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
    print("EDEXCEL MATHEMATICS (9MA0) - COMPLETE NO-TRUNCATION SCRAPER")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print("Full content preserved - NO truncation!\n")
    
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
        
        # Show sample to verify no truncation
        print("\n[INFO] Sample Level 2 topic (to verify full content):")
        level2_topics = [t for t in topics if t['level'] == 2]
        if level2_topics:
            sample = level2_topics[0]
            print(f"   {sample['title'][:200]}...")
        
        # Upload
        if upload_topics(topics):
            print("\n" + "=" * 80)
            print("[OK] MATHEMATICS COMPLETE!")
            print("=" * 80)
            print(f"\nTotal: {len(topics)} topics with {max(levels.keys())+1} levels")
            print("Full content preserved up to 800+ characters per topic!")
        
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

