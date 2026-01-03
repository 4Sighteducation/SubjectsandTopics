"""
GCSE Citizenship Studies - Dedicated Scraper
=============================================

Structure from PDF:
- Level 0: 5 Themes (A-E) - hardcoded
- Level 1: Section headers (questions ending with ?)
- Level 2: Numbered topics (1, 2, 3, 4) in LEFT column of table
- Level 3: Bullet points (•) in RIGHT column of table

Example:
Theme A: Living together in the UK
  How have communities developed in the UK?
    1 The changing UK population
      • The changing composition of the UK population...
      • ...
    2 Migration and its impact
      • The social, economic and other effects...

CRITICAL: Only extracts content that exists in PDF. Does NOT invent.
"""

import os
import sys
import re
import requests
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv
from supabase import create_client

try:
    from pypdf import PdfReader
    PDF_LIBRARY = 'pypdf'
except ImportError:
    import PyPDF2
    PdfReader = PyPDF2.PdfReader
    PDF_LIBRARY = 'PyPDF2'

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT = {
    'code': 'GCSE-Citizenship',
    'name': 'Citizenship Studies',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Citizenship%20Studies/2016/Specification%20and%20sample%20assessments/specification-gcse-l1-l2-in-citizenship.pdf'
}

# The 5 main themes (Level 0)
MAIN_THEMES = [
    {
        'code': 'ThemeA',
        'title': 'Theme A: Living together in the UK',
        'level': 0,
        'parent': None
    },
    {
        'code': 'ThemeB',
        'title': 'Theme B: Democracy at work in the UK',
        'level': 0,
        'parent': None
    },
    {
        'code': 'ThemeC',
        'title': 'Theme C: Law and justice',
        'level': 0,
        'parent': None
    },
    {
        'code': 'ThemeD',
        'title': 'Theme D: Power and influence',
        'level': 0,
        'parent': None
    },
    {
        'code': 'ThemeE',
        'title': 'Theme E: Taking citizenship action',
        'level': 0,
        'parent': None
    }
]


def download_pdf():
    """Download PDF and extract text."""
    print(f"\n[INFO] Downloading PDF...")
    
    try:
        response = requests.get(SUBJECT['pdf_url'], timeout=60)
        response.raise_for_status()
        
        print(f"[OK] Downloaded {len(response.content):,} bytes")
        
        pdf_file = BytesIO(response.content)
        reader = PdfReader(pdf_file)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        print(f"[OK] Extracted {len(text):,} characters from {len(reader.pages)} pages")
        
        # Save debug
        debug_path = Path(__file__).parent / "debug-gcse-citizenship-final.txt"
        debug_path.write_text(text, encoding='utf-8')
        print(f"[OK] Saved debug to {debug_path.name}")
        
        return text
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        raise


