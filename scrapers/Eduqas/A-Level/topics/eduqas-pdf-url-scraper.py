"""
Eduqas PDF URL Scraper

Scrapes the Eduqas qualifications website to find specification PDF URLs
for all subjects listed in the qualifications file.
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Setup logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EduqasPDFURLScraper:
    """Scraper to find specification PDF URLs from Eduqas website."""
    
    BASE_URL = "https://www.eduqas.co.uk"
    QUALIFICATIONS_URL = "https://www.eduqas.co.uk/ed/qualifications/"
    
    def __init__(self, headless=True):
        """Initialize the scraper."""
        self.headless = headless
        self.driver = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def _init_driver(self):
        """Initialize Selenium WebDriver."""
        if self.driver is not None:
            return
            
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            logger.info("WebDriver initialized")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def _close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def parse_qualifications_file(self, file_path: str) -> List[Tuple[str, str]]:
        """
        Parse the qualifications markdown file to extract subjects and levels.
        
        Returns list of tuples: (subject_name, level)
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return []
        
        qualifications = []
        current_section = None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Detect section headers
                if 'GCSE' in line.upper() and 'Eduqas Qualifications' in line:
                    current_section = 'GCSE'
                    continue
                elif 'ALEVEL' in line.upper() or 'A-LEVEL' in line.upper():
                    current_section = 'A-Level'
                    continue
                
                # Skip empty lines and section headers
                if not line or line.startswith('#'):
                    continue
                
                # Parse subject lines (format: "Subject Name - GCSE / A" or "Subject Name = GCSE / A" or "Subject Name - GCSE" or "Subject Name - A")
                # Handle both dash and equals sign separators
                separator = None
                if ' - ' in line:
                    separator = ' - '
                elif ' = ' in line:
                    separator = ' = '
                
                if separator:
                    parts = line.split(separator)
                    if len(parts) >= 2:
                        subject = parts[0].strip()
                        level_part = parts[1].strip()
                        
                        # Handle special cases
                        if subject == "A Geography":
                            qualifications.append(("Geography A", "GCSE"))
                        elif subject == "B Geography":
                            qualifications.append(("Geography B", "GCSE"))
                        elif subject == "Drama (and Theatre)":
                            # Handle "GCSE / A" for Drama
                            if level_part == "GCSE / A":
                                qualifications.append(("Drama", "GCSE"))
                                qualifications.append(("Drama", "A-Level"))
                            else:
                                qualifications.append(("Drama", level_part))
                        elif "Extended Project" in subject:
                            # Skip Extended Project for now
                            continue
                        else:
                            # Determine level
                            if level_part == "GCSE":
                                qualifications.append((subject, "GCSE"))
                            elif level_part == "A":
                                qualifications.append((subject, "A-Level"))
                            elif level_part == "GCSE / A":
                                qualifications.append((subject, "GCSE"))
                                qualifications.append((subject, "A-Level"))
                            elif current_section:
                                # Use current section if level not specified
                                qualifications.append((subject, current_section))
        
        logger.info(f"Parsed {len(qualifications)} qualifications from file")
        return qualifications
    
    def _normalize_subject_name(self, subject: str) -> str:
        """Normalize subject name for URL matching."""
        # Convert to lowercase and replace spaces/special chars
        normalized = subject.lower()
        normalized = normalized.replace(' ', '-')
        normalized = normalized.replace('&', 'and')
        normalized = normalized.replace('(', '').replace(')', '')
        normalized = normalized.replace('and', 'and')
        return normalized
    
    def _guess_pdf_url_pattern(self, subject: str, level: str) -> Optional[str]:
        """
        Try to guess PDF URL based on known patterns.
        This is a fallback method when scraping fails.
        
        Patterns observed:
        - GCSE: eduqas-gcse-{subject}-spec-from-{year}-{date}.pdf
        - A-Level: eduqas-a-level-{subject}-spec-from-{year}-e-{date}.pdf
        - A-Level (short): eduqas-a-{subject}-spec-from-{year}.pdf
        - Geography variants: gcse-geog-{variant}-spec.pdf
        """
        # Note: This won't work perfectly because the hash in the URL is unique
        # But we can document the pattern for manual checking
        normalized = self._normalize_subject_name(subject)
        
        # Handle special cases
        if subject == "Geography A":
            normalized = "geography-a"
        elif subject == "Geography B":
            normalized = "geography-b"
        elif "Geography" in subject and level == "GCSE":
            normalized = "geography-a"  # Default to A
        
        if level == "GCSE":
            pattern = f"eduqas-gcse-{normalized}-spec-from-2016"
        elif level == "A-Level":
            # Try both patterns
            pattern = f"eduqas-a-level-{normalized}-spec-from-2015"
            if len(normalized.split('-')) <= 2:  # Short subject names might use shorter pattern
                pattern_alt = f"eduqas-a-{normalized}-spec-from-2015"
        else:
            return None
        
        # We can't guess the hash, but we can return None to indicate pattern exists
        # The actual URL needs to be scraped
        return None
    
    def find_subject_page_url(self, subject: str, level: str) -> Optional[str]:
        """
        Find the subject page URL from the qualifications listing page.
        
        Returns the URL to the subject's qualification page.
        """
        try:
            self._init_driver()
            logger.info(f"Loading qualifications page...")
            self.driver.get(self.QUALIFICATIONS_URL)
            
            # Wait for page to load and JavaScript to execute
            time.sleep(5)
            
            # Scroll to trigger lazy loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Wait for qualifications to load
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                logger.warning("Page load timeout")
                return None
            
            # Normalize subject name for matching
            normalized_subject = self._normalize_subject_name(subject)
            subject_lower = subject.lower()
            
            # Determine level text to search for
            if level == "GCSE":
                level_texts = ["gcse"]
            elif level == "A-Level":
                level_texts = ["a-level", "as/a level", "as level"]
            else:
                level_texts = [level.lower()]
            
            # Try multiple strategies to find the link
            
            # Strategy 1: Search in page source
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find all links
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                
                # Check various subject name variations
                subject_matches = (
                    normalized_subject in text or
                    subject_lower in text or
                    subject_lower.replace(' and ', ' & ') in text or
                    subject_lower.replace(' & ', ' and ') in text
                )
                
                # Check level matches
                level_matches = any(lt in text for lt in level_texts)
                
                if subject_matches and level_matches:
                    # Construct full URL
                    if href.startswith('/'):
                        full_url = urljoin(self.BASE_URL, href)
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        full_url = urljoin(self.BASE_URL, '/' + href)
                    
                    # Verify it's an Eduqas URL
                    if 'eduqas.co.uk' in full_url:
                        logger.info(f"Found subject page: {full_url} for {subject} ({level})")
                        return full_url
            
            # Strategy 2: Try clicking on subject sections if they're expandable
            try:
                # Look for expandable sections or subject headings
                subject_elements = self.driver.find_elements(
                    By.XPATH, 
                    f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{subject_lower}')]"
                )
                
                for elem in subject_elements[:5]:  # Limit to first 5 matches
                    try:
                        # Scroll to element
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                        time.sleep(1)
                        
                        # Try to click if it's clickable
                        if elem.tag_name == 'a':
                            href = elem.get_attribute('href')
                            if href:
                                full_url = urljoin(self.BASE_URL, href) if href.startswith('/') else href
                                if 'eduqas.co.uk' in full_url:
                                    logger.info(f"Found subject page via click: {full_url}")
                                    return full_url
                        
                        # Try clicking parent if it's a button or expandable
                        parent = elem.find_element(By.XPATH, "./ancestor::a[1]")
                        if parent:
                            href = parent.get_attribute('href')
                            if href:
                                full_url = urljoin(self.BASE_URL, href) if href.startswith('/') else href
                                if 'eduqas.co.uk' in full_url:
                                    logger.info(f"Found subject page via parent: {full_url}")
                                    return full_url
                    except:
                        continue
            except:
                pass
            
            logger.warning(f"Could not find subject page for {subject} ({level})")
            return None
            
        except Exception as e:
            logger.error(f"Error finding subject page for {subject} ({level}): {e}")
            return None
    
    def find_pdf_url_from_subject_page(self, subject_page_url: str, subject: str, level: str) -> Optional[str]:
        """
        Navigate to subject page and find the specification PDF URL.
        
        Returns the PDF URL if found.
        """
        try:
            self._init_driver()
            logger.info(f"Navigating to: {subject_page_url}")
            self.driver.get(subject_page_url)
            
            # Wait for page to load and JavaScript to execute
            time.sleep(5)
            
            # Scroll to trigger lazy loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Wait for page content
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                logger.warning("Page load timeout")
                return None
            
            # Try to expand sections/tabs that might contain the PDF
            try:
                # Look for tabs or sections related to specifications
                tab_selectors = [
                    "//*[contains(text(), 'Specification')]",
                    "//*[contains(text(), 'Key Documents')]",
                    "//*[contains(text(), 'Downloads')]",
                    "//button[contains(text(), 'Specification')]",
                    "//a[contains(text(), 'Specification')]"
                ]
                
                for selector in tab_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for elem in elements[:3]:  # Limit to first 3 matches
                            try:
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                                time.sleep(0.5)
                                self.driver.execute_script("arguments[0].click();", elem)
                                time.sleep(2)
                                break
                            except:
                                continue
                    except:
                        continue
            except:
                pass
            
            # Get page source and parse
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Look for PDF links - multiple strategies
            pdf_urls = []
            
            # Strategy 1: Look for links containing "specification" and ending in .pdf
            spec_links = soup.find_all('a', href=lambda x: x and 'spec' in x.lower() and x.lower().endswith('.pdf'))
            for link in spec_links:
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                if 'specification' in text or 'spec' in text:
                    if href.startswith('/'):
                        full_url = urljoin(self.BASE_URL, href)
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        full_url = urljoin(self.BASE_URL, '/' + href)
                    pdf_urls.append(full_url)
            
            # Strategy 2: Look for all PDF links and filter by text content
            all_pdf_links = soup.find_all('a', href=lambda x: x and x.lower().endswith('.pdf'))
            for link in all_pdf_links:
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                parent_text = ''
                if link.parent:
                    parent_text = link.parent.get_text(strip=True).lower()
                
                # Check if it's a specification PDF
                if any(keyword in (text + ' ' + parent_text) for keyword in ['specification', 'spec', 'syllabus']):
                    if href.startswith('/'):
                        full_url = urljoin(self.BASE_URL, href)
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        full_url = urljoin(self.BASE_URL, '/' + href)
                    if full_url not in pdf_urls:
                        pdf_urls.append(full_url)
            
            # Strategy 3: Look for buttons or elements with "Download" or "Specification"
            buttons = soup.find_all(['button', 'a'], string=re.compile(r'specification|download.*spec|spec.*pdf', re.I))
            for button in buttons:
                # Check if button has href or onclick
                href = button.get('href', '')
                if not href:
                    # Try to find associated link
                    parent = button.parent
                    if parent:
                        link = parent.find('a', href=True)
                        if link:
                            href = link.get('href', '')
                
                if href and href.lower().endswith('.pdf'):
                    if href.startswith('/'):
                        full_url = urljoin(self.BASE_URL, href)
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        full_url = urljoin(self.BASE_URL, '/' + href)
                    if full_url not in pdf_urls:
                        pdf_urls.append(full_url)
            
            # Strategy 4: Try clicking on "Specification" or "Key Documents" tabs/sections
            try:
                # Look for tabs or sections
                spec_tabs = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Specification') or contains(text(), 'Key Documents')]")
                for tab in spec_tabs[:3]:  # Limit to first 3 matches
                    try:
                        tab.click()
                        time.sleep(2)
                        # Re-parse after click
                        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                        pdf_links = soup.find_all('a', href=lambda x: x and x.lower().endswith('.pdf'))
                        for link in pdf_links:
                            href = link.get('href', '')
                            if href.startswith('/'):
                                full_url = urljoin(self.BASE_URL, href)
                            elif href.startswith('http'):
                                full_url = href
                            else:
                                full_url = urljoin(self.BASE_URL, '/' + href)
                            if full_url not in pdf_urls:
                                pdf_urls.append(full_url)
                    except:
                        continue
            except:
                pass
            
            # Return the first PDF URL found (usually the main specification)
            if pdf_urls:
                logger.info(f"Found {len(pdf_urls)} PDF URL(s) for {subject} ({level})")
                return pdf_urls[0]
            else:
                logger.warning(f"No PDF URL found for {subject} ({level})")
                return None
                
        except Exception as e:
            logger.error(f"Error finding PDF URL for {subject} ({level}): {e}")
            return None
    
    def scrape_all_pdf_urls(self, qualifications_file: str, output_file: Optional[str] = None, limit: Optional[int] = None) -> Dict:
        """
        Scrape PDF URLs for all qualifications listed in the file.
        
        Args:
            qualifications_file: Path to qualifications markdown file
            output_file: Optional path to save results JSON
            limit: Optional limit on number of qualifications to process (for testing)
        
        Returns a dictionary mapping (subject, level) to PDF URL.
        """
        # Parse qualifications
        qualifications = self.parse_qualifications_file(qualifications_file)
        
        if not qualifications:
            logger.error("No qualifications found in file")
            return {}
        
        # Apply limit if specified (for testing)
        if limit:
            qualifications = qualifications[:limit]
            logger.info(f"Limited to first {limit} qualifications for testing")
        
        results = {}
        failed = []
        
        logger.info(f"Starting to scrape {len(qualifications)} qualifications...")
        
        try:
            for i, (subject, level) in enumerate(qualifications, 1):
                logger.info(f"\n[{i}/{len(qualifications)}] Processing: {subject} ({level})")
                
                # Find subject page URL
                subject_page_url = self.find_subject_page_url(subject, level)
                
                if not subject_page_url:
                    logger.warning(f"Could not find subject page for {subject} ({level})")
                    failed.append((subject, level, "Subject page not found"))
                    continue
                
                # Find PDF URL from subject page
                pdf_url = self.find_pdf_url_from_subject_page(subject_page_url, subject, level)
                
                if pdf_url:
                    key = f"{subject} - {level}"
                    results[key] = {
                        'subject': subject,
                        'level': level,
                        'subject_page_url': subject_page_url,
                        'pdf_url': pdf_url
                    }
                    logger.info(f"✓ Found PDF: {pdf_url}")
                else:
                    failed.append((subject, level, "PDF URL not found"))
                    logger.warning(f"✗ Could not find PDF URL")
                
                # Be polite - delay between requests
                time.sleep(2)
        
        finally:
            self._close_driver()
        
        # Save results
        if output_file:
            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"\nResults saved to: {output_path}")
        
        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info(f"Scraping complete!")
        logger.info(f"Successfully found: {len(results)} PDF URLs")
        logger.info(f"Failed: {len(failed)}")
        
        if failed:
            logger.info("\nFailed qualifications:")
            for subject, level, reason in failed:
                logger.info(f"  - {subject} ({level}): {reason}")
        
        return results


def main():
    """Main function to run the scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape Eduqas specification PDF URLs')
    parser.add_argument('--qualifications-file', 
                       default='Eduqas Qualifications - All.md',
                       help='Path to qualifications markdown file')
    parser.add_argument('--output', 
                       default='eduqas-pdf-urls.json',
                       help='Output JSON file path')
    parser.add_argument('--no-headless', action='store_true',
                       help='Run browser in visible mode')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of qualifications to process (for testing)')
    
    args = parser.parse_args()
    
    scraper = EduqasPDFURLScraper(headless=not args.no_headless)
    results = scraper.scrape_all_pdf_urls(args.qualifications_file, args.output, limit=args.limit)
    
    print(f"\nFound {len(results)} PDF URLs")
    print(f"Results saved to: {args.output}")


if __name__ == '__main__':
    main()





















