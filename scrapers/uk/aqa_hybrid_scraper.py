"""
AQA Hybrid Scraper - Best of Both Worlds
Uses web scraping (fast, free) with PDF extraction as backup (reliable, costs AI)
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.uk.aqa_web_scraper import AQAWebScraper
from extractors.specification_extractor import SpecificationExtractor
from extractors.html_specification_extractor import HTMLSpecificationExtractor
from utils.logger import get_logger
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import requests

logger = get_logger()


class AQAHybridScraper:
    """
    Hybrid scraper that:
    1. Tries web scraping first (fast, free, no AI)
    2. Falls back to PDF extraction if needed (reliable, uses AI)
    """
    
    def __init__(self, headless=True, supabase_uploader=None):
        self.web_scraper = AQAWebScraper(headless=headless)
        self.html_extractor = HTMLSpecificationExtractor()  # NEW: Extract from HTML
        self.pdf_extractor = SpecificationExtractor()  # Backup only
        self.uploader = supabase_uploader
    
    def process_subject_complete(self, subject: str, qualification: str, 
                                subject_code: str, upload_to_supabase: bool = True) -> dict:
        """
        Complete processing with hybrid approach.
        
        Returns:
        {
            'subject': str,
            'qualification': str,
            'code': str,
            'method': 'web' or 'pdf',
            'success': bool,
            'content_items': [...] or None,
            'pdf_path': str or None,
            'extracted_data': dict or None,
            'errors': []
        }
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {subject} ({qualification}) - AQA Code {subject_code}")
        logger.info(f"{'='*60}\n")
        
        result = {
            'subject': subject,
            'qualification': qualification,
            'code': subject_code,
            'method': None,
            'success': False,
            'content_items': None,
            'pdf_path': None,
            'extracted_data': None,
            'errors': []
        }
        
        # Build specification page URL
        spec_page_url = self._build_specification_url(subject, qualification, subject_code)
        
        # STEP 1: Scrape subject-content pages for detailed topics
        logger.info("Step 1: Scraping subject-content pages...")
        web_result = None
        try:
            web_result = self.web_scraper.scrape_subject_content_complete(
                subject=subject,
                qualification=qualification,
                subject_code=subject_code
            )
            
            if web_result and web_result.get('content_items'):
                logger.info(f"[OK] Found {len(web_result['content_items'])} content items from web")
            else:
                logger.warning("[WARN] No content found from web scraping")
                
        except Exception as e:
            logger.warning(f"[WARN] Web scraping failed: {e}")
            result['errors'].append(f"Web scraping error: {str(e)}")
        
        # STEP 2: Skip HTML extraction for now - go straight to PDF (more reliable)
        # TODO: Fix HTML extraction later
        logger.info("Step 2: Finding PDF for metadata extraction...")
        
        # STEP 3: PDF extraction for metadata
        try:
            logger.info(f"Specification page: {spec_page_url}")
            
            pdf_url = self._find_pdf_on_page(spec_page_url)
            if not pdf_url:
                raise ValueError("Could not find PDF on specification page")
            
            logger.info(f"[OK] Found PDF: {pdf_url}")
            
            # Download PDF
            pdf_path = self._download_pdf(pdf_url, subject, qualification, subject_code)
            if not pdf_path:
                raise ValueError("Failed to download PDF")
            
            logger.info(f"[OK] Downloaded PDF to: {pdf_path}")
            result['pdf_path'] = pdf_path
            
            # Extract with AI
            logger.info("[AI] Extracting with AI (this costs ~$0.10-0.15)...")
            
            complete_data = self.pdf_extractor.extract_complete_specification(
                pdf_path=pdf_path,
                subject=subject,
                exam_board='AQA',
                qualification=qualification
            )
            
            if not complete_data:
                raise ValueError("AI extraction returned no data")
            
            # Debug: Check what we got
            logger.info(f"[DEBUG] Extraction returned type: {type(complete_data)}")
            logger.info(f"[DEBUG] Keys: {complete_data.keys() if isinstance(complete_data, dict) else 'N/A'}")
            
            # Ensure complete_data is a dict
            if not isinstance(complete_data, dict):
                raise ValueError(f"AI extraction returned invalid type: {type(complete_data)}")
            
            # Context fields already added by extractor, just verify
            if 'metadata' not in complete_data:
                logger.warning("[WARN] No metadata in extraction result")
            if 'components' not in complete_data:
                logger.warning("[WARN] No components in extraction result")
            if 'options' not in complete_data:
                logger.warning("[WARN] No options in extraction result")
            
            logger.info(f"[OK] PDF extraction SUCCESS")
            logger.info(f"  - Metadata: {bool(complete_data.get('metadata'))}")
            logger.info(f"  - Components: {len(complete_data.get('components', []))}")
            logger.info(f"  - Constraints: {len(complete_data.get('constraints', []))}")
            logger.info(f"  - Topics: {len(complete_data.get('options', []))}")
            
            result['method'] = 'pdf'
            result['extracted_data'] = complete_data
            result['success'] = True
            
            # Upload if requested
            if upload_to_supabase and self.uploader:
                # Prepare data package with context
                data_package = {
                    **complete_data,
                    'exam_board': 'AQA',
                    'subject': subject,
                    'qualification': qualification
                }
                self._upload_pdf_data(data_package)
                
                # ALSO upload the web-scraped topics (they have rich hierarchical data!)
                if web_result and web_result.get('content_items'):
                    logger.info("Also uploading web-scraped topic details...")
                    self._upload_web_topics(web_result, subject, qualification, subject_code)
            
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] PDF extraction failed: {e}")
            result['errors'].append(f"PDF extraction error: {str(e)}")
        
        # Both methods failed
        logger.error(f"\n[FAILED] Could not extract data using web or PDF methods")
        return result
    
    def _build_specification_url(self, subject: str, qualification: str, code: str) -> str:
        """Build URL for specification page where PDF is located."""
        subject_slug = subject.lower().replace(' ', '-')
        
        # Handle Art and Design variants
        if 'art-and-design' in subject_slug or 'art and design' in subject.lower():
            subject_slug = "art-and-design"
        
        qual_slug = qualification.lower().replace(' ', '-')
        
        return f"https://www.aqa.org.uk/subjects/{subject_slug}/{qual_slug}/{subject_slug}-{code}/specification"
    
    def _find_pdf_on_page(self, url: str) -> str:
        """Find PDF link on specification page."""
        html = self.web_scraper._get_page(url, use_selenium=False)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Look for PDF links
        # AQA now uses cdn.sanity.io for PDFs
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.I))
        
        for link in pdf_links:
            href = link.get('href')
            text = link.get_text().lower()
            
            # Prioritize links with "specification" in text or PDF > 500KB
            if 'specification' in text or 'sp-' in href.lower():
                return urljoin('https://www.aqa.org.uk', href)
        
        # Fallback: return first PDF found
        if pdf_links:
            return urljoin('https://www.aqa.org.uk', pdf_links[0].get('href'))
        
        return None
    
    def _download_pdf(self, url: str, subject: str, qualification: str, code: str) -> str:
        """Download PDF from URL."""
        from utils.helpers import sanitize_filename, ensure_directory
        
        filename = f"{sanitize_filename(subject)}_{sanitize_filename(qualification)}_{code}.pdf"
        output_dir = os.path.join("data", "raw", "AQA", "specifications")
        ensure_directory(output_dir)
        
        filepath = os.path.join(output_dir, filename)
        
        # Check if already downloaded
        if os.path.exists(filepath):
            logger.info(f"PDF already exists: {filepath}")
            return filepath
        
        # Download
        try:
            import requests
            
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return filepath
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None
    
    def _upload_combined_data(self, web_result: dict, html_metadata: dict, subject: str, 
                              qualification: str, code: str, spec_url: str, pdf_url: str):
        """Upload combined web + HTML AI data to Supabase."""
        logger.info("Uploading combined data to Supabase...")
        
        # Create complete data package
        complete_data = {
            'exam_board': 'AQA',
            'subject': subject,
            'qualification': qualification,
            'metadata': html_metadata.get('metadata', {}),
            'components': html_metadata.get('components', []),
            'constraints': html_metadata.get('constraints', []),
            'options': html_metadata.get('options', []),
            'vocabulary': []
        }
        
        # Add URLs to metadata
        if 'metadata' not in complete_data:
            complete_data['metadata'] = {}
        complete_data['metadata']['specification_url'] = spec_url
        complete_data['metadata']['specification_pdf_url'] = pdf_url
        complete_data['metadata']['subject_code'] = code
        
        # Upload specification metadata
        upload_result = self.uploader.upload_specification_complete(complete_data)
        logger.info(f"[OK] Uploaded metadata (ID: {upload_result.get('metadata_id')})")
        
        # Upload web-scraped topics
        if web_result and web_result.get('content_items'):
            self._upload_web_topics(web_result, subject, qualification, code)
    
    def _upload_web_topics(self, web_result: dict, subject: str, qualification: str, code: str):
        """Upload web-scraped data to Supabase."""
        logger.info("Uploading web-scraped data to Supabase...")
        
        # Get exam_board_subject_id (will CREATE if missing!)
        exam_board_subject_id = self.uploader._get_or_create_exam_board_subject(
            'AQA', subject, qualification, subject_code=code
        )
        
        if not exam_board_subject_id:
            raise ValueError(f"Could not find exam_board_subject")
        
        # Upload content items as topics
        uploaded = 0
        for item in web_result.get('content_items', []):
            try:
                # Level 0: Main topic
                topic_data = {
                    'exam_board_subject_id': exam_board_subject_id,
                    'topic_code': item.get('code'),
                    'topic_name': item.get('title'),
                    'topic_level': 0,
                    'description': item.get('title'),
                    'key_themes': item.get('key_questions', [])
                }
                
                # Use upsert to update existing or insert new
                self.uploader.client.table('curriculum_topics').upsert(
                    topic_data
                ).execute()
                uploaded += 1
                
                # Level 1: Study areas (only if they exist - History has these, Accounting doesn't)
                for study_area in item.get('study_areas', []):
                    area_code = f"{item.get('code')}-area-{study_area.get('area_title', '')[:20]}"
                    
                    area_data = {
                        'exam_board_subject_id': exam_board_subject_id,
                        'topic_code': area_code,
                        'topic_name': study_area.get('area_title'),
                        'topic_level': 1,
                        'parent_topic_id': None,  # FIX: Set to None, not the code string
                        'chronological_period': study_area.get('period')
                    }
                    
                    self.uploader.client.table('curriculum_topics').upsert(
                        area_data
                    ).execute()
                    uploaded += 1
                
            except Exception as e:
                logger.error(f"Failed to upload {item.get('code')}: {e}")
        
        logger.info(f"[OK] Uploaded {uploaded} topics")
    
    def _upload_pdf_data(self, complete_data: dict):
        """Upload PDF-extracted data to Supabase."""
        logger.info("Uploading PDF-extracted data to Supabase...")
        
        upload_results = self.uploader.upload_specification_complete(complete_data)
        
        logger.info(f"[OK] Upload complete:")
        logger.info(f"  - Metadata ID: {upload_results.get('metadata_id')}")
        logger.info(f"  - Components: {upload_results.get('components')}")
        logger.info(f"  - Constraints: {upload_results.get('constraints')}")
        logger.info(f"  - Topics: {upload_results.get('topics')}")
    
    def close(self):
        """Close scrapers."""
        self.web_scraper.close()


if __name__ == '__main__':
    # Test both methods
    scraper = AQAHybridScraper()
    
    # Test web scraping (should work)
    result1 = scraper.process_subject_complete(
        subject="Geography",
        qualification="A-Level",
        subject_code="7037",
        upload_to_supabase=False
    )
    print(f"\nGeography result: Method={result1['method']}, Success={result1['success']}")
    
    # Test accounting (might need PDF fallback)
    result2 = scraper.process_subject_complete(
        subject="Accounting",
        qualification="A-Level",
        subject_code="7127",
        upload_to_supabase=False
    )
    print(f"\nAccounting result: Method={result2['method']}, Success={result2['success']}")
    
    scraper.close()
