#!/usr/bin/env python
"""
Upload Assessment Resources to Supabase
Takes scraped papers and uploads to exam_papers table
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

from database.supabase_client import SupabaseUploader
from scrapers.uk.aqa_assessment_scraper import AQAAssessmentScraper

load_dotenv()


def upload_papers_to_supabase(papers_data: dict, uploader: SupabaseUploader):
    """
    Upload assessment papers to Supabase exam_papers table.
    
    Args:
        papers_data: Output from scraper.scrape_assessment_resources()
        uploader: SupabaseUploader instance
    """
    # Find exam_board_subject_id
    exam_board_subject_id = uploader._get_or_create_exam_board_subject(
        'AQA',
        papers_data['subject'],
        papers_data['qualification'],
        papers_data['code']
    )
    
    if not exam_board_subject_id:
        print(f"ERROR: Could not find exam_board_subject")
        return 0
    
    # Group papers by year/series/paper_number
    from collections import defaultdict
    grouped = defaultdict(lambda: {
        'question_paper_url': None,
        'mark_scheme_url': None,
        'examiner_report_url': None
    })
    
    for paper in papers_data['papers']:
        key = (paper['year'], paper['series'], paper['paper_number'])
        
        if paper['doc_type'] == 'question_paper':
            grouped[key]['question_paper_url'] = paper['url']
        elif paper['doc_type'] == 'mark_scheme':
            grouped[key]['mark_scheme_url'] = paper['url']
        elif paper['doc_type'] == 'examiner_report':
            grouped[key]['examiner_report_url'] = paper['url']
    
    # Upload to Supabase
    uploaded = 0
    
    for (year, series, paper_num), urls in grouped.items():
        try:
            paper_data = {
                'exam_board_subject_id': exam_board_subject_id,
                'year': year,
                'exam_series': series,
                'paper_number': paper_num,
                'question_paper_url': urls['question_paper_url'],
                'mark_scheme_url': urls['mark_scheme_url'],
                'examiner_report_url': urls['examiner_report_url']
            }
            
            # Upsert (update if exists, insert if new)
            uploader.client.table('exam_papers').upsert(
                paper_data,
                on_conflict='exam_board_subject_id,year,exam_series,paper_number'
            ).execute()
            
            uploaded += 1
            print(f"✓ Uploaded: {year} {series} Paper {paper_num}")
            
        except Exception as e:
            print(f"✗ Failed: {year} {series} Paper {paper_num}: {e}")
    
    return uploaded


def main():
    """Test with Biology."""
    print("="*60)
    print("ASSESSMENT RESOURCES UPLOAD TEST")
    print("="*60)
    
    # Initialize
    uploader = SupabaseUploader()
    scraper = AQAAssessmentScraper(headless=True)
    
    try:
        # Scrape Biology papers
        print("\nScraping Biology A-Level assessment resources...")
        result = scraper.scrape_assessment_resources(
            subject="Biology",
            qualification="A-Level",
            subject_code="7402",
            years=[2024, 2023, 2022]
        )
        
        print(f"Found {len(result['papers'])} documents")
        
        # Show breakdown
        from collections import Counter
        breakdown = Counter(p['doc_type'] for p in result['papers'])
        print(f"\nBreakdown by type:")
        for doc_type, count in breakdown.items():
            print(f"  {doc_type}: {count}")
        
        # Upload to Supabase
        print("\nUploading to Supabase...")
        count = upload_papers_to_supabase(result, uploader)
        
        print(f"\n✓ Uploaded {count} exam papers to Supabase!")
        print("\nCheck Supabase with:")
        print("SELECT * FROM exam_papers WHERE exam_board_subject_id IN (")
        print("  SELECT id FROM exam_board_subjects WHERE subject_name = 'Biology'")
        print(") ORDER BY year DESC, paper_number;")
        
    finally:
        scraper.close()


if __name__ == '__main__':
    main()
