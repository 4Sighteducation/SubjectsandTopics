"""
Religious Studies - Level 4 Content Scraper
===========================================

Scrapes Level 4 bullet points from PDF tables.

Tables have format:
- Column 1: Topic code (e.g., "4.4.1")
- Column 2: Topic name ending with colon (e.g., "Sikh teaching on human rights:")
- Then: Comma-separated list of Level 4 items

Usage:
    python scrape-religious-studies-level4.py RSA
    python scrape-religious-studies-level4.py RSB
"""

import os
import sys
import re
import requests
import camelot
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

SUBJECTS = {
    'RSA': {
        'code': 'GCSE-RSA',
        'name': 'Religious Studies A',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Religious%20Studies/2016/Specification%20and%20sample%20assessments/specification-gcse-l1-l2-religious-studies-a-june-2016-draft-4.pdf',
        'page_range': '10-200'  # Adjust as needed
    },
    'RSB': {
        'code': 'GCSE-RSB',
        'name': 'Religious Studies B',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Religious%20Studies/2016/Specification%20and%20sample%20assessments/specification-gcse-l1-l2-religious-studies-b-june-2016-draft-4.pdf',
        'page_range': '8-117'  # Content pages according to spec
    }
}


def download_pdf(pdf_url, subject_code):
    """Download PDF."""
    print(f"\n[INFO] Downloading PDF...")
    
    try:
        response = requests.get(pdf_url, timeout=60)
        response.raise_for_status()
        
        print(f"[OK] Downloaded {len(response.content):,} bytes")
        
        temp_path = Path(__file__).parent / f"temp-{subject_code}.pdf"
        temp_path.write_bytes(response.content)
        print(f"[OK] Saved temp file")
        
        return temp_path
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        raise


def get_existing_topics(subject_code):
    """Load existing Level 3 topics from database."""
    print("\n[INFO] Loading existing topics...")
    
    subject_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', subject_code).eq('qualification_type', 'GCSE').eq('exam_board', 'Edexcel').execute()
    
    if not subject_result.data:
        print("[ERROR] Subject not found!")
        return None, {}
    
    subject_id = subject_result.data[0]['id']
    print(f"[OK] Subject ID: {subject_id}")
    
    # Get ALL topics to build complete map
    topics_result = supabase.table('staging_aqa_topics').select('*').eq('subject_id', subject_id).execute()
    
    # Build map of ALL Level 3 topics by full code (not just number)
    level3_topics_by_code = {}
    level3_topics_by_number = {}
    
    for t in topics_result.data:
        if t['topic_level'] == 3:
            # Store by full code
            level3_topics_by_code[t['topic_code']] = {
                'id': t['id'],
                'code': t['topic_code'],
                'name': t['topic_name']
            }
            
            # Also store by number for lookup (but this will have collisions)
            title = t['topic_name']
            match = re.match(r'^(\d+\.\d+)\s+', title)
            if match:
                number = match.group(1)
                # Store as list to handle multiple topics with same number
                if number not in level3_topics_by_number:
                    level3_topics_by_number[number] = []
                level3_topics_by_number[number].append({
                    'id': t['id'],
                    'code': t['topic_code'],
                    'name': t['topic_name']
                })
    
    print(f"[OK] Found {len(level3_topics_by_code)} Level 3 topics")
    print(f"[INFO] Unique topic numbers: {len(level3_topics_by_number)}")
    
    return subject_id, level3_topics_by_code


