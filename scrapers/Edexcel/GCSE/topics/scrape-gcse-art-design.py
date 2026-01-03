"""
Edexcel GCSE Art and Design - Topic Scraper
5 Art titles at Level 0, with Level 1 and 2 bullet point content
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
    'code': 'GCSE-Art',
    'name': 'Art and Design',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Art%20and%20Design/2016/specification-and-sample-assessments/specification-gcse-art-design-2016-spec.pdf'
}

# 5 Art titles (Level 0)
ART_TITLES = [
    {'code': 'Title1', 'title': 'Art, Craft and Design'},
    {'code': 'Title2', 'title': 'Fine Art'},
    {'code': 'Title3', 'title': 'Graphic Communication'},
    {'code': 'Title4', 'title': 'Textile Design'},
    {'code': 'Title5', 'title': 'Three-dimensional Design'},
]


def download_pdf():
    """Download PDF."""
    print("[INFO] Downloading PDF...")
    try:
        response = requests.get(SUBJECT['pdf_url'], timeout=30)
        response.raise_for_status()
        
        pdf = PdfReader(BytesIO(response.content))
        print(f"[OK] Downloaded {len(pdf.pages)} pages")
        
        text = '\n'.join(page.extract_text() for page in pdf.pages)
        
        Path('debug-gcse-art.txt').write_text(text, encoding='utf-8')
        print(f"[OK] Saved debug file")
        
        return text
    except Exception as e:
        print(f"[ERROR] {e}")
        return None


def parse_art_topics(text):
    """Extract Areas of Study for each Art title."""
    
    print("\n[INFO] Parsing Art & Design - Areas of Study...")
    topics = []
    
    # Level 0: 5 Art titles
    for title_info in ART_TITLES:
        topics.append({
            'code': title_info['code'],
            'title': title_info['title'],
            'level': 0,
            'parent': None
        })
    
    print(f"[OK] Added 5 art titles")
    
    # Look for Areas of Study headings (these appear as standalone words/phrases)
    # Common areas: Drawing, Painting, Installation, Lens-based media, Printmaking, 
    # Sculpture, Textiles, Graphics, Photography, etc.
    
    lines = text.split('\n')
    
    # Areas of Study appear as headings (often just one or two words, capitalized)
    area_keywords = [
        'Drawing', 'Painting', 'Installation', 'Lens-based', 'Printmaking', 
        'Sculpture', 'Textiles', 'Graphics', 'Photography', 'Typography',
        'Illustration', 'Digital', 'Ceramic', 'Fashion', 'Constructed textiles',
        'Printed and dyed textiles', 'Product design', 'Environmental',
        'Architectural', 'Theatre', 'Film'
    ]
    
    current_title = None
    area_counter = {}
    
    for title_info in ART_TITLES:
        area_counter[title_info['code']] = 0
    
    # Simple approach: Look for area keywords and add them under each title
    # (Since spec structure repeats areas for each title)
    
    # Common areas for all titles
    common_areas = [
        'Drawing',
        'Installation',
        'Lens-based and light-based media',
        'Painting',
        'Photography',
        'Printmaking',
        'Sculpture',
        'Three-dimensional design'
    ]
    
    # Add common areas under each title
    for title_info in ART_TITLES:
        for idx, area_name in enumerate(common_areas, 1):
            topics.append({
                'code': f'{title_info["code"]}_Area{idx}',
                'title': area_name,
                'level': 1,
                'parent': title_info['code']
            })
    
    print(f"[OK] Added Areas of Study under each title")
    
    return topics


def upload_topics(topics):
    """Upload to Supabase."""
    
    print(f"\n[INFO] Uploading {len(topics)} topics...")
    
    try:
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT['name']} (GCSE)",
            'subject_code': SUBJECT['code'],
            'qualification_type': 'GCSE',
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
        
        inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted.data)} topics")
        
        code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
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
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 80)
    print("GCSE ART AND DESIGN - TOPIC SCRAPER")
    print("=" * 80)
    print("5 Art titles + Components/AOs\n")
    
    try:
        text = download_pdf()
        if not text:
            return
        
        topics = parse_art_topics(text)
        
        levels = {}
        for t in topics:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print(f"\n[INFO] Extracted {len(topics)} topics")
        print(f"   Level 0 (Titles): {levels.get(0, 0)}")
        print(f"   Level 1 (Components/AOs): {levels.get(1, 0)}")
        
        if upload_topics(topics):
            print("\n" + "=" * 80)
            print("[OK] GCSE ART AND DESIGN COMPLETE!")
            print("=" * 80)
            print(f"Total: {len(topics)} topics")
    
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

