"""
GCSE Biology (Standalone) - Structure Uploader
==============================================

Uploads Biology as a separate subject with Papers 1 & 2.

Usage:
    python upload-biology-standalone.py
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
    'code': 'GCSE-Biology',
    'name': 'Biology',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Science/2016/Specification/gcse-biology-spec.pdf'
}

# Import the parser from the universal uploader
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("GCSE BIOLOGY (STANDALONE) - UPLOADER")
print("=" * 80)
print("This will upload Biology as a separate subject")
print("Reading content from edexcel science gcse.md...")
print("=" * 80)

# Read Biology content from the markdown file
md_file = Path(__file__).parent / "edexcel science gcse.md"
full_content = md_file.read_text(encoding='utf-8')

# Extract just Biology papers (Papers 1 & 2)
lines = full_content.split('\n')
biology_lines = []
in_biology = False

for line in lines:
    if line.startswith('Paper 1: Biology'):
        in_biology = True
    elif line.startswith('Paper 3: Chemistry'):
        in_biology = False
        break
    
    if in_biology:
        biology_lines.append(line)

HIERARCHY_TEXT = '\n'.join(biology_lines)

print(f"\n[INFO] Extracted {len(biology_lines)} lines of Biology content")
print(f"[INFO] From Paper 1 & Paper 2")
print()

# Now run the same parser logic
# (Copy the parse_hierarchy and upload_topics functions here or import them)

from upload_from_hierarchy_text import parse_hierarchy, upload_topics

topics = parse_hierarchy(HIERARCHY_TEXT)

if not topics:
    print("[ERROR] No topics found!")
    sys.exit(1)

print(f"\n[OK] Parsed {len(topics)} topics")

success = upload_topics(SUBJECT_INFO, topics)

if success:
    print("\n✅ BIOLOGY (STANDALONE) COMPLETE!")
else:
    print("\n❌ FAILED")
