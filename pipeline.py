#!/usr/bin/env python
"""
FLASH Curriculum Pipeline - Main Orchestrator
Complete end-to-end automation: URLs → PDFs → Extraction → Supabase

ONE COMMAND to process everything!
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from database.supabase_client import SupabaseUploader
from scrapers.uk.aqa_scraper_enhanced import AQAScraperEnhanced
from utils.logger import setup_logger

# Load environment
load_dotenv()

def validate_environment():
    """Check all required environment variables are set."""
    required = ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'ANTHROPIC_API_KEY']
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print(f"\nPlease set these in your .env file:")
        for var in missing:
            print(f"  {var}=your_value_here")
        return False
    
    return True


def main():
    """Main pipeline entry point."""
    
    parser = argparse.ArgumentParser(
        description='FLASH Curriculum Pipeline - Automated scraping and extraction'
    )
    parser.add_argument('--board', 
                       choices=['AQA', 'Edexcel', 'OCR', 'WJEC', 'SQA', 'CCEA', 'all'],
                       default='AQA',
                       help='Exam board to process')
    parser.add_argument('--subject',
                       help='Specific subject to process (default: all)')
    parser.add_argument('--exam-type',
                       choices=['GCSE', 'A-Level', 'all'],
                       default='all',
                       help='Qualification type')
    parser.add_argument('--no-upload',
                       action='store_true',
                       help='Extract only, do not upload to Supabase')
    parser.add_argument('--test-mode',
                       action='store_true',
                       help='Test mode: process one subject only')
    
    args = parser.parse_args()
    
    # Setup logging
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'data/logs/pipeline_{timestamp}.log'
    logger = setup_logger('INFO', log_file)
    
    logger.info("=" * 80)
    logger.info("FLASH CURRICULUM PIPELINE - Starting")
    logger.info("=" * 80)
    logger.info(f"Board: {args.board}")
    logger.info(f"Subject: {args.subject or 'all'}")
    logger.info(f"Exam Type: {args.exam_type}")
    logger.info(f"Upload: {not args.no_upload}")
    logger.info(f"Test Mode: {args.test_mode}")
    logger.info("=" * 80)
    
    # Validate environment
    if not validate_environment():
        return 1
    
    # Initialize Supabase uploader
    uploader = None
    if not args.no_upload:
        try:
            uploader = SupabaseUploader()
            logger.info("Supabase uploader initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
            return 1
    
    # Process based on board selection
    if args.board == 'AQA' or args.board == 'all':
        process_aqa(args, uploader, logger)
    
    # Add other boards here as we develop them
    # if args.board == 'OCR' or args.board == 'all':
    #     process_ocr(args, uploader, logger)
    
    logger.info("\n" + "=" * 80)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 80)
    
    return 0


def process_aqa(args, uploader, logger):
    """Process AQA exam board."""
    logger.info("\n" + "=" * 80)
    logger.info("Processing AQA Exam Board")
    logger.info("=" * 80)
    
    # Initialize scraper
    scraper = AQAScraperEnhanced(
        headless=True,
        supabase_uploader=uploader
    )
    
    # Define subjects to process
    subjects = []
    
    if args.subject:
        # Process specific subject
        subjects = [(args.subject, args.exam_type)]
    elif args.test_mode:
        # Test mode: just process History A-Level
        subjects = [('History', 'A-Level')]
        logger.info("TEST MODE: Processing History A-Level only")
    else:
        # Process all subjects
        subjects = get_all_aqa_subjects(args.exam_type)
    
    # Process each subject
    total = len(subjects)
    successes = 0
    failures = 0
    
    for i, (subject, exam_type) in enumerate(subjects, 1):
        logger.info(f"\n[{i}/{total}] Processing {subject} ({exam_type})...")
        
        try:
            results = scraper.process_subject_complete(
                subject=subject,
                exam_type=exam_type,
                upload_to_supabase=not args.no_upload
            )
            
            if results['success']:
                successes += 1
            else:
                failures += 1
                logger.warning(f"Failed: {subject} - {results.get('errors')}")
                
        except Exception as e:
            failures += 1
            logger.error(f"Error processing {subject}: {e}")
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info(f"AQA PROCESSING COMPLETE")
    logger.info(f"  Successful: {successes}/{total}")
    logger.info(f"  Failed: {failures}/{total}")
    logger.info(f"{'='*80}")
    
    scraper.close()


def get_all_aqa_subjects(exam_type: str) -> list:
    """Get list of all AQA subjects to process."""
    # For now, return a curated list of major subjects
    # Expand this as needed
    
    subjects = [
        ('History', 'A-Level'),
        ('Mathematics', 'A-Level'),
        ('Biology', 'A-Level'),
        ('Chemistry', 'A-Level'),
        ('Physics', 'A-Level'),
        ('English Literature', 'A-Level'),
        ('Psychology', 'A-Level'),
        ('Sociology', 'A-Level'),
        ('Geography', 'A-Level'),
        ('Economics', 'A-Level'),
        
        ('History', 'GCSE'),
        ('Mathematics', 'GCSE'),
        ('Biology', 'GCSE'),
        ('Chemistry', 'GCSE'),
        ('Physics', 'GCSE'),
    ]
    
    # Filter by exam_type if specified
    if exam_type and exam_type != 'all':
        subjects = [(s, t) for s, t in subjects if t == exam_type]
    
    return subjects


if __name__ == '__main__':
    exit(main())
