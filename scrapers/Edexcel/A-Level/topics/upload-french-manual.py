"""
Edexcel French (9FR0) - Manual Topic Upload
Complete hierarchy with themes, sub-themes, and aspects.
French text preserved with English translations.
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
    'code': '9FR0',
    'name': 'French (listening, reading and writing)',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/French/2016/Specification%20and%20sample%20assessments/Specification_GCE_A_level_L3_in_French.pdf'
}

TOPICS = [
    # Level 0: Papers
    {'code': 'Paper1', 'title': 'Paper 1: Listening, Reading and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper2', 'title': 'Paper 2: Written Response to Works and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper3', 'title': 'Paper 3: Listening, Reading and Writing', 'level': 0, 'parent': None},
    
    # ==================================================================================
    # THEME 1: Les changements dans la société française
    # ==================================================================================
    {'code': 'Theme1', 'title': 'Theme 1: Les changements dans la société française (Changes in French Society)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 1.1
    {'code': 'T1-1', 'title': 'Les changements dans les structures familiales (Changes in Family Structures)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-1-1', 'title': 'Les changements dans les attitudes envers le mariage, les couples et la famille (Changes in attitudes towards marriage, couples and family)', 'level': 3, 'parent': 'T1-1'},
    
    # Sub-theme 1.2
    {'code': 'T1-2', 'title': "L'éducation (Education)", 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-2-1', 'title': 'Le système éducatif et les questions estudiantines (The education system and student issues)', 'level': 3, 'parent': 'T1-2'},
    
    # Sub-theme 1.3
    {'code': 'T1-3', 'title': 'Le monde du travail (The World of Work)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-3-1', 'title': 'La vie active en France et les attitudes envers le travail (Working life in France and attitudes towards work)', 'level': 3, 'parent': 'T1-3'},
    {'code': 'T1-3-2', 'title': 'Le droit à la grève (The right to strike)', 'level': 3, 'parent': 'T1-3'},
    {'code': 'T1-3-3', 'title': "L'égalité des sexes (Gender equality)", 'level': 3, 'parent': 'T1-3'},
    
    # ==================================================================================
    # THEME 2: La culture politique et artistique dans les pays francophones
    # ==================================================================================
    {'code': 'Theme2', 'title': 'Theme 2: La culture politique et artistique dans les pays francophones (Political and Artistic Culture in Francophone Countries)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 2.1
    {'code': 'T2-1', 'title': 'La musique (Music)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-1-1', 'title': 'Les changements et les développements (Changes and developments)', 'level': 3, 'parent': 'T2-1'},
    {'code': 'T2-1-2', 'title': "L'impact de la musique sur la culture populaire (The impact of music on popular culture)", 'level': 3, 'parent': 'T2-1'},
    
    # Sub-theme 2.2
    {'code': 'T2-2', 'title': 'Les médias (Media)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-2-1', 'title': "La liberté d'expression (Freedom of expression)", 'level': 3, 'parent': 'T2-2'},
    {'code': 'T2-2-2', 'title': 'La presse écrite et en ligne (Print and online media)', 'level': 3, 'parent': 'T2-2'},
    {'code': 'T2-2-3', 'title': "L'impact sur la société et la politique (Impact on society and politics)", 'level': 3, 'parent': 'T2-2'},
    
    # Sub-theme 2.3
    {'code': 'T2-3', 'title': 'Les festivals et les traditions (Festivals and Traditions)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-3-1', 'title': 'Les festivals, fêtes, coutumes et traditions (Festivals, celebrations, customs and traditions)', 'level': 3, 'parent': 'T2-3'},
    
    # ==================================================================================
    # THEME 3: L'immigration et la société multiculturelle française
    # ==================================================================================
    {'code': 'Theme3', 'title': "Theme 3: L'immigration et la société multiculturelle française (Immigration and Multicultural French Society)", 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 3.1
    {'code': 'T3-1', 'title': "L'impact positif de l'immigration sur la société française (Positive Impact of Immigration on French Society)", 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-1-1', 'title': "Les contributions des immigrés à l'économie et à la culture (The contributions of immigrants to the economy and culture)", 'level': 3, 'parent': 'T3-1'},
    
    # Sub-theme 3.2
    {'code': 'T3-2', 'title': "Répondre aux défis de l'immigration et de l'intégration en France (Responding to the Challenges of Immigration and Integration in France)", 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-2-1', 'title': 'Les activités des communautés (Community activities)', 'level': 3, 'parent': 'T3-2'},
    {'code': 'T3-2-2', 'title': "La marginalisation et l'aliénation du point de vue des immigrés (Marginalization and alienation from the perspective of immigrants)", 'level': 3, 'parent': 'T3-2'},
    
    # Sub-theme 3.3
    {'code': 'T3-3', 'title': "L'extrême droite (The Far Right)", 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-3-1', 'title': 'La montée du Front National (The rise of the National Front)', 'level': 3, 'parent': 'T3-3'},
    {'code': 'T3-3-2', 'title': 'Les leaders du Front National (The leaders of the National Front)', 'level': 3, 'parent': 'T3-3'},
    {'code': 'T3-3-3', 'title': "L'opinion publique (Public opinion)", 'level': 3, 'parent': 'T3-3'},
    
    # ==================================================================================
    # THEME 4: L'Occupation et la Résistance
    # ==================================================================================
    {'code': 'Theme4', 'title': "Theme 4: L'Occupation et la Résistance (The Occupation and the Resistance)", 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 4.1
    {'code': 'T4-1', 'title': 'La France occupée (Occupied France)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-1-1', 'title': 'La collaboration (Collaboration)', 'level': 3, 'parent': 'T4-1'},
    {'code': 'T4-1-2', 'title': "L'antisémitisme (Anti-Semitism)", 'level': 3, 'parent': 'T4-1'},
    
    # Sub-theme 4.2
    {'code': 'T4-2', 'title': 'Le régime de Vichy (The Vichy Regime)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-2-1', 'title': 'Maréchal Pétain et la Révolution nationale (Marshal Pétain and the National Revolution)', 'level': 3, 'parent': 'T4-2'},
    
    # Sub-theme 4.3
    {'code': 'T4-3', 'title': 'La Résistance (The Resistance)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-3-1', 'title': 'Jean Moulin, Charles de Gaulle et les femmes de la Résistance (Jean Moulin, Charles de Gaulle and the women of the Resistance)', 'level': 3, 'parent': 'T4-3'},
    {'code': 'T4-3-2', 'title': "L'implication des Français dans la Résistance (The involvement of the French in the Resistance)", 'level': 3, 'parent': 'T4-3'},
]


def upload_topics():
    """Upload French topics to Supabase."""
    
    print("=" * 80)
    print("EDEXCEL FRENCH (9FR0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("\nComplete hierarchy with French text + English translations\n")
    
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
        print("[OK] FRENCH TOPICS UPLOADED SUCCESSFULLY!")
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

