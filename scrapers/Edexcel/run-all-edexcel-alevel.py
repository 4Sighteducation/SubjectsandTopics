"""
Edexcel A-Level Master Scraper
Runs overnight to scrape all subjects (topics + papers)

Usage:
  python run-all-edexcel-alevel.py              # Run all untested subjects
  python run-all-edexcel-alevel.py --all        # Run ALL subjects (including tested)
  python run-all-edexcel-alevel.py --topics     # Topics only
  python run-all-edexcel-alevel.py --papers     # Papers only
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Load subjects config
config_path = Path(__file__).parent / 'edexcel-alevel-subjects.json'
with open(config_path) as f:
    SUBJECTS = json.load(f)

# Results tracking
results = {
    'started': datetime.now().isoformat(),
    'subjects': [],
    'summary': {
        'total': 0,
        'topics_success': 0,
        'topics_failed': 0,
        'papers_success': 0,
        'papers_failed': 0
    }
}

def log(msg):
    """Log to console and results."""
    print(msg)

def scrape_topics(subject):
    """Scrape topics for a subject."""
    log(f"\n📚 Scraping topics for {subject['name']}...")
    
    # For now, only simple subjects use Python scraper
    # History uses its own custom JS scraper
    if subject['code'] == '9HI0':
        log("   ⏩ History uses custom scraper - skip for now")
        return {'success': True, 'note': 'Custom scraper - run manually'}
    
    # Create Python scraper on-the-fly for this subject
    # (Reuses Biology template with different config)
    scraper_content = f"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import and run Biology scraper with different config
import importlib.util
spec = importlib.util.spec_from_file_location(
    "biology_scraper",
    Path(__file__).parent / "scrape-biology-a-python.py"
)
bio_module = importlib.util.module_from_spec(spec)

# Override SUBJECT config
bio_module.SUBJECT = {{
    'name': '{subject['name']}',
    'code': '{subject['code']}',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': '{subject['pdf_url']}'
}}

# Run
spec.loader.exec_module(bio_module)
"""
    
    # Write temp scraper
    temp_scraper = Path(__file__).parent / 'A-Level' / 'topics' / f'temp-{subject["code"]}.py'
    temp_scraper.write_text(scraper_content)
    
    try:
        # Run scraper
        result = subprocess.run(
            ['python', str(temp_scraper)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Check if successful
        if result.returncode == 0 and 'COMPLETE!' in result.stdout:
            log(f"   ✅ Topics scraped successfully")
            return {'success': True, 'output': result.stdout[-500:]}
        else:
            log(f"   ❌ Topics failed")
            return {'success': False, 'error': result.stderr[-500:]}
            
    except subprocess.TimeoutExpired:
        log(f"   ❌ Timeout (>5 minutes)")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        log(f"   ❌ Error: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        # Cleanup temp file
        if temp_scraper.exists():
            temp_scraper.unlink()


def scrape_papers(subject):
    """Scrape papers for a subject."""
    log(f"\n📄 Scraping papers for {subject['name']}...")
    
    # All subjects use same Selenium approach
    # Just need to update the config in the scraper
    
    log("   ⏩ Papers scraper needs per-subject implementation")
    return {'success': False, 'note': 'Not yet implemented for batch'}


def main():
    """Main overnight scraper."""
    
    print("=" * 60)
    print("EDEXCEL A-LEVEL MASTER SCRAPER")
    print("=" * 60)
    print(f"Started: {results['started']}")
    print(f"Subjects to process: {len(SUBJECTS)}")
    print("")
    
    # Parse args
    run_all = '--all' in sys.argv
    topics_only = '--topics' in sys.argv
    papers_only = '--papers' in sys.argv
    
    # Filter subjects
    subjects_to_run = SUBJECTS if run_all else [s for s in SUBJECTS if s['status'] == 'untested']
    
    log(f"Running: {len(subjects_to_run)} subjects")
    log(f"Mode: {'Topics + Papers' if not (topics_only or papers_only) else 'Topics only' if topics_only else 'Papers only'}")
    log("")
    
    # Process each subject
    for idx, subject in enumerate(subjects_to_run):
        subject_result = {
            'name': subject['name'],
            'code': subject['code'],
            'topics': None,
            'papers': None
        }
        
        log(f"\n{'='*60}")
        log(f"[{idx + 1}/{len(subjects_to_run)}] {subject['name']} ({subject['code']})")
        log(f"{'='*60}")
        
        # Topics
        if not papers_only:
            topic_result = scrape_topics(subject)
            subject_result['topics'] = topic_result
            if topic_result['success']:
                results['summary']['topics_success'] += 1
            else:
                results['summary']['topics_failed'] += 1
        
        # Papers
        if not topics_only:
            paper_result = scrape_papers(subject)
            subject_result['papers'] = paper_result
            if paper_result['success']:
                results['summary']['papers_success'] += 1
            else:
                results['summary']['papers_failed'] += 1
        
        results['subjects'].append(subject_result)
        results['summary']['total'] += 1
    
    # Final summary
    results['completed'] = datetime.now().isoformat()
    
    print("\n" + "=" * 60)
    print("OVERNIGHT RUN COMPLETE!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  Total subjects: {results['summary']['total']}")
    print(f"  Topics: {results['summary']['topics_success']} success, {results['summary']['topics_failed']} failed")
    print(f"  Papers: {results['summary']['papers_success']} success, {results['summary']['papers_failed']} failed")
    
    # Save report
    report_path = Path(__file__).parent / f"scrape-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    report_path.write_text(json.dumps(results, indent=2))
    
    print(f"\n📊 Full report saved to: {report_path.name}")
    
    # Show failures
    failures = [s for s in results['subjects'] if 
                (s['topics'] and not s['topics']['success']) or 
                (s['papers'] and not s['papers']['success'])]
    
    if failures:
        print(f"\n⚠️  {len(failures)} subjects need manual attention:")
        for f in failures:
            print(f"  - {f['name']} ({f['code']})")
    else:
        print(f"\n🎉 ALL SUBJECTS SUCCESSFUL!")


if __name__ == '__main__':
    main()

