"""
GCSE Computer Science - Papers Scraper (FIXED)
==============================================

Properly groups Question Papers, Mark Schemes, and Examiner Reports
into the same year/session profile.

Example URL: https://qualifications.pearson.com/content/dam/pdf/GCSE/Computer-science/2020/Exam-materials/1cp2-01-que-20220517.pdf
Pattern: {code}-{paper}-{type}-{date}.pdf
"""

import os
import sys
import time
import re
from pathlib import Path
from collections import defaultdict
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
    'code': 'GCSE-ComputerScience',
    'name': 'Computer Science',
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


def parse_pdf_filename(filename, href):
    """
    Parse Edexcel PDF filename to extract metadata.
    
    Pattern: 1cp2-01-que-20220517.pdf
    - 1cp2 = subject code
    - 01 = paper number
    - que/ms/er = document type
    - 20220517 = date (YYYYMMDD)
    """
    filename_clean = filename.lower().replace('.pdf', '')
    parts = filename_clean.split('-')
    
    if len(parts) < 4:
        return None
    
    code = parts[0]  # e.g., 1cp2
    paper_num = parts[1]  # e.g., 01
    doc_type_code = parts[2]  # e.g., que, ms, er
    date_str = parts[3] if len(parts) > 3 else ''
    
    # Only process 1CP2 (Computer Science)
    if code != '1cp2':
        return None
    
    # Only accept valid paper numbers (01, 02)
    # Filter out grade boundaries, guidance docs, etc.
    if paper_num not in ['01', '02']:
        return None
    
    # Determine paper title
    if paper_num == '01':
        paper_title = 'Paper 1: Principles of Computer Science'
    elif paper_num == '02':
        paper_title = 'Paper 2: Application of Computational Thinking'
    else:
        paper_title = f'Paper {paper_num}'
    
    # Determine document type
    if 'que' in doc_type_code or 'qp' in doc_type_code:
        doc_type = 'question_paper'
        doc_name = 'Question Paper'
    elif 'ms' in doc_type_code or 'mark' in doc_type_code:
        doc_type = 'mark_scheme'
        doc_name = 'Mark Scheme'
    elif 'er' in doc_type_code or 'report' in doc_type_code:
        doc_type = 'examiner_report'
        doc_name = "Examiner's Report"
    else:
        # Skip non-exam documents (PEF, guidance, etc.)
        return None
    
    # Parse date (YYYYMMDD)
    if len(date_str) == 8:
        year = date_str[0:4]
        month = date_str[4:6]
        
        # Determine exam series from month
        # NOTE: Mark schemes released in July/August are for May/June exams
        # Mark schemes released in November/December are for Oct/Nov exams
        if month in ['05', '06', '07', '08']:
            exam_series = 'May/June'
        elif month in ['10', '11', '12']:
            exam_series = 'October/November'
        elif month in ['01', '02', '03']:
            exam_series = 'January/February'
        else:
            exam_series = f'Month-{month}'
    else:
        year = 'unknown'
        exam_series = 'Unknown'
    
    return {
        'paper_number': paper_num,
        'paper_title': paper_title,
        'doc_type': doc_type,
        'doc_name': doc_name,
        'year': year,
        'exam_series': exam_series,
        'url': href,
        'filename': filename
    }


