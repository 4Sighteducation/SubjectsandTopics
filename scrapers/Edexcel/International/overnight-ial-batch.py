"""
Overnight International A Level Batch Scraper
=============================================

Runs all 21 International A Level subjects with:
- Same proven AI approach as IGCSE
- Adjusted for deeper, more complex hierarchies
- Progress tracking and checkpointing
- Automatic retries

Estimated time: 1.5-2.5 hours
Estimated cost: $5-8

Usage:
    python overnight-ial-batch.py
    
Resume:
    python overnight-ial-batch.py --resume
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class IALBatchRunner:
    """Manages International A Level batch execution."""
    
    def __init__(self, resume: bool = False):
        self.script_dir = Path(__file__).parent
        self.output_dir = self.script_dir / "batch-results"
        self.output_dir.mkdir(exist_ok=True)
        
        self.timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        self.log_file = self.output_dir / f"overnight-ial-{self.timestamp}.log"
        self.checkpoint_file = self.output_dir / "checkpoint-ial.json"
        self.summary_file = self.output_dir / f"summary-ial-{self.timestamp}.json"
        
        self.checkpoint = self._load_checkpoint() if resume else {'completed': [], 'failed': [], 'skipped': []}
        self.results = []
        self.start_time = time.time()
        
    def _load_checkpoint(self) -> Dict:
        """Load checkpoint if exists."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)
                    print(f"[INFO] Resuming: {len(checkpoint['completed'])} completed, {len(checkpoint['failed'])} failed")
                    return checkpoint
            except:
                pass
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
    
    def run_batch(self):
        """Run all International A Level subjects."""
        # Load subjects
        subjects_file = self.script_dir / "International-A-Level" / "international-a-level-subjects.json"
        with open(subjects_file, 'r', encoding='utf-8') as f:
            subjects = json.load(f)
        
        self._log("="*60)
        self._log("OVERNIGHT INTERNATIONAL A LEVEL BATCH SCRAPER")
        self._log("="*60)
        self._log(f"Total subjects: {len(subjects)}")
        self._log(f"Already completed: {len(self.checkpoint['completed'])}")
        self._log(f"To process: {len([s for s in subjects if s['code'] not in self.checkpoint['completed']])}")
        self._log(f"Estimated time: 1.5-2.5 hours")
        self._log(f"Estimated cost: $5-8")
        self._log("="*60)
        
        scraper_script = self.script_dir / "ai-powered-scraper-openai.py"
        
        for idx, subject in enumerate(subjects, 1):
            code = subject['code']
            name = subject['name']
            
            # Skip if already done
            if code in self.checkpoint['completed']:
                self._log(f"[{idx}/{len(subjects)}] ✓ SKIP: {name} ({code}) - already completed")
                continue
            
            self._log(f"\n[{idx}/{len(subjects)}] PROCESSING: {name} ({code})")
            self._log("-"*60)
            
            subject_start = time.time()
            
            try:
                # Run scraper
                result = subprocess.run(
                    [sys.executable, str(scraper_script), '--subject', code],
                    cwd=self.script_dir,
                    capture_output=True,
                    text=True,
                    timeout=360  # 6 minute timeout (A Levels are bigger)
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
                    # Failed
                    self.checkpoint['failed'].append(code)
                    self._save_checkpoint()
                    
                    error_msg = result.stderr[-500:] if result.stderr else "Unknown error"
                    self._log(f"❌ FAILED: {name} - {error_msg}")
                    
                    self.results.append({
                        'code': code,
                        'name': name,
                        'status': 'failed',
                        'error': error_msg,
                        'time_seconds': subject_time
                    })
                
                # Small delay between subjects
                time.sleep(3)
                
            except subprocess.TimeoutExpired:
                self._log(f"⏱️ TIMEOUT: {name} - exceeded 6 minutes")
                self.checkpoint['failed'].append(code)
                self._save_checkpoint()
                
                self.results.append({
                    'code': code,
                    'name': name,
                    'status': 'timeout',
                    'time_seconds': 360
                })
                
            except KeyboardInterrupt:
                self._log(f"\n⚠️ INTERRUPTED by user at {name}")
                self._save_checkpoint()
                self._save_summary()
                print("\n[INFO] Progress saved. Run with --resume to continue.")
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
            'batch_name': 'International A Level Overnight Batch',
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': datetime.now().isoformat(),
            'elapsed_seconds': elapsed,
            'elapsed_formatted': f"{elapsed/3600:.1f} hours",
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
        self._log("OVERNIGHT IAL BATCH COMPLETE")
        self._log("="*60)
        self._log(f"Time elapsed: {elapsed/3600:.1f} hours ({elapsed/60:.0f} minutes)")
        self._log(f"Total subjects: {len(self.results)}")
        self._log(f"✅ Success: {len(success)}")
        self._log(f"❌ Failed: {len(failed)}")
        
        if success:
            total_topics = sum(r.get('topics', 0) for r in success)
            avg_topics = total_topics / len(success)
            self._log(f"📚 Total topics extracted: {total_topics}")
            self._log(f"📊 Average topics/subject: {avg_topics:.0f}")
        
        if failed:
            self._log(f"\nFailed subjects:")
            for r in failed:
                self._log(f"  - {r['name']} ({r['code']})")
        
        self._log("="*60)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Overnight International A Level batch scraper')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    args = parser.parse_args()
    
    print("\n" + "🌙 "*20)
    print("OVERNIGHT INTERNATIONAL A LEVEL BATCH SCRAPER")
    print("🌙 "*20)
    print("\nThis will scrape all 21 International A Level subjects using GPT-4")
    print("Estimated time: 1.5-2.5 hours")
    print("Estimated cost: $5-8")
    print("\nInternational A Levels typically have more depth than IGCSE")
    print("Expect 200-400 topics per subject (vs 100-200 for IGCSE)")
    print("\nPress Ctrl+C at any time to pause (progress will be saved)")
    
    if not args.resume:
        response = input("\nStart International A Level batch? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled.")
            sys.exit(0)
    
    runner = IALBatchRunner(resume=args.resume)
    runner.run_batch()


if __name__ == '__main__':
    main()

