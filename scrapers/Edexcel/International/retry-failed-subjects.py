"""
Retry Failed IGCSE Subjects
============================

Retries the subjects that failed in the overnight batch with:
- Longer timeouts
- Better error handling
- Saves individual logs

Failed subjects from batch:
- Chemistry
- Chinese  
- Human Biology (timeout)
- Physics (timeout)
- Science (Double Award)
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

FAILED_SUBJECTS = [
    'IG-Chemistry',
    'IG-Chinese',
    'IG-HumanBiology',
    'IG-Physics',
    'IG-ScienceDoubleAward'
]

def main():
    script_dir = Path(__file__).parent
    scraper = script_dir / 'ai-powered-scraper-openai.py'
    
    print("\n" + "="*60)
    print("RETRYING 5 FAILED SUBJECTS")
    print("="*60)
    print(f"Will retry: {', '.join(FAILED_SUBJECTS)}")
    print("\nThis may take 30-60 minutes")
    print("="*60 + "\n")
    
    results = {'success': 0, 'failed': 0}
    
    for idx, code in enumerate(FAILED_SUBJECTS, 1):
        print(f"\n[{idx}/5] RETRYING: {code}")
        print("-"*60)
        
        try:
            result = subprocess.run(
                [sys.executable, str(scraper), '--subject', code],
                cwd=script_dir,
                timeout=600  # 10 minute timeout (double the original)
            )
            
            if result.returncode == 0:
                results['success'] += 1
                print(f"✅ {code} SUCCESS")
            else:
                results['failed'] += 1
                print(f"❌ {code} FAILED")
                
        except subprocess.TimeoutExpired:
            results['failed'] += 1
            print(f"⏱️ {code} TIMEOUT (10 minutes)")
        except KeyboardInterrupt:
            print(f"\n⚠️ Interrupted at {code}")
            break
        except Exception as e:
            results['failed'] += 1
            print(f"💥 {code} ERROR: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"RETRY COMPLETE")
    print(f"{'='*60}")
    print(f"Success: {results['success']}/5")
    print(f"Failed: {results['failed']}/5")
    print("="*60)


if __name__ == '__main__':
    main()

