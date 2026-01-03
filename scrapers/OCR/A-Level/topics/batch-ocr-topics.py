"""
BATCH OCR A-LEVEL TOPIC SCRAPER
================================

Runs the AI-powered topic scraper for all OCR A-Level subjects with progress tracking.

Usage:
    python batch-ocr-topics.py
    python batch-ocr-topics.py --resume  # Resume from checkpoint
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Get all subjects from JSON file
SUBJECTS_FILE = Path(__file__).parent.parent / "ocr-alevel-subjects.json"


class BatchTopicScraper:
    """Batch scraper with progress tracking."""
    
    def __init__(self, resume=False):
        self.script_dir = Path(__file__).parent
        self.output_dir = self.script_dir.parent / "batch-results"
        self.output_dir.mkdir(exist_ok=True)
        
        self.timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        self.log_file = self.output_dir / f"batch-topics-{self.timestamp}.log"
        self.checkpoint_file = self.output_dir / "checkpoint-topics.json"
        self.summary_file = self.output_dir / f"summary-topics-{self.timestamp}.json"
        
        self.checkpoint = self._load_checkpoint() if resume else {'completed': [], 'failed': []}
        self.results = []
        self.start_time = time.time()
        
        # Load subjects
        self.subjects = self._load_subjects()
        self.subject_codes = list(self.subjects.keys())
    
    def _load_subjects(self):
        """Load subjects from JSON file."""
        if not SUBJECTS_FILE.exists():
            print(f"[ERROR] Subjects file not found: {SUBJECTS_FILE}")
            sys.exit(1)
        
        with open(SUBJECTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_checkpoint(self):
        """Load checkpoint if exists."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)
                    print(f"[INFO] Resuming: {len(checkpoint['completed'])} completed, {len(checkpoint['failed'])} failed")
                    return checkpoint
            except:
                pass
        return {'completed': [], 'failed': []}
    
    def _save_checkpoint(self):
        """Save checkpoint."""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.checkpoint, f, indent=2)
    
    def _log(self, message):
        """Write to log and console."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    
    def run_batch(self):
        """Run all subjects."""
        self._log("="*80)
        self._log("BATCH OCR A-LEVEL TOPIC SCRAPER")
        self._log("="*80)
        self._log(f"Total subjects: {len(self.subject_codes)}")
        self._log(f"Already completed: {len(self.checkpoint['completed'])}")
        self._log(f"To process: {len([s for s in self.subject_codes if s not in self.checkpoint['completed']])}")
        self._log("="*80)
        
        scraper_script = self.script_dir / "ocr-alevel-smart-scraper.py"
        
        for idx, subject_code in enumerate(self.subject_codes, 1):
            # Skip if already done
            if subject_code in self.checkpoint['completed']:
                self._log(f"[{idx}/{len(self.subject_codes)}] ✓ SKIP: {subject_code} - already completed")
                continue
            
            subject_name = self.subjects[subject_code]['name']
            self._log(f"\n[{idx}/{len(self.subject_codes)}] PROCESSING: {subject_code} - {subject_name}")
            self._log("-"*80)
            
            subject_start = time.time()
            
            try:
                # Run scraper
                result = subprocess.run(
                    [sys.executable, str(scraper_script), subject_code],
                    cwd=self.script_dir,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=600  # 10 minute timeout per subject
                )
                
                subject_time = time.time() - subject_start
                
                if result.returncode == 0:
                    # Success
                    self.checkpoint['completed'].append(subject_code)
                    self._save_checkpoint()
                    
                    # Extract topic count from output
                    topic_count = self._extract_topic_count(result.stdout)
                    
                    self._log(f"✅ SUCCESS: {subject_code} - {topic_count} topics ({subject_time:.1f}s)")
                    
                    self.results.append({
                        'subject': subject_code,
                        'name': subject_name,
                        'status': 'success',
                        'topics': topic_count,
                        'time_seconds': subject_time
                    })
                else:
                    # Failed
                    self.checkpoint['failed'].append(subject_code)
                    self._save_checkpoint()
                    
                    error_msg = result.stderr[-500:] if result.stderr else "Unknown error"
                    self._log(f"❌ FAILED: {subject_code}")
                    self._log(f"Error: {error_msg}")
                    
                    self.results.append({
                        'subject': subject_code,
                        'name': subject_name,
                        'status': 'failed',
                        'error': error_msg,
                        'time_seconds': subject_time
                    })
                
                # Small delay between subjects
                time.sleep(5)
                
            except subprocess.TimeoutExpired:
                self._log(f"⏱️ TIMEOUT: {subject_code} - exceeded 10 minutes")
                self.checkpoint['failed'].append(subject_code)
                self._save_checkpoint()
                
                self.results.append({
                    'subject': subject_code,
                    'name': subject_name,
                    'status': 'timeout',
                    'time_seconds': 600
                })
                
            except KeyboardInterrupt:
                self._log(f"\n⚠️ INTERRUPTED by user at {subject_code}")
                self._save_checkpoint()
                self._save_summary()
                print("\n[INFO] Progress saved. Run with --resume to continue.")
                sys.exit(0)
            
            except Exception as e:
                self._log(f"💥 ERROR: {subject_code} - {str(e)}")
                self.checkpoint['failed'].append(subject_code)
                self._save_checkpoint()
                
                self.results.append({
                    'subject': subject_code,
                    'name': subject_name,
                    'status': 'error',
                    'error': str(e),
                    'time_seconds': 0
                })
        
        # Final summary
        self._save_summary()
        self._print_summary()
    
    def _extract_topic_count(self, output):
        """Extract topic count from scraper output."""
        import re
        match = re.search(r'Parsed (\d+) topics', output)
        if match:
            return int(match.group(1))
        match = re.search(r'Uploaded (\d+) topics', output)
        if match:
            return int(match.group(1))
        return 0
    
    def _save_summary(self):
        """Save detailed summary."""
        elapsed = time.time() - self.start_time
        
        success = [r for r in self.results if r['status'] == 'success']
        failed = [r for r in self.results if r['status'] != 'success']
        
        summary = {
            'batch_name': 'OCR A-Level Topics Batch',
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': datetime.now().isoformat(),
            'elapsed_seconds': elapsed,
            'elapsed_formatted': f"{elapsed/60:.1f} minutes",
            'summary': {
                'total': len(self.results),
                'success': len(success),
                'failed': len(failed),
                'total_topics': sum(r.get('topics', 0) for r in success)
            },
            'results': self.results,
            'checkpoint': self.checkpoint
        }
        
        with open(self.summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self._log(f"\n[INFO] Summary saved to: {self.summary_file.name}")
    
    def _print_summary(self):
        """Print final summary."""
        elapsed = time.time() - self.start_time
        success = [r for r in self.results if r['status'] == 'success']
        failed = [r for r in self.results if r['status'] != 'success']
        
        self._log("\n" + "="*80)
        self._log("BATCH COMPLETE")
        self._log("="*80)
        self._log(f"Time elapsed: {elapsed/60:.1f} minutes")
        self._log(f"Total subjects: {len(self.results)}")
        self._log(f"✅ Success: {len(success)}")
        self._log(f"❌ Failed: {len(failed)}")
        
        if success:
            total_topics = sum(r.get('topics', 0) for r in success)
            self._log(f"📚 Total topics scraped: {total_topics}")
        
        if failed:
            self._log(f"\nFailed subjects:")
            for r in failed:
                self._log(f"  - {r['subject']}: {r['status']}")
        
        self._log("="*80)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Batch OCR A-Level topic scraper')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    args = parser.parse_args()
    
    print("\n" + "📚 "*20)
    print("BATCH OCR A-LEVEL TOPIC SCRAPER")
    print("📚 "*20)
    
    # Load subjects to get count
    if SUBJECTS_FILE.exists():
        with open(SUBJECTS_FILE, 'r', encoding='utf-8') as f:
            subjects = json.load(f)
            subject_count = len(subjects)
    else:
        subject_count = "unknown"
    
    print(f"\nThis will scrape topics for {subject_count} OCR A-Level subjects")
    print("Estimated time: 1-2 hours (depends on AI API speed)")
    print("\nPress Ctrl+C at any time to pause (progress will be saved)")
    
    if not args.resume:
        response = input("\nStart batch scraping? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled.")
            sys.exit(0)
    
    runner = BatchTopicScraper(resume=args.resume)
    runner.run_batch()


if __name__ == '__main__':
    main()

