"""
Edexcel GCSE Drama (1DR0) - Past Papers Scraper
Note: GCSE code is 1DR0 (with 1, not 9 like A-Level)
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
    """Scrape GCSE Drama papers."""
    
    print("=" * 80)
    print("GCSE DRAMA (1DR0) - PAPERS SCRAPER")
    print("=" * 80)
    print("Note: GCSE uses code 1DR0 (not 9DR0)\n")
    
    driver = None
    papers = []
    
    try:
        driver = init_driver(headless=True)
        
        url = 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/drama-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
        
        print("[INFO] Navigating to Drama GCSE page...")
        driver.get(url)
        time.sleep(5)
        
        # Expand
        print("[INFO] Expanding sections...")
        try:
            expand = driver.find_elements(By.XPATH, "//*[contains(text(), 'EXPAND ALL')]")
            if expand:
                driver.execute_script("arguments[0].click();", expand[0])
                time.sleep(3)
        except:
            pass
        
        # Scroll
        print("[INFO] Scrolling...")
        for _ in range(20):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.4)
        
        time.sleep(2)
        
        # Scrape
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
            
            # GCSE Drama papers use 1dr0 (not 9dr0!)
            if '1dr0' not in href.lower():
                continue
            
            filename = href.split('/')[-1]
            
            # Parse: 1dr0-3b-que-20220520.pdf
            # Pattern: 1dr0-[paper][tier]-[type]-[date]
            match = re.search(r'1dr0[-_](\d+)([a-z]?)[-_]([a-z]{3})[-_](\d{8})', filename, re.IGNORECASE)
            
            if not match:
                continue
            
            paper_num = int(match.group(1))
            tier = match.group(2).upper() if match.group(2) else None
            doc_type_code = match.group(3).lower()
            date_str = match.group(4)
            
            year = int(date_str[:4])
            month = int(date_str[4:6])
            
            # GCSE series: June or November
            series = 'June' if month in [5, 6] else 'November' if month == 11 else 'January' if month == 1 else 'June'
            
            doc_types = {
                'que': 'Question Paper',
                'rms': 'Mark Scheme',
                'msc': 'Mark Scheme',
                'pef': 'Examiner Report'
            }
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
            
            tier_text = f" ({tier})" if tier else ""
            print(f"[OK] {year} {series} - Paper {paper_num}{tier_text} - {doc_type}")
        
        print(f"\n[INFO] Found {len(papers)} Drama papers")
        
        if papers:
            # Breakdown
            doc_types_found = Counter(p['doc_type'] for p in papers)
            years = Counter(p['year'] for p in papers)
            
            print("\nBreakdown:")
            for dt, count in doc_types_found.items():
                print(f"   {dt}: {count}")
            print(f"\n   Years: {min(years.keys())}-{max(years.keys())}")
            
            # Group into sets
            sets = {}
            for paper in papers:
                # Key includes tier for GCSE
                tier_key = paper['tier'] if paper['tier'] else ''
                key = (paper['year'], paper['exam_series'], paper['paper_number'], tier_key)
                
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
            
            print(f"\n[INFO] Created {len(paper_sets)} paper sets")
            
            # Upload
            print("[INFO] Uploading to database...")
            uploaded = upload_papers_to_staging(
                subject_code='GCSE-Drama',
                qualification_type='GCSE',
                papers_data=paper_sets,
                exam_board='Edexcel'
            )
            
            print(f"\n[OK] Uploaded {uploaded} paper sets!")
            
            print("\n" + "=" * 80)
            print("[OK] GCSE DRAMA PAPERS COMPLETE!")
            print("=" * 80)
            print(f"Total: {len(paper_sets)} paper sets")
            
            return len(paper_sets)
        else:
            print("\n[WARN] No papers found")
            return 0
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 0
        
    finally:
        if driver:
            driver.quit()


if __name__ == '__main__':
    main()

