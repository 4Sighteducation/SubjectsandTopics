"""
GCSE Statistics - Structure Uploader
====================================

Uploads Statistics GCSE topics from edexcel statistics gcse.md

Usage:
    python upload-statistics.py
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
    'code': 'GCSE-Statistics',
    'name': 'Statistics',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Statistics/2017/specification-and-sample-assessments/gcse-2017-statistics-spec.pdf'
}

print("=" * 80)
print("GCSE STATISTICS - STRUCTURE UPLOADER")
print("=" * 80)
print("Reading content from edexcel statistics gcse.md...")
print("=" * 80)

# Read content from file
md_file = Path(__file__).parent / "edexcel statistics gcse.md"
HIERARCHY_TEXT = md_file.read_text(encoding='utf-8')

print(f"[INFO] Loaded {len(HIERARCHY_TEXT)} characters")
print()


def parse_hierarchy(text):
    """Parse Statistics hierarchy."""
    lines = [line.rstrip() for line in text.strip().split('\n') if line.strip()]
    
    topics = []
    current_section = None  # Level 0
    current_subsection = None  # Level 1
    current_topic = None  # Level 2
    
    for line in lines:
        # Skip header line
        if 'Examined Content for Pearson Edexcel' in line:
            continue
        
        # Detect "1. Name" (Level 0)
        if re.match(r'^\d+\.\s+[A-Z]', line):
            section_match = re.match(r'^(\d+)\.\s+(.+)$', line)
            if section_match:
                section_num = section_match.group(1)
                section_name = section_match.group(2).strip()
                section_code = f"Section{section_num}"
                
                topics.append({
                    'code': section_code,
                    'title': line.strip(),
                    'level': 0,
                    'parent': None
                })
                
                current_section = section_code
                current_subsection = None
                current_topic = None
                print(f"[L0] {line.strip()}")
                continue
        
        # Detect "(a) Name" (Level 1)
        if re.match(r'^\([a-z]\)\s+', line) and current_section:
            subsection_match = re.match(r'^\(([a-z])\)\s+(.+)$', line)
            if subsection_match:
                letter = subsection_match.group(1)
                subsection_name = subsection_match.group(2).strip()
                subsection_code = f"{current_section}_Sub{letter}"
                
                topics.append({
                    'code': subsection_code,
                    'title': line.strip(),
                    'level': 1,
                    'parent': current_section
                })
                
                current_subsection = subsection_code
                current_topic = None
                print(f"  [L1] {line.strip()}")
                continue
        
        # Detect "1a.01:" or "3p.01:" (Level 2 if has subsection, Level 1 if no subsection)
        if re.match(r'^\d+[a-z]\.\d+:', line):
            code_match = re.match(r'^(\d+[a-z]\.\d+):\s*(.+)$', line)
            if code_match:
                code_number = code_match.group(1)
                code_title = code_match.group(2).strip()
                code_safe = code_number.replace('.', '_')
                
                if current_subsection:
                    # Has subsection, so this is Level 2
                    topic_code = f"{current_subsection}_T{code_safe}"
                    level = 2
                    parent = current_subsection
                elif current_section:
                    # No subsection, attach directly to section as Level 1
                    topic_code = f"{current_section}_T{code_safe}"
                    level = 1
                    parent = current_section
                else:
                    continue
                
                topics.append({
                    'code': topic_code,
                    'title': line.strip(),
                    'level': level,
                    'parent': parent
                })
                
                current_topic = topic_code
                indent = "    " if level == 2 else "  "
                print(f"{indent}[L{level}] {code_number}: {code_title[:50]}...")
                continue
        
        # Everything else is detail (Level 3 if parent is Level 2, Level 2 if parent is Level 1)
        if line and current_topic:
            item_num = len([t for t in topics if t.get('parent') == current_topic]) + 1
            item_code = f"{current_topic}_Item{item_num}"
            
            # Determine level based on parent level
            parent_topic = next((t for t in topics if t['code'] == current_topic), None)
            if parent_topic:
                detail_level = parent_topic['level'] + 1
            else:
                detail_level = 3
            
            topics.append({
                'code': item_code,
                'title': line.strip(),
                'level': detail_level,
                'parent': current_topic
            })
            
            indent = "        " if detail_level == 3 else ("      " if detail_level == 2 else "    ")
            print(f"{indent}[L{detail_level}] {line.strip()[:60]}...")
    
    return topics


def upload_topics(topics):
    """Upload to Supabase."""
    print(f"\n[INFO] Uploading {len(topics)} topics...")
    
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
            'exam_board': SUBJECT_INFO['exam_board']
        } for t in topics]
        
        inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted.data)} topics")
        
        # Link parent relationships
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
        print("[SUCCESS] STATISTICS - UPLOAD COMPLETE!")
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
    print("[INFO] Parsing hierarchy...")
    topics = parse_hierarchy(HIERARCHY_TEXT)
    
    if not topics:
        print("[ERROR] No topics found!")
        sys.exit(1)
    
    print(f"\n[OK] Parsed {len(topics)} topics")
    
    success = upload_topics(topics)
    
    if success:
        print("\n✅ STATISTICS COMPLETE!")
    else:
        print("\n❌ FAILED")


if __name__ == '__main__':
    main()

