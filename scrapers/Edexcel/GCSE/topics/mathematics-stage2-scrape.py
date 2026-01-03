"""
Mathematics-specific Stage 2 PDF Scraper
=========================================

Extracts Mathematics content from PDF with 4-level hierarchy:
- Level 2: Subtopics (italic headers like "Structure and calculation")
- Level 3: Topic codes (N1, N2, A1, etc.)
- Level 4: Paragraph content describing knowledge (includes bullets)

Hierarchy:
- Level 0: Foundation / Higher tier
- Level 1: Number, Algebra, Ratio, Geometry, Statistics
- Level 2: Subtopics (Structure and calculation, Fractions decimals percentages, etc.)
- Level 3: Topic codes (N1, N2, A1, etc.)
- Level 4: Content paragraphs (all text including bullets)

Usage:
    python mathematics-stage2-scrape.py configs/mathematics.yaml
"""

import os
import sys
import re
import yaml
import requests
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

# Validate environment variables
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')

if not supabase_url:
    print("[ERROR] SUPABASE_URL not found in environment variables!")
    print(f"[INFO] Checked .env file at: {env_path}")
    sys.exit(1)

if not supabase_key:
    print("[ERROR] SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY not found in environment variables!")
    print(f"[INFO] Checked .env file at: {env_path}")
    sys.exit(1)

try:
    supabase = create_client(supabase_url, supabase_key)
except Exception as e:
    print(f"[ERROR] Failed to create Supabase client: {e}")
    print(f"[INFO] Supabase URL: {supabase_url[:50]}...")
    sys.exit(1)


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
    
    # Get existing topics (Level 0 and 1)
    topics_result = supabase.table('staging_aqa_topics').select('*').eq('subject_id', subject_id).in_('topic_level', [0, 1]).execute()
    
    existing_topics = {}
    for t in topics_result.data:
        existing_topics[t['topic_code']] = {
            'id': t['id'],
            'code': t['topic_code'],
            'name': t['topic_name'],
            'level': t['topic_level']
        }
    
    print(f"[OK] Found {len(existing_topics)} existing topics (Level 0, 1)")
    
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


