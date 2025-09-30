"""
Cambridge International Examinations Scraper
Handles Cambridge IGCSE and Cambridge International A-Level subjects
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.base_scraper import BaseScraper
from extractors.specification_extractor import SpecificationExtractor
from database.supabase_client import SupabaseUploader
from utils.logger import get_logger
from urllib.parse import urljoin
import re

logger = get_logger()


class CambridgeScraper(BaseScraper):
    """
    Scraper for Cambridge International Examinations (CAIE).
    
    Coverage:
    - Cambridge IGCSE (International GCSE)
    - Cambridge International AS & A Level
    
    Similar structure to AQA but with international curriculum focus.
    """
    
    # Cambridge IGCSE subject URLs (Top 30 most popular)
    IGCSE_SUBJECTS = {
        'Mathematics': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-mathematics-0580/',
            'code': '0580'
        },
        'English - First Language': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-first-language-english-0500/',
            'code': '0500'
        },
        'English - Second Language': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-english-second-language-0510/',
            'code': '0510'
        },
        'Biology': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-biology-0610/',
            'code': '0610'
        },
        'Chemistry': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-chemistry-0620/',
            'code': '0620'
        },
        'Physics': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-physics-0625/',
            'code': '0625'
        },
        'Combined Science': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-combined-science-0653/',
            'code': '0653'
        },
        'Computer Science': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-computer-science-0478/',
            'code': '0478'
        },
        'Accounting': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-accounting-0452/',
            'code': '0452'
        },
        'Economics': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-economics-0455/',
            'code': '0455'
        },
        'Business Studies': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-business-studies-0450/',
            'code': '0450'
        },
        'Geography': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-geography-0460/',
            'code': '0460'
        },
        'History': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-history-0470/',
            'code': '0470'
        },
        'Art and Design': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-art-and-design-0400/',
            'code': '0400'
        },
        'French': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-french-foreign-language-0520/',
            'code': '0520'
        },
        'Spanish': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-spanish-foreign-language-0530/',
            'code': '0530'
        },
        'Literature in English': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-literature-english-0475/',
            'code': '0475'
        },
    }
    
    # Cambridge A-Level subjects (Top 20 most popular)
    A_LEVEL_SUBJECTS = {
        'Mathematics': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-mathematics-9709/',
            'code': '9709'
        },
        'Biology': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-biology-9700/',
            'code': '9700'
        },
        'Chemistry': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-chemistry-9701/',
            'code': '9701'
        },
        'Physics': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-physics-9702/',
            'code': '9702'
        },
        'Computer Science': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-computer-science-9618/',
            'code': '9618'
        },
        'Economics': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-economics-9708/',
            'code': '9708'
        },
        'Business': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-business-9609/',
            'code': '9609'
        },
        'Accounting': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-accounting-9706/',
            'code': '9706'
        },
        'Geography': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-geography-9696/',
            'code': '9696'
        },
        'History': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-history-9489/',
            'code': '9489'
        },
        'Psychology': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-psychology-9990/',
            'code': '9990'
        },
        'English - Language': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-english-language-9093/',
            'code': '9093'
        },
        'English - Literature': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-english-literature-9695/',
            'code': '9695'
        },
        'Further Mathematics': {
            'url': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-further-mathematics-9231/',
            'code': '9231'
        },
    }
    
    def __init__(self, headless=True, delay=2.0, supabase_uploader=None):
        """Initialize Cambridge scraper."""
        super().__init__(
            name="Cambridge International",
            base_url="https://www.cambridgeinternational.org",
            headless=headless,
            delay=delay
        )
        
        self.spec_extractor = SpecificationExtractor()
        self.uploader = supabase_uploader
    
    def process_subject_complete(self, subject: str, qualification: str, 
                                 upload_to_supabase: bool = True) -> dict:
        """
        Complete end-to-end processing for Cambridge subject.
        
        Args:
            subject: Subject name (e.g., "Mathematics")
            qualification: "IGCSE" or "A-Level"
            upload_to_supabase: Whether to upload to Supabase
            
        Returns:
            Dict with processing results
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {subject} (Cambridge {qualification})")
        logger.info(f"{'='*60}\n")
        
        results = {
            'subject': subject,
            'qualification': qualification,
            'exam_board': 'Cambridge',
            'success': False,
            'pdf_path': None,
            'extracted_data': None,
            'upload_results': None,
            'errors': []
        }
        
        try:
            # Get subject configuration
            subject_config = self._get_subject_config(subject, qualification)
            if not subject_config:
                raise ValueError(f"Subject not found: {subject} ({qualification})")
            
            logger.info(f"✓ Found subject: {subject_config['code']}")
            logger.info(f"  URL: {subject_config['url']}")
            
            # Navigate to subject page and find syllabus PDF
            syllabus_url = self._find_syllabus_pdf(subject_config['url'])
            if not syllabus_url:
                raise ValueError(f"Could not find syllabus PDF for {subject}")
            
            logger.info(f"✓ Found syllabus PDF: {syllabus_url}")
            
            # Download PDF
            pdf_path = self._download_syllabus_pdf(
                syllabus_url, subject, qualification, subject_config['code']
            )
            
            if not pdf_path:
                raise ValueError("Failed to download syllabus PDF")
            
            logger.info(f"✓ Downloaded PDF to: {pdf_path}")
            results['pdf_path'] = pdf_path
            
            # Extract with AI (same method as AQA!)
            logger.info(f"\n📊 Extracting specification data with AI...")
            logger.info(f"   This may take 2-3 minutes...\n")
            
            complete_data = self.spec_extractor.extract_complete_specification(
                pdf_path=pdf_path,
                subject=subject,
                exam_board='Cambridge',
                qualification=qualification
            )
            
            if not complete_data:
                raise ValueError("AI extraction failed")
            
            # Add root-level context
            complete_data['exam_board'] = 'Cambridge'
            complete_data['subject'] = subject
            complete_data['qualification'] = qualification
            
            logger.info(f"✓ Extracted:")
            logger.info(f"  - Metadata: {bool(complete_data.get('metadata'))}")
            logger.info(f"  - Components: {len(complete_data.get('components', []))}")
            logger.info(f"  - Constraints: {len(complete_data.get('constraints', []))}")
            logger.info(f"  - Topic Options: {len(complete_data.get('options', []))}")
            
            results['extracted_data'] = complete_data
            
            # Upload to Supabase
            if upload_to_supabase and self.uploader:
                logger.info(f"\n💾 Uploading to Supabase...")
                
                upload_results = self.uploader.upload_specification_complete(complete_data)
                
                logger.info(f"✓ Upload complete:")
                logger.info(f"  - Metadata ID: {upload_results.get('metadata_id')}")
                logger.info(f"  - Components: {upload_results.get('components')}")
                logger.info(f"  - Topics: {upload_results.get('topics')}")
                
                results['upload_results'] = upload_results
            
            results['success'] = True
            logger.info(f"\n✅ Complete! {subject} processed successfully\n")
            
        except Exception as e:
            logger.error(f"\n❌ Error processing {subject}: {e}", exc_info=True)
            results['errors'].append(str(e))
        
        return results
    
    def _get_subject_config(self, subject: str, qualification: str) -> Optional[Dict]:
        """Get subject configuration from predefined lists."""
        subjects = self.IGCSE_SUBJECTS if qualification == 'IGCSE' else self.A_LEVEL_SUBJECTS
        
        # Try exact match first
        if subject in subjects:
            return subjects[subject]
        
        # Try case-insensitive match
        for subj_name, config in subjects.items():
            if subj_name.lower() == subject.lower():
                return config
        
        return None
    
    def _find_syllabus_pdf(self, subject_url: str) -> Optional[str]:
        """Navigate to subject page and find syllabus PDF link."""
        from bs4 import BeautifulSoup
        
        try:
            html = self._get_page(subject_url, use_selenium=True)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Look for syllabus PDF link
            # Cambridge uses various text: "Syllabus", "Syllabus for examination"
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
            
            for link in pdf_links:
                link_text = link.get_text().lower()
                if 'syllabus' in link_text and 'examination' in link_text:
                    pdf_url = urljoin(self.base_url, link['href'])
                    return pdf_url
            
            # Fallback: any PDF with "syllabus" in text or href
            for link in pdf_links:
                link_text = link.get_text().lower()
                href = link.get('href', '').lower()
                
                if 'syllabus' in link_text or 'syllabus' in href:
                    pdf_url = urljoin(self.base_url, link['href'])
                    return pdf_url
            
            logger.warning("No syllabus PDF found on page")
            return None
            
        except Exception as e:
            logger.error(f"Error finding syllabus PDF: {e}")
            return None
    
    def _download_syllabus_pdf(self, url: str, subject: str, qualification: str, 
                               subject_code: str) -> Optional[str]:
        """Download syllabus PDF."""
        from utils.helpers import sanitize_filename, ensure_directory
        
        # Create filename
        filename = f"Cambridge_{sanitize_filename(subject)}_{qualification}_{subject_code}.pdf"
        
        # Create directory
        output_dir = os.path.join("data", "raw", "Cambridge", "syllabuses")
        ensure_directory(output_dir)
        
        filepath = os.path.join(output_dir, filename)
        
        # Check if already downloaded
        if os.path.exists(filepath):
            logger.info(f"Syllabus already downloaded: {filepath}")
            return filepath
        
        # Download
        logger.info(f"Downloading syllabus from {url}...")
        
        try:
            import requests
            from tqdm import tqdm
            
            response = requests.get(url, stream=True, timeout=60)
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
    
    def get_all_subjects(self, qualification: str = 'both') -> List[Dict]:
        """
        Get list of all Cambridge subjects.
        
        Args:
            qualification: 'IGCSE', 'A-Level', or 'both'
            
        Returns:
            List of subject dictionaries
        """
        subjects = []
        
        if qualification in ['IGCSE', 'both']:
            for subject_name, config in self.IGCSE_SUBJECTS.items():
                subjects.append({
                    'name': subject_name,
                    'code': config['code'],
                    'qualification': 'IGCSE',
                    'url': config['url']
                })
        
        if qualification in ['A-Level', 'both']:
            for subject_name, config in self.A_LEVEL_SUBJECTS.items():
                subjects.append({
                    'name': subject_name,
                    'code': config['code'],
                    'qualification': 'A-Level',
                    'url': config['url']
                })
        
        return subjects


