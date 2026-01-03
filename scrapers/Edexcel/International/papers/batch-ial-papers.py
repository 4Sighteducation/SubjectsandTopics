"""
BATCH INTERNATIONAL A LEVEL PAPER SCRAPER
=========================================

Runs the universal scraper for all International A Level subjects with progress tracking.

Usage:
    python batch-ial-papers.py
    python batch-ial-papers.py --resume  # Resume from checkpoint
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

# All International A Level subjects to scrape
IAL_SUBJECTS = [
    'IAL-Accounting',
    'IAL-Arabic',
    'IAL-Biology',
    'IAL-Business',
    'IAL-Chemistry',
    'IAL-Economics',
    'IAL-EnglishLanguage',
    'IAL-EnglishLiterature',
    'IAL-French',
    'IAL-Geography',
    'IAL-German',
    'IAL-Greek',
    'IAL-History',
    'IAL-IT',
    'IAL-Law',
    'IAL-Mathematics',
    'IAL-FurtherMaths',
    'IAL-Physics',
    'IAL-Psychology',
    'IAL-Spanish'
]


class BatchPaperScraper:
    """Batch scraper with progress tracking."""
    
    def __init__(self, resume=False):
        self.script_dir = Path(__file__).parent
        self.output_dir = self.script_dir / "batch-results"
        self.output_dir.mkdir(exist_ok=True)
        
        self.timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        self.log_file = self.output_dir / f"batch-ial-papers-{self.timestamp}.log"
        self.checkpoint_file = self.output_dir / "checkpoint-ial-papers.json"
        self.summary_file = self.output_dir / f"summary-ial-papers-{self.timestamp}.json"
        
        self.checkpoint = self._load_checkpoint() if resume else {'completed': [], 'failed': []}
        self.results = []
        self.start_time = time.time()
    
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
        self._log("BATCH INTERNATIONAL A LEVEL EXAM PAPER SCRAPER")
        self._log("="*80)
        self._log(f"Total subjects: {len(IAL_SUBJECTS)}")
        self._log(f"Already completed: {len(self.checkpoint['completed'])}")
        self._log(f"To process: {len([s for s in IAL_SUBJECTS if s not in self.checkpoint['completed']])}")
        self._log("="*80)
        
        scraper_script = self.script_dir / "universal-ial-paper-scraper.py"
        
        for idx, subject_code in enumerate(IAL_SUBJECTS, 1):
            # Skip if already done
            if subject_code in self.checkpoint['completed']:
                self._log(f"[{idx}/{len(IAL_SUBJECTS)}] ✓ SKIP: {subject_code} - already completed")
                continue
            
            self._log(f"\n[{idx}/{len(IAL_SUBJECTS)}] PROCESSING: {subject_code}")
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
                    timeout=300  # 5 minute timeout per subject
                )
                
                subject_time = time.time() - subject_start
                
                if result.returncode == 0:
                    # Success
                    self.checkpoint['completed'].append(subject_code)
                    self._save_checkpoint()
                    
                    # Extract paper count from output
                    paper_count = self._extract_paper_count(result.stdout)
                    
                    self._log(f"✅ SUCCESS: {subject_code} - {paper_count} paper sets ({subject_time:.1f}s)")
                    
                    self.results.append({
                        'subject': subject_code,
                        'status': 'success',
                        'paper_sets': paper_count,
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
                        'status': 'failed',
                        'error': error_msg,
                        'time_seconds': subject_time
                    })
                
                # Small delay between subjects
                time.sleep(3)
                
            except subprocess.TimeoutExpired:
                self._log(f"⏱️ TIMEOUT: {subject_code} - exceeded 5 minutes")
                self.checkpoint['failed'].append(subject_code)
                self._save_checkpoint()
                
                self.results.append({
                    'subject': subject_code,
                    'status': 'timeout',
                    'time_seconds': 300
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
                    'status': 'error',
                    'error': str(e),
                    'time_seconds': 0
                })
        
        # Final summary
        self._save_summary()
        self._print_summary()
    
    def _extract_paper_count(self, output):
        """Extract paper set count from scraper output."""
        import re
        match = re.search(r'Grouped into (\d+) paper sets', output)
        if match:
            return int(match.group(1))
        match = re.search(r'Uploaded (\d+) paper sets', output)
        if match:
            return int(match.group(1))
        return 0
    
    def _save_summary(self):
        """Save detailed summary."""
        elapsed = time.time() - self.start_time
        
        success = [r for r in self.results if r['status'] == 'success']
        failed = [r for r in self.results if r['status'] != 'success']
        
        summary = {
            'batch_name': 'International A Level Exam Papers Batch',
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': datetime.now().isoformat(),
            'elapsed_seconds': elapsed,
            'elapsed_formatted': f"{elapsed/60:.1f} minutes",
            'summary': {
                'total': len(self.results),
                'success': len(success),
                'failed': len(failed),
                'total_paper_sets': sum(r.get('paper_sets', 0) for r in success)
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
            total_papers = sum(r.get('paper_sets', 0) for r in success)
            self._log(f"📄 Total paper sets scraped: {total_papers}")
        
        if failed:
            self._log(f"\nFailed subjects:")
            for r in failed:
                self._log(f"  - {r['subject']}: {r['status']}")
        
        self._log("="*80)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Batch International A Level paper scraper')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    args = parser.parse_args()
    
    print("\n" + "📄 "*20)
    print("BATCH INTERNATIONAL A LEVEL EXAM PAPER SCRAPER")
    print("📄 "*20)
    print(f"\nThis will scrape exam papers for all {len(IAL_SUBJECTS)} International A Level subjects")
    print("Estimated time: 30-60 minutes")
    print("\nPress Ctrl+C at any time to pause (progress will be saved)")
    
    if not args.resume:
        response = input("\nStart batch scraping? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled.")
            sys.exit(0)
    
    runner = BatchPaperScraper(resume=args.resume)
    runner.run_batch()


if __name__ == '__main__':
    main()

