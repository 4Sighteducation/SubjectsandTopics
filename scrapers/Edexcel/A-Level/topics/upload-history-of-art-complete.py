"""
Edexcel History of Art (9HT0) - Complete Manual Upload
Structure:
  Paper 1: Visual Analysis + 3 Themes (choose 2)
  Paper 2: 5 Periods (choose 2)
  
Each Theme and Period has detailed content with prescribed works
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
    'code': '9HT0',
    'name': 'History of Art',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/history-of-art/2017/specification-and-sample-assessments/specification-and-sample-assessments-GCE-HISOFART-SPEC.pdf'
}

TOPICS = [
    # ==================================================================================
    # LEVEL 0: PAPERS
    # ==================================================================================
    {'code': 'Paper1', 'title': 'Paper 1: Visual Analysis and Themes', 'level': 0, 'parent': None},
    {'code': 'Paper2', 'title': 'Paper 2: Periods', 'level': 0, 'parent': None},
    
    # ==================================================================================
    # PAPER 1 - SECTION A: VISUAL ANALYSIS
    # ==================================================================================
    {'code': 'P1-VisualAnalysis', 'title': 'Section A: Visual Analysis', 'level': 1, 'parent': 'Paper1'},
    
    {'code': 'P1-VA-Painting', 'title': 'Visual analysis of a painting', 'level': 2, 'parent': 'P1-VisualAnalysis'},
    {'code': 'P1-VA-Sculpture', 'title': 'Visual analysis of a sculpture', 'level': 2, 'parent': 'P1-VisualAnalysis'},
    {'code': 'P1-VA-Building', 'title': 'Visual analysis of a building', 'level': 2, 'parent': 'P1-VisualAnalysis'},
    
    # ==================================================================================
    # PAPER 1 - SECTION B: THEMES (Choose 2 from 3)
    # ==================================================================================
    {'code': 'P1-Themes', 'title': 'Section B: Themes (Choose 2 from 3)', 'level': 1, 'parent': 'Paper1'},
    
    # Theme B1: Nature in art and architecture
    {'code': 'B1', 'title': 'Theme B1: Nature in Art and Architecture', 'level': 2, 'parent': 'P1-Themes'},
    {'code': 'B1-1', 'title': 'Key Topic 1: Nature as a source of materials and/or processes', 'level': 3, 'parent': 'B1'},
    {'code': 'B1-2', 'title': 'Key Topic 2: Nature as a subject', 'level': 3, 'parent': 'B1'},
    {'code': 'B1-3', 'title': 'Key Topic 3: Art and architecture inspired by nature', 'level': 3, 'parent': 'B1'},
    {'code': 'B1-4', 'title': 'Key Topic 4: Critical concepts (the sublime, pastoral and picturesque, landscape as propaganda)', 'level': 3, 'parent': 'B1'},
    
    # Prescribed works for B1
    {'code': 'B1-Works', 'title': 'Prescribed Works (2 specified artists + 1 architect + other works)', 'level': 3, 'parent': 'B1'},
    {'code': 'B1-W-Pre1850', 'title': 'Pre-1850 works (2D, 3D, Architecture)', 'level': 4, 'parent': 'B1-Works'},
    {'code': 'B1-W-Post1850', 'title': 'Post-1850 works (2D, 3D, Architecture)', 'level': 4, 'parent': 'B1-Works'},
    
    # Theme B2: Identities in art and architecture
    {'code': 'B2', 'title': 'Theme B2: Identities in Art and Architecture', 'level': 2, 'parent': 'P1-Themes'},
    {'code': 'B2-1', 'title': 'Key Topic 1: The individual', 'level': 3, 'parent': 'B2'},
    {'code': 'B2-2', 'title': 'Key Topic 2: The body in art and architecture', 'level': 3, 'parent': 'B2'},
    {'code': 'B2-3', 'title': 'Key Topic 3: Groups and societies', 'level': 3, 'parent': 'B2'},
    {'code': 'B2-4', 'title': 'Key Topic 4: Critical concepts (hybridity, patriarchy and matriarchy, gaze)', 'level': 3, 'parent': 'B2'},
    
    {'code': 'B2-Works', 'title': 'Prescribed Works (2 specified artists + 1 architect + other works)', 'level': 3, 'parent': 'B2'},
    {'code': 'B2-W-Pre1850', 'title': 'Pre-1850 works (2D, 3D, Architecture)', 'level': 4, 'parent': 'B2-Works'},
    {'code': 'B2-W-Post1850', 'title': 'Post-1850 works (2D, 3D, Architecture)', 'level': 4, 'parent': 'B2-Works'},
    
    # Theme B3: War in art and architecture
    {'code': 'B3', 'title': 'Theme B3: War in Art and Architecture', 'level': 2, 'parent': 'P1-Themes'},
    {'code': 'B3-1', 'title': 'Key Topic 1: Preparation for war', 'level': 3, 'parent': 'B3'},
    {'code': 'B3-2', 'title': 'Key Topic 2: Participation in war', 'level': 3, 'parent': 'B3'},
    {'code': 'B3-3', 'title': 'Key Topic 3: Consequences of war', 'level': 3, 'parent': 'B3'},
    {'code': 'B3-4', 'title': 'Key Topic 4: Critical concepts (glorification and condemnation, heroism, memorialisation)', 'level': 3, 'parent': 'B3'},
    
    {'code': 'B3-Works', 'title': 'Prescribed Works (2 specified artists + 1 architect + other works)', 'level': 3, 'parent': 'B3'},
    {'code': 'B3-W-Pre1850', 'title': 'Pre-1850 works (2D, 3D, Architecture)', 'level': 4, 'parent': 'B3-Works'},
    {'code': 'B3-W-Post1850', 'title': 'Post-1850 works (2D, 3D, Architecture)', 'level': 4, 'parent': 'B3-Works'},
    
    # ==================================================================================
    # PAPER 2 - PERIODS (Choose 2 from 5)
    # ==================================================================================
    {'code': 'P2-Periods', 'title': 'Periods (Choose 2 from 5)', 'level': 1, 'parent': 'Paper2'},
    
    # Period C1: Renaissance in Italy
    {'code': 'C1', 'title': 'Period C1: Invention and Illusion - The Renaissance in Italy (1420-1520)', 'level': 2, 'parent': 'P2-Periods'},
    {'code': 'C1-1', 'title': 'Key Topic 1: Anatomy and proportion', 'level': 3, 'parent': 'C1'},
    {'code': 'C1-2', 'title': 'Key Topic 2: Architecture and the revival of classical forms', 'level': 3, 'parent': 'C1'},
    {'code': 'C1-3', 'title': 'Key Topic 3: Perspective and illusionism', 'level': 3, 'parent': 'C1'},
    {'code': 'C1-4', 'title': 'Key Topic 4: Critical approaches (disegno, patronage, linear perspective)', 'level': 3, 'parent': 'C1'},
    
    {'code': 'C1-Works', 'title': 'Prescribed Works (specified artists and architects)', 'level': 3, 'parent': 'C1'},
    {'code': 'C1-W-Artists', 'title': 'Specified Artists: Fra Angelico, Piero della Francesca, Leonardo da Vinci, Michelangelo', 'level': 4, 'parent': 'C1-Works'},
    {'code': 'C1-W-Architects', 'title': 'Specified Architect: Filippo Brunelleschi', 'level': 4, 'parent': 'C1-Works'},
    
    # Period C2: Baroque
    {'code': 'C2', 'title': 'Period C2: Power and Persuasion - The Baroque in Catholic Europe (1597-1685)', 'level': 2, 'parent': 'P2-Periods'},
    {'code': 'C2-1', 'title': 'Key Topic 1: The expression of religious intensity', 'level': 3, 'parent': 'C2'},
    {'code': 'C2-2', 'title': 'Key Topic 2: Drama and illusion', 'level': 3, 'parent': 'C2'},
    {'code': 'C2-3', 'title': 'Key Topic 3: Glorification of the state', 'level': 3, 'parent': 'C2'},
    {'code': 'C2-4', 'title': 'Key Topic 4: Critical approaches (Catholic Reformation, chiaroscuro, tenebrism)', 'level': 3, 'parent': 'C2'},
    
    {'code': 'C2-Works', 'title': 'Prescribed Works (specified artists and architects)', 'level': 3, 'parent': 'C2'},
    {'code': 'C2-W-Artists', 'title': 'Specified Artists: Caravaggio, Artemisia Gentileschi, Gian Lorenzo Bernini, Diego Velázquez', 'level': 4, 'parent': 'C2-Works'},
    {'code': 'C2-W-Architects', 'title': 'Specified Architect: Francesco Borromini', 'level': 4, 'parent': 'C2-Works'},
    
    # Period C3: British and French Avant-Garde
    {'code': 'C3', 'title': 'Period C3: Rebellion and Revival - The British and French Avant-Garde (1848-99)', 'level': 2, 'parent': 'P2-Periods'},
    {'code': 'C3-1', 'title': 'Key Topic 1: Rebellion and the challenge to tradition', 'level': 3, 'parent': 'C3'},
    {'code': 'C3-2', 'title': 'Key Topic 2: New subjects for a new age', 'level': 3, 'parent': 'C3'},
    {'code': 'C3-3', 'title': 'Key Topic 3: Stylistic innovation', 'level': 3, 'parent': 'C3'},
    {'code': 'C3-4', 'title': 'Key Topic 4: Critical approaches (Realism, Impressionism, Post-Impressionism, Pre-Raphaelites)', 'level': 3, 'parent': 'C3'},
    
    {'code': 'C3-Works', 'title': 'Prescribed Works (specified artists and architects)', 'level': 3, 'parent': 'C3'},
    {'code': 'C3-W-Artists', 'title': 'Specified Artists: Gustave Courbet, Édouard Manet, Claude Monet, Vincent van Gogh', 'level': 4, 'parent': 'C3-Works'},
    {'code': 'C3-W-Architects', 'title': 'Specified Architect: Charles Barry and Augustus Pugin', 'level': 4, 'parent': 'C3-Works'},
    
    # Period C4: Modernism in Europe
    {'code': 'C4', 'title': 'Period C4: Brave New World - Modernism in Europe (1900-39)', 'level': 2, 'parent': 'P2-Periods'},
    {'code': 'C4-1', 'title': 'Key Topic 1: A break with the past', 'level': 3, 'parent': 'C4'},
    {'code': 'C4-2', 'title': 'Key Topic 2: Responding to a changing world', 'level': 3, 'parent': 'C4'},
    {'code': 'C4-3', 'title': 'Key Topic 3: Experimentation and abstraction', 'level': 3, 'parent': 'C4'},
    {'code': 'C4-4', 'title': 'Key Topic 4: Critical approaches (Expressionism, Cubism, Futurism, Surrealism, International Style)', 'level': 3, 'parent': 'C4'},
    
    {'code': 'C4-Works', 'title': 'Prescribed Works (specified artists and architects)', 'level': 3, 'parent': 'C4'},
    {'code': 'C4-W-Artists', 'title': 'Specified Artists: Pablo Picasso, Wassily Kandinsky, Frida Kahlo, Salvador Dalí', 'level': 4, 'parent': 'C4-Works'},
    {'code': 'C4-W-Architects', 'title': 'Specified Architect: Le Corbusier', 'level': 4, 'parent': 'C4-Works'},
    
    # Period C5: Pop Life
    {'code': 'C5', 'title': 'Period C5: Pop Life - British and American Contemporary Art and Architecture (1960-2015)', 'level': 2, 'parent': 'P2-Periods'},
    {'code': 'C5-1', 'title': 'Key Topic 1: Responses to mass culture and consumerism', 'level': 3, 'parent': 'C5'},
    {'code': 'C5-2', 'title': 'Key Topic 2: Conceptualism and performance', 'level': 3, 'parent': 'C5'},
    {'code': 'C5-3', 'title': 'Key Topic 3: Art and architecture that challenge conventions', 'level': 3, 'parent': 'C5'},
    {'code': 'C5-4', 'title': 'Key Topic 4: Critical approaches (Pop Art, Minimalism, Post-Modernism)', 'level': 3, 'parent': 'C5'},
    
    {'code': 'C5-Works', 'title': 'Prescribed Works (specified artists and architects)', 'level': 3, 'parent': 'C5'},
    {'code': 'C5-W-Artists', 'title': 'Specified Artists: Richard Hamilton, Andy Warhol, Barbara Hepworth, Tracey Emin', 'level': 4, 'parent': 'C5-Works'},
    {'code': 'C5-W-Architects', 'title': 'Specified Architect: Frank Gehry', 'level': 4, 'parent': 'C5-Works'},
]


def upload_topics():
    """Upload History of Art topics to Supabase."""
    
    print("=" * 80)
    print("EDEXCEL HISTORY OF ART (9HT0) - COMPLETE MANUAL UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("\nStructure: 2 Papers, Visual Analysis, 3 Themes, 5 Periods\n")
    
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
        print("[OK] HISTORY OF ART TOPICS UPLOADED SUCCESSFULLY!")
        print("=" * 80)
        
        levels = {}
        for t in TOPICS:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("\n[INFO] Hierarchy:")
        print(f"   Level 0 (Papers): {levels.get(0, 0)}")
        print(f"   Level 1 (Sections): {levels.get(1, 0)}")
        print(f"   Level 2 (Themes/Periods): {levels.get(2, 0)}")
        print(f"   Level 3 (Key Topics/Works): {levels.get(3, 0)}")
        print(f"   Level 4 (Work Details): {levels.get(4, 0)}")
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










