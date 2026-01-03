"""
Test the hierarchy parser without uploading to Supabase
========================================================

Just parses and shows what would be uploaded.

Usage:
    python test-hierarchy-parse.py
"""

import sys
import re
from pathlib import Path

# Import the parse function
sys.path.insert(0, str(Path(__file__).parent))

from collections import defaultdict

def sanitize_code(text):
    """Convert text to safe code format."""
    safe = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    safe = re.sub(r'\s+', '_', safe.strip())
    return safe[:50]


# Read the hierarchy text from upload-from-hierarchy-text.py
upload_file = Path(__file__).parent / "upload-from-hierarchy-text.py"
content = upload_file.read_text(encoding='utf-8')

# Extract HIERARCHY_TEXT
hierarchy_start = content.find('HIERARCHY_TEXT = """') + len('HIERARCHY_TEXT = """')
hierarchy_end = content.find('"""', hierarchy_start)
hierarchy_text = content[hierarchy_start:hierarchy_end].strip()

# Extract SUBJECT_INFO
subject_start = content.find('SUBJECT_INFO = {')
subject_end = content.find('}', subject_start) + 1
subject_info_text = content[subject_start:subject_end]

print("=" * 80)
print("HIERARCHY PARSER TEST (DRY RUN - NO UPLOAD)")
print("=" * 80)
print(f"\nHierarchy text length: {len(hierarchy_text)} characters")
print(f"Estimated lines: {len(hierarchy_text.split(chr(10)))}")
print()

# Count patterns
areas = len(re.findall(r'^Area of Study', hierarchy_text, re.MULTILINE))
sections = len(re.findall(r'^Section \d+:', hierarchy_text, re.MULTILINE))
level2 = len(re.findall(r'^\d+\.\d+\s+', hierarchy_text, re.MULTILINE))
level3 = len(re.findall(r'^\d+\.\d+\.\d+\s+', hierarchy_text, re.MULTILINE))

print(f"Detected patterns:")
print(f"  - Areas of Study: {areas}")
print(f"  - Sections: {sections}")
print(f"  - Level 2 (1.1): {level2}")
print(f"  - Level 3 (1.1.1): {level3}")
print()

print(f"Estimated total topics: {areas + sections + level2 + level3 + 500} (rough estimate)")
print()
print("=" * 80)
print()

response = input("This looks like a LARGE upload. Continue with test parse? (y/n): ")

if response.lower() != 'y':
    print("Aborted.")
    sys.exit(0)

# Now import and run the parse function
exec(compile(open(upload_file, encoding='utf-8').read(), upload_file, 'exec'))

