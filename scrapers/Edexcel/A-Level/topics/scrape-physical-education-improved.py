"""
Edexcel Physical Education (9PE1) - Improved Topic Scraper  
Extracts deep hierarchy: Papers → Components → Topics → Subtopics → Learning Points (4-5 levels)
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
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Physical%20Education/2016/Specification%20and%20sample%20assessments/a-level-pe-specification.pdf'
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
        Path('debug-pe-spec.txt').write_text(full_text, encoding='utf-8')
        print(f"[OK] Saved debug file")
        
        return full_text
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return None


def parse_pe_topics(text):
    """Parse PE topics with DEEP hierarchy (4-5 levels)."""
    
    print("\n[INFO] Parsing Physical Education topics with deep hierarchy...")
    topics = []
    
    # Level 0: Components
    components = [
        {'code': 'Comp1', 'title': 'Component 1: Fitness and Body Systems', 'level': 0, 'parent': None},
        {'code': 'Comp2', 'title': 'Component 2: Exercise Physiology and Biomechanics', 'level': 0, 'parent': None},
        {'code': 'Comp3', 'title': 'Component 3: Sport Psychology, Sport and Society and Technology in Sport', 'level': 0, 'parent': None},
    ]
    topics.extend(components)
    
    lines = text.split('\n')
    
    # Look for topic patterns in PE:
    # Pattern 1: Section headers (1.1, 2.1, etc. with capital letters)
    # Pattern 2: Sub-sections (a), b), c))
    # Pattern 3: Learning points (o markers or bullets)
    
    current_component = None
    current_major_topic = None
    current_subtopic = None
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Match section numbers: 1.1, 1.2, 2.1, etc.
        section_match = re.match(r'^(\d)\.(\d{1,2})\s+([A-Z][^(]+)', line_stripped)
        if section_match:
            comp_num = section_match.group(1)
            topic_num = section_match.group(2)
            title = section_match.group(3).strip()
            
            # Clean title
            title = re.sub(r'\s+', ' ', title)
            if len(title) > 150:
                title = title[:150]
            
            if len(title) > 5:
                # Assign to component
                parent_comp = f'Comp{comp_num}'
                topic_code = f'C{comp_num}T{topic_num}'
                
                # Check if this is a new major topic
                if not any(t['code'] == topic_code for t in topics):
                    topics.append({
                        'code': topic_code,
                        'title': f'{comp_num}.{topic_num} {title}',
                        'level': 1,
                        'parent': parent_comp
                    })
                    current_major_topic = topic_code
        
        # Match subsections: a), b), c), d), etc.
        subsection_match = re.match(r'^([a-z])\)\s+(.+?)$', line_stripped)
        if subsection_match and current_major_topic:
            letter = subsection_match.group(1)
            title = subsection_match.group(2).strip()
            
            # Clean title
            title = re.sub(r'\s+', ' ', title)
            if len(title) > 150:
                title = title[:150]
            
            if len(title) > 3:
                subsection_code = f'{current_major_topic}_{letter}'
                if not any(t['code'] == subsection_code for t in topics):
                    topics.append({
                        'code': subsection_code,
                        'title': f'{letter}) {title}',
                        'level': 2,
                        'parent': current_major_topic
                    })
                    current_subtopic = subsection_code
        
        # Match sub-points: o markers or roman numerals (i), ii), etc.
        subpoint_match = re.match(r'^(?:o|[ovi]{1,3}\))\s+(.+?)$', line_stripped)
        if subpoint_match and current_subtopic and len(line_stripped) > 3:
            title = subpoint_match.group(1).strip()
            
            # Clean title
            title = re.sub(r'\s+', ' ', title)
            
            if len(title) > 3 and len(title) < 150:
                # Create unique code
                subpoint_code = f'{current_subtopic}_{len(topics)}'
                topics.append({
                    'code': subpoint_code,
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
    print("EDEXCEL PHYSICAL EDUCATION (9PE1) - IMPROVED TOPIC SCRAPER")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}\n")
    
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
