"""
Edexcel Design and Technology (9DT0) - Past Papers Scraper (Enhanced)
Uses Selenium with longer waits and explicit filter clicking
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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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


def init_driver(headless=False):
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


def scrape_design_tech_papers():
    SUBJECT = {
        'name': 'Design and Technology - Product Design',
        'code': '9DT0',
        'exam_materials_url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/design-technology-product-design-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    }
    
    print("=" * 80)
    print("EDEXCEL DESIGN AND TECHNOLOGY (9DT0) - PAPERS SCRAPER (ENHANCED)")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}\n")
    
    driver = None
    papers = []
    
    try:
        driver = init_driver(headless=False)  # Visible to debug
        
        print(f"[INFO] Navigating to Exam Materials page...")
        driver.get(SUBJECT['exam_materials_url'])
        
        # Wait for page to load completely
        print("[INFO] Waiting for page to load (15 seconds)...")
        time.sleep(15)
        
        # Try to ensure Exam materials filter is active
        print("[INFO] Looking for Exam materials filter...")
        try:
            exam_filter = driver.find_elements(By.XPATH, "//*[contains(text(), 'Exam materials')]")
            if exam_filter:
                print(f"[INFO] Found {len(exam_filter)} 'Exam materials' elements")
                for elem in exam_filter[:3]:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", elem)
                        print("[OK] Clicked Exam materials filter")
                        time.sleep(8)  # Wait for filter to apply
                    except:
                        pass
        except Exception as e:
            print(f"[WARN] Could not click filter: {e}")
        
        # Wait even longer after filter
        print("[INFO] Waiting for filtered content (10 seconds)...")
        time.sleep(10)
        
        # Click EXPAND ALL
        print("[INFO] Looking for EXPAND ALL button...")
        try:
            expand_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'EXPAND ALL')]")
            if expand_buttons:
                driver.execute_script("arguments[0].click();", expand_buttons[0])
                time.sleep(5)
                print("[OK] Expanded all sections")
        except:
            print("[WARN] No EXPAND ALL found")
        
        # Expand remaining sections
        print("[INFO] Expanding remaining sections...")
        selectors = ["button[aria-expanded='false']", "summary", "details"]
        expanded = 0
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements[:40]:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", elem)
                        time.sleep(0.5)
                        expanded += 1
                    except:
                        pass
            except:
                pass
        print(f"[OK] Expanded {expanded} additional sections")
        
        # Scroll multiple times
        print("[INFO] Scrolling to load all content...")
        for scroll_round in range(3):
            last_height = driver.execute_script("return document.body.scrollHeight")
            for _ in range(15):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(3)
        
        # Save page source for debugging
        debug_path = Path(__file__).parent / "debug-design-tech-page.html"
        debug_path.write_text(driver.page_source, encoding='utf-8')
        print(f"[INFO] Saved page source to: {debug_path.name}")
        
        # Scrape PDF links
        print("\n[INFO] Scraping PDF links...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Try multiple methods
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        print(f"[INFO] Method 1 (.pdf links): Found {len(pdf_links)} links")
        
        # Also look for any 9dt0 links
        dt_links = soup.find_all('a', href=re.compile(r'9dt0', re.IGNORECASE))
        print(f"[INFO] Method 2 (9dt0 links): Found {len(dt_links)} links")
        
        all_links = list(set(pdf_links + dt_links))
        print(f"[INFO] Total unique links to process: {len(all_links)}\n")
        
        for link in all_links:
            href = link.get('href', '')
            
            if not href or '.pdf' not in href.lower():
                continue
            
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = 'https://qualifications.pearson.com' + href
            
            if '9dt0' not in href.lower():
                continue
            
            filename = href.split('/')[-1]
            print(f"   Found: {filename}")
            
            match = re.search(r'9dt0[-_](\d+)[-_]([a-z]{3})[-_](\d{8})', filename, re.IGNORECASE)
            
            if not match:
                print(f"      [WARN] Could not parse filename")
                continue
            
            paper_num = int(match.group(1))
            doc_type_code = match.group(2).lower()
            date_str = match.group(3)
            year = int(date_str[:4])
            month = int(date_str[4:6])
            series = 'June' if month in [5, 6] else 'October' if month in [10, 11] else 'November' if month == 11 else 'January' if month == 1 else 'June'
            
            doc_types = {'que': 'Question Paper', 'rms': 'Mark Scheme', 'pef': 'Examiner Report'}
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
            print(f"      [OK] {year} {series} - Paper {paper_num} - {doc_type}")
        
        print(f"\n[INFO] Found {len(papers)} papers")
        
        if papers:
            doc_types_found = Counter(p['doc_type'] for p in papers)
            print("\nBreakdown:")
            for dt, count in doc_types_found.items():
                print(f"   {dt}: {count}")
            years = Counter(p['year'] for p in papers)
            print(f"\n   Years: {dict(sorted(years.items(), reverse=True))}")
        else:
            print("\n[WARN] No papers found - check debug-design-tech-page.html")
        
        return papers
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if driver:
            print("\n[INFO] Keeping browser open for 10 seconds so you can check...")
            time.sleep(10)
            driver.quit()
            print("[OK] Browser closed")


def group_papers(papers):
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
    papers = scrape_design_tech_papers()
    
    if not papers:
        print("\n[WARN] No papers found - check the debug HTML file")
        return 0
    
    print("\n[INFO] Grouping into sets...")
    sets = group_papers(papers)
    print(f"   Created {len(sets)} paper sets")
    
    print("\n[INFO] Uploading to database...")
    try:
        uploaded = upload_papers_to_staging(
            subject_code='9DT0',
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
    print("[OK] DESIGN AND TECHNOLOGY PAPERS COMPLETE!")
    print("=" * 80)
    print(f"\nTotal: {len(sets)} paper sets")
    
    return len(sets)


if __name__ == '__main__':
    main()