def extract_mathematics_content(config, existing_topics):
    """Extract Mathematics content from PDF with full hierarchy."""
    subject = config['subject']
    scraping = config.get('scraping', {})
    page_range = scraping.get('page_range', '5-50')
    
    print(f"\n[INFO] Extracting Mathematics content from {subject['name']}...")
    
    new_topics = []
    pdf_path = download_pdf(config)
    
    # Extract text from PDF
    pdf_doc = fitz.open(pdf_path)
    start_page, end_page = map(int, page_range.split('-'))
    
    # Current state tracking
    current_tier = None  # "Foundation" or "Higher"
    current_level1_topic = None  # "Number", "Algebra", etc.
    current_level2_subtopic_code = None  # Code for current subtopic
    current_level2_subtopic_name = None  # Name for current subtopic
    current_level3_code = None  # Current topic code (N1, A1, etc.)
    
    print(f"[INFO] Processing pages {start_page}-{end_page}...")
    
    for page_num in range(start_page - 1, end_page):
        if page_num >= len(pdf_doc):
            break
        
        page = pdf_doc[page_num]
        text = page.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            # Detect tier headings (Foundation/Higher)
            tier_match = re.search(r'(Foundation|Higher)\s+tier\s+knowledge', line, re.IGNORECASE)
            if tier_match:
                tier_name = tier_match.group(1)
                if tier_name.lower() == 'foundation':
                    current_tier = 'Foundation'
                elif tier_name.lower() == 'higher':
                    current_tier = 'Higher'
                print(f"\n[INFO] Detected tier: {current_tier} (page {page_num + 1})")
                current_level1_topic = None
                current_level2_subtopic_code = None
                current_level2_subtopic_name = None
                continue
            
            # Detect Level 1 topic headings (Number, Algebra, etc.)
            if current_tier:
                # Check if this line is a Level 1 topic (numbered sections)
                number_match = re.match(r'^(\d+)\.\s+(.+)$', line)
                if number_match:
                    section_num = number_match.group(1)
                    section_title = number_match.group(2).strip()
                    
                    # Map section numbers to topics
                    section_to_topic = {
                        '1': 'Number',
                        '2': 'Algebra',
                        '3': 'Ratio',
                        '4': 'Geometry',
                        '5': 'Statistics'
                    }
                    
                    if section_num in section_to_topic:
                        current_level1_topic = section_to_topic[section_num]
                        print(f"  [INFO] Detected Level 1 topic: {current_level1_topic} (page {page_num + 1})")
                        current_level2_subtopic_code = None
                        current_level2_subtopic_name = None
            
            # Detect Level 2 subtopics (italic headers)
            # Known subtopics under each Level 1 topic
            if current_tier and current_level1_topic:
                # Skip "What students need to learn:" lines
                if 'What students need to learn' in line:
                    continue
                
                # Define known subtopics for each Level 1 topic with simplified codes
                # Format: (full_name, short_code)
                subtopic_map = {
                    'Number': [
                        ('Structure and calculation', 'N_Structure'),
                        ('Fractions, decimals and percentages', 'N_Fractions'),
                        ('Measures and accuracy', 'N_Measures')
                    ],
                    'Algebra': [
                        ('Notation, vocabulary and manipulation', 'A_Notation'),
                        ('Graphs', 'A_Graphs'),
                        ('Solving equations and inequalities', 'A_Solving'),
                        ('Sequences', 'A_Sequences')
                    ],
                    'Ratio': [
                        # Add as needed
                    ],
                    'Geometry': [
                        ('Properties and constructions', 'G_Properties'),
                        ('Mensuration and calculation', 'G_Mensuration'),
                        ('Vectors', 'G_Vectors')
                    ],
                    'Statistics': [
                        ('Probability', 'S_Probability'),
                        ('Statistics', 'S_Statistics')
                    ]
                }
                
                known_subtopics = subtopic_map.get(current_level1_topic, [])
                
                # Check if this line matches a known subtopic
                for subtopic_name, subtopic_short_code in known_subtopics:
                    if subtopic_name.lower() in line.lower():
                        # Create Level 2 subtopic
                        parent_code = f"{current_tier}_{current_level1_topic}"
                        if parent_code not in existing_topics:
                            continue
                        
                        # Use simplified code
                        subtopic_code = f"{parent_code}_{subtopic_short_code}"
                        
                        current_level2_subtopic_code = subtopic_code
                        current_level2_subtopic_name = subtopic_name
                        
                        new_topics.append({
                            'code': subtopic_code,
                            'title': subtopic_name,
                            'level': 2,
                            'parent_code': parent_code,
                            'order': len([t for t in new_topics if t['level'] == 2])  # Track order
                        })
                        
                        print(f"    [L2] {subtopic_short_code}: {subtopic_name} (page {page_num + 1})")
                        break
            
            # Extract Level 3 topics (N1, N2, A1, etc.)
            if current_tier and current_level1_topic:
                code_match = re.match(r'^([NARGS])(\d+)\s*(.+)?$', line)
                if code_match:
                    letter = code_match.group(1)
                    number = code_match.group(2)
                    description = code_match.group(3).strip() if code_match.group(3) else ""
                    
                    # Map letter to topic name
                    letter_to_topic = {
                        'N': 'Number',
                        'A': 'Algebra',
                        'R': 'Ratio',
                        'G': 'Geometry',
                        'S': 'Statistics'
                    }
                    topic_name = letter_to_topic.get(letter, current_level1_topic)
                    
                    # Determine parent: use subtopic if exists, otherwise Level 1 topic
                    if current_level2_subtopic_code:
                        parent_code = current_level2_subtopic_code
                    else:
                        parent_code = f"{current_tier}_{topic_name}"
                    
                    # Build Level 3 topic code
                    level3_code = f"{parent_code}_{letter}{number}"
                    level3_title = f"{letter}{number}"
                    if description:
                        level3_title += f" {description}"
                    
                    current_level3_code = level3_code
                    
                    new_topics.append({
                        'code': level3_code,
                        'title': level3_title,
                        'level': 3,
                        'parent_code': parent_code
                    })
                    
                    print(f"      [L3] {letter}{number}: {description[:50] if description else ''}...")
                    
                    # Look ahead for Level 4 content (all paragraphs including bullets)
                    content_lines = []
                    
                    for j in range(i + 1, min(i + 25, len(lines))):
                        next_line = lines[j]
                        
                        # Stop conditions
                        if re.match(r'^[NARGS]\d+\s*', next_line):  # Another topic code
                            break
                        if re.match(r'^\d+\.\s+', next_line):  # Another section
                            break
                        if re.search(r'(Foundation|Higher)\s+tier', next_line, re.IGNORECASE):
                            break
                        
                        # Check for known subtopic headers
                        is_subtopic = False
                        all_subtopics = [
                            'Structure and calculation', 'Fractions, decimals and percentages',
                            'Measures and accuracy', 'Notation, vocabulary and manipulation',
                            'Graphs', 'Solving equations and inequalities', 'Sequences',
                            'Properties and constructions', 'Mensuration and calculation',
                            'Vectors', 'Probability', 'Statistics'
                        ]
                        for subtopic in all_subtopics:
                            if subtopic.lower() in next_line.lower():
                                is_subtopic = True
                                break
                        if is_subtopic:
                            break
                        
                        # Skip headers
                        if re.search(r'What students need to learn', next_line, re.IGNORECASE):
                            continue
                        
                        # Collect ALL content (including bullets)
                        if next_line and len(next_line) > 10:
                            if not re.match(r'^[A-Z][A-Z\s]+$', next_line):  # Not all caps
                                # Include bullets as part of content
                                content_lines.append(next_line)
                    
                    # Create Level 4 topic if we have content
                    if content_lines:
                        content_text = ' '.join(content_lines).strip()
                        if len(content_text) > 30:  # Minimum length for Level 4
                            level4_code = f"{level3_code}_Content"
                            new_topics.append({
                                'code': level4_code,
                                'title': content_text,
                                'level': 4,
                                'parent_code': level3_code
                            })
                            print(f"        [L4] {content_text[:80]}...")
    
    pdf_doc.close()
    print(f"\n[OK] Extracted {len(new_topics)} new topics")
    pdf_path.unlink()
    
    return new_topics


