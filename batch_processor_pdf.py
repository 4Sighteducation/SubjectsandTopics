#!/usr/bin/env python
"""
PDF-Only Batch Processor - Gets ALL Rich Metadata
Uses AI extraction for all subjects to capture complete specification data
Cost: ~$7-12 for all 74 subjects
"""

import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Ensure we're in the right directory
script_dir = Path(__file__).parent
os.chdir(script_dir)
sys.path.insert(0, str(script_dir))

from database.supabase_client import SupabaseUploader
from extractors.specification_extractor import SpecificationExtractor
from utils.logger import setup_logger
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

load_dotenv()


class PDFBatchProcessor:
    """Process all subjects using PDF extraction for rich metadata."""
    
    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Setup logging
        log_file = f'data/logs/pdf_batch_{self.timestamp}.log'
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logger('INFO', log_file)
        
        # State file
        self.state_file = f'data/state/pdf_batch_state_{self.timestamp}.json'
        Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)
        
        self.state = self._load_or_create_state()
        
        # Initialize components
        self.uploader = SupabaseUploader()
        self.pdf_extractor = SpecificationExtractor()
        
        self.logger.info("=" * 80)
        self.logger.info(f"PDF BATCH PROCESSOR - Full Rich Metadata Extraction")
        self.logger.info(f"Test Mode: {test_mode}")
        self.logger.info(f"Cost: ~$0.10-0.15 per subject")
        self.logger.info("=" * 80)
    
    def _load_or_create_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file) as f:
                return json.load(f)
        
        return {
            'timestamp': self.timestamp,
            'completed': [],
            'failed': [],
            'total_processed': 0,
            'total_cost_estimate': 0.0
        }
    
    def _save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def load_subjects(self):
        """Load subject configuration."""
        config_path = Path(__file__).parent / 'config' / 'aqa_subjects.yaml'
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        subjects = []
        
        # A-Level subjects
        for subject_key, subject_code in config['a_level'].items():
            subject_name = subject_key.replace('_', ' ')
            subjects.append({
                'name': subject_name,
                'code': subject_code,
                'qualification': 'A-Level',
                'key': subject_key
            })
        
        # GCSE subjects
        for subject_key, subject_code in config['gcse'].items():
            subject_name = subject_key.replace('_', ' ')
            subjects.append({
                'name': subject_name,
                'code': subject_code,
                'qualification': 'GCSE',
                'key': subject_key
            })
        
        # Filter out already completed
        remaining = [
            s for s in subjects 
            if f"{s['name']}_{s['qualification']}" not in self.state['completed']
        ]
        
        if self.test_mode:
            return remaining[:3]
        
        return remaining
    
    def process_all(self):
        """Process all subjects with PDF extraction."""
        subjects = self.load_subjects()
        
        self.logger.info(f"\nProcessing {len(subjects)} subjects with PDF extraction")
        self.logger.info(f"Estimated cost: ${len(subjects) * 0.12:.2f}\n")
        
        for i, subject in enumerate(subjects, 1):
            subject_id = f"{subject['name']}_{subject['qualification']}"
            
            self.logger.info("=" * 80)
            self.logger.info(f"[{i}/{len(subjects)}] {subject['name']} ({subject['qualification']}) - {subject['code']}")
            self.logger.info("=" * 80)
            
            try:
                # Find specification page
                spec_url = self._build_spec_url(subject)
                self.logger.info(f"Spec page: {spec_url}")
                
                # Find PDF
                pdf_url = self._find_pdf(spec_url)
                if not pdf_url:
                    raise ValueError("No PDF found")
                
                self.logger.info(f"[OK] PDF URL: {pdf_url}")
                
                # Download PDF
                pdf_path = self._download_pdf(pdf_url, subject)
                if not pdf_path:
                    raise ValueError("Download failed")
                
                self.logger.info(f"[OK] Downloaded: {pdf_path}")
                
                # Extract with AI
                self.logger.info("[AI] Extracting... (~30 seconds, costs ~$0.12)")
                
                complete_data = self.pdf_extractor.extract_complete_specification(
                    pdf_path=pdf_path,
                    subject=subject['name'],
                    exam_board='AQA',
                    qualification=subject['qualification']
                )
                
                if not complete_data:
                    raise ValueError("Extraction returned no data")
                
                self.logger.info(f"[OK] Extracted:")
                self.logger.info(f"  Metadata: {bool(complete_data.get('metadata'))}")
                self.logger.info(f"  Components: {len(complete_data.get('components', []))}")
                self.logger.info(f"  Constraints: {len(complete_data.get('constraints', []))}")
                self.logger.info(f"  Topics: {len(complete_data.get('options', []))}")
                
                # Upload to Supabase
                self.logger.info("[UPLOAD] Uploading to Supabase...")
                
                upload_result = self.uploader.upload_specification_complete({
                    **complete_data,
                    'exam_board': 'AQA',
                    'subject': subject['name'],
                    'qualification': subject['qualification']
                })
                
                self.logger.info(f"[SUCCESS] Uploaded - Metadata ID: {upload_result.get('metadata_id')}")
                
                self.state['completed'].append(subject_id)
                self.state['total_cost_estimate'] += 0.12
                
            except KeyboardInterrupt:
                self.logger.warning("\nInterrupted by user. State saved.")
                self._save_state()
                sys.exit(1)
                
            except Exception as e:
                self.logger.error(f"[FAILED] {subject_id}: {e}")
                self.state['failed'].append(subject_id)
            
            finally:
                self.state['total_processed'] += 1
                self._save_state()
        
        # Summary
        self.logger.info("\n" + "=" * 80)
        self.logger.info("BATCH COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"Completed: {len(self.state['completed'])}")
        self.logger.info(f"Failed: {len(self.state['failed'])}")
        self.logger.info(f"Estimated cost: ${self.state['total_cost_estimate']:.2f}")
        self.logger.info("=" * 80)
    
    def _build_spec_url(self, subject):
        """Build specification page URL."""
        subject_slug = subject['name'].lower().replace(' ', '-')
        if 'art-and-design' in subject_slug or 'art and design' in subject['name'].lower():
            subject_slug = "art-and-design"
        
        qual_slug = subject['qualification'].lower().replace(' ', '-')
        code = subject['code']
        
        return f"https://www.aqa.org.uk/subjects/{subject_slug}/{qual_slug}/{subject_slug}-{code}/specification"
    
    def _find_pdf(self, spec_url):
        """Find PDF on specification page."""
        try:
            response = requests.get(spec_url, timeout=30)
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Look for PDF links (AQA uses cdn.sanity.io)
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.I))
            
            for link in pdf_links:
                href = link.get('href')
                text = link.get_text().lower()
                
                if 'specification' in text or 'sp-' in href.lower():
                    return urljoin('https://www.aqa.org.uk', href)
            
            # Fallback: first PDF
            if pdf_links:
                return urljoin('https://www.aqa.org.uk', pdf_links[0].get('href'))
            
            return None
        except Exception as e:
            self.logger.error(f"Error finding PDF: {e}")
            return None
    
    def _download_pdf(self, url, subject):
        """Download PDF."""
        from utils.helpers import sanitize_filename, ensure_directory
        
        filename = f"{sanitize_filename(subject['name'])}_{subject['qualification']}_{subject['code']}.pdf"
        output_dir = "data/raw/AQA/specifications"
        ensure_directory(output_dir)
        filepath = os.path.join(output_dir, filename)
        
        if os.path.exists(filepath):
            return filepath
        
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(8192):
                    f.write(chunk)
            
            return filepath
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description='PDF Batch Processor - Full Rich Metadata')
    parser.add_argument('--test', action='store_true', help='Test mode: 3 subjects only')
    
    args = parser.parse_args()
    
    # Validate environment
    required = ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'ANTHROPIC_API_KEY']
    missing = [v for v in required if not os.getenv(v)]
    
    if missing:
        print(f"ERROR: Missing {', '.join(missing)}")
        return 1
    
    processor = PDFBatchProcessor(test_mode=args.test)
    
    try:
        processor.process_all()
        return 0
    except Exception as e:
        processor.logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
