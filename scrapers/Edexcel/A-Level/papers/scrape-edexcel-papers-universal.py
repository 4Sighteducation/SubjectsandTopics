"""
Edexcel A-Level - Universal Past Papers Scraper
Works for all Edexcel A-Level subjects

Uses Selenium to expand and scrape exam materials pages

Usage:
    python scrape-edexcel-papers-universal.py <subject_code> <subject_name> <exam_materials_url>
"""

import os
import sys
import time
import re
from pathlib import Path
from collections import Counter

# Setup paths
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'flash-curriculum-pipeline'))

from selenium import webdriver
from selenium.webdriver.common.by import By
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
    
    print("✓ WebDriver initialized")
    return driver


def scrape_papers(subject_code, subject_name, exam_materials_url, headless=True):
    """Scrape papers using Selenium."""
    
    print("=" * 80)
    print("EDEXCEL A-LEVEL - PAPERS SCRAPER")
    print("=" * 80)
    print(f"\nSubject: {subject_name}")
    print(f"Code: {subject_code}")
    print(f"URL: {exam_materials_url}")
    print(f"\nThis will take 2-3 minutes...\n")
    
    driver = None
    papers = []
    
    try:
        driver = init_driver(headless=headless)
        
        print(f"📂 Navigating to Exam Materials page...")
        driver.get(exam_materials_url)
        time.sleep(5)
        
        # Click EXPAND ALL
        print("   Looking for EXPAND ALL button...")
        try:
            expand_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'EXPAND ALL')]")
            if expand_buttons:
                print("   Found EXPAND ALL - clicking...")
                driver.execute_script("arguments[0].click();", expand_buttons[0])
                time.sleep(3)
                print("   ✓ Expanded all sections")
        except:
            print("   No EXPAND ALL found - trying manual expansion...")
        
        # Expand any remaining collapsed sections
        print("   Expanding remaining sections...")
        selectors = ["button[aria-expanded='false']", "summary"]
        expanded = 0
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements[:30]:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                        time.sleep(0.3)
                        driver.execute_script("arguments[0].click();", elem)
                        time.sleep(0.5)
                        expanded += 1
                    except:
                        pass
            except:
                pass
        
        print(f"   ✓ Expanded {expanded} additional sections")
        
        # Scroll to load lazy content
        print("   Scrolling to load content...")
        time.sleep(3)
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        for _ in range(20):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        # Scrape PDF links
        print("\n📥 Scraping PDF links...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        
        print(f"   Found {len(pdf_links)} total PDF links\n")
        
        # Parse each link
        for link in pdf_links:
            href = link.get('href', '')
            text = link.get_text().strip()
            
            # Make absolute
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = 'https://qualifications.pearson.com' + href
            
            # Only this subject's papers
            subject_code_lower = subject_code.lower()
            subject_code_upper = subject_code.upper()
            
            if subject_code_lower not in href.lower() and subject_code_upper not in href:
                continue
            
            filename = href.split('/')[-1]
            
            # Parse filename: 9ch0-01-que-20240524.pdf or 9CH0_01_que_20201008.pdf
            # Pattern: CODE-PAPER-TYPE-DATE or CODE_PAPER_TYPE_DATE
            pattern = rf'{subject_code_lower}[-_](\d+)[-_]([a-z]{{3}})[-_](\d{{8}})'
            match = re.search(pattern, filename, re.IGNORECASE)
            
            if not match:
                continue
            
            paper_num = int(match.group(1))
            doc_type_code = match.group(2).lower()
            date_str = match.group(3)
            
            year = int(date_str[:4])
            month = int(date_str[4:6])
            
            # Series from month
            if month in [5, 6]:
                series = 'June'
            elif month in [10, 11]:
                series = 'October'
            elif month in [1, 2]:
                series = 'January'
            else:
                series = 'June'  # Default
            
            # Doc type
            doc_types = {
                'que': 'Question Paper',
                'rms': 'Mark Scheme',
                'pef': 'Examiner Report',
                'qp': 'Question Paper',
                'ms': 'Mark Scheme',
                'er': 'Examiner Report'
            }
            doc_type = doc_types.get(doc_type_code, 'Question Paper')
            
            papers.append({
                'year': year,
                'exam_series': series,
                'paper_number': paper_num,
                'component_code': f'{paper_num:02d}',
                'tier': None,
                'doc_type': doc_type,
                'url': href
            })
            
            print(f"   ✓ {year} {series} - Paper {paper_num} - {doc_type}")
        
        print(f"\n✓ Found {len(papers)} papers")
        
        # Breakdown
        if papers:
            doc_types_found = Counter(p['doc_type'] for p in papers)
            print("\n   Breakdown:")
            for dt, count in doc_types_found.items():
                print(f"   • {dt}: {count}")
            
            years = Counter(p['year'] for p in papers)
            print(f"\n   Years: {dict(sorted(years.items(), reverse=True))}")
        
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
            print("✓ Browser closed")


def group_papers(papers):
    """Group into sets by year + series + paper number."""
    sets = {}
    
    for paper in papers:
        key = (paper['year'], paper['exam_series'], paper['paper_number'])
        
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
    
    # Force UTF-8 output
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    # Parse arguments
    if len(sys.argv) < 4:
        print("Usage: python scrape-edexcel-papers-universal.py <subject_code> <subject_name> <exam_materials_url>")
        print("\nExample:")
        print('  python scrape-edexcel-papers-universal.py 9CH0 "Chemistry" "https://..."')
        sys.exit(1)
    
    subject_code = sys.argv[1]
    subject_name = sys.argv[2]
    exam_materials_url = sys.argv[3]
    
    papers = scrape_papers(subject_code, subject_name, exam_materials_url, headless=True)
    
    if not papers:
        print("\n⚠️ No papers found!")
        return 0
    
    # Group
    print("\n📦 Grouping into sets...")
    sets = group_papers(papers)
    print(f"   Created {len(sets)} complete paper sets")
    
    # Upload
    print("\n📤 Uploading to database...")
    
    try:
        uploaded = upload_papers_to_staging(
            subject_code=subject_code,
            qualification_type='A-Level',
            papers_data=sets,
            exam_board='Edexcel'
        )
        
        print(f"\n✓ Uploaded {uploaded} paper sets!")
        
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print(f"✅ {subject_name.upper()} PAPERS COMPLETE!")
    print("=" * 80)
    print(f"\nTotal: {len(sets)} paper sets")
    
    return len(sets)


if __name__ == '__main__':
    main()

