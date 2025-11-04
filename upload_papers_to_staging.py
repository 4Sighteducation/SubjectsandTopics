"""
Upload scraped past papers to staging_aqa_exam_papers table
Companion to aqa_assessment_scraper.py
"""

import os
import sys
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from supabase import create_client
from utils.logger import get_logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = get_logger()


def upload_papers_to_staging(subject_code, qualification_type, papers_data):
    """
    Upload past papers to staging_aqa_exam_papers table.
    
    Args:
        subject_code: str (e.g., "7402")
        qualification_type: str ("A-Level" or "GCSE")
        papers_data: list of dicts from aqa_assessment_scraper
            [{
                'year': 2024,
                'series': 'June',
                'paper_number': 1,
                'doc_type': 'question_paper|mark_scheme|examiner_report',
                'url': '...',
                'title': 'Full title with component code'
            }]
    
    Returns:
        Number of paper sets uploaded
    """
    
    # Create Supabase client directly
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        logger.error("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in environment!")
        return 0
    
    supabase = create_client(supabase_url, supabase_key)
    
    # 1. Get subject ID from staging_aqa_subjects
    result = supabase.table('staging_aqa_subjects')\
        .select('id')\
        .eq('subject_code', subject_code)\
        .eq('qualification_type', qualification_type)\
        .execute()
    
    if not result.data:
        logger.error(f"Subject {subject_code} ({qualification_type}) not found in staging_aqa_subjects!")
        logger.error("Run crawl-aqa-subject-complete.js first to create the subject.")
        return 0
    
    subject_id = result.data[0]['id']
    logger.info(f"Found subject ID: {subject_id}")
    
    # 2. Extract component codes and group papers
    # For History: "Component 1H" or "Component 2S" in title
    paper_sets = {}
    
    for paper in papers_data:
        # Extract component code from title
        title = paper.get('title', '')
        component_match = re.search(r'Component\s+(\d+[A-Z])', title, re.IGNORECASE)
        component_code = component_match.group(1) if component_match else None
        
        # For History, group by: year + series + component code
        # For other subjects without components, group by: year + series + paper number
        if component_code:
            key = f"{paper['year']}-{paper['series']}-{component_code}"
        else:
            key = f"{paper['year']}-{paper['series']}-P{paper['paper_number']}"
        
        if key not in paper_sets:
            paper_sets[key] = {
                'subject_id': subject_id,
                'year': paper['year'],
                'exam_series': paper['series'],
                'paper_number': paper['paper_number'],
                'tier': None,  # A-Level doesn't have tiers
                'component_code': component_code,  # NEW: Track component
                'question_paper_url': None,
                'mark_scheme_url': None,
                'examiner_report_url': None
            }
        
        # Add URL based on document type
        if paper['doc_type'] == 'question_paper':
            paper_sets[key]['question_paper_url'] = paper['url']
        elif paper['doc_type'] == 'mark_scheme':
            paper_sets[key]['mark_scheme_url'] = paper['url']
        elif paper['doc_type'] == 'examiner_report':
            paper_sets[key]['examiner_report_url'] = paper['url']
    
    sets_to_upload = list(paper_sets.values())
    
    logger.info(f"Grouped into {len(sets_to_upload)} complete paper sets")
    
    # 3. Delete existing papers for this subject (clean slate)
    delete_result = supabase.table('staging_aqa_exam_papers')\
        .delete()\
        .eq('subject_id', subject_id)\
        .execute()
    
    logger.info(f"Cleared old papers for subject")
    
    # 4. Insert new papers
    insert_result = supabase.table('staging_aqa_exam_papers')\
        .insert(sets_to_upload)\
        .execute()
    
    if insert_result.data:
        logger.info(f"✅ Uploaded {len(insert_result.data)} paper sets")
        
        # Show breakdown
        by_year = {}
        for paper in insert_result.data:
            year = paper['year']
            by_year[year] = by_year.get(year, 0) + 1
        
        logger.info(f"Breakdown by year:")
        for year in sorted(by_year.keys(), reverse=True):
            year_papers = [p for p in insert_result.data if p['year'] == year]
            with_mark = len([p for p in year_papers if p['mark_scheme_url']])
            with_report = len([p for p in year_papers if p['examiner_report_url']])
            logger.info(f"  {year}: {by_year[year]} papers ({with_mark} with marks, {with_report} with reports)")
        
        return len(insert_result.data)
    else:
        logger.error("Upload failed!")
        return 0


if __name__ == '__main__':
    # Test with sample data
    test_papers = [
        {
            'year': 2024,
            'series': 'June',
            'paper_number': 1,
            'doc_type': 'question_paper',
            'url': 'https://cdn.sanity.io/files/p28bar15/green/abc123.pdf'
        },
        {
            'year': 2024,
            'series': 'June',
            'paper_number': 1,
            'doc_type': 'mark_scheme',
            'url': 'https://cdn.sanity.io/files/p28bar15/green/def456.pdf'
        }
    ]
    
    count = upload_papers_to_staging('7402', 'A-Level', test_papers)
    print(f"\nUploaded {count} paper sets")

