"""
GCSE Physics (Standalone) - Structure Uploader
==============================================

Uploads Physics Paper 1 & 2 as a standalone GCSE subject.
Content extracted from Combined Science (Papers 5 & 6 become Papers 1 & 2).

Usage:
    python upload-physics-standalone.py
"""

import os
import sys
import re
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

SUBJECT_INFO = {
    'code': 'GCSE-Physics',
    'name': 'Physics',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Science/2016/Specification/gcse-physics-spec.pdf'
}

# Read Physics content from the md file
script_dir = Path(__file__).parent
science_file = script_dir / 'edexcel science gcse.md'

print("=" * 80)
print("GCSE PHYSICS (STANDALONE) - STRUCTURE UPLOADER")
print("=" * 80)
print()

if not science_file.exists():
    print(f"[ERROR] File not found: {science_file}")
    sys.exit(1)

# Read and extract Physics sections (Papers 5 & 6 become Papers 1 & 2)
content = science_file.read_text(encoding='utf-8')

# Extract from "Paper 5: Physics" to end
phys_start = content.find('Paper 5: Physics')

if phys_start == -1:
    print("[ERROR] Could not find Physics sections in file!")
    sys.exit(1)

physics_text = content[phys_start:].strip()

# Rename Paper 5 -> Paper 1, Paper 6 -> Paper 2
physics_text = physics_text.replace('Paper 5: Physics', 'Paper 1: Physics')
physics_text = physics_text.replace('Paper 6: Physics', 'Paper 2: Physics')

print(f"[INFO] Extracted Physics content ({len(physics_text)} characters)")
print()

# Now use the same parser
upload_script = script_dir / 'upload-from-hierarchy-text.py'
exec_globals = {}
exec(compile(upload_script.read_text(encoding='utf-8'), upload_script, 'exec'), exec_globals)
parse_hierarchy = exec_globals['parse_hierarchy']
upload_topics_func = exec_globals['upload_topics']

topics = parse_hierarchy(physics_text)

if not topics:
    print("[ERROR] No topics parsed!")
    sys.exit(1)

print(f"\n[OK] Parsed {len(topics)} Physics topics")

# Upload
success = upload_topics_func(SUBJECT_INFO, topics)

if success:
    print("\n✅ COMPLETE!")
    print("\nGCSE Physics (Standalone) uploaded:")
    print("  - Paper 1 & Paper 2")
    print("  - Topics 1-6, 8-15")
    print(f"  - Total: {len(topics)} topics")
else:
    print("\n❌ FAILED")

