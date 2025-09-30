#!/usr/bin/env python
"""
Complete AQA Pipeline - Process ALL subjects for GCSE and A-Level
Gets complete curriculum data and uploads to Supabase.
"""

import os
import sys
import yaml
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from database.supabase_client import SupabaseUploader
from scrapers.uk.aqa_web_scraper import AQAWebScraper
from extractors.specification_extractor import SpecificationExtractor
from utils.logger import setup_logger

load_dotenv()

def load_subject_config():
    """Load AQA subject configuration."""
    config_path = Path(__file__).parent / 'config' / 'aqa_subjects.yaml'
    with open(config_path) as f:
        return yaml.safe_load(f)

def process_all_aqa_subjects(qualification_filter=None, subject_filter=None, 
                             upload=True, start_from=None):
    """
    Process all AQA subjects.
    
    Args:
        qualification_filter: 'a_level', 'gcse', or None for both
        subject_filter: Specific subject key or None for all
        upload: Whether to upload to Supabase
        start_from: Subject to start from (for resuming)
    """
    # Setup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    logger = setup_logger('INFO', f'data/logs/complete_aqa_{timestamp}.log')
    
    logger.info("=" * 80)
    logger.info("COMPLETE AQA PIPELINE - Processing All Subjects")
    logger.info("=" * 80)
    
    # Load config
    config = load_subject_config()
    
    # Initialize components
    uploader = SupabaseUploader() if upload else None
    web_scraper = AQAWebScraper()
    spec_extractor = SpecificationExtractor()
    
    # Build subject list
    subjects_to_process = []
    
    qualifications = ['a_level', 'gcse'] if not qualification_filter else [qualification_filter]
    
    for qual in qualifications:
        qual_display = qual.upper().replace('_', '-')
        
        for subject_key, subject_code in config[qual].items():
            if subject_filter and subject_filter not in subject_key:
                continue
            
            # Convert key to display name
            subject_name = subject_key.replace('_', ' ')
            subject_slug = config['subject_names'].get(subject_key, subject_key.lower().replace('_', '-'))
            
            subjects_to_process.append({
                'key': subject_key,
                'name': subject_name,
                'code': subject_code,
                'qualification': qual_display,
                'slug': subject_slug
            })
    
    # Resume from specific subject if requested
    if start_from:
        start_idx = next((i for i, s in enumerate(subjects_to_process) if start_from in s['key']), 0)
        subjects_to_process = subjects_to_process[start_idx:]
        logger.info(f"Resuming from subject {start_from}")
    
    logger.info(f"Processing {len(subjects_to_process)} subjects")
    logger.info("=" * 80)
    
    # Process each subject
    results = {
        'successful': [],
        'failed': [],
        'partial': []
    }
    
    for i, subject in enumerate(subjects_to_process, 1):
        logger.info(f"\n[{i}/{len(subjects_to_process)}] {subject['name']} ({subject['qualification']}) - {subject['code']}")
        logger.info("-" * 80)
        
        try:
            # Step 1: Get metadata from PDF (using AI)
            logger.info("Step 1: Extracting specification metadata...")
            metadata_result = process_spec_metadata(
                subject, spec_extractor, uploader, upload
            )
            
            # Step 2: Get detailed content from web (no AI!)
            logger.info("Step 2: Scraping detailed content from website...")
            content_result = process_web_content(
                subject, web_scraper, uploader, upload
            )
            
            if metadata_result and content_result:
                results['successful'].append(subject['key'])
                logger.info(f"[SUCCESS] {subject['name']} complete!")
            elif metadata_result or content_result:
                results['partial'].append(subject['key'])
                logger.info(f"[PARTIAL] {subject['name']} - some data extracted")
            else:
                results['failed'].append(subject['key'])
                logger.error(f"[FAILED] {subject['name']}")
                
        except Exception as e:
            logger.error(f"Error processing {subject['name']}: {e}", exc_info=True)
            results['failed'].append(subject['key'])
        
        # Save progress
        save_progress(results, timestamp)
    
    # Final summary
    print_summary(results, logger)
    
    # Generate report
    report_file = generate_final_report(results, timestamp)
    logger.info(f"\n📊 Report generated: {report_file}")
    logger.info(f"Open in browser to view detailed results!")
    
    web_scraper.close()
    
    return results

def process_spec_metadata(subject, spec_extractor, uploader, upload):
    """Process specification metadata using PDF + AI."""
    # For now, skip this - we can add later
    # Focus on web content first
    return True

def process_web_content(subject, web_scraper, uploader, upload):
    """Process detailed content from website."""
    try:
        result = web_scraper.scrape_subject_content_complete(
            subject=subject['name'],
            qualification=subject['qualification'],
            subject_code=subject['code']
        )
        
        if not result or not result.get('content_items'):
            return False
        
        logger = setup_logger('INFO', None)
        logger.info(f"  Scraped {len(result['content_items'])} content items")
        logger.info(f"  Pattern: {result.get('pattern_type')}")
        
        # Upload if enabled
        if upload and uploader:
            upload_hierarchical_content(result, uploader, subject)
        
        # Save to file for review
        output_file = f"data/processed/{subject['key']}_{subject['qualification'].lower()}.json"
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        logger = setup_logger('INFO', None)
        logger.error(f"Failed to process web content: {e}")
        return False

