"""
Run Languages Using Tamil's Successful Approach
================================================

Uses the EXACT same scraper (ai-powered-scraper-openai.py) that worked for Tamil.

Tamil got 56 topics with vocabulary integrated:
1.1.1 Life in town
    1.1.1.1 Vocabulary: நகர மண்டபம் (town hall), கடற்�றம் (seaside)

This script runs that same approach on all remaining languages.

Usage:
    python run-languages-like-tamil.py --all
    python run-languages-like-tamil.py --subject IG-Bangla
"""

import subprocess
import sys
import time
from pathlib import Path

# Languages to process (standard structure languages)
LANGUAGE_SUBJECTS = [
    {'code': 'IG-French', 'name': 'French'},
    {'code': 'IG-Spanish', 'name': 'Spanish'},
    {'code': 'IG-German', 'name': 'German'},
    {'code': 'IG-Bangla', 'name': 'Bangla'},
    {'code': 'IG-Chinese', 'name': 'Chinese'},
    {'code': 'IG-Sinhala', 'name': 'Sinhala'},
    {'code': 'IG-Swahili', 'name': 'Swahili'},
    # Tamil already done successfully
]


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--subject', help='Subject code (e.g., IG-Bangla)')
    parser.add_argument('--all', action='store_true', help='All language subjects')
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    scraper = script_dir / 'ai-powered-scraper-openai.py'  # The WORKING version!
    
    if args.subject:
        subjects = [s for s in LANGUAGE_SUBJECTS if s['code'] == args.subject]
    elif args.all:
        subjects = LANGUAGE_SUBJECTS
    else:
        parser.print_help()
        sys.exit(1)
    
    print("\n" + "="*60)
    print("RUNNING LANGUAGES WITH TAMIL'S SUCCESSFUL METHOD")
    print("="*60)
    print(f"Will process {len(subjects)} language(s)")
    print(f"Using: {scraper.name}")
    print("="*60 + "\n")
    
    results = {'success': 0, 'failed': 0, 'details': []}
    
    for idx, subject in enumerate(subjects, 1):
        code = subject['code']
        name = subject['name']
        
        print(f"\n[{idx}/{len(subjects)}] PROCESSING: {name} ({code})")
        print("-"*60)
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                [sys.executable, str(scraper), '--subject', code],
                cwd=script_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            elapsed = time.time() - start_time
            
            if result.returncode == 0:
                # Extract topic count
                import re
                match = re.search(r'Parsed (\d+) topics', result.stdout)
                topic_count = int(match.group(1)) if match else 0
                
                results['success'] += 1
                print(f"✅ SUCCESS: {name} - {topic_count} topics ({elapsed:.1f}s)")
                
                results['details'].append({
                    'code': code,
                    'name': name,
                    'status': 'success',
                    'topics': topic_count,
                    'time': elapsed
                })
            else:
                results['failed'] += 1
                error = result.stderr[-200:] if result.stderr else "Unknown"
                print(f"❌ FAILED: {name} - {error}")
                
                results['details'].append({
                    'code': code,
                    'name': name,
                    'status': 'failed',
                    'error': error
                })
            
            # Small delay
            time.sleep(5)
            
        except subprocess.TimeoutExpired:
            results['failed'] += 1
            print(f"⏱️ TIMEOUT: {name} (5 minutes)")
            results['details'].append({
                'code': code,
                'name': name,
                'status': 'timeout'
            })
            
        except KeyboardInterrupt:
            print(f"\n⚠️ Interrupted at {name}")
            break
            
        except Exception as e:
            results['failed'] += 1
            print(f"💥 ERROR: {name} - {str(e)}")
            results['details'].append({
                'code': code,
                'name': name,
                'status': 'error',
                'error': str(e)
            })
    
    # Summary
    print(f"\n{'='*60}")
    print(f"LANGUAGE BATCH COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Success: {results['success']}/{len(subjects)}")
    print(f"❌ Failed: {results['failed']}/{len(subjects)}")
    
    if results['success'] > 0:
        total_topics = sum(r.get('topics', 0) for r in results['details'] if r['status'] == 'success')
        print(f"📚 Total topics: {total_topics}")
    
    if results['failed'] > 0:
        print(f"\nFailed subjects:")
        for r in results['details']:
            if r['status'] != 'success':
                print(f"  - {r['name']} ({r['code']}): {r.get('status', 'unknown')}")
    
    print("="*60)
    
    # Save results
    import json
    results_file = script_dir / "batch-results" / "language-batch-results.json"
    results_file.parent.mkdir(exist_ok=True)
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {results_file.name}")


if __name__ == '__main__':
    main()

