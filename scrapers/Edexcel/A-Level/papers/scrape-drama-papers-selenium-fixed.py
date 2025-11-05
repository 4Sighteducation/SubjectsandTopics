"""
Edexcel Drama and Theatre (9DR0) - Past Papers Scraper (FIXED)
Manually clicks the Exam materials radio button filter
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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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


def init_driver(headless=False):
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


def scrape_drama_papers():
    SUBJECT = {
        'name': 'Drama and Theatre',
        'code': '9DR0',
        # Go to main page first, then apply filter manually
        'base_url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/drama-2016.coursematerials.html'
    }
    
    print("=" * 80)
    print("EDEXCEL DRAMA AND THEATRE (9DR0) - PAPERS SCRAPER (FIXED)")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}\n")
    
    driver = None
    papers = []
    
    try:
        driver = init_driver(headless=False)  # Visible to debug
        
        print(f"[INFO] Navigating to course materials page...")
        driver.get(SUBJECT['base_url'])
        
        print("[INFO] Waiting for page to load (10 seconds)...")
        time.sleep(10)
        
        # Try to click the Exam materials radio button directly
        print("[INFO] Looking for Exam materials filter radio button...")
        try:
            # Look for the input radio button with value containing "Exam-materials"
            exam_radio = driver.find_elements(By.CSS_SELECTOR, 'input[value*="Exam-materials"]')
            if exam_radio:
                print(f"[INFO] Found {len(exam_radio)} Exam materials radio buttons")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", exam_radio[0])
                time.sleep(1)
                driver.execute_script("arguments[0].click();", exam_radio[0])
                print("[OK] Clicked Exam materials filter")
                time.sleep(10)  # Wait for AJAX to load content
            else:
                print("[WARN] No radio button found - trying label click...")
                # Try clicking the label instead
                exam_labels = driver.find_elements(By.XPATH, "//label[contains(text(), 'Exam materials')]")
                if exam_labels:
                    driver.execute_script("arguments[0].click();", exam_labels[0])
                    print("[OK] Clicked Exam materials label")
                    time.sleep(10)
        except Exception as e:
            print(f"[WARN] Could not click filter: {e}")
        
        # Click EXPAND ALL
        print("[INFO] Looking for EXPAND ALL button...")
        try:
            expand_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'EXPAND ALL')]")
            if expand_buttons:
                driver.execute_script("arguments[0].click();", expand_buttons[0])
                time.sleep(5)
                print("[OK] Clicked EXPAND ALL")
        except:
            print("[WARN] No EXPAND ALL button")
        
        # Expand remaining sections
        print("[INFO] Expanding remaining sections...")
        expanded = 0
        for selector in ["button[aria-expanded='false']", "summary", "details"]:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements[:40]:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                        time.sleep(0.3)
                        driver.execute_script("arguments[0].click();", elem)
                        time.sleep(0.3)
                        expanded += 1
                    except:
                        pass
            except:
                pass
        print(f"[OK] Expanded {expanded} sections")
        
        # Multiple scroll rounds
        print("[INFO] Scrolling to load all content...")
        for round in range(3):
            last_height = driver.execute_script("return document.body.scrollHeight")
            for _ in range(15):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.8)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
        
        # Save page
        debug_path = Path(__file__).parent / "debug-drama-page-fixed.html"
        debug_path.write_text(driver.page_source, encoding='utf-8')
        print(f"[INFO] Saved page to: {debug_path.name}")
        
        # Scrape
        print("\n[INFO] Scraping PDF links...")
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
            print(f"   Found: {filename}")
            
            match = re.search(r'9dr0[-_](\d+)[-_]([a-z]{3})[-_](\d{8})', filename, re.IGNORECASE)
            
            if not match:
                print(f"      [WARN] Could not parse")
                continue
            
            paper_num = int(match.group(1))
            doc_type_code = match.group(2).lower()
            date_str = match.group(3)
            year = int(date_str[:4])
            month = int(date_str[4:6])
            series = 'June' if month in [5, 6] else 'October' if month in [10, 11] else 'January' if month == 1 else 'June'
            
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
            print(f"      [OK] {year} {series} - Paper {paper_num} - {doc_type}")
        
        print(f"\n[INFO] Found {len(papers)} papers")
        
        if papers:
            doc_types_found = Counter(p['doc_type'] for p in papers)
            print("\nBreakdown:")
            for dt, count in doc_types_found.items():
                print(f"   {dt}: {count}")
            years = Counter(p['year'] for p in papers)
            print(f"\n   Years: {dict(sorted(years.items(), reverse=True))}")
        
        return papers
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if driver:
            print("\n[INFO] Keeping browser open for 15 seconds - check if papers loaded...")
            time.sleep(15)
            driver.quit()
            print("[OK] Browser closed")


def group_papers(papers):
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
    return list(sets.values())


def main():
    papers = scrape_drama_papers()
    
    if not papers:
        print("\n[WARN] No papers found!")
        print("The page might require JavaScript that Selenium can't trigger.")
        print("Check debug-drama-page-fixed.html to see what loaded.")
        return 0
    
    print("\n[INFO] Grouping into sets...")
    sets = group_papers(papers)
    print(f"   Created {len(sets)} paper sets")
    
    print("\n[INFO] Uploading to database...")
    try:
        uploaded = upload_papers_to_staging(
            subject_code='9DR0',
            qualification_type='A-Level',
            papers_data=sets,
            exam_board='Edexcel'
        )
        print(f"\n[OK] Uploaded {uploaded} paper sets!")
    except Exception as e:
        print(f"\n[ERROR] Upload failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("[OK] DRAMA PAPERS COMPLETE!")
    print("=" * 80)
    
    return len(sets)


if __name__ == '__main__':
    main()

