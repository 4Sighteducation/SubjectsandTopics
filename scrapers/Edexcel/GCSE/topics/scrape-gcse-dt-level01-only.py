"""
GCSE Design and Technology - LEVEL 0 & 1 ONLY
==============================================

STEP 1: Just get the structure right first!

Level 0: Component 1 sections (7 sections)
  - Section1: 1 – Core content
  - Section2: 2 – Metals
  - Section3: 3 – Papers and boards
  - Section4: 4 – Polymers
  - Section5: 5 – Systems
  - Section6: 6 – Textiles
  - Section7: 7 – Timbers

Level 1: Key Ideas (like 2.1, 2.2, 2.3, etc.)
  - Under Section2 (Metals): 2.1 Design contexts, 2.2 The sources, origins...
  - Under Section3 (Papers): 3.1 Design contexts, 3.2 The sources...
  - etc.

STOPS HERE - no Level 2 or 3 extraction yet!
"""

import os
import sys
import re
import requests
import camelot
from pathlib import Path
from io import BytesIO
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client
from pypdf import PdfReader

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT = {
    'code': 'GCSE-DesignTech',
    'name': 'Design and Technology',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/design-and-technology/2017/specification-and-sample-assessments/Pearson_Edexcel_GCSE_9_to_1_in_Design_and_Technology_Specification_issue3.pdf'
}

# Level 0: Component 1 sections
SECTIONS = [
    {'code': 'Section1', 'title': '1 – Core content'},
    {'code': 'Section2', 'title': '2 – Metals'},
    {'code': 'Section3', 'title': '3 – Papers and boards'},
    {'code': 'Section4', 'title': '4 – Polymers'},
    {'code': 'Section5', 'title': '5 – Systems'},
    {'code': 'Section6', 'title': '6 – Textiles'},
    {'code': 'Section7', 'title': '7 – Timbers'}
]

# Map section numbers to codes
SECTION_MAP = {
    '1': 'Section1', '2': 'Section2', '3': 'Section3', '4': 'Section4',
    '5': 'Section5', '6': 'Section6', '7': 'Section7'
}


def download_pdf():
    """Download PDF."""
    print(f"\n[INFO] Downloading PDF...")
    
    try:
        response = requests.get(SUBJECT['pdf_url'], timeout=60)
        response.raise_for_status()
        
        print(f"[OK] Downloaded {len(response.content):,} bytes")
        
        # Save temp file for Camelot
        temp_path = Path(__file__).parent / 'temp-gcse-dt.pdf'
        temp_path.write_bytes(response.content)
        
        # Also extract text for context
        pdf = PdfReader(BytesIO(response.content))
        text = '\n'.join(page.extract_text() for page in pdf.pages)
        
        print(f"[OK] Extracted text from {len(pdf.pages)} pages")
        
        return temp_path, text
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        raise


