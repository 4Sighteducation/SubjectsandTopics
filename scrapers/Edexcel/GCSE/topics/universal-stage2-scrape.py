"""
Universal Edexcel GCSE Stage 2 PDF Scraper
===========================================

Reads a YAML config and extracts detailed content from PDF tables.
Extracts Level 2+ key ideas and detailed content.

Usage:
    python universal-stage2-scrape.py configs/geography-a.yaml
    python universal-stage2-scrape.py configs/business.yaml
"""

import os
import sys
import re
import yaml
import requests
import camelot
import fitz  # PyMuPDF
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

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))


def load_config(config_path):
    """Load subject configuration from YAML file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_existing_structure(config):
    """Load existing topics from database."""
    subject = config['subject']
    print("\n[INFO] Loading existing structure...")
    
    subject_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', subject['code']).eq('qualification_type', subject['qualification']).eq('exam_board', subject['exam_board']).execute()
    
    if not subject_result.data:
        print("[ERROR] Subject not found! Run Stage 1 first!")
        return None, None, None
    
    subject_id = subject_result.data[0]['id']
    print(f"[OK] Subject ID: {subject_id}")
    
    # Get existing topics
    topics_result = supabase.table('staging_aqa_topics').select('*').eq('subject_id', subject_id).in_('topic_level', [0, 1, 2]).execute()
    
    existing_topics = {}
    for t in topics_result.data:
        existing_topics[t['topic_code']] = {
            'id': t['id'],
            'code': t['topic_code'],
            'name': t['topic_name'],
            'level': t['topic_level']
        }
    
    print(f"[OK] Found {len(existing_topics)} existing topics (Level 0, 1, 2)")
    
    return subject_id, existing_topics, config


def download_pdf(config):
    """Download PDF."""
    subject = config['subject']
    print(f"\n[INFO] Downloading PDF...")
    
    try:
        response = requests.get(subject['pdf_url'], timeout=60)
        response.raise_for_status()
        
        print(f"[OK] Downloaded {len(response.content):,} bytes")
        
        temp_path = Path(__file__).parent / f"temp-{subject['code']}.pdf"
        temp_path.write_bytes(response.content)
        print(f"[OK] Saved temp file")
        
        return temp_path
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        raise


def extract_detailed_content(config, existing_topics):
    """Extract Level 2+ content from PDF tables."""
    subject = config['subject']
    scraping = config.get('scraping', {})
    page_range = scraping.get('page_range', '7-30')
    
    print(f"\n[INFO] Extracting detailed content from {subject['name']}...")
    
    new_topics = []
    pdf_path = download_pdf(config)
    
    # Extract page text for optional subtopic detection
    pdf_doc = fitz.open(pdf_path)
    page_texts = {}
    start_page, end_page = map(int, page_range.split('-'))
    for page_num in range(start_page - 1, end_page):
        if page_num < len(pdf_doc):
            page_texts[page_num + 1] = pdf_doc[page_num].get_text()
    pdf_doc.close()
    
    # Extract tables - try both lattice and stream
    print(f"[INFO] Using Camelot on pages {page_range}...")
    
    try:
        tables_lattice = camelot.read_pdf(str(pdf_path), pages=page_range, flavor='lattice')
        print(f"[OK] Lattice found {len(tables_lattice)} tables")
        
        tables_stream = camelot.read_pdf(str(pdf_path), pages=page_range, flavor='stream')
        print(f"[OK] Stream found {len(tables_stream)} tables")
        
        # Use whichever found more
        tables = tables_lattice if len(tables_lattice) >= len(tables_stream) else tables_stream
        print(f"[INFO] Using {'lattice' if tables == tables_lattice else 'stream'} ({len(tables)} tables)")
    except Exception as e:
        print(f"[ERROR] Camelot failed: {e}")
        return []
    
    # Build optional subtopic detection map
    optional_map = {}
    if 'optional_subtopics' in config:
        for opt in config['optional_subtopics']:
            code_suffix = opt['code'].split('_')[-1]  # e.g., "1A", "4B"
            optional_map[code_suffix] = {
                'code': opt['code'],
                'patterns': opt.get('detect_in_text', [])
            }
    
    # Build period detection map (for History subjects)
    period_map = {}
    if 'period_detection' in config:
        for period in config['period_detection']:
            period_map[period['code']] = {
                'code': period['code'],
                'patterns': period.get('detect_in_text', [])
            }
    
    exit_patterns = config.get('exit_optional_patterns', [])
    topic_mapping = config.get('topic_to_component', {})
    
    current_optional_subtopic = None
    current_period = None  # For History subjects
    
    for table_idx, table in enumerate(tables):
        df = table.df
        
        if len(df) < 2 or len(df.columns) < 2:
            print(f"[SKIP] Table {table_idx + 1} on page {table.page}: Too small ({len(df)} rows, {len(df.columns)} cols)")
            # Debug: show what's in it anyway
            if len(df) > 0:
                first_cell = str(df.iloc[0, 0])[:50] if len(df.columns) > 0 else ""
                print(f"       First cell: {first_cell}")
            continue
        
        # Check for "Key idea" or "Key topic" header in first 3 rows
        # Geography uses "Key idea", History may have no headers at all
        has_key_header = False
        header_row_idx = -1  # -1 means no header row
        accept_no_headers = scraping.get('accept_tables_without_headers', False)
        
        for check_row in range(min(3, len(df))):  # Check first 3 rows
            # Clean newlines from EACH cell first, then join
            cells_clean = [str(cell).replace('\n', ' ').replace('  ', ' ') for cell in df.iloc[check_row]]
            row_text = ' '.join(cells_clean).lower()
            
            if 'key idea' in row_text or 'key topic' in row_text:
                has_key_header = True
                header_row_idx = check_row
                break
        
        if not has_key_header and not accept_no_headers:
            # Debug: show first row
            first_row = ' | '.join([str(cell).replace('\n', '\\n')[:40] for cell in df.iloc[0][:3]])
            print(f"[SKIP] Table {table_idx + 1} on page {table.page}: No header. Row 0: {first_row}")
            continue
        
        # For History: If accepting tables without headers, check if this looks like a content table
        if accept_no_headers and not has_key_header:
            # Check if first data row starts with a number (like "1 " or "2 ")
            first_data_cell = str(df.iloc[0, 0]).strip()
            if not re.match(r'^\d+\s+\w', first_data_cell):
                # Not a numbered topic table, skip it
                first_row = ' | '.join([str(cell).replace('\n', '\\n')[:40] for cell in df.iloc[0][:3]])
                print(f"[SKIP] Table {table_idx + 1} on page {table.page}: No numbered content. Row 0: {first_row}")
                continue
        
        # Check for optional subtopic sections AND period sections
        page_num = table.page
        if page_num in page_texts:
            page_text = page_texts[page_num]
            
            # Check for period sections (History subjects)
            if period_map:
                for period_code, period_info in period_map.items():
                    for pattern in period_info['patterns']:
                        if pattern in page_text:
                            if current_period != period_code:
                                current_period = period_code
                                period_name = period_info['code'].split('_')[-1]
                                print(f"[INFO] Detected period: {period_code} ({pattern})")
                            break
                    if current_period == period_code:
                        break
            
            # Check each optional subtopic pattern (Geography subjects)
            for opt_code, opt_info in optional_map.items():
                for pattern in opt_info['patterns']:
                    if pattern in page_text:
                        if current_optional_subtopic != opt_code:
                            current_optional_subtopic = opt_code
                            print(f"[INFO] Detected optional subtopic {opt_code}")
                        break
                if current_optional_subtopic == opt_code:
                    break
            
            # Check exit patterns
            for exit_pattern in exit_patterns:
                if re.search(exit_pattern, page_text):
                    if current_optional_subtopic:
                        print(f"[INFO] Exited optional subtopic section")
                        current_optional_subtopic = None
                    break
        
        print(f"\n[INFO] Processing table {table_idx + 1} on page {table.page}...")
        
        # Track current key idea for multi-row detail items
        current_key_idea_code = None
        current_key_idea_level = None
        all_detail_items = []
        
        for row_idx, row in df.iterrows():
            if row_idx <= header_row_idx:
                continue
            
            cell_0 = str(row.iloc[0]).strip() if len(row) > 0 else ""
            cell_1 = str(row.iloc[1]).strip() if len(row) > 1 else ""
            
            if 'Key idea' in cell_0 or 'Detailed content' in cell_1:
                continue
            
            if all(c in ['', 'nan', 'None'] for c in [cell_0, cell_1]):
                continue
            
            # Check if this is a continuation row (empty key idea, but has detail content)
            cell_0_is_empty = cell_0 in ['', 'nan', 'None'] or not cell_0.strip()
            
            if cell_0_is_empty and cell_1 and cell_1 not in ['', 'nan', 'None']:
                # This is a continuation row for the current key idea
                if current_key_idea_code:
                    # Check if it starts with a letter (Geography: b., c., etc.)
                    letter_match = re.match(r'^([a-z])\.\s+(.+)', cell_1, re.DOTALL | re.MULTILINE)
                    if letter_match:
                        letter = letter_match.group(1)
                        content_lines = [line.strip() for line in letter_match.group(2).split('\n') if line.strip()]
                        letter_text = ' '.join(content_lines)
                        
                        all_detail_items.append({
                            'letter': letter,
                            'text': letter_text,
                            'parent_code': current_key_idea_code,
                            'level': current_key_idea_level + 1
                        })
                        print(f"    [L{current_key_idea_level + 1}] {letter}: {letter_text[:60]}...")
                    
                    # Check if it has bullets (History continuation rows)
                    elif '•' in cell_1 or '●' in cell_1:
                        bullet_items = re.split(r'[•●]\s*', cell_1)
                        bullet_num = len([d for d in all_detail_items if d['parent_code'] == current_key_idea_code]) + 1
                        
                        for bullet_text in bullet_items:
                            bullet_text = bullet_text.strip()
                            if bullet_text and bullet_text not in ['', 'nan']:
                                content_lines = [line.strip() for line in bullet_text.split('\n') if line.strip()]
                                clean_text = ' '.join(content_lines)
                                
                                all_detail_items.append({
                                    'letter': f"bullet{bullet_num}",
                                    'text': clean_text,
                                    'parent_code': current_key_idea_code,
                                    'level': current_key_idea_level + 1
                                })
                                print(f"    [L{current_key_idea_level + 1}] •{bullet_num}: {clean_text[:60]}...")
                                bullet_num += 1
                continue
            
            # Match key idea/topic patterns:
            # Geography format: "1.1 Title..." (decimal numbering)
            # History format: "1 Title..." (simple numbering)
            
            major = None
            minor = None
            title = None
            
            # Try Geography format first (decimal)
            geo_match = re.match(r'^(\d+)\.(\d+)\s+(.+)$', cell_0, re.DOTALL)
            if geo_match:
                major = geo_match.group(1)
                minor = geo_match.group(2)
                title = ' '.join([line.strip() for line in geo_match.group(3).split('\n') if line.strip()])
            else:
                # Try History format (simple number + title)
                history_match = re.match(r'^(\d+)\s+(.+)$', cell_0, re.DOTALL)
                if history_match:
                    major = history_match.group(1)
                    minor = "0"  # No minor number in History format
                    title = ' '.join([line.strip() for line in history_match.group(2).split('\n') if line.strip()])
            
            if major and title:
                
                # Determine parent and level
                if current_optional_subtopic:
                    # Inside optional subtopic/period
                    # For Geography: optional subtopics are Level 2, so key ideas are Level 3
                    # For History: period headers are Level 2, so numbered topics are Level 3
                    parent_code = optional_map[current_optional_subtopic]['code']
                    level = 3
                elif current_period:
                    # Old period detection (now using optional_subtopics instead)
                    parent_code = current_period
                    level = 2
                else:
                    # No period/subtopic detected - use topic mapping fallback
                    component = topic_mapping.get(major, f"Component{(int(major)-1)//3 + 1}")
                    parent_code = f"{component}_Topic{major}"
                    level = 2
                
                if parent_code not in existing_topics:
                    print(f"  [WARN] Parent {parent_code} not found for {major}.{minor}")
                    continue
                
                parent_id = existing_topics[parent_code]['id']
                
                # Generate code and title based on format
                if minor == "0":
                    # History format: no minor number
                    code = f"{parent_code}_Topic{major}"
                    topic_title = f"{major}. {title}"
                else:
                    # Geography format: with minor number
                    code = f"{parent_code}_KeyIdea{major}.{minor}"
                    topic_title = f"{major}.{minor} {title}"
                
                new_topics.append({
                    'code': code,
                    'title': topic_title,
                    'level': level,
                    'parent_id': parent_id
                })
                
                if minor == "0":
                    print(f"  [L{level}] {major}. {title[:60]}...")
                else:
                    print(f"  [L{level}] {major}.{minor}: {title[:60]}...")
                
                # Set as current key idea for multi-row detail extraction
                current_key_idea_code = code
                current_key_idea_level = level
                
                # Extract details from THIS row
                # Geography: lettered items (a, b, c)
                # History: bullet points (•)
                detail_level = level + 1
                
                if cell_1 and cell_1 not in ['', 'nan', 'None']:
                    # Check if it uses letters (Geography) or bullets (History)
                    has_letters = bool(re.search(r'^([a-z])\.\s+', cell_1, re.MULTILINE))
                    has_bullets = '•' in cell_1 or '●' in cell_1
                    
                    if has_letters:
                        # Geography format: extract first letter item
                        letter_match = re.match(r'^([a-z])\.\s+(.+)', cell_1, re.DOTALL | re.MULTILINE)
                        if letter_match:
                            letter = letter_match.group(1)
                            content_lines = [line.strip() for line in letter_match.group(2).split('\n') if line.strip()]
                            letter_text = ' '.join(content_lines)
                            
                            all_detail_items.append({
                                'letter': letter,
                                'text': letter_text,
                                'parent_code': code,
                                'level': detail_level
                            })
                            print(f"    [L{detail_level}] {letter}: {letter_text[:60]}...")
                    
                    elif has_bullets:
                        # History format: extract bullet points
                        bullet_items = re.split(r'[•●]\s*', cell_1)
                        bullet_num = 1
                        for bullet_text in bullet_items:
                            bullet_text = bullet_text.strip()
                            if bullet_text and bullet_text not in ['', 'nan']:
                                content_lines = [line.strip() for line in bullet_text.split('\n') if line.strip()]
                                clean_text = ' '.join(content_lines)
                                
                                all_detail_items.append({
                                    'letter': f"bullet{bullet_num}",
                                    'text': clean_text,
                                    'parent_code': code,
                                    'level': detail_level
                                })
                                print(f"    [L{detail_level}] •{bullet_num}: {clean_text[:60]}...")
                                bullet_num += 1
        
        # After processing all rows in this table, add all detail items to new_topics
        for detail in all_detail_items:
            new_topics.append({
                'code': f"{detail['parent_code']}_{detail['letter']}",
                'title': detail['text'],
                'level': detail['level'],
                'parent_code': detail['parent_code']
            })
    
    print(f"\n[OK] Extracted {len(new_topics)} new topics")
    pdf_path.unlink()
    
    return new_topics


def upsert_topics(config, subject_id, new_topics, existing_topics):
    """Upsert extracted topics."""
    subject = config['subject']
    print(f"\n[INFO] Upserting {len(new_topics)} topics...")
    
    try:
        # Delete old scraped content but keep optional subtopics from Stage 1
        all_topics = supabase.table('staging_aqa_topics').select('id, topic_code, topic_level').eq('subject_id', subject_id).execute()
        
        # Build list of codes to preserve (optional subtopics AND periods from Stage 1)
        preserve_codes = set()
        if 'optional_subtopics' in config:
            for opt in config['optional_subtopics']:
                preserve_codes.add(opt['code'])
        
        # Also preserve period codes (History subjects)
        if 'period_detection' in config:
            for period in config['period_detection']:
                # Periods won't be in Level 2+, they're Level 1 topics
                # So we don't need to preserve them here
                pass
        
        to_delete = []
        for t in all_topics.data:
            if t['topic_level'] >= 2:
                code = t['topic_code']
                # Keep if it's in the preserve list (optional subtopics from Stage 1)
                if code not in preserve_codes:
                    to_delete.append(t['id'])
        
        if to_delete:
            for topic_id in to_delete:
                supabase.table('staging_aqa_topics').delete().eq('id', topic_id).execute()
            print(f"[OK] Cleared {len(to_delete)} old topics (kept optional subtopics)")
        
        # Insert by level (support up to Level 5 for complex subjects like History)
        code_to_id = {}
        
        for level_num in [2, 3, 4, 5]:
            level_topics = [t for t in new_topics if t['level'] == level_num]
            if not level_topics:
                continue
            
            # Deduplicate
            seen = set()
            unique = []
            for t in level_topics:
                if t['code'] not in seen:
                    unique.append(t)
                    seen.add(t['code'])
            
            to_insert = []
            for t in unique:
                if 'parent_id' in t:
                    parent_id = t['parent_id']
                else:
                    parent_code = t.get('parent_code')
                    parent_id = code_to_id.get(parent_code)
                
                if not parent_id:
                    continue
                
                to_insert.append({
                    'subject_id': subject_id,
                    'topic_code': t['code'],
                    'topic_name': t['title'],
                    'topic_level': t['level'],
                    'parent_topic_id': parent_id,
                    'exam_board': subject['exam_board']
                })
            
            if to_insert:
                inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
                print(f"[OK] Inserted {len(inserted.data)} Level {level_num} topics")
                for t in inserted.data:
                    code_to_id[t['topic_code']] = t['id']
        
        # Summary
        all_topics = supabase.table('staging_aqa_topics').select('topic_level').eq('subject_id', subject_id).execute()
        levels = defaultdict(int)
        for t in all_topics.data:
            levels[t['topic_level']] += 1
        
        print("\n" + "=" * 80)
        print(f"[SUCCESS] {subject['name'].upper()} - STAGE 2 COMPLETE!")
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
        print("Usage: python universal-stage2-scrape.py <config-file.yaml>")
        print("\nExamples:")
        print("  python universal-stage2-scrape.py configs/geography-a.yaml")
        print("  python universal-stage2-scrape.py configs/business.yaml")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    if not Path(config_path).exists():
        print(f"[ERROR] Config file not found: {config_path}")
        sys.exit(1)
    
    print("=" * 80)
    print("UNIVERSAL EDEXCEL GCSE - STAGE 2 PDF SCRAPER")
    print("=" * 80)
    
    try:
        config = load_config(config_path)
        subject_id, existing_topics, config = get_existing_structure(config)
        
        if not subject_id:
            return
        
        new_topics = extract_detailed_content(config, existing_topics)
        success = upsert_topics(config, subject_id, new_topics, existing_topics)
        
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

