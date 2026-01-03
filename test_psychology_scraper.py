#!/usr/bin/env python
"""
Test Recursive Web Scraper on Psychology
Blind test to verify it works on different subjects
"""

import os
import sys
from pathlib import Path

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.uk.aqa_recursive_web_scraper import AQARecursiveWebScraper

def main():
    print("=" * 80)
    print("BLIND TEST: Psychology A-Level")
    print("Testing if recursive scraper works without adaptations")
    print("=" * 80)
    
    scraper = AQARecursiveWebScraper(headless=True)
    
    try:
        result = scraper.scrape_subject_complete_deep(
            subject="Psychology",
            qualification="A-Level",
            subject_code="7182"
        )
        
        print("\n" + "=" * 80)
        print("RESULTS:")
        print("=" * 80)
        
        content_items = result.get('content_items', [])
        print(f"Main sections found: {len(content_items)}")
        
        total_topics = sum(len(item.get('table_rows', [])) for item in content_items)
        print(f"Total sub-topics: {total_topics}")
        
        print(f"\nBreakdown by section:")
        for item in content_items:
            rows_count = len(item.get('table_rows', []))
            print(f"  {item.get('code')}: {item.get('title')[:50]} → {rows_count} topics")
        
        print("\n" + "=" * 80)
        
        if total_topics > 30:
            print("✓ SUCCESS! Scraper is versatile - works on Psychology too!")
            print(f"✓ Got {total_topics} topics (good coverage)")
        elif total_topics > 0:
            print(f"⚠ PARTIAL: Got {total_topics} topics (might need tweaking)")
        else:
            print("✗ FAILED: No topics extracted")
        
        print("=" * 80)
        
    finally:
        scraper.close()


if __name__ == '__main__':
    main()




















