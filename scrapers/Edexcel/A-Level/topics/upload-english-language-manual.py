"""
Edexcel English Language (9EN0) - Manual Topic Upload
Focus: Language frameworks and key concepts for flashcard revision
"""

import os, sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT = {
    'code': '9EN0',
    'name': 'English Language',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/English%20Language/2015/Specification%20and%20sample%20assessment/AS-EnglishLanguage-Spec.pdf'
}

TOPICS = [
    # Level 0: Components (examined only)
    {'code': 'Comp1', 'title': 'Component 1: Language Variation', 'level': 0, 'parent': None},
    {'code': 'Comp2', 'title': 'Component 2: Child Language', 'level': 0, 'parent': None},
    {'code': 'Comp3', 'title': 'Component 3: Investigating Language', 'level': 0, 'parent': None},
    
    # Component 1: Language Variation
    {'code': 'Comp1.Mode', 'title': 'Mode: Method of communication (spoken, written, multimodal)', 'level': 1, 'parent': 'Comp1'},
    {'code': 'Comp1.Field', 'title': 'Field: Subject matter', 'level': 1, 'parent': 'Comp1'},
    {'code': 'Comp1.Function', 'title': 'Function: Purpose of language use', 'level': 1, 'parent': 'Comp1'},
    {'code': 'Comp1.Audience', 'title': 'Audience: Relationship between users', 'level': 1, 'parent': 'Comp1'},
    
    # Language Frameworks (Level 1)
    {'code': 'Framework.Pragmatics', 'title': 'Pragmatics: Variation in meaning depending on context', 'level': 1, 'parent': 'Comp1'},
    {'code': 'Framework.Discourse', 'title': 'Discourse: Extended texts in context', 'level': 1, 'parent': 'Comp1'},
    {'code': 'Framework.Graphology', 'title': 'Graphology: Writing system and presentation', 'level': 1, 'parent': 'Comp1'},
    {'code': 'Framework.Phonetics', 'title': 'Phonetics/Phonology/Prosody: Speech sounds and intonation', 'level': 1, 'parent': 'Comp1'},
    {'code': 'Framework.Morphology', 'title': 'Morphology: Structure of words', 'level': 1, 'parent': 'Comp1'},
    {'code': 'Framework.Lexis', 'title': 'Lexis and Semantics: Vocabulary and meanings', 'level': 1, 'parent': 'Comp1'},
    {'code': 'Framework.Syntax', 'title': 'Syntax: Relationships between words in sentences', 'level': 1, 'parent': 'Comp1'},
    
    # Individual Variation (Level 1)
    {'code': 'Variation.Individual', 'title': 'Individual Variation: Language and identity', 'level': 1, 'parent': 'Comp1'},
    {'code': 'Variation.Geographical', 'title': 'Geographical factors in language variation', 'level': 2, 'parent': 'Variation.Individual'},
    {'code': 'Variation.Social', 'title': 'Social factors (gender, age, ethnicity)', 'level': 2, 'parent': 'Variation.Individual'},
    
    # Variation Over Time (Level 1)
    {'code': 'Variation.Time', 'title': 'Variation Over Time: English c1550-present', 'level': 1, 'parent': 'Comp1'},
    {'code': 'Variation.EarlyModern', 'title': 'Early Modern English (c1550-1700)', 'level': 2, 'parent': 'Variation.Time'},
    {'code': 'Variation.Modern', 'title': 'Late Modern English (1700-present)', 'level': 2, 'parent': 'Variation.Time'},
    {'code': 'Variation.Contemporary', 'title': 'Contemporary English (21st century)', 'level': 2, 'parent': 'Variation.Time'},
    
    # Component 2: Child Language
    {'code': 'Child.Spoken', 'title': 'Spoken language acquisition (ages 0-8)', 'level': 1, 'parent': 'Comp2'},
    {'code': 'Child.Writing', 'title': 'Learning to write (ages 0-8)', 'level': 1, 'parent': 'Comp2'},
    {'code': 'Child.Reading', 'title': 'Beginning of reading skills', 'level': 1, 'parent': 'Comp2'},
    {'code': 'Child.Theories', 'title': 'Theories of child language development', 'level': 1, 'parent': 'Comp2'},
    
    # Component 3: Investigating Language
    {'code': 'Invest.Topics', 'title': 'Research Topic Areas (5 areas)', 'level': 1, 'parent': 'Comp3'},
    {'code': 'Invest.Methods', 'title': 'Research and investigation methods', 'level': 1, 'parent': 'Comp3'},
    {'code': 'Invest.Analysis', 'title': 'Data analysis techniques', 'level': 1, 'parent': 'Comp3'}
]

print("=" * 80)
print("EDEXCEL ENGLISH LANGUAGE (9EN0) - MANUAL UPLOAD")
print("=" * 80)
print(f"\nFocus: Language frameworks and concepts for flashcard revision")
print(f"Topics: {len(TOPICS)}\n")

try:
    subject_result = supabase.table('staging_aqa_subjects').upsert({
        'subject_name': f"{SUBJECT['name']} (A-Level)",
        'subject_code': SUBJECT['code'],
        'qualification_type': 'A-Level',
        'specification_url': SUBJECT['pdf_url'],
        'exam_board': 'Edexcel'
    }, on_conflict='subject_code,qualification_type,exam_board').execute()
    
    subject_id = subject_result.data[0]['id']
    print(f"[OK] Subject ID: {subject_id}")
    
    supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
    print("[OK] Cleared old topics")
    
    to_insert = [{'subject_id': subject_id, 'topic_code': t['code'], 'topic_name': t['title'], 'topic_level': t['level'], 'exam_board': 'Edexcel'} for t in TOPICS]
    
    inserted_result = supabase.table('staging_aqa_topics').insert(to_insert).execute()
    print(f"[OK] Uploaded {len(inserted_result.data)} topics")
    
    code_to_id = {t['topic_code']: t['id'] for t in inserted_result.data}
    linked = 0
    
    for topic in TOPICS:
        if topic['parent']:
            parent_id = code_to_id.get(topic['parent'])
            child_id = code_to_id.get(topic['code'])
            if parent_id and child_id:
                supabase.table('staging_aqa_topics').update({'parent_topic_id': parent_id}).eq('id', child_id).execute()
                linked += 1
    
    print(f"[OK] Linked {linked} relationships")
    print("\n" + "=" * 80)
    print("[OK] ENGLISH LANGUAGE COMPLETE!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n[ERROR] Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
