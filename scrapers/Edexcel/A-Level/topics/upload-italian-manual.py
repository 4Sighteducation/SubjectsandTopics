"""
Edexcel Italian (9IN0) - Manual Topic Upload
Complete hierarchy with themes, sub-themes, and aspects.
Italian text preserved with English translations.
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
    'code': '9IN0',
    'name': 'Italian (listening, reading and writing)',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Italian/2017/specification-and-sample-assessments/Specification_GCE_A_level_L3_in_Italian_August_2016_Draft.pdf'
}

TOPICS = [
    # Level 0: Papers
    {'code': 'Paper1', 'title': 'Paper 1: Listening, Reading and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper2', 'title': 'Paper 2: Written Response to Works and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper3', 'title': 'Paper 3: Listening, Reading and Writing', 'level': 0, 'parent': None},
    
    # ==================================================================================
    # THEME 1: I cambiamenti della società italiana
    # ==================================================================================
    {'code': 'Theme1', 'title': 'Tema 1: I cambiamenti della società italiana (Changes in Italian Society)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 1.1
    {'code': 'T1-1', 'title': "L'evoluzione della famiglia italiana (Evolution of the Italian Family)", 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-1-1', 'title': "Cambiamenti nell'atteggiamento verso il matrimonio, la coppia e la famiglia (Changes in attitudes towards marriage, couples and family)", 'level': 3, 'parent': 'T1-1'},
    {'code': 'T1-1-2', 'title': 'i mammoni (mummy\'s boys)', 'level': 3, 'parent': 'T1-1'},
    
    # Sub-theme 1.2
    {'code': 'T1-2', 'title': "L'istruzione (Education)", 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-2-1', 'title': 'Il sistema scolastico e i problemi degli studenti (The school system and student problems)', 'level': 3, 'parent': 'T1-2'},
    {'code': 'T1-2-2', 'title': 'la fuga dei cervelli (brain drain)', 'level': 3, 'parent': 'T1-2'},
    
    # Sub-theme 1.3
    {'code': 'T1-3', 'title': 'Il mondo del lavoro (The World of Work)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-3-1', 'title': 'La parità tra i sessi (Gender equality)', 'level': 3, 'parent': 'T1-3'},
    {'code': 'T1-3-2', 'title': 'la disoccupazione (unemployment)', 'level': 3, 'parent': 'T1-3'},
    {'code': 'T1-3-3', 'title': 'le imprese familiari (family businesses)', 'level': 3, 'parent': 'T1-3'},
    {'code': 'T1-3-4', 'title': 'i nuovi modelli di lavoro (new work models)', 'level': 3, 'parent': 'T1-3'},
    
    # ==================================================================================
    # THEME 2: La cultura politica ed artistica nei Paesi di lingua italiana
    # ==================================================================================
    {'code': 'Theme2', 'title': 'Tema 2: La cultura politica ed artistica nei Paesi di lingua italiana (Political and Artistic Culture in Italian-speaking Countries)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 2.1
    {'code': 'T2-1', 'title': 'La musica (Music)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-1-1', 'title': 'Cambiamenti e sviluppi (Changes and developments)', 'level': 3, 'parent': 'T2-1'},
    {'code': 'T2-1-2', 'title': 'impatto sulla cultura popolare (impact on popular culture)', 'level': 3, 'parent': 'T2-1'},
    
    # Sub-theme 2.2
    {'code': 'T2-2', 'title': 'I media (Media)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-2-1', 'title': 'Libertà di espressione (Freedom of expression)', 'level': 3, 'parent': 'T2-2'},
    {'code': 'T2-2-2', 'title': 'la stampa cartacea e online (print and online press)', 'level': 3, 'parent': 'T2-2'},
    {'code': 'T2-2-3', 'title': "l'impatto sulla società e la politica (impact on society and politics)", 'level': 3, 'parent': 'T2-2'},
    
    # Sub-theme 2.3
    {'code': 'T2-3', 'title': 'Il patrimonio culturale (Cultural Heritage)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-3-1', 'title': 'Feste, usi e costumi (Festivals, uses and customs)', 'level': 3, 'parent': 'T2-3'},
    
    # ==================================================================================
    # THEME 3: L'Italia: una società in evoluzione
    # ==================================================================================
    {'code': 'Theme3', 'title': "Tema 3: L'Italia: una società in evoluzione (Italy: A Society in Evolution)", 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 3.1
    {'code': 'T3-1', 'title': "L'impatto positivo dell'immigrazione in Italia (Positive Impact of Immigration in Italy)", 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-1-1', 'title': "Il contributo di immigrati e migranti all'economia e alla cultura (The contribution of immigrants and migrants to the economy and culture)", 'level': 3, 'parent': 'T3-1'},
    
    # Sub-theme 3.2
    {'code': 'T3-2', 'title': 'I problemi della migrazione in Italia (Problems of Migration in Italy)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-2-1', 'title': 'Marginalizzazione e alienazione (Marginalization and alienation)', 'level': 3, 'parent': 'T3-2'},
    {'code': 'T3-2-2', 'title': 'integrazione (integration)', 'level': 3, 'parent': 'T3-2'},
    {'code': 'T3-2-3', 'title': "impatto dell'emigrazione (impact of emigration)", 'level': 3, 'parent': 'T3-2'},
    
    # Sub-theme 3.3
    {'code': 'T3-3', 'title': 'Il divario Nord/Sud (The North/South Divide)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-3-1', 'title': 'Spostamenti tra Nord e Sud (Movements between North and South)', 'level': 3, 'parent': 'T3-3'},
    {'code': 'T3-3-2', 'title': 'il ruolo delle industrie italiane (the role of Italian industries)', 'level': 3, 'parent': 'T3-3'},
    {'code': 'T3-3-3', 'title': 'le differenze socio-culturali (socio-cultural differences)', 'level': 3, 'parent': 'T3-3'},
    {'code': 'T3-3-4', 'title': 'la criminalità (crime)', 'level': 3, 'parent': 'T3-3'},
    
    # ==================================================================================
    # THEME 4: Dal fascismo ai giorni nostri
    # ==================================================================================
    {'code': 'Theme4', 'title': 'Tema 4: Dal fascismo ai giorni nostri (From Fascism to Today)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 4.1
    {'code': 'T4-1', 'title': "L'ascesa di Mussolini al potere (The Rise of Mussolini to Power)", 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-1-1', 'title': 'La nascita del Partito Fascista (The birth of the Fascist Party)', 'level': 3, 'parent': 'T4-1'},
    
    # Sub-theme 4.2
    {'code': 'T4-2', 'title': 'Il Fascismo durante la Seconda Guerra Mondiale (Fascism During World War II)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-2-1', 'title': 'Il governo di Mussolini e la dittatura (The government of Mussolini and the dictatorship)', 'level': 3, 'parent': 'T4-2'},
    {'code': 'T4-2-2', 'title': 'la vita sotto Mussolini durante la seconda guerra mondiale (life under Mussolini during World War II)', 'level': 3, 'parent': 'T4-2'},
    
    # Sub-theme 4.3
    {'code': 'T4-3', 'title': 'Dalla dittatura alla democrazia (From Dictatorship to Democracy)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-3-1', 'title': 'La caduta di Mussolini (The fall of Mussolini)', 'level': 3, 'parent': 'T4-3'},
    {'code': 'T4-3-2', 'title': 'la liberazione (the liberation)', 'level': 3, 'parent': 'T4-3'},
    {'code': 'T4-3-3', 'title': 'le 6 nazioni (the 6 nations)', 'level': 3, 'parent': 'T4-3'},
]


def upload_topics():
    """Upload Italian topics to Supabase."""
    
    print("=" * 80)
    print("EDEXCEL ITALIAN (9IN0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("\nComplete hierarchy with Italian text + English translations\n")
    
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
        print("[OK] ITALIAN TOPICS UPLOADED SUCCESSFULLY!")
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

