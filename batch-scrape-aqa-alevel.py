"""
BATCH SCRAPER: All AQA A-Level Subjects

Runs the complete scraping workflow for all 42 AQA A-Level subjects:
1. Topics (Firecrawl via Node.js)
2. Past Papers (Selenium via Python)

Can be resumed if interrupted.
Tracks progress automatically.
"""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
import sys

# Progress file
PROGRESS_FILE = Path('batch-progress.json')


def load_subjects():
    """Load the subject list."""
    with open('aqa-alevel-subjects.json', 'r') as f:
        return json.load(f)


def load_progress():
    """Load or create progress tracker."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'started_at': datetime.now().isoformat(),
        'last_updated': None,
        'completed_subjects': [],
        'failed_subjects': [],
        'current_subject': None,
        'stats': {
            'total_subjects': 0,
            'completed': 0,
            'failed': 0,
            'total_topics': 0,
            'total_papers': 0
        }
    }


def save_progress(progress):
    """Save progress to file."""
    progress['last_updated'] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def run_node_script(script_name, subject):
    """
    Run a Node.js script for a subject.
    Returns (success, topic_count)
    """
    try:
        # Create temporary config file for the subject
        config = {
            'name': subject['name'],
            'code': subject['code'],
            'slug': subject['slug']
        }
        
        with open('temp-subject-config.json', 'w') as f:
            json.dump(config, f)
        
        # Run Node script
        result = subprocess.run(
            ['node', script_name],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            # Parse output for topic count
            output = result.stdout
            if 'Total topics:' in output:
                # Extract number
                for line in output.split('\n'):
                    if 'Total topics:' in line:
                        try:
                            count = int(line.split(':')[1].strip())
                            return (True, count)
                        except:
                            pass
            return (True, 0)
        else:
            print(f"   ❌ Node script failed: {result.stderr[:200]}")
            return (False, 0)
            
    except subprocess.TimeoutExpired:
        print(f"   ❌ Timeout (>5 min)")
        return (False, 0)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return (False, 0)


def run_python_script(script_name, subject):
    """
    Run a Python script for a subject.
    Returns (success, paper_count)
    """
    try:
        # Create temporary config
        config = {
            'name': subject['name'],
            'code': subject['code'],
            'slug': subject['slug']
        }
        
        with open('temp-subject-config.json', 'w') as f:
            json.dump(config, f)
        
        # Run Python script
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout (Selenium can be slow)
        )
        
        if result.returncode == 0:
            # Parse output for paper count
            output = result.stdout
            if 'Paper sets uploaded:' in output:
                for line in output.split('\n'):
                    if 'Paper sets uploaded:' in line:
                        try:
                            count = int(line.split(':')[1].strip())
                            return (True, count)
                        except:
                            pass
            return (True, 0)
        else:
            print(f"   ❌ Python script failed: {result.stderr[:200]}")
            return (False, 0)
            
    except subprocess.TimeoutExpired:
        print(f"   ❌ Timeout (>10 min)")
        return (False, 0)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return (False, 0)


def scrape_subject(subject, progress):
    """
    Complete scraping workflow for one subject.
    Returns (success, topic_count, paper_count)
    """
    print(f"\n{'='*60}")
    print(f"SUBJECT: {subject['name']} ({subject['code']})")
    print(f"{'='*60}")
    
    progress['current_subject'] = subject['name']
    save_progress(progress)
    
    # Step 1: Topics (Firecrawl)
    print(f"\n📚 Step 1: Scraping topics (Firecrawl)...")
    # For now, we'll use a generic script that reads temp-subject-config.json
    # We'll create this next
    
    # Placeholder - will create generic topic scraper
    topics_success = True
    topic_count = 0  # Will be populated by actual scraper
    
    # Step 2: Papers (Selenium)
    print(f"\n📄 Step 2: Scraping past papers (Selenium)...")
    # Same - will use generic scraper
    
    papers_success = True
    paper_count = 0
    
    # For now, return success
    return (topics_success and papers_success, topic_count, paper_count)


def main():
    print("🚀 AQA A-LEVEL BATCH SCRAPER")
    print("="*60)
    print("Scraping ALL 42 A-Level subjects")
    print("This will take 3-4 hours")
    print("="*60)
    
    # Load subjects and progress
    subjects = load_subjects()
    progress = load_progress()
    
    progress['stats']['total_subjects'] = len(subjects)
    
    print(f"\nTotal subjects: {len(subjects)}")
    print(f"Already completed: {len(progress['completed_subjects'])}")
    print(f"To process: {len(subjects) - len(progress['completed_subjects'])}")
    
    if progress['completed_subjects']:
        print(f"\nResuming from: {progress['completed_subjects'][-1]}")
    
    input("\nPress ENTER to start (or Ctrl+C to cancel)...")
    
    # Process each subject
    start_time = time.time()
    
    for i, subject in enumerate(subjects, 1):
        subject_name = subject['name']
        
        # Skip if already completed
        if subject_name in progress['completed_subjects']:
            print(f"\n[{i}/{len(subjects)}] ⏭️  Skipping {subject_name} (already done)")
            continue
        
        print(f"\n[{i}/{len(subjects)}] Processing {subject_name}...")
        
        # Scrape this subject
        success, topic_count, paper_count = scrape_subject(subject, progress)
        
        # Update progress
        if success:
            progress['completed_subjects'].append(subject_name)
            progress['stats']['completed'] += 1
            progress['stats']['total_topics'] += topic_count
            progress['stats']['total_papers'] += paper_count
            print(f"   ✅ Complete! Topics: {topic_count}, Papers: {paper_count}")
        else:
            progress['failed_subjects'].append({
                'name': subject_name,
                'code': subject['code'],
                'timestamp': datetime.now().isoformat()
            })
            progress['stats']['failed'] += 1
            print(f"   ❌ Failed - logged and continuing")
        
        save_progress(progress)
        
        # Show progress
        elapsed = (time.time() - start_time) / 60
        avg_per_subject = elapsed / (i - len([s for s in subjects[:i] if s['name'] in progress['completed_subjects'] and subjects.index(s) < i]))
        remaining = (len(subjects) - i) * avg_per_subject
        
        print(f"\n📊 Progress: {progress['stats']['completed']}/{len(subjects)} complete")
        print(f"   Time elapsed: {elapsed:.1f} min")
        print(f"   Est. remaining: {remaining:.1f} min")
    
    # Final report
    print("\n" + "="*60)
    print("🎉 BATCH SCRAPING COMPLETE!")
    print("="*60)
    print(f"\nResults:")
    print(f"   Completed: {progress['stats']['completed']}/{len(subjects)}")
    print(f"   Failed: {progress['stats']['failed']}")
    print(f"   Total topics: {progress['stats']['total_topics']}")
    print(f"   Total paper sets: {progress['stats']['total_papers']}")
    print(f"   Time taken: {(time.time() - start_time) / 60:.1f} minutes")
    
    if progress['failed_subjects']:
        print(f"\n⚠️  Failed subjects:")
        for failed in progress['failed_subjects']:
            print(f"   - {failed['name']} ({failed['code']})")
    
    print(f"\n✅ Check Supabase staging_aqa_* tables for data!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("Progress saved - you can resume by running this script again")
        sys.exit(0)

