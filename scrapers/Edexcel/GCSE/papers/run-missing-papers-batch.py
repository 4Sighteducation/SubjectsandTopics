"""
Batch runner for scraping all 16 missing GCSE exam paper subjects
Runs the universal scraper for all subjects that need papers
"""

import subprocess
import sys
from pathlib import Path

# All subjects that need papers scraped (as requested by user)
SUBJECTS_TO_SCRAPE = [
    'GCSE-Biology',
    'GCSE-Chemistry',
    'GCSE-Physics',
    'GCSE-Science',  # Combined Science
    'GCSE-DesignTech',
    'GCSE-EnglishLang',
    'GCSE-EnglishLit',
    'GCSE-GeographyA',
    'GCSE-GeographyB',
    'GCSE-History',
    'GCSE-Mathematics',
    'GCSE-Music',
    'GCSE-PE',
    'GCSE-Statistics',
    'GCSE-ReligiousStudiesA',
    'GCSE-ReligiousStudiesA-Short',
    'GCSE-ReligiousStudiesB',
    'GCSE-ReligiousStudiesB-Short',
]

def main():
    print("=" * 80)
    print("BATCH SCRAPER FOR MISSING GCSE EXAM PAPERS")
    print("=" * 80)
    print(f"Will scrape {len(SUBJECTS_TO_SCRAPE)} subjects")
    print("=" * 80)
    print()
    
    script_path = Path(__file__).parent / 'universal-gcse-paper-scraper.py'
    
    # Run scraper with all subjects at once
    cmd = [sys.executable, str(script_path)] + SUBJECTS_TO_SCRAPE
    
    print(f"Running command:")
    print(f"  python {script_path.name} {' '.join(SUBJECTS_TO_SCRAPE[:3])} ...")
    print()
    
    result = subprocess.run(cmd, cwd=script_path.parent)
    
    print()
    print("=" * 80)
    if result.returncode == 0:
        print("✅ BATCH SCRAPING COMPLETE!")
    else:
        print("❌ BATCH SCRAPING FAILED!")
        print(f"Exit code: {result.returncode}")
    print("=" * 80)
    
    return result.returncode

if __name__ == '__main__':
    sys.exit(main())

