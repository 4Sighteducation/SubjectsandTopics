"""
Diagnostic script to check if Pearson website is accessible
and if we're being blocked
"""

import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Test URLs
TEST_URLS = {
    'GCSE Business': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/business-2017.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
    'GCSE Computer Science': 'https://qualifications.pearson.com/en/qualifications/edexcel-gcses/computer-science-2020.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials',
    'A-Level Business': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/business-2015.coursematerials.html#filterQuery=Pearson-UK:Category%2FExam-materials'
}

def test_direct_http():
    """Test if we can reach Pearson with direct HTTP request."""
    print("=" * 80)
    print("TEST 1: Direct HTTP Request")
    print("=" * 80)
    
    url = 'https://qualifications.pearson.com'
    
    try:
        response = requests.get(url, timeout=10)
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Can reach Pearson website")
        
        if 'Access Denied' in response.text or 'Forbidden' in response.text:
            print("⚠️  WARNING: Response contains 'Access Denied' or 'Forbidden'")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Cannot reach Pearson: {e}")
        return False


def test_selenium_visible():
    """Test with Selenium in VISIBLE mode (not headless)."""
    print("\n" + "=" * 80)
    print("TEST 2: Selenium with VISIBLE browser (not headless)")
    print("=" * 80)
    print("A browser window will open - watch what happens...")
    
    chrome_options = Options()
    # NOT headless - we want to see what happens
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        url = TEST_URLS['GCSE Business']
        print(f"\n[INFO] Navigating to: {url}")
        driver.get(url)
        
        print("[INFO] Waiting 8 seconds for page load...")
        time.sleep(8)
        
        # Check page title
        title = driver.title
        print(f"[INFO] Page title: {title}")
        
        # Check for blocking messages
        page_source = driver.page_source.lower()
        
        if 'access denied' in page_source or 'blocked' in page_source:
            print("❌ BLOCKED: Page contains 'access denied' or 'blocked'")
            return False
        
        if 'cloudflare' in page_source:
            print("⚠️  WARNING: Cloudflare detected (might be challenge page)")
        
        # Check for PDF links
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        all_links = soup.find_all('a', href=True)
        pdf_links = [l for l in all_links if '.pdf' in l.get('href', '').lower()]
        
        print(f"[INFO] Found {len(all_links)} total links")
        print(f"[INFO] Found {len(pdf_links)} PDF links")
        
        if len(pdf_links) == 0:
            print("⚠️  WARNING: No PDF links found - page might not have loaded content")
            
            # Check for Angular/JavaScript content
            if 'ng-' in driver.page_source or 'angular' in page_source:
                print("[INFO] Page uses Angular - content loads dynamically")
                print("[INFO] Trying scroll and expand...")
                
                # Try expand all
                try:
                    expand = driver.find_elements('xpath', "//*[contains(text(), 'EXPAND ALL')]")
                    if expand:
                        driver.execute_script("arguments[0].click();", expand[0])
                        print("[INFO] Clicked EXPAND ALL")
                        time.sleep(3)
                except:
                    print("[WARN] Could not find/click EXPAND ALL")
                
                # Scroll
                for _ in range(10):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(0.5)
                
                print("[INFO] Waiting 5 more seconds after scroll...")
                time.sleep(5)
                
                # Re-check for PDFs
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                pdf_links = [l for l in soup.find_all('a', href=True) if '.pdf' in l.get('href', '').lower()]
                print(f"[INFO] After scroll: Found {len(pdf_links)} PDF links")
        
        if len(pdf_links) > 0:
            print(f"✅ SUCCESS: Found {len(pdf_links)} PDF links")
            print(f"\n[INFO] First 5 PDF URLs:")
            for i, link in enumerate(pdf_links[:5]):
                print(f"  {i+1}. {link.get('href', '')[:100]}...")
            return True
        else:
            print("❌ FAILED: Still no PDF links after all attempts")
            return False
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if driver:
            print("\n[INFO] Browser will close in 5 seconds...")
            time.sleep(5)
            driver.quit()


def test_a_level_comparison():
    """Test A-Level vs GCSE to see if only GCSE is blocked."""
    print("\n" + "=" * 80)
    print("TEST 3: Compare A-Level vs GCSE access")
    print("=" * 80)
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    
    driver = None
    results = {}
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        for name, url in TEST_URLS.items():
            print(f"\n[INFO] Testing {name}...")
            driver.get(url)
            time.sleep(8)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            pdf_links = [l for l in soup.find_all('a', href=True) if '.pdf' in l.get('href', '').lower()]
            
            results[name] = len(pdf_links)
            print(f"  Found {len(pdf_links)} PDF links")
        
        print(f"\n[SUMMARY]")
        for name, count in results.items():
            status = "✅" if count > 0 else "❌"
            print(f"  {status} {name}: {count} PDFs")
        
        if all(count == 0 for count in results.values()):
            print("\n❌ ALL ZERO - Likely being blocked or website issue")
        elif results['A-Level Business'] > 0 and results['GCSE Business'] == 0:
            print("\n⚠️  A-Level works but GCSE doesn't - might be GCSE-specific issue")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
    finally:
        if driver:
            driver.quit()


def main():
    print("\nPEARSON WEBSITE DIAGNOSTIC TOOL")
    print("=" * 80)
    print("This will check:")
    print("  1. Can we reach Pearson website?")
    print("  2. Can Selenium load the page?")
    print("  3. Are PDFs loading?")
    print("  4. Is there a difference between A-Level and GCSE?")
    print("=" * 80)
    
    # Test 1: Direct HTTP
    http_ok = test_direct_http()
    
    if not http_ok:
        print("\n⚠️  Cannot reach Pearson - might be network issue or they're blocking requests")
        return
    
    # Test 2: Selenium visible
    print("\n[INFO] Running visible browser test (browser will open)...")
    selenium_ok = test_selenium_visible()
    
    # Test 3: A-Level vs GCSE
    print("\n[INFO] Comparing A-Level vs GCSE access...")
    test_a_level_comparison()
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)
    
    if not selenium_ok:
        print("\nPOSSIBLE ISSUES:")
        print("  1. Pearson might be blocking automated browsers (Selenium)")
        print("  2. Page structure may have changed recently")
        print("  3. Content might be behind a login/captcha now")
        print("  4. Your IP might be rate-limited (try again later)")
        print("\nRECOMMENDATIONS:")
        print("  • Try visiting the URL manually in your browser")
        print("  • Wait 30-60 minutes and try again")
        print("  • Use VPN if you suspect IP blocking")
        print("  • Contact Pearson to ask about automated access policies")


if __name__ == '__main__':
    main()

