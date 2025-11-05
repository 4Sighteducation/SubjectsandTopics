"""
Edexcel Chinese (9CN0) - Manual Topic Upload
Structured data from specification (similar to Arabic approach)

Themes with Chinese text (Traditional/Simplified) and English translations
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
    'code': '9CN0',
    'name': 'Chinese (Mandarin/Cantonese)',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Chinese/2017/specification-and-sample-assessments/Specification_GCE_A_level_L3_in_Chinese.pdf'
}

# Structured topic data - Traditional characters with English
TOPICS = [
    # Level 0: The 4 Themes
    {
        'code': 'Theme1',
        'title': '當代華人社會變遷 (Changes in Contemporary Chinese Society)',
        'level': 0,
        'parent': None
    },
    {
        'code': 'Theme2',
        'title': '中國文化 (Chinese Culture)',
        'level': 0,
        'parent': None
    },
    {
        'code': 'Theme3',
        'title': '演變中的華人社會 (Evolving Chinese Society)',
        'level': 0,
        'parent': None
    },
    {
        'code': 'Theme4',
        'title': '1978年改革開放對中國的影響 (Impact of China\'s 1978 Reform and Opening Up)',
        'level': 0,
        'parent': None
    },
    
    # ========================================
    # THEME 1: Changes in Contemporary Chinese Society
    # ========================================
    
    # Level 1: Sub-themes
    {
        'code': 'Theme1.Family',
        'title': '家庭 (Family)',
        'level': 1,
        'parent': 'Theme1'
    },
    {
        'code': 'Theme1.EduWork',
        'title': '教育與工作 (Education and Work)',
        'level': 1,
        'parent': 'Theme1'
    },
    
    # Level 2: Family topics
    {
        'code': 'Theme1.Family.1',
        'title': '家庭結構和代溝 (Family structure and generation gap)',
        'level': 2,
        'parent': 'Theme1.Family'
    },
    {
        'code': 'Theme1.Family.2',
        'title': '家庭計劃和人口老齡化 (Family planning and aging population)',
        'level': 2,
        'parent': 'Theme1.Family'
    },
    
    # Level 2: Education and Work topics
    {
        'code': 'Theme1.EduWork.1',
        'title': '學校生活和學生議題 (School life and student issues)',
        'level': 2,
        'parent': 'Theme1.EduWork'
    },
    {
        'code': 'Theme1.EduWork.2',
        'title': '工作機會 (Work opportunities)',
        'level': 2,
        'parent': 'Theme1.EduWork'
    },
    {
        'code': 'Theme1.EduWork.3',
        'title': '工作和生活的平衡 (Work-life balance)',
        'level': 2,
        'parent': 'Theme1.EduWork'
    },
    
    # ========================================
    # THEME 2: Chinese Culture
    # ========================================
    
    # Level 1: Sub-themes
    {
        'code': 'Theme2.Tradition',
        'title': '傳統 (Tradition)',
        'level': 1,
        'parent': 'Theme2'
    },
    {
        'code': 'Theme2.Culture',
        'title': '文化活動 (Cultural Activities)',
        'level': 1,
        'parent': 'Theme2'
    },
    
    # Level 2: Tradition topics
    {
        'code': 'Theme2.Trad.Festivals',
        'title': '節日 (Festivals)',
        'level': 2,
        'parent': 'Theme2.Tradition'
    },
    {
        'code': 'Theme2.Trad.Customs',
        'title': '習俗 (Customs)',
        'level': 2,
        'parent': 'Theme2.Tradition'
    },
    
    # Level 3: Specific Festivals
    {
        'code': 'Theme2.Trad.Fest.Spring',
        'title': '春節 (Spring Festival)',
        'level': 3,
        'parent': 'Theme2.Trad.Festivals'
    },
    {
        'code': 'Theme2.Trad.Fest.Dragon',
        'title': '端午節 (Dragon Boat Festival)',
        'level': 3,
        'parent': 'Theme2.Trad.Festivals'
    },
    {
        'code': 'Theme2.Trad.Fest.MidAutumn',
        'title': '中秋節 (Mid-Autumn Festival)',
        'level': 3,
        'parent': 'Theme2.Trad.Festivals'
    },
    {
        'code': 'Theme2.Trad.Fest.Tomb',
        'title': '清明節 (Tomb-Sweeping Festival)',
        'level': 3,
        'parent': 'Theme2.Trad.Festivals'
    },
    
    # Level 2: Cultural Activities topics
    {
        'code': 'Theme2.Cult.Film',
        'title': '電影 (Film - related to Chinese culture)',
        'level': 2,
        'parent': 'Theme2.Culture'
    },
    {
        'code': 'Theme2.Cult.TV',
        'title': '電視 (Television - related to Chinese culture)',
        'level': 2,
        'parent': 'Theme2.Culture'
    },
    {
        'code': 'Theme2.Cult.Music',
        'title': '音樂 (Music - related to Chinese culture)',
        'level': 2,
        'parent': 'Theme2.Culture'
    },
    {
        'code': 'Theme2.Cult.Reading',
        'title': '閱讀 (Reading - related to Chinese culture)',
        'level': 2,
        'parent': 'Theme2.Culture'
    },
    
    # ========================================
    # THEME 3: Evolving Chinese Society
    # ========================================
    
    # Level 1: Sub-themes
    {
        'code': 'Theme3.CommTech',
        'title': '通訊與科技 (Communication and Technology)',
        'level': 1,
        'parent': 'Theme3'
    },
    {
        'code': 'Theme3.EconEnv',
        'title': '經濟與環境 (Economy and Environment)',
        'level': 1,
        'parent': 'Theme3'
    },
    
    # Level 2: Communication and Technology topics
    {
        'code': 'Theme3.CT.Internet',
        'title': '互聯網和社交媒體 (Internet and social media)',
        'level': 2,
        'parent': 'Theme3.CommTech'
    },
    
    # Level 2: Economy and Environment topics
    {
        'code': 'Theme3.EE.Economic',
        'title': '經濟發展 (Economic development)',
        'level': 2,
        'parent': 'Theme3.EconEnv'
    },
    {
        'code': 'Theme3.EE.Environment',
        'title': '環境保護 (Environmental protection)',
        'level': 2,
        'parent': 'Theme3.EconEnv'
    },
    
    # ========================================
    # THEME 4: Impact of China's 1978 Reform and Opening Up
    # ========================================
    
    # Level 1: Sub-themes
    {
        'code': 'Theme4.Change',
        'title': '變革 (Change)',
        'level': 1,
        'parent': 'Theme4'
    },
    {
        'code': 'Theme4.Relations',
        'title': '中英關係 (Sino-British Relations)',
        'level': 1,
        'parent': 'Theme4'
    },
    
    # Level 2: Change topics
    {
        'code': 'Theme4.Change.1',
        'title': '貧富差距 (Wealth gap)',
        'level': 2,
        'parent': 'Theme4.Change'
    },
    {
        'code': 'Theme4.Change.2',
        'title': '超級大都市 (Megacities)',
        'level': 2,
        'parent': 'Theme4.Change'
    },
    {
        'code': 'Theme4.Change.3',
        'title': '城市移民 (Urban migration)',
        'level': 2,
        'parent': 'Theme4.Change'
    },
    
    # Level 2: Sino-British Relations topics
    {
        'code': 'Theme4.Rel.Trade',
        'title': '貿易 (Trade)',
        'level': 2,
        'parent': 'Theme4.Relations'
    },
    {
        'code': 'Theme4.Rel.Cultural',
        'title': '文化交流 (Cultural exchange)',
        'level': 2,
        'parent': 'Theme4.Relations'
    },
    {
        'code': 'Theme4.Rel.Education',
        'title': '教育交流 (Educational exchange)',
        'level': 2,
        'parent': 'Theme4.Relations'
    }
]


def upload_chinese_topics():
    """Upload Chinese topics to Supabase."""
    
    print("=" * 80)
    print("EDEXCEL CHINESE (9CN0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("\nIncludes Traditional Chinese with English translations!\n")
    
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
        print("[OK] CHINESE TOPICS UPLOADED SUCCESSFULLY!")
        print("=" * 80)
        
        # Show hierarchy breakdown
        levels = {}
        for t in TOPICS:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("\nHierarchy:")
        print(f"   Level 0 (Themes): {levels.get(0, 0)}")
        print(f"   Level 1 (Sub-themes): {levels.get(1, 0)}")
        print(f"   Level 2 (Topics): {levels.get(2, 0)}")
        print(f"   Level 3 (Specific topics): {levels.get(3, 0)}")
        print(f"\n   Total: {len(TOPICS)} topics")
        
        # Sample Chinese topics
        print("\nSample topics with Chinese characters:")
        for t in TOPICS[4:8]:
            print(f"   - {t['title']}")
        
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
    
    success = upload_chinese_topics()
    sys.exit(0 if success else 1)

