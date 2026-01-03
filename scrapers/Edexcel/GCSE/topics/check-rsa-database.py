"""
Check Religious Studies A in Database
======================================

Shows what's currently in Supabase for RSA
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
print("CHECKING RELIGIOUS STUDIES A IN DATABASE")
print("=" * 80)

# Get subject
subject_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', 'GCSE-RSA').eq('qualification_type', 'GCSE').eq('exam_board', 'Edexcel').execute()

if not subject_result.data:
    print("[ERROR] Religious Studies A not found in database!")
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
print("LEVEL 0 (Main Areas):")
print("=" * 80)
for t in by_level[0]:
    print(f"  {t['topic_code']}: {t['topic_name']}")

print(f"\nLevel 0 count: {len(by_level[0])}")

print("\n" + "=" * 80)
print("LEVEL 1 (Sub-Areas):")
print("=" * 80)
for t in by_level[1]:
    print(f"  {t['topic_code']}: {t['topic_name']}")

print(f"\nLevel 1 count: {len(by_level[1])}")

print("\n" + "=" * 80)
print("SUMMARY BY LEVEL:")
print("=" * 80)
for level in sorted(by_level.keys()):
    print(f"  Level {level}: {len(by_level[level])} topics")

print(f"\n  Total: {len(topics)} topics")
print("=" * 80)

