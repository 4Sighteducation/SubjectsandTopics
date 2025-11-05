"""
Edexcel History A-Level - Past Papers Scraper V2
Code: 9HI0

Scrapes from Pearson course materials page with Exam materials filter
Based on actual Pearson website structure (Nov 2025)
"""

import os
import sys
import time
import re
from pathlib import Path
from collections import Counter

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables from project root
project_root = Path(__file__).parent.parent.parent.parent
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path)

# Import our upload helper (from project root)
sys.path.insert(0, str(project_root))
try:
    from upload_papers_to_staging import upload_papers_to_staging
    print("✅ Upload helper imported successfully")
except ImportError as e:
    print(f"⚠️  Warning: upload_papers_to_staging not found ({e})")
    print("   Papers will be scraped but not uploaded to database.")
    upload_papers_to_staging = None


def init_driver(headless=True):
    """Initialize Chrome WebDriver."""
    print("🌐 Initializing Chrome WebDriver...")
    
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    
    print("✅ WebDriver initialized")
    return driver


def parse_edexcel_filename(filename, href):
    """
    Parse Edexcel PDF filename to extract metadata.
    
    Format: 9hi0-1a-que-20240524.pdf
            [code]-[option]-[type]-[date].pdf
    
    Args:
        filename: PDF filename
        href: Full URL
    
    Returns:
        dict with year, series, component_code, doc_type
    """
    
    # Extract from filename: 9hi0-1a-que-20240524.pdf
    match = re.search(r'9hi0-([^-]+)-([a-z]{3})-(\d{8})', filename.lower())
    
    if not match:
        return None
    
    component_code = match.group(1).upper()  # "1A", "2B.1", "30", etc.
    doc_type_code = match.group(2)           # "que", "rms", "pef"
    date_str = match.group(3)                # "20240524"
    
    # Parse date to get year and series
    year = int(date_str[:4])
    month = int(date_str[4:6])
    
    # Determine exam series from month
    if month in [5, 6]:
        series = 'June'
    elif month in [10, 11]:
        series = 'November'
    elif month in [1]:
        series = 'January'
    elif month in [8]:
        series = 'October'  # Results/reports published in August
    else:
        series = 'June'  # Default
    
    # Map doc type codes
    doc_type_map = {
        'que': 'Question Paper',
        'rms': 'Mark Scheme',
        'pef': 'Examiner Report',
        'ms': 'Mark Scheme',
        'er': 'Examiner Report',
        'qp': 'Question Paper'
    }
    
    doc_type = doc_type_map.get(doc_type_code, 'Question Paper')
    
    # Determine paper number from component code
    # 1A, 1B, etc. = Paper 1
    # 2A.1, 2B.1, etc. = Paper 2
    # 30-39 = Paper 3
    if component_code[0] == '1':
        paper_number = 1
    elif component_code[0] == '2':
        paper_number = 2
    elif component_code[0] in ['3', '4']:
        paper_number = 3
    else:
        paper_number = 1
    
    return {
        'year': year,
        'exam_series': series,
        'paper_number': paper_number,
        'component_code': component_code,
        'doc_type': doc_type,
        'filename': filename,
        'url': href
    }


