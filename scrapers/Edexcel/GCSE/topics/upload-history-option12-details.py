"""
GCSE History - Option 12 Detailed Content Upload
=================================================

Option 12: Warfare and British society + London WW2
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
OPTION_CODE = 'Paper1_Opt12'

NEW_TOPICS = [
    # Level 2: Two main sections
    {'code': f'{OPTION_CODE}_Warfare', 'title': 'Warfare and British society, c1250–present (Thematic study)', 'level': 2, 'parent': OPTION_CODE},
    {'code': f'{OPTION_CODE}_London', 'title': 'London and the Second World War, 1939–45 (Historic environment)', 'level': 2, 'parent': OPTION_CODE},
    
    # === WARFARE SECTION ===
    
    # Level 3: Time periods
    {'code': f'{OPTION_CODE}_Warfare_P1', 'title': 'c1250–c1500: Medieval warfare and English society', 'level': 3, 'parent': f'{OPTION_CODE}_Warfare'},
    {'code': f'{OPTION_CODE}_Warfare_P2', 'title': 'c1500–c1700: Warfare and English society in the early modern period', 'level': 3, 'parent': f'{OPTION_CODE}_Warfare'},
    {'code': f'{OPTION_CODE}_Warfare_P3', 'title': 'c1700–c1900: Warfare and British society in the eighteenth and nineteenth centuries', 'level': 3, 'parent': f'{OPTION_CODE}_Warfare'},
    {'code': f'{OPTION_CODE}_Warfare_P4', 'title': 'c1900–present: Warfare and British society in the modern era', 'level': 3, 'parent': f'{OPTION_CODE}_Warfare'},
    
    # PERIOD 1: c1250-c1500
    {'code': f'{OPTION_CODE}_Warfare_P1_T1', 'title': '1. The nature of warfare', 'level': 4, 'parent': f'{OPTION_CODE}_Warfare_P1'},
    {'code': f'{OPTION_CODE}_Warfare_P1_T2', 'title': '2. The experience of war', 'level': 4, 'parent': f'{OPTION_CODE}_Warfare_P1'},
    {'code': f'{OPTION_CODE}_Warfare_P1_T3', 'title': '3. Case studies', 'level': 4, 'parent': f'{OPTION_CODE}_Warfare_P1'},
    
    {'code': f'{OPTION_CODE}_Warfare_P1_T1_B1', 'title': 'The composition of the army, including the roles of the infantry, archer and the mounted knight. The link between social structure and army command', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P1_T1'},
    {'code': f'{OPTION_CODE}_Warfare_P1_T1_B2', 'title': 'The impact on warfare (strategy, tactics and combat) of new weapons and formations, including the longbow and schiltrons. The importance of gunpowder and the development of cannon. The decline of the mounted knight', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P1_T1'},
    {'code': f'{OPTION_CODE}_Warfare_P1_T2_B1', 'title': 'The recruitment and training of combatants in the medieval feudal army', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P1_T2'},
    {'code': f'{OPTION_CODE}_Warfare_P1_T2_B2', 'title': 'The impact of war on civilians, including the impact of feudal duties and army plunder on civilian lives', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P1_T2'},
    {'code': f'{OPTION_CODE}_Warfare_P1_T3_B1', 'title': 'The Battle of Falkirk (1298): reasons for its outcome; the roles of William Wallace and Edward I', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P1_T3'},
    {'code': f'{OPTION_CODE}_Warfare_P1_T3_B2', 'title': 'The Battle of Agincourt (1415): reasons for its outcome; the role of Henry V', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P1_T3'},
    
    # PERIOD 2: c1500-c1700
    {'code': f'{OPTION_CODE}_Warfare_P2_T1', 'title': '1. The nature of warfare', 'level': 4, 'parent': f'{OPTION_CODE}_Warfare_P2'},
    {'code': f'{OPTION_CODE}_Warfare_P2_T2', 'title': '2. The experience of war', 'level': 4, 'parent': f'{OPTION_CODE}_Warfare_P2'},
    {'code': f'{OPTION_CODE}_Warfare_P2_T3', 'title': '3. Case study', 'level': 4, 'parent': f'{OPTION_CODE}_Warfare_P2'},
    
    {'code': f'{OPTION_CODE}_Warfare_P2_T1_B1', 'title': 'Continuity and change in the composition of the army in the sixteenth and seventeenth centuries, including the role of the musketeer, pikemen, dragoons and the cavalry. The development of a standing army', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P2_T1'},
    {'code': f'{OPTION_CODE}_Warfare_P2_T1_B2', 'title': 'The impact on warfare of developments in weaponry, including new muskets and pistols', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P2_T1'},
    {'code': f'{OPTION_CODE}_Warfare_P2_T2_B1', 'title': 'The recruitment and training of combatants, including the New Model Army', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P2_T2'},
    {'code': f'{OPTION_CODE}_Warfare_P2_T2_B2', 'title': 'The impact of war on civilians, including recruitment and requisitioning', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P2_T2'},
    {'code': f'{OPTION_CODE}_Warfare_P2_T3_B1', 'title': 'The Battle of Naseby (1645): reasons for its outcome; the role of Oliver Cromwell', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P2_T3'},
    
    # PERIOD 3: c1700-c1900
    {'code': f'{OPTION_CODE}_Warfare_P3_T1', 'title': '1. The nature of warfare', 'level': 4, 'parent': f'{OPTION_CODE}_Warfare_P3'},
    {'code': f'{OPTION_CODE}_Warfare_P3_T2', 'title': '2. The experience of war', 'level': 4, 'parent': f'{OPTION_CODE}_Warfare_P3'},
    {'code': f'{OPTION_CODE}_Warfare_P3_T3', 'title': '3. Case studies', 'level': 4, 'parent': f'{OPTION_CODE}_Warfare_P3'},
    
    {'code': f'{OPTION_CODE}_Warfare_P3_T1_B1', 'title': 'Continuity and change in the composition of the army, including the decline of the cavalry', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P3_T1'},
    {'code': f'{OPTION_CODE}_Warfare_P3_T1_B2', 'title': 'Impact on warfare of changes in weaponry, including the use of rifles and bullets, and the development of field guns and heavy artillery. The impact on warfare of industrialisation, including steampowered transport and the mass production of weapons', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P3_T1'},
    {'code': f'{OPTION_CODE}_Warfare_P3_T2_B1', 'title': "The recruitment and training of combatants, including Cardwell's army reforms and professionalisation", 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P3_T2'},
    {'code': f'{OPTION_CODE}_Warfare_P3_T2_B2', 'title': 'The impact of war on civilians, including recruitment and requisitioning. The impact on popular attitudes of the growth of newspaper reporting and photography in the nineteenth century, exemplified in the Crimean and Boer Wars', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P3_T2'},
    {'code': f'{OPTION_CODE}_Warfare_P3_T3_B1', 'title': 'The Battle of Waterloo (1815): reasons for its outcome; the role of the Duke of Wellington', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P3_T3'},
    {'code': f'{OPTION_CODE}_Warfare_P3_T3_B2', 'title': 'The Battle of Balaclava (1854): reasons for its outcome; the role of Lord Raglan', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P3_T3'},
    
    # PERIOD 4: c1900-present
    {'code': f'{OPTION_CODE}_Warfare_P4_T1', 'title': '1. The nature of warfare', 'level': 4, 'parent': f'{OPTION_CODE}_Warfare_P4'},
    {'code': f'{OPTION_CODE}_Warfare_P4_T2', 'title': '2. The experience of war', 'level': 4, 'parent': f'{OPTION_CODE}_Warfare_P4'},
    {'code': f'{OPTION_CODE}_Warfare_P4_T3', 'title': '3. Case studies', 'level': 4, 'parent': f'{OPTION_CODE}_Warfare_P4'},
    
    {'code': f'{OPTION_CODE}_Warfare_P4_T1_B1', 'title': 'Continuity and change in the composition of the army, including the growth of a logistics corps and specialised bomb disposal units', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P4_T1'},
    {'code': f'{OPTION_CODE}_Warfare_P4_T1_B2', 'title': 'The impact on warfare of developments in weaponry, transport and surveillance, including machine guns, tanks, chemical and nuclear weapons, the use of radar and aircraft. The impact of computerised high-tech warfare. The increasing use of motor and air transport and aerial support. Dealing with guerrilla warfare in the twenty-first century', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P4_T1'},
    {'code': f'{OPTION_CODE}_Warfare_P4_T2_B1', 'title': 'The recruitment and training of combatants, including the introduction of conscription, national service, the recruitment of women and the development of a professional army', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P4_T2'},
    {'code': f'{OPTION_CODE}_Warfare_P4_T2_B2', 'title': 'The impact of war on civilians, including recruitment and the organisation of a Home Front during the First and Second World Wars and fear of nuclear war post-1945. Attitudes to Conscientious Objectors. The influence of war reporting in the period on attitudes, including increased concern for casualties. Government use of censorship and propaganda in wartime', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P4_T2'},
    {'code': f'{OPTION_CODE}_Warfare_P4_T3_B1', 'title': 'The Western Front during the First World War and the Battle of the Somme (1916): the nature of trench warfare and war of attrition; reasons for the outcome of the Somme; role of General Haig', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P4_T3'},
    {'code': f'{OPTION_CODE}_Warfare_P4_T3_B2', 'title': 'The Iraq War (2003): reasons for its outcome; use of high-tech weaponry and surveillance techniques', 'level': 5, 'parent': f'{OPTION_CODE}_Warfare_P4_T3'},
    
    # === LONDON SECTION ===
    
    # Level 3: Section
    {'code': f'{OPTION_CODE}_London_Env', 'title': 'The historic environment', 'level': 3, 'parent': f'{OPTION_CODE}_London'},
    
    # Level 4: Topics
    {'code': f'{OPTION_CODE}_London_Env_T1', 'title': '1. London and the Second World War, 1939–45', 'level': 4, 'parent': f'{OPTION_CODE}_London_Env'},
    {'code': f'{OPTION_CODE}_London_Env_T2', 'title': '2. Knowledge, selection and use of sources for historical enquiries', 'level': 4, 'parent': f'{OPTION_CODE}_London_Env'},
    
    # Level 5: Bullets for Topic 1
    {'code': f'{OPTION_CODE}_London_Env_T1_B1', 'title': 'The context of London in the Second World War, including its role in national government, significance as a target, importance as a port and industrial centre and its accessibility for German bombers. Preparations for war in London in 1939 and ongoing measures to safeguard the population: implementation of plans for evacuation, provision of Anderson shelters and gas masks', 'level': 5, 'parent': f'{OPTION_CODE}_London_Env_T1'},
    {'code': f'{OPTION_CODE}_London_Env_T1_B2', 'title': 'The nature of attacks on London. Attacks on the docks and industries of the East End, including Black Saturday (7 September 1940), and the V2 attack on Deptford (1944). Types of bomb used in 1940–41 and 1944–45, the scale of attack and extent of devastation, including problems dealing with incendiaries and V1 and V2 rockets', 'level': 5, 'parent': f'{OPTION_CODE}_London_Env_T1'},
    {'code': f'{OPTION_CODE}_London_Env_T1_B3', 'title': "The impact of the Blitz on civilian life in London: air-raid precautions, including the use of underground stations and 'Mickey's shelter'; the impact of the South Hallsville School (1940) and Bethnal Green (1943) disasters. The continuance of leisure activities in London, including dancehalls and theatre. The extent of disruption to daily life and work, and government concerns about morale", 'level': 5, 'parent': f'{OPTION_CODE}_London_Env_T1'},
    {'code': f'{OPTION_CODE}_London_Env_T1_B4', 'title': "London's response to the war. The continued presence of the Royal Family and government ministers; the Cabinet War Rooms. The use of public spaces, including Victoria Park and the Tower of London moat, as part of the 'Dig for Victory' campaign", 'level': 5, 'parent': f'{OPTION_CODE}_London_Env_T1'},
    {'code': f'{OPTION_CODE}_London_Env_T1_B5', 'title': 'The historical context of the Second World War: the nature and purpose of the Blitz. Government use of propaganda and censorship to influence attitudes about the Blitz', 'level': 5, 'parent': f'{OPTION_CODE}_London_Env_T1'},
    
    # Level 5: Bullets for Topic 2
    {'code': f'{OPTION_CODE}_London_Env_T2_B1', 'title': 'Knowledge of local sources relevant to the period and issue, e.g. personal accounts and photographs, local newspapers, local council records', 'level': 5, 'parent': f'{OPTION_CODE}_London_Env_T2'},
    {'code': f'{OPTION_CODE}_London_Env_T2_B2', 'title': 'Knowledge of national sources relevant to the period and issue, e.g. government records, newspapers, Mass Observation reports, newsreels, memoirs', 'level': 5, 'parent': f'{OPTION_CODE}_London_Env_T2'},
    {'code': f'{OPTION_CODE}_London_Env_T2_B3', 'title': 'Recognition of the strengths and weaknesses of different types of source for specific enquiries', 'level': 5, 'parent': f'{OPTION_CODE}_London_Env_T2'},
    {'code': f'{OPTION_CODE}_London_Env_T2_B4', 'title': 'Framing of questions relevant to the pursuit of a specific enquiry', 'level': 5, 'parent': f'{OPTION_CODE}_London_Env_T2'},
    {'code': f'{OPTION_CODE}_London_Env_T2_B5', 'title': 'Selection of appropriate sources for specific investigations', 'level': 5, 'parent': f'{OPTION_CODE}_London_Env_T2'},
]


def upload_option12_details():
    """Add Option 12 detailed content."""
    print(f"\n[INFO] Adding detailed content for Option 12: Warfare...")
    
    try:
        subject_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', SUBJECT_CODE).eq('qualification_type', 'GCSE').eq('exam_board', 'Edexcel').execute()
        
        if not subject_result.data:
            print("[ERROR] History subject not found!")
            return None
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        existing_topics = supabase.table('staging_aqa_topics').select('*').eq('subject_id', subject_id).execute()
        
        opt12_exists = any(t['topic_code'] == OPTION_CODE for t in existing_topics.data)
        if not opt12_exists:
            print(f"[ERROR] Option 12 not found!")
            return None
        
        # Delete old Option 12 details
        for t in existing_topics.data:
            if t['topic_code'].startswith(OPTION_CODE + '_'):
                supabase.table('staging_aqa_topics').delete().eq('id', t['id']).execute()
        
        print("[OK] Cleared old Option 12 details")
        
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
        print("[SUCCESS] OPTION 12: WARFARE - COMPLETE!")
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
    print("GCSE HISTORY - OPTION 12 DETAILED CONTENT")
    print("=" * 80)
    
    try:
        subject_id = upload_option12_details()
        
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


