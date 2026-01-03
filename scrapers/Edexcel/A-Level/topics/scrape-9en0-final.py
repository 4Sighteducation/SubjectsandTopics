"""
Edexcel English Language (9EN0) - Manual Topic Upload
Skill-based subject with 2 examined components (Component 3 is NEA - skip)
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
    'code': '9EN0',
    'name': 'English Language',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/English%20Language/2015/Specification%20and%20sample%20assessment/Pearson_Edexcel_Level_3_GCE_in_English_Language_Specification_issue6.pdf'
}

def create_topics():
    """Create English Language topics - skill-based structure."""
    topics = []
    
    # Level 0: Components (skip Component 3 as it's NEA)
    topics.append({
        'code': 'Component1',
        'title': 'Component 1: Language Variation',
        'level': 0,
        'parent': None
    })
    
    topics.append({
        'code': 'Component2',
        'title': 'Component 2: Child Language',
        'level': 0,
        'parent': None
    })
    
    # Component 1 Content - Level 1
    topics.extend([
        {'code': 'C1-KeyFrameworks', 'title': 'Key Language Frameworks', 'level': 1, 'parent': 'Component1'},
        {'code': 'C1-LanguageLevels', 'title': 'Language Levels', 'level': 1, 'parent': 'Component1'},
        {'code': 'C1-IndividualVariation', 'title': 'Individual Variation', 'level': 1, 'parent': 'Component1'},
        {'code': 'C1-VariationOverTime', 'title': 'Variation Over Time', 'level': 1, 'parent': 'Component1'},
    ])
    
    # Component 1 - Key Frameworks (Level 2)
    topics.extend([
        {'code': 'C1-KF-Mode', 'title': 'Mode: method of communication (spoken, written, multimodal)', 'level': 2, 'parent': 'C1-KeyFrameworks'},
        {'code': 'C1-KF-Field', 'title': 'Field: subject matter', 'level': 2, 'parent': 'C1-KeyFrameworks'},
        {'code': 'C1-KF-Function', 'title': 'Function: purpose', 'level': 2, 'parent': 'C1-KeyFrameworks'},
        {'code': 'C1-KF-Audience', 'title': 'Audience: relationship between writers/speakers and readers/listeners', 'level': 2, 'parent': 'C1-KeyFrameworks'},
        {'code': 'C1-KF-Pragmatics', 'title': 'Pragmatics: variation in meaning depending on context', 'level': 2, 'parent': 'C1-KeyFrameworks'},
        {'code': 'C1-KF-Discourse', 'title': 'Discourse: extended texts in context', 'level': 2, 'parent': 'C1-KeyFrameworks'},
    ])
    
    # Component 1 - Language Levels (Level 2)
    topics.extend([
        {'code': 'C1-LL-Graphology', 'title': 'Graphology: writing system and presentation of language', 'level': 2, 'parent': 'C1-LanguageLevels'},
        {'code': 'C1-LL-Phonetics', 'title': 'Phonetics, phonology and prosody: speech sounds, sound effects and intonation', 'level': 2, 'parent': 'C1-LanguageLevels'},
        {'code': 'C1-LL-Morphology', 'title': 'Morphology: structure of words', 'level': 2, 'parent': 'C1-LanguageLevels'},
        {'code': 'C1-LL-Lexis', 'title': 'Lexis: vocabulary and semantics (meanings)', 'level': 2, 'parent': 'C1-LanguageLevels'},
        {'code': 'C1-LL-Syntax', 'title': 'Syntax: relationships between words in sentences', 'level': 2, 'parent': 'C1-LanguageLevels'},
    ])
    
    # Component 1 - Individual Variation (Level 2)
    topics.extend([
        {'code': 'C1-IV-Identity', 'title': 'Language choices reflecting and constructing identity', 'level': 2, 'parent': 'C1-IndividualVariation'},
        {'code': 'C1-IV-Geographical', 'title': 'Geographical factors affecting language', 'level': 2, 'parent': 'C1-IndividualVariation'},
        {'code': 'C1-IV-Social', 'title': 'Social factors: gender, age, ethnicity and other social identities', 'level': 2, 'parent': 'C1-IndividualVariation'},
    ])
    
    # Component 1 - Variation Over Time (Level 2)
    topics.extend([
        {'code': 'C1-VOT-Development', 'title': 'Development of English as national language', 'level': 2, 'parent': 'C1-VariationOverTime'},
        {'code': 'C1-VOT-Influences', 'title': 'Cultural, social, political and technological influences on English', 'level': 2, 'parent': 'C1-VariationOverTime'},
        {'code': 'C1-VOT-Changes', 'title': 'Language changes across frameworks and levels', 'level': 2, 'parent': 'C1-VariationOverTime'},
    ])
    
    # Component 2 Content - Level 1
    topics.extend([
        {'code': 'C2-SpokenLanguage', 'title': 'Spoken Language Acquisition (ages 0-8)', 'level': 1, 'parent': 'Component2'},
        {'code': 'C2-WrittenLanguage', 'title': 'Written Language Development', 'level': 1, 'parent': 'Component2'},
    ])
    
    # Component 2 - Spoken Language (Level 2)
    topics.extend([
        {'code': 'C2-SL-Beginnings', 'title': 'Beginnings of speech', 'level': 2, 'parent': 'C2-SpokenLanguage'},
        {'code': 'C2-SL-SoundSystem', 'title': 'Acquisition and development of sound system (phonetics)', 'level': 2, 'parent': 'C2-SpokenLanguage'},
        {'code': 'C2-SL-WordStructure', 'title': 'Understanding structure of words (morphology)', 'level': 2, 'parent': 'C2-SpokenLanguage'},
        {'code': 'C2-SL-Vocabulary', 'title': 'Development and extension of vocabulary (lexis)', 'level': 2, 'parent': 'C2-SpokenLanguage'},
        {'code': 'C2-SL-Meanings', 'title': 'Understanding meanings of words (semantics)', 'level': 2, 'parent': 'C2-SpokenLanguage'},
        {'code': 'C2-SL-Syntax', 'title': 'Structures and larger structures (syntax)', 'level': 2, 'parent': 'C2-SpokenLanguage'},
        {'code': 'C2-SL-Conversation', 'title': 'Interactive and pragmatic skills (conversation)', 'level': 2, 'parent': 'C2-SpokenLanguage'},
    ])
    
    # Component 2 - Written Language (Level 2)
    topics.extend([
        {'code': 'C2-WL-Transition', 'title': 'Transition from speech to writing: drawing, gesture and writing', 'level': 2, 'parent': 'C2-WrittenLanguage'},
        {'code': 'C2-WL-EarlyForms', 'title': 'Early forms: drawing, scribbling, letter-like forms, random letters', 'level': 2, 'parent': 'C2-WrittenLanguage'},
        {'code': 'C2-WL-LetterForms', 'title': 'Development of letter forms and directionality (graphology)', 'level': 2, 'parent': 'C2-WrittenLanguage'},
        {'code': 'C2-WL-Spelling', 'title': 'Effect of reading strategies on spelling (morphology)', 'level': 2, 'parent': 'C2-WrittenLanguage'},
        {'code': 'C2-WL-Vocabulary', 'title': 'Vocabulary choices (lexis) and sentence structures (syntax)', 'level': 2, 'parent': 'C2-WrittenLanguage'},
        {'code': 'C2-WL-Narrative', 'title': 'Development of narrative and descriptive skills (discourse)', 'level': 2, 'parent': 'C2-WrittenLanguage'},
    ])
    
    return topics

def upload_topics(topics):
    """Upload to Supabase."""
    print("\n[INFO] Uploading to database...")
    
    # Get/create subject
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
    supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
    print("[OK] Cleared old topics")
    
    # Insert topics
    to_insert = [{
        'subject_id': subject_id,
        'topic_code': t['code'],
        'topic_name': t['title'],
        'topic_level': t['level'],
        'exam_board': 'Edexcel'
    } for t in topics]
    
    inserted_result = supabase.table('staging_aqa_topics').insert(to_insert).execute()
    print(f"[OK] Uploaded {len(inserted_result.data)} topics")
    
    # Link hierarchy
    code_to_id = {t['topic_code']: t['id'] for t in inserted_result.data}
    linked = 0
    
    for topic in topics:
        if topic['parent']:
            parent_id = code_to_id.get(topic['parent'])
            child_id = code_to_id.get(topic['code'])
            if parent_id and child_id:
                supabase.table('staging_aqa_topics').update({
                    'parent_topic_id': parent_id
                }).eq('id', child_id).execute()
                linked += 1
    
    print(f"[OK] Linked {linked} relationships")

def main():
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 80)
    print("EDEXCEL ENGLISH LANGUAGE (9EN0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print("\nNote: Component 3 (Investigating Language) is NEA - excluded")
    
    try:
        topics = create_topics()
        
        # Show distribution
        levels = {}
        for t in topics:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print(f"\n[INFO] Created {len(topics)} topics")
        print("\n   Level distribution:")
        for l in sorted(levels.keys()):
            print(f"   Level {l}: {levels[l]} topics")
        
        upload_topics(topics)
        
        print("\n" + "=" * 80)
        print("[OK] ENGLISH LANGUAGE COMPLETE!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

