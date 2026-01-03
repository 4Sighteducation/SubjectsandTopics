"""
GCSE Business - Manual Upload
Based on the table structure with proper hierarchy:
  Level 0: 2 Themes
  Level 1: Topics (1.1-1.5, 2.1-2.5)  
  Level 2: Content codes (1.1.1, 1.1.2, etc.)
  Level 3: Learning points (sentences before colons)

Sample from specification image/description
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
    'code': 'GCSE-Business',
    'name': 'Business',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Business/2017/specification-and-sample-assessments/gcse-business-spec-2017.pdf'
}

TOPICS = [
    # Level 0: Themes
    {'code': 'Theme1', 'title': 'Theme 1: Investigating small business', 'level': 0, 'parent': None},
    {'code': 'Theme2', 'title': 'Theme 2: Building a business', 'level': 0, 'parent': None},
    
    # ==================================================================================
    # THEME 1: INVESTIGATING SMALL BUSINESS
    # ==================================================================================
    
    # Level 1: Topic 1.1
    {'code': 'T1_1', 'title': '1.1 Enterprise and entrepreneurship', 'level': 1, 'parent': 'Theme1'},
    
    # Level 2: Content codes under 1.1
    {'code': 'C1_1_1', 'title': '1.1.1 The dynamic nature of business', 'level': 2, 'parent': 'T1_1'},
    {'code': 'C1_1_1_1', 'title': 'Why new business ideas come about', 'level': 3, 'parent': 'C1_1_1'},
    {'code': 'C1_1_1_2', 'title': 'How new business ideas come about', 'level': 3, 'parent': 'C1_1_1'},
    
    {'code': 'C1_1_2', 'title': '1.1.2 Risk and reward', 'level': 2, 'parent': 'T1_1'},
    {'code': 'C1_1_2_1', 'title': 'The impact of risk and reward on business activity', 'level': 3, 'parent': 'C1_1_2'},
    
    {'code': 'C1_1_3', 'title': '1.1.3 The role of business enterprise', 'level': 2, 'parent': 'T1_1'},
    {'code': 'C1_1_3_1', 'title': 'The role of business enterprise and the purpose of business activity', 'level': 3, 'parent': 'C1_1_3'},
    {'code': 'C1_1_3_2', 'title': 'The role of entrepreneurship', 'level': 3, 'parent': 'C1_1_3'},
    
    # Level 1: Topic 1.2
    {'code': 'T1_2', 'title': '1.2 Spotting a business opportunity', 'level': 1, 'parent': 'Theme1'},
    
    {'code': 'C1_2_1', 'title': '1.2.1 Customer needs', 'level': 2, 'parent': 'T1_2'},
    {'code': 'C1_2_1_1', 'title': 'Identifying and understanding customer needs', 'level': 3, 'parent': 'C1_2_1'},
    
    {'code': 'C1_2_2', 'title': '1.2.2 Market research', 'level': 2, 'parent': 'T1_2'},
    {'code': 'C1_2_2_1', 'title': 'The purpose of market research', 'level': 3, 'parent': 'C1_2_2'},
    {'code': 'C1_2_2_2', 'title': 'Primary and secondary research', 'level': 3, 'parent': 'C1_2_2'},
    {'code': 'C1_2_2_3', 'title': 'The use of qualitative and quantitative data', 'level': 3, 'parent': 'C1_2_2'},
    {'code': 'C1_2_2_4', 'title': 'The use of market segmentation to target customers', 'level': 3, 'parent': 'C1_2_2'},
    {'code': 'C1_2_2_5', 'title': 'The reliability of market research', 'level': 3, 'parent': 'C1_2_2'},
    
    {'code': 'C1_2_3', 'title': '1.2.3 Market mapping', 'level': 2, 'parent': 'T1_2'},
    {'code': 'C1_2_4', 'title': '1.2.4 Competition', 'level': 2, 'parent': 'T1_2'},
    
    # Level 1: Topic 1.3
    {'code': 'T1_3', 'title': '1.3 Putting a business idea into practice', 'level': 1, 'parent': 'Theme1'},
    
    {'code': 'C1_3_1', 'title': '1.3.1 Business aims and objectives', 'level': 2, 'parent': 'T1_3'},
    {'code': 'C1_3_2', 'title': '1.3.2 Business revenues, costs and profits', 'level': 2, 'parent': 'T1_3'},
    {'code': 'C1_3_3', 'title': '1.3.3 Cash and cash flow', 'level': 2, 'parent': 'T1_3'},
    {'code': 'C1_3_4', 'title': '1.3.4 Sources of business finance', 'level': 2, 'parent': 'T1_3'},
    
    # Level 1: Topic 1.4
    {'code': 'T1_4', 'title': '1.4 Making the business effective', 'level': 1, 'parent': 'Theme1'},
    
    {'code': 'C1_4_1', 'title': '1.4.1 The options for start-up and small businesses', 'level': 2, 'parent': 'T1_4'},
    {'code': 'C1_4_2', 'title': '1.4.2 Business location', 'level': 2, 'parent': 'T1_4'},
    {'code': 'C1_4_3', 'title': '1.4.3 The marketing mix', 'level': 2, 'parent': 'T1_4'},
    {'code': 'C1_4_4', 'title': '1.4.4 Business plans', 'level': 2, 'parent': 'T1_4'},
    
    # Level 1: Topic 1.5
    {'code': 'T1_5', 'title': '1.5 Understanding external influences on business', 'level': 1, 'parent': 'Theme1'},
    
    {'code': 'C1_5_1', 'title': '1.5.1 Business stakeholders', 'level': 2, 'parent': 'T1_5'},
    {'code': 'C1_5_2', 'title': '1.5.2 Technology and business', 'level': 2, 'parent': 'T1_5'},
    {'code': 'C1_5_3', 'title': '1.5.3 Legislation and business', 'level': 2, 'parent': 'T1_5'},
    {'code': 'C1_5_4', 'title': '1.5.4 The economy and business', 'level': 2, 'parent': 'T1_5'},
    {'code': 'C1_5_5', 'title': '1.5.5 External influences', 'level': 2, 'parent': 'T1_5'},
    
    # ==================================================================================
    # THEME 2: BUILDING A BUSINESS
    # ==================================================================================
    
    # Level 1: Topic 2.1
    {'code': 'T2_1', 'title': '2.1 Growing the business', 'level': 1, 'parent': 'Theme2'},
    
    {'code': 'C2_1_1', 'title': '2.1.1 Business growth', 'level': 2, 'parent': 'T2_1'},
    {'code': 'C2_1_2', 'title': '2.1.2 Changes in business aims and objectives', 'level': 2, 'parent': 'T2_1'},
    {'code': 'C2_1_3', 'title': '2.1.3 Business and globalisation', 'level': 2, 'parent': 'T2_1'},
    {'code': 'C2_1_4', 'title': '2.1.4 Ethics, the environment and business', 'level': 2, 'parent': 'T2_1'},
    
    # Level 1: Topic 2.2
    {'code': 'T2_2', 'title': '2.2 Making marketing decisions', 'level': 1, 'parent': 'Theme2'},
    
    {'code': 'C2_2_1', 'title': '2.2.1 Product', 'level': 2, 'parent': 'T2_2'},
    {'code': 'C2_2_2', 'title': '2.2.2 Price', 'level': 2, 'parent': 'T2_2'},
    {'code': 'C2_2_3', 'title': '2.2.3 Promotion', 'level': 2, 'parent': 'T2_2'},
    {'code': 'C2_2_4', 'title': '2.2.4 Place', 'level': 2, 'parent': 'T2_2'},
    {'code': 'C2_2_5', 'title': '2.2.5 Using the marketing mix to make business decisions', 'level': 2, 'parent': 'T2_2'},
    
    # Level 1: Topic 2.3
    {'code': 'T2_3', 'title': '2.3 Making operational decisions', 'level': 1, 'parent': 'Theme2'},
    
    {'code': 'C2_3_1', 'title': '2.3.1 Business operations', 'level': 2, 'parent': 'T2_3'},
    {'code': 'C2_3_2', 'title': '2.3.2 Working with suppliers', 'level': 2, 'parent': 'T2_3'},
    {'code': 'C2_3_3', 'title': '2.3.3 Managing quality', 'level': 2, 'parent': 'T2_3'},
    {'code': 'C2_3_4', 'title': '2.3.4 The sales process and customer service', 'level': 2, 'parent': 'T2_3'},
    
    # Level 1: Topic 2.4
    {'code': 'T2_4', 'title': '2.4 Making financial decisions', 'level': 1, 'parent': 'Theme2'},
    
    {'code': 'C2_4_1', 'title': '2.4.1 Business calculations', 'level': 2, 'parent': 'T2_4'},
    {'code': 'C2_4_2', 'title': '2.4.2 Understanding business performance', 'level': 2, 'parent': 'T2_4'},
    
    # Level 1: Topic 2.5
    {'code': 'T2_5', 'title': '2.5 Making human resource decisions', 'level': 1, 'parent': 'Theme2'},
    
    {'code': 'C2_5_1', 'title': '2.5.1 Organisational structures', 'level': 2, 'parent': 'T2_5'},
    {'code': 'C2_5_2', 'title': '2.5.2 Effective recruitment', 'level': 2, 'parent': 'T2_5'},
    {'code': 'C2_5_3', 'title': '2.5.3 Effective training and development', 'level': 2, 'parent': 'T2_5'},
    {'code': 'C2_5_4', 'title': '2.5.4 Motivation', 'level': 2, 'parent': 'T2_5'},
]


def upload_topics():
    """Upload GCSE Business topics."""
    
    print("=" * 80)
    print("GCSE BUSINESS - MANUAL UPLOAD")
    print("=" * 80)
    print(f"Topics: {len(TOPICS)}")
    print("4-level hierarchy: Themes → Topics → Content codes → Learning points\n")
    
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
        print("[OK] GCSE BUSINESS UPLOADED!")
        print("=" * 80)
        print(f"   Level 0 (Themes): {levels.get(0, 0)}")
        print(f"   Level 1 (Topics): {levels.get(1, 0)}")
        print(f"   Level 2 (Content codes): {levels.get(2, 0)}")
        print(f"   Level 3 (Learning points): {levels.get(3, 0)}")
        print(f"\n   Total: {len(TOPICS)} topics")
        print("\nCore topics from Theme 1 & 2 - ready for expansion")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    upload_topics()

