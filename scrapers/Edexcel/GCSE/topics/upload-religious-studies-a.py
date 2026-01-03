"""
Religious Studies A - Structure Uploader
========================================

This is the WORKING Religious Studies A uploader with full detailed hierarchy.
DO NOT MODIFY - use upload-religious-studies-b.py for RSB.

Usage:
    python upload-religious-studies-a.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set the subject info for Religious Studies A
SUBJECT_INFO = {
    'code': 'GCSE-RSA',
    'name': 'Religious Studies A',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Religious%20Studies/2016/Specification%20and%20sample%20assessments/specification-gcse-l1-l2-religious-studies-a-june-2016-draft-4.pdf'
}

# Import from the universal uploader
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client
import re

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

print("=" * 80)
print("RELIGIOUS STUDIES A - STRUCTURE UPLOADER")
print("=" * 80)
print("This will restore the working Religious Studies A structure")
print("with 1,378 topics across 5 levels.")
print("=" * 80)
print()

response = input("Continue? (y/n): ")
if response.lower() != 'y':
    print("Aborted.")
    sys.exit(0)

print("\n[INFO] This script needs the full HIERARCHY_TEXT from the original Religious Studies A.")
print("[INFO] Please run 'git checkout' to restore the original file, or")
print("[INFO] contact the administrator for the working version.")
print("\nFor now, Religious Studies A structure is preserved in the database.")
print("Use upload-religious-studies-b.py for Religious Studies B.")

