"""
Retry Failed Science Subjects
==============================

Retries only the science subjects that failed/timed out.
These are large specifications that need extended processing time.

Failed sciences:
- Chemistry
- Human Biology (timeout)
- Physics (timeout)
- Science (Double Award)

Extended timeouts: 15 minutes per subject (vs 5 minutes in batch)
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

FAILED_SCIENCES = [
    {'code': 'IG-Chemistry', 'name': 'Chemistry', 'reason': 'Unknown error'},
    {'code': 'IG-HumanBiology', 'name': 'Human Biology', 'reason': 'Timeout (5 min)'},
    {'code': 'IG-Physics', 'name': 'Physics', 'reason': 'Timeout (5 min)'},
    {'code': 'IG-ScienceDoubleAward', 'name': 'Science (Double Award)', 'reason': 'PDF extraction error'}
]

def main():
    script_dir = Path(__file__).parent
    scraper = script_dir / 'ai-powered-scraper-openai.py'
    
    print("\n" + "="*60)
    print("RETRYING 4 FAILED SCIENCE SUBJECTS")
    print("="*60)
    print("\nThese are large specifications that need extra time:")
    for s in FAILED_SCIENCES:
        print(f"  - {s['name']} ({s['reason']})")
    
    print(f"\nExtended timeout: 15 minutes per subject")
    print(f"Estimated total time: 30-60 minutes")
    print("="*60 + "\n")
    
    input("Press Enter to start retries...")
    
    results = {'success': 0, 'failed': 0}
    
    for idx, subject in enumerate(FAILED_SCIENCES, 1):
        code = subject['code']
        name = subject['name']
        
        print(f"\n[{idx}/4] RETRYING: {name} ({code})")
        print("-"*60)
        print(f"Original failure reason: {subject['reason']}")
        print("Starting scrape with 15 minute timeout...\n")
        
        start_time = datetime.now()
        
        try:
            result = subprocess.run(
                [sys.executable, str(scraper), '--subject', code],
                cwd=script_dir,
                timeout=900  # 15 minute timeout for large sciences
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if result.returncode == 0:
                results['success'] += 1
                print(f"\n✅ {name} SUCCESS ({elapsed:.1f}s)")
            else:
                results['failed'] += 1
                print(f"\n❌ {name} FAILED ({elapsed:.1f}s)")
                
        except subprocess.TimeoutExpired:
            results['failed'] += 1
            print(f"\n⏱️ {name} TIMEOUT (15 minutes) - spec may be too large for single-pass")
            print(f"   → Consider manual refinement or multi-pass approach")
            
        except KeyboardInterrupt:
            print(f"\n⚠️ Interrupted at {name}")
            break
            
        except Exception as e:
            results['failed'] += 1
            print(f"\n💥 {name} ERROR: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"RETRY COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Success: {results['success']}/4")
    print(f"❌ Failed: {results['failed']}/4")
    
    if results['failed'] > 0:
        print(f"\nRemaining failures will need manual review or alternative approach.")
        print(f"Check the AI output files in adobe-ai-output/ for partial content.")
    
    print("="*60)


if __name__ == '__main__':
    main()

