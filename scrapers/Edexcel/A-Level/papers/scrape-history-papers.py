"""
Edexcel History A-Level - Past Papers Scraper
Code: 9HI0

Scrapes past papers from Pearson qualifications website
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

# Load environment variables
load_dotenv()

# Import our upload helper
try:
    from upload_papers_to_staging import upload_papers_to_staging
except ImportError:
    print("Warning: upload_papers_to_staging not found. Will only scrape papers.")
    upload_papers_to_staging = None


def init_driver(headless=True):
    """Initialize Chrome WebDriver with options."""
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


def scrape_edexcel_history_papers(years=None):
    """
    Scrape Edexcel History A-Level past papers.
    
    Args:
        years: List of years to scrape (default: last 5 years)
    
    Returns:
        List of paper data dictionaries
    """
    
    SUBJECT = {
        'name': 'History',
        'code': '9HI0',
        'qualification': 'A-Level',
        'exam_board': 'Edexcel',
        'papers_url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/history-2015.html',
        'years': years or [2024, 2023, 2022, 2021, 2020]
    }
    
    print("=" * 60)
    print("EDEXCEL HISTORY - PAST PAPERS SCRAPER")
    print("=" * 60)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Board: {SUBJECT['exam_board']}")
    print(f"Years: {SUBJECT['years']}")
    print(f"\nThis will take 3-5 minutes...\n")
    
    driver = None
    papers = []
    
    try:
        driver = init_driver(headless=True)
        
        # Navigate to subject page first
        print(f"🔍 Navigating to {SUBJECT['name']} page...")
        driver.get(SUBJECT['papers_url'])
        time.sleep(2)
        
        # Try to find "Past papers" or "Assessment resources" link
        print("   Looking for past papers section...")
        
        try:
            # Look for past papers tab or link
            past_papers_keywords = ['past papers', 'past-papers', 'assessment']
            
            # Check all links on the page
            links = driver.find_elements(By.TAG_NAME, 'a')
            past_papers_link = None
            
            for link in links:
                link_text = link.text.lower()
                link_href = link.get_attribute('href') or ''
                
                if any(keyword in link_text or keyword in link_href.lower() for keyword in past_papers_keywords):
                    past_papers_link = link
                    break
            
            if past_papers_link:
                print(f"   Found link: {past_papers_link.text}")
                past_papers_link.click()
                time.sleep(3)
            else:
                # Try direct URL pattern for past papers
                past_papers_url = 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/history-2015/assessment.html'
                print(f"   Trying direct URL: {past_papers_url}")
                driver.get(past_papers_url)
                time.sleep(3)
                
        except Exception as e:
            print(f"   ⚠️  Error navigating to past papers: {e}")
            print("   Continuing with current page...")
        
        # Now scrape for PDF links
        print("\n📄 Scraping PDF links...")
        
        # Get page source
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find all PDF links
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        
        print(f"   Found {len(pdf_links)} PDF links on page")
        
        if len(pdf_links) == 0:
            # Try clicking through tabs or sections
            print("   No PDFs found directly. Looking for tabs/accordions...")
            
            try:
                # Look for expandable sections
                expandable_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[aria-expanded="false"]')
                
                for button in expandable_buttons[:10]:  # Limit to first 10 to avoid infinite loops
                    try:
                        button.click()
                        time.sleep(0.5)
                    except:
                        pass
                
                # Refresh page source
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
                
                print(f"   Found {len(pdf_links)} PDF links after expanding sections")
                
            except Exception as e:
                print(f"   ⚠️  Error expanding sections: {e}")
        
        # Parse PDF links
        for link in pdf_links:
            href = link.get('href', '')
            text = link.get_text().strip()
            
            # Make absolute URL
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = 'https://qualifications.pearson.com' + href
            
            # Extract year from filename or link text
            year_match = re.search(r'(20\d\d)', href + ' ' + text)
            if not year_match:
                continue
            
            year = int(year_match.group(1))
            
            # Filter by requested years
            if year not in SUBJECT['years']:
                continue
            
            # Extract exam series (June, November, etc.)
            series = 'June'  # Default
            if any(month in href.lower() or month in text.lower() for month in ['jan', 'january', 'winter']):
                series = 'January'
            elif any(month in href.lower() or month in text.lower() for month in ['nov', 'november']):
                series = 'November'
            elif any(month in href.lower() or month in text.lower() for month in ['oct', 'october']):
                series = 'October'
            
            # Determine paper type
            doc_type = 'Question Paper'
            if any(term in href.lower() or term in text.lower() for term in ['mark scheme', 'ms', 'markscheme', 'marking']):
                doc_type = 'Mark Scheme'
            elif any(term in href.lower() or term in text.lower() for term in ['examiner', 'report', 'er']):
                doc_type = 'Examiner Report'
            
            # Extract paper number
            paper_match = re.search(r'paper[\s\-_]*(\d+)', text.lower() + href.lower())
            paper_number = int(paper_match.group(1)) if paper_match else 1
            
            # Extract component code (for History: 1A, 1B, 2A, etc.)
            component_match = re.search(r'(\d+[A-Z])', text.upper())
            component_code = component_match.group(1) if component_match else None
            
            # Create paper record
            paper = {
                'year': year,
                'exam_series': series,
                'paper_number': paper_number,
                'component_code': component_code,
                'tier': None,  # History doesn't have tiers
                'question_paper_url': href if doc_type == 'Question Paper' else None,
                'mark_scheme_url': href if doc_type == 'Mark Scheme' else None,
                'examiner_report_url': href if doc_type == 'Examiner Report' else None,
                'doc_type': doc_type,
                'title': text,
                'url': href
            }
            
            papers.append(paper)
            
            # Show progress
            print(f"   ✓ {year} {series} - {doc_type} - Paper {paper_number}{f' ({component_code})' if component_code else ''}")
        
        print(f"\n✅ Scraping complete! Found {len(papers)} documents")
        
        # Group papers by year/series/paper number
        print("\n📊 Breakdown:")
        doc_types = Counter(p['doc_type'] for p in papers)
        for doc_type, count in doc_types.items():
            print(f"   {doc_type}: {count}")
        
        years_found = Counter(p['year'] for p in papers)
        print(f"\n   Years: {dict(sorted(years_found.items()))}")
        
        return papers
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []
        
    finally:
        if driver:
            driver.quit()
            print("\n🔒 Browser closed")


def group_papers_by_set(papers):
    """
    Group individual papers into complete paper sets.
    
    Args:
        papers: List of individual paper records
    
    Returns:
        List of grouped paper sets
    """
    
    # Group by year, series, paper_number, component_code
    sets = {}
    
    for paper in papers:
        key = (
            paper['year'],
            paper['exam_series'],
            paper['paper_number'],
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
        
        # Add URLs based on doc_type
        if paper['doc_type'] == 'Question Paper':
            sets[key]['question_paper_url'] = paper['url']
        elif paper['doc_type'] == 'Mark Scheme':
            sets[key]['mark_scheme_url'] = paper['url']
        elif paper['doc_type'] == 'Examiner Report':
            sets[key]['examiner_report_url'] = paper['url']
    
    return list(sets.values())


def main():
    """Main execution function."""
    
    # Scrape papers
    papers = scrape_edexcel_history_papers()
    
    if not papers:
        print("\n⚠️  No papers found!")
        return 0
    
    # Group into sets
    print("\n🔗 Grouping papers into complete sets...")
    paper_sets = group_papers_by_set(papers)
    print(f"   Created {len(paper_sets)} complete paper sets")
    
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
        print("\n⚠️  Upload function not available - papers not uploaded to database")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    print(f"\nEdexcel History (9HI0) - Complete Dataset:")
    print(f"   Topics: Run scrape-edexcel-history.js")
    print(f"   Papers: {len(paper_sets)} complete paper sets")
    print(f"\nCheck Supabase:")
    print(f"   - staging_aqa_topics: History topics (with exam_board='Edexcel')")
    print(f"   - staging_aqa_exam_papers: {len(paper_sets)} records")
    print(f"\n💡 Can be re-run safely - always replaces, never duplicates!")
    
    return len(paper_sets)


if __name__ == '__main__':
    main()

