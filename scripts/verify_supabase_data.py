#!/usr/bin/env python
"""
Verify what was uploaded to Supabase and analyze the structure.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.supabase_client import SupabaseUploader
from dotenv import load_dotenv
import json

load_dotenv()

uploader = SupabaseUploader()

print("=" * 80)
print("SUPABASE DATA VERIFICATION - AQA History A-Level")
print("=" * 80)

# 1. Check specification_metadata
print("\n1. SPECIFICATION METADATA")
print("-" * 80)
metadata = uploader.client.table('specification_metadata').select('*').eq(
    'subject_name', 'History'
).eq('exam_board', 'AQA').execute()

if metadata.data:
    m = metadata.data[0]
    print(f"Metadata ID: {m['id']}")
    print(f"Subject Code: {m['subject_code']}")
    print(f"Spec Version: {m['spec_version']}")
    print(f"Description: {m['subject_description'][:100]}...")
    print(f"Guided Learning Hours: {m['total_guided_learning_hours']}")
    print(f"Assessment Overview: {m['assessment_overview'][:100]}...")
    spec_id = m['id']
else:
    print("No metadata found!")
    spec_id = None

# 2. Check spec_components
print("\n2. COMPONENTS")
print("-" * 80)
if spec_id:
    components = uploader.client.table('spec_components').select('*').eq(
        'spec_metadata_id', spec_id
    ).order('sort_order').execute()
    
    for c in components.data:
        print(f"\n{c['component_name']}:")
        print(f"  Code: {c['component_code']}")
        print(f"  Type: {c['selection_type']}")
        print(f"  Selection: Choose {c['count_required']} from {c['total_available']}")
        print(f"  Weight: {c['assessment_weight']}")

# 3. Check selection_constraints
print("\n3. SELECTION CONSTRAINTS")
print("-" * 80)
if spec_id:
    constraints = uploader.client.table('selection_constraints').select('*').eq(
        'spec_metadata_id', spec_id
    ).execute()
    
    for c in constraints.data:
        print(f"\n{c['constraint_type']}:")
        print(f"  Description: {c['description']}")
        print(f"  Rule details: {json.dumps(c['constraint_rule'], indent=2)[:200]}...")

# 4. Check curriculum_topics (the 30 options we uploaded)
print("\n4. CURRICULUM TOPICS (History Options)")
print("-" * 80)
topics = uploader.client.table('curriculum_topics').select(
    'topic_code, topic_name, topic_type, geographical_region, chronological_period, topic_level'
).eq('topic_type', 'breadth_study').limit(5).execute()

print(f"Sample topics (showing 5 of 30):")
for t in topics.data:
    print(f"\n  {t['topic_code']}: {t['topic_name']}")
    print(f"    Period: {t.get('chronological_period')}")
    print(f"    Region: {t.get('geographical_region')}")
    print(f"    Level: {t['topic_level']}")

# Count total
total = uploader.client.table('curriculum_topics').select(
    'id', count='exact'
).eq('exam_board_subject_id', '7c1dfb21-94a3-47c7-99fa-9692d91c5f5d').execute()

print(f"\nTotal curriculum_topics for AQA History A-Level: {total.count}")

# 5. Check subject_vocabulary
print("\n5. SUBJECT VOCABULARY")
print("-" * 80)
if spec_id:
    vocab = uploader.client.table('subject_vocabulary').select('*').eq(
        'spec_metadata_id', spec_id
    ).execute()
    
    print(f"Vocabulary terms: {len(vocab.data)}")
    for v in vocab.data:
        print(f"  - {v['term']} ({v['category']})")

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)

print("""
What We Have:
✅ 1 Specification metadata record (overview)
✅ 3 Components (Component 1, 2, 3 structure)
✅ 4 Selection constraints (rules about choosing)
✅ 30 Topic options (the choosable eras like "1B Spain")
✅ 1+ Vocabulary terms

What We DON'T Have Yet:
❌ Detailed study areas within each option (Part one, Part two)
❌ Specific content points (the bullet points)
❌ Key questions for each option

Current Database Structure:
- specification_metadata → Stores overview
- spec_components → Stores component structure
- selection_constraints → Stores rules
- curriculum_topics → Stores the 30 options (using existing table!)
  - Uses exam_board_subject_id as foreign key
  - Has topic_level (0 = option level)
  - Could add level 1 = study areas, level 2 = content points

Recommendation:
The current schema can handle hierarchical topics via parent_topic_id.
We can use topic_level to distinguish:
  - Level 0 = Choosable option (1B Spain)
  - Level 1 = Study area (Part one: New Monarchy)  
  - Level 2 = Content point (Charles' inheritance)

This won't break your app - it's additive!
""")

print("=" * 80)




