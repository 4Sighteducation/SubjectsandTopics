"""
Webpage Content Extractor - Scrape detailed content from AQA subject pages.
Each option has its own webpage with structured content.
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from urllib.parse import urljoin
from utils.logger import get_logger

logger = get_logger()


class WebpageContentExtractor:
    """
    Extracts detailed hierarchical content from AQA webpage structure.
    More reliable than PDF extraction for detailed content!
    """
    
    def __init__(self, base_url: str = "https://www.aqa.org.uk"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def construct_option_url(self, subject: str, qualification: str, subject_code: str,
                            option_code: str, option_title: str) -> str:
        """
        Construct URL for an option's detail page.
        
        Pattern for AQA History:
        /subjects/history/a-level/history-7042/specification/subject-content/1b-spain-in-the-age-of-discovery-1469-1598-a-level-only
        
        Pattern components:
        - subject slug: history
        - qualification: a-level
        - subject-code: history-7042
        - option code: 1b
        - option title: spain-in-the-age-of-discovery-1469-1598
        - suffix: a-level-only (if A-level only option)
        """
        # Create slugs
        subject_slug = subject.lower().replace(' ', '-')
        qual_slug = qualification.lower().replace(' ', '-')
        
        # Create option slug from title
        # "Spain in the Age of Discovery, 1469–1598" → "spain-in-the-age-of-discovery-1469-1598"
        option_slug = option_title.lower()
        # Remove the option code prefix if present
        option_slug = re.sub(rf'^{option_code}:?\s*', '', option_slug, flags=re.IGNORECASE)
        # Remove special chars
        option_slug = re.sub(r'[–—,:]', '-', option_slug)
        option_slug = re.sub(r'[^\w\s-]', '', option_slug)
        option_slug = re.sub(r'[-\s]+', '-', option_slug).strip('-')
        
        # Check if it's A-level only
        is_alevel_only = '(a-level only)' in option_title.lower()
        suffix = '-a-level-only' if is_alevel_only else ''
        
        # Construct full URL
        url = f"{self.base_url}/subjects/{subject_slug}/{qual_slug}/{subject_slug}-{subject_code}/specification/subject-content/{option_code.lower()}-{option_slug}{suffix}"
        
        return url
    
    def extract_from_webpage(self, url: str, option_code: str) -> Dict:
        """
        Extract detailed content from an option's webpage.
        
        Returns hierarchical structure with all levels.
        """
        logger.info(f"Scraping content from: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract content
            result = {
                'option_code': option_code,
                'option_title': self._extract_title(soup),
                'key_questions': self._extract_key_questions(soup),
                'study_areas': self._extract_study_areas(soup)
            }
            
            logger.info(f"Extracted from webpage:")
            logger.info(f"  - Key questions: {len(result['key_questions'])}")
            logger.info(f"  - Study areas: {len(result['study_areas'])}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch webpage: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error extracting from webpage: {e}")
            return {}
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the option title from the page."""
        # Look for h2 or h1 with the option title
        title_elem = soup.find(['h1', 'h2'])
        if title_elem:
            return title_elem.get_text().strip()
        return ""
    
    def _extract_key_questions(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract key questions from the page.
        Usually in a list after "key questions" or "This option allows students to study..."
        """
        questions = []
        
        # Find the paragraph or section containing key questions
        key_q_section = soup.find(string=re.compile(r'key questions', re.I))
        
        if key_q_section:
            # Find the parent element
            parent = key_q_section.find_parent(['p', 'div'])
            if parent:
                # Find the next ul element
                ul = parent.find_next('ul')
                if ul:
                    for li in ul.find_all('li', recursive=False):
                        question = li.get_text().strip()
                        if question:
                            questions.append(question)
        
        return questions
    
    def _extract_study_areas(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract study areas (Parts) and their sections.
        
        Structure:
        h3: Part one: the establishment of a 'New Monarchy', 1469–1556
          h4: The forging of a new state, 1469–1516
            ul: bullet points
          h4: The drive to 'Great Power' status, 1516–1556
            ul: bullet points
        """
        study_areas = []
        
        # Find all h3 headings (these are usually the Part one/Part two level)
        part_headings = soup.find_all('h3')
        
        for part_h3 in part_headings:
            part_title = part_h3.get_text().strip()
            
            # Extract period from title if present
            period_match = re.search(r'(\d{4})[–-](\d{4})', part_title)
            period = period_match.group(0) if period_match else None
            
            # Find sections within this part (h4 headings until next h3)
            sections = []
            
            # Get all siblings until next h3
            current = part_h3.find_next_sibling()
            while current and current.name != 'h3':
                if current.name == 'h4':
                    # This is a section
                    section_title = current.get_text().strip()
                    
                    # Extract period from section title
                    section_period_match = re.search(r'(\d{4})[–-](\d{4})', section_title)
                    section_period = section_period_match.group(0) if section_period_match else None
                    
                    # Find content points (next ul)
                    content_points = []
                    ul = current.find_next_sibling('ul')
                    if ul and ul.find_previous_sibling('h4') == current:
                        # This ul belongs to this h4
                        for li in ul.find_all('li', recursive=False):
                            point = li.get_text().strip()
                            if point:
                                content_points.append(point)
                    
                    sections.append({
                        'section_title': section_title,
                        'period': section_period,
                        'content_points': content_points
                    })
                
                current = current.find_next_sibling()
            
            if sections:  # Only add if we found sections
                study_areas.append({
                    'area_title': part_title,
                    'period': period,
                    'sections': sections
                })
        
        return study_areas
    
    def extract_all_options_for_subject(self, subject: str, qualification: str,
                                       subject_code: str, options: List[Dict]) -> Dict:
        """
        Extract detailed content for ALL options in a subject.
        
        Args:
            subject: e.g., "History"
            qualification: e.g., "A-Level"
            subject_code: e.g., "7042"
            options: List of option dicts with 'code' and 'title'
            
        Returns:
            Dict mapping option_code → detailed content
        """
        results = {}
        
        total = len(options)
        logger.info(f"Extracting detailed content for {total} options...")
        
        for i, option in enumerate(options, 1):
            option_code = option.get('code')
            option_title = option.get('title')
            
            logger.info(f"[{i}/{total}] Processing {option_code}: {option_title}")
            
            # Construct URL
            url = self.construct_option_url(
                subject, qualification, subject_code, option_code, option_title
            )
            
            # Extract content
            content = self.extract_from_webpage(url, option_code)
            
            if content:
                results[option_code] = content
            else:
                logger.warning(f"Failed to extract {option_code}, will retry with fallback")
        
        logger.info(f"Successfully extracted {len(results)}/{total} options")
        
        return results
