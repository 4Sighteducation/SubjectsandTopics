"""
Run Art Subjects Only
=====================

Processes only Art subjects (J170-J176) that share the same PDF.
The universal scraper will automatically group them by PDF URL and
process them together efficiently.
"""

import sys
import os
import importlib.util
from pathlib import Path

# Change to script directory
script_dir = Path(__file__).parent
os.chdir(script_dir)

# Import the scraper module (filename has hyphens, so use importlib)
scraper_path = script_dir / "ocr-gcse-universal-scraper.py"
spec = importlib.util.spec_from_file_location("ocr_gcse_universal_scraper", scraper_path)
scraper_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scraper_module)

# Art subject codes
ART_SUBJECT_CODES = ['J170', 'J171', 'J172', 'J173', 'J174', 'J175', 'J176']

def main():
    print("\n" + "🎨 "*40)
    print("OCR GCSE ART SUBJECTS SCRAPER")
    print("🎨 "*40)
    print("\nProcessing Art subjects:")
    for code in ART_SUBJECT_CODES:
        print(f"  - {code}")
    print("\nAll subjects share the same PDF, so they will be processed together.")
    print("Each subject will get filtered content with prefix:")
    print("  'GCSE Art and Design - [Subject Name] (GCSE)'")
    print("="*80)
    
    scraper = scraper_module.UniversalGCSEscraper()
    
    # Load all subjects
    all_subjects = scraper.load_subjects()
    
    # Filter to only Art subjects
    art_subjects = [s for s in all_subjects if s['code'] in ART_SUBJECT_CODES]
    
    if not art_subjects:
        print("[ERROR] No Art subjects found!")
        return False
    
    print(f"\n[INFO] Found {len(art_subjects)} Art subjects")
    
    # Override load_subjects to return only Art subjects
    original_load = scraper.load_subjects
    scraper.load_subjects = lambda: art_subjects
    
    # Run scraper (it will group by PDF URL automatically)
    success = scraper.scrape_all()
    
    # Restore original method
    scraper.load_subjects = original_load
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

