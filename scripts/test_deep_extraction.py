#!/usr/bin/env python
"""
Test deep extraction with History 1B (Spain in the Age of Discovery).
This will extract all 3 levels of content.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.deep_content_extractor import DeepContentExtractor
from extractors.specification_extractor import SpecificationExtractor
from dotenv import load_dotenv
import json
import PyPDF2

load_dotenv()

def main():
    print("=" * 80)
    print("DEEP EXTRACTION TEST: History 1B - Spain in the Age of Discovery")
    print("=" * 80)
    
    # Load the PDF
    pdf_path = "data/raw/AQA/specifications/History_A-Level_spec.pdf"
    
    print(f"\nReading PDF: {pdf_path}")
    
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
    
    print(f"Extracted {len(full_text)} characters from PDF")
    
    # Initialize deep extractor
    extractor = DeepContentExtractor()
    
    # Extract complete content for option 1B
    print("\nExtracting deep content for 1B: Spain in the Age of Discovery...")
    print("This may take 30-60 seconds...\n")
    
    result = extractor.extract_option_complete(
        pdf_text=full_text,
        option_code="1B",
        option_title="Spain in the Age of Discovery, 1469-1598",
        subject="History"
    )
    
    # Save result
    output_file = "data/test_deep_extraction_1B.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"Saved to: {output_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("EXTRACTION RESULTS")
    print("=" * 80)
    
    if result:
        print(f"\nOption: {result.get('option_code')} - {result.get('option_title')}")
        
        key_qs = result.get('key_questions', [])
        print(f"\nKey Questions: {len(key_qs)}")
        for i, q in enumerate(key_qs[:3], 1):
            print(f"  {i}. {q}")
        if len(key_qs) > 3:
            print(f"  ... and {len(key_qs) - 3} more")
        
        study_areas = result.get('study_areas', [])
        print(f"\nStudy Areas: {len(study_areas)}")
        
        total_sections = 0
        total_points = 0
        
        for area in study_areas:
            print(f"\n  {area.get('area_title')}")
            sections = area.get('sections', [])
            total_sections += len(sections)
            
            for section in sections:
                points = section.get('content_points', [])
                total_points += len(points)
                print(f"    - {section.get('section_title')}: {len(points)} content points")
        
        print(f"\nTOTAL:")
        print(f"  Study Areas: {len(study_areas)}")
        print(f"  Sections: {total_sections}")
        print(f"  Content Points: {total_points}")
        
        print("\n" + "=" * 80)
        print("SUCCESS! Complete hierarchical extraction working!")
        print("=" * 80)
        
        return 0
    else:
        print("\nFailed to extract content")
        return 1

if __name__ == '__main__':
    exit(main())




