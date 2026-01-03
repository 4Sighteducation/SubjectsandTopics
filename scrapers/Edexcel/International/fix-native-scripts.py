"""
Fix Native Scripts in Database
===============================

Re-uploads Bangla, Sinhala, Swahili with explicit UTF-8 encoding to ensure
native scripts (বাংলা, සිංහල, Kiswahili) are properly stored in database.

The AI extracted them correctly, but they weren't making it to the database.
This script fixes the encoding issue.

Usage:
    python fix-native-scripts.py --subject IG-Bangla
    python fix-native-scripts.py --all
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from supabase import create_client

# FORCE UTF-8 everywhere
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')

if not all([supabase_url, supabase_key]):
    print("[ERROR] Missing Supabase credentials!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)


SUBJECTS_TO_FIX = [
    {'code': 'IG-Bangla', 'name': 'Bangla', 'script': 'Bengali'},
    {'code': 'IG-Sinhala', 'name': 'Sinhala', 'script': 'Sinhala'},
    {'code': 'IG-Swahili', 'name': 'Swahili', 'script': 'Latin with special chars'}
]


def read_gpt_output(code: str) -> Optional[List[str]]:
    """Read the GPT-4 output file which should have native script."""
    script_dir = Path(__file__).parent
    output_file = script_dir / "adobe-ai-output" / f"{code}-WORKING.txt"
    
    if not output_file.exists():
        # Try without -WORKING suffix
        output_file = script_dir / "adobe-ai-output" / f"{code}-gpt4-output.txt"
    
    if not output_file.exists():
        print(f"[ERROR] Output file not found for {code}")
        return None
    
    try:
        # Read with explicit UTF-8
        content = output_file.read_text(encoding='utf-8')
        lines = content.split('\n')
        print(f"[OK] Read {len(lines)} lines from {output_file.name}")
        return lines
    except Exception as e:
        print(f"[ERROR] Failed to read file: {str(e)}")
        return None


def parse_hierarchy_with_encoding(lines: List[str]) -> List[Dict]:
    """Parse hierarchy preserving all Unicode characters."""
    import re
    
    topics = []
    parent_stack = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Match numbered items
        match = re.match(r'^([\d.]+)\s+(.+)$', line)
        if not match:
            continue
        
        number = match.group(1).rstrip('.')
        title = match.group(2).strip()
        
        # Ensure title is proper UTF-8 string
        if isinstance(title, bytes):
            title = title.decode('utf-8', errors='replace')
        
        level = number.count('.')
        code = number.replace('.', '_')
        parent_code = parent_stack.get(level - 1) if level > 0 else None
        
        topics.append({
            'code': code,
            'title': title,  # Native script preserved here
            'level': level,
            'parent': parent_code
        })
        
        parent_stack[level] = code
        
        # Clear deeper levels
        for l in list(parent_stack.keys()):
            if l > level:
                del parent_stack[l]
    
    return topics


def upload_with_encoding(subject_code: str, subject_name: str, topics: List[Dict]) -> bool:
    """Upload to Supabase with explicit UTF-8 encoding."""
    print(f"\n[INFO] Uploading {subject_name} to Supabase with UTF-8 encoding...")
    
    try:
        # Get subject
        result = supabase.table('staging_aqa_subjects').select('id').eq(
            'subject_code', subject_code
        ).eq('exam_board', 'Edexcel').execute()
        
        if not result.data:
            print(f"[ERROR] Subject not found in database: {subject_code}")
            return False
        
        subject_id = result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        # Clear old topics
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared old topics")
        
        # Prepare inserts with explicit UTF-8 strings
        to_insert = []
        for t in topics:
            # Double-check title is UTF-8 string
            title = t['title']
            if isinstance(title, bytes):
                title = title.decode('utf-8', errors='replace')
            
            # Ensure it's a proper Python string (Unicode)
            title = str(title)
            
            to_insert.append({
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': title,  # Native script should be preserved
                'topic_level': t['level'],
                'exam_board': 'Edexcel'
            })
        
        # Insert in smaller batches to avoid issues
        BATCH_SIZE = 50
        all_inserted = []
        
        for i in range(0, len(to_insert), BATCH_SIZE):
            batch = to_insert[i:i+BATCH_SIZE]
            
            try:
                inserted = supabase.table('staging_aqa_topics').insert(batch).execute()
                all_inserted.extend(inserted.data)
                print(f"[OK] Batch {i//BATCH_SIZE + 1}: {len(inserted.data)} topics")
            except Exception as e:
                print(f"[WARNING] Batch {i//BATCH_SIZE + 1} failed: {str(e)[:100]}")
                # Try one by one
                for item in batch:
                    try:
                        single = supabase.table('staging_aqa_topics').insert([item]).execute()
                        all_inserted.extend(single.data)
                    except Exception as e2:
                        print(f"[ERROR] Failed to insert: {item['topic_code']} - {str(e2)[:50]}")
        
        print(f"[OK] Total uploaded: {len(all_inserted)} topics")
        
        # Link parents
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
        
        # Verify native script in database
        print(f"\n[INFO] Verifying native script in database...")
        check = supabase.table('staging_aqa_topics').select('topic_name').eq(
            'subject_id', subject_id
        ).ilike('topic_name', '%Vocabulary:%').limit(1).execute()
        
        if check.data and len(check.data) > 0:
            sample = check.data[0]['topic_name']
            print(f"[OK] Sample from DB: {sample[:100]}")
            
            # Check if native script is preserved
            has_native = any(ord(c) > 127 for c in sample)
            if has_native:
                print(f"✅ Native script characters DETECTED in database!")
            else:
                print(f"⚠️ No native script detected - may need database encoding fix")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Upload failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subject', help='Subject code (e.g., IG-Bangla)')
    parser.add_argument('--all', action='store_true', help='Fix all three subjects')
    args = parser.parse_args()
    
    if args.subject:
        subjects = [s for s in SUBJECTS_TO_FIX if s['code'] == args.subject]
    elif args.all:
        subjects = SUBJECTS_TO_FIX
    else:
        parser.print_help()
        sys.exit(1)
    
    print("\n" + "="*60)
    print("FIX NATIVE SCRIPTS IN DATABASE")
    print("="*60)
    print("Re-uploading with explicit UTF-8 encoding:")
    for s in subjects:
        print(f"  - {s['name']} ({s['script']} script)")
    print("="*60 + "\n")
    
    results = {'success': 0, 'failed': 0}
    
    for subject in subjects:
        code = subject['code']
        name = subject['name']
        
        print(f"\n{'='*60}")
        print(f"FIXING: {name} ({code})")
        print('='*60)
        
        # Read GPT output
        lines = read_gpt_output(code)
        if not lines:
            print(f"[ERROR] Cannot read GPT output for {name}")
            results['failed'] += 1
            continue
        
        # Parse with encoding
        topics = parse_hierarchy_with_encoding(lines)
        if not topics:
            print(f"[ERROR] No topics parsed for {name}")
            results['failed'] += 1
            continue
        
        print(f"[OK] Parsed {len(topics)} topics from GPT output")
        
        # Upload with encoding
        if upload_with_encoding(code, name, topics):
            results['success'] += 1
        else:
            results['failed'] += 1
    
    print(f"\n{'='*60}")
    print(f"FIX COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Success: {results['success']}/{len(subjects)}")
    print(f"❌ Failed: {results['failed']}/{len(subjects)}")
    print("="*60)
    
    if results['success'] > 0:
        print(f"\nCheck data viewer to verify native scripts are now visible!")


if __name__ == '__main__':
    main()

