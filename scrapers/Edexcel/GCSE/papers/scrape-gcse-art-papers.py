"""
GCSE Art and Design Papers Scraper
Code: Likely 1AD0 for GCSE
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

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver

print("=" * 80)
print("GCSE ART AND DESIGN - PAPER SCRAPER")
print("=" * 80)

driver = init_driver()

try:
    url = 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/art-and-design-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    driver.get(url)
    time.sleep(5)
    
    # Expand and scroll
    from selenium.webdriver.common.by import By
    try:
        expand = driver.find_elements(By.XPATH, "//*[contains(text(), 'EXPAND ALL')]")
        if expand:
            driver.execute_script("arguments[0].click();", expand[0])
            time.sleep(2)
    except:
        pass
    
    for _ in range(15):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.3)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
    
    print(f"[INFO] Found {len(pdf_links)} total PDFs")
    
    # Art papers use format: p73255-gcse-art-design-1ad0-02.pdf
    papers = []
    
    for link in pdf_links:
        href = link.get('href', '')
        if href.startswith('//'):
            href = 'https:' + href
        elif href.startswith('/'):
            href = 'https://qualifications.pearson.com' + href
        
        filename = href.split('/')[-1].lower()
        
        # Check for art code
        if '1ad0' not in filename and 'art' not in filename:
            continue
        
        # Try to parse: p73255-gcse-art-design-1ad0-02.pdf or standard format
        # Pattern 1: Standard format with date
        match = re.search(r'1ad0[-_](\d+)[-_]([a-z]{3})[-_](\d{8})', filename)
        
        # Pattern 2: Art-specific format (p73255-gcse-art-design-1ad0-02)
        if not match:
            match = re.search(r'1ad0[-_](\d+)', filename)
            if match:
                # No date in filename, just paper number
                paper_num = int(match.group(1))
                # Use current year as placeholder
                papers.append({
                    'year': 2024,
                    'exam_series': 'June',
                    'paper_number': paper_num,
                    'component_code': f'{paper_num:02d}',
                    'tier': None,
                    'doc_type': 'Examiner Report',  # These seem to be reports
                    'url': href
                })
                print(f"[OK] Paper {paper_num} (legacy format)")
                continue
        
        if match:
            paper_num_str = match.group(1)
            doc_type_code = match.group(2) if len(match.groups()) >= 2 else 'pef'
            date_str = match.group(3) if len(match.groups()) >= 3 else '20240601'
            
            paper_num = int(paper_num_str)
            year = int(date_str[:4])
            month = int(date_str[4:6])
            series = 'June' if month in [5, 6] else 'November' if month == 11 else 'June'
            
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
            print(f"[OK] {year} {series} - Paper {paper_num} - {doc_type}")
    
    print(f"\n[INFO] Found {len(papers)} Art papers")
    
    if papers:
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
            subject_code='GCSE-Art',
            qualification_type='GCSE',
            papers_data=paper_sets,
            exam_board='Edexcel'
        )
        
        print(f"\n[OK] Uploaded {uploaded} paper sets!")
    else:
        print("[WARN] No papers found")
        
finally:
    driver.quit()

print("\n" + "=" * 80)
print("[OK] GCSE ART AND DESIGN PAPERS COMPLETE!")
print("=" * 80)

