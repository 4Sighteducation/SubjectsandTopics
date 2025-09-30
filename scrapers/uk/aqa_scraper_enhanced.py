"""
Enhanced AQA Scraper with Complete Specification Extraction.
Automatically finds, downloads, extracts, and uploads to Supabase.
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.base_scraper import BaseScraper
from extractors.specification_extractor import SpecificationExtractor
from database.supabase_client import SupabaseUploader
from utils.logger import get_logger
from urllib.parse import urljoin
import re

logger = get_logger()


class AQAScraperEnhanced(BaseScraper):
    """
    Enhanced AQA scraper that does EVERYTHING:
    - Finds specification URLs automatically
    - Downloads PDFs automatically  
    - Extracts complete metadata with AI
    - Uploads directly to Supabase
    
    All in one command!
    """
    
    # Direct specification PDF URLs for AQA subjects
    # Note: AQA moved to CDN (sanity.io) - need to extract PDF link from web page
    # Better approach: Navigate to /specification page and find PDF link
    SPEC_PDF_URLS = {
        ('History', 'A-Level'): 'https://www.aqa.org.uk/subjects/history/a-level/history-7042/specification',
        ('Mathematics', 'A-Level'): 'https://www.aqa.org.uk/subjects/mathematics/a-level/mathematics-7357/specification',
        ('Biology', 'A-Level'): 'https://www.aqa.org.uk/subjects/biology/a-level/biology-7402/specification',
        ('Chemistry', 'A-Level'): 'https://filestore.aqa.org.uk/resources/chemistry/specifications/AQA-7405-SP-2016.PDF',
        ('Physics', 'A-Level'): 'https://filestore.aqa.org.uk/resources/physics/specifications/AQA-7408-SP-2015.PDF',
        ('English Literature', 'A-Level'): 'https://filestore.aqa.org.uk/resources/english/specifications/AQA-7717-SP-2015.PDF',
        ('Psychology', 'A-Level'): 'https://filestore.aqa.org.uk/resources/psychology/specifications/AQA-7182-SP-2015.PDF',
        ('Sociology', 'A-Level'): 'https://filestore.aqa.org.uk/resources/sociology/specifications/AQA-7192-SP-2015.PDF',
        ('Geography', 'A-Level'): 'https://filestore.aqa.org.uk/resources/geography/specifications/AQA-7037-SP-2016.PDF',
        ('Economics', 'A-Level'): 'https://filestore.aqa.org.uk/resources/economics/specifications/AQA-7136-SP-2015.PDF',
        
        # GCSE
        ('History', 'GCSE'): 'https://filestore.aqa.org.uk/resources/history/specifications/AQA-8145-SP-2016.PDF',
        ('Mathematics', 'GCSE'): 'https://filestore.aqa.org.uk/resources/mathematics/specifications/AQA-8300-SP-2015.PDF',
        ('Biology', 'GCSE'): 'https://filestore.aqa.org.uk/resources/biology/specifications/AQA-8461-SP-2016.PDF',
        ('Chemistry', 'GCSE'): 'https://filestore.aqa.org.uk/resources/chemistry/specifications/AQA-8462-SP-2016.PDF',
        ('Physics', 'GCSE'): 'https://filestore.aqa.org.uk/resources/physics/specifications/AQA-8463-SP-2016.PDF',
        # ... add more as needed
    }
    
    def __init__(self, headless=True, delay=1.5, supabase_uploader=None):
        """Initialize enhanced AQA scraper."""
        super().__init__(
            name="AQA",
            base_url="https://www.aqa.org.uk",
            headless=headless,
            delay=delay
        )
        
        # Initialize extractors
        self.spec_extractor = SpecificationExtractor()
        self.uploader = supabase_uploader
    
    def process_subject_complete(self, subject: str, exam_type: str, 
                                 upload_to_supabase: bool = True) -> dict:
        """
        COMPLETE END-TO-END PROCESSING for a subject.
        
        This method:
        1. Finds the specification URL
        2. Downloads the PDF
        3. Extracts complete metadata with AI
        4. Uploads to Supabase (optional)
        
        Args:
            subject: Subject name (e.g., "History")
            exam_type: Qualification type (e.g., "A-Level", "GCSE")
            upload_to_supabase: Whether to upload (default True)
            
        Returns:
            Dict with extraction results and upload status
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {subject} ({exam_type}) - AQA")
        logger.info(f"{'='*60}\n")
        
        results = {
            'subject': subject,
            'exam_type': exam_type,
            'exam_board': 'AQA',
            'success': False,
            'pdf_path': None,
            'extracted_data': None,
            'upload_results': None,
            'errors': []
        }
        
        try:
            # Step 1: Get specification PDF URL
            spec_url = self._get_spec_url(subject, exam_type)
            if not spec_url:
                raise ValueError(f"No specification URL found for {subject} ({exam_type})")
            
            logger.info(f"✓ Found specification URL: {spec_url}")
            
            # Step 2: Download PDF
            pdf_path = self._download_spec_pdf(spec_url, subject, exam_type)
            if not pdf_path:
                raise ValueError(f"Failed to download specification PDF")
            
            logger.info(f"✓ Downloaded PDF to: {pdf_path}")
            results['pdf_path'] = pdf_path
            
            # Step 3: Extract complete specification with AI
            logger.info(f"\n📊 Extracting complete specification data with AI...")
            logger.info(f"   This may take 2-3 minutes...\n")
            
            complete_data = self.spec_extractor.extract_complete_specification(
                pdf_path=pdf_path,
                subject=subject,
                exam_board='AQA',
                qualification=exam_type
            )
            
            if not complete_data:
                raise ValueError("AI extraction failed")
            
            # Add root-level context for uploader
            complete_data['exam_board'] = 'AQA'
            complete_data['subject'] = subject
            complete_data['qualification'] = exam_type
            
            logger.info(f"✓ Extracted:")
            logger.info(f"  - Metadata: {bool(complete_data.get('metadata'))}")
            logger.info(f"  - Components: {len(complete_data.get('components', []))}")
            logger.info(f"  - Constraints: {len(complete_data.get('constraints', []))}")
            logger.info(f"  - Topic Options: {len(complete_data.get('options', []))}")
            logger.info(f"  - Vocabulary: {len(complete_data.get('vocabulary', []))}")
            
            results['extracted_data'] = complete_data
            
            # Step 4: Upload to Supabase (if enabled)
            if upload_to_supabase and self.uploader:
                logger.info(f"\n💾 Uploading to Supabase...")
                
                upload_results = self.uploader.upload_specification_complete(complete_data)
                
                logger.info(f"✓ Upload complete:")
                logger.info(f"  - Metadata ID: {upload_results.get('metadata_id')}")
                logger.info(f"  - Components: {upload_results.get('components')}")
                logger.info(f"  - Constraints: {upload_results.get('constraints')}")
                logger.info(f"  - Topics: {upload_results.get('topics')}")
                logger.info(f"  - Vocabulary: {upload_results.get('vocabulary')}")
                
                results['upload_results'] = upload_results
            
            results['success'] = True
            logger.info(f"\n✅ Complete! {subject} ({exam_type}) processed successfully\n")
            
        except Exception as e:
            logger.error(f"\n❌ Error processing {subject}: {e}", exc_info=True)
            results['errors'].append(str(e))
        
        return results
    
    def _get_spec_url(self, subject: str, exam_type: str) -> str:
        """
        Get specification PDF URL for a subject.
        First checks hardcoded URLs, then tries to find dynamically.
        """
        # Check hardcoded URLs first
        key = (subject, exam_type)
        if key in self.SPEC_PDF_URLS:
            url = self.SPEC_PDF_URLS[key]
            
            # If it's a webpage (not PDF), extract PDF link from it
            if not url.lower().endswith('.pdf'):
                return self._extract_pdf_from_page(url)
            
            return url
        
        # Try to find dynamically from AQA website
        logger.info(f"No hardcoded URL for {subject} ({exam_type}), searching AQA website...")
        
        # Construct likely subject page URL
        subject_slug = subject.lower().replace(' ', '-')
        exam_slug = 'a-level' if 'level' in exam_type.lower() else exam_type.lower()
        
        subject_page_url = f"https://www.aqa.org.uk/subjects/{subject_slug}/{exam_slug}"
        
        # Get subject page
        html = self._get_page(subject_page_url, use_selenium=True)
        if not html:
            return None
        
        # Look for PDF link with "specification" in it
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
        for link in pdf_links:
            href = link.get('href', '')
            text = link.get_text().lower()
            
            if 'specification' in text or 'specification' in href.lower():
                # Found it!
                pdf_url = urljoin(self.base_url, href)
                logger.info(f"Found specification URL: {pdf_url}")
                return pdf_url
        
        logger.warning(f"Could not find specification PDF for {subject}")
        return None
    
    def _extract_pdf_from_page(self, page_url: str) -> str:
        """Extract PDF download link from a specification page."""
        from bs4 import BeautifulSoup
        
        logger.info(f"Extracting PDF link from page: {page_url}")
        
        html = self._get_page(page_url, use_selenium=False)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Look for PDF download link
        pdf_link = soup.find('a', href=re.compile(r'\.pdf$', re.I), string=re.compile(r'specification', re.I))
        
        if pdf_link:
            pdf_url = urljoin(self.base_url, pdf_link['href'])
            logger.info(f"Found PDF link: {pdf_url}")
            return pdf_url
        
        # Try looking for any PDF link
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
        if pdf_links:
            pdf_url = urljoin(self.base_url, pdf_links[0]['href'])
            logger.info(f"Found PDF link (generic): {pdf_url}")
            return pdf_url
        
        logger.warning("No PDF link found on page")
        return None
    
    def _download_spec_pdf(self, url: str, subject: str, exam_type: str) -> str:
        """
        Download specification PDF.
        Returns path to downloaded file.
        """
        from utils.helpers import sanitize_filename, ensure_directory
        
        # Create filename
        filename = f"{sanitize_filename(subject)}_{sanitize_filename(exam_type)}_spec.pdf"
        
        # Create directory structure
        output_dir = os.path.join("data", "raw", "AQA", "specifications")
        ensure_directory(output_dir)
        
        filepath = os.path.join(output_dir, filename)
        
        # Check if already downloaded
        if os.path.exists(filepath):
            logger.info(f"Specification already downloaded: {filepath}")
            return filepath
        
        # Download
        logger.info(f"Downloading specification from {url}...")
        
        try:
            import requests
            from tqdm import tqdm
            
            # Create a fresh session to avoid base_scraper's session issues
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            response = session.get(url, stream=True, timeout=60, allow_redirects=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f, tqdm(
                desc=filename,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for data in response.iter_content(chunk_size=1024):
                    size = f.write(data)
                    pbar.update(size)
            
            logger.info(f"Downloaded to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None
    
    def scrape_topics(self, subject=None, exam_type=None):
        """
        Legacy method - kept for compatibility.
        For enhanced extraction, use process_subject_complete() instead.
        """
        logger.warning("Using legacy scrape_topics method. Consider using process_subject_complete() for enhanced extraction.")
        return []
    
    def scrape_papers(self, subject=None, exam_type=None, year_from=2021):
        """
        Legacy method - not implemented in enhanced version.
        Focus is on topic/specification extraction, not papers.
        """
        logger.warning("scrape_papers not implemented in enhanced scraper")
        return []


# Convenience function for single subject processing
def process_single_subject(subject: str, exam_type: str, upload: bool = True):
    """
    Process a single subject completely and automatically.
    
    Usage:
        from scrapers.uk.aqa_scraper_enhanced import process_single_subject
        process_single_subject("History", "A-Level", upload=True)
    """
    # Initialize uploader if needed
    uploader = None
    if upload:
        from database.supabase_client import SupabaseUploader
        uploader = SupabaseUploader()
    
    # Create scraper
    scraper = AQAScraperEnhanced(
        headless=True,
        supabase_uploader=uploader
    )
    
    try:
        # Process completely
        results = scraper.process_subject_complete(
            subject=subject,
            exam_type=exam_type,
            upload_to_supabase=upload
        )
        
        return results
        
    finally:
        scraper.close()


if __name__ == '__main__':
    # Allow running directly: python aqa_scraper_enhanced.py
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced AQA Scraper')
    parser.add_argument('--subject', required=True, help='Subject name')
    parser.add_argument('--exam-type', required=True, help='GCSE or A-Level')
    parser.add_argument('--no-upload', action='store_true', help='Skip Supabase upload')
    
    args = parser.parse_args()
    
    results = process_single_subject(
        subject=args.subject,
        exam_type=args.exam_type,
        upload=not args.no_upload
    )
    
    if results['success']:
        print(f"\n✅ Success! Processed {args.subject} ({args.exam_type})")
    else:
        print(f"\n❌ Failed: {results.get('errors')}")
        sys.exit(1)
