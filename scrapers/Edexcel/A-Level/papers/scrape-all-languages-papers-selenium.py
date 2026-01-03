"""
Edexcel A-Level Languages - Universal Papers Scraper
Scrapes exam papers for ALL 14 language subjects in one go.
Uses Selenium to scrape actual links from Edexcel coursematerials pages.

Languages: Arabic, Chinese, French, German, Greek, Gujarati, Italian, 
           Japanese, Persian, Portuguese, Russian, Spanish, Turkish, Urdu
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

# All 14 Edexcel A-Level Languages
# URLs updated to use correct spec year (2018 for newer languages)
# Paper codes may differ from subject codes!
LANGUAGES = {
    '9AA0': {
        'name': 'Arabic',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/arabic-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '9aa0'  # Same as subject code
    },
    '9CN0': {
        'name': 'Chinese',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/chinese-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '9cn0'
    },
    '9FR0': {
        'name': 'French',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/french-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '9fr0'
    },
    '9GN0': {
        'name': 'German',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/german-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '9gn0'
    },
    '9GK0': {
        'name': 'Greek',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/greek-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '9gk0'
    },
    '9GU0': {
        'name': 'Gujarati',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/gujarati-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '9gu0'
    },
    '9IN0': {
        'name': 'Italian',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/italian-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '9in0'
    },
    '9JA0': {
        'name': 'Japanese',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/japanese-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '9ja0'
    },
    '9PE0': {
        'name': 'Persian',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/persian-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '9pn0'  # Papers use 9PN0 not 9PE0!
    },
    '9PT0': {
        'name': 'Portuguese',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/portuguese-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '9pg0'  # Papers use 9PG0 not 9PT0!
    },
    '9RU0': {
        'name': 'Russian',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/russian-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '9ru0'
    },
    '9SP0': {
        'name': 'Spanish',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/spanish-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '9sp0'
    },
    '9TU0': {
        'name': 'Turkish',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/turkish-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '9tu0'
    },
    '9UR0': {
        'name': 'Urdu',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/urdu-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '9ur0'
    }
}


def init_driver(headless=True):
    """Initialize Chrome WebDriver."""
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
    
    return driver


def scrape_language_papers(subject_code, subject_name, url, paper_code, driver):
    """Scrape papers for a single language."""
    
    print(f"\n{'=' * 80}")
    print(f"SCRAPING: {subject_name} ({subject_code})")
    if paper_code != subject_code.lower():
        print(f"Note: Papers use code {paper_code.upper()}")
    print(f"{'=' * 80}\n")
    
    papers = []
    
    try:
        print(f"[INFO] Navigating to exam materials page...")
        driver.get(url)
        time.sleep(5)
        
        # Click EXPAND ALL
        print("[INFO] Looking for EXPAND ALL button...")
        try:
            expand_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'EXPAND ALL')]")
            if expand_buttons:
                print("[INFO] Clicking EXPAND ALL...")
                driver.execute_script("arguments[0].click();", expand_buttons[0])
                time.sleep(3)
                print("[OK] Expanded")
        except:
            print("[WARN] No EXPAND ALL found")
        
        # Expand any remaining collapsed sections
        print("[INFO] Expanding sections...")
        selectors = ["button[aria-expanded='false']", "summary"]
        expanded = 0
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements[:30]:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                        time.sleep(0.2)
                        driver.execute_script("arguments[0].click();", elem)
                        time.sleep(0.3)
                        expanded += 1
                    except:
                        pass
            except:
                pass
        
        print(f"[OK] Expanded {expanded} sections")
        
        # Scroll to load content
        print("[INFO] Scrolling to load content...")
        time.sleep(2)
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        for _ in range(15):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.4)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Scrape PDF links
        print("[INFO] Scraping PDF links...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        
        print(f"[INFO] Found {len(pdf_links)} PDF links")
        
        # Parse each link
        for link in pdf_links:
            href = link.get('href', '')
            
            # Make absolute
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = 'https://qualifications.pearson.com' + href
            
            # Only this subject's papers (use paper_code which may differ from subject_code)
            if paper_code not in href.lower():
                continue
            
            filename = href.split('/')[-1]
            
            # Parse filename: 9fr0-01-que-20240524.pdf (or 9pn0 for Persian, etc.)
            # Pattern works for all languages
            match = re.search(rf'{paper_code}[-_](\d+)[-_]([a-z]{{3}})[-_](\d{{8}})', filename, re.IGNORECASE)
            
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
                'msc': 'Mark Scheme',  # Alternative format
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
        
        print(f"[OK] Parsed {len(papers)} papers for {subject_name}")
        
        if papers:
            # Show breakdown
            doc_types_found = Counter(p['doc_type'] for p in papers)
            years = Counter(p['year'] for p in papers)
            print(f"\n   Breakdown:")
            for dt, count in doc_types_found.items():
                print(f"   {dt}: {count}")
            print(f"   Years: {min(years.keys())}-{max(years.keys())}")
        
        return papers
        
    except Exception as e:
        print(f"[ERROR] Failed to scrape {subject_name}: {e}")
        import traceback
        traceback.print_exc()
        return []


def group_papers(papers):
    """Group papers into sets."""
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
    """Main execution - scrape all languages."""
    
    print("=" * 80)
    print("EDEXCEL A-LEVEL LANGUAGES - UNIVERSAL PAPERS SCRAPER")
    print("=" * 80)
    print(f"\nScraping papers for {len(LANGUAGES)} languages")
    print("This will take 20-30 minutes...\n")
    
    driver = None
    results = {
        'success': [],
        'failed': [],
        'no_papers': []
    }
    
    try:
        # Initialize driver once for all languages
        print("[INFO] Initializing Chrome WebDriver...")
        driver = init_driver(headless=True)
        print("[OK] WebDriver initialized\n")
        
        # Process each language
        for subject_code in sorted(LANGUAGES.keys()):
            subject_info = LANGUAGES[subject_code]
            subject_name = subject_info['name']
            url = subject_info['url']
            paper_code = subject_info.get('paper_code', subject_code.lower())
            
            try:
                # Scrape papers
                papers = scrape_language_papers(subject_code, subject_name, url, paper_code, driver)
                
                if not papers:
                    print(f"[WARN] No papers found for {subject_name}")
                    results['no_papers'].append(subject_name)
                    continue
                
                # Group into sets
                print(f"[INFO] Grouping into sets...")
                sets = group_papers(papers)
                print(f"[OK] Created {len(sets)} paper sets")
                
                # Upload to database
                print(f"[INFO] Uploading to database...")
                uploaded = upload_papers_to_staging(
                    subject_code=subject_code,
                    qualification_type='A-Level',
                    papers_data=sets,
                    exam_board='Edexcel'
                )
                
                print(f"[OK] Uploaded {uploaded} sets for {subject_name}")
                results['success'].append({
                    'name': subject_name,
                    'code': subject_code,
                    'sets': uploaded
                })
                
            except Exception as e:
                print(f"[ERROR] Failed to process {subject_name}: {e}")
                results['failed'].append(subject_name)
        
    finally:
        if driver:
            print("\n[INFO] Closing browser...")
            driver.quit()
            print("[OK] Browser closed")
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    if results['success']:
        print(f"\n✅ Successfully scraped: {len(results['success'])}/{len(LANGUAGES)}")
        total_sets = 0
        for lang in results['success']:
            print(f"   • {lang['name']} ({lang['code']}): {lang['sets']} sets")
            total_sets += lang['sets']
        print(f"\n   TOTAL: {total_sets} paper sets uploaded!")
    
    if results['no_papers']:
        print(f"\n⚠️  No papers found: {len(results['no_papers'])}")
        for lang in results['no_papers']:
            print(f"   • {lang}")
    
    if results['failed']:
        print(f"\n❌ Failed: {len(results['failed'])}")
        for lang in results['failed']:
            print(f"   • {lang}")
    
    print("\n" + "=" * 80)
    
    return len(results['success'])


if __name__ == '__main__':
    total = main()
    print(f"\nCompleted: {total} languages with papers uploaded!")

