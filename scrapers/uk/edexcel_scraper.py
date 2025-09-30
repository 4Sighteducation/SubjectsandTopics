"""
Edexcel/Pearson exam board scraper implementation.

This module provides the EdexcelScraper class that scrapes topic lists and exam materials
from the Edexcel (Pearson) exam board website.
"""

import os
import re
import json
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from urllib.parse import urljoin

from scrapers.base_scraper import BaseScraper
from utils.logger import get_logger
from utils.helpers import (
    sanitize_text, normalize_subject_name, normalize_exam_type, 
    extract_tables_from_html, ensure_directory
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


class EdexcelScraper(BaseScraper):
    """
    Scraper for the Edexcel/Pearson exam board website.
    """
    
    def __init__(self, headless=True, delay=1.5):
        """
        Initialize the Edexcel scraper.
        
        Args:
            headless (bool): Whether to run the browser in headless mode
            delay (float): Delay between requests in seconds
        """
        super().__init__(
            name="Edexcel",
            base_url="https://qualifications.pearson.com",
            headless=headless,
            delay=delay
        )
        
        # Edexcel-specific URLs
        self.qualifications_url = urljoin(self.base_url, "/en/subjects")
        self.past_papers_url = urljoin(self.base_url, "/en/support/support-topics/exams/past-papers.html")
        
        # Map of normalized subject names to Edexcel subject codes
        self.subject_code_map = {}
        
        logger.info("Edexcel scraper initialized")
    
    def _get_subject_urls(self, exam_type=None):
        """
        Get URLs for all subjects based on exam type.
        
        Args:
            exam_type (str, optional): Type of exam to filter by
            
        Returns:
            dict: Dictionary mapping subject names to their URLs
        """
        logger.info(f"Getting subject URLs for Edexcel" + (f" ({exam_type})" if exam_type else ""))
        
        # Normalize exam_type for consistent matching
        norm_exam_type = normalize_exam_type(exam_type) if exam_type else None
        
        # Hard-coded subject URLs for Edexcel subjects
        subject_urls = {}
        
        # GCSE Subjects
        if not norm_exam_type or norm_exam_type.lower() == 'gcse':
            # Core subjects
            subject_urls["Mathematics"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/mathematics-2015.html"
            subject_urls["Mathematics-Resit"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/mathematics-2015-9-1-post-16-resits.html"
            subject_urls["Statistics"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/statistics-2017.html"
            subject_urls["English Language"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/english-language-2015.html"
            subject_urls["English Literature"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/english-literature-2015.html"
            
            # Sciences
            subject_urls["Biology"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/sciences-2016.html#%2Ftab-Biology"
            subject_urls["Chemistry"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/sciences-2016.html#%2Ftab-Chemistry"
            subject_urls["Physics"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/sciences-2016.html#%2Ftab-Physics"
            subject_urls["Combined Science"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/sciences-2016.html#%2Ftab-CombinedSciencefrom2016"
            subject_urls["Combined Science: Trilogy"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/sciences-2016.html#%2Ftab-CombinedSciencefrom2016"
            subject_urls["Environmental Science"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/environmental-science-2016.html"
            subject_urls["Astronomy"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/astronomy-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Geology"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/geology-2017.html"
            subject_urls["Statistics"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/statistics-2017.html"
            
            # Humanities
            subject_urls["Religious Studies A"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/religious-studies-a-2016.html"
            subject_urls["Religious Studies B"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/religious-studies-b-2016.html"
            subject_urls["Geography"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/geography-a-2016.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["History"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/history-2016.html"
            subject_urls["Ancient History"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/ancient-history-2017.html"
            
            # Languages
            subject_urls["French"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/french-2024.html"
            subject_urls["Spanish"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/spanish-2024.html"
            subject_urls["German"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/german-2024.html"
            subject_urls["Arabic"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/arabic-2017.html"
            subject_urls["Chinese"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/chinese-2017.html"
            subject_urls["Italian"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/italian-2017.html"
            subject_urls["Japanese"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/japanese-2017.html"
            subject_urls["Portuguese"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/portuguese-2018.html"
            subject_urls["Persian"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/persian-2018.html"
            subject_urls["Russian"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/russian-2017.html"
            subject_urls["Urdu"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/urdu-2017.coursematerials.html"
            subject_urls["Greek"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/greek-2017.coursematerials.html"
            subject_urls["Turkish"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/turkish-2018.coursematerials.html"
            subject_urls["Biblical Hebrew"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/biblical-hebrew-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Biblical Gujarati"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/gujarati-2018.coursematerials.html"

            # Creative and technical
            subject_urls["Art and Design"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/art-and-design-2016.coursematerials.html"
            subject_urls["Design and Technology"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/design-and-technology-9-1-from-2017.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Textiles"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/art-and-design-2016.coursematerials.html"
            subject_urls["Food Preparation and Nutrition"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/food-preparation-and-nutrition-2016.coursematerials.html"
            subject_urls["Hospitality and Catering"] = "https://qualifications.pearson.com/en/qualifications/btec-firsts/hospitality.coursematerials.html"
            subject_urls["Music"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/music-2016.coursematerials.html"
            subject_urls["Drama"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/drama-2016.coursematerials.html"
            subject_urls["Dance"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/dance-2016.coursematerials.html"
            
            # Technology and business
            subject_urls["Computer Science"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/computer-science-2020.coursematerials.html"
            subject_urls["Business"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/business-2017.coursematerials.html"
            
            # Social sciences
            subject_urls["Citizenship Studies"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/citizenship-studies-2016.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Psychology"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/psychology-2017.coursematerials.html"
            subject_urls["Sociology"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/sociology-2017.coursematerials.html"
            subject_urls["Media Studies"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/media-studies-2017.coursematerials.html"
            subject_urls["Film Studies"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/film-studies-2017.coursematerials.html"
            
            # Physical education and health
            subject_urls["Physical Education"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/physical-education-2016.coursematerials.html"
            subject_urls["Health and Social Care"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/health-and-social-care-2009.coursematerials.html"
        
        # A-Level Subjects
        if not norm_exam_type or norm_exam_type.lower() in ['a-level', 'as-level']:
            # Mathematics
            subject_urls["Mathematics (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/mathematics-2017.coursematerials.html"
            subject_urls["Mathematics - Advanced Extension (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/advanced-extension-award-mathematics-2018.coursematerials.html"
            subject_urls["Statistics (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/statistics-2017.coursematerials.html"
    
            
            # English
            subject_urls["English Language (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/english-language-2015.coursematerials.html"
            subject_urls["English Literature (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/english-literature-2015.coursematerials.html"
            subject_urls["English Language and Literature (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/english-language-and-literature-2015.coursematerials.html"
            
            # Sciences
            subject_urls["Biology A (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/biology-a-2015.coursematerials.html"
            subject_urls["Biology B (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/biology-b-2015.coursematerials.html"
            subject_urls["Chemistry (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/chemistry-2015.coursematerials.html"
            subject_urls["Physics (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/physics-2015.coursematerials.html"
            
            # Humanities
            subject_urls["History (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/history-2015.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Geography A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/geography-a-2016.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Religious Studies (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/religious-studies-2016.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            
            # Languages
            subject_urls["Arabic (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/arabic-2018.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Chinese (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/chinese-2017.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["French (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/french-2016.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["German (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/german-2016.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Greek (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/greek-2018.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Gujarati (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/gujarati-2018.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Italian (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/italian-2017.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Japanese (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/japanese-2018.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Persian (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/persian-2018.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Portuguese (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/portuguese-2018.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Russian (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/russian-2017.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Spanish (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/spanish-2016.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Turkish (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/turkish-2018.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Urdu (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/urdu-2018.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Chinese (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/chinese-2017.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            
            # Social Sciences
            subject_urls["Psychology (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/psychology-2015.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Economics (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/economics-a-2015.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Business (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/business-2015.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments" 
            subject_urls["Business Studies (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/business-studies-2000.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Accounting (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/accounting-2000.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"

            # Technology
            subject_urls["Information Technology/ICT (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/btec-nationals/information-technology-2016.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Design and Technology (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-gcses/design-and-technology-9-1-from-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FSpecification-and-sample-assessments"
            # Creative Arts
            subject_urls["Art and Design (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/art-and-design-2015.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Drama and Theatre (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/drama-and-theatre-2016.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Music (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/music-2016.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["Music Technology (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/music-technology-2017.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["History of Art (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/history-of-art-2017.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
            subject_urls["General Studies (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/history-of-art-2017.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"

            # Physical Education and Health
            subject_urls["Physical Education (A-Level)"] = "https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/physical-education-2016.coursematerials.html#filterQuery=category:Pearson-UK:Category%2FSpecification-and-sample-assessments"
        
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
        
        # For Edexcel, specification links are often found in the "Course Materials" tab
        # First check for any link containing "specification"
        spec_links = soup.find_all('a', href=True, string=re.compile('specification', re.IGNORECASE))
        
        # Also check for links that have 'specification' in the href
        spec_links.extend(soup.find_all('a', href=re.compile('specification', re.IGNORECASE)))
        
        if spec_links:
            # Prioritize PDF links
            pdf_links = [link for link in spec_links if link['href'].lower().endswith('.pdf')]
            if pdf_links:
                return urljoin(self.base_url, pdf_links[0]['href'])
            # Otherwise use the first link found
            return urljoin(self.base_url, spec_links[0]['href'])
        
        # Edexcel often has the following structure: "Course Materials" tab -> "Specification" link
        # Look for tabs and course materials sections
        for tab in soup.find_all('a', attrs={'role': 'tab'}):
            if 'course' in tab.text.lower() or 'material' in tab.text.lower():
                # Try getting the tab's content
                tab_id = tab.get('href', '').replace('#', '')
                tab_content = soup.find('div', id=tab_id)
                
                if tab_content:
                    # Look for specification links in this tab content
                    for link in tab_content.find_all('a', href=True):
                        if 'specification' in link.text.lower() or 'specification' in link['href'].lower():
                            return urljoin(self.base_url, link['href'])
        
        # If still not found, try checking for downloads or resources sections
        download_sections = soup.find_all(class_=re.compile('download|resource', re.IGNORECASE))
        for section in download_sections:
            for link in section.find_all('a', href=True):
                if 'specification' in link.text.lower() or 'specification' in link['href'].lower():
                    return urljoin(self.base_url, link['href'])
        
        return None
    
    def _get_subject_code(self, subject_url):
        """
        Extract subject code from the subject URL or page.
        
        Args:
            subject_url (str): URL of the subject page
            
        Returns:
            str or None: Subject code
        """
        # Edexcel codes are often at the end of URLs or in the form: 1MA0, 9MA0, etc.
        url_match = re.search(r'([1-9][A-Z]{2}[0-9])', subject_url)
        if url_match:
            return url_match.group(1)
        
        # Try to find from page content
        html = self._get_page(subject_url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Look for patterns like: Specification code: 1MA0
        code_pattern = re.compile(r'\b([1-9][A-Z]{2}[0-9])\b')
        
        # Check for specification codes in text
        for element in soup.find_all(string=re.compile('code|specif', re.IGNORECASE)):
            match = code_pattern.search(element)
            if match:
                return match.group(1)
        
        # Check headings and paragraphs for codes
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'p']):
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
            # GCSE Mathematics main topics and subtopics based on Edexcel specification
            topic_structure = {
                "Number": [
                    "Number operations",
                    "Fractions, decimals and percentages",
                    "Measures and accuracy",
                    "Factors, multiples and primes"
                ],
                "Algebra": [
                    "Expressions",
                    "Solving equations and inequalities",
                    "Graphs",
                    "Sequences"
                ],
                "Ratio, proportion and rates of change": [
                    "Ratio",
                    "Proportion",
                    "Percentages",
                    "Compound measures"
                ],
                "Geometry and measures": [
                    "Properties of shapes and solids",
                    "Mensuration",
                    "Angles and trigonometry",
                    "Vectors"
                ],
                "Probability": [
                    "Probability",
                    "Set notation"
                ],
                "Statistics": [
                    "Data collection",
                    "Data representation",
                    "Data interpretation"
                ]
            }
            
            for module, topics in topic_structure.items():
                for topic in topics:
                    topics_data.append(self._build_topic_data(
                        exam_board="Edexcel",
                        exam_type=exam_type,
                        subject=subject,
                        module=module,
                        topic=topic
                    ))
            
            logger.info(f"Generated {len(topics_data)} topics for Mathematics GCSE using predefined structure")
            return topics_data
        
        # General approach for tables
        tables = extract_tables_from_html(html)
        if tables:
            current_module = "General"
            
            for table in tables:
                # For each table, try to identify if it's a topic list
                if len(table) > 2:  # Skip tiny tables
                    # Check if first row looks like a header
                    if any('topic' in cell.lower() for cell in table[0]):
                        for row in table[1:]:
                            if len(row) >= 2:
                                # Use first column as topic and second as subtopic
                                topic = sanitize_text(row[0])
                                subtopic = sanitize_text(row[1]) if len(row) > 1 else None
                                
                                if topic and len(topic) > 2:
                                    topics_data.append(self._build_topic_data(
                                        exam_board="Edexcel",
                                        exam_type=exam_type,
                                        subject=subject,
                                        module=current_module,
                                        topic=topic,
                                        sub_topic=subtopic
                                    ))
        
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
                        exam_board="Edexcel",
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
                            exam_board="Edexcel",
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
                            exam_board="Edexcel",
                            exam_type=exam_type,
                            subject=subject,
                            module=current_module,
                            topic=current_topic
                        ))
        
        logger.info(f"Extracted {len(topics_data)} topics from specification")
        return topics_data
    
    def scrape_topics(self, subject=None, exam_type=None):
        """
        Scrape topic lists from the Edexcel website.
        
        Args:
            subject (str, optional): Subject to scrape topics for
            exam_type (str, optional): Exam type to scrape topics for
            
        Returns:
            list: List of topic data dictionaries
        """
        logger.info(f"Scraping Edexcel topics" + 
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
        
        logger.info(f"Scraped {len(all_topics)} topics from Edexcel")
        return all_topics
    
    def scrape_papers(self, subject=None, exam_type=None, year_from=2021):
        """
        Scrape exam papers from the Edexcel website.
        
        Args:
            subject (str, optional): Subject to scrape papers for
            exam_type (str, optional): Exam type to scrape papers for
            year_from (int): Year to start scraping papers from
            
        Returns:
            list: List of paper data dictionaries
        """
        logger.info(f"Scraping Edexcel papers" + 
                   (f" for {subject}" if subject else "") + 
                   (f" ({exam_type})" if exam_type else "") +
                   f" from {year_from}")
        
        # Get normalized inputs
        normalized_subject = normalize_subject_name(subject) if subject else None
        normalized_exam_type = normalize_exam_type(exam_type) if exam_type else None
        
        # Edexcel's past papers site structure
        papers_url = "https://qualifications.pearson.com/en/support/support-topics/exams/past-papers.html"
        
        # Navigate to the past papers page
        self._init_driver()
        papers = []
        
        try:
            # Go to the past papers page
            logger.info(f"Navigating to past papers page: {papers_url}")
            self.driver.get(papers_url)
            time.sleep(2)  # Give time for the page to load
            
            # Using a more direct approach similar to AQA and OCR
            # Instead of trying to navigate through complex forms
            
            # Direct URL to search results for a specific subject and qualification
            # Format: /en/qualifications/[exam-type]/[subject-name]/past-papers.html
            
            # Try to construct a direct URL for past papers based on subject and exam type
            direct_url = None
            if subject and exam_type:
                # Map normalized exam type to Edexcel URL component
                exam_type_map = {
                    "gcse": "gcse",
                    "a-level": "as-a-level"
                }
                
                # Get exam type URL part
                exam_type_url = exam_type_map.get(normalized_exam_type.lower(), "")
                
                if exam_type_url:
                    # Try to map subject to URL-friendly format
                    subject_url = normalized_subject.lower().replace(" ", "-")
                    
                    # Construct direct URL
                    direct_url = f"https://qualifications.pearson.com/en/qualifications/{exam_type_url}/{subject_url}/past-papers-and-mark-schemes.html"
                    
                    logger.info(f"Trying direct URL: {direct_url}")
                    
                    # Navigate to the direct URL
                    self.driver.get(direct_url)
                    time.sleep(3)
            
            # If direct URL doesn't work or isn't available, use a search approach
            if not direct_url or "404" in self.driver.current_url:
                logger.info("Direct URL not available, trying search approach")
                
                # Navigate back to papers page
                self.driver.get(papers_url)
                time.sleep(2)
                
                # Look for search form or links to past papers
                try:
                    # Try to find and click "Past papers and mark schemes" link
                    past_papers_links = self.driver.find_elements(By.PARTIAL_LINK_TEXT, "Past papers")
                    if past_papers_links:
                        past_papers_links[0].click()
                        time.sleep(2)
                except Exception as e:
                    logger.warning(f"Error finding past papers link: {e}")
            
            # Now search for PDF links on the current page
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'lxml')
            
            # Find all PDF links
            pdf_links = soup.find_all('a', href=lambda href: href and href.lower().endswith('.pdf'))
            
            # If no PDFs found, try to navigate to a page that might have PDFs
            if not pdf_links:
                logger.warning("No PDF links found on current page, searching for resource links")
                
                # Look for links that might lead to resources
                resource_links = []
                for link in self.driver.find_elements(By.TAG_NAME, 'a'):
                    link_text = link.text.lower()
                    if any(term in link_text for term in ['resource', 'past paper', 'assessment', 'exam']):
                        resource_links.append(link)
                
                # Click on the first promising link
                if resource_links:
                    resource_links[0].click()
                    time.sleep(2)
                    
                    # Get updated page
                    html = self.driver.page_source
                    soup = BeautifulSoup(html, 'lxml')
                    pdf_links = soup.find_all('a', href=lambda href: href and href.lower().endswith('.pdf'))
            
            # Filter and process PDF links
            if pdf_links:
                logger.info(f"Found {len(pdf_links)} PDF links, filtering for {subject} ({exam_type})")
                
                for link in pdf_links:
                    pdf_url = urljoin(self.base_url, link['href'])
                    link_text = link.get_text().strip()
                    filename = os.path.basename(pdf_url)
                    
                    # Check if the PDF matches our subject and exam type
                    matches_subject = True
                    matches_exam_type = True
                    
                    if subject:
                        matches_subject = normalized_subject.lower() in link_text.lower() or normalized_subject.lower() in filename.lower()
                    
                    if exam_type:
                        matches_exam_type = normalized_exam_type.lower() in link_text.lower() or normalized_exam_type.lower() in filename.lower()
                    
                    # Only process PDFs that match our criteria
                    if matches_subject and matches_exam_type:
                        # Try to extract year
                        year_match = re.search(r'(20\d\d)', filename) or re.search(r'(20\d\d)', link_text)
                        if year_match:
                            year = int(year_match.group(1))
                            
                            # Skip papers older than year_from
                            if year < year_from:
                                continue
                            
                            # Determine paper type
                            paper_type = "Question Paper"
                            if any(term in filename.lower() or term in link_text.lower() for term in ["mark scheme", "ms", "markscheme"]):
                                paper_type = "Mark Scheme"
                            elif any(term in filename.lower() or term in link_text.lower() for term in ["examiner", "report", "er"]):
                                paper_type = "Examiner Report"
                            
                            # Determine paper number
                            paper_num_match = re.search(r'paper\s*(\d+)', filename.lower()) or re.search(r'paper\s*(\d+)', link_text.lower())
                            paper_number = int(paper_num_match.group(1)) if paper_num_match else 1
                            
                            # Determine season
                            season = "Summer"
                            if any(term in filename.lower() or term in link_text.lower() for term in ["january", "jan", "winter"]):
                                season = "Winter"
                            
                            # Create a standardized filename
                            standardized_filename = f"Edexcel_{normalized_subject}_{year}_{season}_Paper{paper_number}"
                            
                            if paper_type == "Mark Scheme":
                                standardized_filename += "_MS"
                            elif paper_type == "Examiner Report":
                                standardized_filename += "_ER"
                            
                            standardized_filename += ".pdf"
                            
                            # Create subdirectory path
                            subdir = os.path.join(
                                normalized_exam_type,
                                normalized_subject.replace(" ", "_"),
                                str(year),
                                season
                            )
                            
                            # Determine document type for directory structure
                            document_type = paper_type.lower().replace(" ", "_")
                            
                            # Download the paper
                            logger.info(f"Downloading {paper_type} from {pdf_url}")
                            file_path = self._download_document(
                                pdf_url,
                                standardized_filename,
                                subdir,
                                document_type
                            )
                            
                            if file_path:
                                # Create paper data dictionary
                                papers.append(self._build_paper_data(
                                    exam_board="Edexcel",
                                    exam_type=normalized_exam_type,
                                    subject=normalized_subject,
                                    year=year,
                                    season=season,
                                    title=link_text,
                                    paper_number=paper_number,
                                    document_type=paper_type,
                                    specification_code="",  # Edexcel codes are complex and vary by subject
                                    file_path=file_path
                                ))
                
                logger.info(f"Downloaded {len(papers)} papers for {subject} ({exam_type})")
            else:
                logger.warning(f"No matching PDF links found for {subject} ({exam_type})")
        
        except Exception as e:
            logger.error(f"Error scraping papers: {e}", exc_info=True)
        
        finally:
            # Ensure browser is closed
            self.close()
        
        return papers
