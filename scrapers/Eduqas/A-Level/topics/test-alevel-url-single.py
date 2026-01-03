"""
Quick test script to find PDF URL for a single A-Level subject.
Usage: python test-alevel-url-single.py "Biology"
"""

import sys
import importlib.util
from pathlib import Path

# Import the PDF URL scraper module
pdf_url_scraper_path = Path(__file__).parent / "eduqas-pdf-url-scraper.py"
spec = importlib.util.spec_from_file_location("eduqas_pdf_url_scraper", pdf_url_scraper_path)
eduqas_pdf_url_scraper_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eduqas_pdf_url_scraper_module)
EduqasPDFURLScraper = eduqas_pdf_url_scraper_module.EduqasPDFURLScraper

if len(sys.argv) < 2:
    print("Usage: python test-alevel-url-single.py \"Subject Name\"")
    print("\nAvailable A-Level subjects:")
    print("  Biology, Chemistry, Economics, Geography, Law, Physics, Psychology")
    print("  English Language and Literature")
    print("\nExample: python test-alevel-url-single.py \"Biology\"")
    sys.exit(1)

subject_name = sys.argv[1]

print("="*60)
print(f"Testing PDF URL Finder for A-Level: {subject_name}")
print("="*60)
print()

# Initialize scraper (visible browser so you can see what's happening)
scraper = EduqasPDFURLScraper(headless=False)

try:
    print(f"[STEP 1] Finding subject page URL for {subject_name} (A-Level)...")
    subject_page_url = scraper.find_subject_page_url(subject_name, 'A-Level')
    
    if not subject_page_url:
        print(f"\n[ERROR] Could not find subject page for {subject_name}")
        print("Possible reasons:")
        print("  - Subject name doesn't match Eduqas website")
        print("  - Website structure changed")
        print("  - Check the browser window for errors")
        sys.exit(1)
    
    print(f"[OK] Found subject page: {subject_page_url}")
    print()
    
    print(f"[STEP 2] Finding PDF URL from subject page...")
    pdf_url = scraper.find_pdf_url_from_subject_page(subject_page_url, subject_name, 'A-Level')
    
    if not pdf_url:
        print(f"\n[ERROR] Could not find PDF URL on subject page")
        print("Possible reasons:")
        print("  - PDF link not found on page")
        print("  - Need to click a tab/section first")
        print("  - Check the browser window to see the page")
        sys.exit(1)
    
    print(f"[OK] Found PDF URL: {pdf_url}")
    print()
    print("="*60)
    print("SUCCESS!")
    print("="*60)
    print(f"Subject: {subject_name}")
    print(f"Subject Page: {subject_page_url}")
    print(f"PDF URL: {pdf_url}")
    print()
    print("You can now use this URL in the universal scraper!")
    
except Exception as e:
    print(f"\n[ERROR] Exception occurred: {e}")
    import traceback
    traceback.print_exc()
finally:
    scraper._close_driver()

