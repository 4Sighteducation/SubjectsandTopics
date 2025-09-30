#!/usr/bin/env python
"""
Test enhanced extraction with AQA History A-Level.
This will test the complete specification extraction including constraints.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.specification_extractor import SpecificationExtractor
from database.supabase_client import SupabaseUploader
from utils.logger import setup_logger

# Load environment
load_dotenv()

def main():
    # Setup logging
    logger = setup_logger('INFO', 'data/logs/test_aqa_history.log')
    logger.info("=" * 60)
    logger.info("Testing Enhanced Extraction: AQA History A-Level")
    logger.info("=" * 60)
    
    # Check for API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        logger.error("ANTHROPIC_API_KEY not set in .env file")
        return 1
    
    # Initialize extractor
    logger.info("Initializing SpecificationExtractor...")
    extractor = SpecificationExtractor()
    
    # Path to AQA History specification PDF
    # You'll need to download this first or point to existing file
    pdf_path = "data/raw/AQA/specifications/History_A-Level_7042.pdf"
    
    if not Path(pdf_path).exists():
        logger.warning(f"PDF not found at {pdf_path}")
        logger.info("Please download from: https://www.aqa.org.uk/subjects/history/a-level/history-7042/specification")
        logger.info("Or provide path to existing PDF")
        
        # Try to find any history PDF in the data folder
        possible_pdfs = list(Path("data").rglob("*history*.pdf"))
        if possible_pdfs:
            logger.info(f"Found possible History PDFs:")
            for i, pdf in enumerate(possible_pdfs):
                logger.info(f"  [{i+1}] {pdf}")
            
            choice = input("Enter number to use (or 0 to skip): ")
            if choice.isdigit() and int(choice) > 0:
                pdf_path = str(possible_pdfs[int(choice) - 1])
                logger.info(f"Using: {pdf_path}")
            else:
                return 1
        else:
            return 1
    
    # Extract complete specification
    logger.info(f"\nExtracting from: {pdf_path}")
    logger.info("This may take 2-3 minutes as AI analyzes the specification...\n")
    
    try:
        complete_data = extractor.extract_complete_specification(
            pdf_path=pdf_path,
            subject="History",
            exam_board="AQA",
            qualification="A-Level"
        )
        
        # Save results to JSON for review
        output_file = "data/test_aqa_history_complete.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(complete_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✅ Extraction complete! Saved to {output_file}")
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("EXTRACTION SUMMARY")
        logger.info("=" * 60)
        
        if complete_data.get('metadata'):
            meta = complete_data['metadata']
            logger.info(f"Subject Code: {meta.get('subject_code')}")
            logger.info(f"Description: {meta.get('description', '')[:100]}...")
        
        if complete_data.get('components'):
            logger.info(f"\nComponents Found: {len(complete_data['components'])}")
            for comp in complete_data['components']:
                logger.info(f"  - {comp.get('name')}: {comp.get('selection_type')}")
        
        if complete_data.get('constraints'):
            logger.info(f"\nConstraints Found: {len(complete_data['constraints'])}")
            for const in complete_data['constraints']:
                logger.info(f"  - {const.get('type')}: {const.get('description', '')[:80]}...")
        
        if complete_data.get('options'):
            logger.info(f"\nTopic Options Found: {len(complete_data['options'])}")
            logger.info("Sample options:")
            for opt in complete_data['options'][:3]:
                logger.info(f"  - {opt.get('code')}: {opt.get('title')}")
        
        if complete_data.get('vocabulary'):
            logger.info(f"\nVocabulary Terms Found: {len(complete_data['vocabulary'])}")
        
        # Ask if user wants to upload to Supabase
        logger.info("\n" + "=" * 60)
        upload = input("\nUpload this data to Supabase? (y/n): ")
        
        if upload.lower() == 'y':
            logger.info("\nUploading to Supabase...")
            
            # Check for Supabase credentials
            if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_SERVICE_KEY'):
                logger.error("Supabase credentials not set in .env file")
                return 1
            
            uploader = SupabaseUploader()
            results = uploader.upload_specification_complete(complete_data)
            
            logger.info("\n✅ Upload complete!")
            logger.info(f"Metadata ID: {results.get('metadata_id')}")
            logger.info(f"Components uploaded: {results.get('components')}")
            logger.info(f"Constraints uploaded: {results.get('constraints')}")
            logger.info(f"Topics uploaded: {results.get('topics')}")
            logger.info(f"Vocabulary terms uploaded: {results.get('vocabulary')}")
            
            if results.get('errors'):
                logger.warning(f"Errors: {results.get('errors')}")
        else:
            logger.info("Skipping upload. You can upload later using the saved JSON file.")
        
        logger.info("\n" + "=" * 60)
        logger.info("Test complete! Check the JSON file for full details.")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"\n❌ Error during extraction: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())
