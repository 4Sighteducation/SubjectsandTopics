"""
GCSE History - Paper 3: Options 32 and 33
==========================================

Option 32: Mao's China
Option 33: The USA

Final options to complete GCSE History!
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
    # ========== OPTION 32: MAO'S CHINA ==========
    
    # Level 3: Key topics
    {'code': 'Paper3_Opt32_KT1', 'title': 'Key topic 1: Establishing communist rule, 1945–59', 'level': 3, 'parent': 'Paper3_Opt32'},
    {'code': 'Paper3_Opt32_KT2', 'title': 'Key topic 2: Economic policy, 1949–65', 'level': 3, 'parent': 'Paper3_Opt32'},
    {'code': 'Paper3_Opt32_KT3', 'title': 'Key topic 3: The Cultural Revolution and its aftermath, 1966–76', 'level': 3, 'parent': 'Paper3_Opt32'},
    {'code': 'Paper3_Opt32_KT4', 'title': 'Key topic 4: Life in Mao\'s China, 1949–76', 'level': 3, 'parent': 'Paper3_Opt32'},
    
    # KT1 Topics
    {'code': 'Paper3_Opt32_KT1_T1', 'title': '1. The Civil War, 1945–49', 'level': 4, 'parent': 'Paper3_Opt32_KT1'},
    {'code': 'Paper3_Opt32_KT1_T2', 'title': '2. Communist rule', 'level': 4, 'parent': 'Paper3_Opt32_KT1'},
    {'code': 'Paper3_Opt32_KT1_T3', 'title': '3. Consolidating the CCP\'s hold on power, 1951–52', 'level': 4, 'parent': 'Paper3_Opt32_KT1'},
    {'code': 'Paper3_Opt32_KT1_T4', 'title': '4. The Hundred Flowers campaign, 1956–57', 'level': 4, 'parent': 'Paper3_Opt32_KT1'},
    
    # KT2 Topics
    {'code': 'Paper3_Opt32_KT2_T1', 'title': '1. Early changes in agriculture, 1949–57', 'level': 4, 'parent': 'Paper3_Opt32_KT2'},
    {'code': 'Paper3_Opt32_KT2_T2', 'title': '2. Industry and the Five-Year Plan, 1953–57', 'level': 4, 'parent': 'Paper3_Opt32_KT2'},
    {'code': 'Paper3_Opt32_KT2_T3', 'title': '3. The Great Leap Forward', 'level': 4, 'parent': 'Paper3_Opt32_KT2'},
    {'code': 'Paper3_Opt32_KT2_T4', 'title': '4. Economic reform', 'level': 4, 'parent': 'Paper3_Opt32_KT2'},
    
    # KT3 Topics
    {'code': 'Paper3_Opt32_KT3_T1', 'title': '1. Reasons for the Cultural Revolution', 'level': 4, 'parent': 'Paper3_Opt32_KT3'},
    {'code': 'Paper3_Opt32_KT3_T2', 'title': '2. The Red Guards and the Red Terror', 'level': 4, 'parent': 'Paper3_Opt32_KT3'},
    {'code': 'Paper3_Opt32_KT3_T3', 'title': '3. The effects of the Cultural Revolution', 'level': 4, 'parent': 'Paper3_Opt32_KT3'},
    {'code': 'Paper3_Opt32_KT3_T4', 'title': '4. The end of the Cultural Revolution, 1968–76', 'level': 4, 'parent': 'Paper3_Opt32_KT3'},
    
    # KT4 Topics
    {'code': 'Paper3_Opt32_KT4_T1', 'title': '1. Communist control', 'level': 4, 'parent': 'Paper3_Opt32_KT4'},
    {'code': 'Paper3_Opt32_KT4_T2', 'title': '2. Family life and the role of women', 'level': 4, 'parent': 'Paper3_Opt32_KT4'},
    {'code': 'Paper3_Opt32_KT4_T3', 'title': '3. Education and health', 'level': 4, 'parent': 'Paper3_Opt32_KT4'},
    {'code': 'Paper3_Opt32_KT4_T4', 'title': '4. Cultural change', 'level': 4, 'parent': 'Paper3_Opt32_KT4'},
    
    # ========== OPTION 33: THE USA ==========
    
    # Level 3: Key topics
    {'code': 'Paper3_Opt33_KT1', 'title': 'Key topic 1: The development of the civil rights movement, 1954–60', 'level': 3, 'parent': 'Paper3_Opt33'},
    {'code': 'Paper3_Opt33_KT2', 'title': 'Key topic 2: Protest, progress and radicalism, 1960–75', 'level': 3, 'parent': 'Paper3_Opt33'},
    {'code': 'Paper3_Opt33_KT3', 'title': 'Key topic 3: US involvement in the Vietnam War, 1954–75', 'level': 3, 'parent': 'Paper3_Opt33'},
    {'code': 'Paper3_Opt33_KT4', 'title': 'Key topic 4: Reactions to, and the end of, US involvement in Vietnam, 1964–75', 'level': 3, 'parent': 'Paper3_Opt33'},
    
    # KT1 Topics
    {'code': 'Paper3_Opt33_KT1_T1', 'title': '1. The position of Black Americans in the early 1950s', 'level': 4, 'parent': 'Paper3_Opt33_KT1'},
    {'code': 'Paper3_Opt33_KT1_T2', 'title': '2. Developments in education', 'level': 4, 'parent': 'Paper3_Opt33_KT1'},
    {'code': 'Paper3_Opt33_KT1_T3', 'title': '3. The Montgomery Bus Boycott and its impact, 1955–60', 'level': 4, 'parent': 'Paper3_Opt33_KT1'},
    {'code': 'Paper3_Opt33_KT1_T4', 'title': '4. Opposition to the civil rights movement', 'level': 4, 'parent': 'Paper3_Opt33_KT1'},
    
    # KT2 Topics
    {'code': 'Paper3_Opt33_KT2_T1', 'title': '1. Developments, 1960–62', 'level': 4, 'parent': 'Paper3_Opt33_KT2'},
    {'code': 'Paper3_Opt33_KT2_T2', 'title': '2. Peaceful protests and their impact, 1963–65', 'level': 4, 'parent': 'Paper3_Opt33_KT2'},
    {'code': 'Paper3_Opt33_KT2_T3', 'title': '3. Malcolm X and Black Power, 1963–70', 'level': 4, 'parent': 'Paper3_Opt33_KT2'},
    {'code': 'Paper3_Opt33_KT2_T4', 'title': '4. The civil rights movement, 1965–75', 'level': 4, 'parent': 'Paper3_Opt33_KT2'},
    
    # KT3 Topics
    {'code': 'Paper3_Opt33_KT3_T1', 'title': '1. Reasons for US involvement in the conflict in Vietnam, 1954–63', 'level': 4, 'parent': 'Paper3_Opt33_KT3'},
    {'code': 'Paper3_Opt33_KT3_T2', 'title': '2. Escalation of the conflict under Johnson', 'level': 4, 'parent': 'Paper3_Opt33_KT3'},
    {'code': 'Paper3_Opt33_KT3_T3', 'title': '3. The nature of the conflict in Vietnam, 1964–68', 'level': 4, 'parent': 'Paper3_Opt33_KT3'},
    {'code': 'Paper3_Opt33_KT3_T4', 'title': '4. Changes under Nixon, 1969–73', 'level': 4, 'parent': 'Paper3_Opt33_KT3'},
    
    # KT4 Topics
    {'code': 'Paper3_Opt33_KT4_T1', 'title': '1. Opposition to the war', 'level': 4, 'parent': 'Paper3_Opt33_KT4'},
    {'code': 'Paper3_Opt33_KT4_T2', 'title': '2. Support for the war', 'level': 4, 'parent': 'Paper3_Opt33_KT4'},
    {'code': 'Paper3_Opt33_KT4_T3', 'title': '3. The peace process and end of the war', 'level': 4, 'parent': 'Paper3_Opt33_KT4'},
    {'code': 'Paper3_Opt33_KT4_T4', 'title': '4. Reasons for the failure of the USA in Vietnam', 'level': 4, 'parent': 'Paper3_Opt33_KT4'},
]


def upload_paper3_opt32_33():
    """Add Paper 3 Options 32 and 33."""
    print(f"\n[INFO] Adding Paper 3 Options 32 and 33...")
    
    try:
        subject_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', SUBJECT_CODE).eq('qualification_type', 'GCSE').eq('exam_board', 'Edexcel').execute()
        
        if not subject_result.data:
            print("[ERROR] History subject not found!")
            return None
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        existing_topics = supabase.table('staging_aqa_topics').select('*').eq('subject_id', subject_id).execute()
        
        # Delete old details
        deleted_count = 0
        for t in existing_topics.data:
            code = t['topic_code']
            if code.startswith('Paper3_Opt32_') or code.startswith('Paper3_Opt33_'):
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
        print("[SUCCESS] PAPER 3: OPTIONS 32 & 33 - HISTORY COMPLETE!")
        print("=" * 80)
        print("✅ Option 32: Mao's China (structure - 4 Key topics)")
        print("✅ Option 33: The USA, 1954–75 (structure - 4 Key topics)")
        print()
        for level in sorted(levels.keys()):
            print(f"   Level {level}: {levels[level]} topics")
        print(f"\n   Total added: {len(NEW_TOPICS)}")
        print("=" * 80)
        print("\n🎉 GCSE HISTORY QUALIFICATION STRUCTURE COMPLETE!")
        print("All 3 Papers, all 15 Options uploaded!")
        
        return subject_id
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("=" * 80)
    print("GCSE HISTORY - FINAL OPTIONS 32 & 33")
    print("=" * 80)
    
    try:
        subject_id = upload_paper3_opt32_33()
        
        if subject_id:
            print("\n✅ HISTORY COMPLETE!")
        else:
            print("\n❌ FAILED")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()


