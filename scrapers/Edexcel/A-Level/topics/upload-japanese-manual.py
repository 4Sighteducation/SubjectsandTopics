"""
Edexcel Japanese (9JA0) - Manual Topic Upload
Complete hierarchy with themes, sub-themes, and aspects.
Japanese text preserved with English translations.
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
    'code': '9JA0',
    'name': 'Japanese (listening, reading and writing)',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Japanese/2018/specification-and-sample-assessments/a-level-japanese-specification.pdf'
}

TOPICS = [
    # Level 0: Papers
    {'code': 'Paper1', 'title': 'Paper 1: Listening, Reading and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper2', 'title': 'Paper 2: Written Response to Works and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper3', 'title': 'Paper 3: Listening, Reading and Writing', 'level': 0, 'parent': None},
    
    # ==================================================================================
    # THEME 1: 変わっていく若者の生活 (Changing Lives of Young People)
    # ==================================================================================
    {'code': 'Theme1', 'title': 'テーマ１：変わっていく若者の生活 (Theme 1: Changing Lives of Young People)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 1.1
    {'code': 'T1-1', 'title': '教育 (Education)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-1-1', 'title': '教育制度やその改革(ゆとり教育以降) (the education system and its reforms (since Yutori education))', 'level': 3, 'parent': 'T1-1'},
    {'code': 'T1-1-2', 'title': '試験や塾 (exams and cram schools)', 'level': 3, 'parent': 'T1-1'},
    {'code': 'T1-1-3', 'title': '文部科学省によるカリキュラム管理 (curriculum management by MEXT)', 'level': 3, 'parent': 'T1-1'},
    
    # Sub-theme 1.2
    {'code': 'T1-2', 'title': '若者の健康(身体面と心理面) (Health of Young People - Physical and Mental)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-2-1', 'title': '若者にかかるプレッシャー (pressure on young people)', 'level': 3, 'parent': 'T1-2'},
    {'code': 'T1-2-2', 'title': 'それが健康や食生活に与える影響 (its impact on health and diet)', 'level': 3, 'parent': 'T1-2'},
    {'code': 'T1-2-3', 'title': 'いじめ (bullying)', 'level': 3, 'parent': 'T1-2'},
    
    # Research Topic 1
    {'code': 'T1-R', 'title': '自由研究の課題：家族関係や人間関係 (Research: Family and Personal Relationships)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-R-1', 'title': '伝統的な家族構成 (traditional family structures)', 'level': 3, 'parent': 'T1-R'},
    {'code': 'T1-R-2', 'title': '核家族 (nuclear family)', 'level': 3, 'parent': 'T1-R'},
    {'code': 'T1-R-3', 'title': '家庭内の人間関係 (family relationships)', 'level': 3, 'parent': 'T1-R'},
    
    # ==================================================================================
    # THEME 2: 変わっていく文化 (Changing Culture)
    # ==================================================================================
    {'code': 'Theme2', 'title': 'テーマ２：変わっていく文化 (Theme 2: Changing Culture)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 2.1
    {'code': 'T2-1', 'title': '変わるポピュラー・カルチャー (Changing Popular Culture)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-1-1', 'title': 'アニメや漫画 (anime and manga)', 'level': 3, 'parent': 'T2-1'},
    {'code': 'T2-1-2', 'title': '音楽 (music)', 'level': 3, 'parent': 'T2-1'},
    {'code': 'T2-1-3', 'title': '武道・武術 (martial arts)', 'level': 3, 'parent': 'T2-1'},
    
    # Sub-theme 2.2
    {'code': 'T2-2', 'title': 'テクノロジーの影響 (Impact of Technology)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-2-1', 'title': 'テクノロジーの進歩 (technological advances)', 'level': 3, 'parent': 'T2-2'},
    {'code': 'T2-2-2', 'title': 'ロボット (robots)', 'level': 3, 'parent': 'T2-2'},
    {'code': 'T2-2-3', 'title': 'オートメーション (automation)', 'level': 3, 'parent': 'T2-2'},
    
    # Research Topic 2
    {'code': 'T2-R', 'title': '自由研究の課題：変わっていく行事 (Research: Changing Events)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-R-1', 'title': '伝統的な祭りや現代的なイベント (traditional festivals and modern events)', 'level': 3, 'parent': 'T2-R'},
    {'code': 'T2-R-2', 'title': 'イベントや祭りと観光業の影響 (events, festivals and the impact of tourism)', 'level': 3, 'parent': 'T2-R'},
    {'code': 'T2-R-3', 'title': '西洋行事の流入 (influx of Western events)', 'level': 3, 'parent': 'T2-R'},
    
    # ==================================================================================
    # THEME 3: 変わっていく人生観 (Changing Perspectives on Life)
    # ==================================================================================
    {'code': 'Theme3', 'title': 'テーマ３：変わっていく人生観 (Theme 3: Changing Perspectives on Life)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 3.1
    {'code': 'T3-1', 'title': '変化する労働 (Changing Work)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-1-1', 'title': '終身雇用制度の崩壊 (collapse of lifetime employment)', 'level': 3, 'parent': 'T3-1'},
    {'code': 'T3-1-2', 'title': '仕事に対する意識の変化 (changing attitudes towards work)', 'level': 3, 'parent': 'T3-1'},
    {'code': 'T3-1-3', 'title': '仕事のための移住 (relocation for work)', 'level': 3, 'parent': 'T3-1'},
    
    # Sub-theme 3.2
    {'code': 'T3-2', 'title': '長引く不景気 (Prolonged Recession)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-2-1', 'title': '日常生活への影響 (impact on daily life)', 'level': 3, 'parent': 'T3-2'},
    {'code': 'T3-2-2', 'title': '政府の対応 (government response)', 'level': 3, 'parent': 'T3-2'},
    {'code': 'T3-2-3', 'title': '経済の国際化：移住外国人労働者の受け入れ (economic globalization: acceptance of migrant foreign workers)', 'level': 3, 'parent': 'T3-2'},
    
    # Research Topic 3
    {'code': 'T3-R', 'title': '自由研究の課題：高齢化社会 (Research: Aging Society)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-R-1', 'title': '高齢者の孤立 (isolation of the elderly)', 'level': 3, 'parent': 'T3-R'},
    {'code': 'T3-R-2', 'title': '家族からのサポート (family support)', 'level': 3, 'parent': 'T3-R'},
    {'code': 'T3-R-3', 'title': '社会的支援 (social support)', 'level': 3, 'parent': 'T3-R'},
    
    # ==================================================================================
    # THEME 4: 東日本大震災後の日本 (Japan After the Great East Japan Earthquake)
    # ==================================================================================
    {'code': 'Theme4', 'title': 'テーマ４：東日本大震災後の日本 (Theme 4: Japan After the Great East Japan Earthquake)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 4.1
    {'code': 'T4-1', 'title': '3月11日とその直後 (March 11 and Its Immediate Aftermath)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-1-1', 'title': '地震と津波の被害 (earthquake and tsunami damage)', 'level': 3, 'parent': 'T4-1'},
    {'code': 'T4-1-2', 'title': '避難生活 (evacuation life)', 'level': 3, 'parent': 'T4-1'},
    {'code': 'T4-1-3', 'title': '救出と援助：海外の反応 (rescue and aid: international response)', 'level': 3, 'parent': 'T4-1'},
    
    # Sub-theme 4.2
    {'code': 'T4-2', 'title': '復興への政策 (Reconstruction Policies)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-2-1', 'title': '被災地の立て直し (rebuilding affected areas)', 'level': 3, 'parent': 'T4-2'},
    {'code': 'T4-2-2', 'title': 'ボランティアや国民の団結 (volunteers and national unity)', 'level': 3, 'parent': 'T4-2'},
    {'code': 'T4-2-3', 'title': '困難を乗り切る力：心のケア (resilience: psychological care)', 'level': 3, 'parent': 'T4-2'},
    
    # Research Topic 4
    {'code': 'T4-R', 'title': '自由研究の課題：福島原発事故後の省エネ生活 (Research: Energy-Saving Lifestyle After Fukushima)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-R-1', 'title': '日常生活の中の省エネ (energy saving in daily life)', 'level': 3, 'parent': 'T4-R'},
    {'code': 'T4-R-2', 'title': 'エネルギー供給をめぐる議論 (debate over energy supply)', 'level': 3, 'parent': 'T4-R'},
    {'code': 'T4-R-3', 'title': '省エネに関する昔の知恵 (traditional wisdom on energy conservation)', 'level': 3, 'parent': 'T4-R'},
]


def upload_topics():
    """Upload Japanese topics to Supabase."""
    
    print("=" * 80)
    print("EDEXCEL JAPANESE (9JA0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("\nComplete hierarchy with Japanese text + English translations\n")
    
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
        print("[OK] JAPANESE TOPICS UPLOADED SUCCESSFULLY!")
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

