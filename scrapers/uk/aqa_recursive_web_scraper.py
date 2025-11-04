"""
AQA Recursive Web Scraper
Goes deep into each section's page and extracts table content
This is what we should have been doing from the start!
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.uk.aqa_web_scraper import AQAWebScraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils.logger import get_logger
import time

logger = get_logger()


class AQARecursiveWebScraper(AQAWebScraper):
    """Extends base web scraper to go deep into section pages."""
    
    def scrape_subject_complete_deep(self, subject: str, qualification: str, 
                                    subject_code: str) -> dict:
        """
        Scrape complete subject with DEEP content extraction.
        Goes into each section page and extracts table rows.
        """
        logger.info(f"Deep scraping {subject} ({qualification})")
        
        # Step 1: Get main sections
        base_result = self.scrape_subject_content_complete(
            subject, qualification, subject_code
        )
        
        if not base_result or not base_result.get('content_items'):
            logger.error("No main sections found")
            return base_result
        
        logger.info(f"Found {len(base_result['content_items'])} main sections")
        
        # Step 2: For each section, scrape its detail page
        enriched_items = []
        
        for idx, item in enumerate(base_result['content_items'], 1):
            logger.info(f"[{idx}/{len(base_result['content_items'])}] Deep scraping: {item.get('code')} {item.get('title')[:40]}")
            
            # Extract table content from this section's page
            section_url = item.get('url')
            if section_url:
                table_rows = self._extract_table_rows(section_url)
                
                if table_rows:
                    logger.info(f"  Found {len(table_rows)} table rows:")
                    for row in table_rows:
                        logger.info(f"    - {row['title']}")
                    item['table_rows'] = table_rows
                else:
                    logger.warning(f"  No table rows found")
            
            enriched_items.append(item)
            time.sleep(1)  # Be polite
        
        base_result['content_items'] = enriched_items
        
        # Count total topics
        total_topics = sum(len(item.get('table_rows', [])) for item in enriched_items)
        logger.info(f"Total topics extracted: {total_topics}")
        
        return base_result
    
    def _extract_table_rows(self, url: str) -> list:
        """Extract content - tries tables first, then headings."""
        
        html = self._get_page(url, use_selenium=False)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        
        # METHOD 1: Try tables first (Law format)
        rows = self._extract_from_tables(soup)
        if rows:
            logger.info(f"    Extracted {len(rows)} topics from tables")
            return rows
        
        # METHOD 2: Fallback to headings (Psychology format)
        rows = self._extract_from_headings(soup)
        if rows:
            logger.info(f"    Extracted {len(rows)} topics from headings")
            return rows
        
        logger.warning(f"    No content found (tried tables and headings)")
        return []
    
    def _extract_from_tables(self, soup) -> list:
        """Extract from table format (SIMPLE - what worked before)."""
        rows = []
        tables = soup.find_all('table')
        
        for table in tables:
            headers = [th.get_text().strip() for th in table.find_all('th')]
            
            if 'Content' in headers or 'Additional information' in headers:
                for tr in table.find_all('tr')[1:]:
                    cells = tr.find_all('td')
                    
                    if len(cells) >= 2:
                        topic_name = cells[0].get_text().strip()
                        description = cells[1].get_text().strip()
                        
                        if topic_name and len(topic_name) > 3:
                            rows.append({
                                'title': topic_name,
                                'description': description,
                                'level': 1  # All table rows Level 1 for now
                            })
        
        return rows
    
    def _extract_from_headings(self, soup) -> list:
        """Extract from heading format (Psychology style)."""
        import re
        rows = []
        
        # Find all h3 headings with numbers (3.1.1, 3.1.2, etc.)
        headings = soup.find_all(['h3', 'h4'])
        
        for heading in headings:
            text = heading.get_text().strip()
            
            # Check if it has a number pattern (3.1.1, 3.2.3, etc.)
            if re.match(r'^\d+\.\d+\.\d+', text):
                # Find bullet points after this heading
                bullets = []
                next_elem = heading.find_next_sibling()
                
                while next_elem and next_elem.name not in ['h3', 'h4', 'h2']:
                    if next_elem.name == 'ul':
                        bullets = [li.get_text().strip() for li in next_elem.find_all('li')]
                        break
                    next_elem = next_elem.find_next_sibling()
                
                description = ' '.join(bullets[:3]) if bullets else ""  # First 3 bullets
                
                rows.append({
                    'title': text,
                    'description': description,
                    'level': 1
                })
        
        return rows


if __name__ == '__main__':
    # Test with Law
    scraper = AQARecursiveWebScraper(headless=True)
    
    try:
        result = scraper.scrape_subject_complete_deep(
            subject="Law",
            qualification="A-Level",
            subject_code="7162"
        )
        
        print(f"\nFound {len(result.get('content_items', []))} main sections")
        
        total_rows = sum(len(item.get('table_rows', [])) for item in result.get('content_items', []))
        print(f"Total table rows: {total_rows}")
        
        # Show breakdown
        print(f"\nBreakdown:")
        for item in result.get('content_items', []):
            rows = len(item.get('table_rows', []))
            print(f"  {item.get('code')}: {rows} topics")
        
        # Show first section's topics WITH descriptions
        if result.get('content_items'):
            first = result['content_items'][0]
            print(f"\nSample from {first.get('code')} (with descriptions):")
            for row in first.get('table_rows', [])[:5]:
                print(f"  Title: {row['title']}")
                print(f"  Desc:  {row.get('description', 'No description')[:100]}...")
                print()
        
    finally:
        scraper.close()
