"""
OCR GCSE - Universal Past Papers Scraper
Works for all OCR GCSE subjects

Uses Selenium to select filters and scrape past papers from OCR's past paper finder page

Usage:
    python scrape-ocr-gcse-papers-universal.py <subject_code> <subject_name> <qualification_filter> <tier_filter>
    
Example:
    python scrape-ocr-gcse-papers-universal.py J247 "Biology A" "Biology A - J247 (from 2016)" "Foundation"
"""

import os
import sys
import time
import re
from pathlib import Path
from collections import Counter

# Setup paths
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Try to use webdriver-manager if available
try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

# Try to use Firecrawl if available
try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

# Import upload helper
import importlib.util
upload_helper_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\upload_papers_to_staging.py")
spec = importlib.util.spec_from_file_location("upload_papers_to_staging", upload_helper_path)
upload_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload_module)
upload_papers_to_staging = upload_module.upload_papers_to_staging


def init_driver(headless=True, force_headless=False):
    """Initialize Chrome WebDriver.
    
    Args:
        headless: If True, try headless mode first (default: True)
        force_headless: If True, only use headless mode, don't fallback (default: False)
    """
    print("🌐 Initializing Chrome WebDriver...")
    
    # Headless mode configuration
    if headless:
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')  # Use new headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # Try with webdriver-manager first if available
            if WEBDRIVER_MANAGER_AVAILABLE:
                try:
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    driver.implicitly_wait(10)
                    print("✓ WebDriver initialized (headless, using webdriver-manager)")
                    return driver
                except Exception as e:
                    if force_headless:
                        raise
                    print(f"   webdriver-manager failed: {e}, trying standard method...")
            
            # Standard method
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(10)
            print("✓ WebDriver initialized (headless)")
            return driver
        except Exception as e:
            if force_headless:
                print(f"❌ Headless mode failed and force_headless=True: {e}")
                raise
            print(f"⚠️ Headless mode failed: {e}")
            print("   Trying non-headless mode...")
            headless = False  # Fall back to non-headless
    
    # Non-headless mode (either requested or fallback)
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    try:
        # Try with webdriver-manager if available (auto-downloads ChromeDriver)
        if WEBDRIVER_MANAGER_AVAILABLE:
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                driver.implicitly_wait(10)
                print("✓ WebDriver initialized (non-headless, using webdriver-manager)")
                return driver
            except Exception as e:
                print(f"   webdriver-manager failed: {e}, trying standard method...")
        
        # Standard method
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        print("✓ WebDriver initialized (non-headless)")
        return driver
    except Exception as e:
        print(f"❌ Failed to initialize WebDriver: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure Chrome browser is installed")
        print("2. Check ChromeDriver version matches Chrome version")
        print("3. Try running: pip install --upgrade selenium")
        print("4. Or install webdriver-manager: pip install webdriver-manager")
        raise


def expand_all_accordions(driver):
    """Expand all accordions to reveal paper links."""
    print("   Expanding accordions...")
    expanded_count = 0
    
    # Wait for accordions to appear
    time.sleep(2)
    
    # OCR uses jQuery UI accordions - find all h3 and h4 headings that are accordion headers
    accordion_selectors = [
        "h3.level-1.heading",
        "h4.level-2.heading",
        ".ui-accordion-header",
        ".accordion-header",
        "[data-toggle='collapse']"
    ]
    
    for selector in accordion_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                try:
                    # Scroll into view
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                    time.sleep(0.2)
                    
                    # Click to expand
                    driver.execute_script("arguments[0].click();", elem)
                    time.sleep(0.5)
                    expanded_count += 1
                except:
                    pass
        except:
            pass
    
    print(f"   ✓ Expanded {expanded_count} accordions")
    return expanded_count


