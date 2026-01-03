"""
Edexcel Physical Education (9PE1) - Past Papers Scraper
Uses Selenium to scrape actual links from Edexcel coursematerials page
"""

import os
import sys
import time
import re
from pathlib import Path
from collections import Counter

project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'flash-curriculum-pipeline'))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from dotenv import load_dotenv

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

import importlib.util
upload_helper_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\upload_papers_to_staging.py")
spec = importlib.util.spec_from_file_location("upload_papers_to_staging", upload_helper_path)
upload_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload_module)
upload_papers_to_staging = upload_module.upload_papers_to_staging


def init_driver(headless=True):
    """Initialize Chrome WebDriver."""
    print("[INFO] Initializing Chrome WebDriver...")
    
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
    
    print("[OK] WebDriver initialized")
    return driver


def scrape_pe_papers():
    """Scrape Physical Education papers using Selenium."""
    
    SUBJECT = {
        'name': 'Physical Education',
        'code': '9PE1',
        'qualification': 'A-Level',
        'exam_board': 'Edexcel',
        'exam_materials_url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/physical-education-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    }
    
    print("=" * 80)
    print("EDEXCEL PHYSICAL EDUCATION (9PE1) - PAPERS SCRAPER (SELENIUM)")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"\nThis will take 2-3 minutes...\n")
    
    driver = None
    papers = []
    
    try:
        driver = init_driver(headless=True)
        
        print(f"[INFO] Navigating to Exam Materials page...")
        driver.get(SUBJECT['exam_materials_url'])
        time.sleep(5)
        
        # Click EXPAND ALL
        print("[INFO] Looking for EXPAND ALL button...")
        try:
            expand_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'EXPAND ALL')]")
            if expand_buttons:
                print("[INFO] Found EXPAND ALL - clicking...")
                driver.execute_script("arguments[0].click();", expand_buttons[0])
                time.sleep(3)
                print("[OK] Expanded all sections")
        except:
            print("[WARN] No EXPAND ALL found - trying manual expansion...")
        
        # Expand any remaining collapsed sections
        print("[INFO] Expanding remaining sections...")
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
        
        print(f"[OK] Expanded {expanded} additional sections")
        
        # Scroll to load lazy content
        print("[INFO] Scrolling to load content...")
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
        print("\n[INFO] Scraping PDF links...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        
        print(f"[INFO] Found {len(pdf_links)} PDF links\n")
        
        # Parse each link
        for link in pdf_links:
            href = link.get('href', '')
            text = link.get_text().strip()
            
            # Make absolute
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = 'https://qualifications.pearson.com' + href
            
            # Only PE papers (9pe1)
            if '9pe1' not in href.lower():
                continue
            
            filename = href.split('/')[-1]
            
            # Parse filename: 9pe1-01-que-20240524.pdf
            match = re.search(r'9pe1[-_](\d+)[-_]([a-z]{3})[-_](\d{8})', filename, re.IGNORECASE)
            
            if not match:
                continue
            
            paper_num = int(match.group(1))
            doc_type_code = match.group(2).lower()
            date_str = match.group(3)
            
            year = int(date_str[:4])
            month = int(date_str[4:6])
            
            # Series from month
            series = 'June' if month in [5, 6] else 'October' if month == 10 else 'January' if month == 1 else 'June'
            
            # Doc type
            doc_types = {
                'que': 'Question Paper',
                'rms': 'Mark Scheme',
                'pef': 'Examiner Report'
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
            
            print(f"[OK] {year} {series} - Paper {paper_num} - {doc_type}")
        
        print(f"\n[INFO] Found {len(papers)} papers")
        
        # Breakdown
        if papers:
            doc_types_found = Counter(p['doc_type'] for p in papers)
            print("\nBreakdown:")
            for dt, count in doc_types_found.items():
                print(f"   {dt}: {count}")
            
            years = Counter(p['year'] for p in papers)
            print(f"\n   Years: {dict(sorted(years.items(), reverse=True))}")
        
        return papers
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return []
        
    finally:
        if driver:
            print("\n[INFO] Closing browser...")
            driver.quit()
            print("[OK] Browser closed")


def group_papers(papers):
    """Group into sets."""
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
    
    papers = scrape_pe_papers()
    
    if not papers:
        print("\n[WARN] No papers found!")
        return 0
    
    # Group
    print("\n[INFO] Grouping into sets...")
    sets = group_papers(papers)
    print(f"   Created {len(sets)} paper sets")
    
    # Upload
    print("\n[INFO] Uploading to database...")
    
    try:
        uploaded = upload_papers_to_staging(
            subject_code='9PE1',
            qualification_type='A-Level',
            papers_data=sets,
            exam_board='Edexcel'
        )
        
        print(f"\n[OK] Uploaded {uploaded} paper sets!")
        
    except Exception as e:
        print(f"\n[ERROR] Upload failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("[OK] PHYSICAL EDUCATION PAPERS COMPLETE!")
    print("=" * 80)
    print(f"\nTotal: {len(sets)} paper sets")
    
    return len(sets)


if __name__ == '__main__':
    main()










