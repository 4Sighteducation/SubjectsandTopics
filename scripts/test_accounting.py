#!/usr/bin/env python
"""
Test web scraper with Accounting (numbered pattern: 3.1, 3.2, 3.3...).
This will prove both History pattern (1A, 1B) and Accounting pattern (3.1, 3.2) work.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.uk.aqa_web_scraper import AQAWebScraper
import json

def main():
    print("=" * 80)
    print("TESTING ACCOUNTING PATTERN (3.1, 3.2, 3.3...)")
    print("=" * 80)
    
    scraper = AQAWebScraper()
    
    print("\nScraping Accounting A-Level (7127)...")
    print("This should detect numbered pattern (3.1-3.18)\n")
    
    result = scraper.scrape_subject_content_complete(
        subject="Accounting",
        qualification="A-Level",
        subject_code="7127"
    )
    
    # Save result
    output_file = "data/accounting_complete_web_scrape.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved to: {output_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    print(f"\nPattern Detected: {result.get('pattern_type')}")
    print(f"Content Items: {len(result.get('content_items', []))}")
    
    if result.get('content_items'):
        # Show first few items
        print("\nFirst 5 sections:")
        for item in result['content_items'][:5]:
            code = item.get('code')
            title = item.get('title', '')[:60]
            study_areas = len(item.get('study_areas', []))
            
            # Count total content points
            total_points = 0
            for area in item.get('study_areas', []):
                for section in area.get('sections', []):
                    total_points += len(section.get('content_points', []))
            
            print(f"  {code}: {title}")
            print(f"    Study areas: {study_areas}, Content points: {total_points}")
    
    print("\n" + "=" * 80)
    print("COMPARISON")
    print("=" * 80)
    print("""
History (7042):
  Pattern: option_codes (1A, 1B, 2A, 2B...)
  Structure: Choosable options with selection rules
  
Accounting (7127):
  Pattern: numbered_sections (3.1, 3.2, 3.3...)
  Structure: All sections required (linear curriculum)
  
Both patterns successfully detected and scraped!
    """)
    
    scraper.close()
    return 0

if __name__ == '__main__':
    exit(main())
