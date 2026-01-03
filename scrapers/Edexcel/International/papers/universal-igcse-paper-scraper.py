"""
UNIVERSAL INTERNATIONAL GCSE PAPER SCRAPER
==========================================

Scrapes exam papers, mark schemes, and examiner reports for all Edexcel International GCSE subjects.

Handles filename formats:
- Standard: 4FR1_02_que_20210505.pdf, 4fr1-02-que-20210505.pdf
- With underscores: 4FR1_02_rms_20210604.pdf
- Mixed case: 4hi1-02-que-20230608.pdf
- Examiner reports: 4fr1-02-pef-20220825.pdf

Groups papers into sets:
- Question Paper + Mark Scheme + Examiner Report
- Grouped by: (year, series, paper_number)

Usage:
    python universal-igcse-paper-scraper.py IG-French
    python universal-igcse-paper-scraper.py IG-History
    python universal-igcse-paper-scraper.py --all  # All subjects
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

# International GCSE subjects with their codes and URLs
IGCSE_SUBJECTS = {
    'IG-Accounting': {
        'name': 'Accounting',
        'code': '4ac1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-accounting-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-Arabic': {
        'name': 'Arabic',
        'code': '4ar1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-arabic-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-Biology': {
        'name': 'Biology',
        'code': '4bi1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-biology-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-Business': {
        'name': 'Business Studies',
        'code': '4bs1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-business-studies-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-Chemistry': {
        'name': 'Chemistry',
        'code': '4ch1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-chemistry-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-Chinese': {
        'name': 'Chinese',
        'code': '4cn1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-chinese-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-Commerce': {
        'name': 'Commerce',
        'code': '4cm1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-commerce-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-ComputerScience': {
        'name': 'Computer Science',
        'code': '4cs1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-computer-science-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-Economics': {
        'name': 'Economics',
        'code': '4ec1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-economics-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-EnglishESL': {
        'name': 'English as a Second Language',
        'code': '4es1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-english-as-a-second-language-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-EnglishLanguageA': {
        'name': 'English Language A',
        'code': '4ea1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-english-language-a-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-EnglishLanguageB': {
        'name': 'English Language B',
        'code': '4eb1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-english-language-b-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-EnglishLiterature': {
        'name': 'English Literature',
        'code': '4et1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-english-literature-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-French': {
        'name': 'French',
        'code': '4fr1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-french-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-Geography': {
        'name': 'Geography',
        'code': '4ge1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-geography-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-German': {
        'name': 'German',
        'code': '4gn1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-german-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-History': {
        'name': 'History',
        'code': '4hi1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-history-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-HumanBiology': {
        'name': 'Human Biology',
        'code': '4hb1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-human-biology-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-ICT': {
        'name': 'Information and Communication Technology',
        'code': '4it1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-ict-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-MathematicsA': {
        'name': 'Mathematics A',
        'code': '4ma1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-mathematics-a-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-MathematicsB': {
        'name': 'Mathematics B',
        'code': '4mb1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-mathematics-b-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-FurtherPureMaths': {
        'name': 'Further Pure Mathematics',
        'code': '4pm1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-further-pure-mathematics-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-Physics': {
        'name': 'Physics',
        'code': '4ph1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-physics-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-Spanish': {
        'name': 'Spanish',
        'code': '4sp1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-spanish-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    },
    'IG-ScienceDoubleAward': {
        'name': 'Science (Double Award)',
        'code': '4sc1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses/international-gcse-science-double-award-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
    }
}


def parse_igcse_filename(filename, subject_code):
    """
    Parse International GCSE filename formats.
    
    Examples:
    - 4FR1_02_que_20210505.pdf
    - 4fr1-02-rms-20210604.pdf
    - 4hi1-02-pef-20230824.pdf
    - 4ma1_1h_que_20220511.pdf (with tier)
    - 4hi1-2a-que-20230608.pdf (with option)
    """
    filename = filename.lower()
    
    # Normalize separators (both _ and -)
    parts = re.split(r'[-_]', filename)
    
    if len(parts) < 4:
        return None
    
    # Extract components
    code_part = parts[0]  # e.g., 4fr1, 4hi1
    paper_part = parts[1]  # e.g., 02, 1h, 2a
    doc_type_part = parts[2]  # que, rms, pef
    date_part = parts[3].replace('.pdf', '')  # 20210505
    
    # Validate subject code
    if subject_code not in code_part:
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
    
    # Parse paper number and tier/option
    tier = None
    option = None
    paper_num = None
    
    if paper_part.isdigit():
        # Simple paper number: 01, 02
        paper_num = int(paper_part)
    elif len(paper_part) == 2 and paper_part[0].isdigit():
        # Paper with tier or option: 1h, 1f, 2a, 2b
        paper_num = int(paper_part[0])
        suffix = paper_part[1].upper()
        if suffix in ['H', 'F']:
            tier = 'Higher' if suffix == 'H' else 'Foundation'
        else:
            option = suffix
    else:
        return None
    
    # Parse date
    if len(date_part) != 8:
        return None
    
    try:
        year = int(date_part[:4])
        month = int(date_part[4:6])
        day = int(date_part[6:8])
    except:
        return None
    
    return {
        'year': year,
        'month': month,
        'paper_num': paper_num,
        'tier': tier,
        'option': option,
        'doc_type': doc_type
    }


def scrape_subject_papers(subject_code, subject_info, driver):
    """Scrape papers for one International GCSE subject."""
    
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
        
        # Debug: Show first few PDF filenames to check codes
        if pdf_links:
            sample_pdfs = [link.get('href', '').split('/')[-1] for link in pdf_links[:5]]
            print(f"[DEBUG] Sample PDFs: {sample_pdfs}")
        
        papers = []
        skipped = 0
        skipped_samples = []
        matched_code = 0
        
        for link in pdf_links:
            href = link.get('href', '')
            
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = 'https://qualifications.pearson.com' + href
            
            filename = href.split('/')[-1]
            
            # Only process this subject's code (case insensitive)
            if subject_info['code'] not in href.lower():
                continue
            
            matched_code += 1
            
            # Parse filename
            parsed = parse_igcse_filename(filename, subject_info['code'])
            
            if not parsed:
                skipped += 1
                if len(skipped_samples) < 3:  # Keep first 3 failed samples for debugging
                    skipped_samples.append(filename)
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
                'paper_number': parsed['paper_num'],
                'tier': parsed['tier'],
                'option': parsed['option'],
                'doc_type': parsed['doc_type'],
                'url': href,
                'filename': filename
            })
        
        print(f"[INFO] Found {matched_code} PDFs matching code '{subject_info['code']}'")
        print(f"[OK] Parsed {len(papers)} papers")
        if skipped > 0:
            print(f"[INFO] Skipped {skipped} PDFs (couldn't parse filename)")
            if skipped_samples:
                print(f"[DEBUG] Sample skipped files: {skipped_samples}")
        
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
    """Group papers into sets by (year, series, paper, tier/option)."""
    sets_dict = defaultdict(lambda: {'qp': None, 'ms': None, 'er': None})
    
    for paper in papers:
        # Create unique key
        tier_option = paper['tier'] or paper['option'] or 'None'
        key = (paper['year'], paper['exam_series'], paper['paper_number'], tier_option)
        
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
                'paper_number': key[2],
                'tier': key[3] if key[3] in ['Higher', 'Foundation'] else None,
                'option': key[3] if key[3] not in ['Higher', 'Foundation', 'None'] else None,
                'question_paper': docs['qp'],
                'mark_scheme': docs['ms'],
                'examiner_report': docs['er']
            }
            paper_sets.append(paper_set)
    
    # Sort by year, series, paper number
    paper_sets.sort(key=lambda x: (x['year'], x['exam_series'], x['paper_number']))
    
    return paper_sets


def upload_to_database(subject_code, paper_sets):
    """Upload paper sets to database."""
    print(f"\n[INFO] Uploading {len(paper_sets)} paper sets to database...")
    
    try:
        # Convert paper_sets to the format expected by upload_papers_to_staging
        papers_data = []
        for pset in paper_sets:
            paper_data = {
                'year': pset['year'],
                'exam_series': pset['exam_series'],
                'paper_number': pset['paper_number'],
                'tier': pset.get('tier'),
                'component_code': pset.get('option'),  # Use option as component_code
                'question_paper_url': pset['question_paper']['url'] if pset.get('question_paper') else None,
                'mark_scheme_url': pset['mark_scheme']['url'] if pset.get('mark_scheme') else None,
                'examiner_report_url': pset['examiner_report']['url'] if pset.get('examiner_report') else None
            }
            papers_data.append(paper_data)
        
        # Use the upload helper with correct parameters
        uploaded_count = upload_papers_to_staging(
            subject_code=subject_code,
            qualification_type='International GCSE',
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
    parser = argparse.ArgumentParser(description='Universal International GCSE paper scraper')
    parser.add_argument('subject', nargs='?', help='Subject code (e.g., IG-French) or --all for all subjects')
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
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        if args.all:
            # Scrape all subjects
            print(f"\n[INFO] Scraping ALL {len(IGCSE_SUBJECTS)} International GCSE subjects...")
            for subject_code, subject_info in IGCSE_SUBJECTS.items():
                scrape_subject_papers(subject_code, subject_info, driver)
                time.sleep(3)  # Delay between subjects
        else:
            # Scrape single subject
            subject_code = args.subject
            if subject_code not in IGCSE_SUBJECTS:
                print(f"[ERROR] Unknown subject: {subject_code}")
                print(f"Available subjects: {', '.join(IGCSE_SUBJECTS.keys())}")
                sys.exit(1)
            
            scrape_subject_papers(subject_code, IGCSE_SUBJECTS[subject_code], driver)
    
    finally:
        driver.quit()
        print("\n[INFO] Done!")


if __name__ == '__main__':
    main()

