"""
MMERevise Scraper module for UK Exam Board Topic List Scraper.

This module handles scraping exam papers from MMERevise.co.uk.
"""

import os
import re
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

class MMEReviseScraper(BaseScraper):
    """
    Scraper for MMERevise.co.uk exam papers.
    
    This class handles scraping, parsing, and downloading exam papers
    from MMERevise.co.uk.
    """
    
    def __init__(self, output_dir="data", debug=False):
        """
        Initialize the MMERevise scraper.
        
        Args:
            output_dir (str): Base directory for downloaded files
            debug (bool): Enable debug mode (headful browser, more logs)
        """
        # Initialize with proper parameters for BaseScraper
        super().__init__(
            name="MMERevise",
            base_url="https://www.mmerevise.co.uk",
            headless=not debug,
            delay=1.5,  # Slightly higher delay to be respectful to their server
            output_dir=output_dir
        )
        
        # Define main resource paths - corrected to match current site structure
        self.gcse_papers_url = f"{self.base_url}/gcse/"
        self.a_level_papers_url = f"{self.base_url}/a-level/"
        
        # Map MMERevise subjects to our standardized subject names
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
            "business studies": "Business Studies",
            "economics": "Economics",
            "design and technology": "Design and Technology",
            "french": "French",
            "german": "German",
            "spanish": "Spanish",
            "religious studies": "Religious Studies",
            # Add more mappings as needed
        }
        
        # Mapping between exam boards as they appear on MMERevise and our standardized names
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
            url = self.gcse_papers_url
        elif exam_type.lower() in ['a-level', 'a level', 'alevel']:
            url = self.a_level_papers_url
        else:
            logger.warning(f"Unsupported exam type: {exam_type} for MMERevise")
            return {}
        
        subject_urls = {}
        
        try:
            # First try with direct HTTP request
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            html_content = response.text
            
            # If that fails, try with Selenium
            if not html_content or "past papers" not in html_content.lower():
                html_content = self._get_page(url, use_selenium=True)
            
            if not html_content:
                logger.error(f"Failed to get content from {url}")
                return {}
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try different selectors to find subject links
            # 1. Try main navigation
            subjects_container = soup.select('.subjects-container, .subject-list, .resources-list')
            
            if subjects_container:
                # Use the first matching container
                links = subjects_container[0].select('a')
            else:
                # Fallback to all links on the page
                links = soup.select('a')
                
                # Filter links that might be subject links
                links = [link for link in links if 
                         link.get('href') and 
                         ('papers' in link.get('href').lower() or 
                          'revision' in link.get('href').lower()) and
                         link.text.strip()]
            
            logger.debug(f"Found {len(links)} potential subject links")
            
            for link in links:
                subject_name = link.text.strip()
                href = link.get('href')
                
                # Skip empty names or hrefs
                if not subject_name or not href:
                    continue
                
                # Skip navigation or non-subject links
                if subject_name.lower() in ['home', 'papers', 'revision', 'resources', 'login', 'sign up']:
                    continue
                
                # Normalize subject name
                normalized_name = normalize_subject_name(subject_name)
                
                # Get standardized name if available
                for key, value in self.subject_map.items():
                    if key in normalized_name.lower():
                        normalized_name = value
                        break
                
                # Create full URL if it's a relative path
                if href.startswith('/'):
                    subject_url = urljoin(self.base_url, href)
                elif not href.startswith(('http://', 'https://')):
                    subject_url = urljoin(self.base_url, '/' + href)
                else:
                    subject_url = href
                
                subject_urls[normalized_name] = subject_url
            
            logger.info(f"Found {len(subject_urls)} subject URLs for {exam_type}")
            return subject_urls
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching subject URLs: {e}")
            return {}
    
    def _get_exam_board_urls(self, subject_url, exam_type):
        """
        Get URLs for all exam boards for a specific subject.
        
        Args:
            subject_url (str): URL of the subject page
            exam_type (str): Type of exam (e.g., 'gcse', 'a-level')
            
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
            
            # Find links to exam board pages
            board_links = []
            
            # Try different approaches to find exam board links
            
            # 1. Look for exam board sections or filters
            board_sections = soup.select('.exam-board, .board-filter, .filter-board')
            if board_sections:
                for section in board_sections:
                    board_links.extend(section.select('a'))
            
            # 2. Look for links containing exam board names
            if not board_links:
                all_links = soup.select('a')
                for link in all_links:
                    href = link.get('href', '')
                    text = link.text.strip().lower()
                    
                    # Skip empty links
                    if not href or not text:
                        continue
                    
                    # Check if link contains exam board name
                    is_board_link = False
                    for board in self.exam_board_map:
                        if board in text or board in href.lower():
                            is_board_link = True
                            break
                    
                    if is_board_link:
                        board_links.append(link)
            
            # 3. If still no board links, the subject page might already be board-specific
            # In this case, try to identify the board from the URL or page content
            if not board_links:
                page_text = soup.get_text().lower()
                url_lower = subject_url.lower()
                
                for board_key, board_name in self.exam_board_map.items():
                    if board_key in url_lower or board_key in page_text:
                        # This page is for a specific board
                        exam_board_urls[board_name] = subject_url
                        break
            
            # Process board links
            for link in board_links:
                href = link.get('href', '')
                text = link.text.strip().lower()
                
                # Skip empty links
                if not href or not text:
                    continue
                
                # Identify board name from link text or href
                board_name = None
                for board_key, board_value in self.exam_board_map.items():
                    if board_key in text or board_key in href.lower():
                        board_name = board_value
                        break
                
                # If board name not identified, use the text as board name
                if not board_name:
                    board_name = text.capitalize()
                
                # Create full URL
                if href.startswith('/'):
                    board_url = urljoin(self.base_url, href)
                elif not href.startswith(('http://', 'https://')):
                    board_url = urljoin(self.base_url, '/' + href)
                else:
                    board_url = href
                
                # Add to board URLs
                exam_board_urls[board_name] = board_url
            
            # If no exam board URLs found, use the subject URL itself
            if not exam_board_urls:
                logger.warning(f"No exam board links found on {subject_url}. Using subject URL as fallback.")
                exam_board_urls["Unknown"] = subject_url
            
            logger.info(f"Found {len(exam_board_urls)} exam board URLs")
            return exam_board_urls
            
        except Exception as e:
            logger.error(f"Error fetching exam board URLs: {e}", exc_info=True)
            return {}
    
    def _get_papers_from_board_page(self, board_url, board_name, subject, exam_type, year_from=2021):
        """
        Extract papers from an exam board page.
        
        Args:
            board_url (str): URL of the exam board page
            board_name (str): Name of the exam board
            subject (str): Subject name
            exam_type (str): Exam type
            year_from (int): Year to start from
            
        Returns:
            list: List of paper data dictionaries
        """
        logger.info(f"Getting papers from board page: {board_url}")
        
        papers = []
        
        try:
            # Get page content
            html_content = self._get_page(board_url, use_selenium=True)
            
            if not html_content:
                logger.error(f"Failed to get content from {board_url}")
                return []
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for paper links
            # First try more specific selectors for papers
            paper_containers = soup.select('.past-papers, .papers-container, .resources-list')
            
            if paper_containers:
                paper_links = []
                for container in paper_containers:
                    paper_links.extend(container.select('a'))
            else:
                # Fallback to checking all links
                paper_links = soup.select('a[href$=".pdf"]')
                
                # If still no links, check for links that contain common paper indicators
                if not paper_links:
                    all_links = soup.select('a')
                    paper_links = [link for link in all_links if 
                                  any(term in link.get('href', '').lower() or term in link.text.lower() 
                                     for term in ['paper', 'exam', 'past', 'question', 'mark scheme', 'ms'])]
            
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
                
                # Extract paper metadata from link text or URL
                
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
            logger.error(f"Error scraping papers from board page: {e}", exc_info=True)
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
            logger.warning("Both subject and exam_type are required for MMERevise scraper")
            return []
            
        logger.info(f"Scraping MMERevise papers for {subject} ({exam_type})")
        
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
        board_urls = self._get_exam_board_urls(matching_subject_url, normalized_exam_type)
        
        if not board_urls:
            logger.warning(f"No exam board URLs found for {normalized_subject}")
            return []
        
        # Get papers from each board page
        for board_name, board_url in board_urls.items():
            try:
                board_papers = self._get_papers_from_board_page(
                    board_url, board_name, normalized_subject, 
                    normalized_exam_type, year_from
                )
                all_papers.extend(board_papers)
                
            except Exception as e:
                logger.error(f"Error processing board URL {board_url}: {e}", exc_info=True)
        
        logger.info(f"Scraped {len(all_papers)} papers for {subject} from MMERevise")
        return all_papers
    
    def scrape_topics(self, subject=None, exam_type=None):
        """
        MMERevise doesn't provide detailed topic lists, only past papers.
        This is a placeholder implementation returning an empty list.
        
        Args:
            subject (str, optional): Subject name to scrape topics for
            exam_type (str, optional): Exam type to scrape topics for
            
        Returns:
            list: Empty list (no topics available)
        """
        logger.info(f"MMERevise doesn't provide topic lists, only past papers.")
        return []
