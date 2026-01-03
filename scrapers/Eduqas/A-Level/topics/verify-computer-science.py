"""Verify Computer Science extraction completeness."""
import json
import sys
from pathlib import Path
from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

# Get Computer Science topics from database
print("Fetching Computer Science topics from database...")
result = supabase.table('staging_aqa_subjects').select('id, subject_name').eq('subject_name', 'Computer Science').eq('qualification_type', 'A-Level').eq('exam_board', 'WJEC').execute()

if not result.data:
    print("[ERROR] Computer Science subject not found in database")
    sys.exit(1)

subject_id = result.data[0]['id']
print(f"Found subject: {result.data[0]['subject_name']} (ID: {subject_id})\n")

# Get all topics
topics_result = supabase.table('staging_aqa_topics').select('*').eq('subject_id', subject_id).eq('exam_board', 'WJEC').order('topic_code').execute()

topics = topics_result.data
print(f"Total topics in database: {len(topics)}\n")

# Group by level
by_level = {}
for topic in topics:
    level = topic.get('topic_level', 0)
    if level not in by_level:
        by_level[level] = []
    by_level[level].append(topic)

print("Topics by level:")
for level in sorted(by_level.keys()):
    print(f"  Level {level}: {len(by_level[level])} topics")

# Show Level 0 topics (Components)
print("\n" + "="*80)
print("LEVEL 0 TOPICS (Components):")
print("="*80)
for topic in sorted(by_level.get(0, []), key=lambda x: x.get('topic_code', '')):
    print(f"  {topic.get('topic_code', 'N/A'):20s} | {topic.get('topic_name', 'N/A')[:60]}")

# Show Level 1 topics (Main topics under each component)
print("\n" + "="*80)
print("LEVEL 1 TOPICS (Main Topics):")
print("="*80)
for topic in sorted(by_level.get(1, []), key=lambda x: x.get('topic_code', '')):
    print(f"  {topic.get('topic_code', 'N/A'):20s} | {topic.get('topic_name', 'N/A')[:60]}")

# Show sample Level 2-4 topics
print("\n" + "="*80)
print("SAMPLE LEVEL 2-4 TOPICS (showing first 20):")
print("="*80)
all_levels_2_4 = []
for level in [2, 3, 4]:
    all_levels_2_4.extend(by_level.get(level, []))
for topic in sorted(all_levels_2_4, key=lambda x: x.get('topic_code', ''))[:20]:
    level = topic.get('topic_level', 0)
    print(f"  L{level} | {topic.get('topic_code', 'N/A'):20s} | {topic.get('topic_name', 'N/A')[:55]}")

# Expected structure from PDF:
print("\n" + "="*80)
print("EXPECTED STRUCTURE (from PDF):")
print("="*80)
print("""
Component 1: Programming and System Development
  1. Data structures
  2. Logical operations
  3. Algorithms and programs
  4. Principles of programming
  5. Systems analysis
  6. System design
  7. Software engineering
  8. Program construction
  9. Economic, moral, legal, ethical and cultural issues

Component 2: Computer Architecture, Data, Communication and Applications
  1. Hardware and communication
  2. Data transmission
  3. Data representation and data structures
  4. Organisation and structure of data
  5. The use of computer systems
  6. Database systems
  7. The operating system
  8. Data security and integrity processes
  9. Artificial intelligence (AI)

Component 3: Programmed Solution to a Problem (NEA - less content)
""")

print("\n" + "="*80)
print("VERIFICATION:")
print("="*80)
print(f"✓ Found {len(by_level.get(0, []))} Components (expected: 3)")
print(f"✓ Found {len(by_level.get(1, []))} Level 1 topics")
print(f"✓ Total topics: {len(topics)}")
print(f"\nCheck if all main topics from Components 1 & 2 are present above.")





















