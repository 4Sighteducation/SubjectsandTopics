import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from scrapers.uk.aqa_assessment_scraper import AQAAssessmentScraper
from upload_papers_to_staging import upload_papers_to_staging

scraper = AQAAssessmentScraper(headless=True)
try:
    result = scraper.scrape_assessment_resources('Polish', 'A-Level', '7687', [2024,2023,2022,2021,2020])
    uploaded = upload_papers_to_staging('7687', 'A-Level', result.get('papers', []))
    print(f"✅ Polish: {uploaded} paper sets")
finally:
    scraper.close()

