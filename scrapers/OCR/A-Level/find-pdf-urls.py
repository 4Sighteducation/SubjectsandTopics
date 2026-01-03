"""
Find correct PDF URLs for all OCR A-Level subjects by scraping their pages.
"""

import json
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

# Load subjects
subjects_file = Path(__file__).parent / "ocr-alevel-subjects.json"
with open(subjects_file, 'r', encoding='utf-8') as f:
    subjects = json.load(f)

# Setup browser
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=chrome_options)

print("Finding PDF URLs for all OCR A-Level subjects...\n")

updated = 0
failed = []

for code, info in subjects.items():
    print(f"[{code}] {info['name']}...")
    
    try:
        # Load the main qualification page (not "at a glance")
        base_url = info['at_a_glance_url'].replace('/specification-at-a-glance/', '/')
        driver.get(base_url)
        time.sleep(3)
        
        # Find PDF link
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Look for links containing "specification" and ending in .pdf
        pdf_links = soup.find_all('a', href=lambda x: x and 'specification' in x.lower() and '.pdf' in x.lower())
        
        if pdf_links:
            # Get the first one (usually the main spec)
            href = pdf_links[0].get('href')
            if href.startswith('/'):
                href = 'https://www.ocr.org.uk' + href
            
            if href != info['pdf_url']:
                print(f"  OLD: {info['pdf_url']}")
                print(f"  NEW: {href}")
                subjects[code]['pdf_url'] = href
                updated += 1
            else:
                print(f"  ✓ URL is correct")
        else:
            print(f"  ⚠ No PDF found")
            failed.append(code)
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
        failed.append(code)

driver.quit()

# Save updated subjects
if updated > 0:
    with open(subjects_file, 'w', encoding='utf-8') as f:
        json.dump(subjects, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Updated {updated} PDF URLs")
else:
    print(f"\n✓ All URLs are correct")

if failed:
    print(f"⚠ Failed to find PDFs for: {', '.join(failed)}")

print("\nDone!")

