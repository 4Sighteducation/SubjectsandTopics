"""
UNIVERSAL INTERNATIONAL A LEVEL PAPER SCRAPER
==============================================

Scrapes exam papers, mark schemes, and examiner reports for all Edexcel International A Level subjects.

Handles filename formats:
- Standard: wac11-01-que-20230520.pdf (Accounting Unit 1)
- Multiple units: wbi11-01, wbi15-01 (Biology Units 1, 5)
- With underscores: wac11_01_que_20230520.pdf

Groups papers into sets:
- Question Paper + Mark Scheme + Examiner Report
- Grouped by: (year, series, unit, paper_number)

Usage:
    python universal-ial-paper-scraper.py IAL-Accounting
    python universal-ial-paper-scraper.py IAL-Biology
    python universal-ial-paper-scraper.py --all  # All subjects
"""

import os
import sys
import time
import re
import json
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Setup paths
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

import importlib.util
upload_helper_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\upload_papers_to_staging.py")
spec = importlib.util.spec_from_file_location("upload_papers_to_staging", upload_helper_path)
upload_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload_module)
upload_papers_to_staging = upload_module.upload_papers_to_staging

# International A Level subjects with their codes and URLs
IAL_SUBJECTS = {
    'IAL-Accounting': {
        'name': 'Accounting',
        'code': 'wac',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/accounting-2015.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-Arabic': {
        'name': 'Arabic',
        'code': 'war',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/arabic-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-Biology': {
        'name': 'Biology',
        'code': 'wbi',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/biology-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-Business': {
        'name': 'Business',
        'code': 'wbs',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/business-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-Chemistry': {
        'name': 'Chemistry',
        'code': 'wch',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/chemistry-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-Economics': {
        'name': 'Economics',
        'code': 'wec',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/economics-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-EnglishLanguage': {
        'name': 'English Language',
        'code': 'wel',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/english-language-2015.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-EnglishLiterature': {
        'name': 'English Literature',
        'code': 'wet',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/english-literature-2015.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-French': {
        'name': 'French',
        'code': 'wfr',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/french-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-Geography': {
        'name': 'Geography',
        'code': 'wge',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/geography-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-German': {
        'name': 'German',
        'code': 'wgn',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/german-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-Greek': {
        'name': 'Greek',
        'code': 'wgk',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/greek-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-History': {
        'name': 'History',
        'code': 'whi',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/history-2015.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-IT': {
        'name': 'Information Technology',
        'code': 'wit',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/information-technology-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-Law': {
        'name': 'Law',
        'code': 'wla',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/law-2015.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-Mathematics': {
        'name': 'Mathematics',
        'code': 'wma',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/mathematics-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-FurtherMaths': {
        'name': 'Further Mathematics',
        'code': 'wfm',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/further-mathematics-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-Physics': {
        'name': 'Physics',
        'code': 'wph',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/physics-2018.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-Psychology': {
        'name': 'Psychology',
        'code': 'wps',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/psychology-2015.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IAL-Spanish': {
        'name': 'Spanish',
        'code': 'wsp',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-advanced-levels/spanish-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    }
}


def parse_ial_filename(filename, subject_code):
    """
    Parse International A Level filename formats.
    
    Examples:
    - wac11-01-que-20230520.pdf (Accounting Unit 1)
    - wbi11-01-que-20230110.pdf (Biology Unit 1)
    - wbi15-01-que-20230117.pdf (Biology Unit 5)
    - wma01-01-que-20230509.pdf (Maths Unit 1)
    """
    filename = filename.lower()
    
    # Normalize separators (both _ and -)
    filename = filename.replace('_', '-')
    
    # Pattern: w{subject}{unit}{paper}-{type}-{date}.pdf
    # e.g., wac11-01-que-20230520.pdf
    pattern = r'^w([a-z]{2,3})(\d)(\d)-(\d+)-(que|rms|pef|per)-(\d{8})\.pdf$'
    match = re.match(pattern, filename)
    
    if not match:
        return None
    
    file_subject = match.group(1)  # ac, bi, ch, etc.
    unit_tens = match.group(2)      # First digit of unit (1)
    unit_ones = match.group(3)      # Second digit of unit (1)
    paper_num = int(match.group(4)) # Paper number (01)
    doc_type_part = match.group(5)  # que, rms, pef
    date_part = match.group(6)      # 20230520
    
    # Validate subject code
    if subject_code not in f"w{file_subject}":
        return None
    
    # Parse document type
    doc_type_map = {
        'que': 'Question Paper',
        'rms': 'Mark Scheme',
        'pef': 'Examiner Report',
        'per': 'Examiner Report'
    }
    
    doc_type = doc_type_map.get(doc_type_part)
    if not doc_type:
        return None
    
    # Parse unit (e.g., 11 = Unit 1, 15 = Unit 5)
    unit = int(unit_tens + unit_ones)
    
    # Parse date
    try:
        year = int(date_part[:4])
        month = int(date_part[4:6])
        day = int(date_part[6:8])
    except:
        return None
    
    return {
        'year': year,
        'month': month,
        'unit': unit,
        'paper_num': paper_num,
        'doc_type': doc_type
    }


