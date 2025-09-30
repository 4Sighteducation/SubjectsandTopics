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
        
        # Step 1: Get specification overview (this has EVERYTHING for OCR!)
        spec_overview = self._scrape_specification_overview(subject_url)
        
        # For OCR, the spec_overview contains all topics already!
        # No need for separate content_structure
        
        return {
            'subject': subject_name,
            'qualification': qualification,
            'code': subject_code,
            'exam_board': 'OCR',
            
            # Assessment structure
            'components': spec_overview.get('components', []),
            'selection_rules': spec_overview.get('selection_rules', []),
            'content_overview': spec_overview.get('content_overview'),
            
            # Topic content
            'unit_groups': spec_overview.get('unit_groups', []),
            'all_topics': spec_overview.get('all_topics', []),
            
            # For compatibility with pipeline
            'content_structure': spec_overview.get('all_topics', [])
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
        For OCR, ALL the content is on this single page!
        """
        spec_glance_url = f"{subject_url}specification-at-a-glance/"
        
        logger.info(f"Scraping specification at a glance: {spec_glance_url}")
        
        html = self._get_page(spec_glance_url, use_selenium=False)
        if not html:
            logger.warning("Could not load specification overview")
            return {}
        
        soup = BeautifulSoup(html, 'lxml')
        
        result = {
            'components': [],  # From assessment overview table
            'selection_rules': [],
            'content_overview': None,  # General description
            'unit_groups': [],
            'all_topics': []
        }
        
        # Extract content overview (general description)
        content_overview_heading = soup.find(string=re.compile(r'Content overview', re.I))
        if content_overview_heading:
            parent = content_overview_heading.find_parent(['h2', 'h3', 'h4'])
            if parent:
                # Get all paragraphs after this heading until next heading
                description = []
                next_elem = parent.find_next_sibling()
                while next_elem and next_elem.name not in ['h2', 'h3', 'h4', 'table']:
                    if next_elem.name == 'p':
                        description.append(next_elem.get_text().strip())
                    next_elem = next_elem.find_next_sibling()
                result['content_overview'] = ' '.join(description)
        
        # Extract assessment overview table (this has the components!)
        assessment_heading = soup.find(string=re.compile(r'Assessment overview', re.I))
        if assessment_heading:
            parent = assessment_heading.find_parent(['h2', 'h3', 'h4'])
            if parent:
                # Find next table
                table = parent.find_next('table')
                if table:
                    components = self._parse_assessment_table(table)
                    result['components'] = components
                    logger.info(f"  Found {len(components)} components in assessment table")
                    
                    # Extract selection rules from table
                    for comp in components:
                        if comp.get('insert text'):  # The selection rule column
                            rule = comp['insert text']
                            if 'must' in rule.lower() or 'one' in rule.lower():
                                result['selection_rules'].append(rule)
        
        # Extract content - UNIVERSAL approach
        # Look for ANY of: Unit group, Component, Module
        # Each can have nested topics/bullet points
        
        # Patterns to detect
        unit_group_pattern = re.compile(r'Unit group (\d+)', re.I)
        component_pattern = re.compile(r'Component (\d+)', re.I)
        module_pattern = re.compile(r'Module (\d+)', re.I)
        
        for heading in soup.find_all(['h2', 'h3', 'h4']):
            text = heading.get_text().strip()
            
            # Try to match any pattern
            match = None
            content_type = None
            
            if unit_group_pattern.search(text):
                match = unit_group_pattern.search(text)
                content_type = 'unit_group'
            elif component_pattern.search(text):
                match = component_pattern.search(text)
                content_type = 'component'
            elif module_pattern.search(text):
                match = module_pattern.search(text)
                content_type = 'module'
            
            if not match:
                continue
            
            # Universal extraction regardless of type
            match = match
            
            if match:
                group_num = match.group(1)
                
                logger.info(f"  Found Unit group {group_num}")
                
                unit_info = {
                    'group_number': group_num,
                    'group_title': text,
                    'topics': [],
                    'selection_rule': None
                }
                
                # Get description paragraph and topic list
                next_elem = heading.find_next_sibling()
                
                while next_elem and next_elem.name not in ['h2', 'h3', 'h4']:
                    # Check for selection rule in paragraphs
                    if next_elem.name == 'p':
                        p_text = next_elem.get_text().strip()
                        if any(word in p_text.lower() for word in ['select', 'choose', 'must study', 'one of']):
                            unit_info['selection_rule'] = p_text
                    
                    # Extract topics from ul
                    elif next_elem.name == 'ul':
                        for li in next_elem.find_all('li', recursive=False):
                            topic_text = li.get_text().strip()
                            
                            if topic_text and len(topic_text) > 10:
                                # Parse topic to extract title and period
                                topic_data = self._parse_topic_text(topic_text, group_num)
                                unit_info['topics'].append(topic_data)
                                result['all_topics'].append(topic_data)
                    
                    next_elem = next_elem.find_next_sibling()
                
                logger.info(f"    Extracted {len(unit_info['topics'])} topics")
                
                if unit_info['topics']:  # Only add if we found topics
                    result['unit_groups'].append(unit_info)
                continue
            
            # Try Component pattern (Psychology, Biology, etc.)
            comp_match = component_pattern.search(text)
            if comp_match:
                comp_num = comp_match.group(1)
                
                logger.info(f"  Found Component {comp_num}")
                
                comp_info = {
                    'component_number': comp_num,
                    'component_title': text,
                    'topics': []
                }
                
                # Extract nested content under this component
                # Look for bullet points and nested headings
                next_elem = heading.find_next_sibling()
                
                while next_elem and next_elem.name not in ['h2', 'h3']:
                    # Extract from lists
                    if next_elem.name == 'ul':
                        for li in next_elem.find_all('li', recursive=False):
                            topic_text = li.get_text().strip()
                            if topic_text and len(topic_text) > 10:
                                topic_data = {
                                    'topic_name': topic_text,
                                    'component': comp_num,
                                    'is_required': True,  # Components are usually all required
                                    'raw_text': topic_text
                                }
                                comp_info['topics'].append(topic_data)
                                result['all_topics'].append(topic_data)
                    
                    # Or from nested h4/h5 headings
                    elif next_elem.name in ['h4', 'h5']:
                        section_text = next_elem.get_text().strip()
                        # Check if this is a topic or just a label
                        if not any(skip in section_text.lower() for skip in ['compulsory', 'one from', 'overview']):
                            topic_data = {
                                'topic_name': section_text,
                                'component': comp_num,
                                'is_required': True,
                                'raw_text': section_text
                            }
                            comp_info['topics'].append(topic_data)
                            result['all_topics'].append(topic_data)
                    
                    next_elem = next_elem.find_next_sibling()
                
                logger.info(f"    Extracted {len(comp_info['topics'])} topics from component")
                
                if comp_info['topics']:
                    result['unit_groups'].append(comp_info)  # Store in unit_groups for consistency
        
        logger.info(f"Total topics extracted: {len(result['all_topics'])}")
        
        return result
    
    def _parse_topic_text(self, text: str, unit_group: str) -> Dict:
        """
        Parse a topic text to extract title, period, and metadata.
        
        Example: "Spain 1469—1556" or "The early Tudors 1485-1558"
        """
        # Try to extract period (years)
        period_match = re.search(r'(\d{3,4})\s*[–—-]\s*(\d{3,4})', text)
        period = None
        period_start = None
        period_end = None
        
        if period_match:
            period_start = int(period_match.group(1))
            period_end = int(period_match.group(2))
            period = f"{period_start}-{period_end}"
        
        # Determine if being withdrawn
        is_withdrawn = 'being withdrawn' in text.lower()
        
        # Clean title (remove withdrawal note and dates for clean title)
        title = text
        if '(being withdrawn' in title:
            title = title.split('(being withdrawn')[0].strip()
        
        return {
            'topic_name': title,
            'unit_group': unit_group,
            'period': period,
            'period_start': period_start,
            'period_end': period_end,
            'is_withdrawn': is_withdrawn,
            'raw_text': text
        }
    
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
