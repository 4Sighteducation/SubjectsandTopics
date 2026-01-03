"""
GCSE History - Option 11 Detailed Content Upload
=================================================

Adds detailed content for Option 11: Medicine in Britain

Must run upload-history-structure.py FIRST!
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
OPTION_CODE = 'Paper1_Opt11'

NEW_TOPICS = [
    # Level 2: Two main sections
    {'code': f'{OPTION_CODE}_Medicine', 'title': 'Medicine in Britain, c1250–present (Thematic study)', 'level': 2, 'parent': OPTION_CODE},
    {'code': f'{OPTION_CODE}_WesternFront', 'title': 'The British sector of the Western Front, 1914–18 (Historic environment)', 'level': 2, 'parent': OPTION_CODE},
    
    # === MEDICINE SECTION ===
    
    # Level 3: Time periods
    {'code': f'{OPTION_CODE}_Medicine_P1', 'title': 'c1250–c1500: Medicine in medieval England', 'level': 3, 'parent': f'{OPTION_CODE}_Medicine'},
    {'code': f'{OPTION_CODE}_Medicine_P2', 'title': 'c1500–c1700: The Medical Renaissance in England', 'level': 3, 'parent': f'{OPTION_CODE}_Medicine'},
    {'code': f'{OPTION_CODE}_Medicine_P3', 'title': 'c1700–c1900: Medicine in eighteenth- and nineteenth-century Britain', 'level': 3, 'parent': f'{OPTION_CODE}_Medicine'},
    {'code': f'{OPTION_CODE}_Medicine_P4', 'title': 'c1900–present: Medicine in modern Britain', 'level': 3, 'parent': f'{OPTION_CODE}_Medicine'},
    
    # PERIOD 1: c1250-c1500
    {'code': f'{OPTION_CODE}_Medicine_P1_T1', 'title': '1. Ideas about the cause of disease and illness', 'level': 4, 'parent': f'{OPTION_CODE}_Medicine_P1'},
    {'code': f'{OPTION_CODE}_Medicine_P1_T2', 'title': '2. Approaches to prevention and treatment', 'level': 4, 'parent': f'{OPTION_CODE}_Medicine_P1'},
    {'code': f'{OPTION_CODE}_Medicine_P1_T3', 'title': '3. Case study', 'level': 4, 'parent': f'{OPTION_CODE}_Medicine_P1'},
    
    {'code': f'{OPTION_CODE}_Medicine_P1_T1_B1', 'title': 'Supernatural and religious explanations of the cause of disease', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P1_T1'},
    {'code': f'{OPTION_CODE}_Medicine_P1_T1_B2', 'title': 'Rational explanations: the Theory of the Four Humours and the miasma theory; the continuing influence in England of Galen', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P1_T1'},
    {'code': f'{OPTION_CODE}_Medicine_P1_T2_B1', 'title': 'Approaches to prevention and treatment, and their connection with ideas about disease and illness: religious actions, bloodletting and purging, purifying the air', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P1_T2'},
    {'code': f'{OPTION_CODE}_Medicine_P1_T2_B2', 'title': 'Medical training and traditional approaches to treatment and care for the sick: the role of the physician, apothecary and barber surgeon; the role of hospitals, care within the community and at home, including the use of herbal remedies', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P1_T2'},
    {'code': f'{OPTION_CODE}_Medicine_P1_T3_B1', 'title': 'Dealing with the Black Death, 1348–49; approaches to treatment and attempts to prevent its spread', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P1_T3'},
    
    # PERIOD 2: c1500-c1700
    {'code': f'{OPTION_CODE}_Medicine_P2_T1', 'title': '1. Ideas about the cause of disease and illness', 'level': 4, 'parent': f'{OPTION_CODE}_Medicine_P2'},
    {'code': f'{OPTION_CODE}_Medicine_P2_T2', 'title': '2. Approaches to prevention and treatment', 'level': 4, 'parent': f'{OPTION_CODE}_Medicine_P2'},
    {'code': f'{OPTION_CODE}_Medicine_P2_T3', 'title': '3. Case studies', 'level': 4, 'parent': f'{OPTION_CODE}_Medicine_P2'},
    
    {'code': f'{OPTION_CODE}_Medicine_P2_T1_B1', 'title': 'Continuity and change in explanations of the cause of disease and illness. A scientific approach, including the work of Thomas Sydenham in improving diagnosis. The influence of the printing press and the work of the Royal Society on the transmission of ideas', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P2_T1'},
    {'code': f'{OPTION_CODE}_Medicine_P2_T2_B1', 'title': 'Continuity and change in approaches to prevention, treatment and care in the community and in hospitals', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P2_T2'},
    {'code': f'{OPTION_CODE}_Medicine_P2_T2_B2', 'title': 'Improvements in medical training and the influence in England of the work of Vesalius', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P2_T2'},
    {'code': f'{OPTION_CODE}_Medicine_P2_T3_B1', 'title': 'Key individual: William Harvey and the discovery of the circulation of the blood', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P2_T3'},
    {'code': f'{OPTION_CODE}_Medicine_P2_T3_B2', 'title': 'Dealing with the Great Plague in London (1665): approaches to treatment and attempts to prevent its spread', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P2_T3'},
    
    # PERIOD 3: c1700-c1900
    {'code': f'{OPTION_CODE}_Medicine_P3_T1', 'title': '1. Ideas about the cause of disease and illness', 'level': 4, 'parent': f'{OPTION_CODE}_Medicine_P3'},
    {'code': f'{OPTION_CODE}_Medicine_P3_T2', 'title': '2. Approaches to prevention and treatment', 'level': 4, 'parent': f'{OPTION_CODE}_Medicine_P3'},
    {'code': f'{OPTION_CODE}_Medicine_P3_T3', 'title': '3. Case studies', 'level': 4, 'parent': f'{OPTION_CODE}_Medicine_P3'},
    
    {'code': f'{OPTION_CODE}_Medicine_P3_T1_B1', 'title': "Continuity and change in explanations of the cause of disease and illness. The influence in Britain of Pasteur's Germ Theory and Koch's work on microbes", 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P3_T1'},
    {'code': f'{OPTION_CODE}_Medicine_P3_T2_B1', 'title': 'The extent of change in care and treatment: improvements in hospital care and the influence of Nightingale on nursing and hospitals in Britain. The impact of anaesthetics and antiseptics on surgery', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P3_T2'},
    {'code': f'{OPTION_CODE}_Medicine_P3_T2_B2', 'title': 'New approaches to prevention: the development and use of vaccinations and the Public Health Act (1875)', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P3_T2'},
    {'code': f'{OPTION_CODE}_Medicine_P3_T3_B1', 'title': 'Key individual: Jenner and the development of vaccination', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P3_T3'},
    {'code': f'{OPTION_CODE}_Medicine_P3_T3_B2', 'title': 'Fighting Cholera in London (1854); attempts to prevent its spread; the significance of Snow and the Broad Street pump', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P3_T3'},
    
    # PERIOD 4: c1900-present
    {'code': f'{OPTION_CODE}_Medicine_P4_T1', 'title': '1. Ideas about the cause of disease and illness', 'level': 4, 'parent': f'{OPTION_CODE}_Medicine_P4'},
    {'code': f'{OPTION_CODE}_Medicine_P4_T2', 'title': '2. Approaches to prevention and treatment', 'level': 4, 'parent': f'{OPTION_CODE}_Medicine_P4'},
    {'code': f'{OPTION_CODE}_Medicine_P4_T3', 'title': '3. Case studies', 'level': 4, 'parent': f'{OPTION_CODE}_Medicine_P4'},
    
    {'code': f'{OPTION_CODE}_Medicine_P4_T1_B1', 'title': 'Advances in understanding the causes of illness and disease: the influence of genetic and lifestyle factors on health', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P4_T1'},
    {'code': f'{OPTION_CODE}_Medicine_P4_T1_B2', 'title': 'Improvements in diagnosis: the impact of the availability of blood tests, scans and monitors', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P4_T1'},
    {'code': f'{OPTION_CODE}_Medicine_P4_T2_B1', 'title': 'The extent of change in care and treatment. The impact of the NHS and science and technology: improved access to care; advances in medicines, including magic bullets and antibiotics; high-tech medical and surgical treatment in hospitals', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P4_T2'},
    {'code': f'{OPTION_CODE}_Medicine_P4_T2_B2', 'title': 'New approaches to prevention: mass vaccinations and government lifestyle campaigns', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P4_T2'},
    {'code': f'{OPTION_CODE}_Medicine_P4_T3_B1', 'title': "Key individuals: Fleming, Florey and Chain's development of penicillin", 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P4_T3'},
    {'code': f'{OPTION_CODE}_Medicine_P4_T3_B2', 'title': 'The fight against lung cancer in the twenty-first century: the use of science and technology in diagnosis and treatment; government action', 'level': 5, 'parent': f'{OPTION_CODE}_Medicine_P4_T3'},
    
    # === WESTERN FRONT SECTION ===
    
    # Level 3: Section
    {'code': f'{OPTION_CODE}_WesternFront_Env', 'title': 'The historic environment', 'level': 3, 'parent': f'{OPTION_CODE}_WesternFront'},
    
    # Level 4: Topics
    {'code': f'{OPTION_CODE}_WesternFront_Env_T1', 'title': '1. The British sector of the Western Front, 1914–18: injuries, treatment and the trenches', 'level': 4, 'parent': f'{OPTION_CODE}_WesternFront_Env'},
    {'code': f'{OPTION_CODE}_WesternFront_Env_T2', 'title': '2. Knowledge, selection and use of sources for historical enquiries', 'level': 4, 'parent': f'{OPTION_CODE}_WesternFront_Env'},
    
    # Level 5: Bullets for Topic 1
    {'code': f'{OPTION_CODE}_WesternFront_Env_T1_B1', 'title': 'The context of the British sector of Western Front and the theatre of war in Flanders and northern France: the Ypres salient, the Somme, Arras and Cambrai. The trench system - its organisation, including frontline and support trenches. Significance for medical treatment of the nature of the terrain and problems of the transport and communications infrastructure', 'level': 5, 'parent': f'{OPTION_CODE}_WesternFront_Env_T1'},
    {'code': f'{OPTION_CODE}_WesternFront_Env_T1_B2', 'title': 'Conditions requiring medical treatment on the Western Front, including the problems of ill health arising from the trench environment. The nature of wounds from rifles and explosives. The problem of shrapnel, wound infection and increased numbers of head injuries. The effects of gas attacks', 'level': 5, 'parent': f'{OPTION_CODE}_WesternFront_Env_T1'},
    {'code': f'{OPTION_CODE}_WesternFront_Env_T1_B3', 'title': 'Medical treatment on the Western Front. The work of the RAMC and nurses. Transport in the chain of evacuation: stretcher bearers, horse and motor ambulances. Stages of treatment in the chain of evacuation: aid post and field ambulance, dressing station, casualty clearing station, base hospital. The underground hospital at Arras', 'level': 5, 'parent': f'{OPTION_CODE}_WesternFront_Env_T1'},
    {'code': f'{OPTION_CODE}_WesternFront_Env_T1_B4', 'title': 'The significance of the Western Front for experiments in surgery and medicine: new techniques in the treatment of wounds and infection, the Thomas splint, the use of mobile x-ray units, the creation of a blood bank for the Battle of Cambrai', 'level': 5, 'parent': f'{OPTION_CODE}_WesternFront_Env_T1'},
    {'code': f'{OPTION_CODE}_WesternFront_Env_T1_B5', 'title': 'The historical context of medicine in the early twentieth century: the understanding of infection and moves towards aseptic surgery; the development of x-rays; blood transfusions and developments in the storage of blood', 'level': 5, 'parent': f'{OPTION_CODE}_WesternFront_Env_T1'},
    
    # Level 5: Bullets for Topic 2
    {'code': f'{OPTION_CODE}_WesternFront_Env_T2_B1', 'title': 'Knowledge of national sources relevant to the period and issue, e.g. army records, national newspapers, government reports, medical articles', 'level': 5, 'parent': f'{OPTION_CODE}_WesternFront_Env_T2'},
    {'code': f'{OPTION_CODE}_WesternFront_Env_T2_B2', 'title': 'Knowledge of local sources relevant to the period and issue, e.g. personal accounts, photographs, hospital records, army statistics', 'level': 5, 'parent': f'{OPTION_CODE}_WesternFront_Env_T2'},
    {'code': f'{OPTION_CODE}_WesternFront_Env_T2_B3', 'title': 'Recognition of the strengths and weaknesses of different types of source for specific enquiries', 'level': 5, 'parent': f'{OPTION_CODE}_WesternFront_Env_T2'},
    {'code': f'{OPTION_CODE}_WesternFront_Env_T2_B4', 'title': 'Framing of questions relevant to the pursuit of a specific enquiry', 'level': 5, 'parent': f'{OPTION_CODE}_WesternFront_Env_T2'},
    {'code': f'{OPTION_CODE}_WesternFront_Env_T2_B5', 'title': 'Selection of appropriate sources for specific investigations', 'level': 5, 'parent': f'{OPTION_CODE}_WesternFront_Env_T2'},
]


def upload_option11_details():
    """Add Option 11 detailed content."""
    print(f"\n[INFO] Adding detailed content for Option 11: Medicine...")
    
    try:
        # Get History subject
        subject_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', SUBJECT_CODE).eq('qualification_type', 'GCSE').eq('exam_board', 'Edexcel').execute()
        
        if not subject_result.data:
            print("[ERROR] History subject not found!")
            return None
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        # Get existing topics
        existing_topics = supabase.table('staging_aqa_topics').select('*').eq('subject_id', subject_id).execute()
        
        # Check Option 11 exists
        opt11_exists = any(t['topic_code'] == OPTION_CODE for t in existing_topics.data)
        if not opt11_exists:
            print(f"[ERROR] Option 11 not found!")
            return None
        
        print(f"[OK] Found {len(existing_topics.data)} existing topics")
        
        # Delete old Option 11 details
        for t in existing_topics.data:
            if t['topic_code'].startswith(OPTION_CODE + '_'):
                supabase.table('staging_aqa_topics').delete().eq('id', t['id']).execute()
        
        print("[OK] Cleared old Option 11 details")
        
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
        
        # Summary
        levels = defaultdict(int)
        for t in NEW_TOPICS:
            levels[t['level']] += 1
        
        print("\n" + "=" * 80)
        print("[SUCCESS] OPTION 11: MEDICINE IN BRITAIN - COMPLETE!")
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
    print("GCSE HISTORY - OPTION 11 DETAILED CONTENT")
    print("=" * 80)
    
    try:
        subject_id = upload_option11_details()
        
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


