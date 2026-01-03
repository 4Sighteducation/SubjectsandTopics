"""
Universal Edexcel GCSE Stage 1 Uploader
========================================

Reads a YAML config file and uploads Level 0, 1, 2 structure to Supabase.

Usage:
    python universal-stage1-upload.py configs/geography-a.yaml
    python universal-stage1-upload.py configs/business.yaml
"""

import os
import sys
import yaml
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


def upload_topics(config):
    """Upload topics to Supabase based on config."""
    subject = config['subject']
    
    print(f"\n[INFO] Uploading structure for {subject['name']}...")
    
    # Build topics list
    topics = []
    
    # Level 0: Components
    for comp in config['components']:
        topics.append({
            'code': comp['code'],
            'title': comp['title'],
            'level': 0,
            'parent': None
        })
    
    # Level 1: Topics
    for topic in config['topics']:
        topics.append({
            'code': topic['code'],
            'title': topic['title'],
            'level': 1,
            'parent': topic['parent']
        })
    
    # Level 2: Optional subtopics (if any)
    if 'optional_subtopics' in config and config['optional_subtopics']:
        for subtopic in config['optional_subtopics']:
            topics.append({
                'code': subtopic['code'],
                'title': subtopic['title'],
                'level': 2,
                'parent': subtopic['parent']
            })
    
    print(f"[INFO] Total topics to upload: {len(topics)}")
    
    try:
        # Create/update subject
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{subject['name']} ({subject['qualification']})",
            'subject_code': subject['code'],
            'qualification_type': subject['qualification'],
            'specification_url': subject['pdf_url'],
            'exam_board': subject['exam_board']
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
            'exam_board': subject['exam_board']
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
        print(f"[SUCCESS] {subject['name'].upper()} - STAGE 1 COMPLETE!")
        print("=" * 80)
        for level in sorted(levels.keys()):
            count = levels[level]
            level_name = ['Components', 'Topics', 'Optional Sub-topics', 'Level 3', 'Level 4'][min(level, 4)]
            print(f"   Level {level} ({level_name}): {count}")
        print(f"\n   Total: {len(topics)} topics")
        print("=" * 80)
        print("\nNext: Run Stage 2 to extract detailed content from PDF")
        
        return subject_id
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python universal-stage1-upload.py <config-file.yaml>")
        print("\nExamples:")
        print("  python universal-stage1-upload.py configs/geography-a.yaml")
        print("  python universal-stage1-upload.py configs/business.yaml")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    if not Path(config_path).exists():
        print(f"[ERROR] Config file not found: {config_path}")
        sys.exit(1)
    
    print("=" * 80)
    print("UNIVERSAL EDEXCEL GCSE - STAGE 1 UPLOADER")
    print("=" * 80)
    
    try:
        config = load_config(config_path)
        subject_id = upload_topics(config)
        
        if subject_id:
            print("\n✅ COMPLETE!")
            print(f"\nSubject ID: {subject_id}")
            print(f"Config: {config_path}")
        else:
            print("\n❌ FAILED")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

