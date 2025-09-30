"""
Base scraper class for UK exam boards.

This module provides the BaseScraper abstract class that all exam board scrapers must implement.
"""

import os
import time
import json
import random
import requests
from abc import ABC, abstractmethod
from datetime import datetime
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from utils.logger import get_logger
from utils.helpers import (
    sanitize_filename, ensure_directory, sanitize_text, download_file,
    normalize_subject_name, normalize_exam_type, random_delay
)

logger = get_logger()


class BaseScraper(ABC):
    """
    Abstract base class for exam board scrapers.
    
    This class provides common functionality for all exam board scrapers.
    Each exam board scraper must implement the abstract methods.
    """
    
    def __init__(self, name, base_url, headless=True, delay=1.0, output_dir="data/raw"):
        """
        Initialize the base scraper.
        
        Args:
            name (str): Name of the exam board
            base_url (str): Base URL for the exam board website
            headless (bool): Whether to run the browser in headless mode
            delay (float): Delay between requests in seconds
            output_dir (str): Directory to save raw scraped data
        """
        self.name = name
        self.base_url = base_url
        self.headless = headless
        self.delay = delay
        self.output_dir = os.path.join(output_dir, sanitize_filename(name))
        
        # Create output directories
        ensure_directory(self.output_dir)
        
        # Initialize session for requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        
        # Initialize Selenium WebDriver to None (will be created when needed)
        self.driver = None
    
    def _init_driver(self):
        """Initialize the Selenium WebDriver if not already initialized."""
        if self.driver is not None:
            return
        
        options = Options()
        if self.headless:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
        
        # Additional options to improve performance and stability
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-infobars')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(60)
            logger.debug("Selenium WebDriver initialized")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def close(self):
        """Close the scraper and release resources."""
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
        
        self.session.close()
        logger.debug(f"Closed {self.name} scraper")
    
    def _get_page(self, url, use_selenium=False, wait_for=None, retries=3):
        """
        Get a page using either requests or Selenium.
        
        Args:
            url (str): URL to fetch
            use_selenium (bool): Whether to use Selenium
            wait_for (tuple, optional): Tuple of (By, selector) to wait for
            retries (int): Number of retries
            
        Returns:
            str or None: HTML content or None if failed
        """
        for attempt in range(retries):
            try:
                if use_selenium:
                    self._init_driver()
                    self.driver.get(url)
                    
                    if wait_for:
                        by, selector = wait_for
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((by, selector))
                        )
                    
                    content = self.driver.page_source
                    logger.debug(f"Fetched {url} using Selenium")
                    return content
                else:
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    logger.debug(f"Fetched {url} using requests")
                    return response.text
                
            except (requests.exceptions.RequestException, TimeoutException, WebDriverException) as e:
                logger.warning(f"Attempt {attempt+1}/{retries} failed to fetch {url}: {e}")
                
                if attempt < retries - 1:
                    sleep_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
                    
            finally:
                # Respect rate limits
                random_delay(min_seconds=self.delay, max_seconds=self.delay * 2)
    
    def _get_json(self, url, retries=3):
        """
        Get JSON data from a URL.
        
        Args:
            url (str): URL to fetch
            retries (int): Number of retries
            
        Returns:
            dict or None: JSON data or None if failed
        """
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.json()
                
            except (requests.exceptions.RequestException, ValueError) as e:
                logger.warning(f"Attempt {attempt+1}/{retries} failed to fetch JSON from {url}: {e}")
                
                if attempt < retries - 1:
                    sleep_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Failed to fetch JSON from {url} after {retries} attempts")
                    return None
                    
            finally:
                # Respect rate limits
                random_delay(min_seconds=self.delay, max_seconds=self.delay * 2)
    
    def _save_raw_data(self, data, filename, subdir=None):
        """
        Save raw data to a file.
        
        Args:
            data: Data to save (must be JSON serializable)
            filename (str): Filename to save as
            subdir (str, optional): Subdirectory within the output directory
            
        Returns:
            str: Path to the saved file
        """
        # Determine the output directory
        output_dir = self.output_dir
        if subdir:
            output_dir = os.path.join(output_dir, subdir)
        
        # Ensure directory exists
        ensure_directory(output_dir)
        
        # Sanitize filename
        sanitized_filename = sanitize_filename(filename)
        
        # Add timestamp to ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        if not sanitized_filename.endswith('.json'):
            sanitized_filename = f"{sanitized_filename}_{timestamp}.json"
        else:
            sanitized_filename = sanitized_filename.replace('.json', f'_{timestamp}.json')
        
        # Full path to save file
        filepath = os.path.join(output_dir, sanitized_filename)
        
        # Save data
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Saved raw data to {filepath}")
        return filepath
    
    def _download_document(self, url, filename, subdir=None, document_type="question_paper"):
        """
        Download a document.
        
        Args:
            url (str): URL to download from
            filename (str): Filename to save as
            subdir (str, optional): Subdirectory within the output directory
            document_type (str): Type of document (question_paper, mark_scheme, examiner_report)
            
        Returns:
            str or None: Path to the downloaded file or None if download failed
        """
        # Determine the output directory
        output_dir = self.output_dir
        if subdir:
            output_dir = os.path.join(output_dir, subdir)
        
        # Add document type to path
        output_dir = os.path.join(output_dir, document_type)
        
        # Ensure directory exists
        ensure_directory(output_dir)
        
        # Sanitize filename
        sanitized_filename = sanitize_filename(filename)
        
        # Add file extension if missing
        if not sanitized_filename.endswith(('.pdf', '.doc', '.docx')):
            sanitized_filename = f"{sanitized_filename}.pdf"
        
        # Full path to save file
        filepath = os.path.join(output_dir, sanitized_filename)
        
        # Download file
        success = download_file(url, filepath, session=self.session)
        
        if success:
            return filepath
        else:
            return None
    
    def _extract_topics_from_html(self, html, selector, exam_type=None, subject=None):
        """
        Extract topics from HTML content.
        
        This is a placeholder method that should be implemented by subclasses
        to extract topics from HTML content specific to each exam board.
        
        Args:
            html (str): HTML content
            selector (str): CSS selector to find topics
            exam_type (str, optional): Exam type to filter by
            subject (str, optional): Subject to filter by
            
        Returns:
            list: List of topic data dictionaries
        """
        # This is a base implementation that should be overridden by subclasses
        logger.warning("_extract_topics_from_html is not implemented in the base class")
        return []
    
    def _build_topic_data(self, exam_board, exam_type, subject, module, topic, sub_topic=None):
        """
        Build a standardized topic data dictionary.
        
        Args:
            exam_board (str): Name of the exam board
            exam_type (str): Type of exam (GCSE, A-Level, etc.)
            subject (str): Subject name
            module (str): Module name
            topic (str): Topic name
            sub_topic (str, list, optional): Sub-topic name or list of sub-topic names
            
        Returns:
            dict: Topic data dictionary
        """
        data = {
            "Exam Board": exam_board,
            "Exam Type": exam_type,
            "Subject": subject,
            "Module": module,
            "Topic": topic,
        }
        
        if sub_topic:
            # Handle both single string subtopics and lists of subtopics
            data["Sub Topic"] = sub_topic
        
        return data
    
    def _build_paper_data(self, exam_board, exam_type, subject, year, season, 
                         title, paper_number, document_type, specification_code, file_path):
        """
        Build a standardized paper data dictionary.
        
        Args:
            exam_board (str): Name of the exam board
            exam_type (str): Type of exam (GCSE, A-Level, etc.)
            subject (str): Subject name
            year (int): Year of the exam
            season (str): Season of the exam (Summer, Winter, etc.)
            title (str): Title of the paper
            paper_number (int): Paper number
            document_type (str): Type of document (Question Paper, Mark Scheme, Examiner Report)
            specification_code (str): Specification code
            file_path (str): Path to the downloaded file
            
        Returns:
            dict: Paper data dictionary
        """
        return {
            "Year": year,
            "Exam Type": exam_type,
            "Subject": subject,
            "Exam Board": exam_board,
            "Title": title,
            "Season": season,
            "Paper Number": paper_number,
            "Document Type": document_type,
            "Specification Code": specification_code,
            "Paper": file_path
        }
    
    @abstractmethod
    def scrape_topics(self, subject=None, exam_type=None):
        """
        Scrape topic lists from the exam board website.
        
        Args:
            subject (str, optional): Subject to scrape topics for
            exam_type (str, optional): Exam type to scrape topics for
            
        Returns:
            list: List of topic data dictionaries
        """
        pass
    
    @abstractmethod
    def scrape_papers(self, subject=None, exam_type=None, year_from=2021):
        """
        Scrape exam papers from the exam board website.
        
        Args:
            subject (str, optional): Subject to scrape papers for
            exam_type (str, optional): Exam type to scrape papers for
            year_from (int): Year to start scraping papers from
            
        Returns:
            list: List of paper data dictionaries
        """
        pass
