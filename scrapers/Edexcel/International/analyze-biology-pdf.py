"""
Analyze International GCSE Biology PDF Structure
=================================================
Let's see what the actual content structure looks like to improve parsing.
"""

import os
import sys
import requests
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv

try:
    import pdfplumber
except ImportError:
    print("Installing pdfplumber...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfplumber"])
    import pdfplumber

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

PDF_URL = "https://qualifications.pearson.com/content/dam/pdf/International%20GCSE/Biology/2017/specification-and-sample-assessments/international-gcse-biology-2017-specification1.pdf"

print("Downloading PDF...")
response = requests.get(PDF_URL, timeout=30)
pdf_content = response.content
print(f"Downloaded {len(pdf_content)} bytes\n")

print("Extracting text from pages 9-20 (content section)...")
with pdfplumber.open(BytesIO(pdf_content)) as pdf:
    for page_num in range(8, 20):  # Pages 9-20 (0-indexed)
        if page_num >= len(pdf.pages):
            break
            
        page = pdf.pages[page_num]
        text = page.extract_text()
        
        print(f"\n{'='*60}")
        print(f"PAGE {page_num + 1}")
        print('='*60)
        
        # Show first 50 lines
        lines = text.split('\n')[:50]
        for i, line in enumerate(lines, 1):
            if line.strip():
                print(f"{i:3d}: {line}")
        
        if page_num == 10:  # Show more detail for page 11
            print("\n[Showing more lines from page 11...]")
            for i, line in enumerate(text.split('\n')[50:100], 51):
                if line.strip():
                    print(f"{i:3d}: {line}")

