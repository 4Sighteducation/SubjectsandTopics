"""
Drama Papers - Enhanced Version with Longer Waits
Based on design-tech-papers-selenium-v2.py approach for problematic pages
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
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(15)  # Longer wait
    return driver


def main():
    print("=" * 80)
    print("DRAMA PAPERS - ENHANCED V3 (LONG WAITS)")
    print("=" * 80)
    
    driver = init_driver(headless=True)
    papers = []
    
    try:
        url = 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/drama-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
        
        print("[INFO] Navigating to Drama page...")
        driver.get(url)
        print("[INFO] Waiting 15 seconds for page load...")
        time.sleep(15)  # Much longer initial wait
        
        # Try clicking filter explicitly
        print("[INFO] Looking for exam materials filter...")
        try:
            filter_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Exam materials')]")
            if filter_buttons:
                print("[INFO] Clicking Exam materials filter...")
                driver.execute_script("arguments[0].click();", filter_buttons[0])
                time.sleep(10)  # Wait after filter
        except:
            print("[WARN] No filter button found")
        
        # Expand
        print("[INFO] Looking for EXPAND ALL...")
        try:
            expand = driver.find_elements(By.XPATH, "//*[contains(text(), 'EXPAND ALL')]")
            if expand:
                print("[INFO] Clicking EXPAND ALL...")
                driver.execute_script("arguments[0].click();", expand[0])
                time.sleep(10)  # Long wait after expand
                print("[OK] Expanded")
        except:
            print("[WARN] No EXPAND ALL")
        
        # Multiple scroll rounds
        print("[INFO] Scrolling (multiple rounds)...")
        for round_num in range(3):
            for _ in range(15):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.5)
            time.sleep(3)
            print(f"[INFO] Scroll round {round_num + 1} complete")
        
        # Save debug HTML
        Path('debug-drama-page-v3.html').write_text(driver.page_source, encoding='utf-8')
        print("[OK] Saved debug HTML")
        
        # Scrape
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        
        print(f"[INFO] Found {len(pdf_links)} total PDF links")
        
        for link in pdf_links:
            href = link.get('href', '')
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = 'https://qualifications.pearson.com' + href
            
            if '9dr0' not in href.lower():
                continue
            
            filename = href.split('/')[-1]
            match = re.search(r'9dr0[-_](\d+)[-_]([a-z]{3})[-_](\d{8})', filename, re.IGNORECASE)
            
            if not match:
                continue
            
            paper_num = int(match.group(1))
            doc_type_code = match.group(2).lower()
            date_str = match.group(3)
            
            year = int(date_str[:4])
            month = int(date_str[4:6])
            series = 'June' if month in [5, 6] else 'October' if month == 10 else 'January' if month == 1 else 'June'
            
            doc_types = {'que': 'Question Paper', 'rms': 'Mark Scheme', 'msc': 'Mark Scheme', 'pef': 'Examiner Report'}
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
        
        print(f"[OK] Found {len(papers)} Drama papers")
        
        if papers:
            # Group and upload
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
            
            paper_sets = list(sets.values())
            
            uploaded = upload_papers_to_staging(
                subject_code='9DR0',
                qualification_type='A-Level',
                papers_data=paper_sets,
                exam_board='Edexcel'
            )
            
            print(f"[OK] Uploaded {uploaded} Drama paper sets!")
            return uploaded
        else:
            print("[WARN] No Drama papers found - check debug-drama-page-v3.html")
            print("[INFO] Drama papers may need manual entry via data viewer")
        
    finally:
        driver.quit()
    
    return 0


if __name__ == '__main__':
    main()

