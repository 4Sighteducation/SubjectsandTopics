"""
UNIVERSAL GCSE PAPER SCRAPER - Works for ALL Edexcel GCSE subjects
====================================================================

Handles multiple filename formats:
- Standard: 1bs0-01-que-20240516.pdf
- Tiered: 1aa0-1f-que-20230516.pdf (F/H for languages)
- Legacy: p73255-gcse-business-1bs0-01.pdf

Groups papers properly into sets:
- Question Paper + Mark Scheme + Examiner Report
- Grouped by: (year, series, paper_number, tier)

Usage:
    python universal-gcse-paper-scraper.py GCSE-Business
    python universal-gcse-paper-scraper.py GCSE-Arabic
    python universal-gcse-paper-scraper.py --all  # All subjects
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

# Setup paths
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

import importlib.util
upload_helper_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\upload_papers_to_staging.py")
spec = importlib.util.spec_from_file_location("upload_papers_to_staging", upload_helper_path)
upload_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload_module)
upload_papers_to_staging = upload_module.upload_papers_to_staging

# All GCSE subjects with their codes and URLs
GCSE_SUBJECTS = {
    'GCSE-Arabic': {
        'name': 'Arabic',
        'code': '1aa0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/arabic-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': True
    },
    'GCSE-Art': {
        'name': 'Art and Design',
        'code': '1ad0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/art-and-design-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': False
    },
    'GCSE-Astronomy': {
        'name': 'Astronomy',
        'code': '1as0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/astronomy-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': False
    },
    'GCSE-BiblicalHebrew': {
        'name': 'Biblical Hebrew',
        'code': '1bh0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/biblical-hebrew-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': True
    },
    'GCSE-Business': {
        'name': 'Business',
        'code': '1bs0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/business-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': False
    },
    'GCSE-Chinese': {
        'name': 'Chinese',
        'code': '1cn0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/chinese-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': True
    },
    'GCSE-Citizenship': {
        'name': 'Citizenship Studies',
        'code': '1cs0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/citizenship-studies-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': False
    },
    'GCSE-ComputerScience': {
        'name': 'Computer Science',
        'code': '1cp0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/computer-science-2020.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': False
    },
    'GCSE-DesignTech': {
        'name': 'Design and Technology',
        'code': '1dt0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/design-and-technology-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': False
    },
    'GCSE-Drama': {
        'name': 'Drama',
        'code': '1dr0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/drama-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': False
    },
    'GCSE-EnglishLang': {
        'name': 'English Language',
        'code': '1en0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/english-language-2015.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': False
    },
    'GCSE-EnglishLit': {
        'name': 'English Literature',
        'code': '1et0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/english-literature-2015.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': False
    },
    'GCSE-French': {
        'name': 'French',
        'code': '1fr0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/french-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': True
    },
    'GCSE-GeographyA': {
        'name': 'Geography A',
        'code': '1ga0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/geography-a-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': False
    },
    'GCSE-GeographyB': {
        'name': 'Geography B',
        'code': '1gb0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/geography-b-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': False
    },
    'GCSE-German': {
        'name': 'German',
        'code': '1gn0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/german-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': True
    },
    'GCSE-Greek': {
        'name': 'Greek',
        'code': '1gk0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/greek-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': True
    },
    'GCSE-Gujarati': {
        'name': 'Gujarati',
        'code': '1gu0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/gujarati-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': True
    },
    'GCSE-History': {
        'name': 'History',
        'code': '1hi0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/history-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': False
    },
    'GCSE-Italian': {
        'name': 'Italian',
        'code': '1in0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/italian-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': True
    },
    'GCSE-Japanese': {
        'name': 'Japanese',
        'code': '1ja0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/japanese-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': True
    },
    'GCSE-Mathematics': {
        'name': 'Mathematics',
        'code': '1ma1',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/mathematics-2015.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': True  # Foundation/Higher
    },
    'GCSE-Music': {
        'name': 'Music',
        'code': '1mu0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/music-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': False
    },
    'GCSE-Persian': {
        'name': 'Persian',
        'code': '1pn0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/persian-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': True
    },
    'GCSE-PE': {
        'name': 'Physical Education',
        'code': '1pe0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/physical-education-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': False
    },
    'GCSE-Portuguese': {
        'name': 'Portuguese',
        'code': '1pg0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/portuguese-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': True
    },
    'GCSE-Psychology': {
        'name': 'Psychology',
        'code': '1ps0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/psychology-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': False
    },
    'GCSE-ReligiousStudiesA': {
        'name': 'Religious Studies A',
        'code': '1ra0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/religious-studies-a-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': False
    },
    'GCSE-ReligiousStudiesB': {
        'name': 'Religious Studies B',
        'code': '1rb0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/religious-studies-b-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': False
    },
    'GCSE-Russian': {
        'name': 'Russian',
        'code': '1ru0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/russian-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': True
    },
    'GCSE-Science': {
        'name': 'Science (Double Award)',
        'code': '1sc0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/science-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': True
    },
    'GCSE-Spanish': {
        'name': 'Spanish',
        'code': '1sp0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/spanish-2016.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': True
    },
    'GCSE-Statistics': {
        'name': 'Statistics',
        'code': '1st0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/statistics-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': False
    },
    'GCSE-Turkish': {
        'name': 'Turkish',
        'code': '1tu0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/turkish-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': True
    },
    'GCSE-Urdu': {
        'name': 'Urdu',
        'code': '1ur0',
        'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/urdu-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'has_tiers': True
    }
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


def parse_filename_smart(filename, subject_code, has_tiers):
    """
    Smart filename parser - tries multiple patterns.
    
    Returns dict with:
        - paper_num: int
        - tier: 'F'|'H'|None
        - doc_type: 'Question Paper'|'Mark Scheme'|'Examiner Report'
        - year: int
        - month: int
        - component_code: str (e.g., '1BH' for Biology Paper 1 Higher)
    """
    filename_lower = filename.lower()
    
    # Document type codes
    doc_type_map = {
        'que': 'Question Paper',
        'qp': 'Question Paper',
        'rms': 'Mark Scheme',
        'ms': 'Mark Scheme',
        'msc': 'Mark Scheme',
        'pef': 'Examiner Report',
        'er': 'Examiner Report'
    }
    
    # Pattern 0: Combined Science special format - 1sc0-2bh-que-20220616.pdf
    # Format: {code}-{paper}{subject}{tier}-{type}-{date}
    # subject: b=biology, c=chemistry, p=physics
    # tier: f=foundation, h=higher
    if subject_code == '1sc0':
        pattern = r'1sc0-(\d)([bcp])([fh])-([a-z]{2,3})-(\d{8})'
        match = re.search(pattern, filename_lower)
        if match:
            paper_num = int(match.group(1))
            subject_letter = match.group(2).upper()
            tier = match.group(3).upper()
            doc_type_code = match.group(4)
            date_str = match.group(5)
            
            # Map subject letters
            subject_map = {'B': 'Biology', 'C': 'Chemistry', 'P': 'Physics'}
            subject_name = subject_map.get(subject_letter, '')
            
            # Component code format: 1BH = Paper 1, Biology, Higher
            component_code = f"{paper_num}{subject_letter}{tier}"
            
            return {
                'paper_num': paper_num,
                'tier': tier,
                'doc_type': doc_type_map.get(doc_type_code, 'Question Paper'),
                'year': int(date_str[:4]),
                'month': int(date_str[4:6]),
                'component_code': component_code,
                'subject_name': subject_name
            }
    
    # Pattern 1: Standard with tier - 1aa0-1f-que-20230516.pdf
    if has_tiers:
        pattern = rf'{subject_code}[-_](\d+)([fh])[-_]([a-z]{{2,3}})[-_](\d{{8}})'
        match = re.search(pattern, filename_lower)
        if match:
            return {
                'paper_num': int(match.group(1)),
                'tier': match.group(2).upper(),
                'doc_type': doc_type_map.get(match.group(3), 'Question Paper'),
                'year': int(match.group(4)[:4]),
                'month': int(match.group(4)[4:6])
            }
    
    # Pattern 2: Standard without tier - 1bs0-01-que-20240516.pdf
    pattern = rf'{subject_code}[-_](\d+)[-_]([a-z]{{2,3}})[-_](\d{{8}})'
    match = re.search(pattern, filename_lower)
    if match:
        return {
            'paper_num': int(match.group(1)),
            'tier': None,
            'doc_type': doc_type_map.get(match.group(2), 'Question Paper'),
            'year': int(match.group(3)[:4]),
            'month': int(match.group(3)[4:6])
        }
    
    # Pattern 3: Underscores instead of hyphens - 1bs0_01_que_20240516.pdf
    pattern = rf'{subject_code}_(\d+)_([a-z]{{2,3}})_(\d{{8}})'
    match = re.search(pattern, filename_lower)
    if match:
        return {
            'paper_num': int(match.group(1)),
            'tier': None,
            'doc_type': doc_type_map.get(match.group(2), 'Question Paper'),
            'year': int(match.group(3)[:4]),
            'month': int(match.group(3)[4:6])
        }
    
    # Pattern 4: Legacy format - p73255-gcse-business-1bs0-01.pdf
    pattern = rf'p\d+-gcse-.*-{subject_code}[-_](\d+)'
    match = re.search(pattern, filename_lower)
    if match:
        return {
            'paper_num': int(match.group(1)),
            'tier': None,
            'doc_type': 'Examiner Report',  # Legacy files are usually reports
            'year': 2024,  # Placeholder
            'month': 6
        }
    
    # Pattern 5: Just code and paper number - 1bs0-01.pdf
    pattern = rf'{subject_code}[-_](\d+)'
    match = re.search(pattern, filename_lower)
    if match:
        # Try to infer doc type from filename
        doc_type = 'Question Paper'
        if 'mark' in filename_lower or 'ms' in filename_lower:
            doc_type = 'Mark Scheme'
        elif 'report' in filename_lower or 'er' in filename_lower or 'pef' in filename_lower:
            doc_type = 'Examiner Report'
        
        return {
            'paper_num': int(match.group(1)),
            'tier': None,
            'doc_type': doc_type,
            'year': 2024,  # Placeholder
            'month': 6
        }
    
    return None


def scrape_subject_papers(subject_code, subject_info, driver):
    """Scrape papers for one GCSE subject."""
    
    print(f"\n{'=' * 80}")
    print(f"{subject_info['name']} ({subject_code})")
    print(f"Code: {subject_info['code']} | Tiers: {'Yes' if subject_info['has_tiers'] else 'No'}")
    print(f"{'=' * 80}\n")
    
    try:
        driver.get(subject_info['url'])
        print("[INFO] Waiting for page to load...")
        time.sleep(6)  # Increased initial wait for Angular
        
        # Expand all sections
        print("[INFO] Expanding sections...")
        try:
            expand = driver.find_elements(By.XPATH, "//*[contains(text(), 'EXPAND ALL')]")
            if expand:
                driver.execute_script("arguments[0].click();", expand[0])
                time.sleep(3)  # Wait for expansion
        except:
            pass
        
        # Scroll to load all content (triggers lazy loading)
        print("[INFO] Scrolling to load all PDFs...")
        for i in range(25):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)  # Increased wait between scrolls
            
            # Every 5 scrolls, wait a bit longer for Angular to catch up
            if i % 5 == 0:
                time.sleep(1)
        
        # Final wait for Angular to finish rendering
        print("[INFO] Waiting for Angular to finish rendering PDFs...")
        time.sleep(5)
        
        # Save page source for debugging
        page_source = driver.page_source
        debug_path = Path(__file__).parent / f"debug-{subject_code}-page.html"
        debug_path.write_text(page_source, encoding='utf-8')
        print(f"[DEBUG] Saved page source to {debug_path.name}")
        
        # Scrape PDF links
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Try multiple methods to find PDFs
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        print(f"[INFO] Found {len(pdf_links)} PDF links with regex")
        
        # Also try finding by href contains
        all_links = soup.find_all('a', href=True)
        pdf_links_alt = [l for l in all_links if '.pdf' in l.get('href', '').lower()]
        print(f"[INFO] Found {len(pdf_links_alt)} PDF links with string match")
        
        # Use whichever found more
        if len(pdf_links_alt) > len(pdf_links):
            pdf_links = pdf_links_alt
            print(f"[INFO] Using string match method")
        
        print(f"[INFO] Total PDF links to process: {len(pdf_links)}")
        
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
            parsed = parse_filename_smart(filename, subject_info['code'], subject_info['has_tiers'])
            
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
            
            # Use component_code from parsed data if available (for Combined Science)
            component_code = parsed.get('component_code', f"{parsed['paper_num']:02d}")
            
            papers.append({
                'year': parsed['year'],
                'exam_series': series,
                'paper_number': parsed['paper_num'],
                'component_code': component_code,
                'tier': parsed['tier'],
                'doc_type': parsed['doc_type'],
                'url': href,
                'filename': filename,
                'subject_name': parsed.get('subject_name', '')  # For Combined Science
            })
        
        print(f"[OK] Parsed {len(papers)} papers")
        if skipped > 0:
            print(f"[INFO] Skipped {skipped} PDFs (couldn't parse filename)")
        
        # Group into sets
        if papers:
            sets = {}
            for paper in papers:
                # Key includes tier if present
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
            
            print(f"[OK] Grouped into {len(paper_sets)} paper sets")
            
            # Show breakdown
            by_year = defaultdict(int)
            for ps in paper_sets:
                by_year[ps['year']] += 1
            
            print(f"[INFO] Breakdown by year:")
            for year in sorted(by_year.keys(), reverse=True):
                print(f"  {year}: {by_year[year]} sets")
            
            # Upload
            print(f"\n[INFO] Uploading to database...")
            uploaded = upload_papers_to_staging(
                subject_code=subject_code,
                qualification_type='GCSE',
                papers_data=paper_sets,
                exam_board='Edexcel'
            )
            
            print(f"\n✅ {subject_info['name']}: {uploaded} paper sets uploaded!")
            return uploaded
        else:
            print(f"[WARN] No papers found for {subject_info['name']}")
            return 0
            
    except Exception as e:
        print(f"\n[ERROR] {subject_info['name']}: {e}")
        import traceback
        traceback.print_exc()
        return 0


def main():
    """Main execution."""
    
    print("=" * 80)
    print("UNIVERSAL GCSE PAPER SCRAPER")
    print("=" * 80)
    print("Handles all Edexcel GCSE subjects with smart filename parsing\n")
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python universal-gcse-paper-scraper.py GCSE-Business")
        print("  python universal-gcse-paper-scraper.py GCSE-Arabic GCSE-Citizenship")
        print("  python universal-gcse-paper-scraper.py --all")
        print("\nAvailable subjects:")
        for code in sorted(GCSE_SUBJECTS.keys()):
            print(f"  {code}")
        sys.exit(1)
    
    # Determine which subjects to scrape
    if '--all' in sys.argv:
        subjects_to_scrape = sorted(GCSE_SUBJECTS.keys())
    else:
        subjects_to_scrape = [s for s in sys.argv[1:] if s in GCSE_SUBJECTS]
        
        # Check for invalid subjects
        invalid = [s for s in sys.argv[1:] if s not in GCSE_SUBJECTS and s != '--all']
        if invalid:
            print(f"[ERROR] Unknown subjects: {', '.join(invalid)}")
            print(f"\nAvailable: {', '.join(sorted(GCSE_SUBJECTS.keys()))}")
            sys.exit(1)
    
    print(f"Scraping {len(subjects_to_scrape)} subjects...\n")
    
    driver = None
    results = {'success': [], 'failed': [], 'no_papers': []}
    
    try:
        driver = init_driver(headless=True)
        
        for subject_code in subjects_to_scrape:
            subject_info = GCSE_SUBJECTS[subject_code]
            
            uploaded = scrape_subject_papers(subject_code, subject_info, driver)
            
            if uploaded > 0:
                results['success'].append({
                    'code': subject_code,
                    'name': subject_info['name'],
                    'sets': uploaded
                })
            elif uploaded == 0:
                results['no_papers'].append(subject_info['name'])
            else:
                results['failed'].append(subject_info['name'])
            
            time.sleep(1)  # Be nice to server
    
    finally:
        if driver:
            driver.quit()
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    if results['success']:
        total_sets = sum(r['sets'] for r in results['success'])
        print(f"\n✅ Successfully uploaded: {len(results['success'])}/{len(subjects_to_scrape)} subjects")
        print(f"   Total paper sets: {total_sets}")
        print(f"\n   Details:")
        for r in results['success']:
            print(f"   • {r['name']}: {r['sets']} sets")
    
    if results['no_papers']:
        print(f"\n⚠️  No papers found: {len(results['no_papers'])}")
        for name in results['no_papers']:
            print(f"   • {name}")
    
    if results['failed']:
        print(f"\n❌ Failed: {len(results['failed'])}")
        for name in results['failed']:
            print(f"   • {name}")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()

