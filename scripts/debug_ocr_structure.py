#!/usr/bin/env python
"""
Debug OCR website structure to understand how to extract content.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from bs4 import BeautifulSoup

def analyze_page(url):
    """Analyze OCR page structure."""
    print(f"\n{'='*80}")
    print(f"Analyzing: {url}")
    print('='*80)
    
    response = requests.get(url, timeout=30)
    soup = BeautifulSoup(response.content, 'lxml')
    
    # Find all navigation/menu structures
    print("\n1. NAVIGATION MENUS:")
    navs = soup.find_all(['nav', 'ul'], class_=True)
    for i, nav in enumerate(navs[:5]):
        print(f"\n  Menu {i+1}: {nav.get('class')}")
        links = nav.find_all('a', href=True)[:10]
        for link in links:
            print(f"    - {link.get_text().strip()[:60]}")
    
    # Find all headings
    print("\n2. MAIN HEADINGS:")
    for h in soup.find_all(['h1', 'h2', 'h3'], limit=15):
        print(f"  {h.name.upper()}: {h.get_text().strip()}")
    
    # Find links with "unit" or "content" in them
    print("\n3. UNIT/CONTENT LINKS:")
    all_links = soup.find_all('a', href=True)
    unit_links = [l for l in all_links if any(kw in l.get('href', '').lower() for kw in ['unit', 'content', 'module', 'topic'])]
    
    for link in unit_links[:15]:
        print(f"  - {link.get_text().strip()[:50]} → {link.get('href')}")
    
    # Look for tables
    print("\n4. TABLES:")
    tables = soup.find_all('table', limit=3)
    print(f"  Found {len(tables)} tables")
    
    # Look for specific OCR patterns
    print("\n5. SEARCHING FOR 'Y' CODES (Y100, Y101, etc.):")
    y_codes = soup.find_all(string=lambda t: t and ('Y1' in t or 'Y2' in t or 'Y3' in t))
    for code in y_codes[:10]:
        print(f"  - {code.strip()[:80]}")

# Test with OCR History
url1 = "https://www.ocr.org.uk/qualifications/as-and-a-level/history-a-h105-h505-from-2015/"
url2 = "https://www.ocr.org.uk/qualifications/as-and-a-level/history-a-h105-h505-from-2015/specification-at-a-glance/"

analyze_page(url1)
analyze_page(url2)

print("\n" + "="*80)
print("Analysis complete! Use findings to adapt OCR scraper.")
print("="*80)
