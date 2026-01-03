"""
Edexcel English Language & Literature (9EL0) - Manual Topic Upload
2 examined components with prescribed texts
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
    'code': '9EL0',
    'name': 'English Language and Literature',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/English%20Language%20and%20Literature/2015/Specification%20and%20sample%20assessments/Pearson_Edexcel_Level_3_GCE_in_English_Language_and_Literature_Specification_issue6.pdf'
}

def create_topics():
    """Create English Language & Literature topics."""
    topics = []
    
    # Level 0: Components (skip NEA)
    topics.extend([
        {'code': 'Component1', 'title': 'Component 1: Voices in Speech and Writing', 'level': 0, 'parent': None},
        {'code': 'Component2', 'title': 'Component 2: Varieties in Language and Literature', 'level': 0, 'parent': None},
    ])
    
    # Component 1 - Level 1
    topics.extend([
        {'code': 'C1-VoiceConcept', 'title': 'The Concept of Voice', 'level': 1, 'parent': 'Component1'},
        {'code': 'C1-DramaTexts', 'title': 'Prescribed Drama Texts', 'level': 1, 'parent': 'Component1'},
    ])
    
    # Component 1 - Prescribed Drama Texts (Level 2)
    drama_texts = [
        'All My Sons, Arthur Miller',
        'A Streetcar Named Desire, Tennessee Williams',
        "Elmina's Kitchen, Kwame Kwei-Armah",
        'Equus, Peter Shaffer',
        'The History Boys, Alan Bennett',
        'Top Girls, Caryl Churchill',
        'Translations, Brian Friel'
    ]
    
    for i, text in enumerate(drama_texts, 1):
        topics.append({
            'code': f'C1-Drama{i}',
            'title': text,
            'level': 2,
            'parent': 'C1-DramaTexts'
        })
    
    # Component 2 - Level 1
    topics.extend([
        {'code': 'C2-SocietyIndividual', 'title': 'Society and the Individual', 'level': 1, 'parent': 'Component2'},
        {'code': 'C2-LoveLoss', 'title': 'Love and Loss', 'level': 1, 'parent': 'Component2'},
    ])
    
    # Component 2 - Society and the Individual (Level 2)
    topics.extend([
        {'code': 'C2-SI-Chaucer', 'title': "The Wife of Bath's Prologue and Tale (Geoffrey Chaucer)", 'level': 2, 'parent': 'C2-SocietyIndividual'},
        {'code': 'C2-SI-Larkin', 'title': 'The Whitsun Weddings (Philip Larkin)', 'level': 2, 'parent': 'C2-SocietyIndividual'},
    ])
    
    # Component 2 - Love and Loss - Metaphysical Poets (Level 2)
    topics.append({
        'code': 'C2-LL-Metaphysical',
        'title': 'Metaphysical Poetry Collection',
        'level': 2,
        'parent': 'C2-LoveLoss'
    })
    
    # Metaphysical poets (Level 3)
    metaphysical_poets = [
        'John Donne',
        'Edward, Lord Herbert of Cherbury',
        'George Herbert',
        'Owen Felltham',
        'Sidney Godolphin',
        'Anne Bradstreet',
        'Abraham Cowley',
        'Andrew Marvell',
        'Katherine Philips'
    ]
    
    for i, poet in enumerate(metaphysical_poets, 1):
        topics.append({
            'code': f'C2-LL-Poet{i}',
            'title': poet,
            'level': 3,
            'parent': 'C2-LL-Metaphysical'
        })
    
    return topics

def upload_topics(topics):
    """Upload to Supabase."""
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
    print("EDEXCEL ENGLISH LANGUAGE & LITERATURE (9EL0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    
    try:
        topics = create_topics()
        
        levels = {}
        for t in topics:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print(f"\n[INFO] Created {len(topics)} topics")
        print("\n   Level distribution:")
        for l in sorted(levels.keys()):
            print(f"   Level {l}: {levels[l]} topics")
        
        upload_topics(topics)
        
        print("\n" + "=" * 80)
        print("[OK] ENGLISH LANGUAGE & LITERATURE COMPLETE!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
