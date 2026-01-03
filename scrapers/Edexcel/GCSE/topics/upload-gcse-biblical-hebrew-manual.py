"""
GCSE Biblical Hebrew - Manual Topic Upload
Structure based on examined content:
  Component 1: Language (comprehension, translation, grammar)
  Component 2: Literature (2 set texts with specific chapters)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT = {
    'code': 'GCSE-BiblicalHebrew',
    'name': 'Biblical Hebrew',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/biblical-hebrew/2018/Specification%20and%20Sample%20Assessment%20Material/specification-gcse-l1-l2-in-biblical-hebrew1.pdf'
}

TOPICS = [
    # Level 0: Components
    {'code': 'Component1', 'title': 'Component 1: Language', 'level': 0, 'parent': None},
    {'code': 'Component2', 'title': 'Component 2: Literature', 'level': 0, 'parent': None},
    
    # ==================================================================================
    # COMPONENT 1: LANGUAGE
    # ==================================================================================
    
    # Level 1: Skills tested
    {'code': 'C1-Comprehension', 'title': 'Comprehension of unseen Biblical Hebrew passages', 'level': 1, 'parent': 'Component1'},
    {'code': 'C1-Translation', 'title': 'Translation from Biblical Hebrew to English', 'level': 1, 'parent': 'Component1'},
    {'code': 'C1-Optional', 'title': 'Optional: Grammar OR English to Hebrew translation', 'level': 1, 'parent': 'Component1'},
    
    # Level 2: Vocabulary and Grammar resources
    {'code': 'C1-Vocab', 'title': 'Vocabulary: Words appearing 50+ times in Tanakh (prescribed word list)', 'level': 2, 'parent': 'C1-Translation'},
    {'code': 'C1-VerbForms', 'title': 'Vocabulary: Verbs formed from listed roots', 'level': 2, 'parent': 'C1-Translation'},
    {'code': 'C1-Numbers', 'title': 'Vocabulary: Cardinal numbers 1-100, Ordinal numbers 1-10', 'level': 2, 'parent': 'C1-Translation'},
    
    # Level 2: Grammar (for optional grammar route)
    {'code': 'C1-Morphology', 'title': 'Morphology: Formation of nouns, adjectives, pronouns and verbs', 'level': 2, 'parent': 'C1-Optional'},
    {'code': 'C1-Morphology-1', 'title': 'Noun formation: Gender, number, state (regular and irregular)', 'level': 3, 'parent': 'C1-Morphology'},
    {'code': 'C1-Morphology-2', 'title': 'Verb formation: Weaknesses, persons, numbers, perfect, imperfect, imperatives', 'level': 3, 'parent': 'C1-Morphology'},
    {'code': 'C1-Morphology-3', 'title': 'Verb stems: Qal, niphal, piel, hiphil, hithpael formations', 'level': 3, 'parent': 'C1-Morphology'},
    
    {'code': 'C1-Pointing', 'title': 'Pointing: Syllables, vowels, sheva, dagesh', 'level': 2, 'parent': 'C1-Optional'},
    
    {'code': 'C1-Syntax', 'title': 'Syntax: Clause types and sentence structures', 'level': 2, 'parent': 'C1-Optional'},
    {'code': 'C1-Syntax-1', 'title': 'Clause types: Relative, conditional, temporal, purpose, result, verbless', 'level': 3, 'parent': 'C1-Syntax'},
    
    # ==================================================================================
    # COMPONENT 2: LITERATURE
    # ==================================================================================
    
    # Level 1: Set Texts (2 required)
    {'code': 'C2-SetText1', 'title': 'Set Text 1 (varies by exam year)', 'level': 1, 'parent': 'Component2'},
    {'code': 'C2-SetText2', 'title': 'Set Text 2 (varies by exam year)', 'level': 1, 'parent': 'Component2'},
    
    # Level 2: Set Text 1 Options (exam year dependent)
    {'code': 'C2-T1-2023-25', 'title': 'Judges: Gideon and Abimelech (Chapters 7, 8, 9) - Exams 2023-2025', 'level': 2, 'parent': 'C2-SetText1'},
    {'code': 'C2-T1-2026-28', 'title': 'Genesis: Joseph\'s rise to power (Chapters 41, 42, 43) - Exams 2026-2028', 'level': 2, 'parent': 'C2-SetText1'},
    
    # Level 2: Set Text 2 Options (exam year dependent)
    {'code': 'C2-T2-2023-25', 'title': 'I Kings: The reign of Solomon (Chapters 2, 3, 5) - Exams 2023-2025', 'level': 2, 'parent': 'C2-SetText2'},
    {'code': 'C2-T2-2026-28', 'title': 'II Kings: The miracles of Elisha (Chapters 4, 5, 6, 7) - Exams 2026-2028', 'level': 2, 'parent': 'C2-SetText2'},
    
    # Level 1: Skills assessed in Component 2
    {'code': 'C2-Translation', 'title': 'Translation of set texts into idiomatic English', 'level': 1, 'parent': 'Component2'},
    {'code': 'C2-ContentContext', 'title': 'Content and Context: Background, events, characters, places', 'level': 1, 'parent': 'Component2'},
    {'code': 'C2-GramFeatures', 'title': 'Grammatical Features: Complex forms, derivations, morphology', 'level': 1, 'parent': 'Component2'},
    {'code': 'C2-LitFeatures', 'title': 'Literary Features: Style, word choice, imagery, parallelism, oaths', 'level': 1, 'parent': 'Component2'},
    {'code': 'C2-Analysis', 'title': 'Analysis and Evaluation: Themes, events, relationships, characters', 'level': 1, 'parent': 'Component2'},
]


def upload_topics():
    """Upload Biblical Hebrew topics."""
    
    print("=" * 80)
    print("GCSE BIBLICAL HEBREW - MANUAL UPLOAD")
    print("=" * 80)
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("\n2 Components: Language + Literature (set texts)\n")
    
    try:
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT['name']} (GCSE)",
            'subject_code': SUBJECT['code'],
            'qualification_type': 'GCSE',
            'specification_url': SUBJECT['pdf_url'],
            'exam_board': 'Edexcel'
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared old topics")
        
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'exam_board': 'Edexcel'
        } for t in TOPICS]
        
        inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted.data)} topics")
        
        code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
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
        
        levels = {}
        for t in TOPICS:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("\n" + "=" * 80)
        print("[OK] BIBLICAL HEBREW UPLOADED!")
        print("=" * 80)
        print(f"   Level 0 (Components): {levels.get(0, 0)}")
        print(f"   Level 1 (Skills/Texts): {levels.get(1, 0)}")
        print(f"   Level 2 (Details): {levels.get(2, 0)}")
        print(f"   Level 3 (Grammar): {levels.get(3, 0)}")
        print(f"\n   Total: {len(TOPICS)} topics")
        print("\nFocused on examined content: Language skills + Set texts")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    upload_topics()

