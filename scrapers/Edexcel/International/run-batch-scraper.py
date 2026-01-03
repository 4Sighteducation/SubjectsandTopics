"""
Batch Runner for International Qualifications
==============================================

Runs the topic scraper in controlled batches with logging and error recovery.

Usage:
    python run-batch-scraper.py --igcse          # Run International GCSE batch
    python run-batch-scraper.py --ial            # Run International A Level batch
    python run-batch-scraper.py --all            # Run all batches
    python run-batch-scraper.py --resume         # Resume from last checkpoint
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Import the scraper
from universal_international_scraper import InternationalTopicScraper, load_subjects


class BatchRunner:
    """Manages batch execution with checkpointing and logging."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        
        self.checkpoint_file = output_dir / "checkpoint.json"
        self.log_file = output_dir / f"batch-run-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
        
        self.checkpoint = self._load_checkpoint()
        self.results = []
        
    def _load_checkpoint(self) -> Dict:
        """Load checkpoint if exists."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'completed': [], 'failed': []}
    
    def _save_checkpoint(self):
        """Save current checkpoint."""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.checkpoint, f, indent=2)
    
    def _log(self, message: str):
        """Write to log file and console."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    
    def should_skip(self, subject_code: str) -> bool:
        """Check if subject should be skipped (already processed)."""
        return subject_code in self.checkpoint['completed']
    
    def run_batch(self, subjects: List[Dict], batch_name: str = "Batch"):
        """Run scraping for a batch of subjects."""
        self._log(f"\n{'=' * 60}")
        self._log(f"STARTING {batch_name}")
        self._log(f"Total subjects: {len(subjects)}")
        self._log(f"{'=' * 60}\n")
        
        start_time = time.time()
        
        for idx, subject in enumerate(subjects, 1):
            subject_code = subject['code']
            
            # Check if already processed
            if self.should_skip(subject_code):
                self._log(f"[{idx}/{len(subjects)}] SKIPPING {subject_code} (already completed)")
                continue
            
            self._log(f"\n[{idx}/{len(subjects)}] PROCESSING: {subject['name']} ({subject_code})")
            
            try:
                scraper = InternationalTopicScraper(subject)
                success = scraper.scrape()
                
                if success:
                    self.checkpoint['completed'].append(subject_code)
                    self._save_checkpoint()
                    self._log(f"✓ SUCCESS: {subject_code}")
                    
                    self.results.append({
                        'subject_code': subject_code,
                        'subject_name': subject['name'],
                        'status': 'success',
                        'topics_found': len(scraper.topics)
                    })
                else:
                    self.checkpoint['failed'].append(subject_code)
                    self._save_checkpoint()
                    self._log(f"✗ FAILED: {subject_code}")
                    
                    self.results.append({
                        'subject_code': subject_code,
                        'subject_name': subject['name'],
                        'status': 'failed',
                        'topics_found': 0
                    })
                
                # Small delay between subjects
                time.sleep(2)
                
            except KeyboardInterrupt:
                self._log(f"\n⚠ INTERRUPTED by user")
                self._save_checkpoint()
                raise
            
            except Exception as e:
                self._log(f"✗ ERROR: {subject_code} - {str(e)}")
                self.checkpoint['failed'].append(subject_code)
                self._save_checkpoint()
                
                self.results.append({
                    'subject_code': subject_code,
                    'subject_name': subject['name'],
                    'status': 'error',
                    'error': str(e),
                    'topics_found': 0
                })
        
        # Summary
        elapsed = time.time() - start_time
        success_count = sum(1 for r in self.results if r['status'] == 'success')
        failed_count = len(self.results) - success_count
        
        self._log(f"\n{'=' * 60}")
        self._log(f"{batch_name} COMPLETE")
        self._log(f"{'=' * 60}")
        self._log(f"Time elapsed: {elapsed/60:.1f} minutes")
        self._log(f"Successful: {success_count}")
        self._log(f"Failed: {failed_count}")
        self._log(f"Total: {len(self.results)}")
        self._log(f"{'=' * 60}\n")
        
        # Save results summary
        summary_file = self.output_dir / f"summary-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'batch_name': batch_name,
                'start_time': datetime.now().isoformat(),
                'elapsed_seconds': elapsed,
                'summary': {
                    'success': success_count,
                    'failed': failed_count,
                    'total': len(self.results)
                },
                'results': self.results
            }, f, indent=2)
        
        self._log(f"Summary saved to: {summary_file}")


def main():
    parser = argparse.ArgumentParser(description='Batch scrape International qualifications')
    parser.add_argument('--igcse', action='store_true', help='Run International GCSE batch')
    parser.add_argument('--ial', action='store_true', help='Run International A Level batch')
    parser.add_argument('--all', action='store_true', help='Run all batches')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--reset', action='store_true', help='Reset checkpoint and start fresh')
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    output_dir = script_dir / "batch-results"
    
    runner = BatchRunner(output_dir)
    
    if args.reset:
        if runner.checkpoint_file.exists():
            runner.checkpoint_file.unlink()
            print("[INFO] Checkpoint reset")
        return
    
    try:
        if args.igcse or args.all or args.resume:
            ig_file = script_dir / "International-GCSE" / "international-gcse-subjects.json"
            ig_subjects = load_subjects(ig_file)
            runner.run_batch(ig_subjects, "International GCSE")
        
        if args.ial or args.all or args.resume:
            ial_file = script_dir / "International-A-Level" / "international-a-level-subjects.json"
            ial_subjects = load_subjects(ial_file)
            runner.run_batch(ial_subjects, "International A Level")
        
        if not (args.igcse or args.ial or args.all or args.resume):
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n[INFO] Batch run interrupted. Progress saved to checkpoint.")
        print("[INFO] Run with --resume to continue from where you left off.")


if __name__ == '__main__':
    main()

