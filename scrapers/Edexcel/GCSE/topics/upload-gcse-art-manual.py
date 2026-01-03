"""
GCSE Art and Design - PROPER Manual Upload
Each of the 5 titles has DIFFERENT areas of study with bullet point descriptions
Level 0: 5 Art Titles
Level 1: Areas of Study (specific to each title)
Level 2: Bullet point descriptions under each area
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
    'code': 'GCSE-Art',
    'name': 'Art and Design',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Art%20and%20Design/2016/specification-and-sample-assessments/specification-gcse-art-design-2016-spec.pdf'
}

TOPICS = [
    # ==================================================================================
    # TITLE 1: ART, CRAFT AND DESIGN
    # ==================================================================================
    {'code': 'Title1', 'title': 'Art, Craft and Design', 'level': 0, 'parent': None},
    
    # Areas of Study for Title 1
    {'code': 'T1-Drawing', 'title': 'Drawing', 'level': 1, 'parent': 'Title1'},
    {'code': 'T1-Drawing-1', 'title': 'Use of expressive and descriptive mark-making to record and communicate ideas', 'level': 2, 'parent': 'T1-Drawing'},
    {'code': 'T1-Drawing-2', 'title': 'Range of drawing materials and techniques (graphite, pastel, charcoal, ink, chalk, digital)', 'level': 2, 'parent': 'T1-Drawing'},
    
    {'code': 'T1-Installation', 'title': 'Installation', 'level': 1, 'parent': 'Title1'},
    {'code': 'T1-Installation-1', 'title': 'Use of controlled environments to create atmosphere and communicate ideas', 'level': 2, 'parent': 'T1-Installation'},
    {'code': 'T1-Installation-2', 'title': 'Range of installation materials (film, projection, objects, text, audio, lighting)', 'level': 2, 'parent': 'T1-Installation'},
    
    {'code': 'T1-Lens', 'title': 'Lens-based and light-based media', 'level': 1, 'parent': 'Title1'},
    {'code': 'T1-Painting', 'title': 'Painting', 'level': 1, 'parent': 'Title1'},
    {'code': 'T1-Photography', 'title': 'Photography', 'level': 1, 'parent': 'Title1'},
    {'code': 'T1-Printmaking', 'title': 'Printmaking', 'level': 1, 'parent': 'Title1'},
    {'code': 'T1-Sculpture', 'title': 'Sculpture', 'level': 1, 'parent': 'Title1'},
    {'code': 'T1-3D', 'title': 'Three-dimensional design', 'level': 1, 'parent': 'Title1'},
    
    # ==================================================================================
    # TITLE 2: FINE ART
    # ==================================================================================
    {'code': 'Title2', 'title': 'Fine Art', 'level': 0, 'parent': None},
    
    {'code': 'T2-Drawing', 'title': 'Drawing', 'level': 1, 'parent': 'Title2'},
    {'code': 'T2-Installation', 'title': 'Installation', 'level': 1, 'parent': 'Title2'},
    {'code': 'T2-Lens', 'title': 'Lens-based and light-based media', 'level': 1, 'parent': 'Title2'},
    {'code': 'T2-Painting', 'title': 'Painting', 'level': 1, 'parent': 'Title2'},
    {'code': 'T2-Photography', 'title': 'Photography', 'level': 1, 'parent': 'Title2'},
    {'code': 'T2-Printmaking', 'title': 'Printmaking', 'level': 1, 'parent': 'Title2'},
    {'code': 'T2-Sculpture', 'title': 'Sculpture', 'level': 1, 'parent': 'Title2'},
    {'code': 'T2-3D', 'title': 'Three-dimensional design', 'level': 1, 'parent': 'Title2'},
    
    # ==================================================================================
    # TITLE 3: GRAPHIC COMMUNICATION
    # ==================================================================================
    {'code': 'Title3', 'title': 'Graphic Communication', 'level': 0, 'parent': None},
    
    # Areas specific to Graphic Communication
    {'code': 'T3-Advertising', 'title': 'Advertising', 'level': 1, 'parent': 'Title3'},
    {'code': 'T3-Advertising-1', 'title': 'Use of advertising to convey information and promote corporate identity', 'level': 2, 'parent': 'T3-Advertising'},
    {'code': 'T3-Advertising-2', 'title': 'Traditional graphic media and current technology', 'level': 2, 'parent': 'T3-Advertising'},
    
    {'code': 'T3-CommGraphics', 'title': 'Communication graphics', 'level': 1, 'parent': 'Title3'},
    {'code': 'T3-CommGraphics-1', 'title': 'Communication through graphics for worldwide identity', 'level': 2, 'parent': 'T3-CommGraphics'},
    {'code': 'T3-CommGraphics-2', 'title': 'Traditional and digital graphic media in 2D and 3D', 'level': 2, 'parent': 'T3-CommGraphics'},
    
    {'code': 'T3-Print', 'title': 'Design for print', 'level': 1, 'parent': 'Title3'},
    {'code': 'T3-Print-1', 'title': 'Design-based solutions for visual and written material for public distribution', 'level': 2, 'parent': 'T3-Print'},
    {'code': 'T3-Print-2', 'title': 'Traditional print and digital technology', 'level': 2, 'parent': 'T3-Print'},
    
    {'code': 'T3-Illustration', 'title': 'Illustration', 'level': 1, 'parent': 'Title3'},
    {'code': 'T3-Illustration-1', 'title': 'Illustration and narrative to communicate factual, fictional and technical ideas', 'level': 2, 'parent': 'T3-Illustration'},
    {'code': 'T3-Illustration-2', 'title': 'Range of illustration materials and techniques (digital, wet/dry processes, drawing, painting, printing)', 'level': 2, 'parent': 'T3-Illustration'},
    
    {'code': 'T3-Interactive', 'title': 'Interactive design (web, app and game)', 'level': 1, 'parent': 'Title3'},
    {'code': 'T3-Interactive-1', 'title': 'Interactive technology to communicate and engage audiences (web, mobile, TV, games)', 'level': 2, 'parent': 'T3-Interactive'},
    {'code': 'T3-Interactive-2', 'title': 'Range of interactive design materials (2D/3D graphics, digital apps, time-based media)', 'level': 2, 'parent': 'T3-Interactive'},
    
    {'code': 'T3-Multimedia', 'title': 'Multi-media', 'level': 1, 'parent': 'Title3'},
    {'code': 'T3-Multimedia-1', 'title': 'Traditional and non-traditional media for range of purposes and audiences', 'level': 2, 'parent': 'T3-Multimedia'},
    {'code': 'T3-Multimedia-2', 'title': 'Combination of materials (motion graphics, video, animation, screen-based technology)', 'level': 2, 'parent': 'T3-Multimedia'},
    
    {'code': 'T3-Package', 'title': 'Package design', 'level': 1, 'parent': 'Title3'},
    {'code': 'T3-Package-1', 'title': 'Functional 3D design to protect, promote and communicate brand identity', 'level': 2, 'parent': 'T3-Package'},
    {'code': 'T3-Package-2', 'title': 'Range of package materials and construction processes', 'level': 2, 'parent': 'T3-Package'},
    
    {'code': 'T3-Signage', 'title': 'Signage', 'level': 1, 'parent': 'Title3'},
    {'code': 'T3-Signage-1', 'title': 'Development of signage with specific and worldwide application', 'level': 2, 'parent': 'T3-Signage'},
    {'code': 'T3-Signage-2', 'title': 'Digital and non-digital methods of making symbols and signs', 'level': 2, 'parent': 'T3-Signage'},
    
    {'code': 'T3-Typography', 'title': 'Typography', 'level': 1, 'parent': 'Title3'},
    {'code': 'T3-Typography-1', 'title': 'Arrangement and manipulation of type to communicate ideas and create visual interest', 'level': 2, 'parent': 'T3-Typography'},
    {'code': 'T3-Typography-2', 'title': 'Range of typographic materials and techniques (letter forms, fonts, digital/non-digital)', 'level': 2, 'parent': 'T3-Typography'},
    
    # ==================================================================================
    # TITLE 4: TEXTILE DESIGN
    # ==================================================================================
    {'code': 'Title4', 'title': 'Textile Design', 'level': 0, 'parent': None},
    
    {'code': 'T4-Constructed', 'title': 'Constructed textiles', 'level': 1, 'parent': 'Title4'},
    {'code': 'T4-Digital', 'title': 'Digital textiles', 'level': 1, 'parent': 'Title4'},
    {'code': 'T4-Dyed', 'title': 'Printed and dyed textiles', 'level': 1, 'parent': 'Title4'},
    {'code': 'T4-Fashion', 'title': 'Fashion design and illustration', 'level': 1, 'parent': 'Title4'},
    
    # ==================================================================================
    # TITLE 5: THREE-DIMENSIONAL DESIGN
    # ==================================================================================
    {'code': 'Title5', 'title': 'Three-dimensional Design', 'level': 0, 'parent': None},
    
    {'code': 'T5-Architectural', 'title': 'Architectural design', 'level': 1, 'parent': 'Title5'},
    {'code': 'T5-Ceramic', 'title': 'Ceramic design', 'level': 1, 'parent': 'Title5'},
    {'code': 'T5-Environmental', 'title': 'Environmental/landscape/garden design', 'level': 1, 'parent': 'Title5'},
    {'code': 'T5-Exhibition', 'title': 'Exhibition design', 'level': 1, 'parent': 'Title5'},
    {'code': 'T5-Interior', 'title': 'Interior design', 'level': 1, 'parent': 'Title5'},
    {'code': 'T5-Product', 'title': 'Product design', 'level': 1, 'parent': 'Title5'},
    {'code': 'T5-Theatre', 'title': 'Theatre, film and television design', 'level': 1, 'parent': 'Title5'},
]


def upload_topics():
    """Upload GCSE Art topics."""
    
    print("=" * 80)
    print("GCSE ART AND DESIGN - PROPER MANUAL UPLOAD")
    print("=" * 80)
    print(f"5 Titles with DIFFERENT areas of study each\n")
    
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
        print("[OK] GCSE ART AND DESIGN UPLOADED!")
        print("=" * 80)
        print(f"\n   Level 0 (Titles): {levels.get(0, 0)}")
        print(f"   Level 1 (Areas): {levels.get(1, 0)}")
        print(f"   Level 2 (Descriptions): {levels.get(2, 0)}")
        print(f"\n   Total: {len(TOPICS)} topics")
        print("\nEach title has its own specific areas of study!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    upload_topics()