def parse_level_0_and_1():
    """Extract ONLY Level 0 and Level 1 - nothing deeper."""
    print("\n[INFO] Extracting Level 0 & 1 only...")
    
    topics = []
    
    # Level 0: Create all 7 sections
    for section in SECTIONS:
        topics.append({
            'code': section['code'],
            'title': section['title'],
            'level': 0,
            'parent': None
        })
    
    print(f"[OK] Created {len(SECTIONS)} sections (Level 0)")
    
    # Download PDF
    pdf_path, text = download_pdf()
    
    # Use Camelot to extract tables
    print(f"\n[INFO] Using Camelot to find Key Ideas (Level 1)...")
    
    try:
        tables = camelot.read_pdf(
            str(pdf_path),
            pages='12-55',  # Extended to include Timbers on page 52
            flavor='lattice'
        )
        print(f"[OK] Found {len(tables)} tables")
    except Exception as e:
        print(f"[WARN] Lattice failed, trying stream: {e}")
        tables = camelot.read_pdf(
            str(pdf_path),
            pages='12-55',
            flavor='stream'
        )
        print(f"[OK] Found {len(tables)} tables (stream mode)")
    
    # Extract Level 1: Key Ideas
    # Format: "2.1" or "2.2" in first column, title in second
    # OR format: "2.1 Design contexts" all in one cell
    
    key_ideas_found = set()  # Track to avoid duplicates
    
    for table_idx, table in enumerate(tables):
        df = table.df
        
        if len(df) < 2:
            continue
        
        for row_idx, row in df.iterrows():
            # Get both columns
            cell_0 = str(row.iloc[0]).strip() if len(row) > 0 else ""
            cell_1 = str(row.iloc[1]).strip() if len(row) > 1 else ""
            
            # Skip headers and empty
            if 'Key idea' in cell_0 or 'What students' in cell_0:
                continue
            if cell_0 in ['', 'nan', 'None'] and cell_1 in ['', 'nan', 'None']:
                continue
            
            # Look for Key Idea pattern: X.Y (where X = section number)
            # Try both cells
            for cell in [cell_0, cell_1]:
                if not cell or cell in ['nan', 'None']:
                    continue
                
                # Pattern 1: "2.1" or "2.2" at start of cell
                key_idea_match = re.match(r'^(\d)\.(\d+)\s+(.*)$', cell, re.DOTALL)
                if key_idea_match:
                    section_num = key_idea_match.group(1)
                    key_num = key_idea_match.group(2)
                    title_part = key_idea_match.group(3).strip()
                    
                    # Get section code
                    section_code = SECTION_MAP.get(section_num)
                    if not section_code:
                        continue
                    
                    # Build key idea code
                    key_idea_num = f"{section_num}.{key_num}"
                    code = f"{section_code}_KeyIdea{key_idea_num}"
                    
                    # Avoid duplicates
                    if code in key_ideas_found:
                        continue
                    
                    # Extract title (handle multi-line)
                    lines_in_cell = cell.split('\n')
                    title_lines = []
                    
                    for line in lines_in_cell:
                        line = line.strip()
                        if not line:
                            continue
                        # Skip the number itself
                        if line == key_idea_num:
                            continue
                        # Stop at numbered sub-items (2.1.1, 2.2.1, etc.)
                        if re.match(r'^\d+\.\d+\.\d+', line):
                            break
                        title_lines.append(line)
                    
                    title = ' '.join(title_lines).strip()
                    
                    # If title is empty, might be in other cell
                    if not title and cell == cell_0 and cell_1:
                        title = cell_1.split('\n')[0].strip()
                    
                    # Skip if still no title
                    if not title or len(title) < 5:
                        continue
                    
                    topics.append({
                        'code': code,
                        'title': f"{key_idea_num} {title}",
                        'level': 1,
                        'parent': section_code
                    })
                    
                    key_ideas_found.add(code)
                    print(f"  [{section_code}] {key_idea_num}: {title[:60]}...")
    
    print(f"\n[OK] Found {len(key_ideas_found)} key ideas (Level 1)")
    
    # Clean up
    pdf_path.unlink()
    
    return topics


def upload_topics(topics):
    """Upload to Supabase."""
    print(f"\n[INFO] Uploading {len(topics)} topics...")
    
    try:
        # Create/update subject
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT['name']} ({SUBJECT['qualification']})",
            'subject_code': SUBJECT['code'],
            'qualification_type': SUBJECT['qualification'],
            'specification_url': SUBJECT['pdf_url'],
            'exam_board': SUBJECT['exam_board']
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        # Clear old topics
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared old topics")
        
        # Insert topics
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'exam_board': SUBJECT['exam_board']
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
        
        # Summary by section
        print("\n" + "=" * 80)
        print("[SUCCESS] DESIGN & TECHNOLOGY - LEVEL 0 & 1 STRUCTURE")
        print("=" * 80)
        
        for section in SECTIONS:
            children = [t for t in topics if t.get('parent') == section['code'] and t['level'] == 1]
            print(f"  {section['title']:30} - {len(children)} key ideas")
        
        print(f"\n  Total: {len(topics)} topics (Level 0 & 1 only)")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 80)
    print("GCSE DESIGN & TECHNOLOGY - LEVEL 0 & 1 STRUCTURE ONLY")
    print("=" * 80)
    print("Step 1: Get sections and key ideas right FIRST")
    print("Step 2: Will add detailed content later")
    print("=" * 80)
    
    try:
        topics = parse_level_0_and_1()
        success = upload_topics(topics)
        
        if success:
            print("\n✅ Level 0 & 1 structure complete!")
            print("\nNext: Run Part 2 scraper to add detailed content (Level 2 & 3)")
        else:
            print("\n❌ FAILED")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

