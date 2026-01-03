"""
GCSE History - Option 13 Detailed Content Upload
=================================================

Option 13: Migrants in Britain + Notting Hill
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

SUBJECT_CODE = 'GCSE-History'
OPTION_CODE = 'Paper1_Opt13'

NEW_TOPICS = [
    # Level 2: Two main sections
    {'code': f'{OPTION_CODE}_Migrants', 'title': 'Migrants in Britain, c800–present (Thematic study)', 'level': 2, 'parent': OPTION_CODE},
    {'code': f'{OPTION_CODE}_Notting', 'title': 'Notting Hill, c1948–c1970 (Historic environment)', 'level': 2, 'parent': OPTION_CODE},
    
    # === MIGRANTS SECTION ===
    
    # Level 3: Time periods
    {'code': f'{OPTION_CODE}_Migrants_P1', 'title': 'c800–c1500: Migration in medieval England', 'level': 3, 'parent': f'{OPTION_CODE}_Migrants'},
    {'code': f'{OPTION_CODE}_Migrants_P2', 'title': 'c1500–c1700: Migration in early modern England', 'level': 3, 'parent': f'{OPTION_CODE}_Migrants'},
    {'code': f'{OPTION_CODE}_Migrants_P3', 'title': 'c1700–c1900: Migration in eighteenth- and nineteenth-century Britain', 'level': 3, 'parent': f'{OPTION_CODE}_Migrants'},
    {'code': f'{OPTION_CODE}_Migrants_P4', 'title': 'c1900–present: Migration in modern Britain', 'level': 3, 'parent': f'{OPTION_CODE}_Migrants'},
    
    # PERIOD 1: c800-c1500
    {'code': f'{OPTION_CODE}_Migrants_P1_T1', 'title': '1. The context for migration', 'level': 4, 'parent': f'{OPTION_CODE}_Migrants_P1'},
    {'code': f'{OPTION_CODE}_Migrants_P1_T2', 'title': '2. The experience and impact of migrants', 'level': 4, 'parent': f'{OPTION_CODE}_Migrants_P1'},
    {'code': f'{OPTION_CODE}_Migrants_P1_T3', 'title': '3. Case study', 'level': 4, 'parent': f'{OPTION_CODE}_Migrants_P1'},
    
    {'code': f'{OPTION_CODE}_Migrants_P1_T1_B1', 'title': 'Reasons for migration and patterns of settlement, including Vikings, Normans, Jews and other European traders and craftsmen', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P1_T1'},
    {'code': f'{OPTION_CODE}_Migrants_P1_T1_B2', 'title': 'The context of English society: landownership and the growth of towns; the role of the wool industry; opportunities for migrants; the role the monarchy, including the need for royal finance; England as a part of Christendom', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P1_T1'},
    {'code': f'{OPTION_CODE}_Migrants_P1_T2_B1', 'title': "The experience of migrants in England: their relations with the authorities and the existing population, including the legal status of 'alien' and the impact of the Black Death", 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P1_T2'},
    {'code': f'{OPTION_CODE}_Migrants_P1_T2_B2', 'title': 'The impact of migrants in England, including the Danelaw, culture, trade and the built environment', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P1_T2'},
    {'code': f'{OPTION_CODE}_Migrants_P1_T3_B1', 'title': 'The city of York under the Vikings', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P1_T3'},
    
    # PERIOD 2: c1500-c1700
    {'code': f'{OPTION_CODE}_Migrants_P2_T1', 'title': '1. The context for migration', 'level': 4, 'parent': f'{OPTION_CODE}_Migrants_P2'},
    {'code': f'{OPTION_CODE}_Migrants_P2_T2', 'title': '2. The experience and impact of migrants', 'level': 4, 'parent': f'{OPTION_CODE}_Migrants_P2'},
    {'code': f'{OPTION_CODE}_Migrants_P2_T3', 'title': '3. Case studies', 'level': 4, 'parent': f'{OPTION_CODE}_Migrants_P2'},
    
    {'code': f'{OPTION_CODE}_Migrants_P2_T1_B1', 'title': 'Change and continuity in reasons for migration and patterns of settlement, including migrants from Europe and Africa', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P2_T1'},
    {'code': f'{OPTION_CODE}_Migrants_P2_T1_B2', 'title': 'The changing context of English society: changing social structures; economic growth, including the cloth industry and global trading companies; privateering and trade; the emergence of England as a predominantly Protestant nation', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P2_T1'},
    {'code': f'{OPTION_CODE}_Migrants_P2_T2_B1', 'title': 'The experience of migrants in England: their relations with the authorities and the existing population', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P2_T2'},
    {'code': f'{OPTION_CODE}_Migrants_P2_T2_B2', 'title': 'The impact of migrants in England, including culture, trade, industry and agriculture', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P2_T2'},
    {'code': f'{OPTION_CODE}_Migrants_P2_T3_B1', 'title': 'Sandwich and Canterbury in the sixteenth century: the experiences of Flemish and Walloon migrants and their role in the local economy', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P2_T3'},
    {'code': f'{OPTION_CODE}_Migrants_P2_T3_B2', 'title': 'The experience of Huguenots in seventeenth century England', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P2_T3'},
    
    # PERIOD 3: c1700-c1900
    {'code': f'{OPTION_CODE}_Migrants_P3_T1', 'title': '1. The context for migration', 'level': 4, 'parent': f'{OPTION_CODE}_Migrants_P3'},
    {'code': f'{OPTION_CODE}_Migrants_P3_T2', 'title': '2. The experience and impact of migrants', 'level': 4, 'parent': f'{OPTION_CODE}_Migrants_P3'},
    {'code': f'{OPTION_CODE}_Migrants_P3_T3', 'title': '3. Case studies', 'level': 4, 'parent': f'{OPTION_CODE}_Migrants_P3'},
    
    {'code': f'{OPTION_CODE}_Migrants_P3_T1_B1', 'title': 'Change and continuity in reasons for migration and patterns of settlement, including migrants from Ireland, Europe and the Empire', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P3_T1'},
    {'code': f'{OPTION_CODE}_Migrants_P3_T1_B2', 'title': 'The changing context of British society: changing social structures; the Industrial Revolution; urbanisation; transatlantic slavery; the growth of the British Empire; civil liberties', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P3_T1'},
    {'code': f'{OPTION_CODE}_Migrants_P3_T2_B1', 'title': 'The experience of migrants in Britain: their relations with the authorities and the existing population. The role of the media', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P3_T2'},
    {'code': f'{OPTION_CODE}_Migrants_P3_T2_B2', 'title': 'The impact of migrants in Britain, including culture, trade and industry, politics and the urban environment', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P3_T2'},
    {'code': f'{OPTION_CODE}_Migrants_P3_T3_B1', 'title': 'Liverpool in the nineteenth century: its role in migration and the experiences of migrants, including Irish migrants', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P3_T3'},
    {'code': f'{OPTION_CODE}_Migrants_P3_T3_B2', 'title': 'The experience of Jewish migrants in the East End of London in late nineteenth century', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P3_T3'},
    
    # PERIOD 4: c1900-present
    {'code': f'{OPTION_CODE}_Migrants_P4_T1', 'title': '1. The context for migration', 'level': 4, 'parent': f'{OPTION_CODE}_Migrants_P4'},
    {'code': f'{OPTION_CODE}_Migrants_P4_T2', 'title': '2. The experience and impact of migrants', 'level': 4, 'parent': f'{OPTION_CODE}_Migrants_P4'},
    {'code': f'{OPTION_CODE}_Migrants_P4_T3', 'title': '3. Case studies', 'level': 4, 'parent': f'{OPTION_CODE}_Migrants_P4'},
    
    {'code': f'{OPTION_CODE}_Migrants_P4_T1_B1', 'title': 'Change and continuity in reasons for migration and patterns of settlement, including migrants from Ireland, Europe, the British Empire and the Commonwealth; refugees and asylum seekers', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P4_T1'},
    {'code': f'{OPTION_CODE}_Migrants_P4_T1_B2', 'title': 'The changing context of British society: the World Wars; the end of the British Empire, decolonisation and the development of the Commonwealth; EU membership; legislation on immigration and nationality, including the Aliens Act (1905) and British Nationality Acts', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P4_T1'},
    {'code': f'{OPTION_CODE}_Migrants_P4_T2_B1', 'title': 'The experience of migrants in Britain: their relations with the authorities and the existing population, including anti-immigration and equal rights movements. The Race Relations Act (1965). The role of the media', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P4_T2'},
    {'code': f'{OPTION_CODE}_Migrants_P4_T2_B2', 'title': 'The impact of migrants in Britain, including culture, politics, the urban environment, public services and the economy', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P4_T2'},
    {'code': f'{OPTION_CODE}_Migrants_P4_T3_B1', 'title': 'Bristol in the mid-twentieth century: the experiences of migrants and their impact on society', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P4_T3'},
    {'code': f'{OPTION_CODE}_Migrants_P4_T3_B2', 'title': 'The experience of Asian migrants in Leicester from 1945', 'level': 5, 'parent': f'{OPTION_CODE}_Migrants_P4_T3'},
    
    # === NOTTING HILL SECTION ===
    
    # Level 3: Section
    {'code': f'{OPTION_CODE}_Notting_Env', 'title': 'The historic environment', 'level': 3, 'parent': f'{OPTION_CODE}_Notting'},
    
    # Level 4: Topics
    {'code': f'{OPTION_CODE}_Notting_Env_T1', 'title': '1. Notting Hill, c1948–c1970', 'level': 4, 'parent': f'{OPTION_CODE}_Notting_Env'},
    {'code': f'{OPTION_CODE}_Notting_Env_T2', 'title': '2. Knowledge, selection and use of sources for historical enquiries', 'level': 4, 'parent': f'{OPTION_CODE}_Notting_Env'},
    
    # Level 5: Bullets for Topic 1
    {'code': f'{OPTION_CODE}_Notting_Env_T1_B1', 'title': 'The local context of Notting Hill. The reasons for Caribbean migration to the area. The problems of housing: houses of multiple occupation (HMOs), overcrowding and slum landlords, e.g. Peter Rachman. Bruce Kenrick and the Notting Hill Housing Trust. The development of Portobello Road market', 'level': 5, 'parent': f'{OPTION_CODE}_Notting_Env_T1'},
    {'code': f'{OPTION_CODE}_Notting_Env_T1_B2', 'title': 'The influence of Caribbean cultures on the area, in particular the development of shops, markets, cafes and restaurants, shebeens, nightclubs and entertainment which featured Caribbean food and music. The development of All Saints Road. Mutual self-help organisations, e.g. \'pardner\' schemes', 'level': 5, 'parent': f'{OPTION_CODE}_Notting_Env_T1'},
    {'code': f'{OPTION_CODE}_Notting_Env_T1_B3', 'title': "Racism and policing. The Notting Hill Riots (1958). The murder of Kelso Cochrane and the reaction of the local community. The impact of anti-immigrant groups, including Oswald Mosley's Union Movement and his 1959 election campaign", 'level': 5, 'parent': f'{OPTION_CODE}_Notting_Env_T1'},
    {'code': f'{OPTION_CODE}_Notting_Env_T1_B4', 'title': "Black activism in the Notting Hill area. Claudia Jones and the West Indian Gazette. The 1959 Caribbean Carnival and the later development of the Notting Hill Carnival. Frank Crichlow and the Mangrove Restaurant. The British Black Panthers. The 'Mangrove Nine'", 'level': 5, 'parent': f'{OPTION_CODE}_Notting_Env_T1'},
    {'code': f'{OPTION_CODE}_Notting_Env_T1_B5', 'title': "The national and regional context: Britain after the Second World War, reconstruction and demand for labour; the connection to the British Empire and Commonwealth. The 'Swinging Sixties'. Poverty in London. Policing in London", 'level': 5, 'parent': f'{OPTION_CODE}_Notting_Env_T1'},
    
    # Level 5: Bullets for Topic 2
    {'code': f'{OPTION_CODE}_Notting_Env_T2_B1', 'title': 'Knowledge of local sources relevant to the period and issue, e.g. local newspapers, publications written for the Caribbean community, local council and police records, housing and employment records, oral and written memoirs of local residents, photographs', 'level': 5, 'parent': f'{OPTION_CODE}_Notting_Env_T2'},
    {'code': f'{OPTION_CODE}_Notting_Env_T2_B2', 'title': 'Knowledge of national sources relevant to the period and issue, e.g. national newspapers, photographs, government records, census data, opinion polls, television reports, memoirs', 'level': 5, 'parent': f'{OPTION_CODE}_Notting_Env_T2'},
    {'code': f'{OPTION_CODE}_Notting_Env_T2_B3', 'title': 'Recognition of the strengths and weaknesses of different types of source for specific enquiries', 'level': 5, 'parent': f'{OPTION_CODE}_Notting_Env_T2'},
    {'code': f'{OPTION_CODE}_Notting_Env_T2_B4', 'title': 'Framing of questions relevant to the pursuit of a specific enquiry', 'level': 5, 'parent': f'{OPTION_CODE}_Notting_Env_T2'},
    {'code': f'{OPTION_CODE}_Notting_Env_T2_B5', 'title': 'Selection of appropriate sources for specific investigations', 'level': 5, 'parent': f'{OPTION_CODE}_Notting_Env_T2'},
]


def upload_option13_details():
    """Add Option 13 detailed content."""
    print(f"\n[INFO] Adding detailed content for Option 13: Migrants...")
    
    try:
        subject_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', SUBJECT_CODE).eq('qualification_type', 'GCSE').eq('exam_board', 'Edexcel').execute()
        
        if not subject_result.data:
            print("[ERROR] History subject not found!")
            return None
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        existing_topics = supabase.table('staging_aqa_topics').select('*').eq('subject_id', subject_id).execute()
        
        opt13_exists = any(t['topic_code'] == OPTION_CODE for t in existing_topics.data)
        if not opt13_exists:
            print(f"[ERROR] Option 13 not found!")
            return None
        
        # Delete old Option 13 details
        for t in existing_topics.data:
            if t['topic_code'].startswith(OPTION_CODE + '_'):
                supabase.table('staging_aqa_topics').delete().eq('id', t['id']).execute()
        
        print("[OK] Cleared old Option 13 details")
        
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
        print("[SUCCESS] OPTION 13: MIGRANTS IN BRITAIN - COMPLETE!")
        print("=" * 80)
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
    print("GCSE HISTORY - OPTION 13 DETAILED CONTENT")
    print("=" * 80)
    
    try:
        subject_id = upload_option13_details()
        
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


