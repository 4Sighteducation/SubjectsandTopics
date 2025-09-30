#!/usr/bin/env python
"""
Test Single Subject - Verify Complete Upload
Tests ONE subject to ensure everything uploads correctly before batch run
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

from database.supabase_client import SupabaseUploader
from scrapers.uk.aqa_hybrid_scraper import AQAHybridScraper

load_dotenv()

def test_subject(subject_name="History", qualification="A-Level", subject_code="7042"):
    """Test complete processing for one subject."""
    
    print("=" * 80)
    print(f"TESTING: {subject_name} ({qualification}) - Code {subject_code}")
    print("=" * 80)
    
    # Initialize
    uploader = SupabaseUploader()
    scraper = AQAHybridScraper(headless=True, supabase_uploader=uploader)
    
    try:
        # Process
        result = scraper.process_subject_complete(
            subject=subject_name,
            qualification=qualification,
            subject_code=subject_code,
            upload_to_supabase=True
        )
        
        print("\n" + "=" * 80)
        print("RESULT:")
        print("=" * 80)
        print(f"Success: {result['success']}")
        print(f"Method: {result.get('method')}")
        print(f"Errors: {result.get('errors')}")
        print("=" * 80)
        
        if result['success']:
            print("\nNow check Supabase:")
            print("="*80)
            
            # Find the specification_metadata we just created
            spec_result = uploader.client.table('specification_metadata').select('id').eq(
                'exam_board', 'AQA'
            ).eq('subject_name', subject_name).eq('qualification_type', qualification.lower().replace('-','_')).execute()
            
            if spec_result.data:
                spec_id = spec_result.data[0]['id']
                print(f"✓ Specification ID: {spec_id}")
                
                # Count components
                comp_count = uploader.client.table('spec_components').select('id', count='exact').eq('spec_metadata_id', spec_id).execute().count
                print(f"✓ Components: {comp_count}")
                
                # Count constraints
                const_count = uploader.client.table('selection_constraints').select('id', count='exact').eq('spec_metadata_id', spec_id).execute().count
                print(f"✓ Constraints: {const_count}")
                
                # Count topics
                # Find exam_board_subject
                ebs_result = uploader.client.table('exam_board_subjects').select('id').eq('subject_name', subject_name).execute()
                if ebs_result.data:
                    ebs_id = ebs_result.data[0]['id']
                    topic_count = uploader.client.table('curriculum_topics').select('id', count='exact').eq('exam_board_subject_id', ebs_id).execute().count
                    print(f"✓ Topics: {topic_count}")
                    
                    # Show sample topics
                    topics = uploader.client.table('curriculum_topics').select('topic_code,topic_name,topic_level,component_code,geographical_region,chronological_period').eq('exam_board_subject_id', ebs_id).limit(5).execute().data
                    print(f"\nSample topics:")
                    for t in topics:
                        print(f"  {t.get('topic_code')}: {t.get('topic_name')} (Level {t.get('topic_level')})")
                        if t.get('chronological_period'):
                            print(f"    Period: {t.get('chronological_period')}")
                        if t.get('geographical_region'):
                            print(f"    Region: {t.get('geographical_region')}")
            
            print("="*80)
            print("\n✓✓✓ TEST PASSED - Ready for full batch! ✓✓✓\n")
        else:
            print("\n✗✗✗ TEST FAILED - Need to fix issues first ✗✗✗\n")
            return 1
        
    finally:
        scraper.close()
    
    return 0

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--subject', default='History', help='Subject to test')
    parser.add_argument('--qual', default='A-Level', help='Qualification')
    parser.add_argument('--code', default='7042', help='Subject code')
    
    args = parser.parse_args()
    
    sys.exit(test_subject(args.subject, args.qual, args.code))