def extract_level4_from_pdf(pdf_path, page_range, level3_topics):
    """Extract Level 4 content from PDF tables."""
    print(f"\n[INFO] Extracting Level 4 content from tables...")
    
    level4_topics = []
    
    # Try both lattice and stream
    try:
        tables_lattice = camelot.read_pdf(str(pdf_path), pages=page_range, flavor='lattice')
        tables_stream = camelot.read_pdf(str(pdf_path), pages=page_range, flavor='stream')
        
        tables = tables_lattice if len(tables_lattice) >= len(tables_stream) else tables_stream
        print(f"[OK] Found {len(tables)} tables")
    except Exception as e:
        print(f"[ERROR] Camelot failed: {e}")
        return []
    
    for table_idx, table in enumerate(tables):
        df = table.df
        
        if len(df) < 2 or len(df.columns) < 2:
            continue
        
        print(f"\n[INFO] Processing table {table_idx + 1} on page {table.page}...")
        
        for row_idx, row in df.iterrows():
            cell_0 = str(row.iloc[0]).strip() if len(row) > 0 else ""
            cell_1 = str(row.iloc[1]).strip() if len(row) > 1 else ""
            
            # Skip empty rows
            if not cell_0 and not cell_1:
                continue
            
            # Look for rows where column 2 ends with colon
            if cell_1.endswith(':'):
                # Extract topic number from cell 0 (e.g., "4.4.1", "2.3.1")
                number_match = re.match(r'^(\d+\.\d+)\.(\d+)', cell_0)
                if number_match:
                    parent_number = number_match.group(1)  # e.g., "4.4"
                    sub_number = number_match.group(2)  # e.g., "1"
                    topic_name = cell_1.rstrip(':').strip()
                    
                    # Find parent in level3_topics
                    if parent_number not in level3_topics:
                        print(f"  [WARN] Parent {parent_number} not found for {cell_0}")
                        continue
                    
                    parent_info = level3_topics[parent_number]
                    
                    # Look ahead for comma-separated content
                    # Check remaining cells in this row and next few rows
                    content_cells = []
                    
                    # Check rest of current row
                    for col_idx in range(2, len(row)):
                        cell_val = str(row.iloc[col_idx]).strip()
                        if cell_val and cell_val not in ['', 'nan', 'None']:
                            content_cells.append(cell_val)
                    
                    # Join and split by commas
                    content_text = ' '.join(content_cells).strip()
                    
                    if content_text:
                        # Split by comma and create Level 4 topics
                        items = [item.strip() for item in content_text.split(',') if item.strip()]
                        
                        for item_idx, item_text in enumerate(items, 1):
                            level4_code = f"{parent_info['code']}_L4_{sub_number}_{item_idx}"
                            
                            level4_topics.append({
                                'code': level4_code,
                                'title': item_text,
                                'level': 4,
                                'parent_code': parent_info['code'],
                                'parent_id': parent_info['id']
                            })
                            
                            print(f"    [L4] {cell_0} {topic_name}: {item_text[:50]}...")
    
    print(f"\n[OK] Extracted {len(level4_topics)} Level 4 topics")
    
    return level4_topics


def upload_level4_topics(subject_id, level4_topics):
    """Upload Level 4 topics to Supabase."""
    print(f"\n[INFO] Uploading {len(level4_topics)} Level 4 topics...")
    
    if not level4_topics:
        print("[WARN] No Level 4 topics to upload")
        return True
    
    try:
        # Delete existing Level 4+ topics
        all_topics = supabase.table('staging_aqa_topics').select('id, topic_level').eq('subject_id', subject_id).execute()
        
        to_delete = []
        for t in all_topics.data:
            if t['topic_level'] >= 4:
                to_delete.append(t['id'])
        
        if to_delete:
            for topic_id in to_delete:
                supabase.table('staging_aqa_topics').delete().eq('id', topic_id).execute()
            print(f"[OK] Cleared {len(to_delete)} old Level 4+ topics")
        
        # Insert new Level 4 topics
        to_insert = []
        for t in level4_topics:
            to_insert.append({
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': t['title'],
                'topic_level': t['level'],
                'parent_topic_id': t['parent_id'],
                'exam_board': 'Edexcel'
            })
        
        if to_insert:
            inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
            print(f"[OK] Inserted {len(inserted.data)} Level 4 topics")
        
        # Summary
        all_topics = supabase.table('staging_aqa_topics').select('topic_level').eq('subject_id', subject_id).execute()
        levels = defaultdict(int)
        for t in all_topics.data:
            levels[t['topic_level']] += 1
        
        print("\n" + "=" * 80)
        print("[SUCCESS] LEVEL 4 SCRAPE COMPLETE!")
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
    if len(sys.argv) < 2:
        print("Usage: python scrape-religious-studies-level4.py <RSA|RSB>")
        print("\nExamples:")
        print("  python scrape-religious-studies-level4.py RSA")
        print("  python scrape-religious-studies-level4.py RSB")
        sys.exit(1)
    
    subject_key = sys.argv[1].upper()
    
    if subject_key not in SUBJECTS:
        print(f"[ERROR] Unknown subject: {subject_key}")
        print(f"Available: {', '.join(SUBJECTS.keys())}")
        sys.exit(1)
    
    subject = SUBJECTS[subject_key]
    
    print("=" * 80)
    print("RELIGIOUS STUDIES - LEVEL 4 PDF SCRAPER")
    print("=" * 80)
    print(f"Subject: {subject['name']}")
    print("=" * 80)
    
    try:
        # Load existing structure
        subject_id, level3_topics = get_existing_topics(subject['code'])
        
        if not subject_id:
            return
        
        # Download and scrape PDF
        pdf_path = download_pdf(subject['pdf_url'], subject['code'])
        level4_topics = extract_level4_from_pdf(pdf_path, subject['page_range'], level3_topics)
        
        # Clean up
        pdf_path.unlink()
        
        # Upload to Supabase
        success = upload_level4_topics(subject_id, level4_topics)
        
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

