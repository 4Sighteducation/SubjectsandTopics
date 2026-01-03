"""
Add ONLY Paper 2 Level 1 sections (British Depth Studies, Period Studies)
and Level 2 options (B1-B4, P1, P2, P4)

Does NOT delete anything - just adds missing structure
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT_CODE = 'GCSE-History'

# Only the missing Paper 2 structure
TOPICS_TO_ADD = [
    # Level 1: Sections
    {'code': 'Paper2_BritishDepth', 'title': 'British Depth Studies', 'level': 1, 'parent': 'Paper2'},
    {'code': 'Paper2_PeriodStudies', 'title': 'Period Studies', 'level': 1, 'parent': 'Paper2'},
    
    # Level 2: B options
    {'code': 'Paper2_OptB1', 'title': 'Option B1: Anglo-Saxon and Norman England, c1060–88', 'level': 2, 'parent': 'Paper2_BritishDepth'},
    {'code': 'Paper2_OptB2', 'title': 'Option B2: The reigns of King Richard I and King John, 1189–1216', 'level': 2, 'parent': 'Paper2_BritishDepth'},
    {'code': 'Paper2_OptB3', 'title': 'Option B3: Henry VIII and his ministers, 1509–40', 'level': 2, 'parent': 'Paper2_BritishDepth'},
    {'code': 'Paper2_OptB4', 'title': 'Option B4: Early Elizabethan England, 1558–88', 'level': 2, 'parent': 'Paper2_BritishDepth'},
    
    # Level 2: P options
    {'code': 'Paper2_OptP1', 'title': 'Option P1: Spain and the New World, c1490–c1555', 'level': 2, 'parent': 'Paper2_PeriodStudies'},
    {'code': 'Paper2_OptP2', 'title': 'Option P2: British America, 1713–83: empire and revolution', 'level': 2, 'parent': 'Paper2_PeriodStudies'},
    {'code': 'Paper2_OptP3', 'title': 'Option P3: The American West, c1835–c1895', 'level': 2, 'parent': 'Paper2_PeriodStudies'},
    {'code': 'Paper2_OptP4', 'title': 'Option P4: Superpower relations and the Cold War, 1941–91', 'level': 2, 'parent': 'Paper2_PeriodStudies'},
    {'code': 'Paper2_OptP5', 'title': 'Option P5: Conflict in the Middle East, 1945–95', 'level': 2, 'parent': 'Paper2_PeriodStudies'},
]


def add_paper2_sections():
    """Add Paper 2 sections without deleting anything."""
    print(f"\n[INFO] Adding Paper 2 sections...")
    
    try:
        subject_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', SUBJECT_CODE).eq('qualification_type', 'GCSE').eq('exam_board', 'Edexcel').execute()
        
        if not subject_result.data:
            print("[ERROR] History subject not found!")
            return None
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        # Get existing topics
        existing_topics = supabase.table('staging_aqa_topics').select('*').eq('subject_id', subject_id).execute()
        code_to_id = {t['topic_code']: t['id'] for t in existing_topics.data}
        
        # Only add topics that don't already exist
        to_insert = []
        for t in TOPICS_TO_ADD:
            if t['code'] not in code_to_id:
                to_insert.append({
                    'subject_id': subject_id,
                    'topic_code': t['code'],
                    'topic_name': t['title'],
                    'topic_level': t['level'],
                    'exam_board': 'Edexcel'
                })
        
        if to_insert:
            inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
            print(f"[OK] Added {len(inserted.data)} new topics")
            
            # Update code_to_id
            for t in inserted.data:
                code_to_id[t['topic_code']] = t['id']
        else:
            print("[OK] All sections already exist")
        
        # Link parent relationships
        linked = 0
        for topic in TOPICS_TO_ADD:
            if topic['parent']:
                parent_id = code_to_id.get(topic['parent'])
                child_id = code_to_id.get(topic['code'])
                if parent_id and child_id:
                    supabase.table('staging_aqa_topics').update({
                        'parent_topic_id': parent_id
                    }).eq('id', child_id).execute()
                    linked += 1
        
        print(f"[OK] Linked {linked} relationships")
        
        print("\n" + "=" * 80)
        print("[SUCCESS] PAPER 2 SECTIONS ADDED!")
        print("=" * 80)
        print(f"   Added/verified: {len(TOPICS_TO_ADD)} topics")
        print("=" * 80)
        
        return subject_id
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("=" * 80)
    print("ADD PAPER 2 SECTIONS ONLY (SAFE - NO DELETIONS)")
    print("=" * 80)
    
    try:
        subject_id = add_paper2_sections()
        
        if subject_id:
            print("\n✅ COMPLETE!")
        else:
            print("\n❌ FAILED")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