def scrape_subject_papers(subject_code, subject_info, driver):
    """Scrape papers for one International A Level subject."""
    
    print(f"\n{'=' * 80}")
    print(f"{subject_info['name']} ({subject_code})")
    print(f"Code: {subject_info['code']}")
    print(f"{'=' * 80}\n")
    
    try:
        driver.get(subject_info['url'])
        print("[INFO] Waiting for page to load...")
        time.sleep(6)
        
        # Expand all sections
        print("[INFO] Expanding sections...")
        try:
            expand = driver.find_elements(By.XPATH, "//*[contains(text(), 'EXPAND ALL')]")
            if expand:
                driver.execute_script("arguments[0].click();", expand[0])
                time.sleep(3)
        except:
            pass
        
        # Scroll to load all content
        print("[INFO] Scrolling to load all PDFs...")
        for i in range(35):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.7)
            
            if i % 5 == 0:
                time.sleep(2)
        
        print("[INFO] Waiting for page to finish loading...")
        time.sleep(8)
        
        # Scrape PDF links
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.IGNORECASE))
        print(f"[INFO] Found {len(pdf_links)} total PDF links on page")
        
        papers = []
        skipped = 0
        
        for link in pdf_links:
            href = link.get('href', '')
            
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = 'https://qualifications.pearson.com' + href
            
            # Only process this subject's code
            if subject_info['code'] not in href.lower():
                continue
            
            filename = href.split('/')[-1]
            
            # Parse filename
            parsed = parse_ial_filename(filename, subject_info['code'])
            
            if not parsed:
                skipped += 1
                continue
            
            # Determine exam series from month
            month = parsed['month']
            if month in [5, 6]:
                series = 'June'
            elif month in [10, 11]:
                series = 'November'
            elif month in [1, 2]:
                series = 'January'
            else:
                series = 'June'
            
            papers.append({
                'year': parsed['year'],
                'exam_series': series,
                'unit': parsed['unit'],
                'paper_number': parsed['paper_num'],
                'doc_type': parsed['doc_type'],
                'url': href,
                'filename': filename
            })
        
        print(f"[OK] Parsed {len(papers)} papers")
        if skipped > 0:
            print(f"[INFO] Skipped {skipped} PDFs (couldn't parse filename)")
        
        # Group into sets
        if papers:
            sets = group_into_sets(papers)
            print(f"[OK] Grouped into {len(sets)} paper sets")
            
            # Upload to database
            upload_to_database(subject_code, sets)
            
            return sets
        else:
            print("[WARN] No papers found for this subject")
            return []
            
    except Exception as e:
        print(f"[ERROR] Failed to scrape {subject_code}: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def group_into_sets(papers):
    """Group papers into sets by (year, series, unit, paper)."""
    sets_dict = defaultdict(lambda: {'qp': None, 'ms': None, 'er': None})
    
    for paper in papers:
        # Create unique key
        key = (paper['year'], paper['exam_series'], paper['unit'], paper['paper_number'])
        
        doc_type = paper['doc_type']
        if doc_type == 'Question Paper':
            sets_dict[key]['qp'] = paper
        elif doc_type == 'Mark Scheme':
            sets_dict[key]['ms'] = paper
        elif doc_type == 'Examiner Report':
            sets_dict[key]['er'] = paper
    
    # Convert to list of complete/partial sets
    paper_sets = []
    for key, docs in sets_dict.items():
        if docs['qp']:  # Must have at least a question paper
            paper_set = {
                'year': key[0],
                'exam_series': key[1],
                'unit': key[2],
                'paper_number': key[3],
                'question_paper': docs['qp'],
                'mark_scheme': docs['ms'],
                'examiner_report': docs['er']
            }
            paper_sets.append(paper_set)
    
    # Sort by year, series, unit, paper
    paper_sets.sort(key=lambda x: (x['year'], x['exam_series'], x['unit'], x['paper_number']))
    
    return paper_sets


def upload_to_database(subject_code, paper_sets):
    """Upload paper sets to database."""
    print(f"\n[INFO] Uploading {len(paper_sets)} paper sets to database...")
    
    try:
        # Convert paper_sets to the format expected by upload_papers_to_staging
        papers_data = []
        for pset in paper_sets:
            # Use unit as component_code (e.g., "Unit 1", "Unit 5")
            component_code = f"Unit {pset['unit']}"
            
            paper_data = {
                'year': pset['year'],
                'exam_series': pset['exam_series'],
                'paper_number': pset['paper_number'],
                'tier': None,
                'component_code': component_code,
                'question_paper_url': pset['question_paper']['url'] if pset.get('question_paper') else None,
                'mark_scheme_url': pset['mark_scheme']['url'] if pset.get('mark_scheme') else None,
                'examiner_report_url': pset['examiner_report']['url'] if pset.get('examiner_report') else None
            }
            papers_data.append(paper_data)
        
        # Use the upload helper with correct parameters
        uploaded_count = upload_papers_to_staging(
            subject_code=subject_code,
            qualification_type='International A Level',
            papers_data=papers_data,
            exam_board='Edexcel'
        )
        
        print(f"[OK] Uploaded {uploaded_count} paper sets successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Database upload failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Universal International A Level paper scraper')
    parser.add_argument('subject', nargs='?', help='Subject code (e.g., IAL-Biology) or --all for all subjects')
    parser.add_argument('--all', action='store_true', help='Scrape all subjects')
    args = parser.parse_args()
    
    # Setup Selenium
    print("[INFO] Starting Chrome...")
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Suppress DevTools messages
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        if args.all:
            # Scrape all subjects
            print(f"\n[INFO] Scraping ALL {len(IAL_SUBJECTS)} International A Level subjects...")
            for subject_code, subject_info in IAL_SUBJECTS.items():
                scrape_subject_papers(subject_code, subject_info, driver)
                time.sleep(3)  # Delay between subjects
        else:
            # Scrape single subject
            subject_code = args.subject
            if subject_code not in IAL_SUBJECTS:
                print(f"[ERROR] Unknown subject: {subject_code}")
                print(f"Available subjects: {', '.join(IAL_SUBJECTS.keys())}")
                sys.exit(1)
            
            scrape_subject_papers(subject_code, IAL_SUBJECTS[subject_code], driver)
    
    finally:
        driver.quit()
        print("\n[INFO] Done!")


if __name__ == '__main__':
    main()

