"""
CCEA exam board scraper implementation.

This module provides the CCEAScraper class that scrapes topic lists and exam materials
from the CCEA (Council for the Curriculum, Examinations and Assessment) exam board website.
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
from urllib.parse import urljoin, urlparse, parse_qs, unquote

from scrapers.base_scraper import BaseScraper
from utils.logger import get_logger
from utils.helpers import (
    sanitize_text, normalize_subject_name, normalize_exam_type, 
    extract_tables_from_html, ensure_directory, random_delay
)

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


class CCEAScraper(BaseScraper):
    """
    Scraper for the CCEA exam board website.
    """
    
    def __init__(self, headless=True, delay=1.5, output_dir="data"):
        """
        Initialize the CCEA scraper.
        
        Args:
            headless (bool): Whether to run the browser in headless mode
            delay (float): Delay between requests in seconds
            output_dir (str): Directory to save raw scraped data
        """
        super().__init__(
            name="CCEA",
            base_url="https://ccea.org.uk",
            headless=headless,
            delay=delay,
            output_dir=output_dir
        )
        
        # CCEA-specific URLs
        self.qualifications_url = urljoin(self.base_url, "/qualification-search")
        self.gcse_past_papers_url = urljoin(self.base_url, "/key-stage-4/gcse/past-papers-mark-schemes")
        self.alevel_past_papers_url = urljoin(self.base_url, "/post-16/gce/past-papers-mark-schemes")
        
        # Map of normalized subject names to CCEA subject codes
        self.subject_code_map = {}
        
        logger.info("CCEA scraper initialized")
    
    def _get_subject_urls(self, exam_type=None):
        """
        Get URLs for all subjects based on exam type.
        
        Args:
            exam_type (str, optional): Type of exam to filter by
            
        Returns:
            dict: Dictionary mapping subject names to their URLs
        """
        logger.info(f"Getting subject URLs for CCEA" + (f" ({exam_type})" if exam_type else ""))
        
        # Normalize exam_type for consistent matching
        norm_exam_type = normalize_exam_type(exam_type) if exam_type else None
        
        # Hard-coded subject URLs for CCEA subjects
        subject_urls = {}
        
        # GCSE Subjects
        if not norm_exam_type or norm_exam_type.lower() == 'gcse':
            # Core subjects
            subject_urls["Mathematics"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-mathematics-2017"
            subject_urls["Further Mathematics"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-further-mathematics-2017"
            subject_urls["English Language"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-english-language-2017"
            subject_urls["English Literature"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-english-literature-2017"
            
            # Sciences
            subject_urls["Biology"] = "https://ccea.org.uk/downloads/docs/Specifications/GCSE/GCSE%20Biology%20%282017%29/GCSE%20Biology%20%282017%29-specification-Standard.pdf"
            subject_urls["Chemistry"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-chemistry-2017"
            subject_urls["Physics"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-physics-2017"
            subject_urls["Science Double Award"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-science-double-award-2017"
            subject_urls["Science Single Award"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-science-single-award-2017"
            subject_urls["Agriculture and Land Use"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-agriculture-and-land-use-2019"
            subject_urls["Statistics"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-statistics-2017"
            
            # Humanities
            subject_urls["Religious Studies"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-religious-studies-2017"
            subject_urls["History"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-history-2017"
            subject_urls["Geography"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-geography-2017"
            subject_urls["Government and Politics"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-government-and-politics-2017"
            
            # Languages
            subject_urls["French"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-french-2017"
            subject_urls["Spanish"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-spanish-2017"
            subject_urls["German"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-german-2017"
            subject_urls["Irish"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-gaeilge-2017"
            subject_urls["Gaeilge"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-gaeilge-2017"
            
            # Creative and technical
            subject_urls["Art and Design"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-art-and-design-2017"
            subject_urls["Agriculture and Land Use"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-agriculture-and-land-use-2019"
            subject_urls["Construction and the Built Environment"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-construction-and-built-environment-2017"
            subject_urls["Textiles"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-textiles-2017"
            subject_urls["Food and Nutrition"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-food-and-nutrition-2017"
            subject_urls["Food Preparation and Nutrition"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-food-and-nutrition-2017"
            subject_urls["Hospitality and Catering"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-hospitality-2017"
            subject_urls["Music"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-music-2017"
            subject_urls["Drama"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-drama-2017"
            subject_urls["Dance"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-performing-arts-2017"
            subject_urls["Moving Image Arts"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-moving-image-arts-2017"
            
            # Technology and business
            subject_urls["Business Studies"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-business-and-communication-systems-2017"
            subject_urls["Business and Communication Systems"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-business-and-communication-systems-2017"
            subject_urls["Economics"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-economics-2017"
            subject_urls["Digital Technology"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-digital-technology-2017"
            subject_urls["Engineering and Manufacturing"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-engineering-and-manufacturing-2017"
            subject_urls["Electronics"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-electronics-2017"
            subject_urls["Motor Vehicle and Road User Studies"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-motor-vehicle-and-road-user-studies-2017"


            # Social sciences
            subject_urls["Sociology"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-sociology-2017"
            subject_urls["Psychology"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-psychology-2017"
            subject_urls["Media Studies"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-media-studies-2017"
            subject_urls["Government and Politics"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-government-and-politics-2017"
            
            # Physical education and health
            subject_urls["Physical Education"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-physical-education-2017"
            subject_urls["Health and Social Care"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-health-and-social-care-2017"
            subject_urls["Home Economics: Child Development"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-home-economics-child-development-2017"
            subject_urls["Home Economics: Food and Nutrition"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-home-economics-food-and-nutrition-2017"
            subject_urls["Contemporary Crafts"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-contemporary-crafts-2017"
            subject_urls["Learning for Life and Work"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-learning-life-and-work-2017"
            subject_urls["Leisure, Travel and Tourism"] = "https://ccea.org.uk/key-stage-4/gcse/subjects/gcse-leisure-travel-and-tourism-2017"
        
        # A-Level Subjects
        if not norm_exam_type or norm_exam_type.lower() in ['a-level', 'as-level', 'gce']:
            # Mathematics
            subject_urls["Mathematics (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-mathematics-2018"
            subject_urls["Further Mathematics (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-further-mathematics-2018"
            subject_urls["Statistics (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-statistics-2018"
            
            # English
            subject_urls["English Language (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-english-language-2016"
            subject_urls["English Literature (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-english-literature-2016"
            subject_urls["English Language and Literature (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-english-language-and-literature-2016"
            
            # Sciences
            subject_urls["Biology (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-biology-2016"
            subject_urls["Chemistry (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-chemistry-2016"
            subject_urls["Physics (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-physics-2016"
            subject_urls["Environmental Science (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-environmental-technology-2016"
            subject_urls["Geology (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-geology-2016"
            
            # Humanities
            subject_urls["History (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-history-2016"
            subject_urls["Ancient History (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-ancient-history-2016"
            subject_urls["Geography (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-geography-2016"
            subject_urls["Religious Studies (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-religious-studies-2016"
            subject_urls["Philosophy (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-religious-studies-2016"
            subject_urls["Classical Civilization (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-classical-civilisation-2016"
            subject_urls["Latin (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-latin-2016"
            subject_urls["Classical Greek (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-classical-greek-2016"
            subject_urls["Archaeology (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-archaeology-2016"
            
            # Languages
            subject_urls["French (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-french-2016"
            subject_urls["Spanish (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-spanish-2016"
            subject_urls["German (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-german-2016"
            subject_urls["Irish (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-gaeilge-2016"
            subject_urls["Arabic (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-arabic-2016"
            subject_urls["Chinese (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-chinese-2016"
            subject_urls["Italian (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-italian-2016"
            subject_urls["Japanese (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-japanese-2016"
            subject_urls["Russian (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-russian-2016"
            subject_urls["Urdu (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-urdu-2016"
            
            # Social Sciences
            subject_urls["Psychology (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-psychology-2016"
            subject_urls["Sociology (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-sociology-2016"
            subject_urls["Economics (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-economics-2016"
            subject_urls["Business Studies (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-business-studies-2016"
            subject_urls["Accounting (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-accounting-2016"
            subject_urls["Government and Politics (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-government-and-politics-2016"
            subject_urls["Law (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-law-2016"
            subject_urls["Criminology (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-criminology-2016"
            
            # Technology
            subject_urls["Digital Technology (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-digital-technology-2016"
            subject_urls["Design and Technology (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-technology-and-design-2016"
            subject_urls["Textiles (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-textiles-2016"
            subject_urls["Electronics (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-electronics-2016"
            
            # Creative Arts
            subject_urls["Art and Design (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-art-and-design-2016"
            subject_urls["History of Art (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-history-of-art-2016"
            subject_urls["Drama and Theatre (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-drama-and-theatre-studies-2016"
            subject_urls["Theatre Studies (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-drama-and-theatre-studies-2016"
            subject_urls["Media Studies (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-media-studies-2016"
            subject_urls["Film Studies (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-moving-image-arts-2016"
            subject_urls["Music (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-music-2016"
            subject_urls["Music Technology (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-music-technology-2016"
            
            # Physical Education and Health
            subject_urls["Physical Education (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-physical-education-2016"
            subject_urls["Sports Science (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-sports-science-and-active-leisure-industry-2016"
            subject_urls["Dance (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-performing-arts-2016"
            subject_urls["Health and Social Care (A-Level)"] = "https://ccea.org.uk/post-16/gce/subjects/gce-health-and-social-care-2016"
        
        logger.info(f"Found {len(subject_urls)} subject URLs")
        return subject_urls
    
    def _construct_spec_url(self, subject, exam_type):
        """
        Construct a direct specification URL based on CCEA's URL patterns.
        
        Args:
            subject (str): Subject name
            exam_type (str): Exam type
            
        Returns:
            str: Direct specification URL
        """
        # Format the subject name for URL construction
        # Replace spaces with %20 for URL encoding
        formatted_subject = subject.replace(" ", "%20")
        
        # Handle special cases for subject names
        if subject.lower() == "english language":
            formatted_subject = "English%20Language"
        elif subject.lower() == "english literature":
            formatted_subject = "English%20Literature"
        
        # Construct URL based on exam type
        if exam_type.lower() == "gcse":
            # GCSE pattern: https://ccea.org.uk/downloads/docs/Specifications/GCSE/GCSE%20[Subject]%20%282017%29/GCSE%20[Subject]%20%282017%29-specification-Standard.pdf
            url = f"https://ccea.org.uk/downloads/docs/Specifications/GCSE/GCSE%20{formatted_subject}%20%282017%29/GCSE%20{formatted_subject}%20%282017%29-specification-Standard.pdf"
        else:
            # A-Level pattern (GCE): https://ccea.org.uk/downloads/docs/Specifications/GCE/GCE%20[Subject]%20%282016%29/GCE%20[Subject]%20%282016%29-specification-Standard.pdf
            url = f"https://ccea.org.uk/downloads/docs/Specifications/GCE/GCE%20{formatted_subject}%20%282016%29/GCE%20{formatted_subject}%20%282016%29-specification-Standard.pdf"
        
        return url
    
    def _get_spec_url_from_subject_page(self, subject_url, subject=None, exam_type=None):
        """
        Get specification URL from a subject page.
        
        Args:
            subject_url (str): URL of the subject page
            subject (str, optional): Subject name, if known
            exam_type (str, optional): Exam type, if known
            
        Returns:
            str or None: URL of the specification
        """
        # If we have subject and exam_type, try direct URL construction first
        if subject and exam_type:
            direct_url = self._construct_spec_url(subject, exam_type)
            
            # Check if the URL actually exists (HEAD request)
            try:
                import requests
                response = requests.head(direct_url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"Found specification using direct URL pattern for {subject} ({exam_type})")
                    return direct_url
            except Exception as e:
                logger.debug(f"Error checking direct URL: {e}")
        
        # If direct URL construction failed or wasn't attempted, try the traditional methods
        logger.info(f"Attempting to find specification link on the subject page")
        html = self._get_page(subject_url, use_selenium=True)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        
        # CCEA typically has a "Specification" link in a "Key Documents" or "Related Documents" section
        # Look for specification links in various ways
        
        # Method 1: Direct specification links
        spec_links = soup.find_all('a', string=re.compile(r'specification', re.IGNORECASE))
        for link in spec_links:
            href = link.get('href', '')
            if href and href.lower().endswith('.pdf'):
                return urljoin(self.base_url, href)
        
        # Method 2: Look for links in sections that typically contain specifications
        for section_name in ['key-documents', 'related-documents', 'specification', 'support-material']:
            section = soup.find(class_=re.compile(section_name, re.IGNORECASE))
            if section:
                for link in section.find_all('a', href=True):
                    href = link.get('href', '')
                    text = link.text.strip()
                    if ('specification' in text.lower() or 'spec' in text.lower()) and href.lower().endswith('.pdf'):
                        return urljoin(self.base_url, href)
            
        # Method 3: Look for any PDF link containing "specification" in the URL
        for link in soup.find_all('a', href=re.compile(r'specification|spec', re.IGNORECASE)):
            href = link.get('href', '')
            if href and href.lower().endswith('.pdf'):
                return urljoin(self.base_url, href)
        
        # Method 4: Check tabs that might contain specification links
        for tab in soup.find_all(class_=re.compile('tab|tabs', re.IGNORECASE)):
            for link in tab.find_all('a', href=True):
                href = link.get('href', '')
                text = link.text.strip()
                if ('specification' in text.lower() or 'spec' in href.lower()) and href.lower().endswith('.pdf'):
                    return urljoin(self.base_url, href)
        
        # If all methods failed but we have subject and exam_type, return the direct URL anyway
        # as a last resort (it might work even if the HEAD request failed)
        if subject and exam_type:
            logger.warning(f"Could not find specification link on page, trying direct URL as last resort")
            return self._construct_spec_url(subject, exam_type)
            
        return None
    
    def _get_subject_code(self, subject_url):
        """
        Extract subject code from the subject URL or page.
        
        Args:
            subject_url (str): URL of the subject page
            
        Returns:
            str or None: Subject code
        """
        # Look for CCEA subject codes in the URL
        url_match = re.search(r'/([A-Za-z0-9]{4,6})$', subject_url)
        if url_match:
            return url_match.group(1).upper()
        
        # Try extracting from page content
        html = self._get_page(subject_url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Look for patterns like: "Specification Code: G9999"
        code_pattern = re.compile(r'(?:Specification|Code|Subject Code|Qualification Code)[\s:]*([\w\d]{4,6})', re.IGNORECASE)
        
        # Search in various elements
        for element in soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'span']):
            text = element.text.strip()
            match = code_pattern.search(text)
            if match:
                return match.group(1).upper()
        
        return None
        
    def _get_fallback_topics(self, subject, exam_type):
        """
        Get fallback topic structure for a given subject and exam type.
        
        This method provides predefined topic structures for common subjects
        when AI extraction fails or isn't available.
        
        Args:
            subject (str): Subject name
            exam_type (str): Exam type
            
        Returns:
            list: List of topic data dictionaries
        """
        logger.info(f"Using fallback topic structure for {subject} ({exam_type})")
        
        # Normalize subject name and exam type for consistent matching
        norm_subject = normalize_subject_name(subject).lower()
        norm_exam_type = normalize_exam_type(exam_type).lower()
        
        topic_structure = {}
        
        # GCSE Subject fallbacks
        if norm_exam_type == "gcse":
            # GCSE Chemistry
            if "chemistry" in norm_subject:
                topic_structure = {
                    "Unit 1: Structures, Trends, Chemical Reactions, Quantitative Chemistry and Analysis": [
                        "Atomic structure",
                        "Bonding",
                        "Structures",
                        "Periodic Table",
                        "Quantitative chemistry",
                        "Chemical reactions",
                        "Acids, bases and salts",
                        "Chemical analysis"
                    ],
                    "Unit 2: Further Chemical Reactions, Rates and Equilibrium, Calculations and Organic Chemistry": [
                        "Metals and reactivity series",
                        "Rates of reaction",
                        "Equilibrium",
                        "Organic chemistry",
                        "Quantitative chemistry",
                        "Electrochemistry",
                        "Energy changes in chemistry"
                    ],
                    "Unit 3: Practical Assessment": [
                        "Practical skills assessment",
                        "Practical investigation"
                    ]
                }
            
            # GCSE Mathematics
            elif "math" in norm_subject:
                topic_structure = {
                    "Number": [
                        "Place value",
                        "Operations with integers",
                        "Fractions, decimals and percentages",
                        "Estimation and approximation"
                    ],
                    "Algebra": [
                        "Expressions",
                        "Equations and inequalities",
                        "Sequences and functions",
                        "Graphs"
                    ],
                    "Geometry and Measures": [
                        "Properties of shapes",
                        "Coordinate geometry",
                        "Measures and mensuration",
                        "Transformations",
                        "Vectors"
                    ],
                    "Statistics and Probability": [
                        "Data collection and representation",
                        "Statistical measures",
                        "Probability"
                    ]
                }
            
            # GCSE Biology
            elif "biology" in norm_subject:
                topic_structure = {
                    "Unit 1: Cells, Living Processes and Biodiversity": [
                        "Cells",
                        "Photosynthesis and plants",
                        "Nutrition and health",
                        "Enzymes and digestion",
                        "Respiratory system",
                        "Biodiversity and classification"
                    ],
                    "Unit 2: Body Systems, Genetics, Microorganisms and Health": [
                        "Circulatory system",
                        "Reproduction and fertility",
                        "Genetics",
                        "Coordination and control",
                        "Microorganisms and health",
                        "Ecosystem interactions"
                    ],
                    "Unit 3: Practical Skills": [
                        "Laboratory techniques",
                        "Practical investigations",
                        "Data analysis"
                    ]
                }
            
            # GCSE Physics
            elif "physics" in norm_subject:
                topic_structure = {
                    "Unit 1: Motion, Force, Moments, Energy, Density, Kinetic Theory, Radioactivity": [
                        "Motion",
                        "Forces",
                        "Energy",
                        "Density",
                        "Kinetic theory of matter",
                        "Radioactivity"
                    ],
                    "Unit 2: Waves, Light, Electricity, Magnetism, Nuclear Physics, Universe": [
                        "Waves",
                        "Light",
                        "Electricity",
                        "Magnetism and electromagnetism",
                        "Nuclear physics",
                        "Universe and space"
                    ],
                    "Unit 3: Practical Skills": [
                        "Practical techniques",
                        "Data collection and analysis",
                        "Experimental design"
                    ]
                }
                
            # GCSE English Language
            elif "english language" in norm_subject:
                topic_structure = {
                    "Unit 1: Writing for Purpose and Audience and Reading to Access Non-fiction and Media Texts": [
                        "Writing for purpose and audience",
                        "Reading non-fiction texts",
                        "Media texts",
                        "Language analysis"
                    ],
                    "Unit 2: Speaking and Listening": [
                        "Individual presentation",
                        "Group discussion",
                        "Role play"
                    ],
                    "Unit 3: Studying Spoken and Written Language": [
                        "Studying spoken language",
                        "Studying written language"
                    ],
                    "Unit 4: Personal or Creative Writing and Reading Literary and Non-fiction Texts": [
                        "Personal writing",
                        "Creative writing",
                        "Reading literary texts",
                        "Reading non-fiction texts"
                    ]
                }
            
            # GCSE English Literature
            elif "english literature" in norm_subject:
                topic_structure = {
                    "Unit 1: The Study of Prose": [
                        "Study of a novel",
                        "Literary analysis",
                        "Context and themes"
                    ],
                    "Unit 2: The Study of Drama and Poetry": [
                        "Study of a drama text",
                        "Analysis of poetry",
                        "Comparative analysis"
                    ],
                    "Unit 3: The Study of Shakespeare": [
                        "Shakespeare play",
                        "Character analysis",
                        "Themes and context"
                    ]
                }
            
            # GCSE Geography 
            elif "geography" in norm_subject:
                topic_structure = {
                    "Unit 1: Understanding Our Natural World": [
                        "River environments",
                        "Coastal environments",
                        "Our changing weather and climate",
                        "The restless Earth"
                    ],
                    "Unit 2: Living in Our World": [
                        "Population and migration",
                        "Settlement",
                        "Development",
                        "Managing our resources"
                    ],
                    "Unit 3: Fieldwork": [
                        "Primary data collection",
                        "Data presentation",
                        "Analysis and evaluation"
                    ]
                }
                
            # GCSE History
            elif "history" in norm_subject:
                topic_structure = {
                    "Unit 1: Modern World Studies in Depth and Local Study": [
                        "Life in Nazi Germany",
                        "Northern Ireland and its Neighbours",
                        "Local historical investigation"
                    ],
                    "Unit 2: International Relations": [
                        "Peace, war and neutrality",
                        "The Cold War",
                        "New international relations"
                    ]
                }
                
            # Fallback for all other GCSE subjects - generic structure
            else:
                logger.warning(f"No specific fallback structure for {subject} GCSE. Using generic structure.")
                topic_structure = {
                    "Unit 1: Foundation Knowledge and Concepts": [
                        "Basic principles and terminology",
                        "Key concepts and theories",
                        "Fundamental skills and techniques"
                    ],
                    "Unit 2: Development and Applications": [
                        "Advanced concepts",
                        "Practical applications",
                        "Analysis and problem solving"
                    ],
                    "Unit 3: Integration and Assessment": [
                        "Synthesis of knowledge",
                        "Evaluation and critical thinking",
                        "Practical assessment"
                    ]
                }
                
        # A-Level Subject fallbacks
        elif norm_exam_type in ["a-level", "as-level", "gce"]:
            # A-Level Chemistry
            if "chemistry" in norm_subject:
                topic_structure = {
                    "AS 1: Basic Concepts in Physical and Inorganic Chemistry": [
                        "Atomic structure",
                        "Bonding",
                        "Intermolecular forces",
                        "Structure",
                        "Redox reactions",
                        "Periodicity",
                        "Group 2 elements and compounds",
                        "Group 7 elements and compounds",
                        "Qualitative analysis",
                        "Quantitative analysis",
                        "Gases, liquids and solids",
                        "Energetics"
                    ],
                    "AS 2: Further Physical and Inorganic Chemistry and Introduction to Organic Chemistry": [
                        "Molecular orbital theory",
                        "Acid-base reactions",
                        "Kinetics",
                        "Equilibrium",
                        "Organic Chemistry",
                        "Alkanes",
                        "Alkenes",
                        "Haloalkanes",
                        "Alcohols",
                        "Infrared spectroscopy",
                        "Structural isomerism"
                    ],
                    "AS 3: Practical Assessment": [
                        "Laboratory practical skills",
                        "Analytical techniques"
                    ],
                    "A2 1: Further Physical and Organic Chemistry": [
                        "Thermodynamics",
                        "Equilibrium",
                        "Acid-base equilibria",
                        "Carboxylic acids and derivatives",
                        "Aldehydes and ketones",
                        "Nitrogen compounds",
                        "Aromatic chemistry",
                        "Polymers",
                        "Nuclear magnetic resonance spectroscopy",
                        "Mass spectrometry"
                    ],
                    "A2 2: Analytical, Transition Metals, Electrochemistry and Organic Nitrogen Chemistry": [
                        "Transition metals",
                        "Electrode potentials",
                        "Further redox reactions",
                        "Coordination complexes",
                        "Color chemistry",
                        "Amines",
                        "Amino acids and proteins",
                        "Organic synthesis",
                        "Chromatography"
                    ],
                    "A2 3: Practical Assessment": [
                        "Advanced practical skills",
                        "Analytical techniques",
                        "Research and analysis"
                    ]
                }
                
            # A-Level Mathematics
            elif "math" in norm_subject and "further" not in norm_subject:
                topic_structure = {
                    "AS 1: Pure Mathematics": [
                        "Algebra and functions",
                        "Coordinate geometry",
                        "Sequences and series",
                        "Trigonometry",
                        "Exponentials and logarithms",
                        "Differentiation",
                        "Integration"
                    ],
                    "AS 2: Applied Mathematics": [
                        "Kinematics",
                        "Forces and Newton's laws",
                        "Statistical sampling",
                        "Data presentation and interpretation",
                        "Probability",
                        "Statistical distributions"
                    ],
                    "A2 1: Pure Mathematics": [
                        "Proof",
                        "Algebra and functions",
                        "Coordinate geometry",
                        "Sequences and series",
                        "Trigonometry",
                        "Differentiation",
                        "Integration",
                        "Numerical methods"
                    ],
                    "A2 2: Applied Mathematics": [
                        "Mechanics",
                        "Moments",
                        "Projectiles",
                        "Statistical hypothesis testing",
                        "Probability",
                        "Regression and correlation"
                    ]
                }
                
            # A-Level Biology
            elif "biology" in norm_subject:
                topic_structure = {
                    "AS 1: Molecules and Cells": [
                        "Molecules",
                        "Enzymes",
                        "Cell structure",
                        "Transport in cells",
                        "Cell division and organization"
                    ],
                    "AS 2: Organisms and Biodiversity": [
                        "Transport in plants and animals",
                        "Adaptation of organisms",
                        "Biodiversity",
                        "Classification",
                        "Ecology"
                    ],
                    "AS 3: Practical Skills": [
                        "Laboratory skills",
                        "Data handling",
                        "Research methods"
                    ],
                    "A2 1: Physiology, Coordination and Control, and Ecosystems": [
                        "Homeostasis",
                        "Immunity",
                        "Coordination and control",
                        "Ecosystems",
                        "Population dynamics"
                    ],
                    "A2 2: Biochemistry, Genetics and Evolutionary Trends": [
                        "Respiration",
                        "Photosynthesis",
                        "DNA technology",
                        "Genetics",
                        "Evolution"
                    ],
                    "A2 3: Practical Skills": [
                        "Advanced practical techniques",
                        "Analysis and evaluation",
                        "Investigative skills"
                    ]
                }
                
            # A-Level Physics
            elif "physics" in norm_subject:
                topic_structure = {
                    "AS 1: Forces, Energy and Electricity": [
                        "Forces",
                        "Energy",
                        "Materials",
                        "Electricity"
                    ],
                    "AS 2: Waves, Photons and Astronomy": [
                        "Waves",
                        "Photons",
                        "Quantum theory",
                        "Astronomy and space"
                    ],
                    "AS 3: Practical Techniques": [
                        "Experimental design",
                        "Data collection and analysis",
                        "Uncertainties"
                    ],
                    "A2 1: Deformation of Solids, Thermal Physics, Circular Motion, Oscillations and Atomic and Nuclear Physics": [
                        "Deformation of solids",
                        "Thermal physics",
                        "Circular motion",
                        "Simple harmonic motion",
                        "Atomic and nuclear physics"
                    ],
                    "A2 2: Fields, Capacitors and Particle Physics": [
                        "Gravitational fields",
                        "Electric fields",
                        "Magnetic fields",
                        "Capacitors",
                        "Particle physics"
                    ],
                    "A2 3: Practical Techniques and Data Analysis": [
                        "Advanced experimental techniques",
                        "Data analysis and evaluation",
                        "Research methods"
                    ]
                }
                
            # Fallback for all other A-Level subjects - generic structure
            else:
                logger.warning(f"No specific fallback structure for {subject} A-Level. Using generic structure.")
                topic_structure = {
                    "AS 1: Foundation Knowledge and Principles": [
                        "Key theories and concepts",
                        "Fundamental methodologies",
                        "Introduction to advanced techniques"
                    ],
                    "AS 2: Applied Theory and Analysis": [
                        "Applications of theory",
                        "Analysis methods",
                        "Problem-solving techniques"
                    ],
                    "AS 3: Research and Skills": [
                        "Practical skills",
                        "Research methods",
                        "Data handling"
                    ],
                    "A2 1: Advanced Theory and Integration": [
                        "Complex theories and models",
                        "Integration of knowledge",
                        "Advanced concepts"
                    ],
                    "A2 2: Specialist Applications and Analysis": [
                        "Specialized areas of study",
                        "Critical analysis",
                        "Evaluation techniques"
                    ],
                    "A2 3: Professional and Research Skills": [
                        "Professional techniques",
                        "Independent research",
                        "Advanced applications"
                    ]
                }
        
        # Fallback for other exam types or if no match found - simple structure
        else:
            logger.warning(f"No fallback structure available for {exam_type}. Using simple structure.")
            topic_structure = {
                "Core Knowledge": [
                    "Fundamental principles",
                    "Key concepts",
                    "Basic skills"
                ],
                "Applications and Techniques": [
                    "Practical applications",
                    "Techniques and methods",
                    "Problem solving"
                ],
                "Advanced Topics": [
                    "Specialized areas",
                    "Integration of knowledge",
                    "Critical analysis"
                ]
            }
        
        # Convert topic structure to topic data list
        topics_data = []
        for module, topics in topic_structure.items():
            for topic in topics:
                topics_data.append(self._build_topic_data(
                    exam_board="CCEA",
                    exam_type=exam_type,
                    subject=subject,
                    module=module,
                    topic=topic
                ))
        
        logger.info(f"Generated {len(topics_data)} topics for {subject} ({exam_type}) using fallback structure")
        return topics_data
    
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
        
        # For CCEA, most specifications are PDFs
        if specification_url.lower().endswith('.pdf'):
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
                return self._get_fallback_topics(subject, exam_type)
            
            # Try AI-assisted extraction if available
            if AI_HELPERS_AVAILABLE:
                logger.info(f"Attempting AI-assisted topic extraction for {subject} PDF")
                ai_topics = extract_topics_from_pdf(
                    pdf_path, subject, exam_type, self.name
                )
                
                if ai_topics and len(ai_topics) > 0:
                    logger.info(f"AI successfully extracted {len(ai_topics)} topics from PDF")
                    return ai_topics
                else:
                    logger.warning("AI extraction from PDF failed, falling back to predefined structures")
            else:
                logger.warning(f"No AI helpers available for PDF extraction: {pdf_path}")
            
            # If we reach here, AI extraction failed or wasn't available
            # Try using fallback topic structures
            return self._get_fallback_topics(subject, exam_type)
        
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
        
        # Special case handling for common subjects
        if subject.lower() == "mathematics" and exam_type.lower() == "gcse":
            # GCSE Mathematics topics for CCEA (based on their specification structure)
            topic_structure = {
                "Number": [
                    "Place value",
                    "Operations with integers",
                    "Fractions, decimals and percentages",
                    "Estimation and approximation"
                ],
                "Algebra": [
                    "Expressions",
                    "Equations and inequalities",
                    "Sequences and functions",
                    "Graphs"
                ],
                "Geometry and Measures": [
                    "Properties of shapes",
                    "Coordinate geometry",
                    "Measures and mensuration",
                    "Transformations",
                    "Vectors"
                ],
                "Statistics and Probability": [
                    "Data collection and representation",
                    "Statistical measures",
                    "Probability"
                ]
            }
            
            topics_data = []
            for module, topics in topic_structure.items():
                for topic in topics:
                    topics_data.append(self._build_topic_data(
                        exam_board="CCEA",
                        exam_type=exam_type,
                        subject=subject,
                        module=module,
                        topic=topic
                    ))
            
            logger.info(f"Generated {len(topics_data)} topics for Mathematics GCSE using predefined structure")
            return topics_data
        
        # Fallback to conventional extraction methods
        logger.warning(f"No topic extraction method available for {subject}. Using AI extraction is recommended.")
        return []
    
    def scrape_topics(self, subject=None, exam_type=None):
        """
        Scrape topic lists from the CCEA website.
        
        Args:
            subject (str, optional): Subject to scrape topics for
            exam_type (str, optional): Exam type to scrape topics for
            
        Returns:
            list: List of topic data dictionaries
        """
        logger.info(f"Scraping CCEA topics" + 
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
                # Get the specification URL - pass subject and exam type for direct URL construction
                current_exam_type = exam_type
                if not current_exam_type:
                    if "gcse" in subj_url.lower():
                        current_exam_type = "GCSE"
                    elif any(level in subj_url.lower() for level in ["gce", "a-level", "as-level"]):
                        current_exam_type = "A-Level"
                    else:
                        current_exam_type = "GCSE"  # Default to GCSE if can't determine
                
                spec_url = self._get_spec_url_from_subject_page(subj_url, subj_name, current_exam_type)
                if not spec_url:
                    logger.warning(f"Could not find specification URL for {subj_name}")
                    continue
                
                # Extract topics from specification
                current_exam_type = exam_type
                if not current_exam_type:
                    if "gcse" in subj_url.lower():
                        current_exam_type = "GCSE"
                    elif any(level in subj_url.lower() for level in ["gce", "a-level", "as-level"]):
                        current_exam_type = "A-Level"
                    else:
                        current_exam_type = "GCSE"  # Default to GCSE if can't determine
                        
                topics = self._extract_specification_topics(
                    spec_url, 
                    current_exam_type,
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
        
        logger.info(f"Scraped {len(all_topics)} topics from CCEA")
        return all_topics
    
    def scrape_papers(self, subject=None, exam_type=None, year_from=2021):
        """
        Scrape exam papers from the CCEA website.
        
        Args:
            subject (str, optional): Subject to scrape papers for
            exam_type (str, optional): Exam type to scrape papers for
            year_from (int): Year to start scraping papers from
            
        Returns:
            list: List of paper data dictionaries
        """
        logger.info(f"Scraping CCEA papers" + 
                   (f" for {subject}" if subject else "") + 
                   (f" ({exam_type})" if exam_type else "") +
                   f" from {year_from}")
        
        if not subject or not exam_type:
            logger.warning("Both subject and exam_type are required for CCEA scraper")
            return []
        
        # Normalize inputs
        normalized_subject = normalize_subject_name(subject)
        normalized_exam_type = normalize_exam_type(exam_type)
        
        # For CCEA, past papers are typically accessed through a past papers finder tool
        # We'll use Selenium to interact with this tool
        self._init_driver()
        papers = []
        
        try:
            # Navigate to the past papers finder page
            self.driver.get(self.past_papers_url)
            
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form, select, button"))
            )
            
            # Select the appropriate exam type
            try:
                # CCEA's site might have different dropdown IDs, so we'll try a few options
                exam_selectors = [
                    "qualification-level", "qualificationLevel", "ddlQualification",
                    "qualification-type", "qualificationType"
                ]
                
                exam_select = None
                for selector in exam_selectors:
                    try:
                        exam_select = Select(self.driver.find_element(By.ID, selector))
                        break
                    except:
                        try:
                            exam_select = Select(self.driver.find_element(By.NAME, selector))
                            break
                        except:
                            continue
                
                if exam_select:
                    # Find the appropriate option based on exam type
                    target_text = ""
                    if normalized_exam_type.lower() == "gcse":
                        target_text = "GCSE"
                    elif normalized_exam_type.lower() in ["a-level", "as-level", "gce"]:
                        target_text = "GCE"
                    
                    # Select the option that contains our target text
                    for option in exam_select.options:
                        if target_text.lower() in option.text.lower():
                            exam_select.select_by_visible_text(option.text)
                            break
                    
                    # Wait for any AJAX updates
                    time.sleep(2)
                else:
                    logger.warning("Could not find exam type selector")
            
            except Exception as e:
                logger.warning(f"Error selecting exam type: {e}")
            
            # Select the appropriate subject
            try:
                # Try different possible subject field IDs
                subject_selectors = [
                    "subject", "ddlSubject", "SubjectDropDown", 
                    "subject-name", "subjectName"
                ]
                
                subject_select = None
                for selector in subject_selectors:
                    try:
                        subject_select = Select(self.driver.find_element(By.ID, selector))
                        break
                    except:
                        try:
                            subject_select = Select(self.driver.find_element(By.NAME, selector))
                            break
                        except:
                            continue
                
                if subject_select:
                    # Look for the option that best matches our subject
                    best_match = None
                    for option in subject_select.options:
                        if normalized_subject.lower() == option.text.lower():
                            # Exact match, select it immediately
                            subject_select.select_by_visible_text(option.text)
                            best_match = option.text
                            break
                        elif normalized_subject.lower() in option.text.lower():
                            # Partial match, store it as best match so far
                            best_match = option.text
                    
                    # If we have a partial match but no exact match, use the partial match
                    if best_match and normalized_subject.lower() != best_match.lower():
                        subject_select.select_by_visible_text(best_match)
                    
                    # Wait for any AJAX updates
                    time.sleep(2)
                else:
                    logger.warning("Could not find subject selector")
            
            except Exception as e:
                logger.warning(f"Error selecting subject: {e}")
            
            # Click search/submit button
            try:
                # Find the submit button - try different approaches
                submit_button = None
                
                # Try by type
                buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                if buttons:
                    submit_button = buttons[0]
                
                # Try by text
                if not submit_button:
                    for btn in self.driver.find_elements(By.TAG_NAME, "button"):
                        if any(text in btn.text.lower() for text in ["search", "find", "go", "submit"]):
                            submit_button = btn
                            break
                
                if submit_button:
                    submit_button.click()
                    
                    # Wait for results to load
                    WebDriverWait(self.driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, ".results, .papers, .past-papers, table"))
                    )
                    
                    # Give extra time for any AJAX loading
                    time.sleep(3)
                else:
                    logger.warning("Could not find submit button")
            
            except Exception as e:
                logger.warning(f"Error submitting search: {e}")
            
            # Parse the results
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'lxml')
            
            # Look for PDF links in the results
            # CCEA might structure results as tables, lists, or divs
            result_areas = soup.select(".results, .papers, .past-papers, table, .results-list")
            
            if not result_areas:
                # If no specific result area found, look at the whole page
                result_areas = [soup]
            
            for result_area in result_areas:
                # Find all PDF links
                pdf_links = result_area.select('a[href$=".pdf"]')
                logger.debug(f"Found {len(pdf_links)} PDF links in results")
                
                for link in pdf_links:
                    link_text = link.text.strip()
                    link_url = link.get('href', '')
                    
                    # Skip if the link doesn't look like a paper
                    if not link_text or len(link_text) < 5:
                        continue
                    
                    # See if we can extract a year
                    year_match = re.search(r'(20\d\d)', link_text)
                    year = int(year_match.group(1)) if year_match else None
                    
                    # Skip if it's older than our year threshold
                    if year and year < year_from:
                        logger.debug(f"Skipping paper from {year}: {link_text}")
                        continue
                    
                    # If no year in the text, check the URL
                    if not year:
                        url_year_match = re.search(r'(20\d\d)', link_url)
                        year = int(url_year_match.group(1)) if url_year_match else None
                        
                        if year and year < year_from:
                            logger.debug(f"Skipping paper from {year} (URL-extracted): {link_text}")
                            continue
                    
                    # If still no year, default to current year
                    if not year:
                        year = datetime.now().year
                    
                    # Determine if this is a question paper, mark scheme, or examiner report
                    doc_type = "Question Paper"
                    if any(term in link_text.lower() for term in ["mark scheme", "marking", "ms"]):
                        doc_type = "Mark Scheme"
                    elif any(term in link_text.lower() for term in ["examiner", "report", "er"]):
                        doc_type = "Examiner Report"
                    
                    # Determine season (Summer or Winter)
                    season = "Summer"
                    if any(term in link_text.lower() for term in ["january", "winter", "november"]):
                        season = "Winter"
                    
                    # Try to extract paper number
                    paper_num_match = re.search(r'paper\s*(\d+)', link_text.lower())
                    paper_number = int(paper_num_match.group(1)) if paper_num_match else 1
                    
                    # Try to extract subject code
                    subject_code = ""
                    code_match = re.search(r'([A-Z0-9]{4,6})', link_text)
                    if code_match:
                        subject_code = code_match.group(1)
                    
                    # If link URL is relative, make it absolute
                    if not link_url.startswith('http'):
                        link_url = urljoin(self.base_url, link_url)
                    
                    # Create a filename for the paper
                    filename_parts = []
                    if subject_code:
                        filename_parts.append(subject_code)
                    else:
                        filename_parts.append(normalized_subject.replace(" ", "_"))
                    
                    filename_parts.append(str(year))
                    filename_parts.append(season)
                    filename_parts.append(f"Paper{paper_number}")
                    
                    if doc_type == "Mark Scheme":
                        filename_parts.append("MS")
                    elif doc_type == "Examiner Report":
                        filename_parts.append("ER")
                    
                    filename = "_".join(filename_parts)
                    
                    # Create subdirectory path
                    subdir = os.path.join(
                        normalized_exam_type,
                        normalized_subject,
                        str(year),
                        season
                    )
                    
                    # Determine document type for directory structure
                    document_type = doc_type.lower().replace(" ", "_")
                    
                    # Download the paper
                    file_path = self._download_document(
                        link_url, 
                        filename, 
                        subdir, 
                        document_type
                    )
                    
                    if file_path:
                        # Create paper data dictionary
                        papers.append(self._build_paper_data(
                            exam_board="CCEA",
                            exam_type=normalized_exam_type,
                            subject=normalized_subject,
                            year=year,
                            season=season,
                            title=link_text,
                            paper_number=paper_number,
                            document_type=doc_type,
                            specification_code=subject_code,
                            file_path=file_path
                        ))
                        
                        logger.debug(f"Downloaded paper: {link_text}")
        
        except Exception as e:
            logger.error(f"Error scraping papers: {e}", exc_info=True)
        finally:
            # Ensure we close the driver
            try:
                if self.driver:
                    self.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")
        
        logger.info(f"Scraped {len(papers)} papers for {subject} ({exam_type})")
        return papers
