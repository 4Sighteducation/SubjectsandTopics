"""
Edexcel Portuguese (9PT0) - Manual Topic Upload
Complete hierarchy with themes, sub-themes, and aspects.
Portuguese text preserved with English translations.
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
    'code': '9PT0',
    'name': 'Portuguese (listening, reading and writing)',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Portuguese/2018/specification-and-sample-assessments/A-level-Portugese-Specification1.pdf'
}

TOPICS = [
    # Level 0: Papers
    {'code': 'Paper1', 'title': 'Paper 1: Listening, Reading and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper2', 'title': 'Paper 2: Written Response to Works and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper3', 'title': 'Paper 3: Listening, Reading and Writing', 'level': 0, 'parent': None},
    
    # ==================================================================================
    # THEME 1: Mudanças na sociedade contemporânea
    # ==================================================================================
    {'code': 'Theme1', 'title': 'Tema 1: Mudanças na sociedade contemporânea (Changes in Contemporary Society)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 1.1
    {'code': 'T1-1', 'title': 'Mudanças na estrutura familiar (Changes in Family Structure)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-1-1', 'title': 'Mudanças nas atitudes face ao matrimónio e às relações pessoais (Changes in attitudes towards marriage and personal relationships)', 'level': 3, 'parent': 'T1-1'},
    {'code': 'T1-1-2', 'title': 'os novos tipos de família (new types of family)', 'level': 3, 'parent': 'T1-1'},
    {'code': 'T1-1-3', 'title': 'o papel da família alargada (the role of the extended family)', 'level': 3, 'parent': 'T1-1'},
    
    # Sub-theme 1.2
    {'code': 'T1-2', 'title': 'O mundo do trabalho (The World of Work)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-2-1', 'title': 'A vida laboral e atitudes face ao trabalho (Working life and attitudes towards work)', 'level': 3, 'parent': 'T1-2'},
    {'code': 'T1-2-2', 'title': 'o desemprego (unemployment)', 'level': 3, 'parent': 'T1-2'},
    {'code': 'T1-2-3', 'title': 'a igualdade de género (gender equality)', 'level': 3, 'parent': 'T1-2'},
    
    # Research Topic 1
    {'code': 'T1-R', 'title': 'Tema de pesquisa: A importância da educação após o ensino secundário em Portugal (Research: The Importance of Post-Secondary Education in Portugal)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-R-1', 'title': 'Opções no ensino superior e técnico (Options in higher and technical education)', 'level': 3, 'parent': 'T1-R'},
    {'code': 'T1-R-2', 'title': 'estágios (internships)', 'level': 3, 'parent': 'T1-R'},
    {'code': 'T1-R-3', 'title': 'voluntariado (volunteering)', 'level': 3, 'parent': 'T1-R'},
    
    # ==================================================================================
    # THEME 2: Cultura política e artística nos países de língua portuguesa
    # ==================================================================================
    {'code': 'Theme2', 'title': 'Tema 2: Cultura política e artística nos países de língua portuguesa (Political and Artistic Culture in Portuguese-speaking Countries)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 2.1
    {'code': 'T2-1', 'title': 'Os media (Media)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-1-1', 'title': 'Liberdade de expressão (Freedom of expression)', 'level': 3, 'parent': 'T2-1'},
    {'code': 'T2-1-2', 'title': 'a imprensa escrita e online (print and online media)', 'level': 3, 'parent': 'T2-1'},
    {'code': 'T2-1-3', 'title': 'o impacto na sociedade e na política (impact on society and politics)', 'level': 3, 'parent': 'T2-1'},
    
    # Sub-theme 2.2
    {'code': 'T2-2', 'title': 'Música (Music)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-2-1', 'title': 'Mudança e evolução (Change and evolution)', 'level': 3, 'parent': 'T2-2'},
    {'code': 'T2-2-2', 'title': 'o impacto da música na cultura popular (the impact of music on popular culture)', 'level': 3, 'parent': 'T2-2'},
    {'code': 'T2-2-3', 'title': 'music festivals (music festivals)', 'level': 3, 'parent': 'T2-2'},
    
    # Research Topic 2
    {'code': 'T2-R', 'title': 'Tema de pesquisa: Lusofonia no mundo atual (Research: Lusophony in Today\'s World)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-R-1', 'title': 'Unindo os países de língua oficial portuguesa através da CPLP (Uniting Portuguese-speaking countries through CPLP)', 'level': 3, 'parent': 'T2-R'},
    {'code': 'T2-R-2', 'title': 'Eventos culturais que celebram a Lusofonia (Cultural events celebrating Lusophony)', 'level': 3, 'parent': 'T2-R'},
    {'code': 'T2-R-3', 'title': 'O enriquecimento da língua portuguesa através da diversidade linguística (The enrichment of Portuguese through linguistic diversity)', 'level': 3, 'parent': 'T2-R'},
    
    # ==================================================================================
    # THEME 3: Movimentos migratórios
    # ==================================================================================
    {'code': 'Theme3', 'title': 'Tema 3: Movimentos migratórios (Migration Movements)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 3.1
    {'code': 'T3-1', 'title': 'A imigração e a sociedade multicultural Portuguesa (Immigration and Portuguese Multicultural Society)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-1-1', 'title': 'Marginalização e alienação na perspetiva dos imigrantes (Marginalization and alienation from the perspective of immigrants)', 'level': 3, 'parent': 'T3-1'},
    {'code': 'T3-1-2', 'title': 'os passos para integração (steps towards integration)', 'level': 3, 'parent': 'T3-1'},
    {'code': 'T3-1-3', 'title': 'contribuição da imigração na cultura e na sociedade (contribution of immigration to culture and society)', 'level': 3, 'parent': 'T3-1'},
    
    # Sub-theme 3.2
    {'code': 'T3-2', 'title': 'Emigração de Portugal no século XXI (Emigration from Portugal in the 21st Century)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-2-1', 'title': 'Os motivos para a emigração (reasons for emigration)', 'level': 3, 'parent': 'T3-2'},
    {'code': 'T3-2-2', 'title': 'o impacto na sociedade (impact on society)', 'level': 3, 'parent': 'T3-2'},
    {'code': 'T3-2-3', 'title': 'a contribuição dos emigrantes retornados na sociedade Portuguesa (contribution of returned emigrants to Portuguese society)', 'level': 3, 'parent': 'T3-2'},
    
    # Research Topic 3
    {'code': 'T3-R', 'title': 'Tema de pesquisa: Movimento migratório em Portugal (Research: Migration Movement in Portugal)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-R-1', 'title': 'O êxodo rural (rural exodus)', 'level': 3, 'parent': 'T3-R'},
    {'code': 'T3-R-2', 'title': 'as oportunidades de trabalho na cidade e no campo (job opportunities in the city and countryside)', 'level': 3, 'parent': 'T3-R'},
    {'code': 'T3-R-3', 'title': 'o acesso à formação na cidade e no campo (access to training in the city and countryside)', 'level': 3, 'parent': 'T3-R'},
    
    # ==================================================================================
    # THEME 4: Como a História moldou a Política
    # ==================================================================================
    {'code': 'Theme4', 'title': 'Tema 4: Como a História moldou a Política (How History Shaped Politics)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 4.1
    {'code': 'T4-1', 'title': 'A ditadura de Salazar (The Salazar Dictatorship)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-1-1', 'title': 'Pide (Polícia Internacional de Defesa do Estado) e a censura (PIDE and censorship)', 'level': 3, 'parent': 'T4-1'},
    {'code': 'T4-1-2', 'title': 'o impacto da ditadura na sociedade da época (the impact of the dictatorship on society at the time)', 'level': 3, 'parent': 'T4-1'},
    {'code': 'T4-1-3', 'title': 'ditadura em declínio – Portugal nos finais do anos 60 e princípios dos anos 70 (dictatorship in decline - Portugal in the late 60s and early 70s)', 'level': 3, 'parent': 'T4-1'},
    
    # Sub-theme 4.2
    {'code': 'T4-2', 'title': 'Da ditadura à democracia (From Dictatorship to Democracy)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-2-1', 'title': 'O 25 de Abril e a Revolução dos Cravos (April 25 and the Carnation Revolution)', 'level': 3, 'parent': 'T4-2'},
    {'code': 'T4-2-2', 'title': 'o movimento das Forças Armadas (the Armed Forces Movement)', 'level': 3, 'parent': 'T4-2'},
    {'code': 'T4-2-3', 'title': 'Portugal na Comunidade Europeia (Portugal in the European Community)', 'level': 3, 'parent': 'T4-2'},
    
    # Research Topic 4
    {'code': 'T4-R', 'title': 'Tema de pesquisa: Os Descobrimentos - a viagem de Vasco da Gama à India (Research: The Discoveries - Vasco da Gama\'s Voyage to India)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-R-1', 'title': 'A importância de assegurar uma rota comercial para a India (The importance of securing a trade route to India)', 'level': 3, 'parent': 'T4-R'},
    {'code': 'T4-R-2', 'title': 'Lisboa, o centro de negócios da Europa no século XVI (Lisbon, the business center of Europe in the 16th century)', 'level': 3, 'parent': 'T4-R'},
    {'code': 'T4-R-3', 'title': 'o impacto dessa viagem na sociedade Portuguesa da época (the impact of this voyage on Portuguese society at the time)', 'level': 3, 'parent': 'T4-R'},
]


def upload_topics():
    """Upload Portuguese topics to Supabase."""
    
    print("=" * 80)
    print("EDEXCEL PORTUGUESE (9PT0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("\nComplete hierarchy with Portuguese text + English translations\n")
    
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
        print("[OK] PORTUGUESE TOPICS UPLOADED SUCCESSFULLY!")
        print("=" * 80)
        
        # Show hierarchy breakdown
        levels = {}
        for t in TOPICS:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("\n[INFO] Hierarchy:")
        print(f"   Level 0 (Papers): {levels.get(0, 0)}")
        print(f"   Level 1 (Themes): {levels.get(1, 0)}")
        print(f"   Level 2 (Sub-themes + Research): {levels.get(2, 0)}")
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

