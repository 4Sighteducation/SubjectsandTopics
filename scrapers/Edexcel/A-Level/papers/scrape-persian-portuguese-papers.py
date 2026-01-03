"""
Quick scraper for Persian and Portuguese papers with correct paper codes
Persian: 9PE0 subject → 9PN0 papers
Portuguese: 9PT0 subject → 9PG0 papers
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
    driver.implicitly_wait(10)
    return driver


def scrape_and_upload(subject_code, subject_name, url, paper_code):
    """Scrape and upload papers for one language."""
    
    print("=" * 80)
    print(f"{subject_name} ({subject_code}) - Papers use code {paper_code.upper()}")
    print("=" * 80)
    
    driver = init_driver(headless=True)
    papers = []
    
    try:
        driver.get(url)
        time.sleep(5)
        
        # Expand and scroll
        try:
            expand = driver.find_elements(By.XPATH, "//*[contains(text(), 'EXPAND ALL')]")
            if expand:
                driver.execute_script("arguments[0].click();", expand[0])
                time.sleep(3)
        except:
            pass
        
        for _ in range(15):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.4)
        
        # Scrape
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        
        print(f"[INFO] Found {len(pdf_links)} PDF links")
        
        for link in pdf_links:
            href = link.get('href', '')
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = 'https://qualifications.pearson.com' + href
            
            if paper_code not in href.lower():
                continue
            
            filename = href.split('/')[-1]
            match = re.search(rf'{paper_code}[-_](\d+)[-_]([a-z]{{3}})[-_](\d{{8}})', filename, re.IGNORECASE)
            
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
        
        print(f"[OK] Found {len(papers)} papers")
        
        if papers:
            # Group
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
            print(f"[INFO] Created {len(paper_sets)} sets")
            
            # Upload
            uploaded = upload_papers_to_staging(
                subject_code=subject_code,
                qualification_type='A-Level',
                papers_data=paper_sets,
                exam_board='Edexcel'
            )
            
            print(f"[OK] Uploaded {uploaded} sets!")
            
            years = Counter(p['year'] for p in papers)
            print(f"[INFO] Years: {min(years.keys())}-{max(years.keys())}\n")
            
            return uploaded
        
    finally:
        driver.quit()
    
    return 0


def main():
    print("\n" + "=" * 80)
    print("PERSIAN & PORTUGUESE PAPERS - CODE MISMATCH FIX")
    print("=" * 80 + "\n")
    
    # Persian
    persian_sets = scrape_and_upload(
        '9PE0', 'Persian',
        'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/persian-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        '9pn0'
    )
    
    # Portuguese
    portuguese_sets = scrape_and_upload(
        '9PT0', 'Portuguese',
        'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/portuguese-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        '9pg0'
    )
    
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Persian: {persian_sets} sets")
    print(f"Portuguese: {portuguese_sets} sets")
    print(f"TOTAL: {persian_sets + portuguese_sets} sets")
    print("=" * 80)


if __name__ == '__main__':
    main()

