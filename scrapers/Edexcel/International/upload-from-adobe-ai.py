"""
Upload Topics from Adobe AI PDF Extraction
===========================================

Takes hierarchical text extracted by Adobe AI and uploads to Supabase.

Format expected:
1. Biology Paper 1
1.1 Topic Name
1.1.1 Sub-topic
1.1.1.1 Detailed item

Usage:
    1. Run Adobe AI on PDF with hierarchy prompt
    2. Save output to text file (e.g., biology-hierarchy.txt)
    3. Edit SUBJECT_INFO and HIERARCHY_FILE below
    4. Run: python upload-from-adobe-ai.py
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
from supabase import create_client

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

# ===== CONFIGURE THESE =====

SUBJECT_INFO = {
    'code': 'IG-Biology',
    'name': 'Biology',
    'qualification': 'International GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/International%20GCSE/Biology/2017/specification-and-sample-assessments/international-gcse-biology-2017-specification1.pdf'
}

# Path to the text file with Adobe AI output
HIERARCHY_FILE = Path(__file__).parent / "adobe-ai-output" / "biology-hierarchy.txt"

# ===========================


def parse_hierarchy_text(text: str) -> List[Dict]:
    """Parse Adobe AI hierarchical output into topic structure."""
    print("\n[INFO] Parsing hierarchy...")
    
    topics = []
    lines = text.split('\n')
    
    parent_stack = {}  # Track parents at each level
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Match numbered items: 1., 1.1, 1.1.1, 1.1.1.1, etc.
        match = re.match(r'^([\d.]+)\s+(.+)$', line)
        if not match:
            continue
        
        number = match.group(1).rstrip('.')  # Remove trailing dot
        title = match.group(2).strip()
        
        # Determine level by counting dots
        level = number.count('.')
        
        # Generate clean code
        code = number.replace('.', '_')  # 1.1.1 → 1_1_1
        
        # Find parent
        parent_code = None
        if level > 0:
            # Parent is at level-1
            parent_code = parent_stack.get(level - 1)
        
        # Create topic entry
        topic = {
            'code': code,
            'title': title,
            'level': level,
            'parent': parent_code,
            'number': number  # Keep for reference
        }
        
        topics.append(topic)
        
        # Update parent stack
        parent_stack[level] = code
        
        # Clear deeper levels
        levels_to_clear = [l for l in parent_stack.keys() if l > level]
        for l in levels_to_clear:
            del parent_stack[l]
    
    print(f"[OK] Parsed {len(topics)} topics")
    
    # Show level breakdown
    by_level = {}
    for topic in topics:
        level = topic['level']
        by_level[level] = by_level.get(level, 0) + 1
    
    print(f"[OK] Level breakdown:")
    for level in sorted(by_level.keys()):
        print(f"  - Level {level}: {by_level[level]} items")
    
    return topics


def upload_to_supabase(subject_info: Dict, topics: List[Dict]) -> bool:
    """Upload topics to Supabase staging tables."""
    print("\n[INFO] Uploading to Supabase...")
    
    try:
        # Create/update subject
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{subject_info['name']} ({subject_info['qualification']})",
            'subject_code': subject_info['code'],
            'qualification_type': subject_info['qualification'],
            'specification_url': subject_info['pdf_url'],
            'exam_board': subject_info['exam_board']
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        if not subject_result.data:
            print("[ERROR] Failed to create/update subject")
            return False
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        # Clear old topics
        try:
            delete_result = supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
            print(f"[OK] Cleared old topics")
        except Exception as e:
            print(f"[WARNING] Clear operation: {str(e)}")
        
        # Insert topics in batches
        BATCH_SIZE = 500
        all_inserted = []
        
        for i in range(0, len(topics), BATCH_SIZE):
            batch = topics[i:i+BATCH_SIZE]
            to_insert = [{
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': t['title'],
                'topic_level': t['level'],
                'exam_board': subject_info['exam_board']
            } for t in batch]
            
            inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
            all_inserted.extend(inserted.data)
            print(f"[OK] Uploaded batch {i//BATCH_SIZE + 1}: {len(inserted.data)} items")
        
        print(f"[OK] Total uploaded: {len(all_inserted)} items")
        
        # Link parent relationships
        code_to_id = {t['topic_code']: t['id'] for t in all_inserted}
        
        linked = 0
        for topic in topics:
            if topic['parent'] and topic['code'] in code_to_id and topic['parent'] in code_to_id:
                try:
                    supabase.table('staging_aqa_topics').update({
                        'parent_topic_id': code_to_id[topic['parent']]
                    }).eq('id', code_to_id[topic['code']]).execute()
                    linked += 1
                except Exception as e:
                    pass
        
        print(f"[OK] Linked {linked} parent relationships")
        return True
        
    except Exception as e:
        print(f"[ERROR] Upload failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("UPLOAD FROM ADOBE AI PDF EXTRACTION")
    print("=" * 60)
    
    # Check if file exists
    if not HIERARCHY_FILE.exists():
        print(f"\n[ERROR] File not found: {HIERARCHY_FILE}")
        print("\nCreate the file and paste Adobe AI output there, or update HIERARCHY_FILE path.")
        
        # Create directory if it doesn't exist
        HIERARCHY_FILE.parent.mkdir(exist_ok=True)
        
        # Create empty file with instructions
        HIERARCHY_FILE.write_text("""# Paste Adobe AI hierarchy output here
# Format:
# 1. Paper Name
# 1.1 Topic Name
# 1.1.1 Sub-topic
# 1.1.1.1 Detailed item
#
# Then run: python upload-from-adobe-ai.py
""", encoding='utf-8')
        
        print(f"\n[OK] Created template file: {HIERARCHY_FILE}")
        print("     Edit this file and paste your Adobe AI output, then run script again.")
        sys.exit(1)
    
    # Read hierarchy file
    print(f"\n[INFO] Reading: {HIERARCHY_FILE}")
    text = HIERARCHY_FILE.read_text(encoding='utf-8')
    
    # Remove comments
    lines = []
    for line in text.split('\n'):
        if not line.strip().startswith('#'):
            lines.append(line)
    text = '\n'.join(lines)
    
    if not text.strip():
        print("[ERROR] File is empty!")
        sys.exit(1)
    
    # Parse
    topics = parse_hierarchy_text(text)
    
    if not topics:
        print("[ERROR] No topics found!")
        sys.exit(1)
    
    # Upload
    success = upload_to_supabase(SUBJECT_INFO, topics)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        print(f"Uploaded {len(topics)} topics for {SUBJECT_INFO['name']}")
        print("Check your data viewer to see the results!")
    else:
        print("\n" + "=" * 60)
        print("❌ FAILED")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()

