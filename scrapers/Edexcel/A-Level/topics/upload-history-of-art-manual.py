"""
Edexcel History of Art (9HT0) - Manual Topic Upload
2 Papers with 3 Themes and 5 Periods
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT = {
    'code': '9HT0',
    'name': 'History of Art',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/history-of-art/2017/specification-and-sample-assessments/specification-and-sample-assessments-GCE-HISOFART-SPEC.pdf'
}

TOPICS = [
    # Level 0: Papers
    {'code': 'Paper1', 'title': 'Paper 1: Visual Analysis and Themes', 'level': 0, 'parent': None},
    {'code': 'Paper2', 'title': 'Paper 2: Periods', 'level': 0, 'parent': None},
    
    # Level 1: Three Themes (under Paper 1)
    {'code': 'B1', 'title': 'Theme B1: Nature in Art and Architecture', 'level': 1, 'parent': 'Paper1'},
    {'code': 'B2', 'title': 'Theme B2: Identities in Art and Architecture', 'level': 1, 'parent': 'Paper1'},
    {'code': 'B3', 'title': 'Theme B3: War in Art and Architecture', 'level': 1, 'parent': 'Paper1'},
    
    # Level 1: Five Periods (under Paper 2)
    {'code': 'C1', 'title': 'Period C1: Invention and Illusion - The Renaissance in Italy (1420-1520)', 'level': 1, 'parent': 'Paper2'},
    {'code': 'C2', 'title': 'Period C2: Power and Persuasion - The Baroque in Catholic Europe (1597-1685)', 'level': 1, 'parent': 'Paper2'},
    {'code': 'C3', 'title': 'Period C3: Rebellion and Revival - The British and French Avant-Garde (1848-99)', 'level': 1, 'parent': 'Paper2'},
    {'code': 'C4', 'title': 'Period C4: Brave New World - Modernism in Europe (1900-39)', 'level': 1, 'parent': 'Paper2'},
    {'code': 'C5', 'title': 'Period C5: Pop Life - British and American Contemporary Art and Architecture (1960-2015)', 'level': 1, 'parent': 'Paper2'},
]


def upload_topics():
    """Upload History of Art topics to Supabase."""
    
    print("=" * 80)
    print("EDEXCEL HISTORY OF ART (9HT0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("\n2 Papers, 3 Themes, 5 Periods\n")
    
    try:
        # Get/create subject
        print("[INFO] Creating/updating subject...")
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
        print("\n[INFO] Clearing old topics...")
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared")
        
        # Insert topics
        print(f"\n[INFO] Uploading {len(TOPICS)} topics...")
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'exam_board': 'Edexcel'
        } for t in TOPICS]
        
        inserted_result = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted_result.data)} topics")
        
        # Link hierarchy
        print("\n[INFO] Linking parent-child relationships...")
        code_to_id = {t['topic_code']: t['id'] for t in inserted_result.data}
        linked = 0
        
        for topic in TOPICS:
            if topic['parent']:
                parent_id = code_to_id.get(topic['parent'])
                child_id = code_to_id.get(topic['code'])
                if parent_id and child_id:
                    supabase.table('staging_aqa_topics').update({
                        'parent_topic_id': parent_id
                    }).eq('id', child_id).execute()
                    linked += 1
        
        print(f"[OK] Linked {linked} relationships")
        
        # Summary
        print("\n" + "=" * 80)
        print("[OK] HISTORY OF ART TOPICS UPLOADED SUCCESSFULLY!")
        print("=" * 80)
        
        levels = {}
        for t in TOPICS:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("\n[INFO] Hierarchy:")
        print(f"   Level 0 (Papers): {levels.get(0, 0)}")
        print(f"   Level 1 (Themes + Periods): {levels.get(1, 0)}")
        print(f"\n   Total: {len(TOPICS)} topics")
        
        print("\n" + "=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = upload_topics()
    sys.exit(0 if success else 1)











