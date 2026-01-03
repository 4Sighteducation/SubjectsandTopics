"""
Edexcel German (9GN0) - Manual Topic Upload
Complete hierarchy with themes, sub-themes, and aspects.
German text preserved with English translations.
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
    'code': '9GN0',
    'name': 'German (listening, reading and writing)',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/German/2016/Specification%20and%20sample%20assessments/Specification_GCE_A_level_L3_in_German.pdf'
}

TOPICS = [
    # Level 0: Papers
    {'code': 'Paper1', 'title': 'Paper 1: Listening, Reading and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper2', 'title': 'Paper 2: Written Response to Works and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper3', 'title': 'Paper 3: Listening, Reading and Writing', 'level': 0, 'parent': None},
    
    # ==================================================================================
    # THEME 1: Gesellschaftliche Entwicklung in Deutschland
    # ==================================================================================
    {'code': 'Theme1', 'title': 'Theme 1: Gesellschaftliche Entwicklung in Deutschland (Social Development in Germany)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 1.1
    {'code': 'T1-1', 'title': 'Natur und Umwelt (Nature and the Environment)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-1-1', 'title': 'Umweltbewusstsein (Environmental awareness)', 'level': 3, 'parent': 'T1-1'},
    {'code': 'T1-1-2', 'title': 'Recycling (Recycling)', 'level': 3, 'parent': 'T1-1'},
    {'code': 'T1-1-3', 'title': 'erneuerbare Energie (renewable energy)', 'level': 3, 'parent': 'T1-1'},
    {'code': 'T1-1-4', 'title': 'nachhaltig leben (sustainable living)', 'level': 3, 'parent': 'T1-1'},
    
    # Sub-theme 1.2
    {'code': 'T1-2', 'title': 'Bildung (Education)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-2-1', 'title': 'Bildungswesen und die Situation von Studenten (The education system and the situation of students)', 'level': 3, 'parent': 'T1-2'},
    {'code': 'T1-2-2', 'title': 'Sitzenbleiben, Berufsausbildung (Repeating a year, vocational training)', 'level': 3, 'parent': 'T1-2'},
    
    # Sub-theme 1.3
    {'code': 'T1-3', 'title': 'Die Welt der Arbeit (The World of Work)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-3-1', 'title': 'Das Arbeitsleben in Deutschland und die Arbeitsmoral (Working life in Germany and work ethic)', 'level': 3, 'parent': 'T1-3'},
    {'code': 'T1-3-2', 'title': 'deutsche Geschäfte und Industrien (German businesses and industries)', 'level': 3, 'parent': 'T1-3'},
    
    # ==================================================================================
    # THEME 2: Politische und künstlerische Kultur im deutschen Sprachraum
    # ==================================================================================
    {'code': 'Theme2', 'title': 'Theme 2: Politische und künstlerische Kultur im deutschen Sprachraum (Political and Artistic Culture in German-speaking Countries)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 2.1
    {'code': 'T2-1', 'title': 'Musik (Music)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-1-1', 'title': 'Wandel und Trends (Change and trends)', 'level': 3, 'parent': 'T2-1'},
    {'code': 'T2-1-2', 'title': 'Einfluss der Musik auf die populäre Kultur (Influence of music on popular culture)', 'level': 3, 'parent': 'T2-1'},
    
    # Sub-theme 2.2
    {'code': 'T2-2', 'title': 'Die Medien (Media)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-2-1', 'title': 'Fernsehen, Digital-, Print- und Onlinemedien (Television, digital, print and online media)', 'level': 3, 'parent': 'T2-2'},
    {'code': 'T2-2-2', 'title': 'Einfluss auf Gesellschaft und Politik (Influence on society and politics)', 'level': 3, 'parent': 'T2-2'},
    
    # Sub-theme 2.3
    {'code': 'T2-3', 'title': 'Die Rolle von Festen und Traditionen (The Role of Festivals and Traditions)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-3-1', 'title': 'Feste, Feiern, Sitten, Traditionen (Festivals, celebrations, customs, traditions)', 'level': 3, 'parent': 'T2-3'},
    
    # ==================================================================================
    # THEME 3: Immigration und die deutsche multikulturelle Gesellschaft
    # ==================================================================================
    {'code': 'Theme3', 'title': 'Theme 3: Immigration und die deutsche multikulturelle Gesellschaft (Immigration and German Multicultural Society)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 3.1
    {'code': 'T3-1', 'title': 'Die positive Auswirkung von Immigration (The Positive Impact of Immigration)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-1-1', 'title': 'Beitrag der Immigranten zur Wirtschaft und Kultur (Contribution of immigrants to the economy and culture)', 'level': 3, 'parent': 'T3-1'},
    
    # Sub-theme 3.2
    {'code': 'T3-2', 'title': 'Die Herausforderungen von Immigration und Integration (The Challenges of Immigration and Integration)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-2-1', 'title': 'Maßnahmen von Gemeinden und örtlichen Gemeinschaften (Measures by municipalities and local communities)', 'level': 3, 'parent': 'T3-2'},
    {'code': 'T3-2-2', 'title': 'Ausgrenzung und Entfremdung aus der Sicht von Immigranten (Exclusion and alienation from the perspective of immigrants)', 'level': 3, 'parent': 'T3-2'},
    
    # Sub-theme 3.3
    {'code': 'T3-3', 'title': 'Die staatliche und soziale Reaktion zur Immigration (State and Social Response to Immigration)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-3-1', 'title': 'Rechtsextremismus (Right-wing extremism)', 'level': 3, 'parent': 'T3-3'},
    {'code': 'T3-3-2', 'title': 'politische Annäherung an Gastarbeiter, Immigranten und Asylbewerber (political approach to guest workers, immigrants and asylum seekers)', 'level': 3, 'parent': 'T3-3'},
    {'code': 'T3-3-3', 'title': 'die öffentliche Meinung (public opinion)', 'level': 3, 'parent': 'T3-3'},
    
    # ==================================================================================
    # THEME 4: Die Wiedervereinigung Deutschlands
    # ==================================================================================
    {'code': 'Theme4', 'title': 'Theme 4: Die Wiedervereinigung Deutschlands (The Reunification of Germany)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 4.1
    {'code': 'T4-1', 'title': 'Die Gesellschaft in der DDR vor der Wiedervereinigung (Society in the GDR Before Reunification)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-1-1', 'title': 'Arbeit (Work)', 'level': 3, 'parent': 'T4-1'},
    {'code': 'T4-1-2', 'title': 'Wohnungswesen (Housing)', 'level': 3, 'parent': 'T4-1'},
    {'code': 'T4-1-3', 'title': 'kommunistische Prinzipien (Communist principles)', 'level': 3, 'parent': 'T4-1'},
    {'code': 'T4-1-4', 'title': 'das Verhältnis zum Westen (relations with the West)', 'level': 3, 'parent': 'T4-1'},
    
    # Sub-theme 4.2
    {'code': 'T4-2', 'title': 'Ereignisse vor der Wiedervereinigung (Events Before Reunification)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-2-1', 'title': 'Der Zusammenbruch des Kommunismus (The collapse of communism)', 'level': 3, 'parent': 'T4-2'},
    {'code': 'T4-2-2', 'title': 'der Fall der Berliner Mauer (the fall of the Berlin Wall)', 'level': 3, 'parent': 'T4-2'},
    
    # Sub-theme 4.3
    {'code': 'T4-3', 'title': 'Deutschland seit der Wiedervereinigung (Germany Since Reunification)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-3-1', 'title': 'Migration von Ost nach West (Migration from East to West)', 'level': 3, 'parent': 'T4-3'},
    {'code': 'T4-3-2', 'title': 'Arbeitslosigkeit in der früheren DDR (Unemployment in the former GDR)', 'level': 3, 'parent': 'T4-3'},
    {'code': 'T4-3-3', 'title': 'Auswirkungen auf Schulen in Deutschland (Impact on schools in Germany)', 'level': 3, 'parent': 'T4-3'},
]


def upload_topics():
    """Upload German topics to Supabase."""
    
    print("=" * 80)
    print("EDEXCEL GERMAN (9GN0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("\nComplete hierarchy with German text + English translations\n")
    
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
        print("[OK] GERMAN TOPICS UPLOADED SUCCESSFULLY!")
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

