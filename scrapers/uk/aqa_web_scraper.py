"""
AQA Web Scraper - Intelligent scraping of AQA website structure.
Handles both Pattern A (numbered sections 3.1, 3.2) and Pattern B (option codes 1A, 1B).
"""

import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Dict, List, Tuple
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.base_scraper import BaseScraper
from utils.logger import get_logger

logger = get_logger()


class AQAWebScraper(BaseScraper):
    """
    Intelligent AQA website scraper that:
    1. Navigates to 3.0 Subject Content
    2. Detects pattern (numbered vs option codes)
    3. Scrapes all subsections
    4. Extracts hierarchical content
    
    NO AI needed for this - pure HTML parsing!
    """
    
    def __init__(self, headless=True):
        super().__init__(
            name="AQA",
            base_url="https://www.aqa.org.uk",
            headless=headless,
            delay=1.5
        )
    
    def scrape_subject_content_complete(self, subject: str, qualification: str,
                                       subject_code: str) -> Dict:
        """
        Scrape complete subject content using web structure.
        
        Returns:
        {
          "subject": "History",
          "qualification": "A-Level",
          "code": "7042",
          "pattern_type": "options" or "sections",
          "content_items": [...]
        }
        """
        logger.info(f"Scraping {subject} ({qualification}) - {subject_code}")
        
        # Step 1: Navigate to subject content page
        subject_content_url = self._build_subject_content_url(subject, qualification, subject_code)
        
        logger.info(f"Subject content URL: {subject_content_url}")
        
        html = self._get_page(subject_content_url, use_selenium=False)
        if not html:
            logger.error("Failed to load subject content page")
            return {}
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Step 2: Detect pattern and get all content links
        pattern_type, content_links = self._detect_pattern_and_get_links(soup, subject_content_url)
        
        logger.info(f"Detected pattern: {pattern_type}")
        logger.info(f"Found {len(content_links)} content sections")
        
        # Step 3: Scrape each content section
        all_content = []
        
        for i, (code, title, url) in enumerate(content_links, 1):
            logger.info(f"[{i}/{len(content_links)}] Scraping {code}: {title}")
            
            content = self._scrape_content_page(url, code, title, pattern_type)
            
            if content:
                all_content.append(content)
            
            time.sleep(1)  # Be polite to AQA servers
        
        return {
            'subject': subject,
            'qualification': qualification,
            'code': subject_code,
            'pattern_type': pattern_type,
            'content_items': all_content
        }
    
    def _build_subject_content_url(self, subject: str, qualification: str, code: str) -> str:
        """
        Build URL for subject content page.
        Handles special cases like Art and Design variants.
        """
        # Default: use subject name as slug
        subject_slug = subject.lower().replace(' ', '-')
        
        # Handle Art and Design - all variants use "art-and-design"
        if 'art-and-design' in subject_slug or 'art and design' in subject.lower():
            subject_slug = "art-and-design"
        
        qual_slug = qualification.lower().replace(' ', '-')
        
        return f"{self.base_url}/subjects/{subject_slug}/{qual_slug}/{subject_slug}-{code}/specification/subject-content"
    
    def _detect_pattern_and_get_links(self, soup: BeautifulSoup, base_url: str) -> Tuple[str, List[Tuple[str, str, str]]]:
        """
        Find all content links under "Subject content" section.
        Robust to handle AQA's inconsistent numbering (3.x, 4.x, or any pattern).
        Returns: (pattern_type, [(code, title, url), ...])
        """
        content_links = []
        
        # Find the "Subject content" section/heading
        subject_content_heading = soup.find(string=re.compile(r'Subject content', re.I))
        
        if subject_content_heading:
            # Get the parent container (could be nav, ul, div, etc.)
            container = subject_content_heading.find_parent(['nav', 'ul', 'div', 'section'])
            
            if container:
                # Get all links within this container
                section_links = container.find_all('a', href=True)
            else:
                # Fallback: get siblings after the heading
                section_links = []
                current = subject_content_heading.find_next_sibling()
                while current and current.name not in ['h1', 'h2']:
                    if current.name == 'a' and current.get('href'):
                        section_links.append(current)
                    elif current.name in ['ul', 'nav']:
                        section_links.extend(current.find_all('a', href=True))
                    current = current.find_next_sibling()
        else:
            # Fallback: look for all content-like links
            section_links = soup.find_all('a', href=True)
        
        # Process the links we found
        for link in section_links:
            text = link.get_text().strip()
            href = link.get('href')
            
            if not text or len(text) < 2:
                continue
            
            # Try to extract code and title from link text
            # Pattern: "X.Y Title" or "XY Title" or just "Title"
            
            # Numbered pattern (3.1, 4.1, 4.2, etc.)
            numbered_match = re.match(r'^(\d+\.\d+)\s+(.+)$', text)
            if numbered_match:
                code = numbered_match.group(1)
                title = numbered_match.group(2)
                url = urljoin(base_url, href)
                content_links.append((code, title, url))
                continue
            
            # Option code pattern (1A, 1B, 2A, 2B, etc.)
            option_match = re.match(r'^([12][A-Z])\s*(.*)$', text)
            if option_match:
                code = option_match.group(1)
                title = option_match.group(2) or link.get('title', '')
                url = urljoin(base_url, href)
                content_links.append((code, title, url))
                continue
            
            # If link looks like subject content (contains subject-content in URL)
            if 'subject-content' in href and text not in ['Subject content', 'Introduction']:
                # Try to extract code from URL
                url_match = re.search(r'/([^/]+)$', href)
                if url_match:
                    code = url_match.group(1).split('-')[0].upper()
                    if len(code) <= 4:  # Reasonable code length
                        url = urljoin(base_url, href)
                        content_links.append((code, text, url))
        
        # Determine pattern type
        if content_links:
            first_code = content_links[0][0]
            # Check if it's numbered (3.1, 4.1, etc.) or option codes (1A, 2B, etc.)
            if re.match(r'^\d+\.\d+$', first_code):
                pattern_type = 'numbered_sections'
            else:
                pattern_type = 'option_codes'
        else:
            pattern_type = 'unknown'
            logger.warning("Could not detect content pattern")
        
        return pattern_type, content_links
    
    def _scrape_content_page(self, url: str, code: str, title: str, pattern_type: str) -> Dict:
        """
        Scrape a single content page and extract hierarchical structure.
        """
        html = self._get_page(url, use_selenium=False)
        if not html:
            logger.warning(f"Failed to load {url}")
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract hierarchical content
        result = {
            'code': code,
            'title': title,
            'url': url,
            'key_questions': [],
            'study_areas': []
        }
        
        # Extract key questions if present
        key_q_section = soup.find(string=re.compile(r'key questions', re.I))
        if key_q_section:
            parent = key_q_section.find_parent(['p', 'div'])
            if parent:
                ul = parent.find_next('ul')
                if ul:
                    for li in ul.find_all('li', recursive=False):
                        result['key_questions'].append(li.get_text().strip())
        
        # Extract study areas (h3 level)
        study_areas = []
        h3_headings = soup.find_all('h3')
        
        for h3 in h3_headings:
            area_title = h3.get_text().strip()
            
            # Extract period if present
            period_match = re.search(r'(\d{4})[–-](\d{4})', area_title)
            period = period_match.group(0) if period_match else None
            
            # Find sections (h4) within this area
            sections = []
            current = h3.find_next_sibling()
            
            while current and current.name != 'h3':
                if current.name == 'h4':
                    section_title = current.get_text().strip()
                    
                    # Extract period from section
                    sec_period_match = re.search(r'(\d{4})[–-](\d{4})', section_title)
                    sec_period = sec_period_match.group(0) if sec_period_match else None
                    
                    # Find content points (ul after this h4)
                    content_points = []
                    ul = current.find_next_sibling('ul')
                    if ul:
                        for li in ul.find_all('li', recursive=False):
                            point = li.get_text().strip()
                            if point:
                                content_points.append(point)
                    
                    sections.append({
                        'section_title': section_title,
                        'period': sec_period,
                        'content_points': content_points
                    })
                
                current = current.find_next_sibling()
            
            if sections or area_title:  # Add even if no sections (might just be intro text)
                study_areas.append({
                    'area_title': area_title,
                    'period': period,
                    'sections': sections
                })
        
        result['study_areas'] = study_areas
        
        return result
    
    def scrape_topics(self, subject=None, exam_type=None):
        """Legacy method - not used in web scraper."""
        return []
    
    def scrape_papers(self, subject=None, exam_type=None, year_from=2021):
        """Legacy method - not used in web scraper."""
        return []


if __name__ == '__main__':
    # Quick test
    scraper = AQAWebScraper()
    
    result = scraper.scrape_subject_content_complete(
        subject="History",
        qualification="A-Level",
        subject_code="7042"
    )
    
    import json
    print(json.dumps(result, indent=2)[:2000])
