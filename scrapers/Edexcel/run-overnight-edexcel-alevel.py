"""
Edexcel A-Level Overnight Master Scraper
Runs all subjects automatically - topics and papers

Usage:
  python run-overnight-edexcel-alevel.py              # Run all 'ready' subjects
  python run-overnight-edexcel-alevel.py --all        # Run ALL including completed
  python run-overnight-edexcel-alevel.py --test 3     # Test with first 3 subjects only
"""

import json
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Load subjects
config_path = Path(__file__).parent / 'edexcel-alevel-subjects-complete.json'
with open(config_path) as f:
    ALL_SUBJECTS = json.load(f)

# Paths
TOPICS_DIR = Path(__file__).parent / 'A-Level' / 'topics'
PAPERS_DIR = Path(__file__).parent / 'A-Level' / 'papers'

# Results tracking
results = {
    'started': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'subjects': [],
    'summary': defaultdict(int)
}

def log(msg):
    """Print and log."""
    print(msg)
    timestamp = datetime.now().strftime('%H:%M:%S')
    with open('overnight-run.log', 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {msg}\n")

def scrape_topics(subject):
    """Scrape topics for a subject using Python PDF scraper."""
    
    if subject['code'] == '9HI0':
        # History uses custom JS scraper
        log(f"   >> Topics: Running custom History scraper...")
        
        scraper = TOPICS_DIR / 'scrape-edexcel-history.js'
        result = subprocess.run(
            ['node', str(scraper)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=600,
            cwd=str(TOPICS_DIR)
        )
        
        if result.returncode == 0 and 'COMPLETE' in result.stdout:
            count_match = result.stdout.split('Total topics:')[-1].split('\n')[0].strip() if 'Total topics:' in result.stdout else '?'
            log(f"   OK Topics: {count_match} topics")
            return {'success': True, 'count': count_match}
        else:
            error = result.stderr[-200:] if result.stderr else 'Unknown error'
            log(f"   FAIL Topics failed: {error}")
            return {'success': False, 'error': error}
    
    else:
        # Use Python PDF scraper (based on Biology template)
        log(f"   >> Topics: Running Python PDF scraper...")
        
        # Create temp scraper with this subject's config
        template = TOPICS_DIR / 'scrape-biology-a-python.py'
        template_content = template.read_text(encoding='utf-8')
        
        # Replace SUBJECT config
        modified = template_content.replace(
            "SUBJECT = {\n    'name': 'Biology A (Salters-Nuffield)',\n    'code': '9BN0',",
            f"SUBJECT = {{\n    'name': '{subject['name']}',\n    'code': '{subject['code']}',"
        )
        modified = modified.replace(
            subject['pdf_url'] if '9BN0' in template_content else 'REPLACE_ME',
            subject['pdf_url']
        )
        
        temp_file = TOPICS_DIR / f"temp-{subject['code']}.py"
        temp_file.write_text(modified, encoding='utf-8')
        
        try:
            result = subprocess.run(
                ['python', str(temp_file)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace problematic chars instead of crashing
                timeout=300,
                cwd=str(TOPICS_DIR)
            )
            
            if result.returncode == 0 and 'COMPLETE' in result.stdout:
                # Extract topic count
                lines = result.stdout.split('\n')
                count = '?'
                for line in lines:
                    if 'Parsed' in line and 'unique topics' in line:
                        count = line.split()[1]
                        break
                
                log(f"   OK Topics: {count} topics")
                return {'success': True, 'count': count}
            else:
                error = result.stderr[-200:] if result.stderr else result.stdout[-200:]
                log(f"   FAIL Topics failed: {error[:100]}")
                return {'success': False, 'error': error[:200]}
                
        except subprocess.TimeoutExpired:
            log(f"   FAIL Topics timeout (>5 mins)")
            return {'success': False, 'error': 'Timeout'}
        except Exception as e:
            log(f"   FAIL Topics error: {str(e)[:100]}")
            return {'success': False, 'error': str(e)[:200]}
        finally:
            if temp_file.exists():
                temp_file.unlink()

def scrape_papers(subject):
    """Scrape papers using Selenium (same for all subjects)."""
    
    log(f"   >> Papers: Running Selenium scraper...")
    
    # Use Biology papers scraper as template
    template = PAPERS_DIR / 'scrape-biology-a-papers.py'
    template_content = template.read_text(encoding='utf-8')
    
    # Replace SUBJECT config
    modified = template_content.replace(
        "'name': 'Biology A (Salters-Nuffield)',",
        f"'name': '{subject['name']}',"
    )
    modified = modified.replace(
        "'code': '9BN0',",
        f"'code': '{subject['code']}',"
    )
    modified = modified.replace(
        subject['exam_materials_url'] if '9BN0' in template_content else 'REPLACE_ME',
        subject['exam_materials_url']
    )
    
    temp_file = PAPERS_DIR / f"temp-{subject['code']}.py"
    temp_file.write_text(modified, encoding='utf-8')
    
    try:
        result = subprocess.run(
            ['python', str(temp_file)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=600,
            cwd=str(PAPERS_DIR)
        )
        
        if result.returncode == 0 and 'COMPLETE' in result.stdout:
            # Extract paper count
            lines = result.stdout.split('\n')
            count = '?'
            for line in lines:
                if 'paper sets' in line.lower() and 'complete' not in line.lower():
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'paper' in part.lower() and i > 0:
                            count = parts[i-1]
                            break
            
            log(f"   OK Papers: {count} paper sets")
            return {'success': True, 'count': count}
        else:
            error = result.stderr[-200:] if result.stderr else result.stdout[-200:]
            log(f"   FAIL Papers failed: {error[:100]}")
            return {'success': False, 'error': error[:200]}
            
    except subprocess.TimeoutExpired:
        log(f"   FAIL Papers timeout (>10 mins)")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        log(f"   FAIL Papers error: {str(e)[:100]}")
        return {'success': False, 'error': str(e)[:200]}
    finally:
        if temp_file.exists():
            temp_file.unlink()

def main():
    """Main overnight runner."""
    
    # Parse args
    run_all = '--all' in sys.argv
    test_mode = '--test' in sys.argv
    test_count = 3
    
    if test_mode:
        for arg in sys.argv:
            if arg.isdigit():
                test_count = int(arg)
    
    # Filter subjects
    subjects = ALL_SUBJECTS if run_all else [s for s in ALL_SUBJECTS if s['status'] != 'complete']
    
    if test_mode:
        subjects = subjects[:test_count]
    
    print("=" * 60)
    print("EDEXCEL A-LEVEL OVERNIGHT SCRAPER")
    print("=" * 60)
    print(f"Started: {results['started']}")
    print(f"Total subjects: {len(ALL_SUBJECTS)}")
    print(f"Running: {len(subjects)} subjects")
    print(f"Mode: {'TEST (first {})'.format(test_count) if test_mode else 'FULL RUN'}")
    print("=" * 60)
    print("")
    
    # Clear log
    Path('overnight-run.log').write_text(f"Started: {results['started']}\n", encoding='utf-8')
    
    # Run each subject
    for idx, subject in enumerate(subjects):
        log(f"\n{'='*60}")
        log(f"[{idx + 1}/{len(subjects)}] {subject['name']} ({subject['code']})")
        log(f"{'='*60}")
        
        subject_result = {
            'name': subject['name'],
            'code': subject['code'],
            'topics': None,
            'papers': None
        }
        
        # Topics
        try:
            topic_result = scrape_topics(subject)
            subject_result['topics'] = topic_result
            
            if topic_result['success']:
                results['summary']['topics_success'] += 1
            else:
                results['summary']['topics_failed'] += 1
                
        except Exception as e:
            log(f"   FAIL Topics crashed: {e}")
            subject_result['topics'] = {'success': False, 'error': str(e)}
            results['summary']['topics_failed'] += 1
        
        # Papers
        try:
            paper_result = scrape_papers(subject)
            subject_result['papers'] = paper_result
            
            if paper_result['success']:
                results['summary']['papers_success'] += 1
            else:
                results['summary']['papers_failed'] += 1
                
        except Exception as e:
            log(f"   FAIL Papers crashed: {e}")
            subject_result['papers'] = {'success': False, 'error': str(e)}
            results['summary']['papers_failed'] += 1
        
        results['subjects'].append(subject_result)
    
    # Final summary
    results['completed'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("\n" + "=" * 60)
    print("OVERNIGHT RUN COMPLETE!")
    print("=" * 60)
    print(f"\nCompleted: {results['completed']}")
    print(f"\nSummary:")
    print(f"  Subjects processed: {len(subjects)}")
    print(f"  Topics: {results['summary']['topics_success']} OK, {results['summary']['topics_failed']} FAIL")
    print(f"  Papers: {results['summary']['papers_success']} OK, {results['summary']['papers_failed']} FAIL")
    
    # Save detailed report
    report_path = Path(__file__).parent / f"overnight-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nREPORT: Full report: {report_path.name}")
    
    # Show failures
    failures = []
    for s in results['subjects']:
        issues = []
        if s['topics'] and not s['topics']['success']:
            issues.append('topics')
        if s['papers'] and not s['papers']['success']:
            issues.append('papers')
        if issues:
            failures.append(f"{s['name']} ({', '.join(issues)})")
    
    if failures:
        print(f"\nWARNING:  {len(failures)} subjects need attention:")
        for f in failures:
            print(f"  - {f}")
    else:
        print(f"\nSUCCESS! ALL SUBJECTS SUCCESSFUL!")

if __name__ == '__main__':
    main()

