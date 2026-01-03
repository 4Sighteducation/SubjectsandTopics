"""
COMPLETE BIOLOGY SCRAPER - Template for All Subjects

Phase 1: Topics (via Firecrawl - run via Node.js)
Phase 2: Past Papers (via Python/Selenium - this script)

This script ONLY does past papers.
Topics are handled by: node crawl-aqa-biology-complete.js
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.uk.aqa_assessment_scraper import AQAAssessmentScraper
from upload_papers_to_staging import upload_papers_to_staging
from utils.logger import get_logger

logger = get_logger()


def scrape_biology_papers():
    """
    Scrape all past papers for AQA Biology A-Level.
    """
    
    print("=" * 60)
    print("AQA BIOLOGY - PAST PAPERS SCRAPER")
    print("=" * 60)
    
    SUBJECT = {
        'name': 'Biology',
        'code': '7402',
        'qualification': 'A-Level',
        'years': [2024, 2023, 2022, 2021, 2020]  # Last 5 years
    }
    
    scraper = None
    
    try:
        # Initialize scraper with Selenium
        logger.info("Initializing Selenium scraper...")
        scraper = AQAAssessmentScraper(headless=True)
        
        # Scrape assessment resources
        print(f"\n🔍 Scraping past papers for {SUBJECT['name']}...")
        print(f"   Subject code: {SUBJECT['code']}")
        print(f"   Years: {SUBJECT['years']}")
        print(f"   This will take 2-3 minutes...\n")
        
        result = scraper.scrape_assessment_resources(
            subject=SUBJECT['name'],
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
        print(f"   Topics: Already scraped via Firecrawl (70 topics)")
        print(f"   Papers: {uploaded_count} complete paper sets")
        print(f"\nCheck Supabase:")
        print(f"   - staging_aqa_topics: 70 records")
        print(f"   - staging_aqa_exam_papers: {uploaded_count} records")
        print(f"\nNext: Repeat for all AQA subjects!")
        
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
    scrape_biology_papers()