def parse_topics(text):
    """
    Parse Citizenship topics from the PDF text.
    
    Expected structure:
    - Level 0: 5 Themes (A-E) - hardcoded
    - Level 1: Section headers (questions ending with ?)
    - Level 2: Numbered topics (1, 2, 3) from left column
    - Level 3: Bullet points (•) from right column
    """
    print("\n[INFO] Parsing Citizenship topics...")
    
    topics = []
    
    # Add the 5 main themes (Level 0)
    topics.extend(MAIN_THEMES)
    print(f"[OK] Added {len(MAIN_THEMES)} main themes (Level 0)")
    
    lines = text.split('\n')
    
    # Track state
    current_theme = None  # ThemeA, ThemeB, etc.
    current_section = None  # Section code for question headers
    current_topic = None  # Topic code for numbered items
    topic_counter = {}  # Track topic numbers per theme
    
    # Process line by line
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Pattern 1: Detect which Theme we're in
        # "Theme A: Living together in the UK"
        theme_match = re.match(r'^Theme\s+([A-E]):\s*(.+)$', line, re.IGNORECASE)
        if theme_match:
            theme_letter = theme_match.group(1)
            current_theme = f'Theme{theme_letter}'
            topic_counter[current_theme] = 0  # Reset counter for new theme
            print(f"\n[INFO] Entering {current_theme}")
            i += 1
            continue
        
        # Skip if we're not in a Theme section yet
        if not current_theme:
            i += 1
            continue
        
        # Pattern 2: Section headers (Level 1) - questions ending with ?
        # "How have communities developed in the UK?"
        if line.endswith('?') and len(line) > 15:
            # Create section code
            section_num = len([t for t in topics if t.get('parent') == current_theme and t['level'] == 1]) + 1
            section_code = f"{current_theme}_S{section_num}"
            current_section = section_code
            
            topics.append({
                'code': section_code,
                'title': line,
                'level': 1,
                'parent': current_theme
            })
            print(f"  [OK] Level 1: {line[:70]}")
            i += 1
            continue
        
        # Pattern 3: Numbered topics (Level 2) - from LEFT column of table
        # Format: "1 The changing UK population"
        # NOTE: Title may span multiple lines before bullets start
        numbered_match = re.match(r'^(\d+)\s+(.+)$', line)
        if numbered_match and current_section:
            num = numbered_match.group(1)
            title_parts = [numbered_match.group(2).strip()]
            
            # Look ahead to collect multi-line title (stop at bullets)
            j = i + 1
            while j < len(lines) and j < i + 5:
                next_line = lines[j].strip()
                
                # Stop at empty line
                if not next_line:
                    break
                
                # Stop at bullet point (title complete, now in right column)
                if next_line.startswith('●') or next_line.startswith('•'):
                    break
                
                # Stop at next numbered topic
                if re.match(r'^\d+\s+', next_line):
                    break
                
                # Stop at next section (question)
                if next_line.endswith('?') and len(next_line) > 15:
                    break
                
                # Stop at table headers
                if any(header in next_line for header in ['Subject content', 'Students should']):
                    break
                
                # Add this line to title
                title_parts.append(next_line)
                j += 1
            
            # Combine all title parts
            full_title = ' '.join(title_parts).strip()
            
            # Increment topic counter for this theme
            topic_counter[current_theme] += 1
            
            # Create topic code
            topic_code = f"{current_theme}_T{topic_counter[current_theme]}"
            current_topic = topic_code
            
            topics.append({
                'code': topic_code,
                'title': f"{num}. {full_title}",
                'level': 2,
                'parent': current_section
            })
            print(f"    [OK] Level 2: {num}. {full_title[:60]}")
            i += 1
            continue
        
        # Pattern 4: Bullet points (Level 3) - from RIGHT column
        # Lines starting with ● or •
        if (line.startswith('●') or line.startswith('•')) and current_topic:
            # Remove bullet and clean
            bullet_text = line.lstrip('●•').strip()
            
            # Skip if too short or empty
            if len(bullet_text) < 5:
                i += 1
                continue
            
            # Look ahead to collect multi-line bullets
            bullet_lines = [bullet_text]
            j = i + 1
            while j < len(lines) and j < i + 10:  # Allow up to 10 continuation lines
                next_line = lines[j].strip()
                
                # Stop at empty line
                if not next_line:
                    break
                
                # Stop at next bullet
                if next_line.startswith('●') or next_line.startswith('•'):
                    break
                
                # Stop at next numbered topic
                if re.match(r'^\d+\s+', next_line):
                    break
                
                # Stop at next section (question)
                if next_line.endswith('?') and len(next_line) > 15:
                    break
                
                # Stop at table headers
                if any(header in next_line for header in ['Subject content', 'Students should']):
                    break
                
                # Merge continuation
                bullet_lines.append(next_line)
                j += 1
            
            full_bullet = ' '.join(bullet_lines).strip()
            
            # Generate code for this bullet
            existing_bullets = [t for t in topics if t.get('parent') == current_topic and t['level'] == 3]
            bullet_num = len(existing_bullets) + 1
            
            topics.append({
                'code': f"{current_topic}_B{bullet_num}",
                'title': full_bullet,
                'level': 3,
                'parent': current_topic
            })
            print(f"      [OK] Level 3: {full_bullet[:70]}")
            i = j  # Skip merged lines
            continue
        
        i += 1
    
    return topics


def upload_topics(topics):
    """Upload topics to Supabase."""
    print("\n[INFO] Uploading to Supabase...")
    
    try:
        # Create/update subject
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT['name']} (GCSE)",
            'subject_code': SUBJECT['code'],
            'qualification_type': 'GCSE',
            'specification_url': SUBJECT['pdf_url'],
            'exam_board': 'Edexcel'
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        # Clear old topics
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared old topics")
        
        # Insert topics (NO TRUNCATION!)
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],  # Full content, no truncation
            'topic_level': t['level'],
            'exam_board': 'Edexcel'
        } for t in topics]
        
        inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted.data)} topics")
        
        # Link parent relationships
        code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
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
        
        print(f"[OK] Linked {linked} parent-child relationships")
        
        # Summary
        levels = {}
        for t in topics:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("\n" + "=" * 80)
        print("[SUCCESS] GCSE CITIZENSHIP STUDIES UPLOADED!")
        print("=" * 80)
        print(f"   Level 0 (Themes): {levels.get(0, 0)}")
        print(f"   Level 1 (Sections): {levels.get(1, 0)}")
        print(f"   Level 2 (Topics): {levels.get(2, 0)}")
        print(f"   Level 3 (Bullets): {levels.get(3, 0)}")
        print(f"\n   Total: {len(topics)} topics")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 80)
    print("GCSE CITIZENSHIP STUDIES - DEDICATED SCRAPER")
    print("=" * 80)
    print("Structure:")
    print("  Level 0: 5 Themes (A-E)")
    print("  Level 1: Section headers (questions)")
    print("  Level 2: Numbered topics (from left column)")
    print("  Level 3: Bullet points (from right column)")
    print("=" * 80)
    
    try:
        # Download and parse
        text = download_pdf()
        topics = parse_topics(text)
        
        if len(topics) < 20:
            print(f"\n[WARNING] Only {len(topics)} topics found - this seems too low!")
            print("[WARNING] Expected ~100+ topics (5 themes + sections + topics + bullets)")
            response = input("\nContinue with upload anyway? (y/n): ")
            if response.lower() != 'y':
                print("[INFO] Upload cancelled")
                return
        
        # Upload
        success = upload_topics(topics)
        
        if success:
            print("\n✅ SCRAPING COMPLETE!")
        else:
            print("\n❌ SCRAPING FAILED")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

