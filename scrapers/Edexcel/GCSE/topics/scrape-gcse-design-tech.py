"""
GCSE Design and Technology - Camelot Table Parser
==================================================

Structure (Component 1 ONLY):
Level 0: Core content + Material categories (1-7)
Level 1: Key ideas (from "Key idea" column) - 1.1, 1.2, etc.
Level 2: Numbered items (from "What students need to learn") - 1.1.1, 1.1.2, etc.
         STOP at ":" or remove "including:"
Level 3: Lettered sub-items (a, b, c, d, etc.)

URL: https://qualifications.pearson.com/content/dam/pdf/GCSE/design-and-technology/2017/specification-and-sample-assessments/Pearson_Edexcel_GCSE_9_to_1_in_Design_and_Technology_Specification_issue3.pdf
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

# Force UTF-8 encoding
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
COMPONENT_SECTIONS = [
    {'code': 'Section1', 'title': '1 – Core content', 'type': 'core'},
    {'code': 'Section2', 'title': '2 – Metals', 'type': 'material'},
    {'code': 'Section3', 'title': '3 – Papers and boards', 'type': 'material'},
    {'code': 'Section4', 'title': '4 – Polymers', 'type': 'material'},
    {'code': 'Section5', 'title': '5 – Systems', 'type': 'material'},
    {'code': 'Section6', 'title': '6 – Textiles', 'type': 'material'},
    {'code': 'Section7', 'title': '7 – Timbers', 'type': 'material'}
]


def download_pdf():
    """Download PDF and save for Camelot."""
    print(f"\n[INFO] Downloading PDF...")
    
    try:
        response = requests.get(SUBJECT['pdf_url'], timeout=60)
        response.raise_for_status()
        
        print(f"[OK] Downloaded {len(response.content):,} bytes")
        
        # Save temp file for Camelot
        temp_path = Path(__file__).parent / 'temp-gcse-dt.pdf'
        temp_path.write_bytes(response.content)
        print(f"[OK] Saved temp file")
        
        # Also extract text for section detection
        pdf = PdfReader(BytesIO(response.content))
        text = '\n'.join(page.extract_text() for page in pdf.pages)
        
        print(f"[OK] Extracted {len(text):,} characters from {len(pdf.pages)} pages")
        
        return temp_path, text
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        raise


def parse_topics():
    """Use Camelot for clean table extraction."""
    print("\n[INFO] Starting Camelot parse...")
    
    topics = []
    
    # Level 0: Component 1 sections
    for section in COMPONENT_SECTIONS:
        topics.append({
            'code': section['code'],
            'title': section['title'],
            'level': 0,
            'parent': None
        })
    
    print(f"[OK] Created {len(COMPONENT_SECTIONS)} component sections (Level 0)")
    
    # Download PDF
    pdf_path, text = download_pdf()
    
    # Use Camelot to extract tables
    print(f"\n[INFO] Extracting tables with Camelot...")
    
    try:
        tables = camelot.read_pdf(
            str(pdf_path),
            pages='8-50',  # Adjust based on content location
            flavor='lattice'
        )
        print(f"[OK] Found {len(tables)} tables (lattice mode)")
    except Exception as e:
        print(f"[WARN] Lattice failed: {e}")
        tables = camelot.read_pdf(
            str(pdf_path),
            pages='8-50',
            flavor='stream'
        )
        print(f"[OK] Found {len(tables)} tables (stream mode)")
    
    # Map section numbers to codes
    section_map = {
        '1': 'Section1', '2': 'Section2', '3': 'Section3', '4': 'Section4',
        '5': 'Section5', '6': 'Section6', '7': 'Section7'
    }
    
    # Track current context
    current_section = None
    current_key_idea = None
    numbered_items = {}
    
    # Process tables
    for table_idx, table in enumerate(tables):
        df = table.df
        
        if len(df) < 2 or len(df.columns) < 2:
            continue
        
        # Check if this is a D&T table (has "Key idea" or numbered items)
        has_key_idea = any('Key idea' in str(cell) for cell in df.iloc[0])
        first_cells = df.iloc[:5, 0].astype(str).tolist()
        has_numbered = any(re.match(r'^1\.\d+', cell.strip()) for cell in first_cells)
        
        if not has_key_idea and not has_numbered:
            continue
        
        print(f"\n[INFO] Processing table {table_idx + 1} on page {table.page}...")
        
        for row_idx, row in df.iterrows():
            cells = [str(row.iloc[col]).strip() for col in range(len(row))]
            
            # Skip headers
            if any('Key idea' in cell or 'What students need to learn' in cell for cell in cells):
                continue
            
            cell_0 = cells[0] if len(cells) > 0 else ""
            cell_1 = cells[1] if len(cells) > 1 else ""
            
            # Skip empty rows
            if all(c in ['', 'nan', 'None'] for c in cells):
                continue
            
            # Pattern 1: Key idea (Level 1) - format: "1.1 The impact of..."
            # Check if cell_0 or cell_1 contains key idea
            key_idea_match = None
            key_idea_content = ""
            
            if re.match(r'^1\.\d+\s+', cell_0):
                key_idea_match = re.match(r'^(1\.\d+)\s+(.+)$', cell_0, re.DOTALL)
                if key_idea_match:
                    key_idea_content = cell_0
            elif re.match(r'^1\.\d+\s+', cell_1):
                key_idea_match = re.match(r'^(1\.\d+)\s+(.+)$', cell_1, re.DOTALL)
                if key_idea_match:
                    key_idea_content = cell_1
            
            if key_idea_match:
                major = key_idea_match.group(1)  # "1.1"
                title = key_idea_match.group(2).strip()
                
                # Extract just the title (might be on separate lines)
                lines_in_cell = key_idea_content.split('\n')
                title_lines = []
                for line in lines_in_cell:
                    line = line.strip()
                    if not line or line == major:
                        continue
                    # Stop at numbered sub-items (1.1.1)
                    if re.match(r'^\d+\.\d+\.\d+', line):
                        break
                    title_lines.append(line)
                
                title = ' '.join(title_lines).strip()
                
                # Determine which section - ALL key ideas start with "1."
                # But we need to track section context from elsewhere
                # For now, use Section1 and we'll reassign in Pass 2
                current_section = 'Section1'
                
                code = f"{current_section}_KeyIdea{major}"
                current_key_idea = code
                
                topics.append({
                    'code': code,
                    'title': f"{major} {title}",
                    'level': 1,
                    'parent': current_section
                })
                
                print(f"  [OK] {code}: {title[:60]}...")
            
            # Pattern 2: Numbered items (Level 2) - format: "2.2.1 Ferrous metals:"
            # First digit = section number!
            for cell in [cell_0, cell_1]:
                if not cell or cell in ['nan', 'None']:
                    continue
                
                # Check if contains numbered items
                numbered_match = re.match(r'^(\d+)\.(\d+)\.(\d+)\s+(.+)$', cell, re.DOTALL)
                if numbered_match:
                    section_num = numbered_match.group(1)  # First digit = section!
                    major = numbered_match.group(2)
                    minor = numbered_match.group(3)
                    full_content = numbered_match.group(4).strip()
                    
                    # Determine section from first digit
                    current_section = section_map.get(section_num, 'Section1')
                    
                    # Key idea is section.major (e.g., "2.2" from "2.2.1")
                    key_idea_code = f"{current_section}_KeyIdea{section_num}.{major}"
                    
                    # Create key idea if it doesn't exist yet
                    if not any(t['code'] == key_idea_code for t in topics):
                        topics.append({
                            'code': key_idea_code,
                            'title': f"{section_num}.{major} (Key Idea)",
                            'level': 1,
                            'parent': current_section
                        })
                        print(f"  [OK] Auto-created {key_idea_code}")
                    
                    current_key_idea = key_idea_code
                    
                    # Split into Level 2 (main) and Level 3 (lettered)
                    lines_in_cell = full_content.split('\n')
                    main_content = []
                    lettered_items = []
                    in_main = True
                    current_letter = None
                    current_letter_content = []
                    
                    for line in lines_in_cell:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Single letter on its own line
                        if re.match(r'^([a-z])$', line):
                            if current_letter and current_letter_content:
                                lettered_items.append((current_letter, ' '.join(current_letter_content)))
                            in_main = False
                            current_letter = line
                            current_letter_content = []
                            continue
                        
                        # Letter with content on same line
                        letter_match = re.match(r'^([a-z])\s+(.+)$', line)
                        if letter_match:
                            if current_letter and current_letter_content:
                                lettered_items.append((current_letter, ' '.join(current_letter_content)))
                            in_main = False
                            current_letter = letter_match.group(1)
                            current_letter_content = [letter_match.group(2)]
                            continue
                        
                        # Regular content
                        if in_main:
                            main_content.append(line)
                        elif current_letter:
                            current_letter_content.append(line)
                    
                    # Save last letter
                    if current_letter and current_letter_content:
                        lettered_items.append((current_letter, ' '.join(current_letter_content)))
                    
                    # Join main content and clean
                    main_text = ' '.join(main_content)
                    
                    # Remove "including:" as requested
                    main_text = re.sub(r'\s*including:\s*', '', main_text, flags=re.IGNORECASE)
                    
                    # Stop at first colon (if no including was found)
                    if ':' in main_text:
                        main_text = main_text[:main_text.index(':') + 1].strip()
                    
                    # Create Level 2 item
                    code = f"{current_key_idea}_{section_num}.{major}.{minor}"
                    
                    topics.append({
                        'code': code,
                        'title': main_text,
                        'level': 2,
                        'parent': current_key_idea
                    })
                    
                    numbered_items[code] = True
                    print(f"    [OK] {code}: {main_text[:60]}...")
                    
                    # Create Level 3 lettered items
                    for letter, letter_content in lettered_items:
                        letter_code = f"{code}_{letter}"
                        topics.append({
                            'code': letter_code,
                            'title': letter_content.strip(),
                            'level': 3,
                            'parent': code
                        })
                        print(f"      [OK] {letter_code}: {letter_content[:60]}...")
    
    print(f"\n[OK] Extracted from {len(tables)} tables")
    
    # Clean up
    pdf_path.unlink()
    print(f"[OK] Cleaned up temp file")
    
    # Remove duplicates
    unique = []
    seen = set()
    for t in topics:
        if t['code'] not in seen:
            unique.append(t)
            seen.add(t['code'])
    
    print(f"[OK] Total unique topics: {len(unique)}")
    
    return unique


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
        
        # Summary
        levels = defaultdict(int)
        for t in topics:
            levels[t['level']] += 1
        
        print("\n" + "=" * 80)
        print("[SUCCESS] GCSE DESIGN & TECHNOLOGY UPLOADED!")
        print("=" * 80)
        for level in sorted(levels.keys()):
            print(f"   Level {level}: {levels[level]} topics")
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
    print("GCSE DESIGN AND TECHNOLOGY - Component 1 Only")
    print("=" * 80)
    print("Structure:")
    print("  Level 0: Core content + Material categories (1-7)")
    print("  Level 1: Key ideas (1.1, 1.2, etc.)")
    print("  Level 2: Numbered items (1.1.1, stop at ':')")
    print("  Level 3: Lettered sub-items (a, b, c)")
    print("=" * 80)
    
    try:
        topics = parse_topics()
        success = upload_topics(topics)
        
        if success:
            print("\n✅ COMPLETE!")
        else:
            print("\n❌ FAILED")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

