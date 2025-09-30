"""
OCR exam board scraper implementation.

This module provides the OCRScraper class that scrapes topic lists and exam materials
from the OCR (Oxford, Cambridge and RSA) exam board website.
"""

import os
import re
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin, urlparse, parse_qs

from scrapers.base_scraper import BaseScraper
from utils.logger import get_logger
from utils.helpers import (
    sanitize_text, normalize_subject_name, normalize_exam_type, 
    extract_tables_from_html, ensure_directory
)
from utils.subjects import GCSE_SUBJECTS, A_LEVEL_SUBJECTS, normalize_subject

# Import AI-assisted topic extraction functions
try:
    from ai_helpers.topic_extractor import (
        extract_topics_from_html, 
        extract_topics_from_pdf,
        extract_topics_from_content
    )
    AI_HELPERS_AVAILABLE = True
except ImportError:
    AI_HELPERS_AVAILABLE = False
    logger = get_logger()
    logger.warning("AI helpers not available. Some features will be limited.")

logger = get_logger()


class OCRScraper(BaseScraper):
    """
    Scraper for the OCR exam board website.
    """
    
    def __init__(self, headless=True, delay=1.5):
        """
        Initialize the OCR scraper.
        
        Args:
            headless (bool): Whether to run the browser in headless mode
            delay (float): Delay between requests in seconds
        """
        super().__init__(
            name="OCR",
            base_url="https://www.ocr.org.uk",
            headless=headless,
            delay=delay
        )
        
        # OCR-specific URLs
        self.qualifications_url = urljoin(self.base_url, "/qualifications")
        self.past_papers_url = urljoin(self.base_url, "/qualifications/past-paper-finder/")
        
        # Map of normalized subject names to OCR subject codes
        self.subject_code_map = {}
        
        logger.info("OCR scraper initialized")
    
    def _get_subject_urls(self, exam_type=None):
        """
        Get URLs for all subjects based on exam type.
        
        Args:
            exam_type (str, optional): Type of exam to filter by
            
        Returns:
            dict: Dictionary mapping subject names to their URLs
        """
        logger.info(f"Getting subject URLs for OCR" + (f" ({exam_type})" if exam_type else ""))
        
        # Normalize exam_type for consistent matching
        norm_exam_type = normalize_exam_type(exam_type) if exam_type else None
        
        # Define URL patterns for OCR subjects
        def get_url_for_subject(subject, is_gcse=True):
            """Generate a URL for a subject based on common patterns"""
            # Handle special cases
            subject_lower = subject.lower()
            
            if is_gcse:
                # Known GCSE URL map
                gcse_url_map = {
                    "mathematics": "https://www.ocr.org.uk/qualifications/gcse/mathematics-j560-from-2015/",
                    "english language": "https://www.ocr.org.uk/qualifications/gcse/english-language-j351-from-2015/",
                    "english literature": "https://www.ocr.org.uk/qualifications/gcse/english-literature-j352-from-2015/",
                    "biology": "https://www.ocr.org.uk/qualifications/gcse/gateway-science-suite-biology-a-j247-from-2016/",
                    "chemistry": "https://www.ocr.org.uk/qualifications/gcse/gateway-science-suite-chemistry-a-j248-from-2016/",
                    "physics": "https://www.ocr.org.uk/qualifications/gcse/gateway-science-suite-physics-a-j249-from-2016/",
                    "combined science: trilogy": "https://www.ocr.org.uk/qualifications/gcse/gateway-science-suite-combined-science-a-j250-from-2016/",
                    "computer science": "https://www.ocr.org.uk/qualifications/gcse/computer-science-j277-from-2020/",
                }
                
                if subject_lower in gcse_url_map:
                    return gcse_url_map[subject_lower]
                
                # For other subjects, create a standardized URL
                url_subject = subject_lower.replace(" and ", "-").replace(" ", "-").replace(":", "")
                return f"https://www.ocr.org.uk/qualifications/gcse/{url_subject}-j000-from-2015/"
            else:
                # Known A-Level URL map
                a_level_url_map = {
                    "mathematics": "https://www.ocr.org.uk/qualifications/as-and-a-level/mathematics-a-h230-h240-from-2017/",
                    "further mathematics": "https://www.ocr.org.uk/qualifications/as-and-a-level/further-mathematics-a-h235-h245-from-2017/",
                    "english language": "https://www.ocr.org.uk/qualifications/as-and-a-level/english-language-h070-h470-from-2015/",
                    "english literature": "https://www.ocr.org.uk/qualifications/as-and-a-level/english-literature-h072-h472-from-2015/",
                    "english language and literature": "https://www.ocr.org.uk/qualifications/as-and-a-level/english-language-and-literature-emc-h074-h474-from-2015/",
                    "biology": "https://www.ocr.org.uk/qualifications/as-and-a-level/biology-a-h020-h420-from-2015/",
                    "chemistry": "https://www.ocr.org.uk/qualifications/as-and-a-level/chemistry-a-h032-h432-from-2015/",
                    "physics": "https://www.ocr.org.uk/qualifications/as-and-a-level/physics-a-h156-h556-from-2015/",
                    "computer science": "https://www.ocr.org.uk/qualifications/as-and-a-level/computer-science-h046-h446-from-2015/",
                }
                
                if subject_lower in a_level_url_map:
                    return a_level_url_map[subject_lower]
                
                # For other subjects, create a standardized URL
                url_subject = subject_lower.replace(" and ", "-").replace(" ", "-").replace(":", "")
                return f"https://www.ocr.org.uk/qualifications/as-and-a-level/{url_subject}-h000-h000-from-2015/"
        
        # Hard-coded subject URLs for OCR subjects based on official website
        subject_urls = {}
        
        # GCSE Subjects
        if not norm_exam_type or norm_exam_type.lower() == 'gcse':
            # Direct URLs from OCR website
            gcse_subject_urls = {
                "Ancient History": "https://www.ocr.org.uk/qualifications/gcse/ancient-history-j198-from-2017/",
                "Art and Design": "https://www.ocr.org.uk/qualifications/gcse/art-and-design-j170-j176-from-2016/",
                "Biology A (Gateway Science)": "https://www.ocr.org.uk/qualifications/gcse/gateway-science-suite-biology-a-j247-from-2016/",
                "Biology B (Twenty First Century)": "https://www.ocr.org.uk/qualifications/gcse/twenty-first-century-science-suite-biology-b-j257-from-2016/",
                "Business": "https://www.ocr.org.uk/qualifications/gcse/business-j204-from-2017/",
                "Chemistry A (Gateway Science)": "https://www.ocr.org.uk/qualifications/gcse/gateway-science-suite-chemistry-a-j248-from-2016/",
                "Chemistry B (Twenty First Century)": "https://www.ocr.org.uk/qualifications/gcse/twenty-first-century-science-suite-chemistry-b-j258-from-2016/",
                "Citizenship Studies": "https://www.ocr.org.uk/qualifications/gcse/citizenship-studies-j270-from-2016/",
                "Classical Civilisation": "https://www.ocr.org.uk/qualifications/gcse/classical-civilisation-j199-from-2017/",
                "Classical Greek": "https://www.ocr.org.uk/qualifications/gcse/classical-greek-j292-from-2016/",
                "Computer Science": "https://www.ocr.org.uk/qualifications/gcse/computer-science-j277-from-2020/",
                "Design and Technology": "https://www.ocr.org.uk/qualifications/gcse/design-and-technology-j310-from-2017/",
                "Drama": "https://www.ocr.org.uk/qualifications/gcse/drama-j316-from-2016/",
                "Economics": "https://www.ocr.org.uk/qualifications/gcse/economics-j205-from-2017/",
                "English Language": "https://www.ocr.org.uk/qualifications/gcse/english-language-j351-from-2015/",
                "English Literature": "https://www.ocr.org.uk/qualifications/gcse/english-literature-j352-from-2015/",
                "Food Preparation and Nutrition": "https://www.ocr.org.uk/qualifications/gcse/food-preparation-and-nutrition-j309-from-2016/",
                "Geography A (Geographical Themes)": "https://www.ocr.org.uk/qualifications/gcse/geography-a-geographical-themes-j383-from-2016/",
                "Geography B (Geography for Enquiring Minds)": "https://www.ocr.org.uk/qualifications/gcse/geography-b-geography-for-enquiring-minds-j384-from-2016/",
                "History A (Explaining the Modern World)": "https://www.ocr.org.uk/qualifications/gcse/history-a-explaining-the-modern-world-j410-from-2016/",
                "History B (Schools History Project)": "https://www.ocr.org.uk/qualifications/gcse/history-b-schools-history-project-j411-from-2016/",
                "Latin": "https://www.ocr.org.uk/qualifications/gcse/latin-j282-from-2016/",
                "Mathematics": "https://www.ocr.org.uk/qualifications/gcse/mathematics-j560-from-2015/",
                "Media Studies": "https://www.ocr.org.uk/qualifications/gcse/media-studies-j200-from-2023/",
                "Music": "https://www.ocr.org.uk/qualifications/gcse/music-j536-from-2016/",
                "Physical Education": "https://www.ocr.org.uk/qualifications/gcse/physical-education-j587-from-2016/",
                "Physics A (Gateway Science)": "https://www.ocr.org.uk/qualifications/gcse/gateway-science-suite-physics-a-j249-from-2016/",
                "Physics B (Twenty First Century)": "https://www.ocr.org.uk/qualifications/gcse/twenty-first-century-science-suite-physics-b-j259-from-2016/",
                "Psychology": "https://www.ocr.org.uk/qualifications/gcse/psychology-j203-from-2017/",
                "Religious Studies": "https://www.ocr.org.uk/qualifications/gcse/religious-studies-j625-j125-from-2016/",
                "Combined Science A (Gateway Science)": "https://www.ocr.org.uk/qualifications/gcse/gateway-science-suite-combined-science-a-j250-from-2016/",
                "Combined Science B (Twenty First Century)": "https://www.ocr.org.uk/qualifications/gcse/twenty-first-century-science-suite-combined-science-b-j260-from-2016/"
            }
            
            # Add GCSE subjects to the main dictionary
            for subject_name, url in gcse_subject_urls.items():
                subject_urls[subject_name] = url
        
        # A-Level Subjects
        if not norm_exam_type or norm_exam_type.lower() in ['a-level', 'as-level']:
            # Direct URLs from OCR website
            a_level_subject_urls = {
                "Ancient History": "https://www.ocr.org.uk/qualifications/as-and-a-level/ancient-history-h007-h407-from-2017/",
                "Art and Design": "https://www.ocr.org.uk/qualifications/as-and-a-level/art-and-design-h200-h600-from-2015/",
                "Biology A": "https://www.ocr.org.uk/qualifications/as-and-a-level/biology-a-h020-h420-from-2015/",
                "Biology B (Advancing Biology)": "https://www.ocr.org.uk/qualifications/as-and-a-level/biology-b-advancing-biology-h022-h422-from-2015/",
                "Business": "https://www.ocr.org.uk/qualifications/as-and-a-level/business-h031-h431-from-2015/",
                "Chemistry A": "https://www.ocr.org.uk/qualifications/as-and-a-level/chemistry-a-h032-h432-from-2015/",
                "Chemistry B (Salters)": "https://www.ocr.org.uk/qualifications/as-and-a-level/chemistry-b-salters-h033-h433-from-2015/",
                "Classical Civilisation": "https://www.ocr.org.uk/qualifications/as-and-a-level/classical-civilisation-h008-h408-from-2017/",
                "Classical Greek": "https://www.ocr.org.uk/qualifications/as-and-a-level/classical-greek-h044-h444-from-2016/",
                "Computer Science": "https://www.ocr.org.uk/qualifications/as-and-a-level/computer-science-h046-h446-from-2015/",
                "Design and Technology": "https://www.ocr.org.uk/qualifications/as-and-a-level/design-and-technology-h004-h006-h404-h406-from-2017/",
                "Drama and Theatre": "https://www.ocr.org.uk/qualifications/as-and-a-level/drama-and-theatre-h059-h459-from-2016/",
                "Economics": "https://www.ocr.org.uk/qualifications/as-and-a-level/economics-h060-h460-from-2019/",
                "English Language": "https://www.ocr.org.uk/qualifications/as-and-a-level/english-language-h070-h470-from-2015/",
                "English Language and Literature": "https://www.ocr.org.uk/qualifications/as-and-a-level/english-language-and-literature-emc-h074-h474-from-2015/",
                "English Literature": "https://www.ocr.org.uk/qualifications/as-and-a-level/english-literature-h072-h472-from-2015/",
                "Film Studies": "https://www.ocr.org.uk/qualifications/as-and-a-level/film-studies-h010-h410-from-2017/",
                "Geography": "https://www.ocr.org.uk/qualifications/as-and-a-level/geography-h081-h481-from-2016/",
                "Geology": "https://www.ocr.org.uk/qualifications/as-and-a-level/geology-h014-h414-from-2017/",
                "History A": "https://www.ocr.org.uk/qualifications/as-and-a-level/history-a-h105-h505-from-2015/",
                "Latin": "https://www.ocr.org.uk/qualifications/as-and-a-level/latin-h043-h443-from-2016/",
                "Law": "https://www.ocr.org.uk/qualifications/as-and-a-level/law-h018-h418-from-2020/",
                "Mathematics A": "https://www.ocr.org.uk/qualifications/as-and-a-level/mathematics-a-h230-h240-from-2017/",
                "Further Mathematics A": "https://www.ocr.org.uk/qualifications/as-and-a-level/further-mathematics-a-h235-h245-from-2017/",
                "Mathematics B (MEI)": "https://www.ocr.org.uk/qualifications/as-and-a-level/mathematics-b-mei-h630-h640-from-2017/",
                "Further Mathematics B (MEI)": "https://www.ocr.org.uk/qualifications/as-and-a-level/further-mathematics-b-mei-h635-h645-from-2017/",
                "Media Studies": "https://www.ocr.org.uk/qualifications/as-and-a-level/media-studies-h009-h409-from-2023/",
                "Music": "https://www.ocr.org.uk/qualifications/as-and-a-level/music-h143-h543-from-2016/",
                "Physical Education": "https://www.ocr.org.uk/qualifications/as-and-a-level/physical-education-h155-h555-from-2016/",
                "Physics A": "https://www.ocr.org.uk/qualifications/as-and-a-level/physics-a-h156-h556-from-2015/",
                "Physics B (Advancing Physics)": "https://www.ocr.org.uk/qualifications/as-and-a-level/physics-b-advancing-physics-h157-h557-from-2015/",
                "Psychology": "https://www.ocr.org.uk/qualifications/as-and-a-level/psychology-h169-h569-from-2026/",
                "Religious Studies": "https://www.ocr.org.uk/qualifications/as-and-a-level/religious-studies-h173-h573-from-2016/",
                "Sociology": "https://www.ocr.org.uk/qualifications/as-and-a-level/sociology-h180-h580-from-2015/"
            }
            
            # Add A-Level subjects to the main dictionary with A-Level suffix
            for subject_name, url in a_level_subject_urls.items():
                subject_with_level = f"{subject_name} (A-Level)"
                subject_urls[subject_with_level] = url
        
        logger.info(f"Found {len(subject_urls)} subject URLs")
        return subject_urls
    
    def _get_spec_url_from_subject_page(self, subject_url):
        """
        Get specification URL from a subject page.
        
        Args:
            subject_url (str): URL of the subject page
            
        Returns:
            str or None: URL of the specification
        """
        html = self._get_page(subject_url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Look for "Specification" links
        spec_links = soup.find_all('a', href=True, string=re.compile('specification', re.IGNORECASE))
        if spec_links:
            spec_link = spec_links[0]
            return urljoin(self.base_url, spec_link['href'])
        
        # If not found directly, try looking for PDF links
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$'))
        for link in pdf_links:
            if 'specification' in link.text.lower() or 'specification' in link['href'].lower():
                return urljoin(self.base_url, link['href'])
        
        # OCR sometimes has a "Planning and teaching" section that includes the specification
        planning_links = soup.find_all('a', href=True, string=re.compile('planning', re.IGNORECASE))
        if planning_links:
            for link in planning_links:
                planning_url = urljoin(self.base_url, link['href'])
                planning_html = self._get_page(planning_url)
                if planning_html:
                    planning_soup = BeautifulSoup(planning_html, 'lxml')
                    for a_tag in planning_soup.find_all('a', href=True):
                        if 'specification' in a_tag.text.lower() and a_tag['href'].lower().endswith('.pdf'):
                            return urljoin(self.base_url, a_tag['href'])
        
        return None
    
    def _get_subject_code(self, subject_url):
        """
        Extract subject code from the subject URL or page.
        
        Args:
            subject_url (str): URL of the subject page
            
        Returns:
            str or None: Subject code
        """
        # OCR subject codes are typically in the URL in the format j123 or h123
        match = re.search(r'/([a-z]\d{3})-', subject_url.lower())
        if match:
            return match.group(1).upper()
        
        # If not found in URL, try to extract from page content
        html = self._get_page(subject_url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Look for specification code in text
        code_pattern = re.compile(r'\b([HJA]\d{3}[A-Z]?)\b')
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5']):
            match = code_pattern.search(element.text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_specification_topics(self, specification_url, exam_type, subject):
        """
        Extract topics from a specification URL.
        
        Args:
            specification_url (str): URL of the specification
            exam_type (str): Type of exam
            subject (str): Subject name
            
        Returns:
            list: List of topic data dictionaries
        """
        logger.info(f"Extracting topics from specification: {specification_url}")
        
        # Determine if the specification is PDF or HTML
        is_pdf = specification_url.lower().endswith('.pdf')
        
        if is_pdf:
            # For PDFs, download the file and use PDF extraction
            pdf_filename = f"{normalize_subject_name(subject)}_{normalize_exam_type(exam_type)}_spec.pdf"
            pdf_subdir = os.path.join("specifications", self.name.lower())
            pdf_path = self._download_document(
                specification_url, 
                pdf_filename, 
                pdf_subdir, 
                "specification"
            )
            
            if not pdf_path:
                logger.error(f"Failed to download PDF specification: {specification_url}")
                return []
            
            # Try AI-assisted extraction first if available
            if AI_HELPERS_AVAILABLE:
                logger.info(f"Attempting AI-assisted topic extraction for {subject} PDF")
                ai_topics = extract_topics_from_pdf(
                    pdf_path, subject, exam_type, self.name
                )
                
                if ai_topics:
                    logger.info(f"AI successfully extracted {len(ai_topics)} topics from PDF")
                    return ai_topics
                else:
                    logger.warning("AI extraction from PDF failed, falling back to conventional methods")
            
            # Otherwise, return an empty list for now (PDF extraction without AI is difficult)
            logger.warning(f"No AI helpers available for PDF extraction: {pdf_path}")
            return []
        
        # For HTML specifications
        html = self._get_page(specification_url, use_selenium=True)
        if not html:
            logger.error(f"Failed to get specification page: {specification_url}")
            return []
        
        # Try AI-assisted extraction first if available
        if AI_HELPERS_AVAILABLE:
            logger.info(f"Attempting AI-assisted topic extraction for {subject}")
            ai_topics = extract_topics_from_html(
                html, subject, exam_type, self.name
            )
            
            if ai_topics:
                logger.info(f"AI successfully extracted {len(ai_topics)} topics from HTML")
                return ai_topics
            else:
                logger.warning("AI extraction from HTML failed, falling back to conventional methods")
        
        # Fallback to conventional extraction methods
        soup = BeautifulSoup(html, 'lxml')
        topics_data = []
        
        # Special case handling for common subjects
        if subject.lower() == "mathematics" and exam_type.lower() == "gcse":
            # GCSE Mathematics main topics and subtopics based on OCR specification
            topic_structure = {
                "Number": [
                    "Calculations",
                    "Fractions, decimals and percentages",
                    "Indices and standard form",
                    "Surds"
                ],
                "Algebra": [
                    "Manipulation",
                    "Equations and inequalities",
                    "Sequences",
                    "Graphs",
                    "Solving quadratic equations"
                ],
                "Ratio, proportion and rates of change": [
                    "Percentages",
                    "Growth and decay",
                    "Direct and inverse proportion",
                    "Compound units"
                ],
                "Geometry and measures": [
                    "Properties and constructions",
                    "Mensuration",
                    "Vectors",
                    "Trigonometry",
                    "Coordinate geometry"
                ],
                "Probability": [
                    "Probability calculations",
                    "Probability experiments",
                    "Listing outcomes"
                ],
                "Statistics": [
                    "Sampling",
                    "Processing, representing and analyzing data",
                    "Interpreting data"
                ]
            }
            
            for module, topics in topic_structure.items():
                for topic in topics:
                    topics_data.append(self._build_topic_data(
                        exam_board="OCR",
                        exam_type=exam_type,
                        subject=subject,
                        module=module,
                        topic=topic
                    ))
            
            logger.info(f"Generated {len(topics_data)} topics for Mathematics GCSE using predefined structure")
            return topics_data
        
        # Look for headings that might indicate topic sections
        topic_headings = soup.find_all(['h2', 'h3', 'h4', 'h5'])
        current_module = "General"
        current_topic = None
        
        for heading in topic_headings:
            heading_text = sanitize_text(heading.text)
            
            # Skip headings that are not related to content
            if not heading_text or any(ignore in heading_text.lower() for ignore in 
                                      ['assessment', 'introduction', 'appendix']):
                continue
                
            # Based on heading level, decide if it's a module or topic
            if heading.name in ['h2', 'h3']:
                # Likely a module/main section
                current_module = heading_text
                current_topic = None
            else:
                # Likely a topic
                if current_module:
                    current_topic = heading_text
                    topics_data.append(self._build_topic_data(
                        exam_board="OCR",
                        exam_type=exam_type,
                        subject=subject,
                        module=current_module,
                        topic=current_topic
                    ))
        
        # Look for lists that might contain topics
        for ul in soup.find_all('ul'):
            # Skip navigation and utility lists
            if 'nav' in ul.get('class', []) or ul.parent.name == 'nav':
                continue
                
            module_candidate = None
            for parent in ul.parents:
                if parent.name in ['h2', 'h3', 'h4', 'h5']:
                    module_candidate = sanitize_text(parent.text)
                    break
            
            current_module = module_candidate or current_module
            
            for li in ul.find_all('li', recursive=False):
                item_text = sanitize_text(li.text)
                if len(item_text) > 3 and len(item_text) < 200:
                    # This is likely a topic or subtopic
                    if item_text.startswith(('•', '○', '·')) and current_topic:
                        # Probably a bullet point list, treat as subtopic
                        topics_data.append(self._build_topic_data(
                            exam_board="OCR",
                            exam_type=exam_type,
                            subject=subject,
                            module=current_module,
                            topic=current_topic,
                            sub_topic=item_text
                        ))
                    else:
                        # Treat as a topic
                        current_topic = item_text
                        topics_data.append(self._build_topic_data(
                            exam_board="OCR",
                            exam_type=exam_type,
                            subject=subject,
                            module=current_module,
                            topic=current_topic
                        ))
        
        # If we still haven't found topics, try strong tags and paragraphs
        if not topics_data:
            # Look for strong tags that might be topics
            for tag in soup.find_all(['strong', 'b']):
                topic_text = sanitize_text(tag.text)
                if len(topic_text) > 3 and len(topic_text) < 100:
                    topics_data.append(self._build_topic_data(
                        exam_board="OCR",
                        exam_type=exam_type,
                        subject=subject,
                        module=current_module,
                        topic=topic_text
                    ))
            
            # Look for paragraphs that might contain topic indicators
            for p in soup.find_all('p'):
                p_text = sanitize_text(p.text)
                if len(p_text) > 10 and len(p_text) < 150 and p_text[0].isupper():
                    if any(keyword in p_text.lower() for keyword in 
                          ['study', 'learn', 'understand', 'know', 'content']):
                        topics_data.append(self._build_topic_data(
                            exam_board="OCR",
                            exam_type=exam_type,
                            subject=subject,
                            module=current_module,
                            topic=p_text
                        ))
        
        logger.info(f"Extracted {len(topics_data)} topics from specification")
        return topics_data
    
    def scrape_topics(self, subject=None, exam_type=None):
        """
        Scrape topic lists from the OCR website.
        
        Args:
            subject (str, optional): Subject to scrape topics for
            exam_type (str, optional): Exam type to scrape topics for
            
        Returns:
            list: List of topic data dictionaries
        """
        logger.info(f"Scraping OCR topics" + 
                   (f" for {subject}" if subject else "") + 
                   (f" ({exam_type})" if exam_type else ""))
        
        # Get subject URLs
        subject_urls = self._get_subject_urls(exam_type)
        
        # If a specific subject is requested, filter the URLs
        if subject:
            norm_subject = normalize_subject_name(subject)
            filtered_urls = {}
            for subj_name, subj_url in subject_urls.items():
                if norm_subject in normalize_subject_name(subj_name):
                    filtered_urls[subj_name] = subj_url
            subject_urls = filtered_urls
        
        # Get topics for each subject
        all_topics = []
        
        for subj_name, subj_url in subject_urls.items():
            try:
                # Get the specification URL
                spec_url = self._get_spec_url_from_subject_page(subj_url)
                if not spec_url:
                    logger.warning(f"Could not find specification URL for {subj_name}")
                    continue
                
                # Extract topics from specification
                topics = self._extract_specification_topics(
                    spec_url, 
                    exam_type or "GCSE" if "gcse" in subj_url else "A-Level",
                    subj_name
                )
                
                all_topics.extend(topics)
                
                # Save the raw topics data
                if topics:
                    subdir = normalize_exam_type(exam_type) if exam_type else "all"
                    self._save_raw_data(
                        topics,
                        f"{sanitize_text(subj_name)}_topics.json",
                        subdir
                    )
            
            except Exception as e:
                logger.error(f"Error scraping topics for {subj_name}: {e}", exc_info=True)
        
        logger.info(f"Scraped {len(all_topics)} topics from OCR")
        return all_topics
    
    def _parse_paper_details(self, filename, link_text):
        """
        Parse paper details from filename and link text.
        
        Args:
            filename (str): Name of the file
            link_text (str): Text of the link
            
        Returns:
            dict: Dictionary of paper details
        """
        details = {
            'paper_number': 1,
            'season': 'Summer',
            'year': datetime.now().year,
            'document_type': 'Question Paper',
            'subject_code': '',
            'title': link_text
        }
        
        # Extract year
        year_match = re.search(r'(20\d\d)', filename)
        if year_match:
            details['year'] = int(year_match.group(1))
        else:
            year_match = re.search(r'(20\d\d)', link_text)
            if year_match:
                details['year'] = int(year_match.group(1))
        
        # Extract paper number
        paper_match = re.search(r'paper-?(\d+)', filename.lower())
        if paper_match:
            details['paper_number'] = int(paper_match.group(1))
        else:
            paper_match = re.search(r'paper\s+(\d+)', link_text.lower())
            if paper_match:
                details['paper_number'] = int(paper_match.group(1))
        
        # Extract season
        if any(season in filename.lower() for season in ['jan', 'january', 'winter']):
            details['season'] = 'Winter'
        elif any(season in filename.lower() for season in ['june', 'summer']):
            details['season'] = 'Summer'
        elif any(season in link_text.lower() for season in ['jan', 'january', 'winter']):
            details['season'] = 'Winter'
        elif any(season in link_text.lower() for season in ['june', 'summer']):
            details['season'] = 'Summer'
        
        # Extract document type
        if any(doc_type in filename.lower() for doc_type in ['mark-scheme', 'ms', 'markscheme']):
            details['document_type'] = 'Mark Scheme'
        elif any(doc_type in filename.lower() for doc_type in ['examiner-report', 'er', 'examreport']):
            details['document_type'] = 'Examiner Report'
        elif any(doc_type in link_text.lower() for doc_type in ['mark scheme', 'markscheme', 'ms']):
            details['document_type'] = 'Mark Scheme'
        elif any(doc_type in link_text.lower() for doc_type in ['examiner report', 'examreport', 'er']):
            details['document_type'] = 'Examiner Report'
        
        # Extract subject code
        code_match = re.search(r'([A-Z]\d{3}[A-Z]?)', filename.upper())
        if code_match:
            details['subject_code'] = code_match.group(1)
        else:
            code_match = re.search(r'([A-Z]\d{3}[A-Z]?)', link_text.upper())
            if code_match:
                details['subject_code'] = code_match.group(1)
        
        return details
    
    def scrape_papers(self, subject=None, exam_type=None, year_from=2021):
        """
        Scrape exam papers from the OCR website.
        
        Args:
            subject (str, optional): Subject to scrape papers for
            exam_type (str, optional): Exam type to scrape papers for
            year_from (int): Year to start scraping papers from
            
        Returns:
            list: List of paper data dictionaries
        """
        logger.info(f"Scraping OCR papers" + 
                   (f" for {subject}" if subject else "") + 
                   (f" ({exam_type})" if exam_type else "") +
                   f" from {year_from}")
        
        # Get the subject code to use for filtering
        subject_code = None
        if subject:
            # Get normalized subject
            normalized_subject = normalize_subject_name(subject)
            # Try to get existing subject code mapping
            if normalized_subject in self.subject_code_map:
                subject_code = self.subject_code_map[normalized_subject]
        
        # Get normalized exam type
        normalized_exam_type = normalize_exam_type(exam_type) if exam_type else None
        
        # Use a direct URL to the past papers finder
        # This is more reliable than filling out forms with Selenium
        papers_url = "https://www.ocr.org.uk/qualifications/past-paper-finder/"
        
        # Navigate to the past papers finder page
        self._init_driver()
        papers = []
        
        try:
            # Go to the past papers page
            logger.info(f"Navigating to past papers finder: {papers_url}")
            self.driver.get(papers_url)
            time.sleep(2)  # Give time for the page to load
            
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form, input, select, button"))
            )
            
            # OCR's website can be tricky to navigate programmatically
            # Instead of trying to fill out the form, which is prone to errors,
            # let's use a simpler approach: search for PDFs directly on the page
            logger.info("Searching for PDF links for past papers")
            
            try:
                # Get the page source
                html = self.driver.page_source
                soup = BeautifulSoup(html, 'lxml')
                
                # Search for any links to PDFs on the page
                pdf_links = soup.find_all('a', href=lambda href: href and href.lower().endswith('.pdf'))
                
                if not pdf_links:
                    logger.warning(f"No PDF links found on initial page, trying to navigate to resources")
                    
                    # Try to find and click on links that might lead to resources or past papers
                    resource_links = []
                    for link in self.driver.find_elements(By.TAG_NAME, 'a'):
                        link_text = link.text.lower()
                        if any(term in link_text for term in ['resource', 'past paper', 'assessment', 'exam']):
                            resource_links.append(link)
                    
                    # Click on the first promising link
                    if resource_links:
                        resource_links[0].click()
                        time.sleep(2)
                        
                        # Get updated page and check for PDFs again
                        html = self.driver.page_source
                        soup = BeautifulSoup(html, 'lxml')
                        pdf_links = soup.find_all('a', href=lambda href: href and href.lower().endswith('.pdf'))
                
                # If we still don't have PDF links, try a different approach
                if not pdf_links:
                    logger.warning(f"Still no PDF links found, trying direct search for past papers")
                    
                    # Navigate to a URL that's known to contain past papers
                    direct_url = f"https://www.ocr.org.uk/search/?type=Past+paper"
                    if subject:
                        direct_url += f"&subject={normalized_subject.replace(' ', '+')}"
                    if normalized_exam_type:
                        direct_url += f"&level={normalized_exam_type.replace(' ', '+')}"
                    
                    self.driver.get(direct_url)
                    time.sleep(3)
                    
                    # Get updated page and check for PDFs again
                    html = self.driver.page_source
                    soup = BeautifulSoup(html, 'lxml')
                    pdf_links = soup.find_all('a', href=lambda href: href and href.lower().endswith('.pdf'))
                
                if not pdf_links:
                    logger.warning(f"No PDF links found for {subject} ({exam_type}) after multiple attempts")
                else:
                    logger.info(f"Found {len(pdf_links)} PDF links, filtering for {subject} ({exam_type})")
                
                # Process each PDF link
                for link in pdf_links:
                    pdf_url = urljoin(self.base_url, link['href'])
                    link_text = link.get_text().strip()
                    filename = os.path.basename(urlparse(pdf_url).path)
                    
                    # Extract details from the filename and link text
                    paper_details = self._parse_paper_details(filename, link_text)
                    
                    # Skip papers older than year_from
                    if paper_details['year'] < year_from:
                        continue
                    
                    # Create a standardized filename
                    standardized_filename = f"{self.name}_{normalize_subject_name(subject)}_{paper_details['year']}_{paper_details['season']}_Paper{paper_details['paper_number']}"
                    
                    if paper_details['document_type'] == 'Mark Scheme':
                        standardized_filename += "_MS"
                    elif paper_details['document_type'] == 'Examiner Report':
                        standardized_filename += "_ER"
                    
                    standardized_filename += ".pdf"
                    
                    # Create subdirectory path
                    normalized_subject_str = normalize_subject_name(subject).replace(" ", "_")
                    normalized_exam_type_str = normalize_exam_type(exam_type).replace(" ", "_")
                    
                    subdir = os.path.join(
                        normalized_exam_type_str,
                        normalized_subject_str,
                        str(paper_details['year']),
                        paper_details['season']
                    )
                    
                    # Determine document type for directory structure
                    document_type = paper_details['document_type'].lower().replace(" ", "_")
                    
                    # Download the paper
                    logger.info(f"Downloading {paper_details['document_type']} from {pdf_url}")
                    file_path = self._download_document(
                        pdf_url,
                        standardized_filename,
                        subdir,
                        document_type
                    )
                    
                    if file_path:
                        # Create paper data dictionary
                        papers.append(self._build_paper_data(
                            exam_board=self.name,
                            exam_type=normalized_exam_type_str,
                            subject=normalized_subject_str,
                            year=paper_details['year'],
                            season=paper_details['season'],
                            title=paper_details['title'],
                            paper_number=paper_details['paper_number'],
                            document_type=paper_details['document_type'],
                            specification_code=paper_details['subject_code'],
                            file_path=file_path
                        ))
                
                logger.info(f"Downloaded {len(papers)} papers for {subject} ({exam_type})")
            
            except Exception as e:
                logger.error(f"Error parsing search results: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"Error scraping papers: {e}", exc_info=True)
        
        finally:
            # Ensure browser is closed
            self.close()
        
        return papers