def process_single_subject(subject: str, qualification: str, upload: bool = True):
    """
    Process a single Cambridge subject.
    
    Usage:
        from scrapers.international.cambridge_scraper import process_single_subject
        process_single_subject("Mathematics", "IGCSE", upload=True)
    """
    uploader = None
    if upload:
        from database.supabase_client import SupabaseUploader
        uploader = SupabaseUploader()
    
    scraper = CambridgeScraper(headless=True, supabase_uploader=uploader)
    
    try:
        results = scraper.process_subject_complete(
            subject=subject,
            qualification=qualification,
            upload_to_supabase=upload
        )
        return results
    finally:
        scraper.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Cambridge International Scraper')
    parser.add_argument('--subject', required=True, help='Subject name')
    parser.add_argument('--qual', choices=['IGCSE', 'A-Level'], required=True, 
                       help='Qualification type')
    parser.add_argument('--no-upload', action='store_true', help='Skip Supabase upload')
    parser.add_argument('--list', action='store_true', help='List all subjects')
    
    args = parser.parse_args()
    
    if args.list:
        scraper = CambridgeScraper()
        subjects = scraper.get_all_subjects()
        print("\nAvailable Cambridge Subjects:")
        print("=" * 60)
        for s in subjects:
            print(f"{s['name']:30} {s['qualification']:10} {s['code']}")
        sys.exit(0)
    
    results = process_single_subject(
        subject=args.subject,
        qualification=args.qual,
        upload=not args.no_upload
    )
    
    if results['success']:
        print(f"\n✅ Success! Processed {args.subject} (Cambridge {args.qual})")
    else:
        print(f"\n❌ Failed: {results.get('errors')}")
        sys.exit(1)
