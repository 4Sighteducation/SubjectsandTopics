"""
Edexcel A-Level - Batch Runner
Runs topics and papers scrapers for all subjects

Usage:
    python run-all-subjects.py                    # Run all subjects
    python run-all-subjects.py --topics-only      # Topics only
    python run-all-subjects.py --papers-only      # Papers only
    python run-all-subjects.py --start-from 9CH0  # Start from specific subject
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

# Paths
SCRIPT_DIR = Path(__file__).parent
TOPICS_SCRAPER = SCRIPT_DIR / 'topics' / 'scrape-edexcel-universal.py'
PAPERS_SCRAPER = SCRIPT_DIR / 'papers' / 'scrape-edexcel-papers-universal.py'
SUBJECTS_FILE = SCRIPT_DIR / 'edexcel-alevel-subjects.json'
LOG_FILE = SCRIPT_DIR / f'batch-run-{datetime.now().strftime("%Y%m%d-%H%M%S")}.log'


def log(message):
    """Log to console and file."""
    print(message)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(message + '\n')


def run_scraper(script_path, args, timeout=600):
    """Run a scraper script with arguments."""
    try:
        # Set environment to force UTF-8
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            [sys.executable, str(script_path)] + args,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
            env=env
        )
        
        return result.returncode == 0, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        return False, "", f"Timeout after {timeout}s"
    except Exception as e:
        return False, "", str(e)


def main():
    """Main batch runner."""
    
    # Parse arguments
    topics_only = '--topics-only' in sys.argv
    papers_only = '--papers-only' in sys.argv
    start_from = None
    
    if '--start-from' in sys.argv:
        idx = sys.argv.index('--start-from')
        if idx + 1 < len(sys.argv):
            start_from = sys.argv[idx + 1].upper()
    
    # Load subjects
    with open(SUBJECTS_FILE, 'r', encoding='utf-8') as f:
        subjects = json.load(f)
    
    # Filter if start_from specified
    if start_from:
        subjects = [s for s in subjects if s['code'] >= start_from]
    
    log("=" * 100)
    log("EDEXCEL A-LEVEL - BATCH RUNNER")
    log("=" * 100)
    log(f"\nStarting: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Subjects to process: {len(subjects)}")
    log(f"Mode: {'Topics only' if topics_only else 'Papers only' if papers_only else 'Both'}")
    if start_from:
        log(f"Starting from: {start_from}")
    log(f"\nLog file: {LOG_FILE.name}\n")
    log("=" * 100)
    
    # Track results
    results = {
        'topics': {'success': [], 'failed': []},
        'papers': {'success': [], 'failed': []}
    }
    
    start_time = time.time()
    
    # Process each subject
    for i, subject in enumerate(subjects, 1):
        code = subject['code']
        name = subject['name']
        
        log(f"\n[{i}/{len(subjects)}] {code} - {name}")
        log("-" * 80)
        
        # Topics
        if not papers_only:
            log(f"\n  TOPICS: Scraping...")
            success, stdout, stderr = run_scraper(
                TOPICS_SCRAPER,
                [code, name, subject['pdf_url']],
                timeout=600
            )
            
            if success:
                # Extract topic count from output
                topic_count = "?"
                for line in stdout.split('\n'):
                    if 'Parsed' in line and 'unique topics' in line:
                        parts = line.split()
                        if len(parts) > 1:
                            topic_count = parts[1]
                            break
                
                log(f"  [OK] Topics: SUCCESS ({topic_count} topics)")
                results['topics']['success'].append((code, name, topic_count))
            else:
                log(f"  [FAIL] Topics: FAILED")
                if stderr:
                    log(f"     Error: {stderr[:200]}")
                results['topics']['failed'].append((code, name))
        
        # Small delay between topics and papers
        time.sleep(2)
        
        # Papers
        if not topics_only:
            log(f"\n  PAPERS: Scraping...")
            success, stdout, stderr = run_scraper(
                PAPERS_SCRAPER,
                [code, name, subject['exam_materials_url']],
                timeout=600
            )
            
            if success:
                # Extract paper count
                paper_count = "?"
                for line in stdout.split('\n'):
                    if 'paper sets' in line.lower():
                        parts = line.split()
                        for j, part in enumerate(parts):
                            if 'paper' in part.lower() and j > 0:
                                try:
                                    paper_count = parts[j-1]
                                    break
                                except:
                                    pass
                
                log(f"  [OK] Papers: SUCCESS ({paper_count} sets)")
                results['papers']['success'].append((code, name, paper_count))
            else:
                log(f"  [FAIL] Papers: FAILED")
                if stderr:
                    log(f"     Error: {stderr[:200]}")
                results['papers']['failed'].append((code, name))
        
        log("-" * 80)
        
        # Delay between subjects to avoid rate limiting
        if i < len(subjects):
            time.sleep(3)
    
    # Summary
    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    
    log("\n" + "=" * 100)
    log("BATCH RUN COMPLETE!")
    log("=" * 100)
    log(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Duration: {hours}h {minutes}m {seconds}s")
    log(f"\nResults:")
    log("-" * 100)
    
    if not papers_only:
        log(f"\nTOPICS:")
        log(f"  [OK] Success: {len(results['topics']['success'])} subjects")
        if results['topics']['success']:
            total_topics = 0
            for code, name, count in results['topics']['success']:
                try:
                    total_topics += int(count)
                except:
                    pass
                log(f"     - {code} - {name}: {count} topics")
            log(f"\n  [TOTAL] Topics scraped: {total_topics}")
        
        log(f"\n  [FAIL] Failed: {len(results['topics']['failed'])} subjects")
        if results['topics']['failed']:
            for code, name in results['topics']['failed']:
                log(f"     - {code} - {name}")
    
    if not topics_only:
        log(f"\nPAPERS:")
        log(f"  [OK] Success: {len(results['papers']['success'])} subjects")
        if results['papers']['success']:
            total_papers = 0
            for code, name, count in results['papers']['success']:
                try:
                    total_papers += int(count)
                except:
                    pass
                log(f"     - {code} - {name}: {count} sets")
            log(f"\n  [TOTAL] Paper sets scraped: {total_papers}")
        
        log(f"\n  [FAIL] Failed: {len(results['papers']['failed'])} subjects")
        if results['papers']['failed']:
            for code, name in results['papers']['failed']:
                log(f"     - {code} - {name}")
    
    log("\n" + "=" * 100)
    log(f"\nFull log saved to: {LOG_FILE.name}")
    log("=" * 100)
    
    # Return failure count as exit code
    total_failures = len(results['topics']['failed']) + len(results['papers']['failed'])
    return total_failures


if __name__ == '__main__':
    try:
        failures = main()
        sys.exit(min(failures, 255))  # Exit code max is 255
    except KeyboardInterrupt:
        print("\n\n[WARN] Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