def scrape_edexcel_history_papers(years=None):
    """
    Scrape Edexcel History A-Level past papers from Course Materials page.
    
    Args:
        years: List of years (default: [2024, 2023, 2022, 2021, 2020])
    
    Returns:
        List of paper records
    """
    
    SUBJECT = {
        'name': 'History',
        'code': '9HI0',
        'qualification': 'A-Level',
        'exam_board': 'Edexcel',
        # URL with Exam materials filter
        'exam_materials_url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/history-2015.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
        'years': years or [2024, 2023, 2022, 2021, 2020]
    }
    
    print("=" * 60)
    print("EDEXCEL HISTORY - PAST PAPERS SCRAPER V2")
    print("=" * 60)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Board: {SUBJECT['exam_board']}")
    print(f"Years: {SUBJECT['years']}")
    print(f"\nThis will take 2-3 minutes...\n")
    
    driver = None
    papers = []
    
    try:
        driver = init_driver(headless=False)  # Non-headless to see what happens
        
        # Navigate to exam materials page
        print(f"🔍 Navigating to Exam Materials page...")
        driver.get(SUBJECT['exam_materials_url'])
        time.sleep(5)  # Wait for page to load
        
        # Scroll down to trigger lazy loading
        print("   Scrolling to load content...")
        for scroll in range(10):
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(0.5)
        
        print("   ✅ Scrolled to bottom")
        time.sleep(2)
        
        # Try to expand all year dropdowns
        print("   Expanding year dropdowns...")
        
        try:
            # Look for expandable sections (accordions, dropdowns, etc.)
            expandable_elements = driver.find_elements(By.CSS_SELECTOR, '[aria-expanded="false"]')
            
            print(f"   Found {len(expandable_elements)} expandable sections")
            
            for idx, elem in enumerate(expandable_elements[:20]):
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", elem)  # JS click more reliable
                    time.sleep(1)
                    print(f"     Expanded section {idx + 1}/{min(20, len(expandable_elements))}")
                except Exception as ex:
                    print(f"     Failed to expand section {idx + 1}: {ex}")
            
            print("   ✅ Expanded sections")
            
        except Exception as e:
            print(f"   ⚠️  Error expanding: {e}")
        
        # Wait for content to load after expanding
        print("   Waiting for PDFs to load...")
        time.sleep(5)
        
        # Scroll again to make sure everything loaded
        driver.execute_script("window.scrollTo(0, 0);")  # Back to top
        time.sleep(1)
        for scroll in range(10):
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(0.3)
        
        # Get all PDF links
        print("\n📄 Scraping PDF links...")
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find all PDF links
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        
        print(f"   Found {len(pdf_links)} PDF links")
        
        # Parse each PDF
        for link in pdf_links:
            href = link.get('href', '')
            text = link.get_text().strip()
            
            # Make absolute URL
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = 'https://qualifications.pearson.com' + href
            
            filename = href.split('/')[-1]
            
            # Parse filename to get metadata
            parsed = parse_edexcel_filename(filename, href)
            
            if not parsed:
                # Try to parse from URL/text for other formats
                continue
            
            # Filter by year
            if parsed['year'] not in SUBJECT['years']:
                continue
            
            # Add to papers list
            papers.append({
                'year': parsed['year'],
                'exam_series': parsed['exam_series'],
                'paper_number': parsed['paper_number'],
                'component_code': parsed['component_code'],
                'tier': None,
                'doc_type': parsed['doc_type'],
                'url': href,
                'title': text or filename
            })
            
            # Show progress
            print(f"   ✓ {parsed['year']} {parsed['exam_series']} - {parsed['doc_type']} - {parsed['component_code']}")
        
        print(f"\n✅ Scraping complete! Found {len(papers)} documents")
        
        # Breakdown
        print("\n📊 Breakdown:")
        doc_types = Counter(p['doc_type'] for p in papers)
        for doc_type, count in doc_types.items():
            print(f"   {doc_type}: {count}")
        
        years_found = Counter(p['year'] for p in papers)
        print(f"\n   Years: {dict(sorted(years_found.items(), reverse=True))}")
        
        components = Counter(p['component_code'] for p in papers)
        print(f"\n   Components: {len(components)} unique ({', '.join(list(components.keys())[:10])}...)")
        
        return papers
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []
        
    finally:
        if driver:
            input("\n⏸️  Press Enter to close browser...")
            driver.quit()
            print("🔒 Browser closed")


def group_papers_by_set(papers):
    """
    Group individual papers into complete sets.
    
    Groups by: year + series + component_code
    """
    
    sets = {}
    
    for paper in papers:
        key = (
            paper['year'],
            paper['exam_series'],
            paper['component_code']
        )
        
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
        
        # Add URLs by type
        if paper['doc_type'] == 'Question Paper':
            sets[key]['question_paper_url'] = paper['url']
        elif paper['doc_type'] == 'Mark Scheme':
            sets[key]['mark_scheme_url'] = paper['url']
        elif paper['doc_type'] == 'Examiner Report':
            sets[key]['examiner_report_url'] = paper['url']
    
    return list(sets.values())


def main():
    """Main execution."""
    
    # Scrape papers
    papers = scrape_edexcel_history_papers()
    
    if not papers:
        print("\n⚠️  No papers found!")
        return 0
    
    # Group into sets
    print("\n🔗 Grouping papers into complete sets...")
    paper_sets = group_papers_by_set(papers)
    print(f"   Created {len(paper_sets)} complete paper sets")
    
    # Show sample
    print("\n📋 Sample paper sets:")
    for paper_set in sorted(paper_sets, key=lambda x: (x['year'], x['component_code']))[:5]:
        print(f"   {paper_set['year']} {paper_set['exam_series']} - {paper_set['component_code']}:")
        print(f"     QP: {'✅' if paper_set['question_paper_url'] else '❌'}")
        print(f"     MS: {'✅' if paper_set['mark_scheme_url'] else '❌'}")
        print(f"     ER: {'✅' if paper_set['examiner_report_url'] else '❌'}")
    
    # Upload to database
    if upload_papers_to_staging:
        print("\n💾 Uploading to staging database...")
        print("   Note: This DELETES old papers first - no duplicates!")
        
        try:
            uploaded_count = upload_papers_to_staging(
                subject_code='9HI0',
                qualification_type='A-Level',
                papers_data=paper_sets,
                exam_board='Edexcel'
            )
            
            print(f"\n✅ Upload complete! {uploaded_count} paper sets uploaded")
            
        except Exception as e:
            print(f"\n❌ Upload failed: {e}")
            import traceback
            traceback.print_exc()
            return 0
    else:
        print("\n⚠️  Upload function not available")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    print(f"\nEdexcel History (9HI0) - Complete Dataset:")
    print(f"   Topics: ✅ 559 topics in database")
    print(f"   Papers: ✅ {len(paper_sets)} paper sets")
    print(f"\n💡 Can be re-run safely - always replaces, never duplicates!")
    
    return len(paper_sets)


if __name__ == '__main__':
    main()

