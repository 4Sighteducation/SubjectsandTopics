"""
GCSE Chemistry (Standalone) - Structure Uploader
================================================

Uploads Chemistry Paper 1 & 2 as a standalone GCSE subject.
Content extracted from Combined Science (Papers 3 & 4 become Papers 1 & 2).

Usage:
    python upload-chemistry-standalone.py
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
    'code': 'GCSE-Chemistry',
    'name': 'Chemistry',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Science/2016/Specification/gcse-chemistry-spec.pdf'
}

# Read Chemistry content from the md file
script_dir = Path(__file__).parent
science_file = script_dir / 'edexcel science gcse.md'

print("=" * 80)
print("GCSE CHEMISTRY (STANDALONE) - STRUCTURE UPLOADER")
print("=" * 80)
print()

if not science_file.exists():
    print(f"[ERROR] File not found: {science_file}")
    sys.exit(1)

# Read and extract Chemistry sections (Papers 3 & 4 become Papers 1 & 2)
content = science_file.read_text(encoding='utf-8')

# Extract from "Paper 3: Chemistry" to "Paper 5: Physics"
chem_start = content.find('Paper 3: Chemistry')
chem_end = content.find('Paper 5: Physics')

if chem_start == -1 or chem_end == -1:
    print("[ERROR] Could not find Chemistry sections in file!")
    sys.exit(1)

chemistry_text = content[chem_start:chem_end].strip()

# Rename Paper 3 -> Paper 1, Paper 4 -> Paper 2
chemistry_text = chemistry_text.replace('Paper 3: Chemistry', 'Paper 1: Chemistry')
chemistry_text = chemistry_text.replace('Paper 4: Chemistry', 'Paper 2: Chemistry')

print(f"[INFO] Extracted Chemistry content ({len(chemistry_text)} characters)")
print()

# Now use the same parser
upload_script = script_dir / 'upload-from-hierarchy-text.py'
exec_globals = {}
exec(compile(upload_script.read_text(encoding='utf-8'), upload_script, 'exec'), exec_globals)
parse_hierarchy = exec_globals['parse_hierarchy']
upload_topics_func = exec_globals['upload_topics']

topics = parse_hierarchy(chemistry_text)

if not topics:
    print("[ERROR] No topics parsed!")
    sys.exit(1)

print(f"\n[OK] Parsed {len(topics)} Chemistry topics")

# Upload
success = upload_topics_func(SUBJECT_INFO, topics)

if success:
    print("\n✅ COMPLETE!")
    print("\nGCSE Chemistry (Standalone) uploaded:")
    print("  - Paper 1 & Paper 2")
    print("  - Topics 1-8")
    print(f"  - Total: {len(topics)} topics")
else:
    print("\n❌ FAILED")

