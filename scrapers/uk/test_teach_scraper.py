"""
TestTeach Scraper module for UK Exam Board Topic List Scraper.

This module handles scraping exam papers from TestTeach.co.uk.
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

class TestTeachScraper(BaseScraper):
    """
    Scraper for TestTeach.co.uk exam papers.
    
    This class handles scraping, parsing, and downloading exam papers
    from TestTeach.co.uk.
    """
    
    def __init__(self, output_dir="data", debug=False):
        """
        Initialize the TestTeach scraper.
        
        Args:
            output_dir (str): Base directory for downloaded files
            debug (bool): Enable debug mode (headful browser, more logs)
        """
        # Initialize with proper parameters for BaseScraper
        super().__init__(
            name="TestTeach",
            base_url="https://www.testteach.co.uk",
            headless=not debug,
            delay=1.5,  # Slightly higher delay to respect their server
            output_dir=output_dir
        )
        
        # Define main resource paths - updated for current site structure
        self.past_papers_url = f"{self.base_url}/resources/past-papers"
        self.gcse_papers_url = f"{self.base_url}/resources/gcse"
        self.a_level_papers_url = f"{self.base_url}/resources/a-level"
        
        # Map TestTeach subjects to our standardized subject names
        self.subject_map = {
            "maths": "Mathematics",
            "mathematics": "Mathematics",
            "biology": "Biology",
            "chemistry": "Chemistry",
            "physics": "Physics",
            "combined science": "Combined Science",
            "english language": "English Language",
            "english lit": "English Literature",
            "geography": "Geography",
            "history": "History",
            "computer science": "Computer Science",
            "business studies": "Business Studies",
            "economics": "Economics",
            "design and technology": "Design and Technology",
            "french": "French",
            "german": "German",
            "spanish": "Spanish",
            "religious studies": "Religious Studies",
            # Add more mappings as needed
        }
        
        # Mapping between exam boards as they appear on TestTeach and our standardized names
        self.exam_board_map = {
            "aqa": "AQA",
            "edexcel": "Edexcel",
            "ocr": "OCR",
            "wjec": "WJEC",
            "ccea": "CCEA",
            "eduqas": "WJEC",  # Eduqas is part of WJEC
            # Add more as needed
        }
    
    def get_exam_type_urls(self):
        """
        Get URLs for all exam types.
        
        Returns:
            dict: Dictionary mapping exam type names to their URLs
        """
        exam_type_urls = {
            "GCSE": self.gcse_papers_url,
            "A-Level": self.a_level_papers_url
        }
        
        # Also check the main past papers page for more exam types
        try:
            html_content = self._get_page(self.past_papers_url, use_selenium=True)
            
            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Look for links that might be exam types
                all_links = soup.select('a')
                
                for link in all_links:
                    href = link.get('href', '')
                    text = link.text.strip()
                    
                    # Skip empty links
                    if not href or not text:
                        continue
                    
                    # Check if it's an exam type link
                    if 'papers' in href.lower() and text not in exam_type_urls:
                        # Normalize exam type
                        norm_type = normalize_exam_type(text)
                        
                        # Create full URL if needed
                        if href.startswith('/'):
                            type_url = urljoin(self.base_url, href)
                        elif not href.startswith(('http://', 'https://')):
                            type_url = urljoin(self.base_url, '/' + href)
                        else:
                            type_url = href
                        
                        exam_type_urls[norm_type] = type_url
            
            logger.debug(f"Found {len(exam_type_urls)} exam type URLs")
            
        except Exception as e:
            logger.error(f"Error getting exam type URLs: {e}", exc_info=True)
        
        return exam_type_urls
    
    def get_subject_urls(self, exam_type):
        """
        Get URLs for all subjects of a given exam type.
        
        Args:
            exam_type (str): Type of exam (e.g., 'gcse', 'a-level')
            
        Returns:
            dict: Dictionary mapping subject names to their URLs
        """
        # Get URL for this exam type
        exam_type_urls = self.get_exam_type_urls()
        normalized_exam_type = normalize_exam_type(exam_type)
        
        exam_type_url = None
        for exam_key, url in exam_type_urls.items():
            if normalized_exam_type.lower() == exam_key.lower() or normalized_exam_type.lower() in exam_key.lower():
                exam_type_url = url
                break
        
        if not exam_type_url:
            logger.warning(f"No URL found for exam type: {exam_type}")
            return {}
        
        subject_urls = {}
        
        try:
            # Get page content
            html_content = self._get_page(exam_type_url, use_selenium=True)
            
            if not html_content:
                logger.error(f"Failed to get content from {exam_type_url}")
                return {}
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for subject links
            # First try with subject containers/grids
            subject_containers = soup.select('.subjects, .subject-grid, .papers-list')
            
            subject_links = []
            if subject_containers:
                for container in subject_containers:
                    subject_links.extend(container.select('a'))
            else:
                # Fallback to all links
                all_links = soup.select('a')
                
                # Filter links that might be subject links
                for link in all_links:
                    href = link.get('href', '')
                    text = link.text.strip()
                    
                    # Skip empty links
                    if not href or not text:
                        continue
                    
                    # Check if it's a subject link
                    is_subject = False
                    for subject in self.subject_map.keys():
                        if subject in text.lower() or subject in href.lower():
                            is_subject = True
                            break
                    
                    if is_subject:
                        subject_links.append(link)
            
            logger.debug(f"Found {len(subject_links)} potential subject links")
            
            # Process each subject link
            for link in subject_links:
                href = link.get('href', '')
                text = link.text.strip()
                
                # Skip empty links
                if not href or not text:
                    continue
                
                # Skip non-subject links
                if text.lower() in ['home', 'about', 'contact', 'login', 'register']:
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
    
    def _get_exam_board_urls(self, subject_url):
        """
        Get URLs for all exam boards for a specific subject.
        
        Args:
            subject_url (str): URL of the subject page
            
        Returns:
            dict: Dictionary mapping exam board names to their URLs
        """
        logger.info(f"Getting exam board URLs from: {subject_url}")
        
        exam_board_urls = {}
        
        try:
            # Get page content
            html_content = self._get_page(subject_url, use_selenium=True)
            
            if not html_content:
                logger.error(f"Failed to get content from {subject_url}")
                return {}
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for exam board links or sections
            # First try with dedicated board sections
            board_sections = soup.select('.exam-board, .board-section, .board-filter')
            
            board_links = []
            if board_sections:
                for section in board_sections:
                    board_links.extend(section.select('a'))
            else:
                # Fallback to all links
                all_links = soup.select('a')
                
                # Filter links that might be exam board links
                for link in all_links:
                    href = link.get('href', '')
                    text = link.text.strip().lower()
                    
                    # Skip empty links
                    if not href or not text:
                        continue
                    
                    # Check if it's an exam board link
                    for board in self.exam_board_map.keys():
                        if board in text or board in href.lower():
                            board_links.append(link)
                            break
            
            logger.debug(f"Found {len(board_links)} potential board links")
            
            # Process each board link
            for link in board_links:
                href = link.get('href', '')
                text = link.text.strip().lower()
                
                # Skip empty links
                if not href or not text:
                    continue
                
                # Determine board name
                board_name = None
                for board_key, board_value in self.exam_board_map.items():
                    if board_key in text or board_key in href.lower():
                        board_name = board_value
                        break
                
                # If board name not identified, use text as name
                if not board_name:
                    board_name = text.title()
                
                # Create full URL if needed
                if href.startswith('/'):
                    board_url = urljoin(self.base_url, href)
                elif not href.startswith(('http://', 'https://')):
                    board_url = urljoin(self.base_url, '/' + href)
                else:
                    board_url = href
                
                exam_board_urls[board_name] = board_url
            
            # If no board links found, check if the subject page shows papers directly
            if not exam_board_urls:
                # Try to find board info in page content
                page_text = soup.get_text().lower()
                url_lower = subject_url.lower()
                
                for board_key, board_value in self.exam_board_map.items():
                    if board_key in url_lower or board_key in page_text:
                        # This page is for a specific board
                        exam_board_urls[board_value] = subject_url
                        break
                
                # If still no board identified, use "Unknown"
                if not exam_board_urls:
                    # Check if the page has PDFs - might be a direct papers page
                    pdf_links = soup.select('a[href$=".pdf"]')
                    if pdf_links:
                        exam_board_urls["Unknown"] = subject_url
            
            logger.info(f"Found {len(exam_board_urls)} exam board URLs")
            return exam_board_urls
            
        except Exception as e:
            logger.error(f"Error fetching exam board URLs: {e}", exc_info=True)
            return {}
    
    def _extract_papers_from_page(self, page_url, board_name, subject, exam_type, year_from=2021):
        """
        Extract papers from a page.
        
        Args:
            page_url (str): URL of the page
            board_name (str): Name of the exam board
            subject (str): Subject name
            exam_type (str): Exam type
            year_from (int): Year to start from
            
        Returns:
            list: List of paper data dictionaries
        """
        logger.info(f"Extracting papers from: {page_url}")
        
        papers = []
        
        try:
            # Get page content
            html_content = self._get_page(page_url, use_selenium=True)
            
            if not html_content:
                logger.error(f"Failed to get content from {page_url}")
                return []
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for paper links
            paper_links = []
            
            # First try with direct PDF links
            pdf_links = soup.select('a[href$=".pdf"]')
            paper_links.extend(pdf_links)
            
            # If no direct PDF links, try links that might lead to papers
            if not paper_links:
                all_links = soup.select('a')
                
                # Filter links that might be paper links
                for link in all_links:
                    href = link.get('href', '')
                    text = link.text.strip().lower()
                    
                    # Skip empty links
                    if not href or not text:
                        continue
                    
                    # Check if it's a paper link
                    if any(term in text or term in href.lower() for term in 
                           ['paper', 'exam', 'question', 'mark scheme']):
                        paper_links.append(link)
            
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
                
                # Skip non-PDF links
                if not paper_url.lower().endswith('.pdf'):
                    continue
                
                # Extract paper metadata
                
                # 1. Extract year
                year_match = re.search(r'20(\d{2})', text + ' ' + href)
                year = int('20' + year_match.group(1)) if year_match else None
                
                # Skip papers older than year_from
                if year and year < year_from:
                    logger.debug(f"Skipping paper from {year} (earlier than {year_from}): {text}")
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
                
                # Build paper data
                paper_data = self._build_paper_data(
                    exam_board=board_name,
                    exam_type=exam_type,
                    subject=subject,
                    year=year or 2021,  # Default if year not found
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
            logger.warning("Both subject and exam_type are required for TestTeach scraper")
            return []
            
        logger.info(f"Scraping TestTeach papers for {subject} ({exam_type})")
        
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
        
        # Get exam board URLs for this subject
        board_urls = self._get_exam_board_urls(matching_subject_url)
        
        if not board_urls:
            logger.warning(f"No exam board URLs found for {normalized_subject}")
            # Try using the subject URL directly
            papers = self._extract_papers_from_page(
                matching_subject_url, "Unknown", normalized_subject, 
                normalized_exam_type, year_from
            )
            all_papers.extend(papers)
        else:
            # Get papers from each board URL
            for board_name, board_url in board_urls.items():
                try:
                    board_papers = self._extract_papers_from_page(
                        board_url, board_name, normalized_subject, 
                        normalized_exam_type, year_from
                    )
                    all_papers.extend(board_papers)
                    
                except Exception as e:
                    logger.error(f"Error processing board URL {board_url}: {e}", exc_info=True)
        
        logger.info(f"Scraped {len(all_papers)} papers for {subject} from TestTeach")
        return all_papers
    
    def scrape_topics(self, subject=None, exam_type=None):
        """
        TestTeach doesn't provide detailed topic lists, only past papers.
        This is a placeholder implementation returning an empty list.
        
        Args:
            subject (str, optional): Subject name to scrape topics for
            exam_type (str, optional): Exam type to scrape topics for
            
        Returns:
            list: Empty list (no topics available)
        """
        logger.info(f"TestTeach doesn't provide topic lists, only past papers.")
        return []
