"""
GCSE Biblical Hebrew Papers Scraper
Code: 1BH0
"""

import os
import sys
import time
import re
from pathlib import Path

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
print("GCSE BIBLICAL HEBREW - PAPER SCRAPER")
print("=" * 80)
print("Code: 1BH0\n")

driver = init_driver()
papers = []

try:
    url = 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/biblical-hebrew-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    driver.get(url)
    time.sleep(5)
    
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
    
    for link in pdf_links:
        href = link.get('href', '')
        if href.startswith('//'):
            href = 'https:' + href
        elif href.startswith('/'):
            href = 'https://qualifications.pearson.com' + href
        
        if '1bh0' not in href.lower():
            continue
        
        filename = href.split('/')[-1]
        
        # Parse: 1BH0_01_que_20201112.pdf (uses underscores)
        match = re.search(r'1bh0[-_](\d+)[-_]([a-z]{3})[-_](\d{8})', filename, re.IGNORECASE)
        
        if not match:
            continue
        
        paper_num = int(match.group(1))
        doc_type_code = match.group(2).lower()
        date_str = match.group(3)
        
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
    
    print(f"\n[INFO] Found {len(papers)} Biblical Hebrew papers")
    
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
            subject_code='GCSE-BiblicalHebrew',
            qualification_type='GCSE',
            papers_data=paper_sets,
            exam_board='Edexcel'
        )
        
        print(f"\n[OK] Uploaded {uploaded} paper sets!")
    
finally:
    driver.quit()

print("\n" + "=" * 80)
print("[OK] BIBLICAL HEBREW PAPERS COMPLETE!")
print("=" * 80)

