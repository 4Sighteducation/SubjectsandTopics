#!/usr/bin/env python
"""
Robust Batch Processor for All AQA Subjects
Fixes automation issues - runs all subjects reliably with progress tracking
"""

import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Ensure we're in the right directory
script_dir = Path(__file__).parent
os.chdir(script_dir)
sys.path.insert(0, str(script_dir))

from database.supabase_client import SupabaseUploader
from scrapers.uk.aqa_hybrid_scraper import AQAHybridScraper
from utils.logger import setup_logger

load_dotenv()


class BatchProcessor:
    """Robust batch processor with progress tracking and resume capability."""
    
    def __init__(self, test_mode=False):
        """
        Initialize batch processor.
        
        Args:
            test_mode: If True, only process first 3 subjects for testing
        """
        self.test_mode = test_mode
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Setup logging
        log_file = f'data/logs/batch_{self.timestamp}.log'
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logger('INFO', log_file)
        
        # State file for resumability
        self.state_file = f'data/state/batch_state_{self.timestamp}.json'
        Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize state
        self.state = self._load_or_create_state()
        
        # Initialize components
        self.uploader = SupabaseUploader()
        self.scraper = AQAHybridScraper(headless=True, supabase_uploader=self.uploader)
        
        self.logger.info("=" * 80)
        self.logger.info(f"BATCH PROCESSOR INITIALIZED")
        self.logger.info(f"Test Mode: {test_mode}")
        self.logger.info(f"State File: {self.state_file}")
        self.logger.info("=" * 80)
    
    def _load_or_create_state(self):
        """Load existing state or create new."""
        if os.path.exists(self.state_file):
            with open(self.state_file) as f:
                return json.load(f)
        
        return {
            'timestamp': self.timestamp,
            'completed': [],
            'failed': [],
            'partial': [],
            'current': None,
            'total_processed': 0
        }
    
    def _save_state(self):
        """Save current state to file."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def load_subjects(self):
        """Load subject configuration."""
        config_path = Path(__file__).parent / 'config' / 'aqa_subjects.yaml'
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        subjects = []
        art_added = False  # Track if we've added Art and Design already
        
        # A-Level subjects
        for subject_key, subject_code in config['a_level'].items():
            subject_name = subject_key.replace('_', ' ')
            
            # SPECIAL CASE: Art and Design - only add ONCE with first code
            if 'Art and Design' in subject_name:
                if not art_added:
                    subjects.append({
                        'name': 'Art and Design',  # Simplified name
                        'code': '7201',  # Use first code (Art, craft and design)
                        'qualification': 'A-Level',
                        'key': 'Art_and_Design',
                        'is_art': True
                    })
                    art_added = True
                continue  # Skip other Art variants
            
            subjects.append({
                'name': subject_name,
                'code': subject_code,
                'qualification': 'A-Level',
                'key': subject_key
            })
        
        # GCSE subjects  
        art_added_gcse = False
        for subject_key, subject_code in config['gcse'].items():
            subject_name = subject_key.replace('_', ' ')
            
            # SPECIAL CASE: GCSE Art and Design - only add ONCE
            if 'Art and Design' in subject_name:
                if not art_added_gcse:
                    subjects.append({
                        'name': 'Art and Design',
                        'code': '8201',  # First GCSE Art code
                        'qualification': 'GCSE',
                        'key': 'Art_and_Design',
                        'is_art': True
                    })
                    art_added_gcse = True
                continue
            
            subjects.append({
                'name': subject_name,
                'code': subject_code,
                'qualification': 'GCSE',
                'key': subject_key
            })
        
        # Filter out already completed
        remaining = [
            s for s in subjects 
            if f"{s['name']}_{s['qualification']}" not in self.state['completed']
        ]
        
        if self.test_mode:
            return remaining[:3]
        
        return remaining
    
    def process_all(self):
        """Process all subjects with robust error handling."""
        subjects = self.load_subjects()
        
        self.logger.info(f"\nProcessing {len(subjects)} subjects")
        self.logger.info(f"Already completed: {len(self.state['completed'])}")
        self.logger.info(f"Previously failed: {len(self.state['failed'])}\n")
        
        for i, subject in enumerate(subjects, 1):
            subject_id = f"{subject['name']}_{subject['qualification']}"
            
            self.logger.info("=" * 80)
            self.logger.info(f"[{i}/{len(subjects)}] Processing: {subject['name']} ({subject['qualification']})")
            self.logger.info("=" * 80)
            
            self.state['current'] = subject_id
            self._save_state()
            
            try:
                # Process the subject using hybrid scraper (web + PDF backup)
                result = self.scraper.process_subject_complete(
                    subject=subject['name'],
                    qualification=subject['qualification'],
                    subject_code=subject['code'],
                    upload_to_supabase=True  # Hybrid scraper handles upload
                )
                
                # Check result
                if result['success']:
                    self.state['completed'].append(subject_id)
                    self.logger.info(f"SUCCESS: {subject_id} (method: {result['method']})")
                else:
                    self.state['failed'].append(subject_id)
                    self.logger.error(f"FAILED: {subject_id} - {result.get('errors')}")
                
                self.state['total_processed'] += 1
                
            except KeyboardInterrupt:
                self.logger.warning("\n⚠️ Interrupted by user. State saved. Run again to resume.")
                self._save_state()
                self.scraper.close()
                sys.exit(1)
                
            except Exception as e:
                self.logger.error(f"❌ EXCEPTION: {subject_id} - {str(e)}", exc_info=True)
                self.state['failed'].append(subject_id)
            
            finally:
                self.state['current'] = None
                self._save_state()
        
        # Generate final report
        self.generate_report()
        self.scraper.close()
    
    def generate_report(self):
        """Generate HTML report of batch processing."""
        report_file = f'data/reports/batch_report_{self.timestamp}.html'
        Path(report_file).parent.mkdir(parents=True, exist_ok=True)
        
        total = len(self.state['completed']) + len(self.state['partial']) + len(self.state['failed'])
        success_rate = (len(self.state['completed']) / total * 100) if total > 0 else 0
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>AQA Batch Processing Report - {self.timestamp}</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f7fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; margin: 0 0 10px 0; font-size: 32px; }}
        .subtitle {{ color: #7f8c8d; font-size: 14px; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 8px; text-align: center; color: white; }}
        .stat-card.success {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
        .stat-card.partial {{ background: linear-gradient(135deg, #f2994a 0%, #f2c94c 100%); }}
        .stat-card.failed {{ background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }}
        .stat-number {{ font-size: 48px; font-weight: bold; margin-bottom: 5px; }}
        .stat-label {{ font-size: 14px; opacity: 0.9; }}
        .section {{ margin: 40px 0; }}
        .section h2 {{ color: #34495e; font-size: 24px; margin-bottom: 15px; border-left: 4px solid #3498db; padding-left: 15px; }}
        .subject-list {{ display: grid; gap: 10px; }}
        .subject-item {{ padding: 15px; background: #f8f9fa; border-radius: 6px; border-left: 4px solid #3498db; }}
        .subject-item.success {{ border-left-color: #38ef7d; background: #e8f8f5; }}
        .subject-item.partial {{ border-left-color: #f2c94c; background: #fff9e6; }}
        .subject-item.failed {{ border-left-color: #f45c43; background: #ffebe6; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
        .badge.success {{ background: #38ef7d; color: white; }}
        .badge.partial {{ background: #f2c94c; color: #333; }}
        .badge.failed {{ background: #f45c43; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 AQA Batch Processing Report</h1>
        <div class="subtitle">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Run ID: {self.timestamp}</div>
        
        <div class="summary">
            <div class="stat-card">
                <div class="stat-number">{total}</div>
                <div class="stat-label">Total Subjects</div>
            </div>
            <div class="stat-card success">
                <div class="stat-number">{len(self.state['completed'])}</div>
                <div class="stat-label">Completed</div>
            </div>
            <div class="stat-card partial">
                <div class="stat-number">{len(self.state['partial'])}</div>
                <div class="stat-label">Partial</div>
            </div>
            <div class="stat-card failed">
                <div class="stat-number">{len(self.state['failed'])}</div>
                <div class="stat-label">Failed</div>
            </div>
        </div>
        
        <div class="section">
            <h2>✅ Successfully Completed ({len(self.state['completed'])})</h2>
            <div class="subject-list">
"""
        
        for subject in self.state['completed']:
            html += f'                <div class="subject-item success"><span class="badge success">✓</span> {subject}</div>\n'
        
        html += f"""            </div>
        </div>
        
        <div class="section">
            <h2>⚠️ Partially Completed ({len(self.state['partial'])})</h2>
            <div class="subject-list">
"""
        
        for subject in self.state['partial']:
            html += f'                <div class="subject-item partial"><span class="badge partial">⚠</span> {subject}</div>\n'
        
        html += f"""            </div>
        </div>
        
        <div class="section">
            <h2>❌ Failed ({len(self.state['failed'])})</h2>
            <div class="subject-list">
"""
        
        for subject in self.state['failed']:
            html += f'                <div class="subject-item failed"><span class="badge failed">✗</span> {subject}</div>\n'
        
        html += f"""            </div>
        </div>
        
        <div class="section">
            <h2>📊 Statistics</h2>
            <ul>
                <li><strong>Success Rate:</strong> {success_rate:.1f}%</li>
                <li><strong>Total Processed:</strong> {self.state['total_processed']}</li>
                <li><strong>Log File:</strong> data/logs/batch_{self.timestamp}.log</li>
                <li><strong>State File:</strong> {self.state_file}</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>🎯 Next Steps</h2>
            <ul>
                <li>Review failed subjects in log file</li>
                <li>Check Supabase for uploaded data</li>
                <li>Re-run failed subjects individually if needed</li>
                <li>Proceed to international scrapers (Cambridge, IB)</li>
            </ul>
        </div>
    </div>
</body>
</html>"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info("BATCH PROCESSING COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"Completed: {len(self.state['completed'])}")
        self.logger.info(f"Partial: {len(self.state['partial'])}")
        self.logger.info(f"Failed: {len(self.state['failed'])}")
        self.logger.info(f"Success Rate: {success_rate:.1f}%")
        self.logger.info(f"\n📊 Report: {report_file}")
        self.logger.info("=" * 80)
        
        # Open report in browser
        import webbrowser
        webbrowser.open(f'file:///{Path(report_file).absolute()}')


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch Process All AQA Subjects')
    parser.add_argument('--test', action='store_true', help='Test mode: only process 3 subjects')
    parser.add_argument('--resume', help='Resume from specific state file')
    
    args = parser.parse_args()
    
    # Validate environment
    required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'ANTHROPIC_API_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("\nPlease set these in your .env file:")
        for var in missing:
            print(f"  {var}=your_value_here")
        return 1
    
    # Create processor and run
    processor = BatchProcessor(test_mode=args.test)
    
    try:
        processor.process_all()
        return 0
    except Exception as e:
        processor.logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
