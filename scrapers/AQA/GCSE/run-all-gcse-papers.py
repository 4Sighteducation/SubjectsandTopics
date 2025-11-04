"""
MASTER AQA GCSE PAPERS SCRAPER
Runs ALL GCSE subjects overnight
"""

import os, sys, json
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scrapers.uk.aqa_assessment_scraper import AQAAssessmentScraper
from upload_papers_to_staging import upload_papers_to_staging

# Load subjects
with open(Path(__file__).parent / 'aqa-gcse-subjects.json', 'r') as f:
    data = json.load(f)
    subjects = data['subjects']

print('=' * 70)
print('🚀 AQA GCSE MASTER PAPERS SCRAPER')
print('=' * 70)
print(f'📚 Total subjects to scrape: {len(subjects)}')
print('=' * 70)

scraper = AQAAssessmentScraper(headless=True)
results = []
success_count = 0

try:
    for i, subject in enumerate(subjects):
        print(f"\n[{i+1}/{len(subjects)}] Starting {subject['name']}...")
        print('=' * 70)
        
        try:
            result = scraper.scrape_assessment_resources(
                subject['name'], 
                'GCSE', 
                subject['code'], 
                [2024, 2023, 2022, 2021, 2020]
            )
            
            uploaded = upload_papers_to_staging(
                subject['code'], 
                'GCSE', 
                result.get('papers', [])
            )
            
            print(f"✅ {subject['name']}: {uploaded} paper sets")
            results.append({'subject': subject['name'], 'success': True, 'papers': uploaded})
            success_count += 1
            
        except Exception as e:
            print(f"❌ {subject['name']} FAILED: {str(e)}")
            results.append({'subject': subject['name'], 'success': False, 'error': str(e)})
            
finally:
    scraper.close()

print('\n' + '=' * 70)
print('🎉 GCSE PAPERS SCRAPING COMPLETE!')
print('=' * 70)
print(f"✅ Success: {success_count}/{len(subjects)}")
print(f"❌ Failed: {len(subjects) - success_count}")
print('\nResults:')
for r in results:
    status = '✅' if r['success'] else '❌'
    papers = r.get('papers', 0)
    print(f"  {status} {r['subject']}: {papers} paper sets")