def group_papers_by_session(raw_papers):
    """
    Group papers by year, exam series, and paper number.
    
    Combines Question Paper, Mark Scheme, and Examiner Report
    into a single paper set.
    """
    grouped = defaultdict(lambda: {
        'question_paper': None,
        'mark_scheme': None,
        'examiner_report': None,
        'metadata': {}
    })
    
    for paper in raw_papers:
        # Create a key: year_series_papernum
        key = f"{paper['year']}_{paper['exam_series']}_{paper['paper_number']}"
        
        # Store document by type
        grouped[key][paper['doc_type']] = paper['url']
        
        # Store metadata (same for all docs in group)
        if not grouped[key]['metadata']:
            grouped[key]['metadata'] = {
                'year': paper['year'],
                'exam_series': paper['exam_series'],
                'paper_number': paper['paper_number'],
                'paper_title': paper['paper_title']
            }
    
    # Convert to list format expected by upload function
    paper_sets = []
    for key, data in grouped.items():
        meta = data['metadata']
        paper_sets.append({
            'paper_number': meta['paper_number'],
            'paper_title': meta['paper_title'],
            'year': meta['year'],
            'exam_series': meta['exam_series'],
            'question_paper_url': data['question_paper'],
            'mark_scheme_url': data['mark_scheme'],
            'examiner_report_url': data['examiner_report']
        })
    
    # Sort by year (newest first)
    paper_sets.sort(key=lambda x: (x['year'], x['exam_series'], x['paper_number']), reverse=True)
    
    return paper_sets


def main():
    """Scrape GCSE Computer Science papers and group by session."""
    
    print("=" * 80)
    print("GCSE COMPUTER SCIENCE (1CP2) - PAPERS SCRAPER (FIXED)")
    print("=" * 80)
    print("Grouping Question Papers, Mark Schemes, and Examiner Reports")
    print("=" * 80)
    
    driver = None
    raw_papers = []
    
    try:
        driver = init_driver(headless=True)
        
        url = 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/computer-science-2020.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
        
        print("\n[INFO] Navigating to Computer Science GCSE page...")
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
        print("[INFO] Scrolling to load content...")
        for _ in range(20):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.4)
        
        time.sleep(2)
        
        # Scrape PDF links
        print("[INFO] Scraping PDF links...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        
        print(f"[INFO] Found {len(pdf_links)} total PDF links")
        print("\n[INFO] Processing Computer Science papers...\n")
        
        for link in pdf_links:
            href = link.get('href', '')
            
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = 'https://qualifications.pearson.com' + href
            
            filename = href.split('/')[-1]
            
            # Parse filename
            parsed = parse_pdf_filename(filename, href)
            if parsed:
                raw_papers.append(parsed)
                print(f"  [{parsed['doc_name']:20s}] Paper {parsed['paper_number']} | {parsed['year']} {parsed['exam_series']}")
        
        print(f"\n[OK] Found {len(raw_papers)} Computer Science documents")
        
        # Group papers by session
        print("\n[INFO] Grouping papers by year/session...")
        paper_sets = group_papers_by_session(raw_papers)
        
        print(f"[OK] Grouped into {len(paper_sets)} paper sets\n")
        
        # Display grouped papers
        for paper_set in paper_sets:
            print(f"\n{paper_set['year']} {paper_set['exam_series']} - {paper_set['paper_title']}:")
            if paper_set['question_paper_url']:
                print(f"  ✓ Question Paper")
            else:
                print(f"  ✗ Question Paper (missing)")
            
            if paper_set['mark_scheme_url']:
                print(f"  ✓ Mark Scheme")
            else:
                print(f"  ✗ Mark Scheme (missing)")
            
            if paper_set['examiner_report_url']:
                print(f"  ✓ Examiner's Report")
            else:
                print(f"  ✗ Examiner's Report (missing)")
        
        # Upload to database
        if paper_sets:
            print("\n" + "=" * 80)
            print("[INFO] Uploading to database...")
            uploaded = upload_papers_to_staging(
                subject_code=SUBJECT['code'],
                qualification_type='GCSE',
                papers_data=paper_sets,
                exam_board='Edexcel'
            )
            
            print(f"\n[OK] Uploaded {uploaded} paper sets!")
            
            print("\n" + "=" * 80)
            print("[SUCCESS] GCSE COMPUTER SCIENCE PAPERS UPLOADED!")
            print("=" * 80)
            print(f"   Paper Sets: {len(paper_sets)}")
            print(f"   Total Documents: {len(raw_papers)}")
            print("=" * 80)
        else:
            print("\n[WARNING] No papers found to upload")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            driver.quit()


if __name__ == '__main__':
    main()