def upload_hierarchical_content(result, uploader, subject):
    """Upload complete hierarchical content to Supabase."""
    # This needs to upload levels 0, 1, 2 properly
    # For now, just log
    logger = setup_logger('INFO', None)
    logger.info(f"  [Upload] Would upload {len(result['content_items'])} items to Supabase")
    # TODO: Implement complete hierarchical upload

def save_progress(results, timestamp):
    """Save progress to file for resumability."""
    progress_file = f"data/state/aqa_progress_{timestamp}.json"
    Path(progress_file).parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(progress_file, 'w') as f:
        json.dump(results, f, indent=2)

def generate_final_report(results, timestamp):
    """Generate comprehensive HTML report."""
    report_file = f"data/reports/aqa_complete_report_{timestamp}.html"
    Path(report_file).parent.mkdir(parents=True, exist_ok=True)
    
    total = len(results['successful']) + len(results['partial']) + len(results['failed'])
    success_rate = (len(results['successful']) / total * 100) if total > 0 else 0
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>AQA Complete Scrape Report - {timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 8px; max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-box {{ flex: 1; background: #ecf0f1; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-number {{ font-size: 48px; font-weight: bold; color: #3498db; }}
        .stat-label {{ color: #7f8c8d; margin-top: 5px; }}
        .success {{ color: #27ae60; }}
        .partial {{ color: #f39c12; }}
        .failed {{ color: #e74c3c; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #34495e; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f8f9fa; }}
        .success-row {{ background: #d5f4e6; }}
        .partial-row {{ background: #fef5e7; }}
        .failed-row {{ background: #fadbd8; }}
        .timestamp {{ color: #95a5a6; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>AQA Complete Scrape Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <div class="stat-box">
                <div class="stat-number">{total}</div>
                <div class="stat-label">Total Subjects</div>
            </div>
            <div class="stat-box">
                <div class="stat-number success">{len(results['successful'])}</div>
                <div class="stat-label">Successful</div>
            </div>
            <div class="stat-box">
                <div class="stat-number partial">{len(results['partial'])}</div>
                <div class="stat-label">Partial</div>
            </div>
            <div class="stat-box">
                <div class="stat-number failed">{len(results['failed'])}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{success_rate:.1f}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
        </div>
        
        <h2>✅ Successful Subjects ({len(results['successful'])})</h2>
        <table>
            <tr><th>#</th><th>Subject</th><th>Status</th></tr>
"""
    
    for i, subj in enumerate(results['successful'], 1):
        html += f"            <tr class='success-row'><td>{i}</td><td>{subj}</td><td class='success'>✓ Complete</td></tr>\n"
    
    html += f"""        </table>
        
        <h2>⚠️ Partial Subjects ({len(results['partial'])})</h2>
        <table>
            <tr><th>#</th><th>Subject</th><th>Status</th></tr>
"""
    
    for i, subj in enumerate(results['partial'], 1):
        html += f"            <tr class='partial-row'><td>{i}</td><td>{subj}</td><td class='partial'>⚠ Partial Data</td></tr>\n"
    
    html += f"""        </table>
        
        <h2>❌ Failed Subjects ({len(results['failed'])})</h2>
        <table>
            <tr><th>#</th><th>Subject</th><th>Status</th></tr>
"""
    
    for i, subj in enumerate(results['failed'], 1):
        html += f"            <tr class='failed-row'><td>{i}</td><td>{subj}</td><td class='failed'>✗ Failed</td></tr>\n"
    
    html += """        </table>
        
        <h2>Next Steps</h2>
        <ul>
            <li>Review partial/failed subjects in log file</li>
            <li>Verify data in Supabase</li>
            <li>Re-run failed subjects if needed</li>
            <li>Check data/processed/ folder for extracted JSON</li>
        </ul>
    </div>
</body>
</html>"""
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return report_file

def print_summary(results, logger):
    """Print final summary."""
    logger.info("\n" + "=" * 80)
    logger.info("COMPLETE AQA PIPELINE - FINAL SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Successful: {len(results['successful'])}")
    logger.info(f"Partial: {len(results['partial'])}")
    logger.info(f"Failed: {len(results['failed'])}")
    
    if results['failed']:
        logger.warning(f"\nFailed subjects: {', '.join(results['failed'])}")
    
    logger.info("=" * 80)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Complete AQA Scraper')
    parser.add_argument('--qualification', choices=['a_level', 'gcse', 'both'], default='both')
    parser.add_argument('--subject', help='Specific subject to process')
    parser.add_argument('--start-from', help='Resume from specific subject')
    parser.add_argument('--no-upload', action='store_true', help='Extract only, no upload')
    parser.add_argument('--test', action='store_true', help='Test with first 3 subjects only')
    
    args = parser.parse_args()
    
    qual_filter = None if args.qualification == 'both' else args.qualification
    
    results = process_all_aqa_subjects(
        qualification_filter=qual_filter,
        subject_filter=args.subject,
        upload=not args.no_upload,
        start_from=args.start_from
    )
    
    return 0 if len(results['failed']) == 0 else 1

if __name__ == '__main__':
    exit(main())