def upsert_topics(config, subject_id, new_topics, existing_topics):
    """Upsert extracted topics with proper parent linking and ordering."""
    subject = config['subject']
    print(f"\n[INFO] Upserting {len(new_topics)} topics...")
    
    try:
        # Delete old scraped content (Level 2+)
        all_topics = supabase.table('staging_aqa_topics').select('id, topic_code, topic_level').eq('subject_id', subject_id).execute()
        
        to_delete = []
        for t in all_topics.data:
            if t['topic_level'] >= 2:
                to_delete.append(t['id'])
        
        if to_delete:
            for topic_id in to_delete:
                supabase.table('staging_aqa_topics').delete().eq('id', topic_id).execute()
            print(f"[OK] Cleared {len(to_delete)} old topics")
        
        # Build code_to_id map including existing topics (Level 0 and 1)
        code_to_id = {}
        for code, topic_info in existing_topics.items():
            code_to_id[code] = topic_info['id']
        
        # Reorder Level 2 subtopics based on first Level 3 code appearance
        level2_topics = [t for t in new_topics if t['level'] == 2]
        level3_topics = [t for t in new_topics if t['level'] == 3]
        
        # Build mapping of subtopic code to first Level 3 code number
        subtopic_first_code = {}
        for l3 in level3_topics:
            # Extract the subtopic parent and the number from code (e.g., N1, A1)
            parent = l3.get('parent_code')
            code_match = re.search(r'([A-Z])(\d+)', l3['code'])
            if parent and code_match:
                number = int(code_match.group(2))
                if parent not in subtopic_first_code:
                    subtopic_first_code[parent] = number
                else:
                    subtopic_first_code[parent] = min(subtopic_first_code[parent], number)
        
        # Sort Level 2 topics by their first Level 3 code
        level2_sorted = sorted(level2_topics, key=lambda t: subtopic_first_code.get(t['code'], 999))
        
        # Replace Level 2 topics in new_topics with sorted version
        other_topics = [t for t in new_topics if t['level'] != 2]
        new_topics_sorted = level2_sorted + other_topics
        
        # Insert by level (2, 3, 4) to ensure parents exist before children
        for level_num in [2, 3, 4]:
            level_topics = [t for t in new_topics_sorted if t['level'] == level_num]
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
                parent_code = t.get('parent_code')
                parent_id = code_to_id.get(parent_code)
                
                if not parent_id:
                    print(f"  [WARN] Parent '{parent_code}' not found for {t['code']}")
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
                # Add to code_to_id for next level
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
        print("Usage: python mathematics-stage2-scrape.py <config-file.yaml>")
        print("\nExample:")
        print("  python mathematics-stage2-scrape.py configs/mathematics.yaml")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    if not Path(config_path).exists():
        print(f"[ERROR] Config file not found: {config_path}")
        sys.exit(1)
    
    print("=" * 80)
    print("MATHEMATICS STAGE 2 PDF SCRAPER")
    print("=" * 80)
    
    try:
        config = load_config(config_path)
        subject_id, existing_topics, config = get_existing_structure(config)
        
        if not subject_id:
            return
        
        new_topics = extract_mathematics_content(config, existing_topics)
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
