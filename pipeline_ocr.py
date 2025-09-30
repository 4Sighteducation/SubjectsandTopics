#!/usr/bin/env python
"""
Complete OCR Pipeline - All qualifications, all subjects
"""

import os
import time
import yaml
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from scrapers.uk.ocr_complete_scraper import OCRCompleteScraper
from database.supabase_client import SupabaseUploader
from utils.logger import setup_logger
import json

load_dotenv()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Complete OCR Scraper')
    parser.add_argument('--qualification', 
                       choices=['a_level', 'gcse', 'all'], 
                       default='all',
                       help='Qualification type to scrape')
    parser.add_argument('--subject', help='Specific subject to process')
    parser.add_argument('--no-upload', action='store_true')
    parser.add_argument('--test', action='store_true', help='Test with first 3 subjects')
    
    args = parser.parse_args()
    
    # Setup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    logger = setup_logger('INFO', f'data/logs/ocr_complete_{timestamp}.log')
    
    logger.info("=" * 80)
    logger.info("COMPLETE OCR PIPELINE - Starting")
    logger.info("=" * 80)
    
    # Initialize
    scraper = OCRCompleteScraper()
    uploader = SupabaseUploader() if not args.no_upload else None
    
    # Load config
    config_path = Path(__file__).parent / 'config' / 'ocr_subjects.yaml'
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Build subject list
    qualifications = ['a_level', 'gcse'] if args.qualification == 'all' else [args.qualification]
    
    subjects_to_process = []
    for qual in qualifications:
        for subject_key in config[qual].keys():
            if args.subject and args.subject not in subject_key:
                continue
            subjects_to_process.append((subject_key, qual))
    
    if args.test:
        subjects_to_process = subjects_to_process[:3]
        logger.info(f"TEST MODE: Processing first 3 subjects only")
    
    logger.info(f"Processing {len(subjects_to_process)} OCR subjects")
    logger.info("=" * 80)
    
    # Process each subject
    results = {'successful': [], 'failed': [], 'partial': []}
    
    for i, (subject_key, qual) in enumerate(subjects_to_process, 1):
        logger.info(f"\n[{i}/{len(subjects_to_process)}] {subject_key} ({qual.upper()})")
        logger.info("-" * 80)
        
        try:
            result = scraper.scrape_subject_complete(subject_key, qual)
            
            if result and result.get('content_structure'):
                # Save to JSON
                output_file = f"data/processed/ocr_{subject_key}_{qual}.json"
                Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                logger.info(f"  Saved to: {output_file}")
                logger.info(f"  Unit groups: {len(result.get('overview', {}).get('unit_groups', []))}")
                logger.info(f"  Content items: {len(result.get('content_structure', []))}")
                
                results['successful'].append(subject_key)
            else:
                logger.warning(f"  No content extracted")
                results['partial'].append(subject_key)
                
        except Exception as e:
            logger.error(f"  Failed: {e}")
            results['failed'].append(subject_key)
        
        time.sleep(2)  # Be polite to OCR servers
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("OCR PIPELINE COMPLETE")
    logger.info(f"  Successful: {len(results['successful'])}")
    logger.info(f"  Partial: {len(results['partial'])}")
    logger.info(f"  Failed: {len(results['failed'])}")
    logger.info("=" * 80)
    
    # Save results
    results_file = f"data/reports/ocr_results_{timestamp}.json"
    Path(results_file).parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\nResults saved to: {results_file}")
    
    scraper.close()
    
    return 0 if len(results['failed']) == 0 else 1


if __name__ == '__main__':
    exit(main())
