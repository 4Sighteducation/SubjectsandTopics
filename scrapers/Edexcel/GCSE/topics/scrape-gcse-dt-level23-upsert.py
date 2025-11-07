"""
GCSE Design and Technology - LEVEL 2 & 3 UPSERT
===============================================

STEP 2: Add detailed content to existing structure!

Assumes Level 0 & 1 already exist in database.

Adds:
- Level 2: Numbered items (1.1.1, 2.2.1, etc.) - stops at ":"
- Level 3: Lettered sub-items (a, b, c, etc.)

Does NOT delete existing Level 0 & 1!
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


def get_existing_structure():
    """Load existing Level 0 & 1 from database."""
    print("\n[INFO] Loading existing Level 0 & 1 structure from database...")
    
    # Get subject ID
    subject_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', SUBJECT['code']).eq('qualification_type', SUBJECT['qualification']).eq('exam_board', SUBJECT['exam_board']).execute()
    
    if not subject_result.data:
        print("[ERROR] Subject not found! Run Level 0&1 scraper first!")
        return None, None
    
    subject_id = subject_result.data[0]['id']
    print(f"[OK] Subject ID: {subject_id}")
    
    # Get existing topics (Level 0 & 1)
    topics_result = supabase.table('staging_aqa_topics').select('*').eq('subject_id', subject_id).in_('topic_level', [0, 1]).execute()
    
    existing_topics = {}
    for t in topics_result.data:
        existing_topics[t['topic_code']] = {
            'id': t['id'],
            'code': t['topic_code'],
            'name': t['topic_name'],
            'level': t['topic_level']
        }
    
    level_0_count = len([t for t in topics_result.data if t['topic_level'] == 0])
    level_1_count = len([t for t in topics_result.data if t['topic_level'] == 1])
    
    print(f"[OK] Found existing structure:")
    print(f"     Level 0: {level_0_count} sections")
    print(f"     Level 1: {level_1_count} key ideas")
    
    return subject_id, existing_topics


def download_pdf():
    """Download PDF."""
    print(f"\n[INFO] Downloading PDF...")
    
    try:
        response = requests.get(SUBJECT['pdf_url'], timeout=60)
        response.raise_for_status()
        
        print(f"[OK] Downloaded {len(response.content):,} bytes")
        
        # Save temp file for Camelot
        temp_path = Path(__file__).parent / 'temp-gcse-dt-level23.pdf'
        temp_path.write_bytes(response.content)
        print(f"[OK] Saved temp file")
        
        return temp_path
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        raise


def extract_level_2_and_3(existing_topics):
    """Extract Level 2 & 3 content from tables."""
    print("\n[INFO] Extracting Level 2 & 3 detailed content...")
    
    new_topics = []
    
    # Download PDF
    pdf_path = download_pdf()
    
    # Use Camelot
    print(f"[INFO] Extracting tables...")
    
    try:
        tables = camelot.read_pdf(
            str(pdf_path),
            pages='12-55',
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
    
    # Process tables to extract numbered items (Level 2) and lettered items (Level 3)
    current_key_idea = None
    numbered_items = {}
    
    for table_idx, table in enumerate(tables):
        df = table.df
        
        if len(df) < 2:
            continue
        
        print(f"\n[INFO] Processing table {table_idx + 1}...")
        
        for row_idx, row in df.iterrows():
            cell_0 = str(row.iloc[0]).strip() if len(row) > 0 else ""
            cell_1 = str(row.iloc[1]).strip() if len(row) > 1 else ""
            
            # Skip headers and empty
            if 'Key idea' in cell_0 or 'What students' in cell_1:
                continue
            if all(c in ['', 'nan', 'None'] for c in [cell_0, cell_1]):
                continue
            
            # Check both cells for numbered items (X.Y.Z format)
            for cell in [cell_0, cell_1]:
                if not cell or cell in ['nan', 'None']:
                    continue
                
                # Pattern: X.Y.Z (section.keyidea.item)
                numbered_match = re.match(r'^(\d)\.(\d+)\.(\d+)\s+(.+)$', cell, re.DOTALL)
                if numbered_match:
                    section_num = numbered_match.group(1)
                    key_num = numbered_match.group(2)
                    item_num = numbered_match.group(3)
                    full_content = numbered_match.group(4).strip()
                    
                    # Find parent key idea
                    key_idea_code = f"Section{section_num}_KeyIdea{section_num}.{key_num}"
                    
                    if key_idea_code not in existing_topics:
                        # print(f"  [WARN] Parent not found: {key_idea_code}")
                        continue
                    
                    current_key_idea = key_idea_code
                    parent_id = existing_topics[key_idea_code]['id']
                    
                    # Split content into main (Level 2) and lettered (Level 3)
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
                    
                    # Build main text
                    main_text = ' '.join(main_content)
                    
                    # Remove "including:" as requested
                    main_text = re.sub(r'\s*including:\s*', '', main_text, flags=re.IGNORECASE)
                    
                    # Stop at first colon
                    if ':' in main_text:
                        main_text = main_text[:main_text.index(':') + 1].strip()
                    
                    # Skip if no content
                    if len(main_text) < 3:
                        continue
                    
                    # Create Level 2 item
                    code = f"{key_idea_code}_{section_num}.{key_num}.{item_num}"
                    
                    # Skip if this code somehow already exists (shouldn't happen but safety check)
                    if code in existing_topics:
                        continue
                    
                    new_topics.append({
                        'code': code,
                        'title': main_text,
                        'level': 2,
                        'parent_id': parent_id
                    })
                    
                    numbered_items[code] = True
                    # print(f"  [L2] {code}: {main_text[:50]}...")
                    
                    # Create Level 3 lettered items
                    for letter, letter_content in lettered_items:
                        letter_code = f"{code}_{letter}"
                        
                        new_topics.append({
                            'code': letter_code,
                            'title': letter_content.strip(),
                            'level': 3,
                            'parent_code': code  # Will need to resolve this
                        })
                        # print(f"    [L3] {letter}: {letter_content[:50]}...")
    
    print(f"\n[OK] Extracted {len(new_topics)} new topics (Level 2 & 3)")
    
    # Clean up
    pdf_path.unlink()
    
    return new_topics


def upsert_detailed_topics(subject_id, new_topics, existing_topics):
    """Upsert Level 2 & 3 WITHOUT deleting Level 0 & 1."""
    print(f"\n[INFO] Upserting {len(new_topics)} detailed topics...")
    
    try:
        # First, delete ONLY Level 2 & 3 (keep Level 0 & 1)
        delete_result = supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).gte('topic_level', 2).execute()
        print(f"[OK] Cleared old Level 2 & 3 topics")
        
        # Insert Level 2 topics first
        level_2_topics = [t for t in new_topics if t['level'] == 2]
        
        # Remove duplicates before inserting
        seen_codes = set()
        unique_l2 = []
        for t in level_2_topics:
            if t['code'] not in seen_codes:
                unique_l2.append(t)
                seen_codes.add(t['code'])
        
        print(f"[INFO] Filtered to {len(unique_l2)} unique Level 2 topics (from {len(level_2_topics)})")
        
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'parent_topic_id': t['parent_id'],
            'exam_board': SUBJECT['exam_board']
        } for t in unique_l2]
        
        if to_insert:
            inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
            print(f"[OK] Inserted {len(inserted.data)} Level 2 topics")
            
            # Build code to ID mapping for Level 3 parents
            code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
        else:
            code_to_id = {}
        
        # Insert Level 3 topics
        level_3_topics = [t for t in new_topics if t['level'] == 3]
        
        # Remove duplicates
        seen_codes_l3 = set()
        unique_l3 = []
        for t in level_3_topics:
            if t['code'] not in seen_codes_l3:
                unique_l3.append(t)
                seen_codes_l3.add(t['code'])
        
        print(f"[INFO] Filtered to {len(unique_l3)} unique Level 3 topics (from {len(level_3_topics)})")
        
        to_insert_l3 = []
        for t in unique_l3:
            parent_code = t['parent_code']
            parent_id = code_to_id.get(parent_code)
            
            if not parent_id:
                # print(f"[WARN] Parent not found for {t['code']}")
                continue
            
            to_insert_l3.append({
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': t['title'],
                'topic_level': t['level'],
                'parent_topic_id': parent_id,
                'exam_board': SUBJECT['exam_board']
            })
        
        if to_insert_l3:
            inserted_l3 = supabase.table('staging_aqa_topics').insert(to_insert_l3).execute()
            print(f"[OK] Inserted {len(inserted_l3.data)} Level 3 topics")
        
        # Summary
        all_topics = supabase.table('staging_aqa_topics').select('topic_level').eq('subject_id', subject_id).execute()
        levels = defaultdict(int)
        for t in all_topics.data:
            levels[t['topic_level']] += 1
        
        print("\n" + "=" * 80)
        print("[SUCCESS] DESIGN & TECHNOLOGY - COMPLETE WITH DETAILS!")
        print("=" * 80)
        for level in sorted(levels.keys()):
            print(f"   Level {level}: {levels[level]} topics")
        print(f"\n   Total: {len(all_topics.data)} topics")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 80)
    print("GCSE DESIGN & TECHNOLOGY - ADD LEVEL 2 & 3 DETAILS")
    print("=" * 80)
    print("Step 2: Add detailed content to existing structure")
    print("Does NOT delete Level 0 & 1!")
    print("=" * 80)
    
    try:
        # Load existing structure
        subject_id, existing_topics = get_existing_structure()
        
        if not subject_id:
            print("\n[ERROR] Run scrape-gcse-dt-level01-only.py first!")
            return
        
        # Extract Level 2 & 3
        new_topics = extract_level_2_and_3(existing_topics)
        
        # Upsert
        success = upsert_detailed_topics(subject_id, new_topics, existing_topics)
        
        if success:
            print("\n✅ COMPLETE! Design & Technology now has full 4-level hierarchy!")
        else:
            print("\n❌ FAILED")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

