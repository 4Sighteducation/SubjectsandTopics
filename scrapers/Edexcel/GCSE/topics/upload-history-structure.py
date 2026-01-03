"""
GCSE History - Basic Structure Upload (Papers and Options Only)
=================================================================

Level 0: Papers (3 papers)
Level 1: Options (14 options total)
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

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT = {
    'code': 'GCSE-History',
    'name': 'History',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/History/2016/specification-and-sample-assessments/gcse-9-1-history-specification.pdf'
}

TOPICS = [
    # ========== LEVEL 0: PAPERS ==========
    
    {'code': 'Paper1', 'title': 'Paper 1: Thematic study and historic environment', 'level': 0, 'parent': None},
    {'code': 'Paper2', 'title': 'Paper 2: Period study and British depth study', 'level': 0, 'parent': None},
    {'code': 'Paper3', 'title': 'Paper 3: Modern depth study', 'level': 0, 'parent': None},
    
    # ========== LEVEL 1: SECTIONS (for Paper 2 only) ==========
    
    # Paper 2 sections
    {'code': 'Paper2_BritishDepth', 'title': 'British Depth Studies', 'level': 1, 'parent': 'Paper2'},
    {'code': 'Paper2_PeriodStudies', 'title': 'Period Studies', 'level': 1, 'parent': 'Paper2'},
    
    # ========== LEVEL 1 (Paper 1) or LEVEL 2 (Paper 2): OPTIONS ==========
    
    # Paper 1 Options (Level 1)
    {'code': 'Paper1_Opt10', 'title': 'Option 10: Crime and punishment in Britain, c1000–present and Whitechapel, c1870–c1900', 'level': 1, 'parent': 'Paper1'},
    {'code': 'Paper1_Opt11', 'title': 'Option 11: Medicine in Britain, c1250–present and The British sector of the Western Front, 1914–18', 'level': 1, 'parent': 'Paper1'},
    {'code': 'Paper1_Opt12', 'title': 'Option 12: Warfare and British society, c1250–present and London and the Second World War, 1939–45', 'level': 1, 'parent': 'Paper1'},
    {'code': 'Paper1_Opt13', 'title': 'Option 13: Migrants in Britain, c800–present and Notting Hill, c1948–c1970', 'level': 1, 'parent': 'Paper1'},
    
    # Paper 2 British Depth Study Options (Level 2)
    {'code': 'Paper2_OptB1', 'title': 'Option B1: Anglo-Saxon and Norman England, c1060–88', 'level': 2, 'parent': 'Paper2_BritishDepth'},
    {'code': 'Paper2_OptB2', 'title': 'Option B2: The reigns of King Richard I and King John, 1189–1216', 'level': 2, 'parent': 'Paper2_BritishDepth'},
    {'code': 'Paper2_OptB3', 'title': 'Option B3: Henry VIII and his ministers, 1509–40', 'level': 2, 'parent': 'Paper2_BritishDepth'},
    {'code': 'Paper2_OptB4', 'title': 'Option B4: Early Elizabethan England, 1558–88', 'level': 2, 'parent': 'Paper2_BritishDepth'},
    
    # Paper 2 Period Study Options (Level 2)
    {'code': 'Paper2_OptP1', 'title': 'Option P1: Spain and the New World, c1490–c1555', 'level': 2, 'parent': 'Paper2_PeriodStudies'},
    {'code': 'Paper2_OptP2', 'title': 'Option P2: British America, 1713–83: empire and revolution', 'level': 2, 'parent': 'Paper2_PeriodStudies'},
    {'code': 'Paper2_OptP4', 'title': 'Option P4: Superpower relations and the Cold War, 1941–91', 'level': 2, 'parent': 'Paper2_PeriodStudies'},
    
    # Paper 3 Options (Level 1)
    {'code': 'Paper3_Opt30', 'title': 'Option 30: Russia and the Soviet Union, 1917–41', 'level': 1, 'parent': 'Paper3'},
    {'code': 'Paper3_Opt31', 'title': 'Option 31: Weimar and Nazi Germany, 1918–39', 'level': 1, 'parent': 'Paper3'},
    {'code': 'Paper3_Opt32', 'title': "Option 32: Mao's China, 1945–76", 'level': 1, 'parent': 'Paper3'},
    {'code': 'Paper3_Opt33', 'title': 'Option 33: The USA, 1954–75: conflict at home and abroad', 'level': 1, 'parent': 'Paper3'},
]


def upload_topics():
    """Upload to Supabase."""
    print(f"\n[INFO] Uploading {len(TOPICS)} topics for History...")
    
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
        print("[SUCCESS] GCSE HISTORY - BASIC STRUCTURE UPLOADED!")
        print("=" * 80)
        print(f"   Level 0 (Papers): {levels[0]}")
        print(f"   Level 1 (Options): {levels[1]}")
        print(f"\n   Total: {len(TOPICS)} topics")
        print("=" * 80)
        print("\nNext: Add detailed content for each option as needed")
        
        return subject_id
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("=" * 80)
    print("GCSE HISTORY - BASIC STRUCTURE (PAPERS + OPTIONS)")
    print("=" * 80)
    
    try:
        subject_id = upload_topics()
        
        if subject_id:
            print("\n✅ COMPLETE!")
            print(f"\nSubject ID: {subject_id}")
        else:
            print("\n❌ FAILED")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

