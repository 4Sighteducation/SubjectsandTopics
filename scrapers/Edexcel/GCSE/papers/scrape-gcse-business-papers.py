"""
GCSE Business - Papers Scraper
Scrapes exam papers for GCSE Business (1BS0)

Paper codes:
- Paper 1: 1BS0/01 (Theme 1: Investigating small business)
- Paper 2: 1BS0/02 (Theme 2: Building a business)
"""

import os
import sys
import time
import re
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

import importlib.util
upload_helper_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\upload_papers_to_staging.py")
spec = importlib.util.spec_from_file_location("upload_papers_to_staging", upload_helper_path)
upload_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload_module)
upload_papers_to_staging = upload_module.upload_papers_to_staging

SUBJECT = {
    'code': 'GCSE-Business',
    'name': 'Business',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel'
}


def init_driver(headless=True):
    """Initialize Chrome WebDriver."""
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


def main():
    """Scrape GCSE Business papers."""
    
    print("=" * 80)
    print("GCSE BUSINESS (1BS0) - PAPERS SCRAPER")
    print("=" * 80)
    print("Paper 1: 1BS0/01 - Theme 1: Investigating small business")
    print("Paper 2: 1BS0/02 - Theme 2: Building a business\n")
    
    driver = None
    papers = []
    
    try:
        driver = init_driver(headless=True)
        
        url = 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/business-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
        
        print("[INFO] Navigating to Business GCSE page...")
        driver.get(url)
        time.sleep(5)
        
        # Expand sections
        print("[INFO] Expanding sections...")
        try:
            expand = driver.find_elements(By.XPATH, "//*[contains(text(), 'EXPAND ALL')]")
            if expand:
                driver.execute_script("arguments[0].click();", expand[0])
                time.sleep(3)
        except:
            pass
        
        # Scroll to load all content
        print("[INFO] Scrolling...")
        for _ in range(20):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.4)
        
        time.sleep(2)
        
        # Scrape PDF links
        print("[INFO] Scraping PDF links...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        
        print(f"[INFO] Found {len(pdf_links)} total PDF links\n")
        
        for link in pdf_links:
            href = link.get('href', '')
            
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = 'https://qualifications.pearson.com' + href
            
            # Only process Business papers (1BS0)
            if '1bs0' not in href.lower():
                continue
            
            filename = href.split('/')[-1]
            parts = filename.lower().replace('.pdf', '').split('_')
            
            if len(parts) >= 3:
                paper_num = parts[1]
                doc_type = parts[2]
                date_str = parts[3] if len(parts) > 3 else 'unknown'
                
                # Determine paper title
                if paper_num == '01':
                    paper_title = 'Paper 1: Investigating small business'
                elif paper_num == '02':
                    paper_title = 'Paper 2: Building a business'
                else:
                    paper_title = f'Paper {paper_num}'
                
                # Determine document type
                if 'que' in doc_type or 'qp' in doc_type:
                    doc_name = 'Question Paper'
                elif 'ms' in doc_type or 'mark' in doc_type:
                    doc_name = 'Mark Scheme'
                elif 'er' in doc_type or 'report' in doc_type:
                    doc_name = "Examiner's Report"
                else:
                    doc_name = doc_type.upper()
                
                # Parse date
                if len(date_str) == 8:
                    year = date_str[0:4]
                    month = date_str[4:6]
                    # Determine exam series from month
                    if month in ['05', '06']:
                        exam_series = 'May/June'
                    elif month in ['10', '11']:
                        exam_series = 'October/November'
                    elif month in ['01', '02']:
                        exam_series = 'January/February'
                    else:
                        exam_series = month
                else:
                    year = 'unknown'
                    exam_series = date_str
                
                papers.append({
                    'paper_number': paper_num,
                    'paper_title': paper_title,
                    'doc_type': doc_name,  # Changed from document_type
                    'year': year,
                    'exam_series': exam_series,
                    'url': href,
                    'filename': filename
                })
                
                print(f"  [{doc_name:20s}] Paper {paper_num} | {year} {exam_series} | {filename}")
        
        print(f"\n[OK] Found {len(papers)} Business papers")
        
        # Group papers into sets (Question Paper + Mark Scheme + Examiner Report)
        if papers:
            sets = {}
            for paper in papers:
                key = (paper['year'], paper['exam_series'], paper['paper_number'])
                if key not in sets:
                    sets[key] = {
                        'year': paper['year'],
                        'exam_series': paper['exam_series'],
                        'paper_number': int(paper['paper_number']),
                        'component_code': f"{int(paper['paper_number']):02d}",
                        'tier': None,
                        'question_paper_url': None,
                        'mark_scheme_url': None,
                        'examiner_report_url': None
                    }
                
                if paper['doc_type'] == 'Question Paper':
                    sets[key]['question_paper_url'] = paper['url']
                elif paper['doc_type'] == 'Mark Scheme':
                    sets[key]['mark_scheme_url'] = paper['url']
                elif paper['doc_type'] == "Examiner's Report":
                    sets[key]['examiner_report_url'] = paper['url']
            
            paper_sets = list(sets.values())
            
            print(f"\n[INFO] Grouped into {len(paper_sets)} paper sets")
            print("[INFO] Uploading to database...")
            
            uploaded = upload_papers_to_staging(
                subject_code=SUBJECT['code'],
                qualification_type='GCSE',
                papers_data=paper_sets,
                exam_board='Edexcel'
            )
            
            print(f"\n[OK] Uploaded {uploaded} paper sets!")
            
            print("\n" + "=" * 80)
            print("[SUCCESS] GCSE BUSINESS PAPERS UPLOADED!")
            print("=" * 80)
            print(f"   Total: {len(paper_sets)} paper sets")
            print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            driver.quit()


if __name__ == '__main__':
    main()
