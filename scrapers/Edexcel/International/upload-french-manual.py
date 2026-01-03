"""
Upload Manual French Hierarchy
===============================

Uploads the manually created French hierarchy with vocabulary, grammar, and phrases.

Usage:
    python upload-french-manual.py
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from supabase import create_client

# FORCE UTF-8
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


SUBJECT_INFO = {
    'code': 'IG-French',
    'name': 'French',
    'qualification': 'International GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/International%20GCSE/French/2017/specification-and-sample-assessments/international-gcse-french-specification.pdf'
}


def parse_hierarchy(file_path: Path) -> List[Dict]:
    """Parse hierarchy file."""
    print(f"\n[INFO] Reading: {file_path.name}")
    
    content = file_path.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    topics = []
    parent_stack = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        match = re.match(r'^([\d.]+)\s+(.+)$', line)
        if not match:
            continue
        
        number = match.group(1).rstrip('.')
        title = match.group(2).strip()
        
        level = number.count('.')
        code = number.replace('.', '_')
        parent_code = parent_stack.get(level - 1) if level > 0 else None
        
        topics.append({
            'code': code,
            'title': title,
            'level': level,
            'parent': parent_code
        })
        
        parent_stack[level] = code
        
        for l in list(parent_stack.keys()):
            if l > level:
                del parent_stack[l]
    
    print(f"[OK] Parsed {len(topics)} topics")
    
    by_level = {}
    for t in topics:
        by_level[t['level']] = by_level.get(t['level'], 0) + 1
    
    print("[OK] Level breakdown:")
    for level in sorted(by_level.keys()):
        print(f"  Level {level}: {by_level[level]} topics")
    
    return topics


def upload_to_supabase(subject_info: Dict, topics: List[Dict]) -> bool:
    """Upload to Supabase."""
    print("\n[INFO] Uploading to Supabase...")
    
    try:
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{subject_info['name']} ({subject_info['qualification']})",
            'subject_code': subject_info['code'],
            'qualification_type': subject_info['qualification'],
            'specification_url': subject_info['pdf_url'],
            'exam_board': subject_info['exam_board']
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared old topics")
        
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': str(t['title']),
            'topic_level': t['level'],
            'exam_board': subject_info['exam_board']
        } for t in topics]
        
        BATCH_SIZE = 100
        all_inserted = []
        
        for i in range(0, len(to_insert), BATCH_SIZE):
            batch = to_insert[i:i+BATCH_SIZE]
            inserted = supabase.table('staging_aqa_topics').insert(batch).execute()
            all_inserted.extend(inserted.data)
            print(f"[OK] Batch {i//BATCH_SIZE + 1}: {len(inserted.data)} topics")
        
        print(f"[OK] Total uploaded: {len(all_inserted)} topics")
        
        code_to_id = {t['topic_code']: t['id'] for t in all_inserted}
        linked = 0
        
        for topic in topics:
            if topic['parent'] and topic['code'] in code_to_id and topic['parent'] in code_to_id:
                try:
                    supabase.table('staging_aqa_topics').update({
                        'parent_topic_id': code_to_id[topic['parent']]
                    }).eq('id', code_to_id[topic['code']]).execute()
                    linked += 1
                except:
                    pass
        
        print(f"[OK] Linked {linked} parent relationships")
        return True
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*60)
    print("UPLOAD MANUAL FRENCH HIERARCHY")
    print("="*60)
    
    hierarchy_file = Path(__file__).parent / "adobe-ai-output" / "french-manual-hierarchy.txt"
    
    if not hierarchy_file.exists():
        print(f"[ERROR] File not found: {hierarchy_file}")
        sys.exit(1)
    
    topics = parse_hierarchy(hierarchy_file)
    
    if not topics:
        print("[ERROR] No topics parsed!")
        sys.exit(1)
    
    success = upload_to_supabase(SUBJECT_INFO, topics)
    
    if success:
        print("\n" + "="*60)
        print("✅ SUCCESS!")
        print("="*60)
        print(f"Uploaded {len(topics)} French topics")
        print("Check data viewer!")
    else:
        print("\n" + "="*60)
        print("❌ FAILED")
        print("="*60)
        sys.exit(1)


if __name__ == '__main__':
    main()

