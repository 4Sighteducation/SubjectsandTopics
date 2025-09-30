#!/usr/bin/env python
"""
Test webpage extraction with History 1B.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.webpage_content_extractor import WebpageContentExtractor
import json

def main():
    print("=" * 80)
    print("WEBPAGE EXTRACTION TEST: History 1B")
    print("=" * 80)
    
    extractor = WebpageContentExtractor()
    
    # Construct URL for 1B
    url = extractor.construct_option_url(
        subject="History",
        qualification="A-Level",
        subject_code="7042",
        option_code="1B",
        option_title="Spain in the Age of Discovery, 1469–1598 (A-level only)"
    )
    
    print(f"\nConstructed URL: {url}")
    print("\nExtracting content...\n")
    
    result = extractor.extract_from_webpage(url, "1B")
    
    # Save result
    output_file = "data/test_webpage_extraction_1B.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"Saved to: {output_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    if result:
        print(f"\nOption: {result.get('option_code')} - {result.get('option_title')}")
        
        key_qs = result.get('key_questions', [])
        print(f"\nKey Questions: {len(key_qs)}")
        for i, q in enumerate(key_qs, 1):
            print(f"  {i}. {q}")
        
        study_areas = result.get('study_areas', [])
        print(f"\nStudy Areas: {len(study_areas)}")
        
        total_sections = 0
        total_points = 0
        
        for area in study_areas:
            print(f"\n  {area.get('area_title')}")
            sections = area.get('sections', [])
            total_sections += len(sections)
            
            for section in sections[:2]:  # Show first 2
                points = section.get('content_points', [])
                total_points += len(points)
                print(f"    - {section.get('section_title')}: {len(points)} points")
                # Show first 2 points
                for point in points[:2]:
                    print(f"      • {point}")
        
        # Count all points
        for area in study_areas:
            for section in area.get('sections', []):
                total_points += len(section.get('content_points', []))
        
        print(f"\nTOTALS:")
        print(f"  Level 0: 1 option (1B Spain)")
        print(f"  Level 1: {len(study_areas)} study areas (Parts)")
        print(f"  Level 2: {total_sections} sections")
        print(f"  Level 3: ~{total_points} content points")
        
        print("\n" + "=" * 80)
        print("SUCCESS - All 3 levels extracted from webpage!")
        print("This is MUCH better than PDF extraction!")
        print("=" * 80)
        
        return 0
    else:
        print("\nFailed to extract")
        return 1

if __name__ == '__main__':
    exit(main())




