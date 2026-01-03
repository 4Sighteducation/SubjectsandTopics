"""
GCSE History - Paper 3: Options 30 and 31
==========================================

Option 30: Russia and the Soviet Union
Option 31: Weimar and Nazi Germany

Structure: 4 Key topics each (Paper 3 has 4, not 3 like Paper 2)
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
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

NEW_TOPICS = [
    # ========== OPTION 30: RUSSIA AND THE SOVIET UNION ==========
    
    # Level 3: Key topics (4 topics for Paper 3)
    {'code': 'Paper3_Opt30_KT1', 'title': 'Key topic 1: The revolutions of 1917', 'level': 3, 'parent': 'Paper3_Opt30'},
    {'code': 'Paper3_Opt30_KT2', 'title': 'Key topic 2: The Bolsheviks in power, 1917–24', 'level': 3, 'parent': 'Paper3_Opt30'},
    {'code': 'Paper3_Opt30_KT3', 'title': 'Key topic 3: Stalin\'s rise to power and dictatorship, 1924–41', 'level': 3, 'parent': 'Paper3_Opt30'},
    {'code': 'Paper3_Opt30_KT4', 'title': 'Key topic 4: Economic and social changes, 1924–41', 'level': 3, 'parent': 'Paper3_Opt30'},
    
    # KT1 Topics (structure only)
    {'code': 'Paper3_Opt30_KT1_T1', 'title': '1. The growth of opposition to the tsar in early 1917', 'level': 4, 'parent': 'Paper3_Opt30_KT1'},
    {'code': 'Paper3_Opt30_KT1_T2', 'title': '2. The February Revolution', 'level': 4, 'parent': 'Paper3_Opt30_KT1'},
    {'code': 'Paper3_Opt30_KT1_T3', 'title': '3. The Provisional Government', 'level': 4, 'parent': 'Paper3_Opt30_KT1'},
    {'code': 'Paper3_Opt30_KT1_T4', 'title': '4. The Bolshevik Revolution', 'level': 4, 'parent': 'Paper3_Opt30_KT1'},
    
    # KT2 Topics
    {'code': 'Paper3_Opt30_KT2_T1', 'title': '1. Early consolidation of power, 1917–18', 'level': 4, 'parent': 'Paper3_Opt30_KT2'},
    {'code': 'Paper3_Opt30_KT2_T2', 'title': '2. The Civil War, 1918–21', 'level': 4, 'parent': 'Paper3_Opt30_KT2'},
    {'code': 'Paper3_Opt30_KT2_T3', 'title': '3. Moves towards totalitarianism', 'level': 4, 'parent': 'Paper3_Opt30_KT2'},
    {'code': 'Paper3_Opt30_KT2_T4', 'title': '4. Economic and social change, 1918–24', 'level': 4, 'parent': 'Paper3_Opt30_KT2'},
    
    # KT3 Topics
    {'code': 'Paper3_Opt30_KT3_T1', 'title': '1. The struggle for power, 1924–28', 'level': 4, 'parent': 'Paper3_Opt30_KT3'},
    {'code': 'Paper3_Opt30_KT3_T2', 'title': '2. The use of terror in the 1930s', 'level': 4, 'parent': 'Paper3_Opt30_KT3'},
    {'code': 'Paper3_Opt30_KT3_T3', 'title': '3. Propaganda and censorship', 'level': 4, 'parent': 'Paper3_Opt30_KT3'},
    {'code': 'Paper3_Opt30_KT3_T4', 'title': '4. The Cult of Stalin', 'level': 4, 'parent': 'Paper3_Opt30_KT3'},
    
    # KT4 Topics
    {'code': 'Paper3_Opt30_KT4_T1', 'title': '1. Agriculture and collectivisation', 'level': 4, 'parent': 'Paper3_Opt30_KT4'},
    {'code': 'Paper3_Opt30_KT4_T2', 'title': '2. Changes in industry', 'level': 4, 'parent': 'Paper3_Opt30_KT4'},
    {'code': 'Paper3_Opt30_KT4_T3', 'title': '3. Life in the Soviet Union', 'level': 4, 'parent': 'Paper3_Opt30_KT4'},
    {'code': 'Paper3_Opt30_KT4_T4', 'title': '4. The position of women and ethnic minorities', 'level': 4, 'parent': 'Paper3_Opt30_KT4'},
    
    # ========== OPTION 31: WEIMAR AND NAZI GERMANY ==========
    
    # Level 3: Key topics
    {'code': 'Paper3_Opt31_KT1', 'title': 'Key topic 1: The Weimar Republic 1918–29', 'level': 3, 'parent': 'Paper3_Opt31'},
    {'code': 'Paper3_Opt31_KT2', 'title': 'Key topic 2: Hitler\'s rise to power, 1919–33', 'level': 3, 'parent': 'Paper3_Opt31'},
    {'code': 'Paper3_Opt31_KT3', 'title': 'Key topic 3: Nazi control and dictatorship, 1933–39', 'level': 3, 'parent': 'Paper3_Opt31'},
    {'code': 'Paper3_Opt31_KT4', 'title': 'Key topic 4: Life in Nazi Germany, 1933–39', 'level': 3, 'parent': 'Paper3_Opt31'},
    
    # KT1 Topics
    {'code': 'Paper3_Opt31_KT1_T1', 'title': '1. The origins of the Republic, 1918–19', 'level': 4, 'parent': 'Paper3_Opt31_KT1'},
    {'code': 'Paper3_Opt31_KT1_T2', 'title': '2. The early challenges to the Weimar Republic, 1919–23', 'level': 4, 'parent': 'Paper3_Opt31_KT1'},
    {'code': 'Paper3_Opt31_KT1_T3', 'title': '3. The \'Golden Years\': recovery of the Republic, 1924–29', 'level': 4, 'parent': 'Paper3_Opt31_KT1'},
    {'code': 'Paper3_Opt31_KT1_T4', 'title': '4. Changes in society, 1924–29', 'level': 4, 'parent': 'Paper3_Opt31_KT1'},
    
    # KT2 Topics
    {'code': 'Paper3_Opt31_KT2_T1', 'title': '1. Early development of the Nazi Party, 1920–22', 'level': 4, 'parent': 'Paper3_Opt31_KT2'},
    {'code': 'Paper3_Opt31_KT2_T2', 'title': '2. The Munich Putsch and the Nazi Party, 1923–28', 'level': 4, 'parent': 'Paper3_Opt31_KT2'},
    {'code': 'Paper3_Opt31_KT2_T3', 'title': '3. The growth in support for the Nazis, 1929–32', 'level': 4, 'parent': 'Paper3_Opt31_KT2'},
    {'code': 'Paper3_Opt31_KT2_T4', 'title': '4. How Hitler became Chancellor, 1932–33', 'level': 4, 'parent': 'Paper3_Opt31_KT2'},
    
    # KT3 Topics
    {'code': 'Paper3_Opt31_KT3_T1', 'title': '1. The creation of a dictatorship, 1933–34', 'level': 4, 'parent': 'Paper3_Opt31_KT3'},
    {'code': 'Paper3_Opt31_KT3_T2', 'title': '2. The police state', 'level': 4, 'parent': 'Paper3_Opt31_KT3'},
    {'code': 'Paper3_Opt31_KT3_T3', 'title': '3. Controlling and influencing attitudes', 'level': 4, 'parent': 'Paper3_Opt31_KT3'},
    {'code': 'Paper3_Opt31_KT3_T4', 'title': '4. Opposition, resistance and conformity', 'level': 4, 'parent': 'Paper3_Opt31_KT3'},
    
    # KT4 Topics
    {'code': 'Paper3_Opt31_KT4_T1', 'title': '1. Nazi policies towards women', 'level': 4, 'parent': 'Paper3_Opt31_KT4'},
    {'code': 'Paper3_Opt31_KT4_T2', 'title': '2. Nazi policies towards the young', 'level': 4, 'parent': 'Paper3_Opt31_KT4'},
    {'code': 'Paper3_Opt31_KT4_T3', 'title': '3. Employment and living standards', 'level': 4, 'parent': 'Paper3_Opt31_KT4'},
    {'code': 'Paper3_Opt31_KT4_T4', 'title': '4. The persecution of minorities', 'level': 4, 'parent': 'Paper3_Opt31_KT4'},
]


def upload_paper3_opt30_31():
    """Add Paper 3 Options 30 and 31."""
    print(f"\n[INFO] Adding Paper 3 Options 30 and 31...")
    
    try:
        subject_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', SUBJECT_CODE).eq('qualification_type', 'GCSE').eq('exam_board', 'Edexcel').execute()
        
        if not subject_result.data:
            print("[ERROR] History subject not found!")
            return None
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        existing_topics = supabase.table('staging_aqa_topics').select('*').eq('subject_id', subject_id).execute()
        
        # Delete old details for Options 30 and 31
        deleted_count = 0
        for t in existing_topics.data:
            code = t['topic_code']
            if code.startswith('Paper3_Opt30_') or code.startswith('Paper3_Opt31_'):
                supabase.table('staging_aqa_topics').delete().eq('id', t['id']).execute()
                deleted_count += 1
        
        print(f"[OK] Cleared {deleted_count} old details")
        
        # Insert new topics
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'exam_board': 'Edexcel'
        } for t in NEW_TOPICS]
        
        inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted.data)} new topics")
        
        # Link parents
        code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
        for t in existing_topics.data:
            code_to_id[t['topic_code']] = t['id']
        
        linked = 0
        for topic in NEW_TOPICS:
            if topic['parent']:
                parent_id = code_to_id.get(topic['parent'])
                child_id = code_to_id.get(topic['code'])
                if parent_id and child_id:
                    supabase.table('staging_aqa_topics').update({
                        'parent_topic_id': parent_id
                    }).eq('id', child_id).execute()
                    linked += 1
        
        print(f"[OK] Linked {linked} relationships")
        
        levels = defaultdict(int)
        for t in NEW_TOPICS:
            levels[t['level']] += 1
        
        print("\n" + "=" * 80)
        print("[SUCCESS] PAPER 3: OPTIONS 30 & 31 UPLOADED!")
        print("=" * 80)
        print("✅ Option 30: Russia and the Soviet Union (structure - 4 Key topics)")
        print("✅ Option 31: Weimar and Nazi Germany (structure - 4 Key topics)")
        print()
        for level in sorted(levels.keys()):
            print(f"   Level {level}: {levels[level]} topics")
        print(f"\n   Total added: {len(NEW_TOPICS)}")
        print("=" * 80)
        
        return subject_id
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("=" * 80)
    print("GCSE HISTORY - PAPER 3 OPTIONS 30 & 31")
    print("=" * 80)
    
    try:
        subject_id = upload_paper3_opt30_31()
        
        if subject_id:
            print("\n✅ COMPLETE!")
            print("\nNOTE: Structure uploaded (Key topics + numbered sections)")
            print("Bullets can be added later if needed")
        else:
            print("\n❌ FAILED")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()


