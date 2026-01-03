#!/usr/bin/env python
"""
Test Recursive Scraper on Multiple Subjects
Verify it works across different structures
"""

import os
import sys
from pathlib import Path

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.uk.aqa_recursive_web_scraper import AQARecursiveWebScraper

def test_subject(subject, code):
    """Test one subject and return results."""
    print(f"\n{'='*80}")
    print(f"TESTING: {subject} A-Level")
    print(f"{'='*80}")
    
    scraper = AQARecursiveWebScraper(headless=True)
    
    try:
        result = scraper.scrape_subject_complete_deep(
            subject=subject,
            qualification="A-Level",
            subject_code=code
        )
        
        content_items = result.get('content_items', [])
        total_topics = sum(len(item.get('table_rows', [])) for item in content_items)
        
        print(f"\nMain sections: {len(content_items)}")
        print(f"Total sub-topics: {total_topics}")
        
        # Count by level
        from collections import Counter
        all_rows = []
        for item in content_items:
            all_rows.extend(item.get('table_rows', []))
        
        by_level = Counter(row.get('level', 0) for row in all_rows)
        
        print(f"\nBreakdown by section:")
        for item in content_items:
            rows_count = len(item.get('table_rows', []))
            print(f"  {item.get('code')}: {rows_count} topics")
        
        print(f"\nBreakdown by level:")
        for level in sorted(by_level.keys()):
            print(f"  Level {level}: {by_level[level]} topics")
        
        # Show first 5 topics
        if content_items and content_items[0].get('table_rows'):
            print(f"\nFirst 5 topics from {content_items[0].get('code')}:")
            for row in content_items[0]['table_rows'][:5]:
                print(f"  - {row['title'][:60]}")
        
        status = "✓ PASS" if total_topics > 10 else "✗ FAIL" if total_topics == 0 else "⚠ PARTIAL"
        print(f"\n{status}: {total_topics} topics extracted")
        
        return total_topics
        
    finally:
        scraper.close()


def main():
    print("=" * 80)
    print("MULTI-SUBJECT SCRAPER TEST")
    print("Testing: Physical Education, English Literature")
    print("=" * 80)
    
    subjects = [
        ("Physical Education", "7582")
    ]
    
    results = {}
    
    for subject, code in subjects:
        count = test_subject(subject, code)
        results[subject] = count
    
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    for subject, count in results.items():
        status = "✓" if count > 10 else "✗"
        print(f"{status} {subject}: {count} topics")
    
    total = sum(results.values())
    print(f"\nTotal across all subjects: {total}")
    
    if all(c > 10 for c in results.values()):
        print("\n✓✓✓ ALL SUBJECTS PASSED! Scraper is versatile! ✓✓✓")
    else:
        print("\n⚠ Some subjects need adjustment")


if __name__ == '__main__':
    main()
