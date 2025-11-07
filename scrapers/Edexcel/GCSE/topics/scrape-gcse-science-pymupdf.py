"""
GCSE Combined Science - PyMuPDF + Camelot Table Parser
=======================================================

Uses layout-aware parsing:
- PyMuPDF for text with font sizes/positions
- Camelot for extracting clean tables
- Two-pass approach for numbered + lettered items

Structure:
Level 0: 6 Papers
Level 1: Topics (from Content Overview)
Level 2: Numbered items from "Students should:" tables (1.1, 1.2 - stop at "including:")
Level 3: Lettered sub-items (a, b, c)
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

# Force UTF-8 encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT = {
    'code': 'GCSE-Science',
    'name': 'Science (Combined Science)',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Science/2016/Specification/gcse-combinedscience-spec.pdf'
}

# Papers defined from assessment structure
PAPERS = [
    {'code': 'Paper1', 'title': 'Paper 1: Biology 1 (1SC0/1BF, 1SC0/1BH)', 'subject': 'Biology'},
    {'code': 'Paper2', 'title': 'Paper 2: Biology 2 (1SC0/2BF, 1SC0/2BH)', 'subject': 'Biology'},
    {'code': 'Paper3', 'title': 'Paper 3: Chemistry 1 (1SC0/1CF, 1SC0/1CH)', 'subject': 'Chemistry'},
    {'code': 'Paper4', 'title': 'Paper 4: Chemistry 2 (1SC0/2CF, 1SC0/2CH)', 'subject': 'Chemistry'},
    {'code': 'Paper5', 'title': 'Paper 5: Physics 1 (1SC0/1PF, 1SC0/1PH)', 'subject': 'Physics'},
    {'code': 'Paper6', 'title': 'Paper 6: Physics 2 (1SC0/2PF, 1SC0/2PH)', 'subject': 'Physics'}
]


def download_pdf():
    """Download PDF and save locally for Camelot."""
    print(f"\n[INFO] Downloading PDF...")
    
    try:
        response = requests.get(SUBJECT['pdf_url'], timeout=60)
        response.raise_for_status()
        
        print(f"[OK] Downloaded {len(response.content):,} bytes")
        
        # Save to temp file for Camelot (it needs a file path, not BytesIO)
        temp_path = Path(__file__).parent / 'temp-gcse-science.pdf'
        temp_path.write_bytes(response.content)
        print(f"[OK] Saved to temp file for Camelot")
        
        # Also extract text for topic heading detection
        pdf = PdfReader(BytesIO(response.content))
        text = '\n'.join(page.extract_text() for page in pdf.pages)
        
        print(f"[OK] Extracted {len(text):,} characters from {len(pdf.pages)} pages")
        
        return temp_path, text
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        raise


def parse_topics():
    """Use Camelot for clean table extraction."""
    print("\n[INFO] Starting Camelot-powered parse...")
    
    topics = []
    
    # Level 0: Papers
    for paper in PAPERS:
        topics.append({
            'code': paper['code'],
            'title': paper['title'],
            'level': 0,
            'parent': None
        })
    
    print(f"[OK] Created {len(PAPERS)} papers (Level 0)")
    
    # Download PDF
    pdf_path, text = download_pdf()
    
    # Level 1: Topics (manually defined from assessment tables)
    print(f"\n[INFO] Creating Level 1 topics...")
    
    topic_mappings = {
        'Paper1': [(1, 'Key concepts in biology'), (2, 'Cells and control'), (3, 'Genetics'), 
                   (4, 'Natural selection and genetic modification'), (5, 'Health, disease and the development of medicines')],
        'Paper2': [(1, 'Key concepts in biology'), (6, 'Plant structures and their functions'), 
                   (7, 'Animal coordination, control and homeostasis'), (8, 'Exchange and transport in animals'), 
                   (9, 'Ecosystems and material cycles')],
        'Paper3': [(1, 'Key concepts in chemistry'), (2, 'States of matter and mixtures'), 
                   (3, 'Chemical changes'), (4, 'Extracting metals and equilibria')],
        'Paper4': [(1, 'Key concepts in chemistry'), (6, 'Groups in the periodic table'), 
                   (7, 'Rates of reaction and energy changes'), (8, 'Fuels and Earth science')],
        'Paper5': [(1, 'Key concepts of physics'), (2, 'Motion and forces'), (3, 'Conservation of energy'), 
                   (4, 'Waves'), (5, 'Light and the electromagnetic spectrum'), (6, 'Radioactivity')],
        'Paper6': [(1, 'Key concepts of physics'), (8, 'Energy - Forces doing work'), (9, 'Forces and their effects'), 
                   (10, 'Electricity and circuits'), (12, 'Magnetism and the motor effect'), 
                   (13, 'Electromagnetic induction'), (14, 'Particle model'), (15, 'Forces and matter')]
    }
    
    # Build ALL topics and create mapping from (topic_num, paper) to code
    # CRITICAL: Topic 1 appears in MULTIPLE papers!
    topic_to_papers = defaultdict(list)  # Map topic_num to list of paper codes
    
    for paper_code, paper_topics in topic_mappings.items():
        for topic_num, topic_name in paper_topics:
            code = f"{paper_code}_Topic{topic_num}"
            topics.append({
                'code': code,
                'title': f"Topic {topic_num} – {topic_name}",
                'level': 1,
                'parent': paper_code
            })
            topic_to_papers[str(topic_num)].append(code)
    
    print(f"[OK] Created {len(topics) - len(PAPERS)} topics (Level 1)")
    
    # Use Camelot to extract tables from Biology, Chemistry, Physics sections
    print(f"\n[INFO] Using Camelot to extract tables (pages 13-79)...")
    
    try:
        # Try lattice mode first (for tables with visible borders)
        tables = camelot.read_pdf(
            str(pdf_path),
            pages='13-79',
            flavor='lattice'
        )
        print(f"[OK] Camelot found {len(tables)} tables (lattice mode)")
    except Exception as e:
        print(f"[WARN] Lattice mode failed: {e}")
        print(f"[INFO] Trying stream mode...")
        # Fallback to stream mode
        tables = camelot.read_pdf(
            str(pdf_path),
            pages='13-79',
            flavor='stream'
        )
        print(f"[OK] Camelot found {len(tables)} tables (stream mode)")
    
    # Track current topic by scanning text for "Topic X" headings
    lines = text.split('\n')
    page_to_topic = {}  # Map page numbers to topic codes
    
    for line in lines:
        topic_match = re.match(r'^Topic\s+(\d+)\s+[–-]\s+', line, re.IGNORECASE)
        if topic_match:
            topic_num = topic_match.group(1)
            if topic_num in topic_to_papers:
                current_topic_code = topic_to_papers[topic_num][0]
                # Store for use with tables (rough mapping)
    
    # Process each table
    current_topic_code = None
    numbered_items = {}
    
    for table_idx, table in enumerate(tables):
        df = table.df
        
        # Skip if table is too small (not a Students should table)
        if len(df) < 2 or len(df.columns) < 2:
            continue
        
        print(f"\n[INFO] Processing table {table_idx + 1} on page {table.page}...")
        
        # Check if this is a "Students should:" table
        has_students_header = any('Students should' in str(cell) for cell in df.iloc[0])
        
        if not has_students_header:
            # Check first data rows for numbered items
            first_cells = df.iloc[:5, 0].astype(str).tolist()
            has_numbered = any(re.match(r'^\d+\.\d+$', cell.strip()) for cell in first_cells)
            if not has_numbered:
                continue
        
        # Debug: Only show for first table
        if table_idx == 0:
            print(f"  [DEBUG] Sample table structure (showing row with 1.1):")
            for i in range(min(5, len(df))):
                cell = str(df.iloc[i, 0])
                if '1.1' in cell:
                    print(f"    Found 1.1 in row {i}")
                    print(f"    Content length: {len(cell)} chars")
                    print(f"    Has 'including:': {'including:' in cell.lower()}")
                    print(f"    Has 'a ': {bool(re.search(r'\\na\\s+', cell))}")
                    break
        
        # This is a Students should table!
        for row_idx, row in df.iterrows():
            # Get all cells in row
            cells = [str(row.iloc[col]).strip() for col in range(len(row))]
            
            # Skip header row
            if any('Students should' in cell for cell in cells):
                continue
            
            cell_0 = cells[0] if len(cells) > 0 else ""
            cell_1 = cells[1] if len(cells) > 1 else ""
            
            # Skip if all cells are empty
            if all(c in ['', 'nan', 'None'] for c in cells):
                continue
            
            # Sometimes the number and content are in SAME cell (cell_0)
            # Check if cell_0 contains "1.1 Explain..." format
            combined_match = re.match(r'^(\d+)\.(\d+)\s+(.+)$', cell_0, re.DOTALL)
            if combined_match:
                major = combined_match.group(1)
                minor = combined_match.group(2)
                full_content = combined_match.group(3).strip()
                
                # Find which topic this belongs to
                if major in topic_to_papers and topic_to_papers[major]:
                    current_topic_code = topic_to_papers[major][0]
                
                if not current_topic_code:
                    continue
                
                # Split content into Level 2 (main) and Level 3 (lettered items)
                # Level 2: Everything up to (and including) "including:"
                # Level 3: Lines starting with "a ", "b ", "c ", etc.
                
                # Debug for 1.1
                if major == '1' and minor == '1':
                    print(f"    [DEBUG] Processing 1.1 cell content:")
                    print(f"      Length: {len(full_content)} chars")
                    print(f"      First 200 chars: {full_content[:200]}")
                
                lines_in_cell = full_content.split('\n')
                main_content = []
                lettered_items = []
                in_main = True
                current_letter = None
                current_letter_content = []
                
                for idx, line in enumerate(lines_in_cell):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check if this line is JUST a single lowercase letter
                    if re.match(r'^([a-z])$', line):
                        # Save previous letter if any
                        if current_letter and current_letter_content:
                            lettered_items.append((current_letter, ' '.join(current_letter_content)))
                        
                        in_main = False
                        current_letter = line
                        current_letter_content = []
                        continue
                    
                    # Check if line starts with "a ", "b ", etc (letter and content on same line)
                    letter_match = re.match(r'^([a-z])\s+(.+)$', line)
                    if letter_match:
                        # Save previous letter if any
                        if current_letter and current_letter_content:
                            lettered_items.append((current_letter, ' '.join(current_letter_content)))
                        
                        in_main = False
                        current_letter = letter_match.group(1)
                        current_letter_content = [letter_match.group(2)]
                        continue
                    
                    # Otherwise, append to current context
                    if in_main:
                        main_content.append(line)
                    elif current_letter:
                        current_letter_content.append(line)
                
                # Don't forget the last letter!
                if current_letter and current_letter_content:
                    lettered_items.append((current_letter, ' '.join(current_letter_content)))
                
                # Join main content and stop at "including:"
                main_text = ' '.join(main_content)
                if 'including:' in main_text.lower():
                    idx = main_text.lower().index('including:')
                    main_text = main_text[:idx + 10].strip()
                
                # Create Level 2 item
                code = f"{current_topic_code}_{major}.{minor}"
                
                topics.append({
                    'code': code,
                    'title': main_text,
                    'level': 2,
                    'parent': current_topic_code
                })
                
                numbered_items[code] = True
                print(f"    [OK] {code}: {main_text[:60]}...")
                
                # Create Level 3 items (lettered)
                for letter, letter_content in lettered_items:
                    letter_code = f"{code}_{letter}"
                    topics.append({
                        'code': letter_code,
                        'title': letter_content.strip(),
                        'level': 3,
                        'parent': code
                    })
                    print(f"      [OK] {letter_code}: {letter_content[:60]}...")
                
                continue
            
            # Pattern 1: Numbered item in cell 0, content in cell 1
            numbered_match = re.match(r'^(\d+)\.(\d+)$', cell_0)
            if numbered_match and cell_1 and cell_1 not in ['nan', 'None', '']:
                major = numbered_match.group(1)
                minor = numbered_match.group(2)
                
                # Find which topic this belongs to
                if major in topic_to_papers and topic_to_papers[major]:
                    current_topic_code = topic_to_papers[major][0]
                
                if not current_topic_code:
                    continue
                
                content = cell_1
                
                # CRITICAL: Stop at "including:" - this is where Level 2 ends
                if 'including:' in content.lower():
                    idx = content.lower().index('including:')
                    content = content[:idx + 10].strip()
                
                code = f"{current_topic_code}_{major}.{minor}"
                
                topics.append({
                    'code': code,
                    'title': content,
                    'level': 2,
                    'parent': current_topic_code
                })
                
                numbered_items[code] = True
                print(f"    [OK] {code}: {content[:60]}...")
                
            # Pattern 2: Empty cell 0, lettered item in cell 1
            elif (not cell_0 or cell_0 in ['nan', 'None', '']):
                # Check both cell_0 and cell_1 for lettered items
                letter_match = re.match(r'^([a-z])\s+(.+)$', cell_1)
                if not letter_match and cell_0:
                    letter_match = re.match(r'^([a-z])\s+(.+)$', cell_0)
                
                if letter_match:
                    letter = letter_match[1]
                    content = letter_match[2].strip()
                    
                    # Find most recent numbered item
                    if numbered_items:
                        recent_numbered = list(numbered_items.keys())[-1]
                        code = f"{recent_numbered}_{letter}"
                        
                        topics.append({
                            'code': code,
                            'title': content,
                            'level': 3,
                            'parent': recent_numbered
                        })
                        print(f"      [OK] {code}: {content[:60]}...")
    
    print(f"\n[OK] Extracted from {len(tables)} tables")
    
    # Clean up temp file
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
        print("[SUCCESS] GCSE SCIENCE UPLOADED!")
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
    print("GCSE COMBINED SCIENCE - PyMuPDF + Camelot Parser")
    print("=" * 80)
    print("Uses table extraction for clean Level 2 & 3 parsing")
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

