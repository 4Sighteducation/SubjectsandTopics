"""
AQA Assessment Resources Scraper
Scrapes past papers, mark schemes, and examiner reports from AQA website
Uses Selenium because AQA loads resources dynamically
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.base_scraper import BaseScraper
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from datetime import datetime
import time
from utils.logger import get_logger

logger = get_logger()


class AQAAssessmentScraper(BaseScraper):
    """
    Scrape assessment resources from AQA for a subject.
    URL pattern: /subjects/{subject}/{qual}/{subject}-{code}/assessment-resources
    """
    
    def __init__(self, headless=True):
        super().__init__(
            name="AQA Assessment",
            base_url="https://www.aqa.org.uk",
            headless=headless,
            delay=2.0
        )
    
    def scrape_assessment_resources(self, subject: str, qualification: str, 
                                   subject_code: str, years: list = None) -> dict:
        """
        Scrape assessment resources for a subject.
        
        Args:
            subject: Subject name (e.g., "History")
            qualification: "A-Level" or "GCSE"
            subject_code: AQA code (e.g., "7042")
            years: List of years to scrape (default: [2024, 2023, 2022])
        
        Returns:
            {
                'subject': str,
                'qualification': str,
                'code': str,
                'papers': [
                    {
                        'year': 2024,
                        'series': 'June',
                        'paper_number': 1,
                        'question_paper_url': '...',
                        'mark_scheme_url': '...',
                        'examiner_report_url': '...'
                    }
                ]
            }
        """
        logger.info(f"Scraping assessment resources for {subject} ({qualification})")
        
        if years is None:
            years = [2024, 2023, 2022]
        
        # Build assessment resources URL
        subject_slug = subject.lower().replace(' ', '-')
        if 'art' in subject_slug:
            subject_slug = 'art-and-design'
        
        qual_slug = qualification.lower().replace(' ', '-')
        
        resources_url = f"{self.base_url}/subjects/{subject_slug}/{qual_slug}/{subject_slug}-{subject_code}/assessment-resources"
        
        logger.info(f"Assessment resources URL: {resources_url}")
        
        all_papers = []
        
        try:
            # Scrape multiple pages (AQA paginates results)
            # History needs more pages (30 components × multiple years = lots of pages!)
            for page_num in range(1, 40):  # Up to 40 pages for complex subjects like History
                page_url = f"{resources_url}?page={page_num}" if page_num > 1 else resources_url
                
                logger.info(f"Scraping page {page_num}: {page_url}")
                
                # Use base scraper's Selenium method
                html = self._get_page(page_url, use_selenium=True)
                
                if not html:
                    logger.warning(f"Failed to get page {page_num}")
                    break
                
                # Scroll to load lazy content
                if self.driver:
                    for i in range(2):
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1)
                    html = self.driver.page_source
                
                soup = BeautifulSoup(html, 'lxml')
                
                papers = []
                
                # Find all links on THIS page - AQA uses cdn.sanity.io for PDFs
                all_links = soup.find_all('a', href=True)
                
                logger.info(f"Page {page_num}: Found {len(all_links)} total links")
                
                # Filter for PDF links (sanity CDN or .pdf extension)
                pdf_links = [
                    link for link in all_links 
                    if '.pdf' in link.get('href', '').lower() or 'cdn.sanity.io' in link.get('href', '')
                ]
                
                logger.info(f"Page {page_num}: Found {len(pdf_links)} PDF links")
                
                for link in pdf_links:
                    href = link.get('href')
                    text = link.get_text().strip()
                
                    # Skip modified/accessibility versions (large font PDFs)
                    if 'modified' in text.lower():
                        logger.debug(f"Skipping modified version: {text[:60]}")
                        continue
                
                    # Try to extract year
                    year_match = re.search(r'20(2[0-4])', text + href)
                    if not year_match:
                        logger.debug(f"No year found: {text[:60]}")
                        continue
                    
                    year = int('20' + year_match.group(1))
                    if year not in years:
                        logger.debug(f"Year {year} not in range: {text[:60]}")
                        continue
                    
                    # Extract series (June, November)
                    series = 'June'  # Default
                    if 'nov' in text.lower() or 'nov' in href.lower():
                        series = 'November'
                    
                    # Determine document type - check text (format: "Biology - Mark scheme: Paper 1 - June 2024")
                    text_lower = text.lower()
                    
                    doc_type = None
                    
                    # IMPORTANT: Check most specific first!
                    # Mark scheme detection
                    if 'mark scheme' in text_lower:
                        doc_type = 'mark_scheme'
                        logger.info(f"Found MARK SCHEME: {text[:80]}")
                    # Examiner report detection  
                    elif 'examiner' in text_lower or ('report' in text_lower and 'question' not in text_lower):
                        doc_type = 'examiner_report'
                        logger.info(f"Found EXAMINER REPORT: {text[:80]}")
                    # Question paper
                    elif 'question paper' in text_lower or 'question' in text_lower:
                        doc_type = 'question_paper'
                        logger.info(f"Found QUESTION PAPER: {text[:80]}")
                    else:
                        # Log what we're skipping to debug
                        logger.warning(f"UNKNOWN TYPE - skipping: {text[:80]}")
                        continue
                    
                    # Extract paper number if present
                    paper_match = re.search(r'paper\s*(\d+)|p(\d+)', text.lower())
                    paper_num = int(paper_match.group(1) or paper_match.group(2)) if paper_match else 1
                    
                    # Full URL
                    full_url = urljoin(self.base_url, href)
                
                    papers.append({
                        'year': year,
                        'series': series,
                        'paper_number': paper_num,
                        'doc_type': doc_type,
                        'url': full_url,
                        'title': text
                    })
                
                # Add this page's papers to total
                all_papers.extend(papers)
                logger.info(f"Page {page_num}: Added {len(papers)} documents (total so far: {len(all_papers)})")
                
                # Keep going even if 0 on a page (examiner reports might be on page 8!)
                # Only stop if we've gone 3 pages with nothing
                if len(papers) == 0:
                    if page_num > 10:  # Safety limit
                        logger.info(f"Stopping at page {page_num} (too many empty pages)")
                        break
                    # Otherwise continue - content might be on later pages
                
                time.sleep(2)  # Be polite to AQA servers
            
            logger.info(f"Total found: {len(all_papers)} assessment documents")
            
            return {
                'subject': subject,
                'qualification': qualification,
                'code': subject_code,
                'papers': all_papers
            }
            
        except Exception as e:
            logger.error(f"Error scraping assessment resources: {e}")
            return {'papers': []}
    
    def scrape_topics(self, subject=None, exam_type=None):
        """Not used for assessment scraper."""
        return []
    
    def scrape_papers(self, subject=None, exam_type=None, year_from=2021):
        """Not used - use scrape_assessment_resources instead."""
        return []
    
    def download_paper(self, url: str, subject: str, year: int, 
                      series: str, doc_type: str, paper_num: int = 1) -> str:
        """Download a paper and return local filepath."""
        from utils.helpers import sanitize_filename, ensure_directory
        
        # Create directory structure
        output_dir = f"data/assessment_resources/AQA/{subject}/{year}_{series}"
        ensure_directory(output_dir)
        
        # Filename
        filename = f"{doc_type}_paper{paper_num}_{year}_{series}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        # Check if exists
        if os.path.exists(filepath):
            logger.info(f"Already downloaded: {filepath}")
            return filepath
        
        # Download
        try:
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None


if __name__ == '__main__':
    # Quick test with Biology (simpler than History)
    scraper = AQAAssessmentScraper(headless=True)
    
    try:
        result = scraper.scrape_assessment_resources(
            subject="Biology",
            qualification="A-Level",
            subject_code="7402",
            years=[2024, 2023, 2022]
        )
        
        print(f"\nFound {len(result['papers'])} assessment documents for Biology")
        
        # Show breakdown
        from collections import Counter
        doc_types = Counter(p['doc_type'] for p in result['papers'])
        print(f"\nBreakdown:")
        for doc_type, count in doc_types.items():
            print(f"  {doc_type}: {count}")
        
        # Show first 10
        print(f"\nFirst 10 documents:")
        for i, paper in enumerate(result['papers'][:10], 1):
            print(f"{i}. {paper['year']} {paper['series']} - {paper['doc_type']} (Paper {paper['paper_number']})")
            print(f"   {paper['url'][:80]}...")
        
        # Download first 3 as test
        print(f"\nDownloading first 3 documents...")
        for paper in result['papers'][:3]:
            filepath = scraper.download_paper(
                paper['url'],
                result['subject'],
                paper['year'],
                paper['series'],
                paper['doc_type'],
                paper['paper_number']
            )
            
    finally:
        scraper.close()
