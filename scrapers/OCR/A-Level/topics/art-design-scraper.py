"""
Quick scraper for OCR Art and Design - Manual structure
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

# Art & Design structure
ART_DESIGN_STRUCTURE = {
    "H600": {
        "title": "Art, craft and design (H600)",
        "areas": [
            "Fine Art: areas of study such as painting, printmaking or sculpture",
            "Graphic Communication: areas of study such as illustration, packaging or advertising",
            "Photography: areas of study such as traditional, digital or moving image",
            "Textile Design: areas of study such as printed and digital textiles, fashion design or constructed textiles",
            "Three-Dimensional Design: areas of study such as ceramics, product design or jewellery",
            "Critical and Contextual Studies: areas of study such as art theory, artistic movements or architecture"
        ]
    },
    "H601": {
        "title": "Fine art (H601)",
        "areas": [
            "Portraiture", "Landscape", "Still life", "Human form", "Abstraction",
            "Experimental imagery", "Narrative", "Installation", "Working in a genre"
        ]
    },
    "H602": {
        "title": "Graphic communication (H602)",
        "areas": [
            "Image and typography", "Illustration", "Advertising", "Layout design",
            "Packaging", "Editorial design", "Experimental imagery", "Signage", "Abstract approaches"
        ]
    },
    "H603": {
        "title": "Photography (H603)",
        "areas": [
            "Portraiture", "Landscape photography", "Commercial photography", "Still life photography",
            "Documentary photography", "Experimental imagery", "Editorial photography",
            "Photographic installation", "The photographic process", "Moving image", "Animation"
        ]
    },
    "H604": {
        "title": "Textile design (H604)",
        "areas": [
            "Garments/Fashion", "Accessories", "Soft furnishings", "Printed and/or dyed textiles",
            "Constructed textiles", "Textile installation", "Expressive textiles", "Digital textiles"
        ]
    },
    "H605": {
        "title": "Three-dimensional design (H605)",
        "areas": [
            "Craft or commercial ceramics",
            "Commercial sculptures or sculptural commissions",
            "Commercial three-dimensional design, working for a client",
            "Design and/or construction for television, games or film",
            "Stage, environmental or architectural design and/or construction",
            "Experimental three-dimensional design",
            "Body ornament (jewellery, fashion accessories)",
            "Product design and realisation",
            "Constructions in a range of materials"
        ]
    },
    "H606": {
        "title": "Critical and contextual studies (H606)",
        "areas": [
            "Fine art and sculpture", "Design", "Craft", "Art theory", "The human form",
            "Landscape and natural forms", "Still life and designed objects",
            "Architecture and the built environment", "Art movements, styles and genres",
            "Curating exhibitions", "Art management and art in the community",
            "Cultural representations within art and design",
            "Multimedia, emerging technologies and their use in art"
        ]
    }
}

def upload_art_design():
    """Upload Art & Design structure."""
    print("=" * 80)
    print("OCR ART & DESIGN - Manual Structure Upload")
    print("=" * 80)
    
    # Get subject
    subject_result = supabase.table('staging_aqa_subjects').upsert({
        'subject_name': 'Art and Design (A-Level)',
        'subject_code': 'H600',
        'qualification_type': 'A-Level',
        'specification_url': 'https://www.ocr.org.uk/Images/170210-specification-accredited-a-level-gce-art-and-design-h600-h606.pdf',
        'exam_board': 'OCR'
    }, on_conflict='subject_code,qualification_type,exam_board').execute()
    
    subject_id = subject_result.data[0]['id']
    print(f"[OK] Subject ID: {subject_id}")
    
    # Clear old
    supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
    print("[OK] Cleared old topics")
    
    # Build topics
    topics = []
    
    for code, info in ART_DESIGN_STRUCTURE.items():
        # Add specialism (L0)
        specialism_code = code
        topics.append({
            'subject_id': subject_id,
            'topic_code': specialism_code,
            'topic_name': info['title'],
            'topic_level': 0,
            'exam_board': 'OCR'
        })
        print(f"[L0] {specialism_code}: {info['title']}")
        
        # Add areas of study (L1)
        for i, area in enumerate(info['areas'], 1):
            topics.append({
                'subject_id': subject_id,
                'topic_code': f'{specialism_code}_{i}',
                'topic_name': area,
                'topic_level': 1,
                'exam_board': 'OCR'
            })
    
    # Insert
    inserted_result = supabase.table('staging_aqa_topics').insert(topics).execute()
    print(f"[OK] Uploaded {len(inserted_result.data)} topics")
    
    # Link hierarchy
    code_to_id = {t['topic_code']: t['id'] for t in inserted_result.data}
    linked = 0
    
    for topic in topics:
        code = topic['topic_code']
        if '_' in code:  # Has parent
            parent_code = code.split('_')[0]
            parent_id = code_to_id.get(parent_code)
            child_id = code_to_id.get(code)
            if parent_id and child_id:
                supabase.table('staging_aqa_topics').update({
                    'parent_topic_id': parent_id
                }).eq('id', child_id).execute()
                linked += 1
    
    print(f"[OK] Linked {linked} relationships")
    
    # Stats
    l0 = len([t for t in topics if t['topic_level'] == 0])
    l1 = len([t for t in topics if t['topic_level'] == 1])
    
    print(f"\n[SUCCESS] ✅")
    print(f"  Level 0 (Specialisms): {l0}")
    print(f"  Level 1 (Areas of Study): {l1}")
    print(f"  Total: {len(topics)}")

if __name__ == '__main__':
    upload_art_design()

