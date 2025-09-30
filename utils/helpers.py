"""
Helper utilities for the UK Exam Board Topic List Scraper.
"""

import os
import re
import json
import time
import random
import requests
import hashlib
from pathlib import Path
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

from utils.logger import get_logger

logger = get_logger()


def sanitize_filename(filename):
    """
    Sanitize a string to be used as a filename.
    
    Args:
        filename (str): The original filename
        
    Returns:
        str: Sanitized filename
    """
    # Replace illegal characters with underscores
    illegal_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(illegal_chars, '_', filename)
    
    # Limit length to avoid issues with max path length
    if len(sanitized) > 200:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:195] + ext
    
    return sanitized


def ensure_directory(directory):
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory (str): Directory path
    """
    os.makedirs(directory, exist_ok=True)


def sanitize_text(text):
    """
    Clean up text by removing extra whitespace, newlines, etc.
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Replace multiple whitespace with a single space
    text = re.sub(r'\s+', ' ', text)
    # Replace non-breaking spaces with regular spaces
    text = text.replace('\xa0', ' ')
    # Trim leading/trailing whitespace
    text = text.strip()
    
    return text


def download_file(url, output_path, session=None, retries=3, timeout=60):
    """
    Download a file from a URL to a local path with retries.
    
    Args:
        url (str): URL of the file to download
        output_path (str): Local path to save the file
        session (requests.Session, optional): Existing session to use
        retries (int): Number of retry attempts
        timeout (int): Request timeout in seconds
        
    Returns:
        bool: True if download successful, False otherwise
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Use provided session or create a new one
    s = session or requests.Session()
    
    # Try to download with retries
    for attempt in range(retries):
        try:
            # Stream the response to handle large files
            response = s.get(url, stream=True, timeout=timeout)
            response.raise_for_status()
            
            # Save the file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded file from {url} to {output_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Download attempt {attempt+1}/{retries} failed: {e}")
            
            # Exponential backoff
            if attempt < retries - 1:
                sleep_time = 2 ** attempt + random.uniform(0, 1)
                logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
    
    logger.error(f"Failed to download {url} after {retries} attempts")
    return False


def extract_pdf_text(pdf_path):
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text or empty string if extraction fails
    """
    try:
        import PyPDF2
        
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n"
        
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
        return ""


from utils.subjects import normalize_subject

def normalize_subject_name(subject):
    """
    Normalize subject names for consistent matching.
    
    This function now uses the more comprehensive subject normalization
    from the subjects module.
    
    Args:
        subject (str): Original subject name
        
    Returns:
        str: Normalized subject name
    """
    return normalize_subject(subject)


def normalize_exam_type(exam_type):
    """
    Normalize exam type for consistent matching.
    
    Args:
        exam_type (str): Original exam type
        
    Returns:
        str: Normalized exam type
    """
    if not exam_type:
        return ""
    
    # Convert to lowercase
    normalized = exam_type.lower()
    
    # Normalize common variations
    replacements = {
        "gcse": "gcse",
        "igcse": "gcse",
        "general certificate of secondary education": "gcse",
        "a level": "a-level",
        "a levels": "a-level",
        "a-levels": "a-level",
        "as level": "as-level",
        "as levels": "as-level",
        "as": "as-level",
        "gce": "a-level",
        "general certificate of education": "a-level",
        "advanced level": "a-level",
        "international baccalaureate": "ib",
        "ib diploma programme": "ib",
        "ib dp": "ib",
        "btec level 3": "btec-level-3",
        "btec level 2": "btec-level-2",
        "higher": "scottish-higher"
    }
    
    for old, new in replacements.items():
        if normalized == old or normalized.startswith(old + " "):
            normalized = normalized.replace(old, new, 1)
    
    return normalized.strip()


def save_json(data, filepath):
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save (must be JSON serializable)
        filepath (str): Path to save the JSON file
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Save with pretty formatting
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved JSON data to {filepath}")


def load_json(filepath):
    """
    Load data from a JSON file.
    
    Args:
        filepath (str): Path to the JSON file
        
    Returns:
        The loaded data or None if file doesn't exist or is invalid
    """
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {filepath}: {e}")
    
    return None


def get_file_hash(filepath):
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        filepath (str): Path to the file
        
    Returns:
        str: Hex digest of hash or empty string if file doesn't exist
    """
    if not os.path.exists(filepath):
        return ""
    
    try:
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {filepath}: {e}")
        return ""


def get_absolute_url(base_url, relative_url):
    """
    Convert a relative URL to an absolute URL.
    
    Args:
        base_url (str): The base URL
        relative_url (str): The relative URL
        
    Returns:
        str: Absolute URL
    """
    return urljoin(base_url, relative_url)


def extract_tables_from_html(html_content, url=""):
    """
    Extract tables from HTML content.
    
    Args:
        html_content (str): HTML content
        url (str, optional): URL for logging purposes
        
    Returns:
        list: List of tables as lists of lists
    """
    soup = BeautifulSoup(html_content, 'lxml')
    tables = []
    
    for table in soup.find_all('table'):
        current_table = []
        
        # Process the header row if it exists
        headers = []
        header_row = table.find('thead')
        if header_row:
            for th in header_row.find_all('th'):
                headers.append(sanitize_text(th.get_text()))
        
        if headers:
            current_table.append(headers)
        
        # Process the body rows
        for row in table.find_all('tr'):
            cells = []
            for cell in row.find_all(['td', 'th']):
                cells.append(sanitize_text(cell.get_text()))
            
            if cells and cells != headers:  # Skip if same as headers
                current_table.append(cells)
        
        if current_table:
            tables.append(current_table)
    
    logger.debug(f"Extracted {len(tables)} tables from HTML" + (f" at {url}" if url else ""))
    return tables


def random_delay(min_seconds=1, max_seconds=3):
    """
    Introduce a random delay to avoid overloading servers.
    
    Args:
        min_seconds (float): Minimum delay in seconds
        max_seconds (float): Maximum delay in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
