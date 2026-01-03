"""
Retry Failed International A Level Subjects
===========================================

This script retries ONLY the 11 subjects that failed in the first run.

Usage:
    python retry-failed-ial.py
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# Subjects that failed in the first run
FAILED_SUBJECTS = [
    'IAL-Economics',
    'IAL-EnglishLanguage', 
    'IAL-EnglishLiterature',
    'IAL-French',
    'IAL-Law',
    'IAL-Mathematics',
    'IAL-FurtherMaths',
    'IAL-PureMaths',
    'IAL-Physics',
    'IAL-Psychology',
    'IAL-Spanish'
]


class RetryRunner:
    """Retry failed subjects with better error handling."""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.output_dir = self.script_dir / "batch-results"
        self.output_dir.mkdir(exist_ok=True)
        
        self.timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        self.log_file = self.output_dir / f"retry-ial-{self.timestamp}.log"
        self.summary_file = self.output_dir / f"summary-retry-{self.timestamp}.json"
        
        # Load existing checkpoint
        self.checkpoint_file = self.output_dir / "checkpoint-ial.json"
        self.checkpoint = self._load_checkpoint()
        
        self.results = []
        self.start_time = time.time()
    
    def _load_checkpoint(self):
        """Load and reset failed subjects."""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
                # Remove failed subjects from checkpoint so they get retried
                checkpoint['failed'] = []
                return checkpoint
        return {'completed': [], 'failed': [], 'skipped': []}
    
    def _save_checkpoint(self):
        """Save checkpoint."""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.checkpoint, f, indent=2)
    
    def _log(self, message: str):
        """Write to log and console."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    
    def run_retry(self):
        """Retry all failed subjects."""
        # Load subjects
        subjects_file = self.script_dir / "International-A-Level" / "international-a-level-subjects.json"
        with open(subjects_file, 'r', encoding='utf-8') as f:
            all_subjects = json.load(f)
        
        # Filter to only failed subjects
        subjects = [s for s in all_subjects if s['code'] in FAILED_SUBJECTS]
        
        self._log("="*60)
        self._log("RETRY FAILED INTERNATIONAL A LEVEL SUBJECTS")
        self._log("="*60)
        self._log(f"Retrying: {len(subjects)} subjects")
        self._log(f"Already completed (won't retry): {len(self.checkpoint['completed'])}")
        self._log("="*60)
        
        scraper_script = self.script_dir / "ai-powered-scraper-openai.py"
        
        for idx, subject in enumerate(subjects, 1):
            code = subject['code']
            name = subject['name']
            
            # Skip if already completed successfully
            if code in self.checkpoint['completed']:
                self._log(f"[{idx}/{len(subjects)}] ✓ SKIP: {name} ({code}) - already completed")
                continue
            
            self._log(f"\n[{idx}/{len(subjects)}] PROCESSING: {name} ({code})")
            self._log("-"*60)
            
            subject_start = time.time()
            
            try:
                # Run scraper with increased timeout (10 minutes for complex subjects)
                result = subprocess.run(
                    [sys.executable, str(scraper_script), '--subject', code],
                    cwd=self.script_dir,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=600  # 10 minute timeout
                )
                
                subject_time = time.time() - subject_start
                
                if result.returncode == 0:
                    # Success
                    self.checkpoint['completed'].append(code)
                    self._save_checkpoint()
                    
                    # Parse output for topic count
                    topic_count = self._extract_topic_count(result.stdout)
                    
                    self._log(f"✅ SUCCESS: {name} - {topic_count} topics ({subject_time:.1f}s)")
                    
                    self.results.append({
                        'code': code,
                        'name': name,
                        'status': 'success',
                        'topics': topic_count,
                        'time_seconds': subject_time
                    })
                else:
                    # Failed - log full error
                    self.checkpoint['failed'].append(code)
                    self._save_checkpoint()
                    
                    # Log full stdout and stderr
                    self._log(f"❌ FAILED: {name}")
                    self._log(f"STDOUT: {result.stdout[-1000:]}")
                    self._log(f"STDERR: {result.stderr[-1000:]}")
                    
                    self.results.append({
                        'code': code,
                        'name': name,
                        'status': 'failed',
                        'stdout': result.stdout[-500:],
                        'stderr': result.stderr[-500:],
                        'time_seconds': subject_time
                    })
                
                # Small delay between subjects
                time.sleep(3)
                
            except subprocess.TimeoutExpired:
                self._log(f"⏱️ TIMEOUT: {name} - exceeded 10 minutes")
                self.checkpoint['failed'].append(code)
                self._save_checkpoint()
                
                self.results.append({
                    'code': code,
                    'name': name,
                    'status': 'timeout',
                    'time_seconds': 600
                })
                
            except KeyboardInterrupt:
                self._log(f"\n⚠️ INTERRUPTED by user at {name}")
                self._save_checkpoint()
                self._save_summary()
                print("\n[INFO] Progress saved.")
                sys.exit(0)
            
            except Exception as e:
                self._log(f"💥 ERROR: {name} - {str(e)}")
                self.checkpoint['failed'].append(code)
                self._save_checkpoint()
                
                self.results.append({
                    'code': code,
                    'name': name,
                    'status': 'error',
                    'error': str(e),
                    'time_seconds': 0
                })
        
        # Final summary
        self._save_summary()
        self._print_summary()
    
    def _extract_topic_count(self, output: str) -> int:
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
            'batch_name': 'IAL Retry Failed Subjects',
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
        
        self._log("\n" + "="*60)
        self._log("RETRY COMPLETE")
        self._log("="*60)
        self._log(f"Time elapsed: {elapsed/60:.1f} minutes")
        self._log(f"Total subjects: {len(self.results)}")
        self._log(f"✅ Success: {len(success)}")
        self._log(f"❌ Failed: {len(failed)}")
        
        if success:
            total_topics = sum(r.get('topics', 0) for r in success)
            self._log(f"📚 Total topics extracted: {total_topics}")
        
        if failed:
            self._log(f"\nStill failing:")
            for r in failed:
                self._log(f"  - {r['name']} ({r['code']}): {r['status']}")
        
        self._log("="*60)


def main():
    print("\n" + "🔄 "*20)
    print("RETRY FAILED INTERNATIONAL A LEVEL SUBJECTS")
    print("🔄 "*20)
    print(f"\nThis will retry the 11 subjects that failed:")
    for code in FAILED_SUBJECTS:
        print(f"  - {code}")
    print("\nIncreased timeout: 10 minutes per subject")
    print("Better error logging enabled")
    
    response = input("\nStart retry? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Cancelled.")
        sys.exit(0)
    
    runner = RetryRunner()
    runner.run_retry()


if __name__ == '__main__':
    main()

