"""
Edexcel Turkish (9TU0) - Manual Topic Upload
Complete hierarchy with themes, sub-themes, and aspects.
Turkish text preserved with English translations.
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
    'code': '9TU0',
    'name': 'Turkish (listening, reading and writing)',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Turkish/2018/specification-and-sample-assessments/A-level-Turkish-Specification11.pdf'
}

TOPICS = [
    # Level 0: Papers
    {'code': 'Paper1', 'title': 'Paper 1: Listening, Reading and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper2', 'title': 'Paper 2: Written Response to Works and Translation', 'level': 0, 'parent': None},
    {'code': 'Paper3', 'title': 'Paper 3: Listening, Reading and Writing', 'level': 0, 'parent': None},
    
    # ==================================================================================
    # THEME 1: Türk toplumunda değişim
    # ==================================================================================
    {'code': 'Theme1', 'title': '1. Konu: Türk toplumunda değişim (Theme 1: Change in Turkish Society)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 1.1
    {'code': 'T1-1', 'title': 'Aile ve İlişkiler (Family and Relationships)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-1-1', 'title': 'Aile yaşamı ve bireylerinin rollerindeki değişiklikler (changes in family life and individual roles)', 'level': 3, 'parent': 'T1-1'},
    {'code': 'T1-1-2', 'title': 'evlilik ve boşanmaya karşı gösterilen tutumun değişmesi (changing attitudes towards marriage and divorce)', 'level': 3, 'parent': 'T1-1'},
    {'code': 'T1-1-3', 'title': 'aile bireylerinin sayısındaki değişim (change in the number of family members)', 'level': 3, 'parent': 'T1-1'},
    
    # Sub-theme 1.2
    {'code': 'T1-2', 'title': 'İş dünyası (The Business World)', 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-2-1', 'title': 'Genç nesil ve istihdam (youth and employment)', 'level': 3, 'parent': 'T1-2'},
    {'code': 'T1-2-2', 'title': 'gençler için mesleki eğitim (vocational education for young people)', 'level': 3, 'parent': 'T1-2'},
    {'code': 'T1-2-3', 'title': "kadınların iş yaşamındaki yeri (women's place in working life)", 'level': 3, 'parent': 'T1-2'},
    
    # Research Topic 1
    {'code': 'T1-R', 'title': "Araştırma Konusu: Türkiye'de eğitim fırsatları (Research: Educational Opportunities in Turkey)", 'level': 2, 'parent': 'Theme1'},
    {'code': 'T1-R-1', 'title': 'Eğitim sisteminde özel ve devlet okulları arasındaki farklar (differences between private and state schools)', 'level': 3, 'parent': 'T1-R'},
    {'code': 'T1-R-2', 'title': 'zihinsel ve bedensel engellilerin eğitimi (education of mentally and physically disabled)', 'level': 3, 'parent': 'T1-R'},
    {'code': 'T1-R-3', 'title': 'kentsel ve kırsal bölgelerde eğitim imkanları (educational opportunities in urban and rural areas)', 'level': 3, 'parent': 'T1-R'},
    
    # ==================================================================================
    # THEME 2: Türkiye ve Kıbrıs'ta Sanat ve Kültür
    # ==================================================================================
    {'code': 'Theme2', 'title': "2. Konu: Türkiye ve Kıbrıs'ta Sanat ve Kültür (Theme 2: Art and Culture in Turkey and Cyprus)", 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 2.1
    {'code': 'T2-1', 'title': 'Modern kültür ve medya (Modern Culture and Media)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-1-1', 'title': 'Televizyon (television)', 'level': 3, 'parent': 'T2-1'},
    {'code': 'T2-1-2', 'title': 'çağdaş sanat (contemporary art)', 'level': 3, 'parent': 'T2-1'},
    {'code': 'T2-1-3', 'title': 'teknolojinin kültürel etkinlikler üzerindeki etkisi (impact of technology on cultural activities)', 'level': 3, 'parent': 'T2-1'},
    
    # Sub-theme 2.2
    {'code': 'T2-2', 'title': 'Geleneksel sanat kültürü (Traditional Art Culture)', 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-2-1', 'title': 'Geleneksel tiyatro (traditional theatre)', 'level': 3, 'parent': 'T2-2'},
    {'code': 'T2-2-2', 'title': 'geleneksel müzik (traditional music)', 'level': 3, 'parent': 'T2-2'},
    {'code': 'T2-2-3', 'title': 'geleneksel el sanatları (traditional handicrafts)', 'level': 3, 'parent': 'T2-2'},
    
    # Research Topic 2
    {'code': 'T2-R', 'title': "Araştırma Konusu: Geleneksel kutlamaların Türkiye'de veya Kıbrıs'ta değişmesi (Research: Changing Traditional Celebrations)", 'level': 2, 'parent': 'Theme2'},
    {'code': 'T2-R-1', 'title': 'Günümüzdeki geleneksel kutlamalar (traditional celebrations today)', 'level': 3, 'parent': 'T2-R'},
    {'code': 'T2-R-2', 'title': 'modern yaşamın geleneksel kutlamalar üzerindeki etkisi (impact of modern life on traditional celebrations)', 'level': 3, 'parent': 'T2-R'},
    {'code': 'T2-R-3', 'title': 'geleneksel kutlamaların ülke yaşamındaki önemi (importance of traditional celebrations in national life)', 'level': 3, 'parent': 'T2-R'},
    
    # ==================================================================================
    # THEME 3: Türkiye üzerinde görüşler
    # ==================================================================================
    {'code': 'Theme3', 'title': '3. Konu: Türkiye üzerinde görüşler (Theme 3: Views on Turkey)', 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 3.1
    {'code': 'T3-1', 'title': 'Beşeri Coğrafya (Human Geography)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-1-1', 'title': 'Yaşam standartları ve hayat kalitesinde değişim (changes in living standards and quality of life)', 'level': 3, 'parent': 'T3-1'},
    {'code': 'T3-1-2', 'title': 'kırsal ve kentsel kesim ayrımı (rural and urban division)', 'level': 3, 'parent': 'T3-1'},
    {'code': 'T3-1-3', 'title': 'kırsal kesimden kente göç (migration from rural to urban areas)', 'level': 3, 'parent': 'T3-1'},
    
    # Sub-theme 3.2
    {'code': 'T3-2', 'title': 'Çevre (Environment)', 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-2-1', 'title': 'Çevre sorunlarına karşı değişen tutumlar (changing attitudes towards environmental problems)', 'level': 3, 'parent': 'T3-2'},
    {'code': 'T3-2-2', 'title': 'doğal kaynakların korunması (conservation of natural resources)', 'level': 3, 'parent': 'T3-2'},
    {'code': 'T3-2-3', 'title': 'endüstrileşme ve kentleşmenin çevre üzerinde olumlu ve olumsuz etkileri (positive and negative effects of industrialization and urbanization on environment)', 'level': 3, 'parent': 'T3-2'},
    
    # Research Topic 3
    {'code': 'T3-R', 'title': "Araştırma Konusu: Türkiye'de Turizm (Research: Tourism in Turkey)", 'level': 2, 'parent': 'Theme3'},
    {'code': 'T3-R-1', 'title': 'Turizmin ekonomi üzerindeki etkisi (impact of tourism on the economy)', 'level': 3, 'parent': 'T3-R'},
    {'code': 'T3-R-2', 'title': 'turizmin yerel halk için yararları ve zararları (benefits and harms of tourism for local people)', 'level': 3, 'parent': 'T3-R'},
    {'code': 'T3-R-3', 'title': "Türkiye'de turizmi teşvik amacıyla yapılan yatırımlar (investments to promote tourism in Turkey)", 'level': 3, 'parent': 'T3-R'},
    
    # ==================================================================================
    # THEME 4: Türkiye'de siyasal konular
    # ==================================================================================
    {'code': 'Theme4', 'title': "4. Konu: Türkiye'de siyasal konular (Theme 4: Political Issues in Turkey)", 'level': 1, 'parent': 'Paper1'},
    
    # Sub-theme 4.1
    {'code': 'T4-1', 'title': "Türkiye'de Atatürk devrimleri (Atatürk Revolutions in Turkey)", 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-1-1', 'title': "Türkiye Cumhuriyetinin kuruluşu (establishment of the Republic of Turkey)", 'level': 3, 'parent': 'T4-1'},
    {'code': 'T4-1-2', 'title': "Atatürk'ün Türk dili üzerindeki değişimlere etkisi (Atatürk's influence on changes in the Turkish language)", 'level': 3, 'parent': 'T4-1'},
    {'code': 'T4-1-3', 'title': 'Atatürk öncülüğünde daha eşit bir topluma yönelik çıkarılan yasalar (laws enacted under Atatürk for a more equal society)', 'level': 3, 'parent': 'T4-1'},
    
    # Sub-theme 4.2
    {'code': 'T4-2', 'title': 'Siyasal alan (Political Arena)', 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-2-1', 'title': 'Başlıca siyasi partiler ve gündemleri (main political parties and their agendas)', 'level': 3, 'parent': 'T4-2'},
    {'code': 'T4-2-2', 'title': 'ekonomiyi geliştirmek için hükümetin girişimleri (government initiatives to develop the economy)', 'level': 3, 'parent': 'T4-2'},
    {'code': 'T4-2-3', 'title': 'siyasette kadınlar (women in politics)', 'level': 3, 'parent': 'T4-2'},
    
    # Research Topic 4
    {'code': 'T4-R', 'title': "Araştırma Konusu: 2015'ten beri Türkiye'deki mülteciler (Research: Refugees in Turkey Since 2015)", 'level': 2, 'parent': 'Theme4'},
    {'code': 'T4-R-1', 'title': "Mültecilerin Türkiye'ye geliş nedenleri (reasons for refugees coming to Turkey)", 'level': 3, 'parent': 'T4-R'},
    {'code': 'T4-R-2', 'title': 'Türkler ve mülteciler arasındaki ilişkiler (relations between Turks and refugees)', 'level': 3, 'parent': 'T4-R'},
    {'code': 'T4-R-3', 'title': 'hükümetin ve diğer kuruluşların yardımları (assistance from government and other organizations)', 'level': 3, 'parent': 'T4-R'},
]


def upload_topics():
    """Upload Turkish topics to Supabase."""
    
    print("=" * 80)
    print("EDEXCEL TURKISH (9TU0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("\nComplete hierarchy with Turkish text + English translations\n")
    
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
        print("[OK] TURKISH TOPICS UPLOADED SUCCESSFULLY!")
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











