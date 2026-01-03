"""
GCSE Astronomy - Structure Uploader
===================================

Uploads Astronomy GCSE topics from edexcel astronomy gcse.md

Usage:
    python upload-astronomy.py
"""

import os
import sys
import re
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

SUBJECT_INFO = {
    'code': 'GCSE-Astronomy',
    'name': 'Astronomy',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Astronomy/2017/Specification%20and%20sample%20assessments/gcse-astronomy-specification.pdf'
}

print("=" * 80)
print("GCSE ASTRONOMY - STRUCTURE UPLOADER")
print("=" * 80)
print("Reading content from edexcel astronomy gcse.md...")
print("=" * 80)

# Read content from file
md_file = Path(__file__).parent / "edexcel astronomy gcse.md"
HIERARCHY_TEXT = md_file.read_text(encoding='utf-8')

print(f"[INFO] Loaded {len(HIERARCHY_TEXT)} characters")
print()

def parse_hierarchy(text):
    """Parse Astronomy hierarchy."""
    lines = [line.rstrip() for line in text.strip().split('\n') if line.strip()]
    
    topics = []
    current_paper = None  # Level 0
    current_topic = None  # Level 1
    current_section = None  # Level 2
    current_subsection = None  # Level 3
    
    for line in lines:
        # Detect "Paper X:" (Level 0)
        if re.match(r'^Paper\s+\d+:', line, re.IGNORECASE):
            paper_match = re.match(r'^Paper\s+(\d+):\s*(.+)$', line, re.IGNORECASE)
            if paper_match:
                paper_num = paper_match.group(1)
                paper_code = f"Paper{paper_num}"
                
                topics.append({
                    'code': paper_code,
                    'title': line.strip(),
                    'level': 0,
                    'parent': None
                })
                
                current_paper = paper_code
                current_topic = None
                current_section = None
                current_subsection = None
                print(f"[L0] {line.strip()}")
                continue
        
        # Detect "Topic X –" (Level 1)
        if re.match(r'^Topic\s+\d+\s*[:\-–]', line, re.IGNORECASE):
            topic_match = re.match(r'^Topic\s+(\d+)\s*[:\-–]\s*(.*)$', line, re.IGNORECASE)
            if topic_match and current_paper:
                topic_num = topic_match.group(1)
                topic_code = f"{current_paper}_Topic{topic_num}"
                
                topics.append({
                    'code': topic_code,
                    'title': line.strip(),
                    'level': 1,
                    'parent': current_paper
                })
                
                current_topic = topic_code
                current_section = None
                current_subsection = None
                print(f"  [L1] {line.strip()}")
                continue
        
        # Detect "9.1" (Level 2)
        if re.match(r'^\d+\.\d+\s', line) and not re.match(r'^\d+\.\d+\.\d+', line) and current_topic:
            section_match = re.match(r'^(\d+\.\d+)\s+(.+)$', line)
            if section_match:
                section_number = section_match.group(1)
                section_title = section_match.group(2).strip()
                section_code = f"{current_topic}_S{section_number.replace('.', '_')}"
                
                topics.append({
                    'code': section_code,
                    'title': line.strip(),
                    'level': 2,
                    'parent': current_topic
                })
                
                current_section = section_code
                current_subsection = None
                print(f"    [L2] {line.strip()[:60]}...")
                continue
        
        # Detect "9.5.1" (Level 3)
        if re.match(r'^\d+\.\d+\.\d+\s', line) and current_section:
            subsection_match = re.match(r'^(\d+\.\d+\.\d+)\s+(.+)$', line)
            if subsection_match:
                subsection_number = subsection_match.group(1)
                subsection_title = subsection_match.group(2).strip()
                subsection_code = f"{current_section}_SS{subsection_number.replace('.', '_')}"
                
                topics.append({
                    'code': subsection_code,
                    'title': line.strip(),
                    'level': 3,
                    'parent': current_section
                })
                
                current_subsection = subsection_code
                print(f"      [L3] {line.strip()[:60]}...")
                continue
        
        # Everything else is detail (Level 3 if no section, Level 4 if has subsection)
        if line and (current_topic or current_section or current_subsection):
            parent = current_subsection or current_section or current_topic
            parent_topic = next((t for t in topics if t['code'] == parent), None)
            if parent_topic:
                detail_level = parent_topic['level'] + 1
                item_num = len([t for t in topics if t.get('parent') == parent]) + 1
                item_code = f"{parent}_Item{item_num}"
                
                topics.append({
                    'code': item_code,
                    'title': line.strip(),
                    'level': detail_level,
                    'parent': parent
                })
                
                indent = "          " if detail_level == 4 else ("        " if detail_level == 3 else "      ")
                print(f"{indent}[L{detail_level}] {line.strip()[:60]}...")
    
    return topics

topics = parse_hierarchy(HIERARCHY_TEXT)

if not topics:
    print("[ERROR] No topics found!")
    sys.exit(1)

print(f"\n[OK] Parsed {len(topics)} topics")

# Now upload
try:
    # Create/update subject
    subject_result = supabase.table('staging_aqa_subjects').upsert({
        'subject_name': f"{SUBJECT_INFO['name']} ({SUBJECT_INFO['qualification']})",
        'subject_code': SUBJECT_INFO['code'],
        'qualification_type': SUBJECT_INFO['qualification'],
        'specification_url': SUBJECT_INFO['pdf_url'],
        'exam_board': SUBJECT_INFO['exam_board']
    }, on_conflict='subject_code,qualification_type,exam_board').execute()
    
    subject_id = subject_result.data[0]['id']
    print(f"[INFO] Subject ID: {subject_id}")
    
    # Clear old topics
    supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
    print("[OK] Cleared old topics")
    
    # Insert topics
    to_insert = [{
        'subject_id': subject_id,
        'topic_code': t['code'],
        'topic_name': t['title'],
        'topic_level': t['level'],
        'exam_board': SUBJECT_INFO['exam_board']
    } for t in topics]
    
    inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
    print(f"[OK] Uploaded {len(inserted.data)} topics")
    
    # Link parents
    code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
    
    for level_num in [1, 2, 3, 4]:
        level_topics = [t for t in topics if t['level'] == level_num and t['parent']]
        linked = 0
        
        for topic in level_topics:
            parent_id = code_to_id.get(topic['parent'])
            child_id = code_to_id.get(topic['code'])
            if parent_id and child_id:
                supabase.table('staging_aqa_topics').update({
                    'parent_topic_id': parent_id
                }).eq('id', child_id).execute()
                linked += 1
        
        if linked > 0:
            print(f"[OK] Linked {linked} Level {level_num} parent relationships")
    
    # Summary
    levels = defaultdict(int)
    for t in topics:
        levels[t['level']] += 1
    
    print("\n" + "=" * 80)
    print("[SUCCESS] ASTRONOMY - UPLOAD COMPLETE!")
    print("=" * 80)
    for level in sorted(levels.keys()):
        print(f"   Level {level}: {levels[level]} topics")
    print(f"\n   Total: {len(topics)} topics")
    print("=" * 80)
    
    print("\n✅ ASTRONOMY COMPLETE!")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

