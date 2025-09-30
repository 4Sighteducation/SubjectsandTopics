"""
WJEC exam board scraper implementation.

This module provides the WJECScraper class that scrapes topic lists and exam materials
from the WJEC (Welsh Joint Education Committee) exam board website.
"""

import os
import re
import json
import time
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


class WJECScraper(BaseScraper):
    """
    Scraper for the WJEC exam board website.
    """
    
    def __init__(self, headless=True, delay=1.5, output_dir="data"):
        """
        Initialize the WJEC scraper.
        
        Args:
            headless (bool): Whether to run the browser in headless mode
            delay (float): Delay between requests in seconds
            output_dir (str): Directory to save raw scraped data
        """
        super().__init__(
            name="WJEC",
            base_url="https://www.wjec.co.uk",
            headless=headless,
            delay=delay,
            output_dir=output_dir
        )
        
        # WJEC-specific URLs
        self.qualifications_url = urljoin(self.base_url, "/qualifications/")
        self.past_papers_url = urljoin(self.base_url, "/home/past-papers/")
        
        # Map of normalized subject names to WJEC subject codes
        self.subject_code_map = {}
        
        logger.info("WJEC scraper initialized")
    
    def _get_subject_urls(self, exam_type=None):
        """
        Get URLs for all subjects based on exam type.
        
        Args:
            exam_type (str, optional): Type of exam to filter by
            
        Returns:
            dict: Dictionary mapping subject names to their URLs
        """
        logger.info(f"Getting subject URLs for WJEC" + (f" ({exam_type})" if exam_type else ""))
        
        # Normalize exam_type for consistent matching
        norm_exam_type = normalize_exam_type(exam_type) if exam_type else None
        
        # Hard-coded subject URLs for WJEC subjects
        subject_urls = {}
        
        # GCSE Subjects
        if not norm_exam_type or norm_exam_type.lower() == 'gcse':
            # Core subjects
            subject_urls["Mathematics"] = "https://www.wjec.co.uk/qualifications/mathematics-gcse"
            subject_urls["English Language"] = "https://www.wjec.co.uk/qualifications/english-language-gcse"
            subject_urls["English Literature"] = "https://www.wjec.co.uk/qualifications/english-literature-gcse"
            
            # Sciences
            subject_urls["Biology"] = "https://www.wjec.co.uk/qualifications/biology-gcse"
            subject_urls["Chemistry"] = "https://www.wjec.co.uk/qualifications/chemistry-gcse"
            subject_urls["Physics"] = "https://www.wjec.co.uk/qualifications/physics-gcse"
            subject_urls["Science (Double Award)"] = "https://www.wjec.co.uk/qualifications/science-double-award-gcse"
            subject_urls["Combined Science: Trilogy"] = "https://www.wjec.co.uk/qualifications/science-double-award-gcse"
            subject_urls["Environmental Science"] = "https://www.wjec.co.uk/qualifications/environmental-science-gcse"
            subject_urls["Astronomy"] = "https://www.wjec.co.uk/qualifications/astronomy-gcse"
            subject_urls["Geology"] = "https://www.wjec.co.uk/qualifications/geology-gcse"
            subject_urls["Statistics"] = "https://www.wjec.co.uk/qualifications/mathematics-gcse"
            
            # Humanities
            subject_urls["Religious Studies"] = "https://www.wjec.co.uk/qualifications/religious-studies-gcse"
            subject_urls["History"] = "https://www.wjec.co.uk/qualifications/history-gcse"
            subject_urls["Ancient History"] = "https://www.wjec.co.uk/qualifications/ancient-history-gcse"
            subject_urls["Geography"] = "https://www.wjec.co.uk/qualifications/geography-gcse"
            
            # Languages
            subject_urls["French"] = "https://www.wjec.co.uk/qualifications/french-gcse"
            subject_urls["Spanish"] = "https://www.wjec.co.uk/qualifications/spanish-gcse"
            subject_urls["German"] = "https://www.wjec.co.uk/qualifications/german-gcse"
            subject_urls["Welsh Second Language"] = "https://www.wjec.co.uk/qualifications/welsh-second-language-gcse"
            subject_urls["Italian"] = "https://www.wjec.co.uk/qualifications/language-pathways-itlian/#tab_keydocuments"
            subject_urls["Japanese"] = "https://www.wjec.co.uk/qualifications/language-pathways-japanese/#tab_keydocuments"
            subject_urls["Mandarin"] = "https://www.wjec.co.uk/qualifications/language-pathways-mandarin/#tab_keydocuments"
            subject_urls["Cornish"] = "https://www.wjec.co.uk/qualifications/language-pathways-cornish/#tab_keydocuments"

            
            # Creative and technical
            subject_urls["Art and Design"] = "https://www.wjec.co.uk/qualifications/art-and-design-gcse"
            subject_urls["Design and Technology"] = "https://www.wjec.co.uk/qualifications/design-and-technology-gcse"
            subject_urls["Textiles"] = "https://www.wjec.co.uk/qualifications/design-and-technology-gcse"
            subject_urls["Food and Nutrition"] = "https://www.wjec.co.uk/qualifications/food-and-nutrition-gcse"
            subject_urls["Food Preparation and Nutrition"] = "https://www.wjec.co.uk/qualifications/food-and-nutrition-gcse"
            subject_urls["Hospitality and Catering"] = "https://www.wjec.co.uk/qualifications/hospitality-and-catering-level-1-2"
            subject_urls["Music"] = "https://www.wjec.co.uk/qualifications/music-gcse"
            subject_urls["Drama"] = "https://www.wjec.co.uk/qualifications/drama-gcse"
            subject_urls["Dance"] = "https://www.wjec.co.uk/qualifications/gcse-dance-teaching-from-2026/#tab_keydocuments"
            
            # Technology and business
            subject_urls["Computer Science"] = "https://www.wjec.co.uk/qualifications/computer-science-gcse"
            subject_urls["Information and Communications Technology (ICT)"] = "https://www.wjec.co.uk/qualifications/ict-gcse"
            subject_urls["Business"] = "https://www.wjec.co.uk/qualifications/business-gcse"
            subject_urls["Economics"] = "https://www.wjec.co.uk/qualifications/economics-gcse"
            subject_urls["Engineering"] = "https://www.wjec.co.uk/qualifications/engineering-level-1-2"
            subject_urls["Electronics"] = "https://www.wjec.co.uk/qualifications/electronics-gcse"
            subject_urls["Built Environment"] = "https://www.wjec.co.uk/qualifications/gcse-built-environment/#tab_keydocuments"
            subject_urls["Construction"] = "https://www.wjec.co.uk/qualifications/constructing-the-built-environment-level-12"
            
            # Social sciences
            subject_urls["Sociology"] = "https://www.wjec.co.uk/qualifications/sociology-gcse"
            subject_urls["Psychology"] = "https://www.wjec.co.uk/qualifications/psychology-gcse"
            subject_urls["Digital Film & Media"] = "https://www.wjec.co.uk/qualifications/gcse-digital-media-and-film-teaching-from-2026/#tab_keydocuments"
            subject_urls["Film Studies"] = "https://www.wjec.co.uk/qualifications/film-studies-gcse"
            
            # Physical education and health
            subject_urls["Physical Education"] = "https://www.wjec.co.uk/qualifications/physical-education-gcse"
            subject_urls["Health and Social Care"] = "https://www.wjec.co.uk/qualifications/health-and-social-care-gcse"
            
            # Citizenship
            subject_urls["Citizenship"] = "https://www.wjec.co.uk/qualifications/citizenship-gcse"
        
        # A-Level Subjects
        if not norm_exam_type or norm_exam_type.lower() in ['a-level', 'as-level', 'gce']:
            # Mathematics
            subject_urls["Mathematics (A-Level)"] = "https://www.wjec.co.uk/qualifications/mathematics-as-a-level"
            subject_urls["Further Mathematics (A-Level)"] = "https://www.wjec.co.uk/qualifications/further-mathematics-as-a-level"
            subject_urls["Statistics (A-Level)"] = "https://www.wjec.co.uk/qualifications/mathematics-as-a-level"
            
            # English
            subject_urls["English Language (A-Level)"] = "https://www.wjec.co.uk/qualifications/english-language-as-a-level"
            subject_urls["English Literature (A-Level)"] = "https://www.wjec.co.uk/qualifications/english-literature-as-a-level"
            subject_urls["English Language and Literature (A-Level)"] = "https://www.wjec.co.uk/qualifications/english-language-and-literature-as-a-level"
            
            # Sciences
            subject_urls["Biology (A-Level)"] = "https://www.wjec.co.uk/qualifications/biology-as-a-level"
            subject_urls["Chemistry (A-Level)"] = "https://www.wjec.co.uk/qualifications/chemistry-as-a-level"
            subject_urls["Physics (A-Level)"] = "https://www.wjec.co.uk/qualifications/physics-as-a-level"
            subject_urls["Environmental Science (A-Level)"] = "https://www.wjec.co.uk/qualifications/environmental-science-as-a-level"
            subject_urls["Geology (A-Level)"] = "https://www.wjec.co.uk/qualifications/geology-as-a-level"
            
            # Humanities
            subject_urls["History (A-Level)"] = "https://www.wjec.co.uk/qualifications/history-as-a-level"
            subject_urls["Ancient History (A-Level)"] = "https://www.wjec.co.uk/qualifications/ancient-history-as-a-level"
            subject_urls["Geography (A-Level)"] = "https://www.wjec.co.uk/qualifications/geography-as-a-level"
            subject_urls["Religious Studies (A-Level)"] = "https://www.wjec.co.uk/qualifications/religious-studies-as-a-level"
            subject_urls["Philosophy (A-Level)"] = "https://www.wjec.co.uk/qualifications/philosophy-as-a-level"
            subject_urls["Classical Civilization (A-Level)"] = "https://www.wjec.co.uk/qualifications/classical-civilisation-as-a-level"
            subject_urls["Latin (A-Level)"] = "https://www.wjec.co.uk/qualifications/latin-as-a-level"
            subject_urls["Classical Greek (A-Level)"] = "https://www.wjec.co.uk/qualifications/classical-greek-as-a-level"
            subject_urls["Archaeology (A-Level)"] = "https://www.wjec.co.uk/qualifications/archaeology-as-a-level"
            
            # Languages
            subject_urls["French (A-Level)"] = "https://www.wjec.co.uk/qualifications/french-as-a-level"
            subject_urls["Spanish (A-Level)"] = "https://www.wjec.co.uk/qualifications/spanish-as-a-level"
            subject_urls["German (A-Level)"] = "https://www.wjec.co.uk/qualifications/german-as-a-level"
            subject_urls["Welsh Second Language (A-Level)"] = "https://www.wjec.co.uk/qualifications/welsh-second-language-as-a-level"
            subject_urls["Arabic (A-Level)"] = "https://www.wjec.co.uk/qualifications/arabic-as-a-level"
            subject_urls["Chinese (A-Level)"] = "https://www.wjec.co.uk/qualifications/chinese-as-a-level"
            subject_urls["Italian (A-Level)"] = "https://www.wjec.co.uk/qualifications/italian-as-a-level"
            subject_urls["Japanese (A-Level)"] = "https://www.wjec.co.uk/qualifications/japanese-as-a-level"
            subject_urls["Russian (A-Level)"] = "https://www.wjec.co.uk/qualifications/russian-as-a-level"
            subject_urls["Urdu (A-Level)"] = "https://www.wjec.co.uk/qualifications/urdu-as-a-level"
            
            # Social Sciences
            subject_urls["Psychology (A-Level)"] = "https://www.wjec.co.uk/qualifications/psychology-as-a-level"
            subject_urls["Sociology (A-Level)"] = "https://www.wjec.co.uk/qualifications/sociology-as-a-level"
            subject_urls["Economics (A-Level)"] = "https://www.wjec.co.uk/qualifications/economics-as-a-level"
            subject_urls["Business (A-Level)"] = "https://www.wjec.co.uk/qualifications/business-as-a-level"
            subject_urls["Business Studies (A-Level)"] = "https://www.wjec.co.uk/qualifications/business-as-a-level"
            subject_urls["Accounting (A-Level)"] = "https://www.wjec.co.uk/qualifications/accounting-as-a-level"
            subject_urls["Government and Politics (A-Level)"] = "https://www.wjec.co.uk/qualifications/government-and-politics-as-a-level"
            subject_urls["Law (A-Level)"] = "https://www.wjec.co.uk/qualifications/law-as-a-level"
            subject_urls["Criminology (A-Level)"] = "https://www.wjec.co.uk/qualifications/criminology-level-3"
            
            # Technology
            subject_urls["Computer Science (A-Level)"] = "https://www.wjec.co.uk/qualifications/computer-science-as-a-level"
            subject_urls["Information Technology/ICT (A-Level)"] = "https://www.wjec.co.uk/qualifications/ict-as-a-level"
            subject_urls["Design and Technology (A-Level)"] = "https://www.wjec.co.uk/qualifications/design-and-technology-as-a-level"
            subject_urls["Textiles (A-Level)"] = "https://www.wjec.co.uk/qualifications/design-and-technology-as-a-level"
            subject_urls["Electronics (A-Level)"] = "https://www.wjec.co.uk/qualifications/electronics-as-a-level"
            
            # Creative Arts
            subject_urls["Art and Design (A-Level)"] = "https://www.wjec.co.uk/qualifications/art-and-design-as-a-level"
            subject_urls["History of Art (A-Level)"] = "https://www.wjec.co.uk/qualifications/art-and-design-as-a-level"
            subject_urls["Drama and Theatre (A-Level)"] = "https://www.wjec.co.uk/qualifications/drama-and-theatre-as-a-level"
            subject_urls["Theatre Studies (A-Level)"] = "https://www.wjec.co.uk/qualifications/drama-and-theatre-as-a-level"
            subject_urls["Media Studies (A-Level)"] = "https://www.wjec.co.uk/qualifications/media-studies-as-a-level"
            subject_urls["Film Studies (A-Level)"] = "https://www.wjec.co.uk/qualifications/film-studies-as-a-level"
            subject_urls["Music (A-Level)"] = "https://www.wjec.co.uk/qualifications/music-as-a-level"
            subject_urls["Music Technology (A-Level)"] = "https://www.wjec.co.uk/qualifications/music-technology-as-a-level"
            
            # Physical Education and Health
            subject_urls["Physical Education (A-Level)"] = "https://www.wjec.co.uk/qualifications/physical-education-as-a-level"
            subject_urls["Dance (A-Level)"] = "https://www.wjec.co.uk/qualifications/dance-as-a-level"
            subject_urls["Health and Social Care (A-Level)"] = "https://www.wjec.co.uk/qualifications/health-and-social-care-as-a-level"
        
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
        html = self._get_page(subject_url, use_selenium=True)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Look for links containing "specification"
        # WJEC often uses "Specification" text for the link
        spec_links = soup.find_all('a', string=re.compile(r'specification', re.IGNORECASE))
        for link in spec_links:
            href = link.get('href', '')
            if href and href.lower().endswith('.pdf'):
                return urljoin(self.base_url, href)
        
        # If no direct text match, try looking for links with "specification" in the URL
        all_links = soup.find_all('a', href=re.compile(r'specification|spec', re.IGNORECASE))
        for link in all_links:
            href = link.get('href', '')
            if href and href.lower().endswith('.pdf'):
                return urljoin(self.base_url, href)
        
        # On WJEC site, look for resources or key documents sections
        resource_sections = soup.find_all(class_=re.compile(r'resources|documents|key-documents', re.IGNORECASE))
        for section in resource_sections:
            for link in section.find_all('a', href=True):
                href = link.get('href', '')
                text = link.text.strip()
                if ('specification' in text.lower() or 'spec' in text.lower()) and href.lower().endswith('.pdf'):
                    return urljoin(self.base_url, href)
        
        return None
    
    def _get_subject_code(self, subject_url):
        """
        Extract subject code from the subject URL or page.
        
        Args:
            subject_url (str): URL of the subject page
            
        Returns:
            str or None: Subject code
        """
        # Look for WJEC subject codes in the URL
        url_match = re.search(r'([A-Z0-9]{4,6})', subject_url)
        if url_match:
            return url_match.group(1)
        
        # Try extracting from page content
        html = self._get_page(subject_url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Look for patterns like: "Specification: C100"
        code_pattern = re.compile(r'(?:Specification|Code|Qualification code)[\s:]*([\w\d]{4,6})', re.IGNORECASE)
        
        # Search in various elements
        for element in soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'span']):
            text = element.text.strip()
            match = code_pattern.search(text)
            if match:
                return match.group(1).upper()
        
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
        
        # If specification_url is empty, jump directly to the fallback structures
        if not specification_url:
            logger.info(f"Empty specification URL provided, using fallback structure")
            
            # Special handling for Mathematics A-Level
            if (subject.lower() == "mathematics" or subject.lower() == "mathematics (a-level)") and exam_type.lower() in ["a-level", "as-level", "gce"]:
                logger.info(f"Using predefined structure for Mathematics A-Level")
                topic_structure = {
                    "Pure Mathematics": [
                        "Proof",
                        "Algebra and functions",
                        "Coordinate geometry",
                        "Sequences and series",
                        "Trigonometry",
                        "Exponentials and logarithms",
                        "Differentiation",
                        "Integration",
                        "Numerical methods",
                        "Vectors"
                    ],
                    "Statistics": [
                        "Statistical sampling",
                        "Data presentation and interpretation",
                        "Probability",
                        "Statistical distributions",
                        "Statistical hypothesis testing"
                    ],
                    "Mechanics": [
                        "Quantities and units in mechanics",
                        "Kinematics",
                        "Forces and Newton's laws",
                        "Moments",
                        "Projectiles"
                    ]
                }
                
                topics_data = []
                for module, topics in topic_structure.items():
                    for topic in topics:
                        topics_data.append(self._build_topic_data(
                            exam_board="WJEC",
                            exam_type=exam_type,
                            subject="Mathematics",
                            module=module,
                            topic=topic
                        ))
                
                logger.info(f"Generated {len(topics_data)} topics for Mathematics A-Level using predefined structure")
                return topics_data
            
            # Special handling for Further Mathematics A-Level
            elif (subject.lower() == "further mathematics" or subject.lower() == "further mathematics (a-level)") and exam_type.lower() in ["a-level", "as-level", "gce"]:
                logger.info(f"Using predefined structure for Further Mathematics A-Level")
                topic_structure = {
                    "Further Pure Mathematics": [
                        "Proof",
                        "Complex numbers",
                        "Matrices",
                        "Further algebra and functions",
                        "Further calculus",
                        "Further vectors",
                        "Polar coordinates",
                        "Hyperbolic functions",
                        "Differential equations"
                    ],
                    "Further Statistics": [
                        "Discrete random variables",
                        "Continuous random variables",
                        "Chi-squared tests",
                        "Exponential distribution",
                        "Inference",
                        "Correlation and regression"
                    ],
                    "Further Mechanics": [
                        "Momentum and impulse",
                        "Work, energy and power",
                        "Elastic collisions",
                        "Circular motion",
                        "Centres of mass",
                        "Further dynamics"
                    ],
                    "Decision Mathematics": [
                        "Algorithms and graph theory",
                        "Algorithms on graphs",
                        "Critical path analysis",
                        "Linear programming",
                        "Transportation problems",
                        "Game theory"
                    ]
                }
                
                topics_data = []
                for module, topics in topic_structure.items():
                    for topic in topics:
                        topics_data.append(self._build_topic_data(
                            exam_board="WJEC",
                            exam_type=exam_type,
                            subject="Further Mathematics",
                            module=module,
                            topic=topic
                        ))
                
                logger.info(f"Generated {len(topics_data)} topics for Further Mathematics A-Level using predefined structure")
                return topics_data
            
            # Special handling for Physics A-Level
            elif (subject.lower() == "physics" or subject.lower() == "physics (a-level)") and exam_type.lower() in ["a-level", "as-level", "gce"]:
                logger.info(f"Using predefined structure for Physics A-Level")
                topic_structure = {
                    "Fundamental Principles of Physics": [
                        "Physical quantities and units",
                        "Measurements and uncertainties",
                        "Scalars and vectors",
                        "Dimensional analysis",
                        "Estimation of physical quantities"
                    ],
                    "Mechanics and Properties of Matter": [
                        "Kinematics",
                        "Dynamics and forces",
                        "Work, energy and power",
                        "Momentum and impulse",
                        "Circular motion",
                        "Elasticity",
                        "Fluids and fluid dynamics"
                    ],
                    "Waves and Oscillations": [
                        "Simple harmonic motion",
                        "Wave properties",
                        "Superposition of waves",
                        "Standing waves",
                        "Doppler effect",
                        "Interference and diffraction"
                    ],
                    "Electricity and Magnetism": [
                        "Electric fields",
                        "Capacitance",
                        "Current and resistance",
                        "DC circuits",
                        "Magnetic fields",
                        "Electromagnetic induction",
                        "AC theory"
                    ],
                    "Thermal Physics and Matter": [
                        "Thermal concepts",
                        "Ideal gases",
                        "Thermodynamics",
                        "Heat transfer",
                        "Specific heat capacity",
                        "Phase changes"
                    ],
                    "Nuclear and Particle Physics": [
                        "Atomic structure",
                        "Nuclear physics",
                        "Radioactivity",
                        "Particle physics",
                        "Quantum phenomena",
                        "Nuclear energy"
                    ],
                    "Astrophysics and Cosmology": [
                        "Stellar evolution",
                        "Cosmology",
                        "The expanding universe",
                        "Astronomical measurements",
                        "Space exploration"
                    ]
                }
                
                topics_data = []
                for module, topics in topic_structure.items():
                    for topic in topics:
                        topics_data.append(self._build_topic_data(
                            exam_board="WJEC",
                            exam_type=exam_type,
                            subject="Physics",
                            module=module,
                            topic=topic
                        ))
                
                logger.info(f"Generated {len(topics_data)} topics for Physics A-Level using predefined structure")
                return topics_data
                
            # If no specific fallback is available, return empty list
            logger.warning(f"No fallback available for {subject} ({exam_type}) with empty specification URL")
            return []
        
        # For PDFs, download the file and use PDF extraction
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
                return []
            
            # Try AI-assisted extraction if available
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
            
            # Otherwise, return an empty list (PDF extraction without AI is difficult)
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
        
        # Check directly if this is Chemistry GCSE and prioritize its special handling
        if subject.lower() == "chemistry" and exam_type.lower() == "gcse":
            # GCSE Chemistry topics for WJEC (based on their specification structure)
            logger.info(f"Using predefined structure for Chemistry GCSE")
            topic_structure = {
                "Chemical substances, reactions and essential resources": [
                    "The nature of substances and chemical reactions",
                    "Atomic structure and the Periodic Table",
                    "Water",
                    "The ever-changing Earth",
                    "Rate of chemical change"
                ],
                "Chemical bonding, application of chemical reactions and organic chemistry": [
                    "Bonding, structure and properties",
                    "Acids, bases and salts",
                    "Metals and their extraction",
                    "Chemical reactions and energy",
                    "Crude oil, fuels and organic chemistry"
                ],
                "Chemical and spectroscopic analysis": [
                    "The Periodic Table and properties of elements",
                    "Chemical formulae, equations and amount of substance",
                    "Identification of ions and gases",
                    "Analysis and detection of substances"
                ],
                "Chemical production and environmental considerations": [
                    "The production of chemicals and materials",
                    "Environmental considerations and sustainability",
                    "Industrial processes and equilibrium"
                ],
                "Organic chemistry and chemical synthesis": [
                    "Alcohols and carboxylic acids",
                    "Mass spectra and IR", 
                    "Reversible reactions, industrial processes and important chemicals"
                ]
            }
            
            topics_data = []
            for module, topics in topic_structure.items():
                for topic in topics:
                    topics_data.append(self._build_topic_data(
                        exam_board="WJEC",
                        exam_type=exam_type,
                        subject=subject,
                        module=module,
                        topic=topic
                    ))
            
            logger.info(f"Generated {len(topics_data)} topics for Chemistry GCSE using predefined structure")
            return topics_data
            
        # Special case handling for Mathematics GCSE 
        elif subject.lower() == "mathematics" and exam_type.lower() == "gcse":
            # GCSE Mathematics topics for WJEC (based on their specification structure)
            logger.info(f"Using predefined structure for Mathematics GCSE")
            topic_structure = {
                "Number": [
                    "Structure and calculation",
                    "Fractions, decimals and percentages",
                    "Measures and accuracy"
                ],
                "Algebra": [
                    "Expressions and equations",
                    "Graphs",
                    "Sequences",
                    "Functions"
                ],
                "Ratio, proportion and rates of change": [
                    "Ratio and proportion",
                    "Percentages and interest",
                    "Growth and decay"
                ],
                "Geometry and measures": [
                    "Properties and constructions",
                    "Coordinates and transformations",
                    "Mensuration",
                    "Vectors"
                ],
                "Probability": [
                    "Calculating probabilities",
                    "Experimental probability",
                    "Probability distributions"
                ],
                "Statistics": [
                    "Data collection and sampling",
                    "Data representation",
                    "Central tendency and spread"
                ]
            }
            
            topics_data = []
            for module, topics in topic_structure.items():
                for topic in topics:
                    topics_data.append(self._build_topic_data(
                        exam_board="WJEC",
                        exam_type=exam_type,
                        subject=subject,
                        module=module,
                        topic=topic
                    ))
            
            logger.info(f"Generated {len(topics_data)} topics for Mathematics GCSE using predefined structure")
            return topics_data
        
        # Special case handling for Mathematics A-Level
        elif (subject.lower() == "mathematics" or subject.lower() == "mathematics (a-level)") and exam_type.lower() in ["a-level", "as-level", "gce"]:
            logger.info(f"Using predefined structure for Mathematics A-Level")
            topic_structure = {
                "Pure Mathematics": [
                    "Proof",
                    "Algebra and functions",
                    "Coordinate geometry",
                    "Sequences and series",
                    "Trigonometry",
                    "Exponentials and logarithms",
                    "Differentiation",
                    "Integration",
                    "Numerical methods",
                    "Vectors"
                ],
                "Statistics": [
                    "Statistical sampling",
                    "Data presentation and interpretation",
                    "Probability",
                    "Statistical distributions",
                    "Statistical hypothesis testing"
                ],
                "Mechanics": [
                    "Quantities and units in mechanics",
                    "Kinematics",
                    "Forces and Newton's laws",
                    "Moments",
                    "Projectiles"
                ]
            }
            
            topics_data = []
            for module, topics in topic_structure.items():
                for topic in topics:
                    topics_data.append(self._build_topic_data(
                        exam_board="WJEC",
                        exam_type=exam_type,
                        subject="Mathematics",
                        module=module,
                        topic=topic
                    ))
            
            logger.info(f"Generated {len(topics_data)} topics for Mathematics A-Level using predefined structure")
            return topics_data
        
        # Special case handling for Further Mathematics A-Level
        elif (subject.lower() == "further mathematics" or subject.lower() == "further mathematics (a-level)") and exam_type.lower() in ["a-level", "as-level", "gce"]:
            logger.info(f"Using predefined structure for Further Mathematics A-Level")
            topic_structure = {
                "Further Pure Mathematics": [
                    "Proof",
                    "Complex numbers",
                    "Matrices",
                    "Further algebra and functions",
                    "Further calculus",
                    "Further vectors",
                    "Polar coordinates",
                    "Hyperbolic functions",
                    "Differential equations"
                ],
                "Further Statistics": [
                    "Discrete random variables",
                    "Continuous random variables",
                    "Chi-squared tests",
                    "Exponential distribution",
                    "Inference",
                    "Correlation and regression"
                ],
                "Further Mechanics": [
                    "Momentum and impulse",
                    "Work, energy and power",
                    "Elastic collisions",
                    "Circular motion",
                    "Centres of mass",
                    "Further dynamics"
                ],
                "Decision Mathematics": [
                    "Algorithms and graph theory",
                    "Algorithms on graphs",
                    "Critical path analysis",
                    "Linear programming",
                    "Transportation problems",
                    "Game theory"
                ]
            }
            
            topics_data = []
            for module, topics in topic_structure.items():
                for topic in topics:
                    topics_data.append(self._build_topic_data(
                        exam_board="WJEC",
                        exam_type=exam_type,
                        subject="Further Mathematics",
                        module=module,
                        topic=topic
                    ))
            
            logger.info(f"Generated {len(topics_data)} topics for Further Mathematics A-Level using predefined structure")
            return topics_data
        
        # Special case handling for Physics A-Level
        elif (subject.lower() == "physics" or subject.lower() == "physics (a-level)") and exam_type.lower() in ["a-level", "as-level", "gce"]:
            logger.info(f"Using predefined structure for Physics A-Level")
            topic_structure = {
                "Fundamental Principles of Physics": [
                    "Physical quantities and units",
                    "Measurements and uncertainties",
                    "Scalars and vectors",
                    "Dimensional analysis",
                    "Estimation of physical quantities"
                ],
                "Mechanics and Properties of Matter": [
                    "Kinematics",
                    "Dynamics and forces",
                    "Work, energy and power",
                    "Momentum and impulse",
                    "Circular motion",
                    "Elasticity",
                    "Fluids and fluid dynamics"
                ],
                "Waves and Oscillations": [
                    "Simple harmonic motion",
                    "Wave properties",
                    "Superposition of waves",
                    "Standing waves",
                    "Doppler effect",
                    "Interference and diffraction"
                ],
                "Electricity and Magnetism": [
                    "Electric fields",
                    "Capacitance",
                    "Current and resistance",
                    "DC circuits",
                    "Magnetic fields",
                    "Electromagnetic induction",
                    "AC theory"
                ],
                "Thermal Physics and Matter": [
                    "Thermal concepts",
                    "Ideal gases",
                    "Thermodynamics",
                    "Heat transfer",
                    "Specific heat capacity",
                    "Phase changes"
                ],
                "Nuclear and Particle Physics": [
                    "Atomic structure",
                    "Nuclear physics",
                    "Radioactivity",
                    "Particle physics",
                    "Quantum phenomena",
                    "Nuclear energy"
                ],
                "Astrophysics and Cosmology": [
                    "Stellar evolution",
                    "Cosmology",
                    "The expanding universe",
                    "Astronomical measurements",
                    "Space exploration"
                ]
            }
            
            topics_data = []
            for module, topics in topic_structure.items():
                for topic in topics:
                    topics_data.append(self._build_topic_data(
                        exam_board="WJEC",
                        exam_type=exam_type,
                        subject="Physics",
                        module=module,
                        topic=topic
                    ))
            
            logger.info(f"Generated {len(topics_data)} topics for Physics A-Level using predefined structure")
            return topics_data
        
        # Fallback to conventional extraction methods
        logger.warning(f"No topic extraction method available for {subject}. Using AI extraction is recommended.")
        return []
    
    def scrape_topics(self, subject=None, exam_type=None):
        """
        Scrape topic lists from the WJEC website.
        
        Args:
            subject (str, optional): Subject to scrape topics for
            exam_type (str, optional): Exam type to scrape topics for
            
        Returns:
            list: List of topic data dictionaries
        """
        logger.info(f"Scraping WJEC topics" + 
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
                # Special handling for known problematic subjects - directly use fallback structures
                current_exam_type = exam_type or "GCSE" if "gcse" in subj_url.lower() else "A-Level"
                
                # Check if this is one of our special case subjects
                if ((subj_name.lower() == "mathematics" or subj_name.lower() == "mathematics (a-level)") and 
                    current_exam_type.lower() in ["a-level", "as-level", "gce"]):
                    logger.info(f"Using direct fallback for Mathematics A-Level")
                    topics = self._extract_specification_topics(
                        "", # No spec URL needed for direct fallback
                        current_exam_type,
                        "Mathematics"
                    )
                
                elif ((subj_name.lower() == "further mathematics" or subj_name.lower() == "further mathematics (a-level)") and 
                      current_exam_type.lower() in ["a-level", "as-level", "gce"]):
                    logger.info(f"Using direct fallback for Further Mathematics A-Level")
                    topics = self._extract_specification_topics(
                        "", # No spec URL needed for direct fallback
                        current_exam_type,
                        "Further Mathematics"
                    )
                
                elif ((subj_name.lower() == "physics" or subj_name.lower() == "physics (a-level)") and 
                      current_exam_type.lower() in ["a-level", "as-level", "gce"]):
                    # Try normal process first, but ensure fallback if that fails
                    spec_url = self._get_spec_url_from_subject_page(subj_url)
                    if not spec_url:
                        logger.warning(f"Could not find specification URL for {subj_name}, using fallback")
                        topics = self._extract_specification_topics(
                            "", # No spec URL needed for direct fallback
                            current_exam_type,
                            "Physics"
                        )
                    else:
                        topics = self._extract_specification_topics(
                            spec_url,
                            current_exam_type,
                            subj_name
                        )
                
                else:
                    # For all other subjects, use the normal process
                    # Get the specification URL
                    spec_url = self._get_spec_url_from_subject_page(subj_url)
                    if not spec_url:
                        logger.warning(f"Could not find specification URL for {subj_name}")
                        continue
                    
                    # Extract topics from specification
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
        
        logger.info(f"Scraped {len(all_topics)} topics from WJEC")
        return all_topics
    
    def scrape_papers(self, subject=None, exam_type=None, year_from=2021):
        """
        Scrape exam papers from the WJEC website.
        
        Args:
            subject (str, optional): Subject to scrape papers for
            exam_type (str, optional): Exam type to scrape papers for
            year_from (int): Year to start scraping papers from
            
        Returns:
            list: List of paper data dictionaries
        """
        logger.info(f"Scraping WJEC papers" + 
                   (f" for {subject}" if subject else "") + 
                   (f" ({exam_type})" if exam_type else "") +
                   f" from {year_from}")
        
        if not subject or not exam_type:
            logger.warning("Both subject and exam_type are required for WJEC scraper")
            return []
        
        # Normalize inputs
        normalized_subject = normalize_subject_name(subject)
        normalized_exam_type = normalize_exam_type(exam_type)
        
        # Use Selenium to navigate the past papers section
        self._init_driver()
        papers = []
        
        try:
            # Go to the past papers page
            self.driver.get(self.past_papers_url)
            
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select, input, button"))
            )
            
            # Select the appropriate exam type
            exam_select = None
            try:
                exam_select = Select(self.driver.find_element(By.ID, "QualificationType"))
                # Map exam_type to option value
                exam_option = ""
                if normalized_exam_type.lower() == "gcse":
                    exam_option = "GCSE"
                elif normalized_exam_type.lower() in ["a-level", "as-level", "gce"]:
                    exam_option = "GCE AS/A LEVEL"
                
                if exam_option:
                    # Find option by visible text
                    for option in exam_select.options:
                        if exam_option in option.text:
                            exam_select.select_by_visible_text(option.text)
                            break
            except Exception as e:
                logger.warning(f"Could not select exam type: {e}")
            
            # Wait for subject options to load (if exam_select was changed)
            if exam_select:
                time.sleep(2)
            
            # Select the subject
            subject_select = None
            try:
                subject_select = Select(self.driver.find_element(By.ID, "Subject"))
                
                # Try to match the subject
                for option in subject_select.options:
                    if normalized_subject.lower() in option.text.lower():
                        subject_select.select_by_visible_text(option.text)
                        break
            except Exception as e:
                logger.warning(f"Could not select subject: {e}")
            
            # Click search button
            try:
                search_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                search_button.click()
                
                # Wait for results
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".results-container, .no-results"))
                )
            except Exception as e:
                logger.warning(f"Could not submit search: {e}")
            
            # Get the page source and parse it
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'lxml')
            
            # Find the results
            results_container = soup.select_one('.results-container, .past-papers-results')
            if not results_container:
                logger.warning(f"No results found for {subject} {exam_type}")
                return []
            
            # Process the results
            paper_links = []
            
            # Find all paper links
            for link in results_container.select('a[href$=".pdf"]'):
                href = link.get('href', '')
                if not href:
                    continue
                
                text = link.text.strip()
                
                # Skip if doesn't seem like a paper
                if not text or len(text) < 5:
                    continue
                
                # Check if it's from the desired year
                year_match = re.search(r'(20\d\d)', text)
                year = int(year_match.group(1)) if year_match else None
                
                if year and year >= year_from:
                    # Determine document type
                    doc_type = "Question Paper"
                    if any(marker in text.lower() for marker in ["mark scheme", "marking", "ms"]):
                        doc_type = "Mark Scheme"
                    elif any(marker in text.lower() for marker in ["examiner", "report", "er"]):
                        doc_type = "Examiner Report"
                    
                    # Determine season
                    season = "Summer"
                    if any(marker in text.lower() for marker in ["january", "winter", "november"]):
                        season = "Winter"
                    
                    # Extract paper number
                    paper_num_match = re.search(r'paper\s*(\d+)', text.lower())
                    paper_number = int(paper_num_match.group(1)) if paper_num_match else 1
                    
                    # Get subject code if possible
                    subject_code = ""
                    code_match = re.search(r'([A-Z0-9]{4,6})', text)
                    if code_match:
                        subject_code = code_match.group(1)
                    
                    # Add to paper links
                    paper_links.append({
                        "url": urljoin(self.base_url, href),
                        "text": text,
                        "year": year,
                        "season": season,
                        "document_type": doc_type,
                        "paper_number": paper_number,
                        "subject_code": subject_code
                    })
            
            # Download each paper and create data dictionary
            for paper_data in paper_links:
                # Construct filename
                filename_parts = []
                if paper_data["subject_code"]:
                    filename_parts.append(paper_data["subject_code"])
                else:
                    filename_parts.append(normalized_subject.replace(" ", "_"))
                
                filename_parts.append(str(paper_data["year"]))
                filename_parts.append(paper_data["season"])
                filename_parts.append(f"Paper{paper_data['paper_number']}")
                
                if paper_data["document_type"] == "Mark Scheme":
                    filename_parts.append("MS")
                elif paper_data["document_type"] == "Examiner Report":
                    filename_parts.append("ER")
                
                filename = "_".join(filename_parts)
                
                # Create subdirectory path
                subdir = os.path.join(
                    normalized_exam_type,
                    normalized_subject,
                    str(paper_data["year"]),
                    paper_data["season"]
                )
                
                # Determine document type for directory structure
                document_type = paper_data["document_type"].lower().replace(" ", "_")
                
                # Download the paper
                file_path = self._download_document(
                    paper_data["url"], 
                    filename, 
                    subdir, 
                    document_type
                )
                
                if file_path:
                    # Create paper data dictionary
                    papers.append(self._build_paper_data(
                        exam_board="WJEC",
                        exam_type=normalized_exam_type,
                        subject=normalized_subject,
                        year=paper_data["year"],
                        season=paper_data["season"],
                        title=paper_data["text"],
                        paper_number=paper_data["paper_number"],
                        document_type=paper_data["document_type"],
                        specification_code=paper_data["subject_code"],
                        file_path=file_path
                    ))
                    
                    logger.debug(f"Downloaded paper: {paper_data['text']}")
            
        except Exception as e:
            logger.error(f"Error scraping papers: {e}", exc_info=True)
        
        logger.info(f"Scraped {len(papers)} papers for {subject} ({exam_type})")
        return papers
