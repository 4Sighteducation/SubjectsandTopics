"""
Complete OCR Web Scraper
Handles all OCR qualifications: A-Level, GCSE, Entry Level, Cambridge Nationals, etc.
Adapts to OCR's unit group structure.
"""

import re
import time
import yaml
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Dict, List, Tuple
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.base_scraper import BaseScraper
from utils.logger import get_logger

logger = get_logger()


class OCRCompleteScraper(BaseScraper):
    """
    Complete OCR scraper for all qualification types.
    
    Handles:
    - AS and A Level
    - GCSE  
    - Entry Level
    - Cambridge Advanced Nationals
    - Cambridge Technicals
    - Cambridge Nationals
    - Core Maths
    """
    
    def __init__(self, headless=True):
        super().__init__(
            name="OCR",
            base_url="https://www.ocr.org.uk",
            headless=headless,
            delay=1.5
        )
        
        # Load subject config
        config_path = Path(__file__).parent.parent.parent / 'config' / 'ocr_subjects.yaml'
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
    
    def scrape_subject_complete(self, subject_key: str, qualification: str) -> Dict:
        """
        Scrape complete subject content for any OCR qualification.
        
        Args:
            subject_key: e.g., "History_A", "Mathematics_A"
            qualification: "a_level", "gcse", etc.
            
        Returns:
            Complete subject data with hierarchical content
        """
        # Get subject info from config
        if qualification not in self.config:
            logger.error(f"Unknown qualification: {qualification}")
            return {}
        
        if subject_key not in self.config[qualification]:
            logger.error(f"Unknown subject: {subject_key} for {qualification}")
            return {}
        
        subject_code = self.config[qualification][subject_key]
        subject_slug = self.config['subject_slugs'].get(subject_key, subject_key.lower().replace('_', '-'))
        subject_name = subject_key.replace('_', ' ')
        
        logger.info(f"Scraping OCR {subject_name} ({qualification.upper()}) - {subject_code}")
        
        # Build qualification URL
        qual_slug = self._get_qualification_slug(qualification)
        
        # Build subject page URL
        # Pattern: /qualifications/{qual}/{subject}-{code}/
        subject_url = f"{self.base_url}/qualifications/{qual_slug}/{subject_slug}-{subject_code}/"
        
        logger.info(f"Subject URL: {subject_url}")
        
        # Step 1: Get specification overview
        spec_overview = self._scrape_specification_overview(subject_url)
        
        # Step 2: Get detailed content
        # OCR typically has content under "Content" or specific unit pages
        content = self._scrape_content_structure(subject_url, subject_code)
        
        return {
            'subject': subject_name,
            'qualification': qualification,
            'code': subject_code,
            'overview': spec_overview,
            'content_structure': content,
            'exam_board': 'OCR'
        }
    
    def _get_qualification_slug(self, qualification: str) -> str:
        """Convert qualification to URL slug."""
        mapping = {
            'a_level': 'as-and-a-level',
            'gcse': 'gcse',
            'entry_level': 'entry-level',
            'cambridge_advanced_nationals': 'cambridge-advanced-nationals',
            'cambridge_technicals': 'cambridge-technicals',
            'cambridge_nationals': 'cambridge-nationals',
            'core_maths': 'core-maths'
        }
        return mapping.get(qualification, qualification.replace('_', '-'))
    
    def _scrape_specification_overview(self, subject_url: str) -> Dict:
        """
        Scrape 'Specification at a glance' page.
        This shows unit groups and selection rules.
        """
        spec_glance_url = f"{subject_url}specification-at-a-glance/"
        
        logger.info(f"Scraping specification overview: {spec_glance_url}")
        
        html = self._get_page(spec_glance_url, use_selenium=False)
        if not html:
            logger.warning("Could not load specification overview")
            return {}
        
        soup = BeautifulSoup(html, 'lxml')
        
        result = {
            'unit_groups': [],
            'selection_rules': [],
            'assessment_overview': []
        }
        
        # Extract assessment overview table if present
        tables = soup.find_all('table')
        for table in tables:
            # Look for assessment overview table
            if 'component' in str(table).lower() or 'unit' in str(table).lower():
                result['assessment_overview'].append(self._parse_assessment_table(table))
        
        # Extract unit groups from content
        # Look for "Unit group 1", "Unit group 2", etc.
        unit_group_pattern = re.compile(r'Unit group (\d+)', re.I)
        
        for heading in soup.find_all(['h2', 'h3', 'h4']):
            text = heading.get_text()
            match = unit_group_pattern.search(text)
            
            if match:
                group_num = match.group(1)
                
                # Get description and options from following content
                unit_info = {
                    'group_number': group_num,
                    'title': text.strip(),
                    'options': []
                }
                
                # Find next ul or list of options
                next_elem = heading.find_next_sibling()
                while next_elem and next_elem.name not in ['h2', 'h3', 'h4']:
                    if next_elem.name == 'ul':
                        for li in next_elem.find_all('li', recursive=False):
                            option_text = li.get_text().strip()
                            if option_text and len(option_text) > 5:
                                unit_info['options'].append(option_text)
                    elif next_elem.name == 'p':
                        # Might contain selection rule
                        p_text = next_elem.get_text()
                        if 'select' in p_text.lower() or 'choose' in p_text.lower():
                            unit_info['selection_rule'] = p_text.strip()
                    
                    next_elem = next_elem.find_next_sibling()
                
                result['unit_groups'].append(unit_info)
        
        return result
    
    def _parse_assessment_table(self, table) -> Dict:
        """Parse assessment overview table."""
        data = []
        rows = table.find_all('tr')
        
        headers = []
        for row in rows:
            cells = row.find_all(['th', 'td'])
            if row.find('th'):
                headers = [c.get_text().strip() for c in cells]
            else:
                row_data = [c.get_text().strip() for c in cells]
                if row_data:
                    data.append(dict(zip(headers, row_data)))
        
        return data
    
    def _scrape_content_structure(self, subject_url: str, subject_code: str) -> List[Dict]:
        """
        Scrape actual content/topics for the subject.
        OCR may have different structures - unit pages, content pages, etc.
        """
        content_items = []
        
        # Try to find content pages
        # OCR typically links to individual unit pages or has content sections
        
        html = self._get_page(subject_url, use_selenium=True)
        if not html:
            return content_items
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Look for links to individual units or content pages
        # Pattern: h105/Y100, h105/Y101, etc. or unit pages
        
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href')
            text = link.get_text().strip()
            
            # Look for unit links (Y100, Y101, etc.) or topic links
            if subject_code.split('-')[0].lower() in href.lower():
                # This might be a unit/content page
                if any(keyword in href.lower() for keyword in ['unit', 'content', 'topic', 'y1', 'y2', 'y3']):
                    full_url = urljoin(self.base_url, href)
                    
                    # Extract unit code from URL if possible
                    unit_match = re.search(r'([YH]\d+)', href, re.I)
                    unit_code = unit_match.group(1) if unit_match else text[:10]
                    
                    content_items.append({
                        'code': unit_code,
                        'title': text,
                        'url': full_url
                    })
        
        # Remove duplicates
        seen = set()
        unique_items = []
        for item in content_items:
            key = (item['code'], item['title'])
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        logger.info(f"Found {len(unique_items)} content items")
        
        return unique_items
    
    def scrape_topics(self, subject=None, exam_type=None):
        """Legacy method."""
        return []
    
    def scrape_papers(self, subject=None, exam_type=None, year_from=2021):
        """Legacy method."""
        return []


if __name__ == '__main__':
    # Quick test
    scraper = OCRCompleteScraper()
    
    result = scraper.scrape_subject_complete("History_A", "a_level")
    
    import json
    print(json.dumps(result, indent=2)[:1500])
