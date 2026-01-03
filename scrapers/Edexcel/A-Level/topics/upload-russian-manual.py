"""
Edexcel Russian (9RU0) - Manual Topic Upload
Complete hierarchy with themes, sub-themes, and aspects.
Russian text preserved with English translations.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT = {
    'code': '9RU0',
    'name': 'Russian (listening, reading and writing)',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Russian/2017/specification-sample-assessments/Specification_GCE_A_level_L3_in_Russian.pdf'
}

TOPICS = [
    # Level 0: Papers
    {'code': 'Paper1', 'title': 'Paper 1: Listening, Reading and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper2', 'title': 'Paper 2: Written Response to Works and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper3', 'title': 'Paper 3: Listening, Reading and Writing', 'level': 0, 'parent': None},
    
    # ==================================================================================
    # THEME 1: Развитие российского общества
    # ==================================================================================
    {'code': 'Theme1', 'title': 'Тема 1: Развитие российского общества (Theme 1: Development of Russian Society)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 1.1
    {'code': 'T1-1', 'title': 'Жизнь российской молодёжи (Life of Russian Youth)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-1-1', 'title': 'Здоровье (health)', 'level': 3, 'parent': 'T1-1'},
    {'code': 'T1-1-2', 'title': 'отдых (leisure)', 'level': 3, 'parent': 'T1-1'},
    {'code': 'T1-1-3', 'title': 'новые технологии (new technologies)', 'level': 3, 'parent': 'T1-1'},
    
    # Sub-theme 1.2
    {'code': 'T1-2', 'title': 'Образование (Education)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-2-1', 'title': 'Система образования (education system)', 'level': 3, 'parent': 'T1-2'},
    {'code': 'T1-2-2', 'title': 'жизнь российских школьников (life of Russian schoolchildren)', 'level': 3, 'parent': 'T1-2'},
    
    # Sub-theme 1.3
    {'code': 'T1-3', 'title': 'Мир труда (World of Work)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-3-1', 'title': 'Отношение к труду (attitudes to work)', 'level': 3, 'parent': 'T1-3'},
    {'code': 'T1-3-2', 'title': 'возможности для молодых россиян (opportunities for young Russians)', 'level': 3, 'parent': 'T1-3'},
    {'code': 'T1-3-3', 'title': 'равноправие (equality)', 'level': 3, 'parent': 'T1-3'},
    
    # ==================================================================================
    # THEME 2: Политическая и художественная культура
    # ==================================================================================
    {'code': 'Theme2', 'title': 'Тема 2: Политическая и художественная культура в русскоязычном мире (Theme 2: Political and Artistic Culture in the Russian-speaking World)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 2.1
    {'code': 'T2-1', 'title': 'Средства массовой информации (Mass Media)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-1-1', 'title': 'Свобода выражения (freedom of expression)', 'level': 3, 'parent': 'T2-1'},
    {'code': 'T2-1-2', 'title': 'печатная и онлайн пресса (print and online press)', 'level': 3, 'parent': 'T2-1'},
    {'code': 'T2-1-3', 'title': 'влияние на общество и политику (influence on society and politics)', 'level': 3, 'parent': 'T2-1'},
    
    # Sub-theme 2.2
    {'code': 'T2-2', 'title': 'Массовая культура (Popular Culture)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-2-1', 'title': 'Музыка (music)', 'level': 3, 'parent': 'T2-2'},
    {'code': 'T2-2-2', 'title': 'цирк (circus)', 'level': 3, 'parent': 'T2-2'},
    {'code': 'T2-2-3', 'title': 'танец (dance)', 'level': 3, 'parent': 'T2-2'},
    
    # Sub-theme 2.3
    {'code': 'T2-3', 'title': 'Праздники, фестивали и традиции (Holidays, Festivals and Traditions)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-3-1', 'title': 'Фестивали (festivals)', 'level': 3, 'parent': 'T2-3'},
    {'code': 'T2-3-2', 'title': 'праздники (holidays)', 'level': 3, 'parent': 'T2-3'},
    {'code': 'T2-3-3', 'title': 'обычаи (customs)', 'level': 3, 'parent': 'T2-3'},
    {'code': 'T2-3-4', 'title': 'традиции (traditions)', 'level': 3, 'parent': 'T2-3'},
    
    # ==================================================================================
    # THEME 3: Москва или Санкт-Петербург
    # ==================================================================================
    {'code': 'Theme3', 'title': 'Тема 3: Москва или Санкт-Петербург - Изменения в жизни большого российского города (Theme 3: Moscow or St. Petersburg - Changes in the Life of a Major Russian City)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 3.1
    {'code': 'T3-1', 'title': 'Изменение населения (Population Change)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-1-1', 'title': 'Жизнь в городе (life in the city)', 'level': 3, 'parent': 'T3-1'},
    {'code': 'T3-1-2', 'title': 'жизнь в пригородах (life in the suburbs)', 'level': 3, 'parent': 'T3-1'},
    
    # Sub-theme 3.2
    {'code': 'T3-2', 'title': 'Общественные проблемы (Social Problems)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-2-1', 'title': 'Бездомность (homelessness)', 'level': 3, 'parent': 'T3-2'},
    {'code': 'T3-2-2', 'title': 'преступность (crime)', 'level': 3, 'parent': 'T3-2'},
    
    # Sub-theme 3.3
    {'code': 'T3-3', 'title': 'Окружающая среда (Environment)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-3-1', 'title': 'Реконструкция и благоустройства города (reconstruction and improvement of the city)', 'level': 3, 'parent': 'T3-3'},
    {'code': 'T3-3-2', 'title': 'загрязнение (pollution)', 'level': 3, 'parent': 'T3-3'},
    
    # ==================================================================================
    # THEME 4: Последние годы СССР - М.С. Горбачёв (1985-1991)
    # ==================================================================================
    {'code': 'Theme4', 'title': 'Тема 4: Последние годы СССР - М.С. Горбачёв (1985-1991) (Theme 4: The Last Years of the USSR - M.S. Gorbachev)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 4.1
    {'code': 'T4-1', 'title': 'Перестройка (Perestroika)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-1-1', 'title': 'Что вызвало перестройку (what caused perestroika)', 'level': 3, 'parent': 'T4-1'},
    {'code': 'T4-1-2', 'title': 'экономические изменения (economic changes)', 'level': 3, 'parent': 'T4-1'},
    {'code': 'T4-1-3', 'title': 'исходы (outcomes)', 'level': 3, 'parent': 'T4-1'},
    
    # Sub-theme 4.2
    {'code': 'T4-2', 'title': 'Гласность (Glasnost)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-2-1', 'title': 'Что вызвало гласность (what caused glasnost)', 'level': 3, 'parent': 'T4-2'},
    {'code': 'T4-2-2', 'title': 'общественные изменения (social changes)', 'level': 3, 'parent': 'T4-2'},
    {'code': 'T4-2-3', 'title': 'исходы (outcomes)', 'level': 3, 'parent': 'T4-2'},
    
    # Sub-theme 4.3
    {'code': 'T4-3', 'title': '1991 год (The Year 1991)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-3-1', 'title': 'Проблемы для СССР к началу 1991 г. (problems for the USSR by the beginning of 1991)', 'level': 3, 'parent': 'T4-3'},
    {'code': 'T4-3-2', 'title': 'путч в августе (coup in August)', 'level': 3, 'parent': 'T4-3'},
    {'code': 'T4-3-3', 'title': 'распад СССР (collapse of the USSR)', 'level': 3, 'parent': 'T4-3'},
]


def upload_topics():
    """Upload Russian topics to Supabase."""
    
    print("=" * 80)
    print("EDEXCEL RUSSIAN (9RU0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("\nComplete hierarchy with Russian text + English translations\n")
    
    try:
        # Get/create subject
        print("[INFO] Creating/updating subject...")
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT['name']} (A-Level)",
            'subject_code': SUBJECT['code'],
            'qualification_type': 'A-Level',
            'specification_url': SUBJECT['pdf_url'],
            'exam_board': 'Edexcel'
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        # Clear old topics
        print("\n[INFO] Clearing old topics...")
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared")
        
        # Insert topics
        print(f"\n[INFO] Uploading {len(TOPICS)} topics...")
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'exam_board': 'Edexcel'
        } for t in TOPICS]
        
        inserted_result = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted_result.data)} topics")
        
        # Link hierarchy
        print("\n[INFO] Linking parent-child relationships...")
        code_to_id = {t['topic_code']: t['id'] for t in inserted_result.data}
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
        
        print(f"[OK] Linked {linked} relationships")
        
        # Summary
        print("\n" + "=" * 80)
        print("[OK] RUSSIAN TOPICS UPLOADED SUCCESSFULLY!")
        print("=" * 80)
        
        # Show hierarchy breakdown
        levels = {}
        for t in TOPICS:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("\n[INFO] Hierarchy:")
        print(f"   Level 0 (Papers): {levels.get(0, 0)}")
        print(f"   Level 1 (Themes): {levels.get(1, 0)}")
        print(f"   Level 2 (Sub-themes): {levels.get(2, 0)}")
        print(f"   Level 3 (Aspects): {levels.get(3, 0)}")
        print(f"\n   Total: {len(TOPICS)} topics")
        
        print("\n" + "=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = upload_topics()
    sys.exit(0 if success else 1)











