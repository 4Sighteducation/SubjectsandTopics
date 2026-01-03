"""
Quick scraper for the 7 missing GCSE language papers
French, German, Spanish (try 2016 URLs)
Gujarati, Persian, Portuguese, Turkish (try 2017/2018 URLs)
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

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Missing languages
LANGUAGES = [
    ('GCSE-French', 'French', '1fr0', 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/french-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'),
    ('GCSE-German', 'German', '1gn0', 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/german-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'),
    ('GCSE-Spanish', 'Spanish', '1sp0', 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/spanish-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'),
    ('GCSE-Gujarati', 'Gujarati', '1gu0', 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/gujarati-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'),
    ('GCSE-Persian', 'Persian', '1pn0', 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/persian-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'),
    ('GCSE-Portuguese', 'Portuguese', '1pg0', 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/portuguese-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'),
    ('GCSE-Turkish', 'Turkish', '1tu0', 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/turkish-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'),
]

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver

def scrape_and_upload(code, name, paper_code, url, driver):
    print(f"\n{'=' * 80}")
    print(f"{name} ({code}) - Papers: {paper_code.upper()}")
    print(f"{'=' * 80}")
    
    papers = []
    try:
        driver.get(url)
        time.sleep(4)
        
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
        
        for link in pdf_links:
            href = link.get('href', '')
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = 'https://qualifications.pearson.com' + href
            
            if paper_code not in href.lower():
                continue
            
            filename = href.split('/')[-1]
            match = re.search(rf'{paper_code}[-_](\d+)([fh])[-_]([a-z]{{3}})[-_](\d{{8}})', filename, re.IGNORECASE)
            
            if not match:
                continue
            
            paper_num = int(match.group(1))
            tier = match.group(2).upper()
            doc_type_code = match.group(3).lower()
            date_str = match.group(4)
            
            year = int(date_str[:4])
            month = int(date_str[4:6])
            series = 'June' if month in [5, 6] else 'November' if month == 11 else 'January' if month == 1 else 'June'
            
            doc_types = {'que': 'Question Paper', 'rms': 'Mark Scheme', 'msc': 'Mark Scheme', 'pef': 'Examiner Report'}
            doc_type = doc_types.get(doc_type_code, 'Question Paper')
            
            papers.append({
                'year': year,
                'exam_series': series,
                'paper_number': paper_num,
                'component_code': f'{paper_num:02d}',
                'tier': tier,
                'doc_type': doc_type,
                'url': href
            })
        
        print(f"[OK] Found {len(papers)} papers")
        
        if papers:
            sets = {}
            for paper in papers:
                key = (paper['year'], paper['exam_series'], paper['paper_number'], paper['tier'])
                if key not in sets:
                    sets[key] = {
                        'year': paper['year'],
                        'exam_series': paper['exam_series'],
                        'paper_number': paper['paper_number'],
                        'component_code': paper['component_code'],
                        'tier': paper['tier'],
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
                subject_code=code,
                qualification_type='GCSE',
                papers_data=paper_sets,
                exam_board='Edexcel'
            )
            
            print(f"[OK] Uploaded {uploaded} sets!")
            return uploaded
        else:
            print(f"[WARN] No papers")
            return 0
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return 0

def main():
    print("=" * 80)
    print("GCSE MISSING LANGUAGES - PAPER SCRAPER")
    print("=" * 80)
    print("Trying 2016/2018 URLs for the 7 missing languages\n")
    
    driver = init_driver()
    results = {}
    
    try:
        for code, name, paper_code, url in LANGUAGES:
            result = scrape_and_upload(code, name, paper_code, url, driver)
            results[name] = result
    finally:
        driver.quit()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total = sum(results.values())
    for name, count in results.items():
        status = "✅" if count > 0 else "❌"
        print(f"   {status} {name}: {count} sets")
    print(f"\n   TOTAL: {total} additional paper sets!")
    print("=" * 80)

if __name__ == '__main__':
    main()

