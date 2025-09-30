"""Debug - save assessment page HTML to see what we're getting"""

from scrapers.uk.aqa_assessment_scraper import AQAAssessmentScraper
import time

scraper = AQAAssessmentScraper(headless=False)  # headless=False so you can see what's happening

url = "https://www.aqa.org.uk/subjects/biology/a-level/biology-7402/assessment-resources"

print(f"Loading: {url}")

# Load page
html = scraper._get_page(url, use_selenium=True)

# Scroll and wait
if scraper.driver:
    print("Scrolling...")
    for i in range(3):
        scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
    
    # Wait for any AJAX to complete
    print("Waiting for dynamic content...")
    time.sleep(5)
    
    html = scraper.driver.page_source

# Save to file
with open('debug_assessment_page.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Saved to: debug_assessment_page.html")

# Count links
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'lxml')

all_links = soup.find_all('a', href=True)
pdf_links = [link for link in all_links if 'cdn.sanity' in link.get('href', '') or '.pdf' in link.get('href', '').lower()]

print(f"\nTotal links: {len(all_links)}")
print(f"PDF links: {len(pdf_links)}")

if pdf_links:
    print(f"\nFirst 5 PDF links:")
    for link in pdf_links[:5]:
        print(f"  Text: {link.get_text().strip()[:60]}")
        print(f"  Href: {link.get('href')[:80]}")
        print()
else:
    print("\nNo PDF links found!")
    print("\nSearching for 'sanity' in HTML...")
    if 'sanity' in html:
        print("  'sanity' found in HTML")
        # Find where
        import re
        matches = re.findall(r'.{0,50}sanity.{0,50}', html, re.IGNORECASE)
        print(f"  Found {len(matches)} occurrences")
        for m in matches[:3]:
            print(f"    {m}")
    else:
        print("  'sanity' NOT in HTML - PDFs not loaded!")

scraper.close()
