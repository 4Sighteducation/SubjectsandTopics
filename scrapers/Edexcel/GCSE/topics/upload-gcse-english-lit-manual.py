"""
GCSE English Literature - Manual Upload
========================================

Simple structure:
Level 0: 2 Components
Level 1: Set texts (Shakespeare, novels, plays, poetry collections)

No scraping needed - just a clean list!
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
    'code': 'GCSE-EnglishLit',
    'name': 'English Literature',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/English%20Literature/2015/specification-and-sample-assesment/9781446914359_GCSE_2015_L12_Englit.pdf'
}

# The complete topic structure
TOPICS = [
    # Level 0: Components
    {
        'code': 'Component1',
        'title': 'Component 1: Shakespeare and Post-1914 Literature',
        'level': 0,
        'parent': None
    },
    {
        'code': 'Component2',
        'title': 'Component 2: 19th-century Novel and Poetry since 1789',
        'level': 0,
        'parent': None
    },
    
    # Level 1: Component 1 - Shakespeare texts
    {
        'code': 'Component1_Shakespeare',
        'title': 'Shakespeare (choose one)',
        'level': 1,
        'parent': 'Component1'
    },
    {
        'code': 'Component1_Shakespeare_Macbeth',
        'title': 'Macbeth',
        'level': 2,
        'parent': 'Component1_Shakespeare'
    },
    {
        'code': 'Component1_Shakespeare_TheTempest',
        'title': 'The Tempest',
        'level': 2,
        'parent': 'Component1_Shakespeare'
    },
    {
        'code': 'Component1_Shakespeare_RomeoJuliet',
        'title': 'Romeo and Juliet',
        'level': 2,
        'parent': 'Component1_Shakespeare'
    },
    {
        'code': 'Component1_Shakespeare_MuchAdo',
        'title': 'Much Ado About Nothing',
        'level': 2,
        'parent': 'Component1_Shakespeare'
    },
    {
        'code': 'Component1_Shakespeare_TwelfthNight',
        'title': 'Twelfth Night',
        'level': 2,
        'parent': 'Component1_Shakespeare'
    },
    {
        'code': 'Component1_Shakespeare_Merchant',
        'title': 'The Merchant of Venice',
        'level': 2,
        'parent': 'Component1_Shakespeare'
    },
    
    # Level 1: Component 1 - Post-1914 texts
    {
        'code': 'Component1_Post1914',
        'title': 'Post-1914 British Play or Novel (choose one)',
        'level': 1,
        'parent': 'Component1'
    },
    {
        'code': 'Component1_Post1914_InspectorCalls',
        'title': 'An Inspector Calls - J B Priestley',
        'level': 2,
        'parent': 'Component1_Post1914'
    },
    {
        'code': 'Component1_Post1914_HobsonsChoice',
        'title': "Hobson's Choice - Harold Brighouse",
        'level': 2,
        'parent': 'Component1_Post1914'
    },
    {
        'code': 'Component1_Post1914_BloodBrothers',
        'title': 'Blood Brothers - Willy Russell',
        'level': 2,
        'parent': 'Component1_Post1914'
    },
    {
        'code': 'Component1_Post1914_JourneysEnd',
        'title': "Journey's End - R C Sherriff",
        'level': 2,
        'parent': 'Component1_Post1914'
    },
    {
        'code': 'Component1_Post1914_AnimalFarm',
        'title': 'Animal Farm - George Orwell',
        'level': 2,
        'parent': 'Component1_Post1914'
    },
    {
        'code': 'Component1_Post1914_LordFlies',
        'title': 'Lord of the Flies - William Golding',
        'level': 2,
        'parent': 'Component1_Post1914'
    },
    {
        'code': 'Component1_Post1914_AnitaMe',
        'title': 'Anita and Me - Meera Syal',
        'level': 2,
        'parent': 'Component1_Post1914'
    },
    {
        'code': 'Component1_Post1914_WomanBlack',
        'title': 'The Woman in Black - Susan Hill',
        'level': 2,
        'parent': 'Component1_Post1914'
    },
    {
        'code': 'Component1_Post1914_Empress',
        'title': 'The Empress - Tanika Gupta',
        'level': 2,
        'parent': 'Component1_Post1914'
    },
    {
        'code': 'Component1_Post1914_RefugeeBoy',
        'title': 'Refugee Boy - Benjamin Zephaniah (adapted by Lemn Sissay)',
        'level': 2,
        'parent': 'Component1_Post1914'
    },
    {
        'code': 'Component1_Post1914_CoramBoy',
        'title': 'Coram Boy - Jamila Gavin',
        'level': 2,
        'parent': 'Component1_Post1914'
    },
    {
        'code': 'Component1_Post1914_BoysDontCry',
        'title': "Boys Don't Cry - Malorie Blackman",
        'level': 2,
        'parent': 'Component1_Post1914'
    },
    
    # Level 1: Component 2 - 19th-century novels
    {
        'code': 'Component2_19thCentury',
        'title': '19th-century Novel (choose one)',
        'level': 1,
        'parent': 'Component2'
    },
    {
        'code': 'Component2_19thCentury_JaneEyre',
        'title': 'Jane Eyre - Charlotte Brontë',
        'level': 2,
        'parent': 'Component2_19thCentury'
    },
    {
        'code': 'Component2_19thCentury_GreatExpectations',
        'title': 'Great Expectations - Charles Dickens',
        'level': 2,
        'parent': 'Component2_19thCentury'
    },
    {
        'code': 'Component2_19thCentury_JekyllHyde',
        'title': 'Dr Jekyll and Mr Hyde - R L Stevenson',
        'level': 2,
        'parent': 'Component2_19thCentury'
    },
    {
        'code': 'Component2_19thCentury_ChristmasCarol',
        'title': 'A Christmas Carol - Charles Dickens',
        'level': 2,
        'parent': 'Component2_19thCentury'
    },
    {
        'code': 'Component2_19thCentury_PridePrejudice',
        'title': 'Pride and Prejudice - Jane Austen',
        'level': 2,
        'parent': 'Component2_19thCentury'
    },
    {
        'code': 'Component2_19thCentury_SilasMarner',
        'title': 'Silas Marner - George Eliot',
        'level': 2,
        'parent': 'Component2_19thCentury'
    },
    {
        'code': 'Component2_19thCentury_Frankenstein',
        'title': 'Frankenstein - Mary Shelley',
        'level': 2,
        'parent': 'Component2_19thCentury'
    },
    
    # Level 1: Component 2 - Poetry collections
    {
        'code': 'Component2_Poetry',
        'title': 'Pearson Poetry Anthology Collections (choose one)',
        'level': 1,
        'parent': 'Component2'
    },
    {
        'code': 'Component2_Poetry_Relationships',
        'title': 'Relationships',
        'level': 2,
        'parent': 'Component2_Poetry'
    },
    {
        'code': 'Component2_Poetry_Conflict',
        'title': 'Conflict',
        'level': 2,
        'parent': 'Component2_Poetry'
    },
    {
        'code': 'Component2_Poetry_TimePlace',
        'title': 'Time and Place',
        'level': 2,
        'parent': 'Component2_Poetry'
    },
    {
        'code': 'Component2_Poetry_Belonging',
        'title': 'Belonging',
        'level': 2,
        'parent': 'Component2_Poetry'
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
        print("[SUCCESS] GCSE ENGLISH LITERATURE UPLOADED!")
        print("=" * 80)
        print(f"   Level 0: {levels[0]} components")
        print(f"   Level 1: {levels[1]} categories (Shakespeare, Post-1914, Novel, Poetry)")
        print(f"   Level 2: {levels[2]} set texts")
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
    print("GCSE ENGLISH LITERATURE - MANUAL UPLOAD")
    print("=" * 80)
    print("Simple structure: Components → Categories → Set Texts")
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

