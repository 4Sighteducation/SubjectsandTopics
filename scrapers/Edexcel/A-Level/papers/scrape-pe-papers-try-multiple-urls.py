"""
Edexcel Physical Education (9PE1) - Papers Scraper with Multiple URL Attempts
Tries different spec year URLs like we did for languages (2016, 2017, 2018)
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


def try_scrape_url(driver, url, year_label):
    """Try scraping from a specific URL."""
    
    print(f"\n[INFO] Trying {year_label} URL...")
    papers = []
    
    try:
        driver.get(url)
        time.sleep(5)
        
        # Click EXPAND ALL
        try:
            expand_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'EXPAND ALL')]")
            if expand_buttons:
                driver.execute_script("arguments[0].click();", expand_buttons[0])
                time.sleep(3)
        except:
            pass
        
        # Expand sections
        selectors = ["button[aria-expanded='false']", "summary"]
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements[:30]:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                        time.sleep(0.2)
                        driver.execute_script("arguments[0].click();", elem)
                        time.sleep(0.3)
                    except:
                        pass
            except:
                pass
        
        # Scroll
        time.sleep(2)
        for _ in range(15):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.4)
        
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Scrape PDF links
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        
        print(f"[INFO] Found {len(pdf_links)} PDF links total")
        
        # Parse each link
        for link in pdf_links:
            href = link.get('href', '')
            
            # Make absolute
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = 'https://qualifications.pearson.com' + href
            
            # Only PE papers (9pe0 - note the 0 not 1!)
            if '9pe0' not in href.lower():
                continue
            
            filename = href.split('/')[-1]
            
            # Parse filename: 9pe0-01-que-20240524.pdf (note: 9pe0 not 9pe1!)
            match = re.search(r'9pe0[-_](\d+)[-_]([a-z]{3})[-_](\d{8})', filename, re.IGNORECASE)
            
            if not match:
                continue
            
            paper_num = int(match.group(1))
            doc_type_code = match.group(2).lower()
            date_str = match.group(3)
            
            year = int(date_str[:4])
            month = int(date_str[4:6])
            
            # Series from month
            series = 'June' if month in [5, 6] else 'October' if month == 10 else 'January' if month == 1 else 'June'
            
            # Doc type
            doc_types = {
                'que': 'Question Paper',
                'rms': 'Mark Scheme',
                'pef': 'Examiner Report'
            }
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
        
        if papers:
            print(f"[OK] Found {len(papers)} PE papers at {year_label}!")
        else:
            print(f"[WARN] No PE papers found at {year_label}")
        
        return papers
        
    except Exception as e:
        print(f"[ERROR] Error trying {year_label}: {e}")
        return []


def main():
    """Try multiple URL patterns."""
    
    print("=" * 80)
    print("EDEXCEL PHYSICAL EDUCATION (9PE1) - MULTI-URL PAPER SCRAPER")
    print("=" * 80)
    print("\nTrying different spec year URLs (like we did for languages)...\n")
    
    # Try different year URLs
    urls_to_try = [
        ('2016', 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/physical-education-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'),
        ('2017', 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/physical-education-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'),
        ('2018', 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/physical-education-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'),
    ]
    
    driver = None
    all_papers = []
    
    try:
        driver = init_driver(headless=True)
        
        for year_label, url in urls_to_try:
            papers = try_scrape_url(driver, url, year_label)
            if papers:
                all_papers.extend(papers)
                print(f"[OK] Got {len(papers)} papers from {year_label}!")
                break  # Found papers, stop trying
        
    finally:
        if driver:
            print("\n[INFO] Closing browser...")
            driver.quit()
            print("[OK] Browser closed")
    
    if not all_papers:
        print("\n" + "=" * 80)
        print("[WARN] NO PAPERS FOUND on any URL")
        print("=" * 80)
        print("\nPhysical Education papers may not be published by Edexcel.")
        print("Recommendation: Use Manual Paper Entry in data viewer if you have URLs.")
        return 0
    
    # Group papers
    print("\n[INFO] Grouping into sets...")
    sets = {}
    
    for paper in all_papers:
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
    print(f"[OK] Created {len(paper_sets)} paper sets")
    
    # Upload
    print("\n[INFO] Uploading to database...")
    
    try:
        uploaded = upload_papers_to_staging(
            subject_code='9PE1',
            qualification_type='A-Level',
            papers_data=paper_sets,
            exam_board='Edexcel'
        )
        
        print(f"\n[OK] Uploaded {uploaded} paper sets!")
        
        # Show breakdown
        doc_types_found = Counter(p['doc_type'] for p in all_papers)
        years = Counter(p['year'] for p in all_papers)
        
        print("\nBreakdown:")
        for dt, count in doc_types_found.items():
            print(f"   {dt}: {count}")
        print(f"\n   Years: {dict(sorted(years.items(), reverse=True))}")
        
    except Exception as e:
        print(f"\n[ERROR] Upload failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("[OK] PHYSICAL EDUCATION PAPERS COMPLETE!")
    print("=" * 80)
    print(f"\nTotal: {len(paper_sets)} paper sets")
    
    return len(paper_sets)


if __name__ == '__main__':
    main()

