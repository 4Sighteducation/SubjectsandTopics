"""
RevisionWorld Scraper module for UK Exam Board Topic List Scraper.

This module handles scraping exam papers from RevisionWorld.com.
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
    normalize_exam_type
)

logger = get_logger()

class RevisionWorldScraper(BaseScraper):
    """
    Scraper for RevisionWorld.com exam papers.
    
    This class handles scraping, parsing, and downloading exam papers
    from RevisionWorld.com.
    """
    
    def __init__(self, output_dir="data", debug=False):
        """
        Initialize the RevisionWorld scraper.
        
        Args:
            output_dir (str): Base directory for downloaded files
            debug (bool): Enable debug mode (headful browser, more logs)
        """
        # Initialize with proper parameters for BaseScraper
        super().__init__(
            name="RevisionWorld",
            base_url="https://revisionworld.com",
            headless=not debug,
            delay=1.0,
            output_dir=output_dir
        )
        
        # The site seems to have rebranded to revision science for science subjects
        self.revision_science_base_url = "https://revisionscience.com"
        self.gcse_past_papers_url = f"{self.base_url}/gcse-revision/gcse-exam-past-papers"
        self.a_level_past_papers_url = f"{self.base_url}/a-level-revision/a-level-exam-past-papers"
        self.science_gcse_past_papers_url = f"{self.revision_science_base_url}/gcse-revision/gcse-exam-past-papers"
        
        # Map RevisionWorld subjects to our standardized subject names
        self.subject_map = {
            "biology": "Biology",
            "business (including economics)": "Business Studies",
            "chemistry": "Chemistry",
            "combined science": "Combined Science",
            "computer science": "Computer Science",
            "design and technology": "Design and Technology",
            "drama": "Drama",
            "english language": "English Language",
            "english literature": "English Literature",
            "food preparation and nutrition": "Food Preparation and Nutrition",
            "french": "French",
            "geography": "Geography",
            "german": "German",
            "history": "History",
            # Add more mappings as needed
        }
        
        # Mapping between exam boards as they appear on RevisionWorld and our standardized names
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
            url = self.gcse_past_papers_url
        elif exam_type.lower() in ['a-level', 'a level', 'alevel']:
            url = self.a_level_past_papers_url
        else:
            logger.warning(f"Unsupported exam type: {exam_type} for RevisionWorld")
            return {}
        
        subject_urls = {}
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract all links on the page
            all_links = soup.select('a')
            
            # Find subject links by common subject names
            common_subjects = [
                "maths", "mathematics", "english", "science", "history", "geography", 
                "biology", "chemistry", "physics", "combined science", "computer science",
                "french", "german", "spanish", "religious studies"
            ]
            
            subject_links = []
            for link in all_links:
                href = link.get('href', '')
                text = link.text.strip().lower()
                
                # Skip empty links
                if not href or not text:
                    continue
                    
                # Check if link text contains a common subject name
                if any(subj in text for subj in common_subjects):
                    # Check if it might be a past paper link
                    if "past" in href.lower() or "paper" in href.lower() or "exam" in href.lower():
                        subject_links.append(link)
            
            logger.debug(f"Found {len(subject_links)} potential subject links")
            
            for link in subject_links:
                subject_name = link.text.strip()
                subject_url = urljoin(self.base_url, link['href'])
                
                # Skip non-subject links
                if not subject_name or subject_name.lower() in ['home', 'gcse revision', 'a level revision']:
                    continue
                
                normalized_name = normalize_subject_name(subject_name)
                subject_urls[normalized_name] = subject_url
            
            logger.info(f"Found {len(subject_urls)} subject URLs")
            return subject_urls
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching subject URLs: {e}")
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
        
        # Check if we need to use RevisionScience URL
        base_url = self.revision_science_base_url if "revisionscience.com" in subject_url else self.base_url
        
        exam_board_urls = {}
        
        try:
            response = requests.get(subject_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find links to exam board pages
            all_links = soup.select('a')
            
            # Common exam board names
            exam_boards = ["aqa", "edexcel", "ocr", "wjec", "ccea", "sqa", "cie", "eduqas"]
            
            for link in all_links:
                href = link.get('href', '')
                text = link.text.strip().lower()
                
                # Skip empty links
                if not href or not text:
                    continue
                
                # Look for links that contain exam board names
                if any(board in text or board in href.lower() for board in exam_boards):
                    # Filter out irrelevant links
                    if "past-papers" in href.lower() and not exam_board_urls.get(text):
                        exam_board_urls[text] = urljoin(base_url, href)
            
            logger.info(f"Found {len(exam_board_urls)} exam board URLs")
            return exam_board_urls
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching exam board URLs: {e}")
            return {}
    
    def _get_papers_from_board_page(self, board_url, board_name, subject, exam_type, year_from):
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
        
        # Check if we need to use RevisionScience URL
        base_url = self.revision_science_base_url if "revisionscience.com" in board_url else self.base_url
        
        papers = []
        
        try:
            response = requests.get(board_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for direct PDF links
            pdf_links = soup.select('a[href$=".pdf"]')
            
            # If no direct PDF links, try alternative methods
            if not pdf_links:
                # Look for all links
                all_links = soup.select('a')
                
                # Check for links that end with .pdf
                pdf_links = [link for link in all_links if link.get('href', '').lower().endswith('.pdf')]
                
                # Check for links that contain pdf in the URL
                if not pdf_links:
                    pdf_links = [link for link in all_links if 'pdf' in link.get('href', '').lower()]
                
                # Look for links to exam papers without PDF extension
                if not pdf_links:
                    pdf_links = []
                    for link in all_links:
                        href = link.get('href', '').lower()
                        text = link.text.strip().lower()
                        # Use heuristics to identify paper links
                        if any(term in text for term in ['paper', 'exam', 'past', 'question']) and len(text) > 5:
                            # Filter out navigation links
                            if not any(term in href for term in ['subject', 'topics', 'revision', 'home', 'about']):
                                pdf_links.append(link)
            
            logger.debug(f"Found {len(pdf_links)} potential paper links")
            
            # Process each PDF link
            for link in pdf_links:
                paper_url = urljoin(base_url, link['href'])
                paper_name = link.text.strip()
                
                # Skip empty names or very short ones (likely not papers)
                if len(paper_name) < 5:
                    continue
                
                # Try to identify the exam board if not provided
                exam_board = "Unknown"
                if board_name:
                    for board in self.exam_board_map.keys():
                        if board in board_name.lower():
                            exam_board = self.exam_board_map[board]
                            break
                
                # Try to extract metadata from the paper name
                year_match = re.search(r'(20\d\d)', paper_name)
                year = int(year_match.group(1)) if year_match else None
                
                # Skip papers older than year_from
                if year and year < year_from:
                    logger.debug(f"Skipping paper from {year} (earlier than {year_from}): {paper_name}")
                    continue
                
                # Check for document type
                doc_type = "Question Paper"
                if any(marker in paper_name.lower() for marker in ["mark scheme", "marking", "ms"]):
                    doc_type = "Mark Scheme"
                elif any(marker in paper_name.lower() for marker in ["examiner", "report", "er"]):
                    doc_type = "Examiner Report"
                
                # Extract season information
                season = "Summer"  # Default to summer
                for season_name in ["Summer", "Winter", "January", "June", "November"]:
                    if season_name.lower() in paper_name.lower():
                        season = season_name
                        break
                
                # Extract paper number if available
                paper_number_match = re.search(r'paper\s*(\d+)', paper_name.lower())
                paper_number = int(paper_number_match.group(1)) if paper_number_match else None
                
                # Create paper data dictionary
                paper_data = self._build_paper_data(
                    exam_board=exam_board, 
                    exam_type=exam_type,
                    subject=subject,
                    year=year or 2021,  # Default to current year if no year found
                    season=season,
                    title=paper_name,
                    paper_number=paper_number or 1,  # Default to paper 1 if no number found
                    document_type=doc_type,
                    specification_code="",  # Not available from RevisionWorld
                    file_path=""  # Will be filled in after download
                )
                
                # Add URL for download
                paper_data["URL"] = paper_url
                
                # Download the paper
                output_path = self._download_paper(paper_data)
                if output_path:
                    paper_data["Paper"] = output_path  # Use the standard field name
                    papers.append(paper_data)
                    logger.debug(f"Added paper: {paper_name}")
                
            return papers
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error scraping papers from board page: {e}")
            return []
    
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
            logger.warning("Both subject and exam_type are required for RevisionWorld scraper")
            return []
            
        logger.info(f"Scraping RevisionWorld papers for {subject} ({exam_type})")
        
        # Normalize inputs
        normalized_subject = normalize_subject_name(subject)
        normalized_exam_type = normalize_exam_type(exam_type)
        
        # Try both RevisionWorld and RevisionScience URLs
        all_papers = []
        
        # Get subject URLs for this exam type
        subject_urls = self.get_subject_urls(normalized_exam_type)
        
        # Find URLs for our target subject
        matching_subject_urls = []
        for subj, url in subject_urls.items():
            if (normalized_subject in subj.lower() or 
                subj.lower() in normalized_subject or 
                any(common in subj.lower() for common in ['biology', 'chemistry', 'physics', 'science'] 
                    if common in normalized_subject)):
                matching_subject_urls.append(url)
        
        if not matching_subject_urls:
            # Try science subjects from RevisionScience specifically
            if any(subject in normalized_subject for subject in ['biology', 'chemistry', 'physics', 'science']):
                # Try both direct mapping and searching
                if normalized_exam_type.lower() == 'gcse':
                    science_url = f"{self.revision_science_base_url}/gcse-revision/{normalized_subject.lower()}/{normalized_subject.lower()}-gcse-past-papers"
                    matching_subject_urls.append(science_url)
            else:
                logger.warning(f"Could not find URL for {subject} in RevisionWorld")
                return []
        
        # Process each matching subject URL
        for subject_url in matching_subject_urls:
            try:
                # Get exam board URLs
                board_urls = self._get_exam_board_urls(subject_url)
                
                if not board_urls:
                    logger.warning(f"No exam board links found on {subject_url}")
                    continue
                
                # Get papers from each board page
                for board_name, board_url in board_urls.items():
                    board_papers = self._get_papers_from_board_page(
                        board_url, board_name, normalized_subject, 
                        normalized_exam_type, year_from
                    )
                    all_papers.extend(board_papers)
                
            except Exception as e:
                logger.error(f"Error processing subject URL {subject_url}: {e}", exc_info=True)
        
        logger.info(f"Scraped {len(all_papers)} papers for {subject} from RevisionWorld/RevisionScience")
        return all_papers
    
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
        if not file_name.endswith('.pdf'):
            file_name += '.pdf'
        
        # Use the standard method from BaseScraper to download document
        subdir = os.path.join(
            exam_type,
            subject,
            str(year),
            season
        )
        
        return self._download_document(url, file_name, subdir, document_type)
    
    def scrape_topics(self, subject=None, exam_type=None):
        """
        RevisionWorld doesn't provide detailed topic lists, only past papers.
        This is a placeholder implementation returning an empty list.
        
        Args:
            subject (str, optional): Subject name to scrape topics for
            exam_type (str, optional): Exam type to scrape topics for
            
        Returns:
            list: Empty list (no topics available)
        """
        logger.info(f"RevisionWorld doesn't provide topic lists, only past papers.")
        return []
