"""
OCR A-Level - Universal Past Papers Scraper
Works for all OCR A-Level subjects

Uses Selenium to select filters and scrape past papers from OCR's past paper finder page

Usage:
    python scrape-ocr-papers-universal.py <subject_code> <subject_name> <qualification_filter> <level_filter>
    
Example:
    python scrape-ocr-papers-universal.py H407 "Ancient History" "Ancient History - H007, H407 (from 2017)" "A Level"
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


def select_filter_option_js(driver, filter_label, option_text, wait_time=5):
    """Select dropdown option using JavaScript (more reliable for custom dropdowns)."""
    try:
        print(f"   Selecting '{option_text}' in '{filter_label}'...")
        time.sleep(2)  # Wait for page to settle
        
        # Strategy: Use JavaScript to find and select dropdowns
        js_code = f"""
        // Find all select elements
        var selects = document.querySelectorAll('select');
        var found = false;
        
        for (var i = 0; i < selects.length; i++) {{
            var select = selects[i];
            var label = select.closest('*').textContent || '';
            
            // Check if this select is for the filter we want
            if (label.toLowerCase().includes('{filter_label.lower()}')) {{
                // Try to find and select the option
                for (var j = 0; j < select.options.length; j++) {{
                    var opt = select.options[j];
                    if (opt.text.toLowerCase().includes('{option_text.lower()}') || 
                        '{option_text.lower()}'.includes(opt.text.toLowerCase())) {{
                        select.value = opt.value;
                        select.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        select.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        found = true;
                        return true;
                    }}
                }}
            }}
        }}
        
        // If no select found, try clicking on custom dropdowns
        var labels = document.querySelectorAll('label, *[class*="label"], *[class*="Label"]');
        for (var i = 0; i < labels.length; i++) {{
            var label = labels[i];
            if (label.textContent.toLowerCase().includes('{filter_label.lower()}')) {{
                // Find nearby clickable element
                var parent = label.closest('div, form, fieldset') || label.parentElement;
                var triggers = parent.querySelectorAll('button, div[role="button"], *[class*="select"], *[class*="dropdown"]');
                
                for (var j = 0; j < triggers.length; j++) {{
                    triggers[j].click();
                    // Wait a bit for dropdown to open
                    await new Promise(r => setTimeout(r, 500));
                    
                    // Find option and click
                    var options = document.querySelectorAll('*[role="option"], li, div[class*="option"]');
                    for (var k = 0; k < options.length; k++) {{
                        if (options[k].textContent.toLowerCase().includes('{option_text.lower()}')) {{
                            options[k].click();
                            found = true;
                            return true;
                        }}
                    }}
                }}
            }}
        }}
        
        return found;
        """
        
        result = driver.execute_script(js_code)
        if result:
            print(f"   ✓ Selected '{option_text}' (JavaScript)")
            time.sleep(wait_time)
            return True
        else:
            print(f"   ⚠️ JavaScript selection failed, trying alternative...")
            return False
            
    except Exception as e:
        print(f"   ⚠️ JavaScript error: {e}")
        return False


def select_filter_option(driver, filter_label, option_text, wait_time=5):
    """Select an option from a filter dropdown (handles custom JS dropdowns)."""
    try:
        print(f"   Looking for '{filter_label}' filter...")
        time.sleep(1)  # Wait for page to settle
        
        # First try JavaScript approach
        if select_filter_option_js(driver, filter_label, option_text, wait_time):
            return True
        
        # Strategy 1: Try standard HTML select element
        try:
            from selenium.webdriver.support.ui import Select
            selects = driver.find_elements(By.TAG_NAME, "select")
            for select_elem in selects:
                try:
                    # Check if label is nearby
                    parent = select_elem.find_element(By.XPATH, "./ancestor::*[contains(text(), '{}')]".format(filter_label))
                    select = Select(select_elem)
                    # Try exact match
                    try:
                        select.select_by_visible_text(option_text)
                        print(f"   ✓ Selected '{option_text}' in '{filter_label}' (select)")
                        time.sleep(wait_time)
                        return True
                    except:
                        # Try partial match
                        for opt in select.options:
                            if option_text.lower() in opt.text.lower() or opt.text.lower() in option_text.lower():
                                select.select_by_visible_text(opt.text)
                                print(f"   ✓ Selected '{opt.text}' in '{filter_label}' (select, partial)")
                                time.sleep(wait_time)
                                return True
                except:
                    continue
        except:
            pass
        
        # Strategy 2: Custom dropdown - click to open, then click option
        # Look for clickable elements (buttons, divs, spans) that might be dropdowns
        try:
            # Find label, then look for clickable element after it
            label_xpath = f"//*[contains(text(), '{filter_label}')]"
            labels = driver.find_elements(By.XPATH, label_xpath)
            
            for label in labels:
                try:
                    # Find the dropdown trigger (button, div, etc.) near the label
                    parent = label.find_element(By.XPATH, "./ancestor::*[contains(@class, 'dropdown') or contains(@class, 'select') or contains(@role, 'combobox')]")
                    
                    # Click to open dropdown
                    trigger = parent.find_element(By.XPATH, ".//button | .//div[@role='button'] | .//*[contains(@class, 'trigger')] | .//*[contains(@class, 'select')]")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", trigger)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", trigger)
                    time.sleep(1)  # Wait for dropdown to open
                    
                    # Find and click the option
                    option_xpath = f"//*[contains(text(), '{option_text}')]"
                    options = driver.find_elements(By.XPATH, option_xpath)
                    
                    for opt in options:
                        try:
                            # Check if it's visible and clickable
                            if opt.is_displayed():
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", opt)
                                time.sleep(0.3)
                                driver.execute_script("arguments[0].click();", opt)
                                print(f"   ✓ Selected '{option_text}' in '{filter_label}' (custom dropdown)")
                                time.sleep(wait_time)
                                return True
                        except:
                            continue
                except:
                    continue
        except:
            pass
        
        # Strategy 3: Use JavaScript to set value directly
        try:
            # Try to find by data attributes or IDs
            js_code = f"""
            var selects = document.querySelectorAll('select');
            for (var i = 0; i < selects.length; i++) {{
                var label = selects[i].closest('*').textContent || '';
                if (label.toLowerCase().includes('{filter_label.lower()}')) {{
                    var options = selects[i].options;
                    for (var j = 0; j < options.length; j++) {{
                        if (options[j].text.toLowerCase().includes('{option_text.lower()}')) {{
                            selects[i].value = options[j].value;
                            selects[i].dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                    }}
                }}
            }}
            return false;
            """
            result = driver.execute_script(js_code)
            if result:
                print(f"   ✓ Selected '{option_text}' in '{filter_label}' (JavaScript)")
                time.sleep(wait_time)
                return True
        except:
            pass
        
        # Strategy 4: Try clicking anywhere near the label and looking for options
        try:
            labels = driver.find_elements(By.XPATH, f"//*[contains(text(), '{filter_label}')]")
            for label in labels:
                try:
                    # Click near the label to see if it opens something
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", label)
                    time.sleep(0.5)
                    
                    # Look for any clickable element after the label
                    following = label.find_elements(By.XPATH, "./following-sibling::* | ./parent::*/following-sibling::*")
                    for elem in following[:5]:  # Check first 5 following elements
                        try:
                            if elem.is_displayed():
                                driver.execute_script("arguments[0].click();", elem)
                                time.sleep(1)
                                
                                # Now look for the option
                                option_elems = driver.find_elements(By.XPATH, f"//*[contains(text(), '{option_text}')]")
                                for opt in option_elems:
                                    if opt.is_displayed():
                                        driver.execute_script("arguments[0].click();", opt)
                                        print(f"   ✓ Selected '{option_text}' in '{filter_label}' (click method)")
                                        time.sleep(wait_time)
                                        return True
                        except:
                            continue
                except:
                    continue
        except:
            pass
        
        # Strategy 5: Debug - save page source
        print(f"   ⚠️ Could not find '{filter_label}' dropdown")
        print(f"   Debug: Saving page HTML for inspection...")
        
        try:
            debug_dir = Path(__file__).parent / "debug-output"
            debug_dir.mkdir(exist_ok=True)
            html_file = debug_dir / "ocr-paper-finder-page.html"
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"   💾 Saved page HTML to: {html_file}")
            print(f"   💡 Please inspect this file to see the actual dropdown structure")
        except Exception as e:
            print(f"   ⚠️ Could not save debug file: {e}")
        
        return False
        
    except Exception as e:
        print(f"   ⚠️ Error selecting '{filter_label}': {e}")
        import traceback
        traceback.print_exc()
        return False


def expand_all_accordions(driver):
    """Expand all collapsed accordions on the page (OCR uses jQuery UI accordion)."""
    print("   Expanding accordions...")
    
    expanded_count = 0
    
    # OCR uses jQuery UI accordion - click h3 and h4 headings
    # Level 1: h3.level-1.heading
    # Level 2: h4.level-2.heading
    
    # Expand Level 1 accordions (main sections)
    try:
        level1_headings = driver.find_elements(By.CSS_SELECTOR, "h3.level-1.heading")
        for heading in level1_headings:
            try:
                # Check if already expanded
                aria_expanded = heading.get_attribute("aria-expanded")
                if aria_expanded == "false":
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", heading)
                    time.sleep(0.2)
                    driver.execute_script("arguments[0].click();", heading)
                    time.sleep(0.5)
                    expanded_count += 1
            except:
                pass
    except:
        pass
    
    # Expand Level 2 accordions (year/series)
    try:
        level2_headings = driver.find_elements(By.CSS_SELECTOR, "h4.level-2.heading")
        for heading in level2_headings:
            try:
                # Check if content is hidden
                parent = heading.find_element(By.XPATH, "./following-sibling::div[1]")
                style = parent.get_attribute("style") or ""
                if "display: none" in style or not parent.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", heading)
                    time.sleep(0.2)
                    driver.execute_script("arguments[0].click();", heading)
                    time.sleep(0.5)
                    expanded_count += 1
            except:
                pass
    except:
        pass
    
    print(f"   ✓ Expanded {expanded_count} accordions")
    return expanded_count
    
    # Try multiple selectors for accordions
    accordion_selectors = [
        "button[aria-expanded='false']",
        "summary",
        "[role='button'][aria-expanded='false']",
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


def scrape_papers(subject_code, subject_name, qualification_filter, level_filter, headless=True, force_headless=False):
    """Scrape papers from OCR past paper finder page."""
    
    print("=" * 80)
    print("OCR A-LEVEL - PAPERS SCRAPER")
    print("=" * 80)
    print(f"\nSubject: {subject_name}")
    print(f"Code: {subject_code}")
    print(f"Qualification: {qualification_filter}")
    print(f"Level: {level_filter}")
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
        
        # Step 1: Select "Type of Qualification" dropdown (id="pp-qual-type")
        try:
            qual_type_select = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "pp-qual-type"))
            )
            select = Select(qual_type_select)
            select.select_by_value("3863")  # "AS and A Level"
            print("   ✓ Selected 'AS and A Level'")
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
            # Try to find the qualification option
            found = False
            for option in select.options:
                if qualification_filter.lower() in option.text.lower() or option.text.lower() in qualification_filter.lower():
                    select.select_by_value(option.get_attribute("value"))
                    print(f"   ✓ Selected '{option.text}'")
                    found = True
                    break
            
            if not found:
                # Try partial match
                for option in select.options:
                    if "ancient history" in option.text.lower() and "h407" in option.text.lower():
                        select.select_by_value(option.get_attribute("value"))
                        print(f"   ✓ Selected '{option.text}' (partial match)")
                        found = True
                        break
            
            if not found:
                print("   ⚠️ Could not find qualification option")
            
            time.sleep(5)  # Wait for AJAX to populate Level dropdown
        except Exception as e:
            print(f"   ⚠️ Failed to select Qualification: {e}")
        
        # Step 3: Select Level dropdown (id="pp-level")
        try:
            # Wait for Level dropdown to be enabled and populated
            level_select = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "pp-level"))
            )
            
            # Wait for options to be populated
            WebDriverWait(driver, 15).until(
                lambda d: len(Select(d.find_element(By.ID, "pp-level")).options) > 1
            )
            
            select = Select(level_select)
            # Try to find level option
            found = False
            for option in select.options:
                if level_filter.lower() in option.text.lower() or "a level" in option.text.lower():
                    select.select_by_value(option.get_attribute("value"))
                    print(f"   ✓ Selected '{option.text}'")
                    found = True
                    break
            
            if not found:
                print("   ⚠️ Could not find level option")
            
            time.sleep(5)  # Wait for results to load
        except Exception as e:
            print(f"   ⚠️ Failed to select Level: {e}")
        
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
        
        # Step 4: Expand all accordions
        print("\n📂 Step 2: Expanding accordions...")
        expand_all_accordions(driver)
        
        # Scroll to load all content
        print("   Scrolling to load content...")
        time.sleep(2)
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        for _ in range(10):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        # Step 5: Scrape PDF links using exact OCR structure
        print("\n📥 Step 3: Scraping PDF links...")
        
        # Save page HTML for debugging
        try:
            debug_dir = Path(__file__).parent / "debug-output"
            debug_dir.mkdir(exist_ok=True)
            with open(debug_dir / "ocr-paper-finder-after-filters.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"   💾 Saved page HTML to debug-output/ocr-paper-finder-after-filters.html")
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
                    parsed = parse_paper_metadata_ocr(href, text, year_series, unit_code, subject_code)
                    
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
                parsed = parse_paper_metadata_ocr(href, text, year_series, unit_code, subject_code)
                
                if parsed:
                    papers.append(parsed)
                    print(f"   ✓ {parsed['year']} {parsed['exam_series']} - Paper {parsed['paper_number']} - {parsed['doc_type']}")
        
        print(f"\n✓ Found {len(papers)} papers")
        
        print(f"\n✓ Found {len(papers)} papers")
        
        # Breakdown
        if papers:
            doc_types_found = Counter(p['doc_type'] for p in papers)
            print("\n   Breakdown:")
            for dt, count in doc_types_found.items():
                print(f"   • {dt}: {count}")
            
            years = Counter(p['year'] for p in papers)
            print(f"\n   Years: {dict(sorted(years.items(), reverse=True))}")
        
        return papers
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []
        
    finally:
        if driver:
            print("\n🔒 Closing browser...")
            driver.quit()
            print("✓ Browser closed")


def parse_paper_metadata_ocr(href, link_text, year_series_text, unit_code, subject_code):
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
    
    # Extract paper number from unit_code (e.g., "H407/11" -> 11)
    paper_number = None
    component_code = None
    
    if unit_code:
        # Pattern: H407/11 or H407/11/12/13
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
    
    return {
        'year': year,
        'exam_series': series,
        'paper_number': paper_number,
        'component_code': component_code,
        'tier': None,
        'doc_type': doc_type,
        'url': href
    }


def parse_paper_metadata(href, link_text, accordion_title, subject_code):
    """Legacy function - redirects to OCR-specific parser."""
    return parse_paper_metadata_ocr(href, link_text, accordion_title, "", subject_code)


def scrape_papers_manual(subject_code, subject_name, qualification_filter, level_filter):
    """Manual mode - opens browser, user selects filters, then scrapes."""
    print("=" * 80)
    print("OCR A-LEVEL - PAPERS SCRAPER (MANUAL MODE)")
    print("=" * 80)
    print(f"\nSubject: {subject_name}")
    print(f"Code: {subject_code}")
    print(f"\n📋 Instructions:")
    print(f"1. Browser will open to OCR past paper finder")
    print(f"2. Please manually select:")
    print(f"   - Type: AS and A Level")
    print(f"   - Qualification: {qualification_filter}")
    print(f"   - Level: {level_filter}")
    print(f"3. Wait for papers to appear")
    print(f"4. Expand all year/series accordions")
    print(f"5. Press ENTER here to start scraping")
    print("\n" + "=" * 80)
    
    driver = None
    papers = []
    base_url = "https://www.ocr.org.uk/qualifications/past-paper-finder/"
    
    try:
        driver = init_driver(headless=False)  # Always non-headless for manual mode
        
        print(f"\n📂 Opening browser...")
        driver.get(base_url)
        print(f"   ✓ Browser opened")
        print(f"\n⏸️  Waiting for you to select filters...")
        print(f"   (Expand all accordions, then press ENTER here)")
        
        # Wait for user to press Enter
        input()
        
        print(f"\n📥 Starting to scrape...")
        time.sleep(2)
        
        # Expand any remaining accordions
        expand_all_accordions(driver)
        time.sleep(2)
        
        # Scroll to load content
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(10):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        # Scrape PDF links using OCR structure
        print("\n📥 Scraping PDF links...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find all resource lists (each year/series has one)
        resource_lists = soup.find_all('ul', class_='resource-list')
        print(f"   Found {len(resource_lists)} resource lists")
        
        # Parse each resource list
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
                parsed = parse_paper_metadata_ocr(href, text, year_series, unit_code, subject_code)
                
                if parsed:
                    papers.append(parsed)
                    print(f"   ✓ {parsed['year']} {parsed['exam_series']} - Paper {parsed['paper_number']} - {parsed['doc_type']}")
        
        print(f"\n✓ Found {len(papers)} papers")
        
        # Breakdown
        if papers:
            doc_types_found = Counter(p['doc_type'] for p in papers)
            print("\n   Breakdown:")
            for dt, count in doc_types_found.items():
                print(f"   • {dt}: {count}")
            
            years = Counter(p['year'] for p in papers)
            print(f"\n   Years: {dict(sorted(years.items(), reverse=True))}")
        
        return papers
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []
        
    finally:
        if driver:
            print("\n🔒 Closing browser...")
            driver.quit()
            print("✓ Browser closed")


def scrape_papers_firecrawl(subject_code, subject_name, qualification_filter, level_filter):
    """Alternative scraper using Firecrawl (faster, handles JS better)."""
    print("=" * 80)
    print("OCR A-LEVEL - PAPERS SCRAPER (FIRECRAWL)")
    print("=" * 80)
    print(f"\nSubject: {subject_name}")
    print(f"Code: {subject_code}")
    print(f"\nNote: Firecrawl mode requires manual filter selection or URL construction")
    print("This is a placeholder - you may need to manually navigate and scrape")
    
    # Firecrawl can scrape the page, but we still need to handle filters
    # Option 1: Construct URL with filters (if OCR supports it)
    # Option 2: Use Firecrawl's browser mode to interact
    
    firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY')
    if not firecrawl_api_key:
        print("❌ FIRECRAWL_API_KEY not found in environment!")
        return []
    
    try:
        app = FirecrawlApp(api_key=firecrawl_api_key)
        
        # Try to scrape the page (may need filters applied via URL params)
        base_url = "https://www.ocr.org.uk/qualifications/past-paper-finder/"
        
        print(f"\n📂 Scraping with Firecrawl...")
        result = app.scrape_url(base_url, {
            'formats': ['markdown', 'html'],
            'waitFor': 5000,  # Wait 5 seconds for JS to load
            'onlyMainContent': False
        })
        
        if result and result.get('markdown'):
            print(f"   ✓ Scraped {len(result['markdown'])} chars")
            # Parse markdown/HTML for PDF links
            # This would need similar parsing logic as Selenium version
            print("   ⚠️ Firecrawl scraping needs filter interaction - use Selenium for now")
            return []
        else:
            print("   ⚠️ No content scraped")
            return []
            
    except Exception as e:
        print(f"❌ Firecrawl error: {e}")
        return []


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
    """Main execution."""
    
    # Force UTF-8 output
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    # Parse arguments
    if len(sys.argv) < 5:
        print("Usage: python scrape-ocr-papers-universal.py <subject_code> <subject_name> <qualification_filter> <level_filter> [options]")
        print("\nExample:")
        print('  python scrape-ocr-papers-universal.py H407 "Ancient History" "Ancient History - H007, H407 (from 2017)" "A Level"')
        print('  python scrape-ocr-papers-universal.py H407 "Ancient History" "Ancient History - H007, H407 (from 2017)" "A Level" --visible')
        print('  python scrape-ocr-papers-universal.py H407 "Ancient History" "Ancient History - H007, H407 (from 2017)" "A Level" --manual')
        print('  python scrape-ocr-papers-universal.py H407 "Ancient History" "Ancient History - H007, H407 (from 2017)" "A Level" --firecrawl')
        print("\nOptions:")
        print("  --headless : Run in headless mode (no browser window) - DEFAULT")
        print("  --visible  : Show browser window (for debugging)")
        print("  --manual   : Opens browser, lets you select filters manually, then scrapes")
        print("  --firecrawl: Use Firecrawl API instead of Selenium")
        sys.exit(1)
    
    subject_code = sys.argv[1]
    subject_name = sys.argv[2]
    qualification_filter = sys.argv[3]
    level_filter = sys.argv[4]
    use_manual = '--manual' in sys.argv
    use_firecrawl = '--firecrawl' in sys.argv
    use_visible = '--visible' in sys.argv
    use_headless = '--headless' in sys.argv or not use_visible  # Default to headless unless --visible is specified
    
    # Try Firecrawl if requested and available
    if use_firecrawl and FIRECRAWL_AVAILABLE:
        print("🔥 Using Firecrawl mode...")
        papers = scrape_papers_firecrawl(subject_code, subject_name, qualification_filter, level_filter)
    elif use_manual:
        print("👤 Using MANUAL mode - browser will open, please select filters manually")
        print("   After selecting filters and seeing papers, press ENTER in this window to continue scraping...")
        papers = scrape_papers_manual(subject_code, subject_name, qualification_filter, level_filter)
    else:
        if use_firecrawl and not FIRECRAWL_AVAILABLE:
            print("⚠️ Firecrawl requested but not available. Install with: pip install firecrawl-py")
        
        # Use headless mode by default (unless --visible is specified)
        if use_headless:
            print("🔇 Running in HEADLESS mode (browser will not be visible)")
        else:
            print("👁️  Running in VISIBLE mode (browser window will be shown)")
        
        papers = scrape_papers(subject_code, subject_name, qualification_filter, level_filter, headless=use_headless)
    
    if not papers:
        print("\n⚠️ No papers found!")
        return 0
    
    # Group (filter to 2019+)
    print("\n📦 Grouping into sets (2019 onwards only)...")
    sets = group_papers(papers, min_year=2019)
    print(f"   Created {len(sets)} complete paper sets (2019+)")
    
    # Upload
    print("\n📤 Uploading to database...")
    
    try:
        uploaded = upload_papers_to_staging(
            subject_code=subject_code,
            qualification_type='A-Level',
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

