"""
Edexcel GCSE Drama (1DR0) - Manual Topic Upload
ONLY Component 3: Theatre Makers in Practice (examined written component)
12 prescribed performance texts + Live Theatre Evaluation
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
    'code': 'GCSE-Drama',
    'name': 'Drama',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Drama/2016/Specification%20and%20sample%20assessments/gcse2016-l12-drama.pdf'
}

TOPICS = [
    # Level 0: Component 3 (ONLY examined written component)
    {'code': 'Component3', 'title': 'Component 3: Theatre Makers in Practice (Written Exam)', 'level': 0, 'parent': None},
    
    # Level 1: Sections
    {'code': 'SectionA', 'title': 'Section A: Bringing Texts to Life', 'level': 1, 'parent': 'Component3'},
    {'code': 'SectionB', 'title': 'Section B: Live Theatre Evaluation', 'level': 1, 'parent': 'Component3'},
    
    # Level 2: Text Lists
    {'code': 'ListA', 'title': 'List A: Pre-1954 Performance Texts (Choose 1)', 'level': 2, 'parent': 'SectionA'},
    {'code': 'ListB', 'title': 'List B: Post-2000 Performance Texts (Choose 1)', 'level': 2, 'parent': 'SectionA'},
    
    # Level 3: List A Texts (Pre-1954)
    {'code': 'ListA-1', 'title': "A Doll's House by Henrik Ibsen (adapted by Tanika Gupta) - Historical drama", 'level': 3, 'parent': 'ListA'},
    {'code': 'ListA-2', 'title': 'An Inspector Calls by J B Priestley - Social thriller/mystery', 'level': 3, 'parent': 'ListA'},
    {'code': 'ListA-3', 'title': 'Antigone by Sophocles (adapted by Roy Williams) - Tragedy', 'level': 3, 'parent': 'ListA'},
    {'code': 'ListA-4', 'title': 'Government Inspector by Nikolai Gogol (adapted by David Harrower) - Black comedy', 'level': 3, 'parent': 'ListA'},
    {'code': 'ListA-5', 'title': 'The Crucible by Arthur Miller - Historical drama', 'level': 3, 'parent': 'ListA'},
    {'code': 'ListA-6', 'title': 'Twelfth Night by William Shakespeare - Romantic comedy', 'level': 3, 'parent': 'ListA'},
    
    # Level 3: List B Texts (Post-2000)
    {'code': 'ListB-1', 'title': '100 by Diene Petterle, Neil Monaghan and Christopher Heimann - Ensemble story-telling', 'level': 3, 'parent': 'ListB'},
    {'code': 'ListB-2', 'title': '1984 by George Orwell, Robert Icke and Duncan Macmillan - Political satire', 'level': 3, 'parent': 'ListB'},
    {'code': 'ListB-3', 'title': 'Blue Stockings by Jessica Swale - Historical drama', 'level': 3, 'parent': 'ListB'},
    {'code': 'ListB-4', 'title': 'DNA by Dennis Kelly - Black comedy', 'level': 3, 'parent': 'ListB'},
    {'code': 'ListB-5', 'title': 'The Free9 by In-Sook Chappell - Tragedy/ensemble story-telling', 'level': 3, 'parent': 'ListB'},
    {'code': 'ListB-6', 'title': 'Gone Too Far! by Bola Agbaje - Social drama', 'level': 3, 'parent': 'ListB'},
    
    # Level 2: Live Theatre Evaluation
    {'code': 'LiveTheatre', 'title': 'Live Theatre Evaluation (Analysis of one performance)', 'level': 2, 'parent': 'SectionB'},
    
    # Level 3: Evaluation Focus Areas
    {'code': 'LT-Performers', 'title': 'Analysis of performers and specific roles', 'level': 3, 'parent': 'LiveTheatre'},
    {'code': 'LT-Design', 'title': 'Design elements (costume, set, lighting, sound)', 'level': 3, 'parent': 'LiveTheatre'},
    {'code': 'LT-Director', 'title': "Director's concept and performance style", 'level': 3, 'parent': 'LiveTheatre'},
    {'code': 'LT-Impact', 'title': 'Impact on audience and communication of ideas', 'level': 3, 'parent': 'LiveTheatre'},
]


def upload_topics():
    """Upload GCSE Drama topics to Supabase."""
    
    print("=" * 80)
    print("EDEXCEL GCSE DRAMA - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("\nFocused on Component 3 (examined written component) ONLY\n")
    
    try:
        # Get/create subject
        print("[INFO] Creating/updating subject...")
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT['name']} (GCSE)",
            'subject_code': SUBJECT['code'],
            'qualification_type': 'GCSE',
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
        print("[OK] GCSE DRAMA TOPICS UPLOADED SUCCESSFULLY!")
        print("=" * 80)
        
        levels = {}
        for t in TOPICS:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("\n[INFO] Hierarchy:")
        print(f"   Level 0 (Component): {levels.get(0, 0)}")
        print(f"   Level 1 (Sections): {levels.get(1, 0)}")
        print(f"   Level 2 (Lists/Areas): {levels.get(2, 0)}")
        print(f"   Level 3 (Texts/Focus): {levels.get(3, 0)}")
        print(f"\n   Total: {len(TOPICS)} topics")
        print("\nFocused on EXAMINED content only (Component 3)")
        
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

