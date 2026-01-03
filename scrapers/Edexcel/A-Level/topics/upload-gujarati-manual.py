"""
Edexcel Gujarati (9GU0) - Manual Topic Upload
Complete hierarchy with themes, sub-themes, and aspects.
Gujarati text preserved with English translations.
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
    'code': '9GU0',
    'name': 'Gujarati (listening, reading and writing)',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Gujarati/2018/specification-and-sample-assessments/A-level-Gujarati-Specification.pdf'
}

TOPICS = [
    # Level 0: Papers
    {'code': 'Paper1', 'title': 'Paper 1: Listening, Reading and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper2', 'title': 'Paper 2: Written Response to Works and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper3', 'title': 'Paper 3: Listening, Reading and Writing', 'level': 0, 'parent': None},
    
    # ==================================================================================
    # THEME 1: ગુજરાતી સમાજમાં પરિવર્તન (Changes in Gujarati Society)
    # ==================================================================================
    {'code': 'Theme1', 'title': 'મુખ્ય વિષય ૧: ગુજરાતી સમાજમાં પરિવર્તન (Theme 1: Changes in Gujarati Society)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 1.1
    {'code': 'T1-1', 'title': 'બદલાતાં પારિવારિક માળખાં (Changing Family Structures)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-1-1', 'title': 'લગ્ન, સંબંધો તથા પરિવાર પ્રત્યે ભૂત તથા બદલાતો દૃષ્ટિકોણ (changing attitudes towards marriage, relationships and family)', 'level': 3, 'parent': 'T1-1'},
    {'code': 'T1-1-2', 'title': 'અપારંપરિક સંબંધો (non-traditional relationships)', 'level': 3, 'parent': 'T1-1'},
    {'code': 'T1-1-3', 'title': 'પરિવારમાં પેઢીઓ વચ્ચે ટકર (generational conflicts in families)', 'level': 3, 'parent': 'T1-1'},
    
    # Sub-theme 1.2
    {'code': 'T1-2', 'title': 'કામની દુનિયા (The World of Work)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-2-1', 'title': 'વ્યવસાયો તરફ પરંપરાગત અને આધુનિક અભિગમ (traditional and modern approaches to professions)', 'level': 3, 'parent': 'T1-2'},
    {'code': 'T1-2-2', 'title': 'યુવાનો માટે રોજગારની તકો (employment opportunities for young people)', 'level': 3, 'parent': 'T1-2'},
    {'code': 'T1-2-3', 'title': 'બેરોજગારી (બેકારી)ના કારણો અને પરિણામો (causes and consequences of unemployment)', 'level': 3, 'parent': 'T1-2'},
    
    # Research Topic 1
    {'code': 'T1-R', 'title': 'સંશોધન માટેનો વિષય: સમાજમાં મહિલાઓનું સ્થાન (Research: The Place of Women in Society)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-R-1', 'title': 'મહિલાઓની સામાજિક પ્રતિષ્ઠાનો વિકાસ કરવો (developing the social status of women)', 'level': 3, 'parent': 'T1-R'},
    {'code': 'T1-R-2', 'title': 'કેળવણી (ભણતર) માટે પ્રવેશમાર્ગ (access to education)', 'level': 3, 'parent': 'T1-R'},
    {'code': 'T1-R-3', 'title': 'ગુજરાતી સ્ત્રીઓએ મેળવેલી સિદ્ધિઓ અને સમાજમાં તેઓનું યોગદાન (achievements of Gujarati women and their contribution to society)', 'level': 3, 'parent': 'T1-R'},
    
    # ==================================================================================
    # THEME 2: માધ્યમ અને સંસ્કૃતિ (Media and Culture)
    # ==================================================================================
    {'code': 'Theme2', 'title': 'મુખ્ય વિષય ૨: માધ્યમ અને સંસ્કૃતિ (Theme 2: Media and Culture)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 2.1
    {'code': 'T2-1', 'title': 'માધ્યમ (Media)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-1-1', 'title': 'યુવાનોનાં જીવન પર ઇન્ટરનેટની અસર (impact of the internet on young people\'s lives)', 'level': 3, 'parent': 'T2-1'},
    {'code': 'T2-1-2', 'title': 'ઇન્ટરનેટ પર મળતી માહિતીની આધારભૂતતા (reliability of information available on the internet)', 'level': 3, 'parent': 'T2-1'},
    {'code': 'T2-1-3', 'title': 'વર્તમાનપત્રોની રાજકારણ પર અસર (impact of newspapers on politics)', 'level': 3, 'parent': 'T2-1'},
    
    # Sub-theme 2.2
    {'code': 'T2-2', 'title': 'લોકપ્રિય સંસ્કૃતિમાં બદલાવ (Changes in Popular Culture)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-2-1', 'title': 'તહેવારો, ઉજવણીઓ (festivals, celebrations)', 'level': 3, 'parent': 'T2-2'},
    {'code': 'T2-2-2', 'title': 'ગુજરાતી ફિલ્મ સંગીત (Gujarati film music)', 'level': 3, 'parent': 'T2-2'},
    
    # Research Topic 2
    {'code': 'T2-R', 'title': 'સંશોધન માટેનો વિષય: ભારતીય સમાજ પર મહાત્મા ગાંધીનો પ્રભાવ (Research: The Influence of Mahatma Gandhi on Indian Society)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-R-1', 'title': 'વિચારસરણી અને દૃષ્ટિકોણ ઉપર મહાત્મા ગાંધીની અસર (Mahatma Gandhi\'s impact on thoughts and perspectives)', 'level': 3, 'parent': 'T2-R'},
    {'code': 'T2-R-2', 'title': 'જીવનશૈલી ઉપર તેમનો પ્રભાવ (his influence on lifestyle)', 'level': 3, 'parent': 'T2-R'},
    {'code': 'T2-R-3', 'title': 'મહાત્મા ગાંધીનો વારસો (Mahatma Gandhi\'s legacy)', 'level': 3, 'parent': 'T2-R'},
    
    # ==================================================================================
    # THEME 3: તત્કાલીન ગુજરાતી સમાજના વિવિધ પાસાં
    # ==================================================================================
    {'code': 'Theme3', 'title': 'મુખ્ય વિષય ૩: તત્કાલીન ગુજરાતી સમાજના વિવિધ પાસાં (Theme 3: Various Aspects of Contemporary Gujarati Society)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 3.1
    {'code': 'T3-1', 'title': 'આંતરિક સ્થળાંતર (Internal Migration)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-1-1', 'title': 'ગ્રામીણ વિરુદ્ધ શહેરી સાંસ્કૃતિક વિભાજન (rural vs urban cultural division)', 'level': 3, 'parent': 'T3-1'},
    {'code': 'T3-1-2', 'title': 'તાલીમ પામેલા વિરુદ્ધ તાલીમ ન પામેલા કામદારો (trained vs untrained workers)', 'level': 3, 'parent': 'T3-1'},
    {'code': 'T3-1-3', 'title': 'સ્થળાંતર કરનાર લોકોને બધાંથી સાવ અલગ પાડી દેવા (segregation of migrants from all)', 'level': 3, 'parent': 'T3-1'},
    
    # Sub-theme 3.2
    {'code': 'T3-2', 'title': 'જીવો તથા તેમની આસપાસની પરિસ્થિતિનું વિજ્ઞાન (Science of Living Beings and Their Environment)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-2-1', 'title': 'પર્યાવરણની સમસ્યાઓ તરફ બદલાયું વલણ (changing attitudes towards environmental problems)', 'level': 3, 'parent': 'T3-2'},
    {'code': 'T3-2-2', 'title': 'કુદરતી સંપત્તિનું રક્ષણ (protection of natural resources)', 'level': 3, 'parent': 'T3-2'},
    {'code': 'T3-2-3', 'title': 'પર્યાવરણ ઉપર ઉદ્યોગીકરણ અને શહેરીકરણની અસર (impact of industrialization and urbanization on the environment)', 'level': 3, 'parent': 'T3-2'},
    
    # Research Topic 3
    {'code': 'T3-R', 'title': 'સંશોધન માટેનો વિષય: પ્રવાસન (Research: Tourism)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-R-1', 'title': 'વૈદ્યકીય પ્રવાસન (medical tourism)', 'level': 3, 'parent': 'T3-R'},
    {'code': 'T3-R-2', 'title': 'રાજ્ય પ્રવર્તક પ્રવાસન (state-promoted tourism)', 'level': 3, 'parent': 'T3-R'},
    {'code': 'T3-R-3', 'title': 'પ્રવાસનના આર્થિક ફાયદાઓ તથા ગેરફાયદાઓ (economic advantages and disadvantages of tourism)', 'level': 3, 'parent': 'T3-R'},
    
    # ==================================================================================
    # THEME 4: ગુજરાતના રાજકીય પાસાં (Political Aspects of Gujarat)
    # ==================================================================================
    {'code': 'Theme4', 'title': 'મુખ્ય વિષય ૪: ગુજરાતના રાજકીય પાસાં (Theme 4: Political Aspects of Gujarat)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 4.1
    {'code': 'T4-1', 'title': 'ગુજરાત રાજ્ય – તકોની ભૂમિ (Gujarat State - Land of Opportunities)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-1-1', 'title': 'કાપડ ઉદ્યોગનો વિકાસ (development of the textile industry)', 'level': 3, 'parent': 'T4-1'},
    {'code': 'T4-1-2', 'title': 'પ્રચલિત ગુજરાતી ઉત્પાદનોની નિકાસ (export of popular Gujarati products)', 'level': 3, 'parent': 'T4-1'},
    {'code': 'T4-1-3', 'title': 'વાહનવ્યવહારના માળખામાં રોકાણ (investment in transport infrastructure)', 'level': 3, 'parent': 'T4-1'},
    
    # Sub-theme 4.2
    {'code': 'T4-2', 'title': 'ગુજરાત રાજ્યનાં રાજકીય પાસાં (Political Aspects of Gujarat State)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-2-1', 'title': 'ગુજરાતના વિકાસ માટે સરકારની પહેલકૃતિ (government initiatives for Gujarat\'s development)', 'level': 3, 'parent': 'T4-2'},
    {'code': 'T4-2-2', 'title': 'રાજકીય નેતૃત્વનાં નવાં રૂપો (new forms of political leadership)', 'level': 3, 'parent': 'T4-2'},
    {'code': 'T4-2-3', 'title': 'રાજકારણમાં યુવાનોની ભૂમિકા (the role of young people in politics)', 'level': 3, 'parent': 'T4-2'},
    
    # Research Topic 4
    {'code': 'T4-R', 'title': 'સંશોધન માટેનો વિષય: ગુજરાત રાજ્યમાં કાયદો અને વ્યવસ્થા (Research: Law and Order in Gujarat State)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-R-1', 'title': 'ગુજરાત રાજ્યમાં કાયદો અને વ્યવસ્થામાં સુધારાઓ અને પડકારો (improvements and challenges in law and order in Gujarat)', 'level': 3, 'parent': 'T4-R'},
    {'code': 'T4-R-2', 'title': 'વેપાર ઉદ્યોગો માટે કાયદો અને વ્યવસ્થાનું મહત્વ (importance of law and order for business industries)', 'level': 3, 'parent': 'T4-R'},
    {'code': 'T4-R-3', 'title': 'કાયદામાં થતાં ફેરફારો સ્ત્રીઓને કેવી રીતે અસર કરે છે (how changes in law affect women)', 'level': 3, 'parent': 'T4-R'},
]


def upload_topics():
    """Upload Gujarati topics to Supabase."""
    
    print("=" * 80)
    print("EDEXCEL GUJARATI (9GU0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("\nComplete hierarchy with Gujarati text + English translations\n")
    
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
        print("[OK] GUJARATI TOPICS UPLOADED SUCCESSFULLY!")
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

