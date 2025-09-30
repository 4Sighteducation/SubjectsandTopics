"""
ExamPapersPlus Scraper module for UK Exam Board Topic List Scraper.

This module handles scraping exam papers from ExamPapersPlus.co.uk.
"""

import os
import re
import time
import logging
from urllib.parse import urljoin, urlparse
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from utils.logger import get_logger
from utils.helpers import (
    download_file, ensure_directory, normalize_subject_name, 
    normalize_exam_type, random_delay
)

logger = get_logger()

class ExamPapersPlusScraper(BaseScraper):
    """
    Scraper for ExamPapersPlus.co.uk exam papers.
    
    This class handles scraping, parsing, and downloading exam papers
    from ExamPapersPlus.co.uk.
    """
    
    def __init__(self, output_dir="data", debug=False):
        """
        Initialize the ExamPapersPlus scraper.
        
        Args:
            output_dir (str): Base directory for downloaded files
            debug (bool): Enable debug mode (headful browser, more logs)
        """
        # Initialize with proper parameters for BaseScraper
        super().__init__(
            name="ExamPapersPlus",
            base_url="https://www.exampapersplus.co.uk",
            headless=not debug,
            delay=2.0,  # Higher delay to respect server load
            output_dir=output_dir
        )
        
        # Common URLs - updated to match actual site structure
        self.gcse_url = f"{self.base_url}/resources/gcse"
        self.a_level_url = f"{self.base_url}/resources/a-level"
        
        # Map ExamPapersPlus subjects to our standardized subject names
        self.subject_map = {
            "maths": "Mathematics",
            "biology": "Biology",
            "chemistry": "Chemistry",
            "physics": "Physics",
            "combined science": "Combined Science",
            "english language": "English Language",
            "english literature": "English Literature",
            "geography": "Geography",
            "history": "History",
            "computer science": "Computer Science",
            "business": "Business Studies",
            "economics": "Economics",
            "french": "French",
            "german": "German",
            "spanish": "Spanish",
            "religious studies": "Religious Studies",
            # Add more mappings as needed
        }
        
        # Mapping between exam boards as they appear on ExamPapersPlus and our standardized names
        self.exam_board_map = {
            "aqa": "AQA",
            "edexcel": "Edexcel",
            "ocr": "OCR",
            "wjec": "WJEC",
            "ccea": "CCEA",
            # Add more as needed
        }
    
    def get_subject_urls(self, exam_type):
        """
        Get URLs for all subjects of a given exam type.
        
        Args:
            exam_type (str): Type of exam (e.g., 'gcse', 'a-level')
            
        Returns:
            dict: Dictionary mapping subject names to their URLs
        """
        if exam_type.lower() == 'gcse':
            url = self.gcse_url
        elif exam_type.lower() in ['a-level', 'a level', 'alevel']:
            url = self.a_level_url
        else:
            logger.warning(f"Unsupported exam type: {exam_type} for ExamPapersPlus")
            return {}
        
        subject_urls = {}
        
        try:
            # Use Selenium to navigate the site, as it may have dynamic content
            html_content = self._get_page(url, use_selenium=True)
            
            if not html_content:
                logger.error(f"Failed to get content from {url}")
                return {}
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for subject links - try different possible selectors
            subject_links = []
            
            # Look for links in main navigation/subject grid
            subject_containers = soup.select('.subject-grid, .subjects-list, .category-grid')
            if subject_containers:
                for container in subject_containers:
                    subject_links.extend(container.select('a'))
            
            # If no subject links found yet, try other common structures
            if not subject_links:
                # Try looking for list items that might contain subject links
                list_items = soup.select('li.subject-item, li.category-item')
                for item in list_items:
                    subject_links.extend(item.select('a'))
            
            # If still no subject links, fallback to examining all links
            if not subject_links:
                all_links = soup.select('a')
                for link in all_links:
                    href = link.get('href', '')
                    text = link.text.strip()
                    
                    # Skip empty, navigation or non-subject links
                    if not href or not text:
                        continue
                    
                    if text.lower() in ['home', 'login', 'register', 'cart', 'checkout']:
                        continue
                    
                    # Look for common subject names in the link
                    for subject_key in self.subject_map.keys():
                        if subject_key in text.lower() or subject_key in href.lower():
                            subject_links.append(link)
                            break
            
            logger.debug(f"Found {len(subject_links)} potential subject links")
            
            # Process subject links
            for link in subject_links:
                href = link.get('href', '')
                text = link.text.strip()
                
                # Skip empty links
                if not href or not text:
                    continue
                
                # Skip non-subject links
                if text.lower() in ['home', 'login', 'register', 'cart', 'checkout']:
                    continue
                
                # Normalize subject name
                normalized_name = normalize_subject_name(text)
                
                # Get standardized name if available
                for key, value in self.subject_map.items():
                    if key in normalized_name.lower():
                        normalized_name = value
                        break
                
                # Create full URL if needed
                if href.startswith('/'):
                    subject_url = urljoin(self.base_url, href)
                elif not href.startswith(('http://', 'https://')):
                    subject_url = urljoin(self.base_url, '/' + href)
                else:
                    subject_url = href
                
                subject_urls[normalized_name] = subject_url
            
            logger.info(f"Found {len(subject_urls)} subject URLs for {exam_type}")
            return subject_urls
            
        except Exception as e:
            logger.error(f"Error fetching subject URLs: {e}", exc_info=True)
            return {}
    
    def _navigate_to_papers(self, subject_url, exam_type, use_selenium=True):
        """
        Navigate to the papers section for a subject.
        
        ExamPapersPlus might have a different structure where we need to navigate
        through multiple pages to reach the actual papers.
        
        Args:
            subject_url (str): URL of the subject page
            exam_type (str): Type of exam
            use_selenium (bool): Whether to use Selenium for navigation
            
        Returns:
            tuple: (soup, url) where soup is the BeautifulSoup object of the papers page
                  and url is the URL of that page
        """
        logger.info(f"Navigating to papers for {subject_url}")
        
        try:
            # Get the subject page
            html_content = self._get_page(subject_url, use_selenium=use_selenium)
            
            if not html_content:
                logger.error(f"Failed to get content from {subject_url}")
                return None, subject_url
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for links that might lead to past papers
            paper_links = []
            
            # Look for links with common paper-related text
            all_links = soup.select('a')
            for link in all_links:
                href = link.get('href', '')
                text = link.text.strip().lower()
                
                # Skip empty links
                if not href or not text:
                    continue
                
                # Check if it's likely a link to papers
                if any(term in text or term in href.lower() for term in 
                      ['past paper', 'exam paper', 'question paper', 'past exam']):
                    paper_links.append(link)
            
            # If found links to navigate further, follow the first one
            if paper_links:
                href = paper_links[0].get('href', '')
                
                # Create full URL if needed
                if href.startswith('/'):
                    papers_url = urljoin(self.base_url, href)
                elif not href.startswith(('http://', 'https://')):
                    papers_url = urljoin(self.base_url, '/' + href)
                else:
                    papers_url = href
                
                # Get the papers page
                html_content = self._get_page(papers_url, use_selenium=use_selenium)
                
                if html_content:
                    return BeautifulSoup(html_content, 'html.parser'), papers_url
            
            # If no paper links found or navigation failed, return the original page
            return soup, subject_url
            
        except Exception as e:
            logger.error(f"Error navigating to papers: {e}", exc_info=True)
            return None, subject_url
    
    def _get_exam_board_sections(self, soup, current_url):
        """
        Get exam board sections or links from a page.
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object of the page
            current_url (str): URL of the current page
            
        Returns:
            dict: Dictionary mapping exam board names to their URLs or BeautifulSoup sections
        """
        exam_board_sections = {}
        
        try:
            # Try to find explicit exam board sections/tabs/filters
            board_sections = soup.select('.exam-board-section, .board-tab, .board-filter')
            
            if board_sections:
                # Process each section
                for section in board_sections:
                    # Try to determine the board name from section attributes
                    board_name = None
                    
                    # Check id or class attributes for board name
                    section_id = section.get('id', '').lower()
                    section_class = ' '.join(section.get('class', [])).lower()
                    
                    for board_key, board_value in self.exam_board_map.items():
                        if board_key in section_id or board_key in section_class:
                            board_name = board_value
                            break
                    
                    # If board name not found in attributes, check text content
                    if not board_name:
                        section_text = section.get_text().lower()
                        for board_key, board_value in self.exam_board_map.items():
                            if board_key in section_text:
                                board_name = board_value
                                break
                    
                    # If still no board name, skip this section
                    if not board_name:
                        continue
                    
                    # Add section to board sections
                    exam_board_sections[board_name] = section
                
                return exam_board_sections
            
            # If no explicit sections, look for links to board-specific pages
            board_links = []
            all_links = soup.select('a')
            
            for link in all_links:
                href = link.get('href', '')
                text = link.text.strip().lower()
                
                # Skip empty links
                if not href or not text:
                    continue
                
                # Check if link is related to an exam board
                is_board_link = False
                board_name = None
                
                for board_key, board_value in self.exam_board_map.items():
                    if board_key in text or board_key in href.lower():
                        is_board_link = True
                        board_name = board_value
                        break
                
                if is_board_link and board_name:
                    # Create full URL if needed
                    if href.startswith('/'):
                        board_url = urljoin(self.base_url, href)
                    elif not href.startswith(('http://', 'https://')):
                        board_url = urljoin(self.base_url, '/' + href)
                    else:
                        board_url = href
                    
                    exam_board_sections[board_name] = board_url
            
            # If no board links found, check if the current page is board-specific
            if not exam_board_sections:
                url_lower = current_url.lower()
                page_text = soup.get_text().lower()
                
                for board_key, board_value in self.exam_board_map.items():
                    if board_key in url_lower or board_key in page_text:
                        # This page is for a specific board
                        exam_board_sections[board_value] = current_url
                        break
            
            # If still no board sections, use the current page with Unknown board
            if not exam_board_sections:
                exam_board_sections["Unknown"] = current_url
            
            return exam_board_sections
            
        except Exception as e:
            logger.error(f"Error getting exam board sections: {e}", exc_info=True)
            return {"Unknown": current_url}
    
    def _extract_papers_from_board_section(self, section_or_url, board_name, subject, exam_type, year_from=2021):
        """
        Extract papers from an exam board section or page.
        
        Args:
            section_or_url: BeautifulSoup section or URL string
            board_name (str): Name of the exam board
            subject (str): Subject name
            exam_type (str): Exam type
            year_from (int): Year to start from
            
        Returns:
            list: List of paper data dictionaries
        """
        papers = []
        
        try:
            # Check if section_or_url is a URL string
            if isinstance(section_or_url, str):
                # Get page content
                html_content = self._get_page(section_or_url, use_selenium=True)
                
                if not html_content:
                    logger.error(f"Failed to get content from {section_or_url}")
                    return []
                
                soup = BeautifulSoup(html_content, 'html.parser')
                section = soup
            else:
                # It's already a BeautifulSoup section
                section = section_or_url
            
            # Look for paper links
            # Try first with links that end with .pdf
            paper_links = section.select('a[href$=".pdf"]')
            
            # If no direct PDF links, try links that might lead to papers
            if not paper_links:
                all_links = section.select('a')
                
                paper_links = [link for link in all_links if 
                               any(term in link.get('href', '').lower() or term in link.text.lower() 
                                  for term in ['paper', 'exam', 'past', 'question', 'mark scheme'])]
            
            logger.debug(f"Found {len(paper_links)} potential paper links")
            
            # Process each paper link
            for link in paper_links:
                href = link.get('href', '')
                text = link.text.strip()
                
                # Skip empty links
                if not href or not text:
                    continue
                
                # Create full URL
                if href.startswith('/'):
                    paper_url = urljoin(self.base_url, href)
                elif not href.startswith(('http://', 'https://')):
                    paper_url = urljoin(self.base_url, '/' + href)
                else:
                    paper_url = href
                
                # Skip if URL doesn't end with .pdf (likely not a direct paper link)
                if not paper_url.lower().endswith('.pdf'):
                    continue
                
                # Extract paper metadata from link text, URL or surrounding context
                
                # 1. Extract year
                year_match = re.search(r'20(\d{2})', text + ' ' + href)
                year = int('20' + year_match.group(1)) if year_match else None
                
                # Skip papers older than year_from
                if year and year < year_from:
                    continue
                
                # 2. Extract document type
                doc_type = "Question Paper"  # Default
                if any(term in text.lower() or term in href.lower() 
                       for term in ['mark scheme', 'ms', 'marking']):
                    doc_type = "Mark Scheme"
                elif any(term in text.lower() or term in href.lower() 
                         for term in ['examiner', 'report', 'er']):
                    doc_type = "Examiner Report"
                
                # 3. Extract season
                season = "Summer"  # Default
                for season_name in ["Summer", "Winter", "January", "June", "November"]:
                    if season_name.lower() in text.lower() or season_name.lower() in href.lower():
                        season = season_name
                        break
                
                # 4. Extract paper number
                paper_number = 1  # Default
                paper_match = re.search(r'paper\s*(\d+)', text.lower() + ' ' + href.lower())
                if paper_match:
                    paper_number = int(paper_match.group(1))
                
                # 5. Extract specification code
                spec_code = ""
                spec_match = re.search(r'(\d{4}[A-Za-z0-9]*)', text + ' ' + href)
                if spec_match:
                    spec_code = spec_match.group(1)
                
                # Build paper data dictionary
                paper_data = self._build_paper_data(
                    exam_board=board_name,
                    exam_type=exam_type,
                    subject=subject,
                    year=year or 2021,  # Default if no year found
                    season=season,
                    title=text,
                    paper_number=paper_number,
                    document_type=doc_type,
                    specification_code=spec_code,
                    file_path=""  # Will be filled after download
                )
                
                # Add URL for download
                paper_data["URL"] = paper_url
                
                # Download the paper
                output_path = self._download_paper(paper_data)
                if output_path:
                    paper_data["Paper"] = output_path
                    papers.append(paper_data)
                    logger.debug(f"Added paper: {text}")
            
            return papers
            
        except Exception as e:
            logger.error(f"Error extracting papers: {e}", exc_info=True)
            return []
    
    def _download_paper(self, paper_data):
        """
        Download a paper file.
        
        Args:
            paper_data (dict): Paper metadata dictionary
            
        Returns:
            str: Path to the downloaded file, or None if download failed
        """
        if not paper_data.get("URL"):
            return None
        
        url = paper_data["URL"]
        
        # Skip non-PDF URLs
        if not url.lower().endswith('.pdf'):
            logger.warning(f"Skipping non-PDF URL: {url}")
            return None
        
        # Create appropriate directory structure
        exam_board = paper_data.get("Exam Board", "Unknown")
        exam_type = paper_data.get("Exam Type", "Unknown")
        subject = paper_data.get("Subject", "Unknown")
        year = paper_data.get("Year", "Unknown")
        season = paper_data.get("Season", "Unknown")
        
        # Determine the document type for directory structure
        document_type = paper_data.get("Document Type", "Question Paper").lower().replace(" ", "_")
        
        # Construct file name
        file_name = os.path.basename(urlparse(url).path)
        if not file_name or file_name == '':
            # Generate a filename from metadata if URL doesn't provide one
            spec_code = paper_data.get("Specification Code", "")
            paper_num = paper_data.get("Paper Number", "")
            file_name = f"{exam_board}_{exam_type}_{subject}_{year}_{season}_Paper{paper_num}_{document_type}"
            if spec_code:
                file_name = f"{spec_code}_{file_name}"
            file_name = file_name.replace(" ", "_") + ".pdf"
        
        # Use the standard method from BaseScraper to download document
        subdir = os.path.join(
            exam_type,
            subject,
            str(year),
            season
        )
        
        return self._download_document(url, file_name, subdir, document_type)
    
    def scrape_papers(self, subject=None, exam_type=None, year_from=2021):
        """
        Scrape past papers for a specific subject and exam type.
        
        Args:
            subject (str, optional): Subject name to scrape papers for
            exam_type (str, optional): Exam type to scrape papers for
            year_from (int): Year to start scraping papers from
            
        Returns:
            list: List of paper data dictionaries
        """
        if not subject or not exam_type:
            logger.warning("Both subject and exam_type are required for ExamPapersPlus scraper")
            return []
            
        logger.info(f"Scraping ExamPapersPlus papers for {subject} ({exam_type})")
        
        # Normalize inputs
        normalized_subject = normalize_subject_name(subject)
        normalized_exam_type = normalize_exam_type(exam_type)
        
        all_papers = []
        
        # Get subject URLs for this exam type
        subject_urls = self.get_subject_urls(normalized_exam_type)
        
        if not subject_urls:
            logger.warning(f"No subject URLs found for {normalized_exam_type}")
            return []
        
        # Find matching subject URL
        matching_subject_url = None
        for subj, url in subject_urls.items():
            # Check for exact match or if subject name contains our target
            if (normalized_subject.lower() == subj.lower() or
                normalized_subject.lower() in subj.lower() or
                subj.lower() in normalized_subject.lower()):
                matching_subject_url = url
                break
        
        if not matching_subject_url:
            logger.warning(f"No matching subject URL found for {normalized_subject}")
            return []
        
        # Navigate to the papers section
        papers_soup, papers_url = self._navigate_to_papers(matching_subject_url, normalized_exam_type)
        
        if not papers_soup:
            logger.warning(f"Failed to navigate to papers for {normalized_subject}")
            return []
        
        # Get exam board sections or URLs
        board_sections = self._get_exam_board_sections(papers_soup, papers_url)
        
        if not board_sections:
            logger.warning(f"No exam board sections found for {normalized_subject}")
            return []
        
        # Extract papers from each board section or URL
        for board_name, section_or_url in board_sections.items():
            try:
                board_papers = self._extract_papers_from_board_section(
                    section_or_url, board_name, normalized_subject, 
                    normalized_exam_type, year_from
                )
                all_papers.extend(board_papers)
                
            except Exception as e:
                logger.error(f"Error processing board {board_name}: {e}", exc_info=True)
        
        logger.info(f"Scraped {len(all_papers)} papers for {subject} from ExamPapersPlus")
        return all_papers
    
    def scrape_topics(self, subject=None, exam_type=None):
        """
        ExamPapersPlus doesn't provide detailed topic lists, only past papers.
        This is a placeholder implementation returning an empty list.
        
        Args:
            subject (str, optional): Subject name to scrape topics for
            exam_type (str, optional): Exam type to scrape topics for
            
        Returns:
            list: Empty list (no topics available)
        """
        logger.info(f"ExamPapersPlus doesn't provide topic lists, only past papers.")
        return []
