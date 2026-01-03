"""
Edexcel Spanish (9SP0) - Manual Topic Upload
Complete hierarchy with themes, sub-themes, and aspects.
Spanish text preserved with English translations.
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
    'code': '9SP0',
    'name': 'Spanish (listening, reading and writing)',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Spanish/2016/Specification%20and%20sample%20assessments/Specification_GCE_A_level_L3_in_Spanish.pdf'
}

TOPICS = [
    # Level 0: Papers
    {'code': 'Paper1', 'title': 'Paper 1: Listening, Reading and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper2', 'title': 'Paper 2: Written Response to Works and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper3', 'title': 'Paper 3: Listening, Reading and Writing', 'level': 0, 'parent': None},
    
    # ==================================================================================
    # THEME 1: La evolución de la sociedad española
    # ==================================================================================
    {'code': 'Theme1', 'title': 'Theme 1: La evolución de la sociedad española (The Evolution of Spanish Society)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 1.1
    {'code': 'T1-1', 'title': 'El cambio en la estructura familiar (Change in Family Structure)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-1-1', 'title': 'La evolución de las actitudes hacia el matrimonio, las relaciones y las familias (The evolution of attitudes towards marriage, relationships and families)', 'level': 3, 'parent': 'T1-1'},
    
    # Sub-theme 1.2
    {'code': 'T1-2', 'title': 'El mundo laboral (The World of Work)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-2-1', 'title': 'La vida laboral en España y las actitudes hacia el trabajo (Working life in Spain and attitudes towards work)', 'level': 3, 'parent': 'T1-2'},
    {'code': 'T1-2-2', 'title': 'las oportunidades de trabajo para los jóvenes (job opportunities for young people)', 'level': 3, 'parent': 'T1-2'},
    {'code': 'T1-2-3', 'title': 'la igualdad de género (gender equality)', 'level': 3, 'parent': 'T1-2'},
    
    # Sub-theme 1.3
    {'code': 'T1-3', 'title': 'El impacto turístico en España (The Impact of Tourism in Spain)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-3-1', 'title': 'El impacto económico (Economic impact)', 'level': 3, 'parent': 'T1-3'},
    {'code': 'T1-3-2', 'title': 'las oportunidades que ofrece el turismo (the opportunities offered by tourism)', 'level': 3, 'parent': 'T1-3'},
    {'code': 'T1-3-3', 'title': 'el impacto socioambiental (the socio-environmental impact)', 'level': 3, 'parent': 'T1-3'},
    
    # ==================================================================================
    # THEME 2: La cultura política y artística en el mundo hispanohablante
    # ==================================================================================
    {'code': 'Theme2', 'title': 'Theme 2: La cultura política y artística en el mundo hispanohablante (Political and Artistic Culture in the Spanish-speaking World)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 2.1
    {'code': 'T2-1', 'title': 'La música (Music)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-1-1', 'title': 'Los cambios y las tendencias (Changes and trends)', 'level': 3, 'parent': 'T2-1'},
    {'code': 'T2-1-2', 'title': 'el impacto de la música en la cultura contemporánea (the impact of music on contemporary culture)', 'level': 3, 'parent': 'T2-1'},
    
    # Sub-theme 2.2
    {'code': 'T2-2', 'title': 'Los medios de comunicación (Media)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-2-1', 'title': 'La televisión y las telenovelas (Television and soap operas)', 'level': 3, 'parent': 'T2-2'},
    {'code': 'T2-2-2', 'title': 'los medios de comunicación escritos y en internet (print and online media)', 'level': 3, 'parent': 'T2-2'},
    {'code': 'T2-2-3', 'title': 'el impacto en la sociedad y la política (the impact on society and politics)', 'level': 3, 'parent': 'T2-2'},
    
    # Sub-theme 2.3
    {'code': 'T2-3', 'title': 'Los festivales y las tradiciones (Festivals and Traditions)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-3-1', 'title': 'Los festivales, las fiestas, las costumbres y las tradiciones (Festivals, celebrations, customs and traditions)', 'level': 3, 'parent': 'T2-3'},
    
    # ==================================================================================
    # THEME 3: La inmigración y la sociedad multicultural española
    # ==================================================================================
    {'code': 'Theme3', 'title': 'Theme 3: La inmigración y la sociedad multicultural española (Immigration and Multicultural Spanish Society)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 3.1
    {'code': 'T3-1', 'title': 'El impacto positivo de la inmigración en la sociedad Española (The Positive Impact of Immigration on Spanish Society)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-1-1', 'title': 'Las aportaciones de los inmigrantes en la economía y la cultura (The contributions of immigrants to the economy and culture)', 'level': 3, 'parent': 'T3-1'},
    
    # Sub-theme 3.2
    {'code': 'T3-2', 'title': 'Enfrentando los desafíos de la inmigración y la integración en España (Confronting the Challenges of Immigration and Integration in Spain)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-2-1', 'title': 'Las medidas adoptadas por las comunidades locales (Measures adopted by local communities)', 'level': 3, 'parent': 'T3-2'},
    {'code': 'T3-2-2', 'title': 'la marginación y el aislamiento desde el punto de vista de los inmigrantes (marginalization and isolation from the perspective of immigrants)', 'level': 3, 'parent': 'T3-2'},
    
    # Sub-theme 3.3
    {'code': 'T3-3', 'title': 'La reacción social y pública hacia la inmigración en España (Social and Public Reaction to Immigration in Spain)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-3-1', 'title': 'El enfoque político hacia la inmigración (The political approach to immigration)', 'level': 3, 'parent': 'T3-3'},
    {'code': 'T3-3-2', 'title': 'la opinión pública (public opinion)', 'level': 3, 'parent': 'T3-3'},
    
    # ==================================================================================
    # THEME 4: La dictadura franquista y la transición a la democracia
    # ==================================================================================
    {'code': 'Theme4', 'title': 'Theme 4: La dictadura franquista y la transición a la democracia (The Franco Dictatorship and the Transition to Democracy)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 4.1
    {'code': 'T4-1', 'title': 'La Guerra Civil y el ascenso de Franco (1936-1939) (The Civil War and the Rise of Franco)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-1-1', 'title': 'La Guerra Civil y el ascenso de Franco, los republicanos contra los nacionalistas (The Civil War and the rise of Franco, republicans versus nationalists)', 'level': 3, 'parent': 'T4-1'},
    {'code': 'T4-1-2', 'title': 'las divisiones en la sociedad (divisions in society)', 'level': 3, 'parent': 'T4-1'},
    
    # Sub-theme 4.2
    {'code': 'T4-2', 'title': 'La dictadura franquista (The Franco Dictatorship)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-2-1', 'title': 'La vida cotidiana bajo la dictadura franquista (Daily life under the Franco dictatorship)', 'level': 3, 'parent': 'T4-2'},
    {'code': 'T4-2-2', 'title': 'la opresión política (political oppression)', 'level': 3, 'parent': 'T4-2'},
    {'code': 'T4-2-3', 'title': 'la censura (censorship)', 'level': 3, 'parent': 'T4-2'},
    {'code': 'T4-2-4', 'title': 'las divisiones en la sociedad (divisions in society)', 'level': 3, 'parent': 'T4-2'},
    
    # Sub-theme 4.3
    {'code': 'T4-3', 'title': 'La transición de la dictadura a la democracia (The Transition from Dictatorship to Democracy)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-3-1', 'title': 'El papel del Rey Juan Carlos en la transición (The role of King Juan Carlos in the transition)', 'level': 3, 'parent': 'T4-3'},
    {'code': 'T4-3-2', 'title': 'el Gobierno de Suárez (the Suárez government)', 'level': 3, 'parent': 'T4-3'},
    {'code': 'T4-3-3', 'title': 'el golpe de Estado de 1981 (the coup attempt of 1981)', 'level': 3, 'parent': 'T4-3'},
]


def upload_topics():
    """Upload Spanish topics to Supabase."""
    
    print("=" * 80)
    print("EDEXCEL SPANISH (9SP0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("\nComplete hierarchy with Spanish text + English translations\n")
    
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
        print("[OK] SPANISH TOPICS UPLOADED SUCCESSFULLY!")
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

