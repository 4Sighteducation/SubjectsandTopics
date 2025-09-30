#!/usr/bin/env python
"""
Batch Assessment Resources Scraper
Scrapes past papers + mark schemes for all AQA subjects
"""

import os
import sys
import yaml
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

from database.supabase_client import SupabaseUploader
from scrapers.uk.aqa_assessment_scraper import AQAAssessmentScraper
from utils.logger import setup_logger
from collections import Counter

load_dotenv()


def upload_papers_to_supabase(papers_data, uploader):
    """Upload papers to Supabase."""
    exam_board_subject_id = uploader._get_or_create_exam_board_subject(
        'AQA',
        papers_data['subject'],
        papers_data['qualification'],
        papers_data['code']
    )
    
    if not exam_board_subject_id:
        return 0
    
    # Group by year/series/paper_number
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
    
    # Upload
    uploaded = 0
    for (year, series, paper_num), urls in grouped.items():
        try:
            uploader.client.table('exam_papers').upsert({
                'exam_board_subject_id': exam_board_subject_id,
                'year': year,
                'exam_series': series,
                'paper_number': paper_num,
                'question_paper_url': urls['question_paper_url'],
                'mark_scheme_url': urls['mark_scheme_url'],
                'examiner_report_url': urls['examiner_report_url']
            }).execute()
            
            uploaded += 1
            
        except Exception as e:
            print(f"Error uploading {year} {series} P{paper_num}: {e}")
    
    return uploaded


def main():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'data/logs/assessment_batch_{timestamp}.log'
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logger = setup_logger('INFO', log_file)
    
    # State file for resumability
    state_file = f'data/state/assessment_batch_state_{timestamp}.json'
    Path(state_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Load or create state
    import json
    if os.path.exists(state_file):
        with open(state_file) as f:
            state = json.load(f)
        logger.info(f"Resuming from previous run: {len(state['completed'])} already done")
    else:
        state = {'completed': [], 'failed': [], 'timestamp': timestamp}
    
    logger.info("=" * 80)
    logger.info("ASSESSMENT RESOURCES BATCH SCRAPER")
    logger.info("=" * 80)
    
    # Load subjects from config
    config_path = Path(__file__).parent / 'config' / 'aqa_subjects.yaml'
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    subjects = []
    
    # A-Level subjects (skip Art variants)
    art_added = False
    for subject_key, subject_code in config['a_level'].items():
        subject_name = subject_key.replace('_', ' ')
        if 'Art and Design' in subject_name:
            if not art_added:
                subjects.append(('Art and Design', 'A-Level', '7201'))
                art_added = True
            continue
        subjects.append((subject_name, 'A-Level', subject_code))
    
    # GCSE subjects (skip Art variants)
    art_added = False
    for subject_key, subject_code in config['gcse'].items():
        subject_name = subject_key.replace('_', ' ')
        if 'Art and Design' in subject_name:
            if not art_added:
                subjects.append(('Art and Design', 'GCSE', '8201'))
                art_added = True
            continue
        subjects.append((subject_name, 'GCSE', subject_code))
    
    # Filter out completed subjects
    subjects = [
        s for s in subjects 
        if f"{s[0]}_{s[1]}" not in state['completed']
    ]
    
    logger.info(f"Processing assessment resources for {len(subjects)} subjects")
    logger.info(f"Already completed: {len(state['completed'])}\n")
    
    # Initialize
    uploader = SupabaseUploader()
    scraper = None  # Will create/recreate as needed
    
    total_uploaded = 0
    successes = 0
    failures = 0
    subjects_since_restart = 0
    
    try:
        for i, (subject, qual, code) in enumerate(subjects, 1):
            subject_id = f"{subject}_{qual}"
            logger.info(f"[{i}/{len(subjects)}] {subject} ({qual}) - {code}")
            
            # Restart browser every 10 subjects to prevent crashes
            if subjects_since_restart == 0 or subjects_since_restart >= 10:
                if scraper:
                    logger.info("  Restarting browser to prevent crashes...")
                    scraper.close()
                scraper = AQAAssessmentScraper(headless=True)
                subjects_since_restart = 0
            
            try:
                # Scrape
                result = scraper.scrape_assessment_resources(
                    subject=subject,
                    qualification=qual,
                    subject_code=code,
                    years=[2024, 2023, 2022]
                )
                
                if result['papers']:
                    breakdown = Counter(p['doc_type'] for p in result['papers'])
                    logger.info(f"  Found: {dict(breakdown)}")
                    
                    # Upload
                    count = upload_papers_to_supabase(result, uploader)
                    logger.info(f"  Uploaded: {count} exam papers")
                    
                    total_uploaded += count
                    successes += 1
                    state['completed'].append(subject_id)
                else:
                    logger.warning(f"  No papers found")
                    failures += 1
                    state['failed'].append(subject_id)
                    
            except Exception as e:
                logger.error(f"  Error: {e}")
                failures += 1
                state['failed'].append(subject_id)
            
            finally:
                subjects_since_restart += 1
                # Save state after each subject
                with open(state_file, 'w') as f:
                    json.dump(state, f, indent=2)
        
        logger.info("\n" + "=" * 80)
        logger.info("BATCH COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Subjects processed: {len(subjects)}")
        logger.info(f"Successes: {successes}")
        logger.info(f"Failures: {failures}")
        logger.info(f"Total papers uploaded: {total_uploaded}")
        logger.info("=" * 80)
        
    finally:
        scraper.close()


if __name__ == '__main__':
    main()
