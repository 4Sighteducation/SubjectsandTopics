"""
Edexcel Economics A (9EC0) - Past Papers Scraper
Uses Selenium - same approach as Business
"""

import os, sys, time, re
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
    if headless: chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    return webdriver.Chrome(options=chrome_options)

SUBJECT = {
    'code': '9EC0',
    'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/economics-a-2015.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
}

print("=" * 80)
print("EDEXCEL ECONOMICS A (9EC0) - PAPERS SCRAPER")
print("=" * 80)

driver = init_driver(headless=True)
papers = []

try:
    driver.get(SUBJECT['url'])
    time.sleep(5)
    
    # EXPAND ALL
    try:
        expand = driver.find_elements(By.XPATH, "//*[contains(text(), 'EXPAND ALL')]")
        if expand:
            driver.execute_script("arguments[0].click();", expand[0])
            time.sleep(3)
    except: pass
    
    # Scroll
    for _ in range(20):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
    
    for link in pdf_links:
        href = link.get('href', '')
        if href.startswith('//'): href = 'https:' + href
        elif href.startswith('/'): href = 'https://qualifications.pearson.com' + href
        
        if '9ec0' not in href.lower(): continue
        
        filename = href.split('/')[-1]
        match = re.search(r'9ec0[-_](\d+)[-_]([a-z]{3})[-_](\d{8})', filename, re.IGNORECASE)
        if not match: continue
        
        paper_num = int(match.group(1))
        doc_type = match.group(2).lower()
        date_str = match.group(3)
        year = int(date_str[:4])
        month = int(date_str[4:6])
        series = 'June' if month in [5,6] else 'October' if month == 10 else 'January'
        
        doc_types = {'que': 'Question Paper', 'rms': 'Mark Scheme', 'pef': 'Examiner Report'}
        
        papers.append({'year': year, 'exam_series': series, 'paper_number': paper_num, 'component_code': f'{paper_num:02d}', 'tier': None, 'doc_type': doc_types.get(doc_type, 'Question Paper'), 'url': href})
        print(f"[OK] {year} {series} - Paper {paper_num} - {doc_types.get(doc_type)}")
    
    print(f"\n[INFO] Found {len(papers)} papers")
    
finally:
    driver.quit()

# Group
sets = {}
for p in papers:
    key = (p['year'], p['exam_series'], p['paper_number'])
    if key not in sets:
        sets[key] = {'year': p['year'], 'exam_series': p['exam_series'], 'paper_number': p['paper_number'], 'component_code': p['component_code'], 'tier': None, 'question_paper_url': None, 'mark_scheme_url': None, 'examiner_report_url': None}
    if p['doc_type'] == 'Question Paper': sets[key]['question_paper_url'] = p['url']
    elif p['doc_type'] == 'Mark Scheme': sets[key]['mark_scheme_url'] = p['url']
    elif p['doc_type'] == 'Examiner Report': sets[key]['examiner_report_url'] = p['url']

sets = list(sets.values())
print(f"[INFO] Grouped into {len(sets)} sets")

# Upload
uploaded = upload_papers_to_staging(subject_code='9EC0', qualification_type='A-Level', papers_data=sets, exam_board='Edexcel')
print(f"[OK] Uploaded {uploaded} paper sets!")
print("=" * 80)

