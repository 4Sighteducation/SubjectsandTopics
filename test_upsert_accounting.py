#!/usr/bin/env python
"""
Test UPSERT on Accounting Only
Verify it updates existing topics and creates proper parent-child relationships
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

from database.supabase_client import SupabaseUploader

load_dotenv()


def check_accounting_before():
    """Check current state of Accounting topics."""
    uploader = SupabaseUploader()
    
    accounting_id = uploader._get_or_create_exam_board_subject('AQA', 'Accounting', 'A-Level', '7127')
    
    # Count total topics
    total = uploader.client.table('curriculum_topics').select('id', count='exact').eq(
        'exam_board_subject_id', accounting_id
    ).execute().count
    
    # Count duplicates
    topics = uploader.client.table('curriculum_topics').select('topic_code, topic_level').eq(
        'exam_board_subject_id', accounting_id
    ).execute().data
    
    from collections import Counter
    codes_levels = [(t['topic_code'], t['topic_level']) for t in topics if t.get('topic_code')]
    duplicates = {k: v for k, v in Counter(codes_levels).items() if v > 1}
    
    # Count with parent_topic_id
    with_parents = uploader.client.table('curriculum_topics').select('id', count='exact').eq(
        'exam_board_subject_id', accounting_id
    ).not_.is_('parent_topic_id', None).execute().count
    
    print("=" * 80)
    print("ACCOUNTING TOPICS - BEFORE FIX")
    print("=" * 80)
    print(f"Total topics: {total}")
    print(f"Unique (code, level) combinations: {len(set(codes_levels))}")
    print(f"Duplicated entries: {sum(duplicates.values()) - len(duplicates)}")
    print(f"Topics with parent_topic_id: {with_parents}")
    print(f"\nSample duplicates:")
    for (code, level), count in list(duplicates.items())[:5]:
        print(f"  {code} (Level {level}): {count} copies")
    print("=" * 80)
    
    return accounting_id


def test_fixed_upsert(accounting_id):
    """Test the fixed uploader on Accounting."""
    
    print("\nRunning fixed scraper on Accounting...")
    print("(This will UPDATE existing topics and create proper hierarchy)")
    print()
    
    # Import the hybrid scraper
    from scrapers.uk.aqa_hybrid_scraper_fixed import AQAHybridScraperFixed
    
    uploader = SupabaseUploader()
    scraper = AQAHybridScraperFixed(headless=True, supabase_uploader=uploader)
    
    try:
        result = scraper.process_subject_complete(
            subject='Accounting',
            qualification='A-Level',
            subject_code='7127',
            upload_to_supabase=True
        )
        
        print(f"\nResult: Success={result['success']}, Method={result.get('method')}")
        
    finally:
        scraper.close()


def check_accounting_after(accounting_id):
    """Check state after fix."""
    uploader = SupabaseUploader()
    
    # Count total topics
    total = uploader.client.table('curriculum_topics').select('id', count='exact').eq(
        'exam_board_subject_id', accounting_id
    ).execute().count
    
    # Count unique
    topics = uploader.client.table('curriculum_topics').select('topic_code, topic_level, component_code, parent_topic_id').eq(
        'exam_board_subject_id', accounting_id
    ).execute().data
    
    from collections import Counter
    codes_levels = [(t['topic_code'], t['topic_level']) for t in topics if t.get('topic_code')]
    duplicates = {k: v for k, v in Counter(codes_levels).items() if v > 1}
    
    # Count with parent_topic_id
    with_parents = uploader.client.table('curriculum_topics').select('id', count='exact').eq(
        'exam_board_subject_id', accounting_id
    ).not_.is_('parent_topic_id', None).execute().count
    
    # Count with component_code
    with_components = uploader.client.table('curriculum_topics').select('id', count='exact').eq(
        'exam_board_subject_id', accounting_id
    ).not_.is_('component_code', None).execute().count
    
    print("\n" + "=" * 80)
    print("ACCOUNTING TOPICS - AFTER FIX")
    print("=" * 80)
    print(f"Total topics: {total}")
    print(f"Unique (code, level) combinations: {len(set(codes_levels))}")
    print(f"Duplicated entries: {sum(duplicates.values()) - len(duplicates) if duplicates else 0}")
    print(f"Topics with parent_topic_id: {with_parents}")
    print(f"Topics with component_code: {with_components}")
    
    if duplicates:
        print(f"\nRemaining duplicates:")
        for (code, level), count in list(duplicates.items())[:5]:
            print(f"  {code} (Level {level}): {count} copies")
    else:
        print(f"\n✓ NO DUPLICATES!")
    
    # Show sample with hierarchy
    print(f"\nSample topics with metadata:")
    for t in topics[:5]:
        print(f"  {t['topic_code']} (L{t['topic_level']}): {t.get('component_code', 'no component')}, parent={t.get('parent_topic_id', 'None')[:8] if t.get('parent_topic_id') else 'None'}...")
    
    print("=" * 80)


def main():
    print("\n" + "=" * 80)
    print("TESTING PROPER UPSERT - Accounting Only")
    print("=" * 80)
    
    # Step 1: Check before
    accounting_id = check_accounting_before()
    
    input("\nPress Enter to run the fixed scraper on Accounting...")
    
    # Step 2: Run fixed scraper
    test_fixed_upsert(accounting_id)
    
    # Step 3: Check after
    check_accounting_after(accounting_id)
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nIf this worked:")
    print("- Duplicates reduced")
    print("- Topics have component_code")
    print("- Parent-child relationships created")
    print("\nThen we can:")
    print("- Apply this fix to all subjects")
    print("- Use for other exam boards (OCR, Edexcel)")
    print("=" * 80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())




















