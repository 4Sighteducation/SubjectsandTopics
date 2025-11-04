"""
AQA Accounting A-Level - Past Papers Scraper
Code: 7127
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.uk.aqa_assessment_scraper import AQAAssessmentScraper
from upload_papers_to_staging import upload_papers_to_staging
from utils.logger import get_logger

logger = get_logger()


def scrape_accounting_papers():
    """Scrape all past papers for AQA Accounting A-Level."""
    
    print("=" * 60)
    print("AQA ACCOUNTING - PAST PAPERS SCRAPER")
    print("=" * 60)
    
    SUBJECT = {
        'name': 'Accounting',
        'code': '7127',
        'qualification': 'A-Level',
        'years': [2024, 2023, 2022, 2021, 2020]
    }
    
    scraper = None
    
    try:
        logger.info("Initializing Selenium scraper...")
        scraper = AQAAssessmentScraper(headless=True)
        
        print(f"\n🔍 Scraping past papers for {SUBJECT['name']}...")
        print(f"   Subject code: {SUBJECT['code']}")
        print(f"   This will take 2-3 minutes...\n")
        
        result = scraper.scrape_assessment_resources(
            subject=SUBJECT['name'],
            qualification=SUBJECT['qualification'],
            subject_code=SUBJECT['code'],
            years=SUBJECT['years']
        )
        
        papers = result.get('papers', [])
        
        print(f"\n✅ Scraping complete! Found {len(papers)} documents")
        
        from collections import Counter
        doc_types = Counter(p['doc_type'] for p in papers)
        
        print(f"\n📊 Breakdown:")
        for doc_type, count in doc_types.items():
            print(f"   {doc_type}: {count}")
        
        print(f"\n💾 Uploading to staging database...")
        
        uploaded_count = upload_papers_to_staging(
            subject_code=SUBJECT['code'],
            qualification_type=SUBJECT['qualification'],
            papers_data=papers
        )
        
        print(f"\n✅ Complete! Paper sets uploaded: {uploaded_count}")
        
        return uploaded_count
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 0
        
    finally:
        if scraper:
            scraper.close()


if __name__ == '__main__':
    scrape_accounting_papers()

