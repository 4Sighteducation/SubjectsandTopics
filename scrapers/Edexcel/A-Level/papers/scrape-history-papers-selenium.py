"""
Edexcel History A-Level - Past Papers Scraper (Selenium)
Code: 9HI0

Uses Selenium to properly load Pearson's dynamic page and extract all PDFs
"""

import os
import sys
import time
import re
from pathlib import Path
from collections import Counter

# Add parent directories to path
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'flash-curriculum-pipeline'))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

# Import upload helper
import importlib.util
upload_helper_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\upload_papers_to_staging.py")
spec = importlib.util.spec_from_file_location("upload_papers_to_staging", upload_helper_path)
upload_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload_module)
upload_papers_to_staging = upload_module.upload_papers_to_staging


def init_driver(headless=True):
    """Initialize Chrome WebDriver."""
    print("🌐 Initializing Chrome WebDriver...")
    
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    
    print("✅ WebDriver initialized")
    return driver


def scrape_edexcel_history_papers():
    """
    Scrape all available History papers from Pearson's Exam Materials page.
    Uses Selenium to handle dynamic content.
    """
    
    SUBJECT = {
        'name': 'History',
        'code': '9HI0',
        'qualification': 'A-Level',
        'exam_board': 'Edexcel',
        'exam_materials_url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/history-2015.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    }
    
    print("=" * 60)
    print("EDEXCEL HISTORY - SELENIUM SCRAPER")
    print("=" * 60)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Board: {SUBJECT['exam_board']}")
    print(f"\nThis will take 3-5 minutes...\n")
    
    driver = None
    papers = []
    
    try:
        driver = init_driver(headless=False)
        
        # Navigate to exam materials page
        print(f"🔍 Navigating to Exam Materials page...")
        driver.get(SUBJECT['exam_materials_url'])
        time.sleep(5)
        
        # Wait for page to fully load
        print("   Waiting for content to load...")
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except:
            pass
        
        # Click "EXPAND ALL" button if it exists
        print("   Looking for EXPAND ALL button...")
        try:
            expand_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'EXPAND ALL')]")
            if expand_buttons:
                print("   Found EXPAND ALL button - clicking...")
                driver.execute_script("arguments[0].click();", expand_buttons[0])
                time.sleep(3)
                print("   ✅ Clicked EXPAND ALL")
        except Exception as e:
            print(f"   No EXPAND ALL button found")
        
        # Try to find and expand year sections
        print("   Expanding year sections...")
        
        # Try different selectors for expandable elements
        selectors_to_try = [
            "button[aria-expanded='false']",
            "[role='button'][aria-expanded='false']",
            ".accordion-header",
            "h3[role='button']",
            "summary"  # For <details> tags
        ]
        
        expanded_count = 0
        for selector in selectors_to_try:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"   Found {len(elements)} elements with selector: {selector}")
                
                for elem in elements[:30]:  # Limit to avoid infinite loops
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                        time.sleep(0.3)
                        driver.execute_script("arguments[0].click();", elem)
                        time.sleep(0.5)
                        expanded_count += 1
                    except:
                        pass
            except:
                pass
        
        print(f"   ✅ Attempted to expand {expanded_count} sections")
        
        # Wait for PDFs to load
        time.sleep(5)
        
        # Scroll entire page to trigger lazy loading
        print("   Scrolling to load lazy content...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        for _ in range(20):  # Scroll multiple times
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        # Now scrape all PDF links
        print("\n📄 Scraping PDF links from page...")
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find all PDF links
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        
        print(f"   Found {len(pdf_links)} PDF links\n")
        
        # Parse each PDF link
        for link in pdf_links:
            href = link.get('href', '')
            text = link.get_text().strip()
            
            # Make absolute URL
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = 'https://qualifications.pearson.com' + href
            
            # Only process 9HI0 History papers
            if '9hi0' not in href.lower() and '9HI0' not in href:
                continue
            
            filename = href.split('/')[-1]
            
            # Parse filename - handle both formats:
            # 9hi0-1a-que-20240524.pdf (lowercase, hyphens)
            # 9HI0_1G_que_20201008.pdf (uppercase, underscores)
            
            match = re.search(r'9[Hh][Ii]0[-_]([^-_]+)[-_]([a-z]{3})[-_](\d{8})', filename, re.IGNORECASE)
            
            if not match:
                continue
            
            component_code = match.group(1).upper().replace('-', '.')  # "1A", "2B.1", "30"
            doc_type_code = match.group(2).lower()
            date_str = match.group(3)
            
            year = int(date_str[:4])
            month = int(date_str[4:6])
            
            # Determine series from month
            if month in [5, 6]:
                series = 'June'
            elif month in [10, 11]:
                series = 'October'  # COVID
            elif month in [1]:
                series = 'January'
            else:
                series = 'June'
            
            # Map doc type
            doc_type_map = {
                'que': 'Question Paper',
                'rms': 'Mark Scheme',
                'pef': 'Examiner Report',
                'ms': 'Mark Scheme',
                'er': 'Examiner Report'
            }
            
            doc_type = doc_type_map.get(doc_type_code, 'Question Paper')
            
            # Paper number
            if component_code[0] == '1':
                paper_number = 1
            elif component_code[0] == '2':
                paper_number = 2
            else:
                paper_number = 3
            
            papers.append({
                'year': year,
                'exam_series': series,
                'paper_number': paper_number,
                'component_code': component_code,
                'tier': None,
                'doc_type': doc_type,
                'url': href,
                'filename': filename
            })
            
            print(f"   ✓ {year} {series} - {doc_type} - {component_code}")
        
        print(f"\n✅ Found {len(papers)} papers")
        
        # Breakdown
        print("\n📊 Breakdown:")
        doc_types = Counter(p['doc_type'] for p in papers)
        for dt, count in doc_types.items():
            print(f"   {dt}: {count}")
        
        years_found = Counter(p['year'] for p in papers)
        print(f"\n   Years: {dict(sorted(years_found.items(), reverse=True))}")
        
        components_found = len(set(p['component_code'] for p in papers))
        print(f"\n   Components: {components_found} unique")
        
        return papers
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []
        
    finally:
        if driver:
            print("\n🔒 Closing browser...")
            driver.quit()
            print("✅ Browser closed")


def group_papers(papers):
    """Group papers into complete sets."""
    sets = {}
    
    for paper in papers:
        key = (paper['year'], paper['exam_series'], paper['component_code'])
        
        if key not in sets:
            sets[key] = {
                'year': paper['year'],
                'exam_series': paper['exam_series'],
                'paper_number': paper['paper_number'],
                'component_code': paper['component_code'],
                'tier': None,
                'question_paper_url': None,
                'mark_scheme_url': None,
                'examiner_report_url': None
            }
        
        if paper['doc_type'] == 'Question Paper':
            sets[key]['question_paper_url'] = paper['url']
        elif paper['doc_type'] == 'Mark Scheme':
            sets[key]['mark_scheme_url'] = paper['url']
        elif paper['doc_type'] == 'Examiner Report':
            sets[key]['examiner_report_url'] = paper['url']
    
    return list(sets.values())


def main():
    """Main execution."""
    
    papers = scrape_edexcel_history_papers()
    
    if not papers:
        print("\n⚠️  No papers found!")
        return 0
    
    # Group
    print("\n🔗 Grouping into complete sets...")
    paper_sets = group_papers(papers)
    print(f"   Created {len(paper_sets)} complete paper sets")
    
    # Upload
    print("\n💾 Uploading to database...")
    
    try:
        uploaded = upload_papers_to_staging(
            subject_code='9HI0',
            qualification_type='A-Level',
            papers_data=paper_sets,
            exam_board='Edexcel'
        )
        
        print(f"\n✅ Uploaded {uploaded} paper sets!")
        
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("COMPLETE!")
    print("=" * 60)
    print(f"\nEdexcel History: {len(paper_sets)} paper sets")
    
    return len(paper_sets)


if __name__ == '__main__':
    main()

