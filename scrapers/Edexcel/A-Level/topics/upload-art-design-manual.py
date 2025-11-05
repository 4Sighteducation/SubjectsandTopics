"""
Edexcel Art and Design (9AD0) - Manual Topic Upload
5 Endorsed titles with their disciplines and key knowledge areas

Structure:
- Level 0: 5 Endorsed titles
- Level 1: Disciplines within each title
- Level 2: Key knowledge/skills areas
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
    'code': '9AD0',
    'name': 'Art and Design',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Art%20and%20Design/2015/specification-and-sample-assessment-materials/gce-a-level-art-and-design-specification-issue-4.pdf'
}

# Structured topic data
TOPICS = [
    # Level 0: The 5 Endorsed Titles
    {
        'code': 'FineArt',
        'title': 'Fine Art (9FA0)',
        'level': 0,
        'parent': None
    },
    {
        'code': 'GraphicComm',
        'title': 'Graphic Communication (9GC0)',
        'level': 0,
        'parent': None
    },
    {
        'code': 'TextileDesign',
        'title': 'Textile Design (9TE0)',
        'level': 0,
        'parent': None
    },
    {
        'code': 'ThreeDDesign',
        'title': 'Three-dimensional Design (9TD0)',
        'level': 0,
        'parent': None
    },
    {
        'code': 'Photography',
        'title': 'Photography (9PY0)',
        'level': 0,
        'parent': None
    },
    
    # ========================================
    # FINE ART - Disciplines (Level 1)
    # ========================================
    {
        'code': 'FA.PaintDraw',
        'title': 'Painting and Drawing',
        'level': 1,
        'parent': 'FineArt'
    },
    {
        'code': 'FA.Printmaking',
        'title': 'Printmaking',
        'level': 1,
        'parent': 'FineArt'
    },
    {
        'code': 'FA.Sculpture',
        'title': 'Sculpture',
        'level': 1,
        'parent': 'FineArt'
    },
    {
        'code': 'FA.LensBased',
        'title': 'Lens-based Image Making',
        'level': 1,
        'parent': 'FineArt'
    },
    
    # Fine Art - Painting and Drawing (Level 2)
    {
        'code': 'FA.PaintDraw.Materials',
        'title': 'Characteristics of materials (plasticity, opacity, translucence, malleability, transparency)',
        'level': 2,
        'parent': 'FA.PaintDraw'
    },
    {
        'code': 'FA.PaintDraw.Colour',
        'title': 'Properties of colour (hue, tint, saturation, tone, colour perception)',
        'level': 2,
        'parent': 'FA.PaintDraw'
    },
    {
        'code': 'FA.PaintDraw.Media',
        'title': 'Materials and media (graphite, crayon, pastel, charcoal, ink, chalk, paint, dyes, software)',
        'level': 2,
        'parent': 'FA.PaintDraw'
    },
    {
        'code': 'FA.PaintDraw.Tools',
        'title': 'Range of tools and techniques (brushes, knives, sponges, digital, found objects)',
        'level': 2,
        'parent': 'FA.PaintDraw'
    },
    {
        'code': 'FA.PaintDraw.Combinations',
        'title': 'Exploring combinations (drawn/painted elements, collage, mixed media)',
        'level': 2,
        'parent': 'FA.PaintDraw'
    },
    
    # Fine Art - Printmaking (Level 2)
    {
        'code': 'FA.Print.Qualities',
        'title': 'Print qualities from different tools, materials and processes',
        'level': 2,
        'parent': 'FA.Printmaking'
    },
    {
        'code': 'FA.Print.Processes',
        'title': 'Printing processes (screen printing, intaglio, relief printing)',
        'level': 2,
        'parent': 'FA.Printmaking'
    },
    
    # Fine Art - Sculpture (Level 2)
    {
        'code': 'FA.Sculpt.3DForms',
        'title': 'Producing 3D forms (volume, space, materials, movement)',
        'level': 2,
        'parent': 'FA.Sculpture'
    },
    {
        'code': 'FA.Sculpt.Modelling',
        'title': 'Modelling techniques (clay, plaster, wax, 3D software)',
        'level': 2,
        'parent': 'FA.Sculpture'
    },
    {
        'code': 'FA.Sculpt.Carving',
        'title': 'Carving techniques (cutting and abrading)',
        'level': 2,
        'parent': 'FA.Sculpture'
    },
    {
        'code': 'FA.Sculpt.Construction',
        'title': 'Construction techniques (joining, soldering, welding, 3D printing)',
        'level': 2,
        'parent': 'FA.Sculpture'
    },
    {
        'code': 'FA.Sculpt.Materials',
        'title': 'Materials (wood, stone, plaster, clay, textiles, plastics, found objects)',
        'level': 2,
        'parent': 'FA.Sculpture'
    },
    
    # Fine Art - Lens-based (Level 2)
    {
        'code': 'FA.Lens.Production',
        'title': 'Production processes (mixed media, installation, montage, film, video, animation)',
        'level': 2,
        'parent': 'FA.LensBased'
    },
    {
        'code': 'FA.Lens.Elements',
        'title': 'Contributing elements (lighting, sets, environments, sound)',
        'level': 2,
        'parent': 'FA.LensBased'
    },
    {
        'code': 'FA.Lens.Formats',
        'title': 'Film and video formats (8mm, digital, HD, 4K, various file types)',
        'level': 2,
        'parent': 'FA.LensBased'
    },
    {
        'code': 'FA.Lens.Editing',
        'title': 'Editing techniques (in-camera, non-linear, compression, effects)',
        'level': 2,
        'parent': 'FA.LensBased'
    },
    
    # ========================================
    # GRAPHIC COMMUNICATION - Disciplines (Level 1)
    # ========================================
    {
        'code': 'GC.Advertising',
        'title': 'Advertising',
        'level': 1,
        'parent': 'GraphicComm'
    },
    {
        'code': 'GC.Illustration',
        'title': 'Illustration',
        'level': 1,
        'parent': 'GraphicComm'
    },
    {
        'code': 'GC.Branding',
        'title': 'Branding',
        'level': 1,
        'parent': 'GraphicComm'
    },
    {
        'code': 'GC.InfoDesign',
        'title': 'Information Design',
        'level': 1,
        'parent': 'GraphicComm'
    },
    
    # Graphic Communication - Advertising (Level 2)
    {
        'code': 'GC.Ad.Purpose',
        'title': 'Purpose and use (convey information, brand recognition, marketing strategies)',
        'level': 2,
        'parent': 'GC.Advertising'
    },
    {
        'code': 'GC.Ad.Context',
        'title': 'Design context (briefs, clients, audiences, digital advertising, social media)',
        'level': 2,
        'parent': 'GC.Advertising'
    },
    {
        'code': 'GC.Ad.Elements',
        'title': 'Images and typography (photography, animation, video)',
        'level': 2,
        'parent': 'GC.Advertising'
    },
    
    # Graphic Communication - Illustration (Level 2)
    {
        'code': 'GC.Illus.Narrative',
        'title': 'Illustration and narrative relationships',
        'level': 2,
        'parent': 'GC.Illustration'
    },
    {
        'code': 'GC.Illus.Briefs',
        'title': 'Briefs, clients and audiences',
        'level': 2,
        'parent': 'GC.Illustration'
    },
    {
        'code': 'GC.Illus.Digital',
        'title': 'Digital technology (photo-editing, vector software) with traditional processes',
        'level': 2,
        'parent': 'GC.Illustration'
    },
    {
        'code': 'GC.Illus.Purposes',
        'title': 'Variety of purposes (books, magazines, advertising, web-based, interactive)',
        'level': 2,
        'parent': 'GC.Illustration'
    },
    {
        'code': 'GC.Illus.Infographics',
        'title': 'Infographics (communicating data through charts and diagrams)',
        'level': 2,
        'parent': 'GC.Illustration'
    },
    
    # Graphic Communication - Branding (Level 2)
    {
        'code': 'GC.Brand.Packaging',
        'title': 'Packaging design (determined by contents, brand identity)',
        'level': 2,
        'parent': 'GC.Branding'
    },
    {
        'code': 'GC.Brand.Development',
        'title': 'Development (production drawings, 3D prototypes, sustainable materials)',
        'level': 2,
        'parent': 'GC.Branding'
    },
    {
        'code': 'GC.Brand.Surface',
        'title': 'Surface design (illustration, decoration, pattern)',
        'level': 2,
        'parent': 'GC.Branding'
    },
    {
        'code': 'GC.Brand.Legal',
        'title': 'Legal requirements (labeling, barcoding, tracking)',
        'level': 2,
        'parent': 'GC.Branding'
    },
    
    # Graphic Communication - Information Design (Level 2)
    {
        'code': 'GC.Info.Typography',
        'title': 'Typography (fonts, leading, kerning, alignment, justification)',
        'level': 2,
        'parent': 'GC.InfoDesign'
    },
    {
        'code': 'GC.Info.Digital',
        'title': 'Digital and print products (magazines, newspapers, web pages, leaflets, posters)',
        'level': 2,
        'parent': 'GC.InfoDesign'
    },
    {
        'code': 'GC.Info.3D',
        'title': '3D digital techniques (modelling, textures, lighting effects)',
        'level': 2,
        'parent': 'GC.InfoDesign'
    },
    {
        'code': 'GC.Info.TimeBased',
        'title': 'Moving image/time-based (storyboarding, sound, animation)',
        'level': 2,
        'parent': 'GC.InfoDesign'
    },
    {
        'code': 'GC.Info.Interface',
        'title': 'Interface design (navigation, symbols, control panels, user experience)',
        'level': 2,
        'parent': 'GC.InfoDesign'
    },
    
    # ========================================
    # TEXTILE DESIGN - Disciplines (Level 1)
    # ========================================
    {
        'code': 'TD.Interiors',
        'title': 'Textiles for Interiors',
        'level': 1,
        'parent': 'TextileDesign'
    },
    {
        'code': 'TD.FineArt',
        'title': 'Fine Art Textiles',
        'level': 1,
        'parent': 'TextileDesign'
    },
    {
        'code': 'TD.Fashion',
        'title': 'Fashion Textiles',
        'level': 1,
        'parent': 'TextileDesign'
    },
    
    # Textile Design - Interiors (Level 2)
    {
        'code': 'TD.Int.Design',
        'title': 'Design development (computer-generated ideas, colour, materials, construction)',
        'level': 2,
        'parent': 'TD.Interiors'
    },
    {
        'code': 'TD.Int.Techniques',
        'title': 'Construction techniques (weaving, knitting, embroidery, applique, felting)',
        'level': 2,
        'parent': 'TD.Interiors'
    },
    {
        'code': 'TD.Int.Printing',
        'title': 'Printing (croquis, repeat pattern, various print methods)',
        'level': 2,
        'parent': 'TD.Interiors'
    },
    {
        'code': 'TD.Int.Dyeing',
        'title': 'Dyeing techniques (batik, tie-dye, shibori, silk painting)',
        'level': 2,
        'parent': 'TD.Interiors'
    },
    
    # Textile Design - Fine Art (Level 2)
    {
        'code': 'TD.FA.Materials',
        'title': 'Range of materials and tools (including digital)',
        'level': 2,
        'parent': 'TD.FineArt'
    },
    {
        'code': 'TD.FA.Communication',
        'title': 'Communicating ideas through materials and formal elements',
        'level': 2,
        'parent': 'TD.FineArt'
    },
    {
        'code': 'TD.FA.Presentation',
        'title': 'Forms and presentation methods (audience response)',
        'level': 2,
        'parent': 'TD.FineArt'
    },
    {
        'code': 'TD.FA.Contemporary',
        'title': 'Contemporary practice (combining media and approaches)',
        'level': 2,
        'parent': 'TD.FineArt'
    },
    
    # Textile Design - Fashion (Level 2)
    {
        'code': 'TD.Fash.Creation',
        'title': 'Design creation (drawing, digital designs, toiles, samples)',
        'level': 2,
        'parent': 'TD.Fashion'
    },
    {
        'code': 'TD.Fash.Skills',
        'title': 'Technical skills (modelling, cutting, joining, embellishing)',
        'level': 2,
        'parent': 'TD.Fashion'
    },
    {
        'code': 'TD.Fash.Broader',
        'title': 'Broader fashion context (marketing, promotion, styling)',
        'level': 2,
        'parent': 'TD.Fashion'
    },
    
    # ========================================
    # THREE-DIMENSIONAL DESIGN - Disciplines (Level 1)
    # ========================================
    {
        'code': '3D.Spatial',
        'title': 'Spatial Design',
        'level': 1,
        'parent': 'ThreeDDesign'
    },
    {
        'code': '3D.Product',
        'title': 'Product Design',
        'level': 1,
        'parent': 'ThreeDDesign'
    },
    {
        'code': '3D.Crafts',
        'title': 'Design Crafts',
        'level': 1,
        'parent': 'ThreeDDesign'
    },
    
    # 3D Design - Spatial (Level 2)
    {
        'code': '3D.Sp.Scope',
        'title': 'Scope (performance spaces, interiors, exhibitions, architecture)',
        'level': 2,
        'parent': '3D.Spatial'
    },
    {
        'code': '3D.Sp.Development',
        'title': 'Development tools (scale drawings, models, plans, elevations, visualisations)',
        'level': 2,
        'parent': '3D.Spatial'
    },
    {
        'code': '3D.Sp.Production',
        'title': 'Production elements (text, sound, choreography, props, costumes)',
        'level': 2,
        'parent': '3D.Spatial'
    },
    {
        'code': '3D.Sp.Factors',
        'title': 'Influencing factors (public/private spaces, built environment)',
        'level': 2,
        'parent': '3D.Spatial'
    },
    {
        'code': '3D.Sp.Technology',
        'title': 'Technology (intelligent lighting, energy-saving, interactivity)',
        'level': 2,
        'parent': '3D.Spatial'
    },
    
    # 3D Design - Product (Level 2)
    {
        'code': '3D.Prod.Types',
        'title': 'Product types (mechanical, electronic, decorative)',
        'level': 2,
        'parent': '3D.Product'
    },
    {
        'code': '3D.Prod.Development',
        'title': 'Development (drawing, CAD, maquettes, prototypes, models)',
        'level': 2,
        'parent': '3D.Product'
    },
    {
        'code': '3D.Prod.Modelling',
        'title': 'Modelling and materials (real/virtual, various materials and processes)',
        'level': 2,
        'parent': '3D.Product'
    },
    {
        'code': '3D.Prod.Factors',
        'title': 'Design factors (interface, portability, maintainability, miniaturisation)',
        'level': 2,
        'parent': '3D.Product'
    },
    {
        'code': '3D.Prod.Market',
        'title': 'Market context (branding, market position, customer relations)',
        'level': 2,
        'parent': '3D.Product'
    },
    {
        'code': '3D.Prod.Production',
        'title': 'Production methods (batch, mass production, industrial methods)',
        'level': 2,
        'parent': '3D.Product'
    },
    
    # 3D Design - Crafts (Level 2)
    {
        'code': '3D.Craft.Materials',
        'title': 'Materials and processes (clay, wood, plastic, glass, metal, textiles)',
        'level': 2,
        'parent': '3D.Crafts'
    },
    {
        'code': '3D.Craft.Artefacts',
        'title': 'Craft artefacts (jewellery, furniture, lighting, containers, toys)',
        'level': 2,
        'parent': '3D.Crafts'
    },
    {
        'code': '3D.Craft.Combinations',
        'title': 'Combining materials in artefact production',
        'level': 2,
        'parent': '3D.Crafts'
    },
    {
        'code': '3D.Craft.Market',
        'title': 'Routes to market (specialist shops, events, exhibitions, online)',
        'level': 2,
        'parent': '3D.Crafts'
    },
    {
        'code': '3D.Craft.Commission',
        'title': 'Commissioned pieces (specific locations, clients, organisations)',
        'level': 2,
        'parent': '3D.Crafts'
    },
    
    # ========================================
    # PHOTOGRAPHY - Disciplines (Level 1)
    # ========================================
    {
        'code': 'PH.Film',
        'title': 'Film-based Photography',
        'level': 1,
        'parent': 'Photography'
    },
    {
        'code': 'PH.Digital',
        'title': 'Digital Photography',
        'level': 1,
        'parent': 'Photography'
    },
    {
        'code': 'PH.Video',
        'title': 'Film and Video',
        'level': 1,
        'parent': 'Photography'
    },
    
    # Photography - Film-based (Level 2)
    {
        'code': 'PH.Film.Types',
        'title': 'Film types and speeds (specialised films, pushing/pulling, reciprocity)',
        'level': 2,
        'parent': 'PH.Film'
    },
    {
        'code': 'PH.Film.Camera',
        'title': 'Camera techniques (viewpoint, composition, focus, aperture, shutter speed, exposure)',
        'level': 2,
        'parent': 'PH.Film'
    },
    {
        'code': 'PH.Film.Darkroom',
        'title': 'Darkroom techniques (paper types, developing, printing, tone, contrast)',
        'level': 2,
        'parent': 'PH.Film'
    },
    {
        'code': 'PH.Film.Techniques',
        'title': 'Special techniques (polarisation, solarisation, photograms, photomontage)',
        'level': 2,
        'parent': 'PH.Film'
    },
    {
        'code': 'PH.Film.Digital',
        'title': 'Digital processing (scanners, computers, manipulation software)',
        'level': 2,
        'parent': 'PH.Film'
    },
    
    # Photography - Digital (Level 2)
    {
        'code': 'PH.Dig.Principles',
        'title': 'Digital principles (pixels, digital processing)',
        'level': 2,
        'parent': 'PH.Digital'
    },
    {
        'code': 'PH.Dig.Camera',
        'title': 'Camera techniques (viewpoint, white balance, composition, shooting modes, histograms)',
        'level': 2,
        'parent': 'PH.Digital'
    },
    {
        'code': 'PH.Dig.Software',
        'title': 'Hardware and software (image acquisition, manipulation)',
        'level': 2,
        'parent': 'PH.Digital'
    },
    {
        'code': 'PH.Dig.Colour',
        'title': 'Colour and tone (screen calibration, colour gamut, file formats)',
        'level': 2,
        'parent': 'PH.Digital'
    },
    
    # Photography - Film and Video (Level 2)
    {
        'code': 'PH.Vid.Planning',
        'title': 'Planning (synopsis, storyboards, scripting, camera angles, shot length)',
        'level': 2,
        'parent': 'PH.Video'
    },
    {
        'code': 'PH.Vid.Animation',
        'title': 'Animation processes (stop-frame, rostrum, 3D modelling)',
        'level': 2,
        'parent': 'PH.Video'
    },
    {
        'code': 'PH.Vid.Formats',
        'title': 'Formats and quality (8mm, analogue, digital, HD, 4K, file types)',
        'level': 2,
        'parent': 'PH.Video'
    },
    {
        'code': 'PH.Vid.Sound',
        'title': 'Sound and narrative (narration, storyline, relation to moving images)',
        'level': 2,
        'parent': 'PH.Video'
    },
    {
        'code': 'PH.Vid.Editing',
        'title': 'Editing techniques (in-camera, non-linear, compression, effects)',
        'level': 2,
        'parent': 'PH.Video'
    }
]


def upload_art_design_topics():
    """Upload Art and Design topics to Supabase."""
    
    print("=" * 80)
    print("EDEXCEL ART AND DESIGN (9AD0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("\n5 Endorsed titles with disciplines and key knowledge areas\n")
    
    try:
        # Get/create subject
        print("Creating/updating subject...")
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
        print("\nClearing old topics...")
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared")
        
        # Insert new topics
        print(f"\nUploading {len(TOPICS)} topics...")
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
        print("\nLinking parent-child relationships...")
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
        print("[OK] ART AND DESIGN TOPICS UPLOADED SUCCESSFULLY!")
        print("=" * 80)
        
        # Show hierarchy breakdown
        levels = {}
        for t in TOPICS:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("\nHierarchy:")
        print(f"   Level 0 (Endorsed Titles): {levels.get(0, 0)}")
        print(f"   Level 1 (Disciplines): {levels.get(1, 0)}")
        print(f"   Level 2 (Knowledge Areas): {levels.get(2, 0)}")
        print(f"\n   Total: {len(TOPICS)} topics")
        
        # Show sample structure
        print("\nSample structure:")
        print("   - Fine Art (9FA0)")
        print("       - Painting and Drawing")
        print("           - Characteristics of materials")
        print("           - Properties of colour")
        print("       - Printmaking")
        print("       - Sculpture")
        print("       - Lens-based Image Making")
        
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
    
    success = upload_art_design_topics()
    sys.exit(0 if success else 1)

