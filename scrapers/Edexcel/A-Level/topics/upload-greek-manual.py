"""
Edexcel Greek (9GK0) - Manual Topic Upload
Complete hierarchy with themes, sub-themes, research topics, and aspects.
Greek text preserved with English translations.
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
    'code': '9GK0',
    'name': 'Greek (listening, reading and writing)',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Greek/2018/specification/A-level-Greek-specification.pdf'
}

TOPICS = [
    # Level 0: Papers
    {'code': 'Paper1', 'title': 'Paper 1: Translation into English, Reading Comprehension and Writing', 'level': 0, 'parent': None},
    {'code': 'Paper2', 'title': 'Paper 2: Translation into Greek and Written Response to Works', 'level': 0, 'parent': None},
    {'code': 'Paper3', 'title': 'Paper 3: Listening, Reading and Writing in Greek', 'level': 0, 'parent': None},
    
    # ==================================================================================
    # THEME 1: Αλλαγές στην ελληνική κοινωνία (Changes in Greek Society)
    # ==================================================================================
    {'code': 'Theme1', 'title': 'Πρώτο Θέμα: Αλλαγές στην ελληνική κοινωνία (Theme 1: Changes in Greek Society)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 1.1
    {'code': 'T1-1', 'title': 'Σχέσεις και Οικογένεια (Relationships and Family)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-1-1', 'title': 'η εξέλιξη του μοντέλου της πυρηνικής οικογένειας (the evolution of the nuclear family model)', 'level': 3, 'parent': 'T1-1'},
    {'code': 'T1-1-2', 'title': 'οι έμφυλοι ρόλοι (gender roles)', 'level': 3, 'parent': 'T1-1'},
    {'code': 'T1-1-3', 'title': 'οι σχέσεις με τους μεγαλύτερους και τους συνομήλικους (relationships with older people and peers)', 'level': 3, 'parent': 'T1-1'},
    
    # Sub-theme 1.2
    {'code': 'T1-2', 'title': 'Ο χώρος της εργασίας (The Workplace)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-2-1', 'title': 'οι εξελίξεις στον τομέα της απασχόλησης στην Ελλάδα (developments in the field of employment in Greece)', 'level': 3, 'parent': 'T1-2'},
    {'code': 'T1-2-2', 'title': 'ανεργία (unemployment)', 'level': 3, 'parent': 'T1-2'},
    {'code': 'T1-2-3', 'title': 'οι φοιτητές στην αγορά εργασίας (students in the job market)', 'level': 3, 'parent': 'T1-2'},
    
    # Research Topic 1
    {'code': 'T1-R', 'title': 'Ερευνητικό θέμα: Η Παιδεία στην Ελλάδα (Research: Education in Greece)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-R-1', 'title': 'εξελίξεις στο εκπαιδευτικό σύστημα (developments in the education system)', 'level': 3, 'parent': 'T1-R'},
    {'code': 'T1-R-2', 'title': 'το γλωσσικό ζήτημα (the language question)', 'level': 3, 'parent': 'T1-R'},
    {'code': 'T1-R-3', 'title': 'αλλαγές στη διδακτέα ύλη (changes in the curriculum)', 'level': 3, 'parent': 'T1-R'},
    
    # ==================================================================================
    # THEME 2: Τέχνη και πνευματικός πολιτισμός στην Ελλάδα
    # ==================================================================================
    {'code': 'Theme2', 'title': 'Δεύτερο Θέμα: Τέχνη και πνευματικός πολιτισμός στην Ελλάδα (Theme 2: Art and Artistic Culture in Greece)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 2.1
    {'code': 'T2-1', 'title': 'Σύγχρονος πνευματικός πολιτισμός και μέσα επικοινωνίας (Contemporary Cultural Life and Media)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-1-1', 'title': 'δημοφιλή μέσα επικοινωνίας (popular media)', 'level': 3, 'parent': 'T2-1'},
    {'code': 'T2-1-2', 'title': 'κινηματογράφος και τηλεόραση (cinema and television)', 'level': 3, 'parent': 'T2-1'},
    {'code': 'T2-1-3', 'title': 'η επιρροή της τεχνολογίας στις κοινωνικές πρακτικές και στον πνευματικό πολιτισμό (the influence of technology on social practices and cultural life)', 'level': 3, 'parent': 'T2-1'},
    
    # Sub-theme 2.2
    {'code': 'T2-2', 'title': 'Παράδοση, ήθη και έθιμα (Tradition, Customs and Beliefs)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-2-1', 'title': 'τοπικές γιορτές (local festivals)', 'level': 3, 'parent': 'T2-2'},
    {'code': 'T2-2-2', 'title': 'παραδοσιακοί τρόποι αναψυχής και ψυχαγωγίας (traditional ways of recreation and entertainment)', 'level': 3, 'parent': 'T2-2'},
    {'code': 'T2-2-3', 'title': 'απόψεις σχετικά με την παράδοση και τα πιστεύω (views on tradition and beliefs)', 'level': 3, 'parent': 'T2-2'},
    
    # Research Topic 2
    {'code': 'T2-R', 'title': 'Ερευνητικό θέμα: Το ρεμπέτικο (Research: Rebetiko Music)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-R-1', 'title': 'το ιστορικό πλαίσιο (the historical context)', 'level': 3, 'parent': 'T2-R'},
    {'code': 'T2-R-2', 'title': 'θεματολογία και πολιτιστικά συμφραζόμενα (themes and cultural contexts)', 'level': 3, 'parent': 'T2-R'},
    {'code': 'T2-R-3', 'title': 'διάσημοι καλλιτέχνες του ρεμπέτικου (famous rebetiko artists)', 'level': 3, 'parent': 'T2-R'},
    
    # ==================================================================================
    # THEME 3: Όψεις της Κύπρου (Aspects of Cyprus)
    # ==================================================================================
    {'code': 'Theme3', 'title': 'Τρίτο θέμα: Όψεις της Κύπρου (Theme 3: Aspects of Cyprus)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 3.1
    {'code': 'T3-1', 'title': 'Ανθρωπογεωγραφία (Human Geography)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-1-1', 'title': 'αλλαγές σχετικά με το βιοτικό επίπεδο και την ποιότητα ζωής (changes in living standards and quality of life)', 'level': 3, 'parent': 'T3-1'},
    {'code': 'T3-1-2', 'title': 'διαχωρισμός μεταξύ αστικού και αγροτικού περιβάλλοντος (division between urban and rural environments)', 'level': 3, 'parent': 'T3-1'},
    {'code': 'T3-1-3', 'title': 'τουρισμός (tourism)', 'level': 3, 'parent': 'T3-1'},
    
    # Sub-theme 3.2
    {'code': 'T3-2', 'title': 'Φυσική γεωγραφία (Physical Geography)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-2-1', 'title': 'το περιβάλλον (the environment)', 'level': 3, 'parent': 'T3-2'},
    {'code': 'T3-2-2', 'title': 'αλλαγές στις αντιλήψεις σχετικά με την προστασία του περιβάλλοντος (changes in attitudes towards environmental protection)', 'level': 3, 'parent': 'T3-2'},
    {'code': 'T3-2-3', 'title': 'επιπτώσεις της βιομηχανοποίησης στην κοινωνία και στο περιβάλλον (impact of industrialization on society and the environment)', 'level': 3, 'parent': 'T3-2'},
    
    # Research Topic 3
    {'code': 'T3-R', 'title': 'Ερευνητικό θέμα: Ιστορία της Κύπρου 1974-1983 (Research: History of Cyprus 1974-1983)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-R-1', 'title': 'Ιούλιος 1974 (July 1974)', 'level': 3, 'parent': 'T3-R'},
    {'code': 'T3-R-2', 'title': 'οι επιπτώσεις των γεγονότων του 1974 στην κοινωνία της Κύπρου (the impact of the 1974 events on Cypriot society)', 'level': 3, 'parent': 'T3-R'},
    {'code': 'T3-R-3', 'title': 'σημαντικές προσωπικότητες της περιόδου (important figures of the period)', 'level': 3, 'parent': 'T3-R'},
    
    # ==================================================================================
    # THEME 4: Νέες εξελίξεις στο πολιτικό και οικονομικό πεδίο
    # ==================================================================================
    {'code': 'Theme4', 'title': 'Τέταρτο θέμα: Νέες εξελίξεις στο πολιτικό και οικονομικό πεδίο (Theme 4: New Developments in Politics and Economics)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 4.1
    {'code': 'T4-1', 'title': 'Η οικονομία από το 2009 και μετά (The Economy from 2009 Onwards)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-1-1', 'title': 'οι αιτίες και οι επιπτώσεις της κρίσης (the causes and effects of the crisis)', 'level': 3, 'parent': 'T4-1'},
    {'code': 'T4-1-2', 'title': 'ο ρόλος της Ευρωπαϊκής Ένωσης (the role of the European Union)', 'level': 3, 'parent': 'T4-1'},
    {'code': 'T4-1-3', 'title': 'κοινωνικές διαμάχες και αναταραχές (social conflicts and unrest)', 'level': 3, 'parent': 'T4-1'},
    
    # Sub-theme 4.2
    {'code': 'T4-2', 'title': 'Η πολιτική σκηνή (The Political Scene)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-2-1', 'title': 'τα κύρια πολιτικά κόμματα (the main political parties)', 'level': 3, 'parent': 'T4-2'},
    {'code': 'T4-2-2', 'title': 'τα πολιτικά τους προγράμματα και οι σημαντικές προσωπικότητες από το 2009 και μετά (their political programs and important figures from 2009 onwards)', 'level': 3, 'parent': 'T4-2'},
    {'code': 'T4-2-3', 'title': 'το δημοψήφισμα της 5ης Ιουλίου 2015 (the referendum of July 5, 2015)', 'level': 3, 'parent': 'T4-2'},
    
    # Research Topic 4
    {'code': 'T4-R', 'title': 'Ερευνητικό θέμα: Πρόσφυγες στην Ελλάδα (Research: Refugees in Greece)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-R-1', 'title': 'πρόσφυγες στην Ελλάδα από το 2015 και μετά (refugees in Greece from 2015 onwards)', 'level': 3, 'parent': 'T4-R'},
    {'code': 'T4-R-2', 'title': 'η ένταξη των προσφύγων στην ελληνική κοινωνία (the integration of refugees into Greek society)', 'level': 3, 'parent': 'T4-R'},
    {'code': 'T4-R-3', 'title': 'το έργο των Μη Κυβερνητικών Οργανώσεων (ΜΚΟ) (the work of Non-Governmental Organizations (NGOs))', 'level': 3, 'parent': 'T4-R'},
]


def upload_topics():
    """Upload Greek topics to Supabase."""
    
    print("=" * 80)
    print("EDEXCEL GREEK (9GK0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("\nComplete hierarchy with Greek text + English translations\n")
    
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
        print("[OK] GREEK TOPICS UPLOADED SUCCESSFULLY!")
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

