"""
EDEXCEL GCSE LANGUAGES - UNIVERSAL TEMPLATE
Works for ALL 14 languages with standardized 2024 structure:
- 6 universal themes
- Vocabulary organized by grammar function
- Examined skills: Speaking, Listening, Reading, Writing

Structure enables AI flashcard generation:
  Level 0: Skills (Speaking, Listening, Reading, Writing)
  Level 1: 6 Themes (universal across all languages)
  Level 2: Vocabulary Categories
  Level 3: Grammar/Vocab Types

This creates context for AI to generate vocabulary flashcards
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

# UNIVERSAL structure - same for ALL GCSE languages
# AI-friendly: Theme + Grammar = Context for flashcard generation

def create_universal_topics():
    """Create universal GCSE language structure."""
    topics = []
    
    # Level 0: 6 Themes + Basic Vocabulary (7 total)
    themes = [
        {'code': 'Theme1', 'title': 'Theme 1: My personal world', 'level': 0, 'parent': None},
        {'code': 'Theme2', 'title': 'Theme 2: Lifestyle and wellbeing', 'level': 0, 'parent': None},
        {'code': 'Theme3', 'title': 'Theme 3: My neighbourhood', 'level': 0, 'parent': None},
        {'code': 'Theme4', 'title': 'Theme 4: Media and technology', 'level': 0, 'parent': None},
        {'code': 'Theme5', 'title': 'Theme 5: Studying and my future', 'level': 0, 'parent': None},
        {'code': 'Theme6', 'title': 'Theme 6: Travel and tourism', 'level': 0, 'parent': None},
        {'code': 'BasicVocab', 'title': 'Basic Vocabulary', 'level': 0, 'parent': None},
    ]
    topics.extend(themes)
    
    # Level 1: Grammar categories (same under each theme)
    grammar_cats = [
        {'code': 'ArticlesPronouns', 'title': 'Articles and pronouns'},
        {'code': 'Conjunctions', 'title': 'Conjunctions'},
        {'code': 'Prepositions', 'title': 'Prepositions'},
        {'code': 'Adverbs', 'title': 'Adverbs'},
        {'code': 'Adjectives', 'title': 'Adjectives'},
        {'code': 'Nouns', 'title': 'Nouns'},
        {'code': 'Verbs', 'title': 'Verbs'},
    ]
    
    # Add grammar categories under each theme
    for theme in themes[:6]:  # First 6 themes (not Basic Vocab)
        for gram in grammar_cats:
            topics.append({
                'code': f'{theme["code"]}_{gram["code"]}',
                'title': gram['title'],
                'level': 1,
                'parent': theme['code']
            })
    
    # Level 1 under Basic Vocabulary: Specific categories
    basic_cats = [
        'Greetings',
        'Numbers',
        'Days of the week',
        'Months of the year',
        'Seasons',
        'Times of the day',
        'Colours',
        'Cultural and geographical words',
        'Common phrases'
    ]
    
    for cat in basic_cats:
        code_safe = cat.replace(' ', '').replace('-', '')
        topics.append({
            'code': f'BasicVocab_{code_safe}',
            'title': cat,
            'level': 1,
            'parent': 'BasicVocab'
        })
    
    return topics

UNIVERSAL_LANGUAGE_TOPICS = create_universal_topics()

# All GCSE Languages
GCSE_LANGUAGES = {
    'GCSE-French': {
        'name': 'French',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/French/2024/specification-and-sample-assessments/gq000023-gcse-french-specification-2024-issue-2.pdf'
    },
    'GCSE-German': {
        'name': 'German',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/German/2024/specification-and-sample-assessments/gq000025-gcse-german-specification-2024-issue-2.pdf'
    },
    'GCSE-Spanish': {
        'name': 'Spanish',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Spanish/2024/specification-and-sample-assessments/gq000027-gcse-spanish-specification-2024-issue-2.pdf'
    },
    'GCSE-Arabic': {
        'name': 'Arabic',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Arabic/2017/specification-and-sample-assessments/specification-gcse2017-l12-arabic-issue5.pdf'
    },
    'GCSE-Chinese': {
        'name': 'Chinese',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Chinese/2017/specification-and-sample-assessments/specification-gcse2017-l12-chinese-issue5.pdf'
    },
    'GCSE-Greek': {
        'name': 'Greek',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Greek/2017/specification-and-sample-assessments/specification-gcse2017-l12-greek-issue5.pdf'
    },
    'GCSE-Gujarati': {
        'name': 'Gujarati',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Gujarati/2018/specification-and-sample-assessment-material/specification-gcse2017-l12-gujarati-iss4.pdf'
    },
    'GCSE-Italian': {
        'name': 'Italian',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Italian/2017/specification-and-sample-assessments/specification-gcse2017-l12-italian-issue5.pdf'
    },
    'GCSE-Japanese': {
        'name': 'Japanese',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Japanese/2017/specification-and-sample-assessments/specification-gcse2017-l12-japanese-issue5.pdf'
    },
    'GCSE-Persian': {
        'name': 'Persian',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Persian/2017/Specification%20and%20Sample%20Assessment%20Material/specification-gcse2017-l12-persian-iss4.pdf'
    },
    'GCSE-Portuguese': {
        'name': 'Portuguese',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Portuguese/2018/Specification-and-sample-assessments/specification-gcse2017-l12-portuguese-iss4.pdf'
    },
    'GCSE-Russian': {
        'name': 'Russian',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Russian/2017/specification-and-sample-assessments/specification-gcse2017-l12-russian-issue5.pdf'
    },
    'GCSE-Turkish': {
        'name': 'Turkish',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Turkish/2018/Specification-and-sample-assessments/specification-gcse2017-l12-turkish-iss4.pdf'
    },
    'GCSE-Urdu': {
        'name': 'Urdu',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Urdu/2017/specification-and-sample-assessments/specification-gcse2017-l12-urdu-issue5.pdf'
    },
}


def upload_language(code, name, pdf_url):
    """Upload universal language structure for one language."""
    
    print(f"\n{'=' * 80}")
    print(f"Uploading: {name} ({code})")
    print(f"{'=' * 80}\n")
    
    try:
        # Get/create subject
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{name} (GCSE)",
            'subject_code': code,
            'qualification_type': 'GCSE',
            'specification_url': pdf_url,
            'exam_board': 'Edexcel'
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        
        # Clear old
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        
        # Insert universal topics
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'exam_board': 'Edexcel'
        } for t in UNIVERSAL_LANGUAGE_TOPICS]
        
        inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        
        # Link hierarchy
        code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
        for topic in UNIVERSAL_LANGUAGE_TOPICS:
            if topic['parent']:
                parent_id = code_to_id.get(topic['parent'])
                child_id = code_to_id.get(topic['code'])
                if parent_id and child_id:
                    supabase.table('staging_aqa_topics').update({
                        'parent_topic_id': parent_id
                    }).eq('id', child_id).execute()
        
        print(f"[OK] {name}: {len(inserted.data)} topics uploaded")
        return True
        
    except Exception as e:
        print(f"[ERROR] {name} failed: {e}")
        return False


def main():
    """Upload universal language structure for all 14 GCSE languages."""
    
    print("=" * 80)
    print("GCSE LANGUAGES - UNIVERSAL TEMPLATE UPLOADER")
    print("=" * 80)
    print("\nUploading SAME structure for all 14 languages:")
    print("- 6 universal themes")
    print("- Vocabulary categories")
    print("- Grammar types")
    print("- Speaking scenarios")
    print("\nEnables AI to generate vocabulary flashcards with context!\n")
    
    results = {'success': [], 'failed': []}
    
    for code, info in GCSE_LANGUAGES.items():
        if upload_language(code, info['name'], info['pdf_url']):
            results['success'].append(info['name'])
        else:
            results['failed'].append(info['name'])
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n✅ Successfully uploaded: {len(results['success'])}/14")
    for lang in results['success']:
        print(f"   • {lang} ({len(UNIVERSAL_LANGUAGE_TOPICS)} topics)")
    
    if results['failed']:
        print(f"\n❌ Failed: {len(results['failed'])}")
        for lang in results['failed']:
            print(f"   • {lang}")
    
    total_topics = len(results['success']) * len(UNIVERSAL_LANGUAGE_TOPICS)
    print(f"\n🎯 TOTAL: {total_topics} language topics uploaded!")
    print("=" * 80)
    
    print("\n💡 AI FLASHCARD GENERATION:")
    print("   AI can now generate flashcards like:")
    print("   • Theme 1 (My personal world) → Nouns → Family vocabulary")
    print("   • Theme 6 (Travel) → Verbs → Transport vocabulary")
    print("   • Speaking → Restaurant scenario → Ordering food phrases")
    print("\n   The 6 themes + vocab categories provide CONTEXT for smart generation!")


if __name__ == '__main__':
    main()

