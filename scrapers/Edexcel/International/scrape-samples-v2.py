"""
Scrape Sample International Subjects (V2 - Improved)
====================================================

Scrapes a few key subjects to verify quality before full batch run.
"""

import subprocess
import sys
from pathlib import Path

# Sample subjects to test
SAMPLES = [
    # International GCSE
    'IG-Biology',
    'IG-Chemistry',
    'IG-Physics',
    'IG-MathematicsA',
    'IG-Business',
    'IG-Economics',
    'IG-Geography',
    'IG-History',
    
    # International A Level
    'IAL-Biology',
    'IAL-Chemistry',
    'IAL-Physics',
    'IAL-Mathematics',
    'IAL-Business',
    'IAL-Economics',
]

def main():
    script_dir = Path(__file__).parent
    scraper = script_dir / 'universal-international-scraper-v2.py'
    
    print(f"Will scrape {len(SAMPLES)} sample subjects for testing...")
    print()
    
    results = {'success': 0, 'failed': 0}
    
    for subject in SAMPLES:
        print(f"\n{'='*60}")
        print(f"SCRAPING: {subject}")
        print('='*60)
        
        try:
            result = subprocess.run(
                [sys.executable, str(scraper), '--subject', subject],
                cwd=script_dir,
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                results['success'] += 1
                print(f"✓ {subject} SUCCESS")
            else:
                results['failed'] += 1
                print(f"✗ {subject} FAILED")
                
        except Exception as e:
            results['failed'] += 1
            print(f"✗ {subject} ERROR: {str(e)}")
    
    # Summary
    print(f"\n{'='*60}")
    print("SAMPLE SCRAPE COMPLETE")
    print('='*60)
    print(f"Success: {results['success']}/{len(SAMPLES)}")
    print(f"Failed: {results['failed']}/{len(SAMPLES)}")
    print('='*60)

if __name__ == '__main__':
    main()

