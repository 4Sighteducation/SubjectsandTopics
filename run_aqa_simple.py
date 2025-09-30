#!/usr/bin/env python
"""
SIMPLE AQA runner - Uses the EXACT approach that worked for History.
No complications, just what we know works!
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.uk.aqa_scraper_enhanced import AQAScraperEnhanced
from database.supabase_client import SupabaseUploader
from dotenv import load_dotenv

load_dotenv()

# Load ALL subjects from config
import yaml
config_path = Path(__file__).parent / 'config' / 'aqa_subjects.yaml'
with open(config_path) as f:
    config = yaml.safe_load(f)

# Build complete subject list
SUBJECTS = []

# A-Level subjects
for subject_key, code in config['a_level'].items():
    subject_name = subject_key.replace('_', ' ')
    SUBJECTS.append((subject_name, 'A-Level'))

# GCSE subjects  
for subject_key, code in config['gcse'].items():
    subject_name = subject_key.replace('_', ' ')
    SUBJECTS.append((subject_name, 'GCSE'))

def main():
    print("=" * 80)
    print("SIMPLE AQA PIPELINE - Using Proven History Approach")
    print("=" * 80)
    print(f"\nProcessing {len(SUBJECTS)} subjects\n")
    
    # Initialize
    uploader = SupabaseUploader()
    
    results = {'success': [], 'failed': []}
    
    for i, (subject, qual) in enumerate(SUBJECTS, 1):
        print(f"\n[{i}/{len(SUBJECTS)}] {subject} ({qual})")
        print("-" * 80)
        
        scraper = AQAScraperEnhanced(supabase_uploader=uploader)
        
        try:
            result = scraper.process_subject_complete(
                subject=subject,
                exam_type=qual,
                upload_to_supabase=True
            )
            
            if result['success']:
                print(f"✓ SUCCESS")
                print(f"  - Metadata ID: {result.get('extracted_data', {}).get('metadata', {})}")
                results['success'].append(subject)
            else:
                print(f"✗ FAILED: {result.get('errors')}")
                results['failed'].append(subject)
                
        except Exception as e:
            print(f"✗ ERROR: {e}")
            results['failed'].append(subject)
        
        finally:
            scraper.close()
    
    # Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Successful: {len(results['success'])}/{len(SUBJECTS)}")
    print(f"Failed: {len(results['failed'])}/{len(SUBJECTS)}")
    
    if results['success']:
        print(f"\n✓ Success: {', '.join(results['success'])}")
    if results['failed']:
        print(f"\n✗ Failed: {', '.join(results['failed'])}")
    
    print("=" * 80)
    
    return 0 if len(results['failed']) == 0 else 1

if __name__ == '__main__':
    exit(main())
