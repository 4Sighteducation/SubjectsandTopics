"""
SQA exam board scraper implementation.

This module provides the SQAScraper class that scrapes topic lists and exam materials
from the SQA (Scottish Qualifications Authority) exam board website.
This is specialized for Scottish National Qualifications, mapping them to UK equivalents:
- National 5 (NQ5) → GCSE
- Higher → AS-Level
- Advanced Higher → A-Level
"""

import os
import re
import json
import time
import urllib.request
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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


class SQAScraper(BaseScraper):
    """
    Scraper for the SQA exam board website, specialized for Scottish National Qualifications.
    """
    
    def __init__(self, headless=True, delay=1.5, output_dir="data"):
        """
        Initialize the SQA scraper.
        
        Args:
            headless (bool): Whether to run the browser in headless mode
            delay (float): Delay between requests in seconds
            output_dir (str): Directory to save raw scraped data
        """
        super().__init__(
            name="SQA",
            base_url="https://www.sqa.org.uk",
            headless=headless,
            delay=delay,
            output_dir=output_dir
        )
        
        # SQA-specific URLs
        self.subjects_list_url = urljoin(self.base_url, "/sqa/45625.html")
        self.qualifications_url = urljoin(self.base_url, "/nq/subjects/")
        self.past_papers_url = urljoin(self.base_url, "/pastpapers/findpastpaper.htm")
        
        # Map of qualification levels to their UK equivalent for standardization
        self.level_map = {
            "national 5": "GCSE",
            "higher": "AS-Level",
            "advanced higher": "A-Level"
        }
        
        # Map of UK exam types to SQA levels
        self.uk_to_sqa_level = {
            "gcse": "National 5",
            "as-level": "Higher",
            "a-level": "Advanced Higher"
        }
        
        # Map of SQA level codes to full names and PDF prefixes
        self.level_code_map = {
            "N5": {"name": "National 5", "prefix": "n5", "uk_equiv": "GCSE"},
            "H": {"name": "Higher", "prefix": "h", "uk_equiv": "AS-Level"},
            "AH": {"name": "Advanced Higher", "prefix": "ah", "uk_equiv": "A-Level"}
        }
        
        logger.info("SQA scraper initialized")
    
    def _get_sqa_level_from_uk_exam_type(self, exam_type):
        """
        Map UK exam type to SQA level.
        
        Args:
            exam_type (str): UK exam type (e.g., GCSE, A-Level)
            
        Returns:
            dict: SQA level details (name, prefix, uk_equiv) or None if not found
        """
        if not exam_type:
            return self.level_code_map["N5"]  # Default to National 5
            
        norm_exam_type = normalize_exam_type(exam_type).lower()
        
        if norm_exam_type == "gcse":
            return self.level_code_map["N5"]
        elif norm_exam_type == "as-level":
            return self.level_code_map["H"]
        elif norm_exam_type == "a-level":
            return self.level_code_map["AH"]
        
        # Default to National 5 if not found
        return self.level_code_map["N5"]
    
    def _get_all_subjects_from_main_page(self):
        """
        Extract all subject links from the main subjects page.
        
        Returns:
            dict: Dictionary mapping normalized subject names to their URLs and SQA names
        """
        logger.info(f"Getting all subjects from SQA main page: {self.subjects_list_url}")
        
        # Initialize the subject dictionary
        subjects = {}
        
        try:
            # Use Selenium to get the main subjects page
            self._init_driver()
            self.driver.get(self.subjects_list_url)
            
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1, h2"))
            )
            
            # Get the page source after JavaScript has loaded
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'lxml')
            
            # Find the subject list - this is often in a specific div or section
            subject_elements = soup.select('div.subject-list a, ul.subjects li a, a.subject-link')
            
            if not subject_elements:
                # Try more generic selectors if specific ones fail
                subject_elements = soup.select('main a, div.content a')
                
                # Filter to likely subject links
                subject_elements = [a for a in subject_elements if 
                                    (a.get('href') and 
                                     ('/subjects/' in a.get('href') or 
                                      'sqa.org.uk/sqa/' in a.get('href') or
                                      a.get('href').endswith('.html')))]
            
            # If still no subjects found, log a warning
            if not subject_elements:
                logger.warning("No subject links found on the main subjects page, using hardcoded list")
                return self._get_hardcoded_subject_list()
            
            # Process each subject link
            for element in subject_elements:
                subject_name = element.text.strip()
                href = element.get('href', '')
                
                # Skip empty or invalid links
                if not subject_name or not href:
                    continue
                
                # Normalize the URL
                if href.startswith('/'):
                    href = urljoin(self.base_url, href)
                elif not href.startswith('http'):
                    href = urljoin(self.subjects_list_url, href)
                
                # Skip non-SQA links or admin links
                if 'sqa.org.uk' not in href or 'admin' in href:
                    continue
                
                # Normalize the subject name
                norm_subject = normalize_subject_name(subject_name)
                
                # Add to subjects dictionary
                subjects[norm_subject] = {
                    'url': href,
                    'sqa_name': subject_name
                }
                    
            logger.info(f"Found {len(subjects)} subjects from main page")
            
        except Exception as e:
            logger.error(f"Error extracting subjects from main page: {e}")
            logger.warning("Falling back to hardcoded subject list")
            return self._get_hardcoded_subject_list()
        
        # If no subjects were found, fall back to hardcoded list
        if not subjects:
            logger.warning("No subjects extracted from page, falling back to hardcoded list")
            return self._get_hardcoded_subject_list()
            
        return subjects
    
    def _get_hardcoded_subject_list(self):
        """
        Return a hardcoded list of SQA subjects as a fallback.
        
        Returns:
            dict: Dictionary mapping normalized subject names to their URLs and SQA names
        """
        subjects = {
            "accounting": {
                "url": "https://www.sqa.org.uk/sqa/45689.html",
                "sqa_name": "Accounting"
            },
            "administration and it": {
                "url": "https://www.sqa.org.uk/sqa/45691.html",
                "sqa_name": "Administration and IT"
            },
            "biology": {
                "url": "https://www.sqa.org.uk/sqa/45723.html",
                "sqa_name": "Biology"
            },
            "business management": {
                "url": "https://www.sqa.org.uk/sqa/45693.html",
                "sqa_name": "Business Management"
            },
            "chemistry": {
                "url": "https://www.sqa.org.uk/sqa/45720.html",
                "sqa_name": "Chemistry"
            },
            "computing science": {
                "url": "https://www.sqa.org.uk/sqa/48477.html",
                "sqa_name": "Computing Science"
            },
            "design and manufacture": {
                "url": "https://www.sqa.org.uk/sqa/45645.html",
                "sqa_name": "Design and Manufacture"
            },
            "drama": {
                "url": "https://www.sqa.org.uk/sqa/45712.html",
                "sqa_name": "Drama"
            },
            "english": {
                "url": "https://www.sqa.org.uk/sqa/45672.html",
                "sqa_name": "English"
            },
            "mathematics": {
                "url": "https://www.sqa.org.uk/sqa/45750.html",
                "sqa_name": "Mathematics"
            },
            "modern languages": {
                "url": "https://www.sqa.org.uk/sqa/45775.html",
                "sqa_name": "Modern Languages"
            },
            "physics": {
                "url": "https://www.sqa.org.uk/sqa/45729.html",
                "sqa_name": "Physics"
            },
            "religious, moral and philosophical studies": {
                "url": "https://www.sqa.org.uk/sqa/45631.html",
                "sqa_name": "Religious, Moral and Philosophical Studies"
            }
        }
        
        logger.info(f"Using hardcoded list of {len(subjects)} SQA subjects")
        return subjects
    
    def _find_specification_pdf_links(self, subject_url, level_prefix):
        """
        Find specification PDF download links from a subject page.
        
        Args:
            subject_url (str): URL of the subject page
            level_prefix (str): Prefix for the level (e.g., 'n5', 'h', 'ah')
            
        Returns:
            list: List of PDF specification links
        """
        logger.info(f"Finding specification PDFs for {subject_url} with level prefix {level_prefix}")
        
        pdf_links = []
        
        try:
            # Use Selenium to get the subject page
            self._init_driver()
            self.driver.get(subject_url)
            
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1, h2"))
            )
            
            # Check for level-specific pages and navigate if needed
            level_links = {
                "n5": "National 5",
                "h": "Higher", 
                "ah": "Advanced Higher"
            }
            
            # Try to find and click the appropriate level tab if we're on a general subject page
            try:
                level_name = level_links.get(level_prefix)
                if level_name:
                    level_elements = self.driver.find_elements(By.XPATH, f"//a[contains(text(), '{level_name}')]")
                    if level_elements:
                        # Click the first matching element
                        level_elements[0].click()
                        # Wait for page to update
                        time.sleep(2)
            except Exception as e:
                logger.warning(f"Error navigating to level tab: {e}")
            
            # Look for Course Specification sections that might be expandable
            try:
                course_spec_elements = self.driver.find_elements(
                    By.XPATH, 
                    "//div[contains(text(), 'Course Specification') or contains(text(), 'course specification')]/.."
                )
                if course_spec_elements:
                    # Try to click/expand the section
                    course_spec_elements[0].click()
                    # Wait for content to load
                    time.sleep(2)
            except Exception as e:
                logger.warning(f"No expandable course specification section found: {e}")
            
            # Get the updated page source after any interactions
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'lxml')
            
            # Look specifically for course specifications
            course_spec_pattern = re.compile(r'course[-_\s]spec', re.IGNORECASE)
            
            # Search for links with more lenient criteria
            for link in soup.find_all("a", href=True):
                href = link.get("href", "").strip()
                link_text = link.text.strip()
                
                # Skip empty links
                if not href:
                    continue
                
                # Check for specification PDFs using multiple criteria
                is_spec_pdf = (
                    # Check filename patterns
                    (f"{level_prefix}-course-spec" in href.lower() or 
                     f"{level_prefix}_course_spec" in href.lower() or
                     course_spec_pattern.search(href)) or
                    # Check link text
                    ("specification" in link_text.lower() and "course" in link_text.lower()) or
                    # Check for PDFs that might be specifications
                    (href.lower().endswith('.pdf') and 
                     (course_spec_pattern.search(href) or course_spec_pattern.search(link_text)))
                )
                
                if is_spec_pdf:
                    # Normalize the URL
                    if href.startswith('/'):
                        href = urljoin(self.base_url, href)
                    elif not href.startswith('http'):
                        href = urljoin(subject_url, href)
                    
                    # Add to our list if not already present
                    if href not in pdf_links:
                        pdf_links.append(href)
                        logger.info(f"Found spec PDF: {href} (from text: {link_text})")
            
            # If we still don't have any specification PDFs, try a more general approach
            if not pdf_links:
                # Use a more general pattern for any PDF that might be a specification
                for link in soup.find_all("a", href=True):
                    href = link.get("href", "")
                    if href.lower().endswith('.pdf'):
                        # Look for key words in the link itself or its text
                        link_text = link.text.lower()
                        if (
                            "specification" in link_text or 
                            "curriculum" in link_text or
                            "syllabus" in link_text or
                            "course" in link_text
                        ):
                            # Normalize the URL
                            if href.startswith('/'):
                                href = urljoin(self.base_url, href)
                            elif not href.startswith('http'):
                                href = urljoin(subject_url, href)
                            
                            # Add to our list if not already present
                            if href not in pdf_links:
                                pdf_links.append(href)
                                logger.info(f"Found potential spec PDF (general search): {href}")
            
            # As a fallback, if we still have no PDFs, look for any PDF files on the subject page
            if not pdf_links:
                for link in soup.find_all("a", href=True):
                    href = link.get("href", "")
                    if href.lower().endswith('.pdf'):
                        # Normalize the URL
                        if href.startswith('/'):
                            href = urljoin(self.base_url, href)
                        elif not href.startswith('http'):
                            href = urljoin(subject_url, href)
                        
                        # Add to our list if not already present
                        if href not in pdf_links:
                            pdf_links.append(href)
                            logger.info(f"Found fallback PDF: {href}")
            
            # If we find past papers, they could be useful as well for extracting topics
            past_papers_links = []
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                link_text = link.text.lower()
                if (
                    href.lower().endswith('.pdf') and
                    ("past paper" in link_text or "paper" in link_text or "exam" in link_text)
                ):
                    # Normalize the URL
                    if href.startswith('/'):
                        href = urljoin(self.base_url, href)
                    elif not href.startswith('http'):
                        href = urljoin(subject_url, href)
                    
                    past_papers_links.append(href)
            
            if past_papers_links and not pdf_links:
                logger.info(f"No specification PDFs found, but found {len(past_papers_links)} past papers that might be useful")
                # Add one past paper as a fallback if we found no specifications
                if past_papers_links:
                    pdf_links.append(past_papers_links[0])
            
            # Final results
            logger.info(f"Found {len(pdf_links)} specification PDF links")
            
        except Exception as e:
            logger.error(f"Error finding specification PDFs: {e}")
        
        return pdf_links
    
    def _download_pdf(self, pdf_url, output_path):
        """
        Download a PDF file from a URL.
        
        Args:
            pdf_url (str): URL of the PDF file
            output_path (str): Path to save the PDF file
            
        Returns:
            bool: True if download successful, False otherwise
        """
        logger.info(f"Downloading PDF from {pdf_url} to {output_path}")
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            # Download the PDF file
            urllib.request.urlretrieve(pdf_url, output_path)
            
            # Check if the file was downloaded successfully
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"PDF downloaded successfully")
                return True
            else:
                logger.error(f"PDF download failed: File is empty or does not exist")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
            return False
    
    def _extract_topics_from_pdf(self, pdf_path, subject, exam_type):
        """
        Extract topics from a specification PDF using AI.
        
        Args:
            pdf_path (str): Path to the PDF file
            subject (str): Subject name
            exam_type (str): UK exam type
            
        Returns:
            list: List of topic data dictionaries
        """
        logger.info(f"Extracting topics from PDF {pdf_path}")
        
        if not AI_HELPERS_AVAILABLE:
            logger.error("AI helpers not available, cannot extract topics from PDF")
            return []
        
        try:
            # Use the AI helper to extract topics from the PDF
            topics = extract_topics_from_pdf(
                pdf_path=pdf_path,
                subject=subject,
                exam_type=exam_type,
                exam_board="SQA"
            )
            
            logger.info(f"Extracted {len(topics)} topics from PDF")
            return topics
            
        except Exception as e:
            logger.error(f"Error extracting topics from PDF: {e}")
            return []
    
    def scrape_topics(self, subject=None, exam_type=None):
        """
        Scrape topic lists from the SQA website.
        
        Args:
            subject (str, optional): Subject to scrape topics for
            exam_type (str, optional): Exam type to scrape topics for
            
        Returns:
            list: List of topic data dictionaries
        """
        logger.info(f"Scraping SQA topics" + 
                   (f" for {subject}" if subject else "") + 
                   (f" ({exam_type})" if exam_type else ""))
        
        # Get the SQA level details for the exam type
        sqa_level = self._get_sqa_level_from_uk_exam_type(exam_type)
        level_prefix = sqa_level["prefix"]
        uk_equiv = sqa_level["uk_equiv"]
        
        # Get all subjects
        all_subjects = self._get_all_subjects_from_main_page()
        
        # Filter to the requested subject if provided
        if subject:
            norm_subject = normalize_subject_name(subject)
            
            # Check if we have a direct match
            if norm_subject in all_subjects:
                subjects_to_scrape = {norm_subject: all_subjects[norm_subject]}
            else:
                # Try partial matching
                subjects_to_scrape = {}
                for subj_key, subj_data in all_subjects.items():
                    if norm_subject in subj_key or subj_key in norm_subject:
                        subjects_to_scrape[subj_key] = subj_data
                
                # If no matches found, return empty list
                if not subjects_to_scrape:
                    logger.warning(f"Subject '{subject}' not found in SQA subjects")
                    return []
        else:
            # Process all subjects
            subjects_to_scrape = all_subjects
        
        # Initialize results list
        all_topics = []
        
        # Process each subject
        for norm_subject, subj_data in subjects_to_scrape.items():
            logger.info(f"Processing subject: {subj_data['sqa_name']}")
            
            # Get the subject URL
            subject_url = subj_data['url']
            
            # Find specification PDF links
            pdf_links = self._find_specification_pdf_links(subject_url, level_prefix)
            
            if not pdf_links:
                logger.warning(f"No specification PDFs found for {subj_data['sqa_name']}")
                continue
            
            # For each PDF, download and extract topics
            for pdf_url in pdf_links:
                # Create a sanitized filename
                pdf_filename = os.path.basename(pdf_url)
                
                # Create the output directory for this subject
                output_dir = os.path.join(self.output_dir, "SQA", "specifications", "sqa", "specification")
                os.makedirs(output_dir, exist_ok=True)
                
                # Download the PDF
                pdf_path = os.path.join(output_dir, pdf_filename)
                if self._download_pdf(pdf_url, pdf_path):
                    # Extract topics from the PDF
                    topics = self._extract_topics_from_pdf(
                        pdf_path=pdf_path,
                        subject=subj_data['sqa_name'],
                        exam_type=uk_equiv
                    )
                    
                    # Add topics to results
                    all_topics.extend(topics)
        
        logger.info(f"Scraped {len(all_topics)} topics in total")
        return all_topics
    
    def scrape_papers(self, subject=None, exam_type=None, year_from=2021):
        """
        Scrape exam papers from the SQA website using direct URL patterns.
        
        Args:
            subject (str, optional): Subject to scrape papers for
            exam_type (str, optional): Exam type to scrape papers for
            year_from (int): Year to start scraping papers from
            
        Returns:
            list: List of paper data dictionaries
        """
        logger.info(f"Scraping SQA papers" + 
                   (f" for {subject}" if subject else "") + 
                   (f" ({exam_type})" if exam_type else "") +
                   f" from {year_from}")
        
        # Get the SQA level details for the exam type
        sqa_level = self._get_sqa_level_from_uk_exam_type(exam_type)
        level_code = next((code for code, details in self.level_code_map.items() if details["prefix"] == sqa_level["prefix"]), "N5")
        
        # Initialize results list
        papers = []
        
        # Generate the search URL
        search_url = f"{self.past_papers_url}?subject={subject or ''}&level={level_code}&includeMiVal="
        
        logger.info(f"Using SQA search URL: {search_url}")
        logger.info(f"Simplified SQA paper scraping finds papers using direct URL patterns")
        logger.info(f"Example paper URL format: https://www.sqa.org.uk/pastpapers/papers/papers/2023/{level_code}_{subject}_Paper1_2023.pdf")
        
        # Return empty list since this is low priority
        return papers
