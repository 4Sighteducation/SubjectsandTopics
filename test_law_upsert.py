#!/usr/bin/env python
"""
Test UPSERT on Law
Verify it creates proper parent-child relationships
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

from database.supabase_client import SupabaseUploader

load_dotenv()


def main():
    print("=" * 80)
    print("LAW UPSERT TEST - Checking Before")
    print("=" * 80)
    
    uploader = SupabaseUploader()
    law_id = uploader._get_or_create_exam_board_subject('AQA', 'Law', 'A-Level', '7162')
    
    # Check current state
    total = uploader.client.table('curriculum_topics').select('id', count='exact').eq(
        'exam_board_subject_id', law_id
    ).execute().count
    
    with_parents = uploader.client.table('curriculum_topics').select('id', count='exact').eq(
        'exam_board_subject_id', law_id
    ).not_.is_('parent_topic_id', 'null').execute().count
    
    print(f"\nBEFORE:")
    print(f"  Total topics: {total}")
    print(f"  With parent_topic_id: {with_parents}")
    
    if total == 0:
        print("\n✓ Clean slate - ready to test!")
    else:
        print(f"\n⚠ Law still has {total} topics")
        print("Please delete them first with:")
        print("DELETE FROM curriculum_topics WHERE exam_board_subject_id = '{law_id}';")
        return 1
    
    print("\n" + "=" * 80)
    print("Running Fixed Scraper on Law...")
    print("=" * 80)
    
    from scrapers.uk.aqa_hybrid_scraper_fixed import AQAHybridScraperFixed
    
    scraper = AQAHybridScraperFixed(headless=True, supabase_uploader=uploader)
    
    try:
        result = scraper.process_subject_complete(
            subject='Law',
            qualification='A-Level',
            subject_code='7162',
            upload_to_supabase=True
        )
        
        print(f"\nScraper result: Success={result['success']}")
        
    finally:
        scraper.close()
    
    print("\n" + "=" * 80)
    print("LAW UPSERT TEST - Checking After")
    print("=" * 80)
    
    # Check after
    total_after = uploader.client.table('curriculum_topics').select('id', count='exact').eq(
        'exam_board_subject_id', law_id
    ).execute().count
    
    with_parents_after = uploader.client.table('curriculum_topics').select('id', count='exact').eq(
        'exam_board_subject_id', law_id
    ).not_.is_('parent_topic_id', 'null').execute().count
    
    # Get samples
    samples = uploader.client.table('curriculum_topics').select(
        'topic_code, topic_name, topic_level, parent_topic_id'
    ).eq('exam_board_subject_id', law_id).order('topic_level').limit(15).execute().data
    
    print(f"\nAFTER:")
    print(f"  Total topics: {total_after}")
    print(f"  With parent_topic_id: {with_parents_after}")
    print(f"\nSample topics:")
    for t in samples:
        indent = "  " * (t['topic_level'] + 1)
        parent = f"→ {t['parent_topic_id'][:8]}..." if t.get('parent_topic_id') else "✗ None"
        print(f"{indent}L{t['topic_level']}: {t['topic_code']} {t['topic_name'][:40]} {parent}")
    
    print("\n" + "=" * 80)
    print("TEST RESULT:")
    print("=" * 80)
    
    if with_parents_after > 0:
        print(f"✓ SUCCESS! {with_parents_after} topics have parent relationships")
        print(f"✓ Total topics: {total_after}")
        print("\nHierarchy is working! Ready to apply to all subjects.")
    else:
        print("✗ FAILED - No parent relationships created")
        print("Need to debug the scraper")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
