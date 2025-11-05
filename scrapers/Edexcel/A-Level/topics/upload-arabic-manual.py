"""
Edexcel Arabic (9AA0) - Manual Topic Upload
Structured data from PDF pages 8-9

Themes are in Arabic with English translations.
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
    'code': '9AA0',
    'name': 'Arabic (listening, reading and writing)',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Arabic/2018/specification-and-sample-assessments/A-level-Arabic-Specification1.pdf'
}

# Structured topic data from PDF pages 8-9
TOPICS = [
    # Level 0: Papers
    {
        'code': 'Paper1',
        'title': 'Paper 1: Listening, Reading and Translation',
        'level': 0,
        'parent': None
    },
    {
        'code': 'Paper2',
        'title': 'Paper 2: Written Response to Works and Translation',
        'level': 0,
        'parent': None
    },
    {
        'code': 'Paper3',
        'title': 'Paper 3: Speaking',
        'level': 0,
        'parent': None
    },
    
    # Level 1: Four Themes (محاور)
    {
        'code': 'Theme1',
        'title': 'المحور الأول: التغيرات في المجتمع العربي (Theme 1: Changes in Arab Society)',
        'level': 1,
        'parent': 'Paper1'
    },
    {
        'code': 'Theme2',
        'title': 'المحور الثاني: الثقافة الفنية في العالم العربي (Theme 2: Artistic Culture in the Arab World)',
        'level': 1,
        'parent': 'Paper1'
    },
    {
        'code': 'Theme3',
        'title': 'المحور الثالث: العمل والمواطنة في العالم العربي (Theme 3: Work and Citizenship in the Arab World)',
        'level': 1,
        'parent': 'Paper1'
    },
    {
        'code': 'Theme4',
        'title': 'المحور الرابع: الثقافة السياسية في العالم العربي (Theme 4: Political Culture in the Arab World)',
        'level': 1,
        'parent': 'Paper1'
    },
    
    # Level 2: Theme 1 Sub-themes
    {
        'code': 'Theme1.1',
        'title': 'الأسرة العربية (The Arab Family)',
        'level': 2,
        'parent': 'Theme1'
    },
    {
        'code': 'Theme1.1.1',
        'title': 'أدوار الجنسين ضمن الأسرة (Gender roles within the family)',
        'level': 3,
        'parent': 'Theme1.1'
    },
    {
        'code': 'Theme1.1.2',
        'title': 'دور الأسرة الممتدة والأقرباء (The role of the extended family and relatives)',
        'level': 3,
        'parent': 'Theme1.1'
    },
    {
        'code': 'Theme1.1.3',
        'title': 'الموقف من الزواج والطلاق (Attitudes to marriage and divorce)',
        'level': 3,
        'parent': 'Theme1.1'
    },
    
    {
        'code': 'Theme1.2',
        'title': 'الإعلام (Media)',
        'level': 2,
        'parent': 'Theme1'
    },
    {
        'code': 'Theme1.2.1',
        'title': 'تأثير الإعلام على المجتمع العربي (The influence of media on Arab society)',
        'level': 3,
        'parent': 'Theme1.2'
    },
    {
        'code': 'Theme1.2.2',
        'title': 'التكنولوجيا ووسائل الإعلام (Technology and media)',
        'level': 3,
        'parent': 'Theme1.2'
    },
    {
        'code': 'Theme1.2.3',
        'title': 'تأثير وسائل التواصل الاجتماعي على المجتمع والعلاقات (Impact of social media on society and relationships)',
        'level': 3,
        'parent': 'Theme1.2'
    },
    
    {
        'code': 'Theme1.3',
        'title': 'موضوع البحث: الأعراف الاجتماعية في إحدى الدول العربية (Research: Social Customs in an Arabic-speaking Country)',
        'level': 2,
        'parent': 'Theme1'
    },
    {
        'code': 'Theme1.3.1',
        'title': 'أصول الأعراف الاجتماعية (Origins of social customs)',
        'level': 3,
        'parent': 'Theme1.3'
    },
    {
        'code': 'Theme1.3.2',
        'title': 'أهمية هذه الأعراف للمجتمع العربي (Importance of these customs to Arab society)',
        'level': 3,
        'parent': 'Theme1.3'
    },
    {
        'code': 'Theme1.3.3',
        'title': 'تأثير الحياة العصرية على هذه الأعراف (Impact of modern life on these customs)',
        'level': 3,
        'parent': 'Theme1.3'
    },
    
    # Level 2: Theme 2 Sub-themes
    {
        'code': 'Theme2.1',
        'title': 'الموسيقى والأغنية (Music and Song)',
        'level': 2,
        'parent': 'Theme2'
    },
    {
        'code': 'Theme2.1.1',
        'title': 'أنواع الموسيقى والأغاني التقليدية (Types of traditional music and songs)',
        'level': 3,
        'parent': 'Theme2.1'
    },
    {
        'code': 'Theme2.1.2',
        'title': 'الثقافة الشعبية والموسيقية (Popular and musical culture)',
        'level': 3,
        'parent': 'Theme2.1'
    },
    {
        'code': 'Theme2.1.3',
        'title': 'دور الموسيقى والأغنية (The role of music and song)',
        'level': 3,
        'parent': 'Theme2.1'
    },
    
    {
        'code': 'Theme2.2',
        'title': 'فن عربي، الأرابيسك (Arab Art, Arabesque)',
        'level': 2,
        'parent': 'Theme2'
    },
    {
        'code': 'Theme2.2.1',
        'title': 'المهارات الفنية والحرفية من جيل لآخر (Artistic and craft skills from generation to generation)',
        'level': 3,
        'parent': 'Theme2.2'
    },
    {
        'code': 'Theme2.2.2',
        'title': 'التغيرات في فن العمارة (Changes in architecture)',
        'level': 3,
        'parent': 'Theme2.2'
    },
    {
        'code': 'Theme2.2.3',
        'title': 'الخط العربي (Arabic calligraphy)',
        'level': 3,
        'parent': 'Theme2.2'
    },
    
    {
        'code': 'Theme2.3',
        'title': 'موضوع البحث: الاحتفالات والمناسبات في إحدى الدول العربية (Research: Celebrations and Events in an Arabic-speaking Country)',
        'level': 2,
        'parent': 'Theme2'
    },
    {
        'code': 'Theme2.3.1',
        'title': 'الاحتفالات والمناسبات التقليدية القائمة (Existing traditional celebrations and events)',
        'level': 3,
        'parent': 'Theme2.3'
    },
    {
        'code': 'Theme2.3.2',
        'title': 'تحديث الاحتفالات والمناسبات التقليدية (Modernisation of traditional celebrations and events)',
        'level': 3,
        'parent': 'Theme2.3'
    },
    {
        'code': 'Theme2.3.3',
        'title': 'السياحة والمهرجانات والمناسبات (Tourism and festivals and events)',
        'level': 3,
        'parent': 'Theme2.3'
    },
    
    # Level 2: Theme 3 Sub-themes
    {
        'code': 'Theme3.1',
        'title': 'الحياة والعمل (Life and Work)',
        'level': 2,
        'parent': 'Theme3'
    },
    {
        'code': 'Theme3.1.1',
        'title': 'الموقف من تكافؤ الفرص في العمل (Attitudes to equal opportunities in employment)',
        'level': 3,
        'parent': 'Theme3.1'
    },
    {
        'code': 'Theme3.1.2',
        'title': 'البطالة (Unemployment)',
        'level': 3,
        'parent': 'Theme3.1'
    },
    {
        'code': 'Theme3.1.3',
        'title': 'الحراك الاجتماعي (Social mobility)',
        'level': 3,
        'parent': 'Theme3.1'
    },
    
    {
        'code': 'Theme3.2',
        'title': 'المسؤولية تجاه البيئة (Responsibility Towards the Environment)',
        'level': 2,
        'parent': 'Theme3'
    },
    {
        'code': 'Theme3.2.1',
        'title': 'الاتجاهات العامة للمجتمع العربي نحو التلوث وإعادة التدوير (Public attitudes in Arab society towards pollution and recycling)',
        'level': 3,
        'parent': 'Theme3.2'
    },
    {
        'code': 'Theme3.2.2',
        'title': 'الموقف الحكومي من الطاقة البديلة (Government position on alternative energy)',
        'level': 3,
        'parent': 'Theme3.2'
    },
    {
        'code': 'Theme3.2.3',
        'title': 'الجماعات والمنظمات الصديقة للبيئة (Eco-friendly groups and organisations)',
        'level': 3,
        'parent': 'Theme3.2'
    },
    
    {
        'code': 'Theme3.3',
        'title': 'موضوع البحث: السياحة في إحدى الدول العربية (Research: Tourism in an Arabic-speaking Country)',
        'level': 2,
        'parent': 'Theme3'
    },
    {
        'code': 'Theme3.3.1',
        'title': 'التأثير على الاقتصاد السياحي (Impact on the tourist economy)',
        'level': 3,
        'parent': 'Theme3.3'
    },
    {
        'code': 'Theme3.3.2',
        'title': 'تكاليف وفوائد السياحة على السكان المحليين (Costs and benefits of tourism on local populations)',
        'level': 3,
        'parent': 'Theme3.3'
    },
    {
        'code': 'Theme3.3.3',
        'title': 'تأثير السياحة على التراث الوطني والبنية التحتية (Impact of tourism on national heritage and infrastructure)',
        'level': 3,
        'parent': 'Theme3.3'
    },
    
    # Level 2: Theme 4 Sub-themes
    {
        'code': 'Theme4.1',
        'title': 'الهوية العربية (Arab Identity)',
        'level': 2,
        'parent': 'Theme4'
    },
    {
        'code': 'Theme4.1.1',
        'title': 'حركات الاستقلال والقومية في القرن العشرين (Independence and nationalist movements in the 20th century)',
        'level': 3,
        'parent': 'Theme4.1'
    },
    {
        'code': 'Theme4.1.2',
        'title': 'الفلسفة السياسية ومعتقدات العروبة (Political philosophy and beliefs of Arabism)',
        'level': 3,
        'parent': 'Theme4.1'
    },
    {
        'code': 'Theme4.1.3',
        'title': 'مدى انتشار العروبة اليوم (Extent of the spread of Arabism today)',
        'level': 3,
        'parent': 'Theme4.1'
    },
    
    {
        'code': 'Theme4.2',
        'title': 'الأحوال السياسية (Political Conditions)',
        'level': 2,
        'parent': 'Theme4'
    },
    {
        'code': 'Theme4.2.1',
        'title': 'النظم السياسية في العالم العربي (Political systems in the Arab world)',
        'level': 3,
        'parent': 'Theme4.2'
    },
    {
        'code': 'Theme4.2.2',
        'title': 'تغيرات النظم السياسية (Changes in political systems)',
        'level': 3,
        'parent': 'Theme4.2'
    },
    {
        'code': 'Theme4.2.3',
        'title': 'الموقف من الانتخابات وحرية الاختيار في القرن الواحد والعشرين (Attitudes to elections and freedom of choice in the 21st century)',
        'level': 3,
        'parent': 'Theme4.2'
    },
    
    {
        'code': 'Theme4.3',
        'title': 'موضوع البحث: الأقليات العرقية في إحدى الدول العربية (Research: Ethnic Minorities in an Arabic-speaking Country)',
        'level': 2,
        'parent': 'Theme4'
    },
    {
        'code': 'Theme4.3.1',
        'title': 'السياق التاريخي للأقليات (Historical context of minorities)',
        'level': 3,
        'parent': 'Theme4.3'
    },
    {
        'code': 'Theme4.3.2',
        'title': 'مدى اندماج الأقليات في المجتمع (Extent of integration of minorities in society)',
        'level': 3,
        'parent': 'Theme4.3'
    },
    {
        'code': 'Theme4.3.3',
        'title': 'مدى تمتع الأقليات بالمساواة (Extent to which minorities enjoy equality)',
        'level': 3,
        'parent': 'Theme4.3'
    }
]


def upload_arabic_topics():
    """Upload Arabic topics to Supabase."""
    
    print("=" * 80)
    print("EDEXCEL ARABIC (9AA0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("\nThis includes Arabic script - Unicode supported!\n")
    
    try:
        # Get/create subject
        print("📝 Creating/updating subject...")
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT['name']} (A-Level)",
            'subject_code': SUBJECT['code'],
            'qualification_type': 'A-Level',
            'specification_url': SUBJECT['pdf_url'],
            'exam_board': 'Edexcel'
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f"✓ Subject ID: {subject_id}")
        
        # Clear old topics
        print("\n🗑️  Clearing old topics...")
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("✓ Cleared")
        
        # Insert new topics
        print(f"\n📤 Uploading {len(TOPICS)} topics...")
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'exam_board': 'Edexcel'
        } for t in TOPICS]
        
        inserted_result = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"✓ Uploaded {len(inserted_result.data)} topics")
        
        # Link hierarchy
        print("\n🔗 Linking parent-child relationships...")
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
        
        print(f"✓ Linked {linked} relationships")
        
        # Summary
        print("\n" + "=" * 80)
        print("✅ ARABIC TOPICS UPLOADED SUCCESSFULLY!")
        print("=" * 80)
        
        # Show hierarchy breakdown
        levels = {}
        for t in TOPICS:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("\n📊 Hierarchy:")
        print(f"   Level 0 (Papers): {levels.get(0, 0)}")
        print(f"   Level 1 (Themes): {levels.get(1, 0)}")
        print(f"   Level 2 (Sub-themes): {levels.get(2, 0)}")
        print(f"   Level 3 (Topics): {levels.get(3, 0)}")
        print(f"\n   Total: {len(TOPICS)} topics")
        
        # Sample Arabic topics
        print("\n📝 Sample topics with Arabic script:")
        for t in TOPICS[4:8]:  # Show first few themes
            print(f"   • {t['title']}")
        
        print("\n" + "=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Force UTF-8 output
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    success = upload_arabic_topics()
    sys.exit(0 if success else 1)

