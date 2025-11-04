"""
AQA Hybrid Scraper - FIXED VERSION
Properly handles UPSERT and parent-child relationships
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.uk.aqa_web_scraper import AQAWebScraper
from extractors.specification_extractor import SpecificationExtractor
from utils.logger import get_logger
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import requests

logger = get_logger()


class AQAHybridScraperFixed:
    """Fixed version that properly updates existing topics."""
    
    def __init__(self, headless=True, supabase_uploader=None):
        self.web_scraper = AQAWebScraper(headless=headless)
        self.pdf_extractor = SpecificationExtractor()
        self.uploader = supabase_uploader
    
    def process_subject_complete(self, subject: str, qualification: str,
                                subject_code: str, upload_to_supabase: bool = True) -> dict:
        """Process subject with proper UPSERT."""
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {subject} ({qualification})")
        logger.info(f"{'='*60}\n")
        
        result = {
            'subject': subject,
            'qualification': qualification,
            'code': subject_code,
            'method': None,
            'success': False,
            'errors': []
        }
        
        # Build spec URL
        spec_page_url = self._build_specification_url(subject, qualification, subject_code)
        
        # STEP 1: Web scrape topics
        logger.info("Step 1: Web scraping topics...")
        web_result = None
        try:
            web_result = self.web_scraper.scrape_subject_content_complete(
                subject=subject,
                qualification=qualification,
                subject_code=subject_code
            )
            
            if web_result and web_result.get('content_items'):
                logger.info(f"[OK] Found {len(web_result['content_items'])} content items")
        except Exception as e:
            logger.warning(f"[WARN] Web scraping failed: {e}")
        
        # STEP 2: PDF for metadata
        logger.info("\nStep 2: PDF extraction for metadata...")
        try:
            pdf_url = self._find_pdf_on_page(spec_page_url)
            if not pdf_url:
                raise ValueError("No PDF found")
            
            logger.info(f"[OK] Found PDF")
            
            pdf_path = self._download_pdf(pdf_url, subject, qualification, subject_code)
            complete_data = self.pdf_extractor.extract_complete_specification(
                pdf_path=pdf_path,
                subject=subject,
                exam_board='AQA',
                qualification=qualification
            )
            
            logger.info(f"[OK] Extracted metadata, components, constraints")
            
            # Upload metadata
            if upload_to_supabase and self.uploader:
                self._upload_metadata_only({
                    **complete_data,
                    'exam_board': 'AQA',
                    'subject': subject,
                    'qualification': qualification
                }, spec_page_url, pdf_url)
                
                # Upload topics from PDF (has complete hierarchy!)
                logger.info("\nStep 3: Uploading topics from PDF extraction...")
                self._upload_pdf_topics_deep(complete_data, subject, qualification, subject_code)
            
            result['success'] = True
            result['method'] = 'web+pdf'
            
        except Exception as e:
            logger.error(f"[ERROR] {e}")
            result['errors'].append(str(e))
        
        return result
    
    def _upload_pdf_topics_deep(self, pdf_data: dict, subject: str, qualification: str, code: str):
        """Upload deep hierarchical topics from PDF AI extraction."""
        
        exam_board_subject_id = self.uploader._get_or_create_exam_board_subject(
            'AQA', subject, qualification, subject_code=code
        )
        
        if not exam_board_subject_id:
            raise ValueError("Could not find exam_board_subject")
        
        # Get all topics from PDF extraction
        all_topics = pdf_data.get('options', [])
        
        # Debug: Check what we got
        logger.info(f"[DEBUG] Topics type: {type(all_topics)}")
        if isinstance(all_topics, dict):
            logger.info(f"[DEBUG] Dict keys: {all_topics.keys()}")
            # If it's a dict, try to extract the list
            if 'topics' in all_topics:
                all_topics = all_topics['topics']
            else:
                # Convert dict values to list
                all_topics = list(all_topics.values()) if all_topics else []
        
        # Debug: Show what we're working with
        if all_topics and len(all_topics) > 0:
            logger.info(f"[DEBUG] First topic: {all_topics[0]}")
            logger.info(f"[DEBUG] Levels found: {set(t.get('level', 0) for t in all_topics if isinstance(t, dict))}")
        else:
            logger.warning("[DEBUG] No topics in list!")
        
        if not all_topics or not isinstance(all_topics, list):
            logger.warning(f"No topics extracted from PDF or wrong format: {type(all_topics)}")
            return
        
        logger.info(f"Processing {len(all_topics)} topics from PDF extraction...")
        
        # Map to track code → UUID for parent relationships
        code_to_uuid = {}
        uploaded = 0
        
        # Sort by level to ensure parents are created before children
        try:
            all_topics.sort(key=lambda x: x.get('level', 0) if isinstance(x, dict) else 0)
        except Exception as e:
            logger.error(f"Error sorting topics: {e}")
        
        for topic in all_topics:
            try:
                topic_code = topic.get('code')
                parent_code = topic.get('parent_code')
                level = topic.get('level', 0)
                
                # Look up parent UUID if this has a parent
                parent_uuid = None
                if parent_code and parent_code in code_to_uuid:
                    parent_uuid = code_to_uuid[parent_code]
                
                topic_data = {
                    'exam_board_subject_id': exam_board_subject_id,
                    'topic_code': topic_code,
                    'topic_name': topic.get('title'),
                    'topic_level': level,
                    'parent_topic_id': parent_uuid,
                    'description': topic.get('description') or topic.get('title'),
                    'chronological_period': topic.get('period'),
                    'period_start_year': topic.get('period_start'),
                    'period_end_year': topic.get('period_end'),
                    'geographical_region': topic.get('region'),
                    'component_code': topic.get('component_code'),
                    'key_themes': topic.get('content_points', [])
                }
                
                # INSERT and capture UUID
                result = self.uploader.client.table('curriculum_topics').insert(
                    topic_data
                ).execute()
                
                if result.data and len(result.data) > 0:
                    topic_uuid = result.data[0]['id']
                    code_to_uuid[topic_code] = topic_uuid  # Store for children
                    uploaded += 1
                    
                    indent = "  " * level
                    logger.debug(f"{indent}L{level}: {topic_code} {topic.get('title')[:40]}")
                    
                    # EXPAND content_points into Level 1 topics!
                    content_points = topic.get('content_points', [])
                    if content_points and level == 0:
                        for idx, point in enumerate(content_points, 1):
                            child_topic = {
                                'exam_board_subject_id': exam_board_subject_id,
                                'topic_code': f"{topic_code}.{idx}",
                                'topic_name': point,
                                'topic_level': 1,
                                'parent_topic_id': topic_uuid,  # Link to parent!
                                'description': point
                            }
                            
                            try:
                                child_result = self.uploader.client.table('curriculum_topics').insert(
                                    child_topic
                                ).execute()
                                
                                if child_result.data:
                                    uploaded += 1
                                    logger.debug(f"  └─ L1: {topic_code}.{idx} {point[:30]}")
                            except Exception as e:
                                logger.error(f"Error uploading child {topic_code}.{idx}: {e}")
                    
            except Exception as e:
                logger.error(f"Error uploading {topic.get('code')}: {e}")
        
        logger.info(f"[OK] Uploaded {uploaded} topics with proper hierarchy")
    
    def _upload_metadata_only(self, complete_data: dict, spec_url: str, pdf_url: str):
        """Upload just metadata/components/constraints, not topics."""
        
        if 'metadata' not in complete_data:
            complete_data['metadata'] = {}
        complete_data['metadata']['specification_url'] = spec_url
        complete_data['metadata']['specification_pdf_url'] = pdf_url
        
        # Skip topic upload in the standard method
        complete_data['options'] = []  # Clear options to skip topic upload
        
        self.uploader.upload_specification_complete(complete_data)
        logger.info("[OK] Uploaded metadata, components, constraints")
    
    def _build_specification_url(self, subject: str, qualification: str, code: str) -> str:
        subject_slug = subject.lower().replace(' ', '-')
        if 'art' in subject_slug:
            subject_slug = 'art-and-design'
        qual_slug = qualification.lower().replace(' ', '-')
        return f"https://www.aqa.org.uk/subjects/{subject_slug}/{qual_slug}/{subject_slug}-{code}/specification"
    
    def _find_pdf_on_page(self, url: str) -> str:
        response = requests.get(url, timeout=30)
        soup = BeautifulSoup(response.content, 'lxml')
        
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.I))
        for link in pdf_links:
            href = link.get('href')
            text = link.get_text().lower()
            if 'specification' in text or 'cdn.sanity' in href:
                return urljoin('https://www.aqa.org.uk', href)
        
        if pdf_links:
            return urljoin('https://www.aqa.org.uk', pdf_links[0].get('href'))
        return None
    
    def _download_pdf(self, url: str, subject: str, qualification: str, code: str) -> str:
        from utils.helpers import sanitize_filename, ensure_directory
        
        filename = f"{sanitize_filename(subject)}_{qualification}_{code}.pdf"
        output_dir = "data/raw/AQA/specifications"
        ensure_directory(output_dir)
        filepath = os.path.join(output_dir, filename)
        
        if os.path.exists(filepath):
            return filepath
        
        import requests
        response = requests.get(url, stream=True, timeout=60)
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        
        return filepath
    
    def close(self):
        self.web_scraper.close()


if __name__ == '__main__':
    print("Use test_upsert_accounting.py to test this!")

