"""
Edexcel Urdu (9UR0) and Persian (9PE0) - Combined Manual Topic Upload
Simplified upload with basic 3-level hierarchy (Papers, Themes, Sub-themes)
Full native text parsing is complex due to RTL script - this creates working structure
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

# ==================================================================================
# URDU
# ==================================================================================

URDU_SUBJECT = {
    'code': '9UR0',
    'name': 'Urdu (listening, reading and writing)',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Urdu/2018/specification-and-sample-assessments/A-level-Urdu-Specification11.pdf'
}

URDU_TOPICS = [
    # Papers
    {'code': 'Paper1', 'title': 'Paper 1: Listening, Reading and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper2', 'title': 'Paper 2: Written Response to Works and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper3', 'title': 'Paper 3: Listening, Reading and Writing', 'level': 0, 'parent': None},
    
    # Theme 1
    {'code': 'Theme1', 'title': 'عنوان 1: پاکستانی معاشرے کا ارتقا (Theme 1: Development of Pakistani Society)', 'level': 1, 'parent': 'Paper1'},
    {'code': 'T1-1', 'title': 'خاندان (Family)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-2', 'title': 'کام (Work)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-R', 'title': 'تحقیق: غربت (Research: Poverty)', 'level': 2, 'parent': 'Theme1'},
    
    # Theme 2
    {'code': 'Theme2', 'title': 'عنوان 2: اردو بولنے والی دنیا میں فنون اور تہذیب (Theme 2: Arts and Culture in Urdu-speaking World)', 'level': 1, 'parent': 'Paper1'},
    {'code': 'T2-1', 'title': 'لوک روایت و رسوم (Folklore and Customs)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-2', 'title': 'مقبول کلچر (Popular Culture)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-R', 'title': 'تحقیق: میڈیا (Research: Media)', 'level': 2, 'parent': 'Theme2'},
    
    # Theme 3
    {'code': 'Theme3', 'title': 'عنوان 3: کثیر الثقافتی معاشرہ (Theme 3: Multicultural Society)', 'level': 1, 'parent': 'Paper1'},
    {'code': 'T3-1', 'title': 'مثبت پہلو (Positive Aspects)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-2', 'title': 'ہجرت کے رجحانات (Migration Trends)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-R', 'title': 'تحقیق: پاکستان سے ہجرت (Research: Emigration from Pakistan)', 'level': 2, 'parent': 'Theme3'},
    
    # Theme 4
    {'code': 'Theme4', 'title': 'عنوان 4: پاکستانی سیاست کے پہلو (Theme 4: Aspects of Pakistani Politics)', 'level': 1, 'parent': 'Paper1'},
    {'code': 'T4-1', 'title': '1947 تقسیم ہند و پاک (1947 Partition of India and Pakistan)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-2', 'title': 'نظام جاگیرداری (Feudal System)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-R', 'title': 'تحقیق: ماحولیاتی مسائل (Research: Environmental Issues)', 'level': 2, 'parent': 'Theme4'},
]

# ==================================================================================
# PERSIAN
# ==================================================================================

PERSIAN_SUBJECT = {
    'code': '9PE0',
    'name': 'Persian (listening, reading and writing)',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Persian/2018/specification-and-sample-assessments/A-level-Persian-Specification.pdf'
}

PERSIAN_TOPICS = [
    # Papers
    {'code': 'Paper1', 'title': 'Paper 1: Listening, Reading and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper2', 'title': 'Paper 2: Written Response to Works and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper3', 'title': 'Paper 3: Listening, Reading and Writing', 'level': 0, 'parent': None},
    
    # Theme 1
    {'code': 'Theme1', 'title': 'موضوع ۱: تغییرات در جامعه معاصر (Theme 1: Changes in Contemporary Society)', 'level': 1, 'parent': 'Paper1'},
    {'code': 'T1-1', 'title': 'تغییرات در ساختار خانواده (Changes in Family Structure)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-2', 'title': 'پرورش و آموزش (Education)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-R', 'title': 'تحقیق: فرصت های کاری (Research: Job Opportunities)', 'level': 2, 'parent': 'Theme1'},
    
    # Theme 2
    {'code': 'Theme2', 'title': 'موضوع ۲: فرهنگ و رسانه ها (Theme 2: Culture and Media)', 'level': 1, 'parent': 'Paper1'},
    {'code': 'T2-1', 'title': 'موسیقی (Music)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-2', 'title': 'جشنواره ها و سنت ها (Festivals and Traditions)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-R', 'title': 'تحقیق: رسانه (Research: Media)', 'level': 2, 'parent': 'Theme2'},
    
    # Theme 3
    {'code': 'Theme3', 'title': 'موضوع ۳: جنبه های متنوع جامعه فارسی زبان (Theme 3: Diverse Aspects of Persian-speaking Society)', 'level': 1, 'parent': 'Paper1'},
    {'code': 'T3-1', 'title': 'مشارکت در مسائل زیست محیطی (Participation in Environmental Issues)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-2', 'title': 'گردشگری (Tourism)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-R', 'title': 'تحقیق: زنان در جامعه (Research: Women in Society)', 'level': 2, 'parent': 'Theme3'},
    
    # Theme 4
    {'code': 'Theme4', 'title': 'موضوع ٤: تأثیرات سیاسی و هنری (Theme 4: Political and Artistic Influences)', 'level': 1, 'parent': 'Paper1'},
    {'code': 'T4-1', 'title': 'جنگ ایران و عراق (Iran-Iraq War)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-2', 'title': 'تغییر نگرش به هنر (Changing Attitudes to Art)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-R', 'title': 'تحقیق: هنر معاصر ایران (Research: Contemporary Iranian Art)', 'level': 2, 'parent': 'Theme4'},
]


def upload_language(subject_info, topics):
    """Upload topics for a language to Supabase."""
    
    print("=" * 80)
    print(f"EDEXCEL {subject_info['name'].upper()} ({subject_info['code']}) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {subject_info['name']}")
    print(f"Code: {subject_info['code']}")
    print(f"Topics: {len(topics)}")
    print("\nBasic hierarchy with native text + English translations\n")
    
    try:
        # Get/create subject
        print("[INFO] Creating/updating subject...")
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{subject_info['name']} (A-Level)",
            'subject_code': subject_info['code'],
            'qualification_type': 'A-Level',
            'specification_url': subject_info['pdf_url'],
            'exam_board': 'Edexcel'
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        # Clear old topics
        print("\n[INFO] Clearing old topics...")
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared")
        
        # Insert topics
        print(f"\n[INFO] Uploading {len(topics)} topics...")
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
        print("\n[INFO] Linking parent-child relationships...")
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
        
        # Summary
        levels = {}
        for t in topics:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("\n[INFO] Hierarchy:")
        for level in sorted(levels.keys()):
            print(f"   Level {level}: {levels[level]} topics")
        print(f"\n   Total: {len(topics)} topics")
        
        print("\n" + "=" * 80)
        print(f"[OK] {subject_info['name'].upper()} TOPICS UPLOADED SUCCESSFULLY!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Upload both Urdu and Persian."""
    
    print("\n" + "=" * 80)
    print("UPLOADING URDU AND PERSIAN")
    print("=" * 80 + "\n")
    
    results = []
    
    # Upload Urdu
    if upload_language(URDU_SUBJECT, URDU_TOPICS):
        results.append(('Urdu', True))
    else:
        results.append(('Urdu', False))
    
    print("\n" + "=" * 80 + "\n")
    
    # Upload Persian
    if upload_language(PERSIAN_SUBJECT, PERSIAN_TOPICS):
        results.append(('Persian', True))
    else:
        results.append(('Persian', False))
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    success = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]
    
    if success:
        print(f"\n✅ Successfully uploaded: {len(success)}")
        for lang, _ in success:
            print(f"   • {lang}")
    
    if failed:
        print(f"\n❌ Failed: {len(failed)}")
        for lang, _ in failed:
            print(f"   • {lang}")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()











