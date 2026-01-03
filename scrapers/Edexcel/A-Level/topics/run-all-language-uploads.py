"""
Run all Edexcel A-Level language manual uploads
Uploads: Greek, French, German, Spanish, Italian, Gujarati, Japanese, Portuguese, Russian
"""

import os
import sys
import subprocess
from pathlib import Path

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Language upload scripts to run
UPLOAD_SCRIPTS = [
    ('Greek', 'upload-greek-manual.py'),
    ('French', 'upload-french-manual.py'),
    ('German', 'upload-german-manual.py'),
    ('Spanish', 'upload-spanish-manual.py'),
    ('Italian', 'upload-italian-manual.py'),
    ('Gujarati', 'upload-gujarati-manual.py'),
    ('Japanese', 'upload-japanese-manual.py'),
    ('Portuguese', 'upload-portuguese-manual.py'),
    ('Russian', 'upload-russian-manual.py'),
]

def main():
    print("=" * 80)
    print("EDEXCEL A-LEVEL LANGUAGES - BATCH UPLOAD")
    print("=" * 80)
    print(f"\nUploading {len(UPLOAD_SCRIPTS)} languages with complete hierarchies\n")
    
    results = {'success': [], 'failed': []}
    
    for lang_name, script_name in UPLOAD_SCRIPTS:
        print(f"\n{'=' * 80}")
        print(f"Processing: {lang_name}")
        print(f"{'=' * 80}\n")
        
        try:
            result = subprocess.run(
                [sys.executable, script_name],
                capture_output=False,
                text=True,
                check=True
            )
            results['success'].append(lang_name)
            print(f"\n[OK] {lang_name} completed successfully!")
            
        except subprocess.CalledProcessError as e:
            results['failed'].append(lang_name)
            print(f"\n[ERROR] {lang_name} failed!")
        except Exception as e:
            results['failed'].append(lang_name)
            print(f"\n[ERROR] {lang_name} failed: {e}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("BATCH UPLOAD SUMMARY")
    print("=" * 80)
    print(f"\n✅ Successfully uploaded: {len(results['success'])}/{len(UPLOAD_SCRIPTS)}")
    for lang in results['success']:
        print(f"   • {lang}")
    
    if results['failed']:
        print(f"\n❌ Failed: {len(results['failed'])}")
        for lang in results['failed']:
            print(f"   • {lang}")
    
    print("\n" + "=" * 80)
    print(f"Total: {len(results['success'])} languages uploaded with complete hierarchies!")
    print("=" * 80)


if __name__ == '__main__':
    main()











