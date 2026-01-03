"""
EDEXCEL GCSE LANGUAGES - UNIVERSAL PAPER SCRAPER
Handles all 14 GCSE languages in one script
GCSE uses '1' prefix (1in0, 1fr0) vs A-Level '9' prefix (9in0, 9fr0)
GCSE has tiers: F (Foundation), H (Higher)
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

# All GCSE Languages with paper codes
GCSE_LANGUAGES = {
    'GCSE-French': {
        'name': 'French',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/french-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',  # Use 2016 for papers!
        'paper_code': '1fr0'
    },
    'GCSE-German': {
        'name': 'German',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/german-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',  # Use 2016 for papers!
        'paper_code': '1gn0'
    },
    'GCSE-Spanish': {
        'name': 'Spanish',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/spanish-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',  # Use 2016 for papers!
        'paper_code': '1sp0'
    },
    'GCSE-Arabic': {
        'name': 'Arabic',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/arabic-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '1aa0'
    },
    'GCSE-Chinese': {
        'name': 'Chinese',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/chinese-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '1cn0'
    },
    'GCSE-Greek': {
        'name': 'Greek',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/greek-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '1gk0'
    },
    'GCSE-Gujarati': {
        'name': 'Gujarati',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/gujarati-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '1gu0'
    },
    'GCSE-Italian': {
        'name': 'Italian',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/italian-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '1in0'
    },
    'GCSE-Japanese': {
        'name': 'Japanese',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/japanese-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '1ja0'
    },
    'GCSE-Persian': {
        'name': 'Persian',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/persian-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '1pn0'  # Same as A-Level but with 1 prefix
    },
    'GCSE-Portuguese': {
        'name': 'Portuguese',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/portuguese-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '1pg0'  # Same as A-Level but with 1 prefix
    },
    'GCSE-Russian': {
        'name': 'Russian',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/russian-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '1ru0'
    },
    'GCSE-Turkish': {
        'name': 'Turkish',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/turkish-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '1tu0'
    },
    'GCSE-Urdu': {
        'name': 'Urdu',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/urdu-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'paper_code': '1ur0'
    },
}


def init_driver(headless=True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver


def scrape_language_papers(subject_code, name, url, paper_code, driver):
    """Scrape papers for one GCSE language."""
    
    print(f"\n{'=' * 80}")
    print(f"{name} ({subject_code}) - Papers: {paper_code.upper()}")
    print(f"{'=' * 80}\n")
    
    papers = []
    
    try:
        driver.get(url)
        time.sleep(4)
        
        # Expand
        try:
            expand = driver.find_elements(By.XPATH, "//*[contains(text(), 'EXPAND ALL')]")
            if expand:
                driver.execute_script("arguments[0].click();", expand[0])
                time.sleep(2)
        except:
            pass
        
        # Scroll
        for _ in range(15):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.3)
        
        # Scrape
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
            
            # Parse: 1in0-1f-que-20230516.pdf
            # Pattern: [code]-[paper][tier]-[type]-[date]
            match = re.search(rf'{paper_code}[-_](\d+)([fh])[-_]([a-z]{{3}})[-_](\d{{8}})', filename, re.IGNORECASE)
            
            if not match:
                continue
            
            paper_num = int(match.group(1))
            tier = match.group(2).upper()  # F or H
            doc_type_code = match.group(3).lower()
            date_str = match.group(4)
            
            year = int(date_str[:4])
            month = int(date_str[4:6])
            
            # GCSE series
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
        
        print(f"[OK] Found {len(papers)} papers")
        return papers
        
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        return []


def main():
    """Scrape papers for all 14 GCSE languages."""
    
    print("=" * 80)
    print("GCSE LANGUAGES - UNIVERSAL PAPER SCRAPER")
    print("=" * 80)
    print("Scraping papers for all 14 languages")
    print("GCSE uses '1' prefix + tier indicators (F/H)\n")
    
    driver = None
    results = {'success': [], 'failed': []}
    
    try:
        driver = init_driver(headless=True)
        
        for subject_code in sorted(GCSE_LANGUAGES.keys()):
            info = GCSE_LANGUAGES[subject_code]
            
            papers = scrape_language_papers(
                subject_code, 
                info['name'], 
                info['url'], 
                info['paper_code'], 
                driver
            )
            
            if papers:
                # Group into sets (including tier)
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
                
                # Upload
                uploaded = upload_papers_to_staging(
                    subject_code=subject_code,
                    qualification_type='GCSE',
                    papers_data=paper_sets,
                    exam_board='Edexcel'
                )
                
                results['success'].append({
                    'name': info['name'],
                    'sets': uploaded
                })
                print(f"[OK] {info['name']}: {uploaded} sets uploaded")
            else:
                results['failed'].append(info['name'])
                print(f"[WARN] {info['name']}: No papers found")
            
            time.sleep(0.5)
    
    finally:
        if driver:
            driver.quit()
    
    # Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    if results['success']:
        print(f"\n✅ Success: {len(results['success'])}/14")
        total = sum(r['sets'] for r in results['success'])
        for r in results['success']:
            print(f"   • {r['name']}: {r['sets']} sets")
        print(f"\n   TOTAL: {total} paper sets")
    
    if results['failed']:
        print(f"\n❌ No papers: {len(results['failed'])}")
        for name in results['failed']:
            print(f"   • {name}")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()

