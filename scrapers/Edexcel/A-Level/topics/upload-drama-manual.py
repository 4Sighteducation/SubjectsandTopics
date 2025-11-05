"""
Edexcel Drama and Theatre (9DR0) - Manual Topic Upload
Unique structure: Components, Prescribed Texts, and Theatre Practitioners

Structure:
- Level 0: Component 2 and 3 (Component 1 is non-examined)
- Level 1: Text Lists (A and B) and Practitioners
- Level 2: Individual texts and practitioners
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT = {
    'code': '9DR0',
    'name': 'Drama and Theatre',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Drama-and-Theatre/2016/Specification%20and%20sample%20assessments/a-level-drama-spec.pdf'
}

# Structured topic data
TOPICS = [
    # Level 0: Examined Components
    {
        'code': 'Component2',
        'title': 'Component 2: Text in Performance',
        'level': 0,
        'parent': None
    },
    {
        'code': 'Component3',
        'title': 'Component 3: Theatre Makers in Practice (Written Exam)',
        'level': 0,
        'parent': None
    },
    
    # ========================================
    # COMPONENT 3: Performance Texts
    # ========================================
    
    # Level 1: Text Lists (under Component 2 - where students perform them)
    {
        'code': 'TextListA',
        'title': 'Prescribed Texts - List A',
        'level': 1,
        'parent': 'Component2'
    },
    {
        'code': 'TextListB',
        'title': 'Prescribed Texts - List B',
        'level': 1,
        'parent': 'Component2'
    },
    
    # Level 2: List A Texts
    {
        'code': 'Text.A1',
        'title': 'Accidental Death Of An Anarchist - Dario Fo (adapted by Gavin Richards)',
        'level': 2,
        'parent': 'TextListA'
    },
    {
        'code': 'Text.A2',
        'title': 'Colder Than Here - Laura Wade',
        'level': 2,
        'parent': 'TextListA'
    },
    {
        'code': 'Text.A3',
        'title': 'Equus - Peter Shaffer',
        'level': 2,
        'parent': 'TextListA'
    },
    {
        'code': 'Text.A4',
        'title': 'Fences - August Wilson',
        'level': 2,
        'parent': 'TextListA'
    },
    {
        'code': 'Text.A5',
        'title': 'Machinal - Sophie Treadwell',
        'level': 2,
        'parent': 'TextListA'
    },
    {
        'code': 'Text.A6',
        'title': 'That Face - Polly Stenham',
        'level': 2,
        'parent': 'TextListA'
    },
    
    # Level 2: List B Texts
    {
        'code': 'Text.B1',
        'title': 'Antigone - Sophocles (adapted by Don Taylor)',
        'level': 2,
        'parent': 'TextListB'
    },
    {
        'code': 'Text.B2',
        'title': 'Doctor Faustus - Christopher Marlowe (Text A only)',
        'level': 2,
        'parent': 'TextListB'
    },
    {
        'code': 'Text.B3',
        'title': 'Hedda Gabler - Henrik Ibsen (adapted by Richard Eyre)',
        'level': 2,
        'parent': 'TextListB'
    },
    {
        'code': 'Text.B4',
        'title': 'Lysistrata - Aristophanes (translated by Alan H. Sommerstein)',
        'level': 2,
        'parent': 'TextListB'
    },
    {
        'code': 'Text.B5',
        'title': 'The Maids - Jean Genet (translated by Bernard Frechtman)',
        'level': 2,
        'parent': 'TextListB'
    },
    {
        'code': 'Text.B6',
        'title': 'The School for Scandal - Richard Brinsley Sheridan',
        'level': 2,
        'parent': 'TextListB'
    },
    {
        'code': 'Text.B7',
        'title': 'The Tempest - William Shakespeare',
        'level': 2,
        'parent': 'TextListB'
    },
    {
        'code': 'Text.B8',
        'title': 'Waiting for Godot - Samuel Beckett',
        'level': 2,
        'parent': 'TextListB'
    },
    {
        'code': 'Text.B9',
        'title': 'Woyzeck - Georg Büchner (translated by John Mackendrick)',
        'level': 2,
        'parent': 'TextListB'
    },
    
    # ========================================
    # COMPONENT 3: Theatre Practitioners
    # ========================================
    
    # Level 1: Practitioners List
    {
        'code': 'Practitioners',
        'title': 'Theatre Practitioners (Component 3)',
        'level': 1,
        'parent': 'Component3'
    },
    
    # Level 2: Individual Practitioners
    {
        'code': 'Prac.1',
        'title': 'Antonin Artaud',
        'level': 2,
        'parent': 'Practitioners'
    },
    {
        'code': 'Prac.2',
        'title': 'Bertolt Brecht',
        'level': 2,
        'parent': 'Practitioners'
    },
    {
        'code': 'Prac.3',
        'title': 'Steven Berkoff',
        'level': 2,
        'parent': 'Practitioners'
    },
    {
        'code': 'Prac.4',
        'title': 'Complicite (Theatre Company)',
        'level': 2,
        'parent': 'Practitioners'
    },
    {
        'code': 'Prac.5',
        'title': 'Constantin Stanislavski',
        'level': 2,
        'parent': 'Practitioners'
    },
    {
        'code': 'Prac.6',
        'title': 'Kneehigh (Theatre Company)',
        'level': 2,
        'parent': 'Practitioners'
    },
    {
        'code': 'Prac.7',
        'title': 'Joan Littlewood',
        'level': 2,
        'parent': 'Practitioners'
    },
    {
        'code': 'Prac.8',
        'title': 'Punchdrunk (Theatre Company)',
        'level': 2,
        'parent': 'Practitioners'
    },
    
    # ========================================
    # COMPONENT 3: Exam Structure/Skills
    # ========================================
    
    # Level 1: Exam Sections
    {
        'code': 'Exam.SectionA',
        'title': 'Section A: Live Theatre Evaluation',
        'level': 1,
        'parent': 'Component3'
    },
    {
        'code': 'Exam.SectionB',
        'title': 'Section B: Page to Stage - Realising a Performance Text',
        'level': 1,
        'parent': 'Component3'
    },
    {
        'code': 'Exam.SectionC',
        'title': 'Section C: Interpreting a Performance Text',
        'level': 1,
        'parent': 'Component3'
    },
    
    # Level 2: Skills for each section
    {
        'code': 'Exam.A.Skill',
        'title': 'Analyse and evaluate live theatre performance (500 word notes allowed)',
        'level': 2,
        'parent': 'Exam.SectionA'
    },
    {
        'code': 'Exam.B.Skill1',
        'title': 'Demonstrate how to realise extract as performer',
        'level': 2,
        'parent': 'Exam.SectionB'
    },
    {
        'code': 'Exam.B.Skill2',
        'title': 'Demonstrate how to realise extract as designer',
        'level': 2,
        'parent': 'Exam.SectionB'
    },
    {
        'code': 'Exam.C.Skill1',
        'title': 'Re-imagined production concept for contemporary audience',
        'level': 2,
        'parent': 'Exam.SectionC'
    },
    {
        'code': 'Exam.C.Skill2',
        'title': 'Apply practitioner influence to production concept',
        'level': 2,
        'parent': 'Exam.SectionC'
    }
]


def upload_drama_topics():
    """Upload Drama and Theatre topics to Supabase."""
    
    print("=" * 80)
    print("EDEXCEL DRAMA AND THEATRE (9DR0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("\nPrescribed texts and theatre practitioners\n")
    
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
        
        # Insert new topics
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
        print("[OK] DRAMA AND THEATRE TOPICS UPLOADED SUCCESSFULLY!")
        print("=" * 80)
        
        # Show hierarchy breakdown
        levels = {}
        for t in TOPICS:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("\nHierarchy:")
        print(f"   Level 0 (Components): {levels.get(0, 0)}")
        print(f"   Level 1 (Categories): {levels.get(1, 0)}")
        print(f"   Level 2 (Texts/Practitioners/Skills): {levels.get(2, 0)}")
        print(f"\n   Total: {len(TOPICS)} topics")
        
        # Show sample
        print("\nSample content:")
        print("   Prescribed Texts:")
        print("     List A: Accidental Death Of An Anarchist, Equus, Fences...")
        print("     List B: Antigone, Doctor Faustus, The Tempest, Waiting for Godot...")
        print("   Theatre Practitioners:")
        print("     Antonin Artaud, Bertolt Brecht, Stanislavski, Kneehigh...")
        
        print("\n" + "=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Force UTF-8 output
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    success = upload_drama_topics()
    sys.exit(0 if success else 1)

