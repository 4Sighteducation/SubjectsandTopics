"""
GCSE English Language - Manual Upload
======================================

Structure:
Level 0: 2 Components
Level 1: Reading & Writing skills
Level 2: Specific skills and text types
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT = {
    'code': 'GCSE-EnglishLang',
    'name': 'English Language',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/English%20Language/2015/specification-and-sample-assesment/gcse-2015-englang-spec.pdf'
}

# Complete topic structure
TOPICS = [
    # Level 0: Components
    {
        'code': 'Component1',
        'title': 'Component 1: Fiction and Imaginative Writing',
        'level': 0,
        'parent': None
    },
    {
        'code': 'Component2',
        'title': 'Component 2: Non-fiction and Transactional Writing',
        'level': 0,
        'parent': None
    },
    
    # === COMPONENT 1 ===
    
    # Level 1: Main skills
    {
        'code': 'Component1_Reading',
        'title': '1.1 Reading',
        'level': 1,
        'parent': 'Component1'
    },
    {
        'code': 'Component1_Writing',
        'title': '1.2 Writing',
        'level': 1,
        'parent': 'Component1'
    },
    
    # Level 2: Reading skills
    {
        'code': 'Component1_Reading_1.1.1',
        'title': '1.1.1 Reading prose fiction: Read and understand a range of prose fiction texts, including unseen passages',
        'level': 2,
        'parent': 'Component1_Reading'
    },
    {
        'code': 'Component1_Reading_1.1.2',
        'title': '1.1.2 Critical reading and comprehension: Identify and interpret themes, ideas and information; draw inferences and justify with evidence; evaluate usefulness and presentation of content; distinguish between supported and unsupported statements; recognise bias and misuse of evidence',
        'level': 2,
        'parent': 'Component1_Reading'
    },
    {
        'code': 'Component1_Reading_1.1.3',
        'title': '1.1.3 Summary skills: Identify main themes and summarise ideas and information from a single text',
        'level': 2,
        'parent': 'Component1_Reading'
    },
    {
        'code': 'Component1_Reading_1.1.4',
        'title': "1.1.4 Evaluation of writer's choices: Explain and illustrate how vocabulary, grammar, form and structure contribute to effectiveness and impact using accurate linguistic and literary terminology",
        'level': 2,
        'parent': 'Component1_Reading'
    },
    
    # Level 2: Writing skills
    {
        'code': 'Component1_Writing_1.2.1',
        'title': '1.2.1 Producing clear and coherent text: Write accurately for different purposes and audiences (describe, narrate, explain, instruct, argue); select vocabulary, grammar, form and structure appropriately; use language imaginatively and creatively; maintain consistent point of view and coherence',
        'level': 2,
        'parent': 'Component1_Writing'
    },
    {
        'code': 'Component1_Writing_1.2.2',
        'title': '1.2.2 Writing for impact: Select and emphasise key points; cite evidence effectively; create emotional impact; use persuasive and rhetorical devices (rhetorical questions, antithesis, parenthesis)',
        'level': 2,
        'parent': 'Component1_Writing'
    },
    
    # === COMPONENT 2 ===
    
    # Level 1: Main skills
    {
        'code': 'Component2_Reading',
        'title': '2.1 Reading Non-fiction',
        'level': 1,
        'parent': 'Component2'
    },
    {
        'code': 'Component2_Writing',
        'title': '2.2 Transactional Writing',
        'level': 1,
        'parent': 'Component2'
    },
    
    # Level 2: Reading non-fiction
    {
        'code': 'Component2_Reading_2.1.1',
        'title': '2.1.1 Study 20th and 21st-century non-fiction texts: Study a range of non-fiction texts including literary non-fiction',
        'level': 2,
        'parent': 'Component2_Reading'
    },
    {
        'code': 'Component2_Reading_2.1.2',
        'title': '2.1.2 Analysis and evaluation: Analyse, evaluate and compare non-fiction extracts',
        'level': 2,
        'parent': 'Component2_Reading'
    },
    
    # Level 2: Transactional writing
    {
        'code': 'Component2_Writing_2.2.1',
        'title': '2.2.1 Writing techniques: Develop non-fiction writing techniques including planning and proofreading skills',
        'level': 2,
        'parent': 'Component2_Writing'
    },
    {
        'code': 'Component2_Writing_2.2.2',
        'title': '2.2.2 SPaG: Use spelling, punctuation and grammar accurately',
        'level': 2,
        'parent': 'Component2_Writing'
    },
    {
        'code': 'Component2_Writing_TextTypes',
        'title': '2.2.3 Transactional text types',
        'level': 2,
        'parent': 'Component2_Writing'
    },
    
    # Level 3: Specific text types
    {
        'code': 'Component2_Writing_TextTypes_Article',
        'title': 'Article',
        'level': 3,
        'parent': 'Component2_Writing_TextTypes'
    },
    {
        'code': 'Component2_Writing_TextTypes_Letter',
        'title': 'Letter',
        'level': 3,
        'parent': 'Component2_Writing_TextTypes'
    },
    {
        'code': 'Component2_Writing_TextTypes_Review',
        'title': 'Review',
        'level': 3,
        'parent': 'Component2_Writing_TextTypes'
    },
    {
        'code': 'Component2_Writing_TextTypes_Speech',
        'title': 'Text for a speech',
        'level': 3,
        'parent': 'Component2_Writing_TextTypes'
    },
    {
        'code': 'Component2_Writing_TextTypes_InformationalTexts',
        'title': 'Section for guide/textbook/leaflet/booklet',
        'level': 3,
        'parent': 'Component2_Writing_TextTypes'
    }
]


def upload_topics():
    """Upload to Supabase."""
    print(f"\n[INFO] Uploading {len(TOPICS)} topics...")
    
    try:
        # Create/update subject
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT['name']} ({SUBJECT['qualification']})",
            'subject_code': SUBJECT['code'],
            'qualification_type': SUBJECT['qualification'],
            'specification_url': SUBJECT['pdf_url'],
            'exam_board': SUBJECT['exam_board']
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
            'exam_board': SUBJECT['exam_board']
        } for t in TOPICS]
        
        inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted.data)} topics")
        
        # Link parent relationships
        code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
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
        
        print(f"[OK] Linked {linked} parent-child relationships")
        
        # Summary
        levels = defaultdict(int)
        for t in TOPICS:
            levels[t['level']] += 1
        
        print("\n" + "=" * 80)
        print("[SUCCESS] GCSE ENGLISH LANGUAGE UPLOADED!")
        print("=" * 80)
        print(f"   Level 0: {levels[0]} components")
        print(f"   Level 1: {levels[1]} skill areas (Reading/Writing)")
        print(f"   Level 2: {levels[2]} specific skills")
        print(f"   Level 3: {levels.get(3, 0)} text types")
        print(f"\n   Total: {len(TOPICS)} topics")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 80)
    print("GCSE ENGLISH LANGUAGE - MANUAL UPLOAD")
    print("=" * 80)
    print("Structure: Components -> Reading/Writing -> Skills -> Text Types")
    print("=" * 80)
    
    try:
        success = upload_topics()
        
        if success:
            print("\n✅ COMPLETE!")
        else:
            print("\n❌ FAILED")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