def scrape_papers(subject_code, subject_name, qualification_filter, tier_filter=None, headless=True, force_headless=False):
    """Scrape papers from OCR past paper finder page."""
    
    print("=" * 80)
    print("OCR GCSE - PAPERS SCRAPER")
    print("=" * 80)
    print(f"\nSubject: {subject_name}")
    print(f"Code: {subject_code}")
    print(f"Qualification: {qualification_filter}")
    if tier_filter:
        print(f"Tier: {tier_filter}")
    print(f"\nThis will take 2-3 minutes...\n")
    
    driver = None
    papers = []
    base_url = "https://www.ocr.org.uk/qualifications/past-paper-finder/"
    
    try:
        driver = init_driver(headless=headless, force_headless=force_headless)
        
        # Navigate to past paper finder
        print(f"📂 Navigating to past paper finder...")
        driver.get(base_url)
        time.sleep(5)
        
        # Step 1: Select filters - OCR uses AJAX dropdowns with specific IDs
        print("\n📋 Step 1: Selecting filters...")
        print("   OCR uses AJAX dropdowns - waiting for dynamic loading...")
        
        # Wait for page to fully load
        time.sleep(5)
        
        # Step 1: Select "Type of Qualification" dropdown (id="pp-qual-type") - GCSE
        try:
            qual_type_select = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "pp-qual-type"))
            )
            select = Select(qual_type_select)
            select.select_by_value("3828")  # "GCSE"
            print("   ✓ Selected 'GCSE'")
            time.sleep(3)  # Wait for AJAX to populate Qualification dropdown
        except Exception as e:
            print(f"   ⚠️ Failed to select Type of Qualification: {e}")
        
        # Step 2: Select Qualification dropdown (id="pp-qual")
        try:
            qual_select = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "pp-qual"))
            )
            # Wait for options to be populated (not just the select element)
            WebDriverWait(driver, 15).until(
                lambda d: len(Select(d.find_element(By.ID, "pp-qual")).options) > 1
            )
            
            select = Select(qual_select)
            # Try to find the qualification option - multiple strategies
            found = False
            
            # Strategy 1: Exact match (or contains both ways)
            for option in select.options:
                opt_text = option.text.lower()
                qual_filter_lower = qualification_filter.lower()
                if qual_filter_lower in opt_text or opt_text in qual_filter_lower:
                    select.select_by_value(option.get_attribute("value"))
                    print(f"   ✓ Selected '{option.text}'")
                    found = True
                    break
            
            # Strategy 2: Match by subject code (e.g., "J247")
            if not found and subject_code:
                code_pattern = subject_code.lower()
                for option in select.options:
                    if code_pattern in option.text.lower():
                        select.select_by_value(option.get_attribute("value"))
                        print(f"   ✓ Selected '{option.text}' (matched by code {subject_code})")
                        found = True
                        break
            
            # Strategy 3: Partial match by subject name
            if not found:
                # Clean subject name (remove "A", "B" suffixes for matching)
                clean_name = subject_name.lower().replace(" a", "").replace(" b", "").strip()
                for option in select.options:
                    opt_text = option.text.lower()
                    # Check if subject name appears in option text
                    if clean_name in opt_text or any(word in opt_text for word in clean_name.split() if len(word) > 3):
                        # Also check if code matches
                        if subject_code and subject_code.lower() in opt_text:
                            select.select_by_value(option.get_attribute("value"))
                            print(f"   ✓ Selected '{option.text}' (matched by name + code)")
                            found = True
                            break
            
            if not found:
                print("   ⚠️ Could not find qualification option")
                print(f"   Looking for: '{qualification_filter}'")
                print(f"   Subject code: {subject_code}")
                print(f"   Available options (first 15):")
                for opt in select.options[1:16]:  # Skip first "Which qualification?" option
                    print(f"     - {opt.text}")
            
            time.sleep(5)  # Wait for Level dropdown to populate (if needed)
        except Exception as e:
            print(f"   ⚠️ Failed to select Qualification: {e}")
        
        # Step 3: Select Level if dropdown is enabled (some GCSE subjects need this)
        try:
            level_select = driver.find_element(By.ID, "pp-level")
            if level_select.is_enabled() and not level_select.get_attribute("disabled"):
                select_level = Select(level_select)
                # Wait for options to populate
                WebDriverWait(driver, 10).until(
                    lambda d: len(Select(d.find_element(By.ID, "pp-level")).options) > 1
                )
                # Select "GCSE" (not "GCSE (Short course)")
                for option in select_level.options:
                    if option.get_attribute("value") != "0" and "Short course" not in option.text:
                        select_level.select_by_value(option.get_attribute("value"))
                        print(f"   ✓ Selected '{option.text}'")
                        break
                time.sleep(3)  # Wait for results to load
        except Exception as e:
            # Level dropdown might be hidden/disabled for some subjects - that's OK
            pass
        
        # Step 4: Wait for results to appear in .finder-results div
        print("\n⏳ Waiting for results to load...")
        try:
            # Wait for loading indicator to disappear
            WebDriverWait(driver, 20).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".loading-documents"))
            )
            
            # Wait for results to appear
            WebDriverWait(driver, 20).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, ".finder-results .multi-accordion, .finder-results .resource-list")
            )
            
            print("   ✓ Results loaded")
        except TimeoutException:
            print("   ⚠️ Results did not appear - checking page state...")
            # Check if loading indicator is still there
            loading = driver.find_elements(By.CSS_SELECTOR, ".loading-documents")
            if loading:
                print("   ⚠️ Still loading...")
            else:
                print("   ⚠️ No results found")
        
        time.sleep(3)  # Extra wait for content to settle
        
        # Step 5: Expand all accordions
        print("\n📂 Step 2: Expanding accordions...")
        expand_all_accordions(driver)
        
        # Scroll to load any lazy content
        print("   Scrolling to load content...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Step 6: Scrape PDF links using exact OCR structure
        print("\n📥 Step 3: Scraping PDF links...")
        
        # Save page HTML for debugging
        try:
            debug_dir = Path(__file__).parent / "debug-output"
            debug_dir.mkdir(exist_ok=True)
            with open(debug_dir / f"ocr-gcse-{subject_code}-after-filters.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"   💾 Saved page HTML to debug-output/ocr-gcse-{subject_code}-after-filters.html")
        except:
            pass
        
        # Get the finder-results div content (results are loaded via AJAX)
        try:
            finder_results = driver.find_element(By.CSS_SELECTOR, ".finder-results")
            results_html = finder_results.get_attribute('innerHTML')
            print(f"   Found finder-results div ({len(results_html)} chars)")
        except:
            print("   ⚠️ Could not find .finder-results div")
            results_html = driver.page_source
        
        soup = BeautifulSoup(results_html, 'html.parser')
        
        # Strategy 1: Find resource lists (preferred method)
        resource_lists = soup.find_all('ul', class_='resource-list')
        print(f"   Found {len(resource_lists)} resource lists")
        
        papers = []
        
        if resource_lists:
            # Use structured approach
            for resource_list in resource_lists:
                # Find the parent accordion to get year/series
                parent_accordion = resource_list.find_parent('div', class_='level-2')
                year_series = ""
                
                if parent_accordion:
                    # Find the h4 heading before this div (contains year/series)
                    prev_sibling = parent_accordion.find_previous_sibling('h4', class_='level-2')
                    if prev_sibling:
                        year_series = prev_sibling.get_text().strip()
                
                # Find all PDF links in this resource list
                pdf_items = resource_list.find_all('li', class_='resource pdf')
                
                for item in pdf_items:
                    link = item.find('a', href=True)
                    if not link:
                        continue
                    
                    href = link.get('href', '')
                    text = link.get_text().strip()
                    
                    # Get unit code (paper number)
                    unit_code_span = item.find('span', class_='unit-code')
                    unit_code = unit_code_span.get_text().strip() if unit_code_span else ""
                    
                    # Make absolute URL
                    if href.startswith('//'):
                        href = 'https:' + href
                    elif href.startswith('/'):
                        href = 'https://www.ocr.org.uk' + href
                    
                    # Skip if not a PDF
                    if not href.lower().endswith('.pdf'):
                        continue
                    
                    # Parse metadata
                    parsed = parse_paper_metadata_ocr(href, text, year_series, unit_code, subject_code, tier_filter)
                    
                    if parsed:
                        papers.append(parsed)
                        print(f"   ✓ {parsed['year']} {parsed['exam_series']} - Paper {parsed['paper_number']} - {parsed['doc_type']}")
        else:
            # Strategy 2: Fallback - find all PDF links and try to extract metadata
            print("   ⚠️ No resource lists found, using fallback method...")
            all_pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
            print(f"   Found {len(all_pdf_links)} PDF links")
            
            # Try to find year/series from page structure
            year_headings = soup.find_all(['h4', 'h3'], string=re.compile(r'\d{4}'))
            
            for link in all_pdf_links:
                href = link.get('href', '')
                text = link.get_text().strip()
                
                # Make absolute URL
                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = 'https://www.ocr.org.uk' + href
                
                # Find nearest year heading
                year_series = ""
                parent = link.find_parent(['div', 'section', 'li'])
                if parent:
                    for heading in year_headings:
                        if parent.find_parent() == heading.find_parent() or heading in parent.find_all():
                            year_series = heading.get_text().strip()
                            break
                
                # Try to find unit code nearby
                unit_code = ""
                if parent:
                    unit_code_span = parent.find('span', class_='unit-code')
                    if unit_code_span:
                        unit_code = unit_code_span.get_text().strip()
                
                # Parse metadata
                parsed = parse_paper_metadata_ocr(href, text, year_series, unit_code, subject_code, tier_filter)
                
                if parsed:
                    papers.append(parsed)
                    print(f"   ✓ {parsed['year']} {parsed['exam_series']} - Paper {parsed['paper_number']} - {parsed['doc_type']}")
        
        print(f"\n✓ Found {len(papers)} papers")
        
        if papers:
            years = Counter(p['year'] for p in papers)
            print(f"\n   Years: {dict(sorted(years.items(), reverse=True))}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            print("\n🔒 Closing browser...")
            driver.quit()
            print("✓ Browser closed")
    
    return papers


def parse_paper_metadata_ocr(href, link_text, year_series_text, unit_code, subject_code, tier_filter=None):
    """Parse paper metadata from OCR's HTML structure."""
    
    # Extract year and series from year_series_text (e.g., "2024 - June series")
    year = None
    series = "June"  # Default
    
    if year_series_text:
        year_match = re.search(r'(\d{4})', year_series_text)
        if year_match:
            year = int(year_match.group(1))
        
        series_match = re.search(r'(June|November|January|May|October)', year_series_text, re.IGNORECASE)
        if series_match:
            series = series_match.group(1).capitalize()
    
    # Extract from URL if not found
    if not year:
        year_match = re.search(r'(\d{4})', href)
        if year_match:
            year = int(year_match.group(1))
    
    if not year:
        from datetime import datetime
        current_year = datetime.now().year
        year = current_year
    
    # Extract paper number from unit_code (e.g., "J247/01" -> 1)
    paper_number = None
    component_code = None
    
    if unit_code:
        # Pattern: J247/01 or J247/01/02/03
        match = re.search(rf'{subject_code}[/\-_](\d+)', unit_code, re.IGNORECASE)
        if match:
            paper_number = int(match.group(1))
            component_code = f"{paper_number:02d}"
    
    # Fallback: try to extract from URL or link text
    if not paper_number:
        code_pattern = rf'{subject_code}[/\-_](\d+)'
        match = re.search(code_pattern, href, re.IGNORECASE)
        if not match:
            match = re.search(code_pattern, link_text, re.IGNORECASE)
        
        if match:
            paper_number = int(match.group(1))
            component_code = f"{paper_number:02d}"
    
    # Default if still not found
    if not paper_number:
        paper_number = 1
        component_code = "01"
    
    # Determine document type from link text
    doc_type = "Question Paper"  # Default
    link_lower = link_text.lower()
    
    if 'mark scheme' in link_lower:
        doc_type = "Mark Scheme"
    elif 'examiner' in link_lower or 'examiners' in link_lower:
        doc_type = "Examiner Report"
    elif 'question paper' in link_lower or 'question' in link_lower:
        doc_type = "Question Paper"
    
    # Determine tier from link text or filter
    tier = None
    if tier_filter:
        tier = tier_filter
    elif 'foundation' in link_lower:
        tier = "Foundation"
    elif 'higher' in link_lower:
        tier = "Higher"
    
    return {
        'year': year,
        'exam_series': series,
        'paper_number': paper_number,
        'component_code': component_code,
        'tier': tier,
        'doc_type': doc_type,
        'url': href,
        'subject_code': subject_code
    }


def group_papers(papers, min_year=2019):
    """Group into sets by year + series + paper number.
    
    Args:
        papers: List of paper dictionaries
        min_year: Minimum year to include (default: 2019)
    """
    sets = {}
    
    for paper in papers:
        # Filter by year
        if paper['year'] < min_year:
            continue
        
        key = (paper['year'], paper['exam_series'], paper['paper_number'], paper.get('tier'))
        
        if key not in sets:
            sets[key] = {
                'year': paper['year'],
                'exam_series': paper['exam_series'],
                'paper_number': paper['paper_number'],
                'component_code': paper['component_code'],
                'tier': paper.get('tier'),
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
    """Main execution."""
    
    # Force UTF-8 output
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    # Parse arguments
    if len(sys.argv) < 4:
        print("Usage: python scrape-ocr-gcse-papers-universal.py <subject_code> <subject_name> <qualification_filter> [tier_filter] [options]")
        print("\nExample:")
        print('  python scrape-ocr-gcse-papers-universal.py J247 "Biology A" "Biology A - J247 (from 2016)"')
        print('  python scrape-ocr-gcse-papers-universal.py J247 "Biology A" "Biology A - J247 (from 2016)" "Foundation"')
        print('  python scrape-ocr-gcse-papers-universal.py J247 "Biology A" "Biology A - J247 (from 2016)" --visible')
        print('  python scrape-ocr-gcse-papers-universal.py J247 "Biology A" "Biology A - J247 (from 2016)" --min-year 2019')
        print("\nOptions:")
        print("  --headless : Run in headless mode (no browser window) - DEFAULT")
        print("  --visible  : Show browser window (for debugging)")
        print("  --min-year : Minimum year to include (default: 2019)")
        sys.exit(1)
    
    subject_code = sys.argv[1]
    subject_name = sys.argv[2]
    qualification_filter = sys.argv[3]
    tier_filter = None
    use_visible = '--visible' in sys.argv
    use_headless = '--headless' in sys.argv or not use_visible  # Default to headless unless --visible is specified
    
    # Check for --min-year argument
    min_year = 2019  # Default
    if '--min-year' in sys.argv:
        try:
            idx = sys.argv.index('--min-year')
            if idx + 1 < len(sys.argv):
                min_year = int(sys.argv[idx + 1])
        except (ValueError, IndexError):
            pass
    
    # Check if 4th arg is tier filter or option flag
    if len(sys.argv) > 4 and sys.argv[4] not in ['--visible', '--headless', '--min-year']:
        tier_filter = sys.argv[4]
    
    if use_headless:
        print("🔇 Running in HEADLESS mode (browser will not be visible)")
    else:
        print("👁️  Running in VISIBLE mode (browser window will be shown)")
    
    papers = scrape_papers(subject_code, subject_name, qualification_filter, tier_filter, headless=use_headless)
    
    if not papers:
        print("\n⚠️ No papers found!")
        return 0
    
    # Group (filter by min_year)
    print(f"\n📦 Grouping into sets ({min_year} onwards only)...")
    sets = group_papers(papers, min_year=min_year)
    print(f"   Created {len(sets)} complete paper sets (2019+)")
    
    # Upload
    print("\n📤 Uploading to database...")
    
    try:
        uploaded = upload_papers_to_staging(
            subject_code=subject_code,
            qualification_type='GCSE',
            papers_data=sets,
            exam_board='OCR'
        )
        
        print(f"\n✓ Uploaded {uploaded} paper sets!")
        
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print(f"✅ {subject_name.upper()} PAPERS COMPLETE!")
    print("=" * 80)
    print(f"\nTotal: {len(sets)} paper sets")
    
    return len(sets)


if __name__ == '__main__':
    main()

