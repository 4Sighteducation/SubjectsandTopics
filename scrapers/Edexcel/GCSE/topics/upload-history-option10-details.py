"""
GCSE History - Option 10 Detailed Content Upload
=================================================

Adds detailed content for Option 10: Crime and punishment

Must run upload-history-structure.py FIRST to create Papers and Options!

This adds:
- Level 2: Sections (Britain thematic + Whitechapel)
- Level 3: Time periods  
- Level 4: Numbered topics (1, 2, 3)
- Level 5: Bullet points
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
OPTION_CODE = 'Paper1_Opt10'

# New topics to add under Option 10
NEW_TOPICS = [
    # Level 2: Two main sections
    {'code': f'{OPTION_CODE}_Britain', 'title': 'Crime and punishment in Britain, c1000–present (Thematic study)', 'level': 2, 'parent': OPTION_CODE},
    {'code': f'{OPTION_CODE}_Whitechapel', 'title': 'Whitechapel, c1870–c1900 (Historic environment)', 'level': 2, 'parent': OPTION_CODE},
    
    # === BRITAIN SECTION ===
    
    # Level 3: Time periods
    {'code': f'{OPTION_CODE}_Britain_P1', 'title': 'c1000–c1500: Crime and punishment in medieval England', 'level': 3, 'parent': f'{OPTION_CODE}_Britain'},
    {'code': f'{OPTION_CODE}_Britain_P2', 'title': 'c1500–c1700: Crime and punishment in early modern England', 'level': 3, 'parent': f'{OPTION_CODE}_Britain'},
    {'code': f'{OPTION_CODE}_Britain_P3', 'title': 'c1700–c1900: Crime and punishment in eighteenth- and nineteenth-century Britain', 'level': 3, 'parent': f'{OPTION_CODE}_Britain'},
    {'code': f'{OPTION_CODE}_Britain_P4', 'title': 'c1900–present: Crime and punishment in modern Britain', 'level': 3, 'parent': f'{OPTION_CODE}_Britain'},
    
    # PERIOD 1: c1000-c1500
    # Level 4: Topics
    {'code': f'{OPTION_CODE}_Britain_P1_T1', 'title': '1. Nature and changing definitions of criminal activity', 'level': 4, 'parent': f'{OPTION_CODE}_Britain_P1'},
    {'code': f'{OPTION_CODE}_Britain_P1_T2', 'title': '2. The nature of law enforcement and punishment', 'level': 4, 'parent': f'{OPTION_CODE}_Britain_P1'},
    {'code': f'{OPTION_CODE}_Britain_P1_T3', 'title': '3. Case study', 'level': 4, 'parent': f'{OPTION_CODE}_Britain_P1'},
    
    # Level 5: Bullets
    {'code': f'{OPTION_CODE}_Britain_P1_T1_B1', 'title': "Crimes against the person, property and authority, including poaching as an example of 'social' crime", 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P1_T1'},
    {'code': f'{OPTION_CODE}_Britain_P1_T1_B2', 'title': "Changing definitions of crime as a result of the Norman Conquest, including William I's Forest Laws", 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P1_T1'},
    {'code': f'{OPTION_CODE}_Britain_P1_T2_B1', 'title': 'The role of the authorities and local communities in law enforcement in Anglo-Saxon, Norman and later medieval England, including tithings, the hue and cry, and the parish constable', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P1_T2'},
    {'code': f'{OPTION_CODE}_Britain_P1_T2_B2', 'title': 'The emphasis on deterrence and retribution, the use of fines, corporal and capital punishment. The use and end of the Saxon Wergild', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P1_T2'},
    {'code': f'{OPTION_CODE}_Britain_P1_T3_B1', 'title': 'The influence of the Church on crime and punishment in the early thirteenth century: the significance of Sanctuary and Benefit of Clergy; the use of trial by ordeal and reasons for its ending', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P1_T3'},
    
    # PERIOD 2: c1500-c1700
    # Level 4: Topics
    {'code': f'{OPTION_CODE}_Britain_P2_T1', 'title': '1. Nature and changing definitions of criminal activity', 'level': 4, 'parent': f'{OPTION_CODE}_Britain_P2'},
    {'code': f'{OPTION_CODE}_Britain_P2_T2', 'title': '2. The nature of law enforcement and punishment', 'level': 4, 'parent': f'{OPTION_CODE}_Britain_P2'},
    {'code': f'{OPTION_CODE}_Britain_P2_T3', 'title': '3. Case studies', 'level': 4, 'parent': f'{OPTION_CODE}_Britain_P2'},
    
    # Level 5: Bullets
    {'code': f'{OPTION_CODE}_Britain_P2_T1_B1', 'title': 'Continuity and change in the nature of crimes against the person, property and authority, including heresy and treason', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P2_T1'},
    {'code': f'{OPTION_CODE}_Britain_P2_T1_B2', 'title': 'New definitions of crime in the sixteenth century: vagabondage and witchcraft', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P2_T1'},
    {'code': f'{OPTION_CODE}_Britain_P2_T2_B1', 'title': 'The role of the authorities and local communities in law enforcement, including town watchmen', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P2_T2'},
    {'code': f'{OPTION_CODE}_Britain_P2_T2_B2', 'title': 'The continued use of corporal and capital punishment; the introduction of transportation and the start of the Bloody Code', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P2_T2'},
    {'code': f'{OPTION_CODE}_Britain_P2_T3_B1', 'title': 'The Gunpowder Plotters, 1605: their crimes and punishment', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P2_T3'},
    {'code': f'{OPTION_CODE}_Britain_P2_T3_B2', 'title': 'Key individual: Matthew Hopkins and the witch-hunts of 1645–47. The reasons for their intensity; the punishment of those convicted', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P2_T3'},
    
    # PERIOD 3: c1700-c1900
    # Level 4: Topics
    {'code': f'{OPTION_CODE}_Britain_P3_T1', 'title': '1. Nature and changing definitions of criminal activity', 'level': 4, 'parent': f'{OPTION_CODE}_Britain_P3'},
    {'code': f'{OPTION_CODE}_Britain_P3_T2', 'title': '2. The nature of law enforcement and punishment', 'level': 4, 'parent': f'{OPTION_CODE}_Britain_P3'},
    {'code': f'{OPTION_CODE}_Britain_P3_T3', 'title': '3. Case studies', 'level': 4, 'parent': f'{OPTION_CODE}_Britain_P3'},
    
    # Level 5: Bullets
    {'code': f'{OPTION_CODE}_Britain_P3_T1_B1', 'title': 'Continuity and change in the nature of crimes against the person, property and authority, including highway robbery, poaching and smuggling', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P3_T1'},
    {'code': f'{OPTION_CODE}_Britain_P3_T1_B2', 'title': 'Changing definitions of crime exemplified in the ending of witchcraft prosecutions and treatment of the Tolpuddle Martyrs', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P3_T1'},
    {'code': f'{OPTION_CODE}_Britain_P3_T2_B1', 'title': 'The role of the authorities and local communities in law enforcement, including the work of the Fielding brothers. The development of police forces and the beginning of CID', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P3_T2'},
    {'code': f'{OPTION_CODE}_Britain_P3_T2_B2', 'title': 'Changing views on the purpose of punishment. The use and ending of transportation, public execution and the Bloody Code. Prison reform, including the influence of John Howard and Elizabeth Fry', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P3_T2'},
    {'code': f'{OPTION_CODE}_Britain_P3_T3_B1', 'title': 'Pentonville prison in the mid nineteenth century: reasons for its construction; the strengths and weaknesses of the separate system in operation', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P3_T3'},
    {'code': f'{OPTION_CODE}_Britain_P3_T3_B2', 'title': 'Key individual: Robert Peel – his contribution to penal reform and to the development of the Metropolitan Police Force', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P3_T3'},
    
    # PERIOD 4: c1900-present
    # Level 4: Topics
    {'code': f'{OPTION_CODE}_Britain_P4_T1', 'title': '1. Nature and changing definitions of criminal activity', 'level': 4, 'parent': f'{OPTION_CODE}_Britain_P4'},
    {'code': f'{OPTION_CODE}_Britain_P4_T2', 'title': '2. The nature of law enforcement and punishment', 'level': 4, 'parent': f'{OPTION_CODE}_Britain_P4'},
    {'code': f'{OPTION_CODE}_Britain_P4_T3', 'title': '3. Case studies', 'level': 4, 'parent': f'{OPTION_CODE}_Britain_P4'},
    
    # Level 5: Bullets
    {'code': f'{OPTION_CODE}_Britain_P4_T1_B1', 'title': 'Continuity and change in the nature of crimes against the person, property and authority, including new forms of theft and smuggling', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P4_T1'},
    {'code': f'{OPTION_CODE}_Britain_P4_T1_B2', 'title': 'Changing definitions of crime, including driving offences, race crimes and drug crimes', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P4_T1'},
    {'code': f'{OPTION_CODE}_Britain_P4_T2_B1', 'title': 'The role of the authorities and local communities in law enforcement, including the development of Neighbourhood Watch. Changes within the police force: increasing specialisation, use of science and technology and the move towards prevention', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P4_T2'},
    {'code': f'{OPTION_CODE}_Britain_P4_T2_B2', 'title': 'The abolition of the death penalty; changes to prisons, including the development of open prisons and specialised treatment of young offenders; the development of non-custodial alternatives to prison', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P4_T2'},
    {'code': f'{OPTION_CODE}_Britain_P4_T3_B1', 'title': 'The treatment of Conscientious Objectors in the First and Second World Wars', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P4_T3'},
    {'code': f'{OPTION_CODE}_Britain_P4_T3_B2', 'title': 'The Derek Bentley case: its significance for the abolition of the death penalty', 'level': 5, 'parent': f'{OPTION_CODE}_Britain_P4_T3'},
    
    # === WHITECHAPEL SECTION ===
    
    # Level 3: Section
    {'code': f'{OPTION_CODE}_Whitechapel_Env', 'title': 'The historic environment', 'level': 3, 'parent': f'{OPTION_CODE}_Whitechapel'},
    
    # Level 4: Topics
    {'code': f'{OPTION_CODE}_Whitechapel_Env_T1', 'title': '1. Whitechapel, c1870–c1900: crime, policing and the inner city', 'level': 4, 'parent': f'{OPTION_CODE}_Whitechapel_Env'},
    {'code': f'{OPTION_CODE}_Whitechapel_Env_T2', 'title': '2. Knowledge, selection and use of sources for historical enquiries', 'level': 4, 'parent': f'{OPTION_CODE}_Whitechapel_Env'},
    
    # Level 5: Bullets for Topic 1
    {'code': f'{OPTION_CODE}_Whitechapel_Env_T1_B1', 'title': 'The local context of Whitechapel. The problems of housing and overcrowding. Attempts to improve housing: the Peabody Estate. Provision for the poor in the Whitechapel workhouses. Links between the environment and crime. Life in Whitechapel as an inner city area of poverty and discontent', 'level': 5, 'parent': f'{OPTION_CODE}_Whitechapel_Env_T1'},
    {'code': f'{OPTION_CODE}_Whitechapel_Env_T1_B2', 'title': 'The inhabitants of Whitechapel. The lack of employment opportunities and level of poverty. The prevalence of lodging houses and pubs creating a fluctuating population without ties to the community. The impact of changing patterns of migration: the settlement of migrants from Ireland and Eastern Europe, and the increase in Jewish migration during the 1880s', 'level': 5, 'parent': f'{OPTION_CODE}_Whitechapel_Env_T1'},
    {'code': f'{OPTION_CODE}_Whitechapel_Env_T1_B3', 'title': "The organisation of policing in Whitechapel. The role of the 'beat constable'. The work of H division and the difficulties of policing the slum area of Whitechapel, the rookeries, alleys and courts. Problems of policing caused by crime and antisocial behaviour: alcohol, prostitution, protection rackets, gangs, violent demonstrations and attacks on Jewish people", 'level': 5, 'parent': f'{OPTION_CODE}_Whitechapel_Env_T1'},
    {'code': f'{OPTION_CODE}_Whitechapel_Env_T1_B4', 'title': "Investigative policing in Whitechapel: developments in techniques of detective investigation, including the use of sketches, photographs and interviews; problems caused by the need for cooperation between the Metropolitan Police, the City of London Police and Scotland Yard. Dealing with the crimes of Jack the Ripper and the added problems caused by the media reporting of the 'Ripper' murders. The Whitechapel Vigilance Committee", 'level': 5, 'parent': f'{OPTION_CODE}_Whitechapel_Env_T1'},
    {'code': f'{OPTION_CODE}_Whitechapel_Env_T1_B5', 'title': 'The national and regional context: the working of the Metropolitan Police, the quality of police recruits. The development of CID, the role of the Home Secretary and of Sir Charles Warren, public attitudes towards the police', 'level': 5, 'parent': f'{OPTION_CODE}_Whitechapel_Env_T1'},
    
    # Level 5: Bullets for Topic 2
    {'code': f'{OPTION_CODE}_Whitechapel_Env_T2_B1', 'title': "Knowledge of local sources relevant to the period and issue, e.g. housing and employment records, council records and census returns, Charles Booth's survey, workhouse records, local police records, coroners' reports, photographs and London newspapers", 'level': 5, 'parent': f'{OPTION_CODE}_Whitechapel_Env_T2'},
    {'code': f'{OPTION_CODE}_Whitechapel_Env_T2_B2', 'title': 'Knowledge of national sources relevant to the period and issue, e.g. national newspapers, records of crimes and police investigations, Old Bailey records of trials and Punch cartoons', 'level': 5, 'parent': f'{OPTION_CODE}_Whitechapel_Env_T2'},
    {'code': f'{OPTION_CODE}_Whitechapel_Env_T2_B3', 'title': 'Recognition of the strengths and weaknesses of different types of source for specific enquiries', 'level': 5, 'parent': f'{OPTION_CODE}_Whitechapel_Env_T2'},
    {'code': f'{OPTION_CODE}_Whitechapel_Env_T2_B4', 'title': 'Framing of questions relevant to the pursuit of a specific enquiry', 'level': 5, 'parent': f'{OPTION_CODE}_Whitechapel_Env_T2'},
    {'code': f'{OPTION_CODE}_Whitechapel_Env_T2_B5', 'title': 'Selection of appropriate sources for specific investigations', 'level': 5, 'parent': f'{OPTION_CODE}_Whitechapel_Env_T2'},
]


def upload_option10_details():
    """Add Option 10 detailed content to existing structure."""
    print(f"\n[INFO] Adding detailed content for Option 10...")
    
    try:
        # Get History subject
        subject_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', SUBJECT_CODE).eq('qualification_type', 'GCSE').eq('exam_board', 'Edexcel').execute()
        
        if not subject_result.data:
            print("[ERROR] History subject not found! Run upload-history-structure.py first!")
            return None
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        # Get existing topics to verify Option 10 exists and to link parents
        existing_topics = supabase.table('staging_aqa_topics').select('*').eq('subject_id', subject_id).execute()
        
        # Check Option 10 exists
        opt10_exists = any(t['topic_code'] == OPTION_CODE for t in existing_topics.data)
        if not opt10_exists:
            print(f"[ERROR] Option 10 ({OPTION_CODE}) not found! Run upload-history-structure.py first!")
            return None
        
        print(f"[OK] Found {len(existing_topics.data)} existing topics")
        
        # Delete old Option 10 details (Level 2+) to allow re-running
        for t in existing_topics.data:
            if t['topic_code'].startswith(OPTION_CODE + '_'):
                supabase.table('staging_aqa_topics').delete().eq('id', t['id']).execute()
        
        print("[OK] Cleared old Option 10 details")
        
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
        
        # Link parent relationships
        code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
        # Also need existing topics for parents
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
        
        print(f"[OK] Linked {linked} parent-child relationships")
        
        # Summary
        levels = defaultdict(int)
        for t in NEW_TOPICS:
            levels[t['level']] += 1
        
        print("\n" + "=" * 80)
        print("[SUCCESS] OPTION 10: CRIME AND PUNISHMENT - DETAILS UPLOADED!")
        print("=" * 80)
        print(f"   Level 2 (Sections): {levels[2]}")
        print(f"   Level 3 (Periods): {levels[3]}")
        print(f"   Level 4 (Topics): {levels[4]}")
        print(f"   Level 5 (Bullets): {levels[5]}")
        print(f"\n   Total added: {len(NEW_TOPICS)} topics")
        print("=" * 80)
        
        return subject_id
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("=" * 80)
    print("GCSE HISTORY - OPTION 10 DETAILED CONTENT")
    print("=" * 80)
    
    try:
        subject_id = upload_option10_details()
        
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


