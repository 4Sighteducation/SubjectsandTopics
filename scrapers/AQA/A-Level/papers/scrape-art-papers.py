"""
AQA Art and Design A-Level - Past Papers Scraper
Code: 7201 (base code for all Art pathways)

Note: Art papers may be pathway-specific or shared
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.uk.aqa_assessment_scraper import AQAAssessmentScraper
from upload_papers_to_staging import upload_papers_to_staging
from utils.logger import get_logger

logger = get_logger()


def scrape_art_papers():
    """Scrape all past papers for AQA Art and Design A-Level."""
    
    print("=" * 60)
    print("AQA ART AND DESIGN - PAST PAPERS SCRAPER")
    print("=" * 60)
    
    SUBJECT = {
        'name': 'Art and Design',
        'code': '7201',
        'qualification': 'A-Level',
        'years': [2024, 2023, 2022, 2021, 2020]
    }
    
    scraper = None
    
    try:
        logger.info("Initializing Selenium scraper...")
        scraper = AQAAssessmentScraper(headless=True)
        
        print(f"\n🔍 Scraping past papers for {SUBJECT['name']}...")
        print(f"   Subject code: {SUBJECT['code']}")
        print(f"   Years: {SUBJECT['years']}")
        print(f"   This will take 2-3 minutes...\n")
        
        result = scraper.scrape_assessment_resources(
            subject='Art and Design',
            qualification=SUBJECT['qualification'],
            subject_code=SUBJECT['code'],
            years=SUBJECT['years']
        )
        
        papers = result.get('papers', [])
        
        print(f"\n✅ Scraping complete!")
        print(f"   Total documents found: {len(papers)}")
        
        # Show breakdown
        from collections import Counter
        doc_types = Counter(p['doc_type'] for p in papers)
        
        print(f"\n📊 Breakdown:")
        for doc_type, count in doc_types.items():
            print(f"   {doc_type}: {count}")
        
        # Upload to database
        print(f"\n💾 Uploading to staging database...")
        
        uploaded_count = upload_papers_to_staging(
            subject_code=SUBJECT['code'],
            qualification_type=SUBJECT['qualification'],
            papers_data=papers
        )
        
        print(f"\n✅ Upload complete!")
        print(f"   Paper sets uploaded: {uploaded_count}")
        
        # Summary
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"\n{SUBJECT['name']} ({SUBJECT['code']}) - Complete Dataset:")
        print(f"   Topics: Check staging_aqa_topics (run node crawl-aqa-art.js first)")
        print(f"   Papers: {uploaded_count} complete paper sets")
        print(f"\nCheck Supabase:")
        print(f"   - staging_aqa_topics: Art topics")
        print(f"   - staging_aqa_exam_papers: {uploaded_count} records")
        
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
    scrape_art_papers()

