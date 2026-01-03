"""
Check Statistics in Database
============================

Shows what's in Supabase for Statistics, especially Section 3
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

print("=" * 80)
print("CHECKING STATISTICS IN DATABASE")
print("=" * 80)

# Get subject
subject_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', 'GCSE-Statistics').eq('qualification_type', 'GCSE').eq('exam_board', 'Edexcel').execute()

if not subject_result.data:
    print("[ERROR] Statistics not found in database!")
    sys.exit(1)

subject_id = subject_result.data[0]['id']
print(f"Subject ID: {subject_id}\n")

# Get all topics
topics_result = supabase.table('staging_aqa_topics').select('*').eq('subject_id', subject_id).order('topic_code').execute()

topics = topics_result.data

# Group by level
by_level = defaultdict(list)
for t in topics:
    by_level[t['topic_level']].append(t)

print(f"Total topics in database: {len(topics)}\n")

print("=" * 80)
print("LEVEL 0 (Main Sections):")
print("=" * 80)
for t in by_level[0]:
    print(f"  {t['topic_code']}: {t['topic_name']}")

print("\n" + "=" * 80)
print("SECTION 3 CHILDREN (Should be 13 probability codes):")
print("=" * 80)

# Find Section3
section3 = next((t for t in topics if t['topic_code'] == 'Section3'), None)
if section3:
    section3_id = section3['id']
    print(f"Section3 ID: {section3_id}")
    
    # Find children
    children = [t for t in topics if t.get('parent_topic_id') == section3_id]
    print(f"Children found: {len(children)}\n")
    
    for child in children:
        print(f"  [L{child['topic_level']}] {child['topic_code']}: {child['topic_name'][:80]}")
else:
    print("Section3 not found!")

print("\n" + "=" * 80)
print("LEVEL 1 topics starting with 'Section3':")
print("=" * 80)
level1_section3 = [t for t in by_level[1] if t['topic_code'].startswith('Section3')]
print(f"Found: {len(level1_section3)}\n")
for t in level1_section3[:10]:
    print(f"  {t['topic_code']}: {t['topic_name'][:80]}")
    print(f"    Parent ID: {t.get('parent_topic_id')}")

print("\n" + "=" * 80)
print("SUMMARY BY LEVEL:")
print("=" * 80)
for level in sorted(by_level.keys()):
    print(f"  Level {level}: {len(by_level[level])} topics")

print(f"\n  Total: {len(topics)} topics")
print("=" * 80)

