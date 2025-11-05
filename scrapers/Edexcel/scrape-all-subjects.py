"""
Scrape ALL Edexcel A-Level Subjects from Pearson Website
Automatically builds edexcel-alevel-subjects.json

This scraper:
1. Finds all A-Level subjects on Pearson website
2. Extracts specification PDF URLs
3. Generates complete subject list for overnight scraping
"""

import re
import json
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests

def init_driver():
    """Initialize Chrome WebDriver."""
    print("🌐 Initializing Chrome WebDriver...")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    
    print("✅ WebDriver initialized")
    return driver


def scrape_all_subjects():
    """Scrape all Edexcel A-Level subjects from index pages."""
    
    print("=" * 60)
    print("EDEXCEL A-LEVEL SUBJECT SCRAPER")
    print("=" * 60)
    print("\nUsing Pearson's 'First Teaching' index pages...\n")
    
    driver = None
    subjects = []
    
    # Index pages with clean subject lists
    index_pages = [
        {
            'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/about/first-teaching-from-2015-and-2016.html',
            'year_group': '2015-2016'
        },
        {
            'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/about/first-teaching-from-2017.html',
            'year_group': '2017'
        },
        {
            'url': 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/about/first-teaching-from-2018.html',
            'year_group': '2018'
        }
    ]
    
    try:
        driver = init_driver()
        
        unique_subjects = {}
        
        # Scrape each index page
        for index in index_pages:
            print(f"🔍 Scraping {index['year_group']} subjects...")
            driver.get(index['url'])
            time.sleep(2)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find all subject links on this page
            # They link to subject pages like /edexcel-a-levels/biology-a-2015.html
            subject_links = soup.find_all('a', href=re.compile(r'/edexcel-a-levels/[a-z0-9\-]+-\d{4}\.html'))
            
            print(f"   Found {len(subject_links)} subjects")
            
            for link in subject_links:
                href = link.get('href', '')
                if href.startswith('/'):
                    href = 'https://qualifications.pearson.com' + href
                
                # Extract slug
                match = re.search(r'/edexcel-a-levels/([^/]+)\.html', href)
                if match:
                    slug = match.group(1)
                    if slug not in unique_subjects:
                        unique_subjects[slug] = {
                            'url': href,
                            'slug': slug
                        }
        
        print(f"\n✅ Found {len(unique_subjects)} unique subjects across all years")
        print("\n📚 Processing each subject to extract details...\n")
        
        # Process each subject to extract details
        for idx, (slug, info) in enumerate(unique_subjects.items()):
            try:
                driver.get(info['url'])
                time.sleep(1)
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Extract subject name from h1 or title
                subject_name = slug.replace('-', ' ').title()
                h1 = soup.find('h1')
                if h1:
                    subject_name = h1.get_text().strip()
                    # Clean up "Edexcel AS and A level Biology A 2015" -> "Biology A"
                    subject_name = re.sub(r'Edexcel\s+(AS\s+and\s+)?A\s+level\s+', '', subject_name, flags=re.IGNORECASE)
                    subject_name = re.sub(r'\s*\(?\d{4}\)?$', '', subject_name).strip()
                
                # Find specification PDF
                # Look in the "Specification" tab/section which has a Download button
                spec_pdf = None
                
                # Find all sections/divs that might contain the specification
                # Usually in a tab or section with ID/class containing "specification"
                spec_sections = soup.find_all(['div', 'section'], {'id': re.compile(r'spec', re.IGNORECASE)})
                spec_sections += soup.find_all(['div', 'section'], {'class': re.compile(r'spec', re.IGNORECASE)})
                
                for section in spec_sections:
                    # Look for Download link in this section
                    download = section.find('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
                    if download:
                        href = download.get('href', '')
                        if href.startswith('//'):
                            spec_pdf = 'https:' + href
                        elif href.startswith('/'):
                            spec_pdf = 'https://qualifications.pearson.com' + href
                        else:
                            spec_pdf = href
                        break
                
                # Fallback: Find first PDF link that has "specification" near it
                if not spec_pdf:
                    all_pdfs = soup.find_all('a', href=re.compile(r'specification.*\.pdf', re.IGNORECASE))
                    if all_pdfs:
                        href = all_pdfs[0].get('href', '')
                        if href.startswith('//'):
                            spec_pdf = 'https:' + href
                        elif href.startswith('/'):
                            spec_pdf = 'https://qualifications.pearson.com' + href
                        else:
                            spec_pdf = href
                
                # Extract subject code from page (pattern: 9XX0)
                code_match = re.search(r'\b(9[A-Z]{2,3}0)\b', driver.page_source)
                subject_code = code_match.group(1) if code_match else 'UNKNOWN'
                
                # Build exam materials URL
                exam_materials_url = info['url'].replace('.html', '.coursematerials.html') + '#filterQuery=Pearson-UK:Category%2FExam-materials'
                
                # Determine scraper type
                scraper_type = 'complex' if 'history' in slug.lower() else 'simple'
                
                # Determine status
                status = 'complete' if slug in ['history-2015', 'biology-a-2015'] else 'ready'
                
                subject_data = {
                    'name': subject_name,
                    'code': subject_code,
                    'slug': slug,
                    'pdf_url': spec_pdf,
                    'exam_materials_url': exam_materials_url,
                    'scraper_type': scraper_type,
                    'status': status
                }
                
                subjects.append(subject_data)
                
                print(f"[{idx + 1}/{len(unique_subjects)}] {subject_name} ({subject_code}) - PDF: {'✅' if spec_pdf else '❌'}")
                
            except Exception as e:
                print(f"[{idx + 1}/{len(unique_subjects)}] {slug} - ⚠️  Error: {e}")
                continue
        
        print(f"\n✅ Processed {len(subjects)} subjects")
        
        return subjects
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []
        
    finally:
        if driver:
            driver.quit()
            print("\n🔒 Browser closed")


def save_subjects_json(subjects):
    """Save subjects to JSON file."""
    
    output_path = Path(__file__).parent / 'edexcel-alevel-subjects.json'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(subjects, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved to: {output_path.name}")
    print(f"   Total subjects: {len(subjects)}")
    
    # Show breakdown
    with_pdf = len([s for s in subjects if s['pdf_url']])
    tested = len([s for s in subjects if s['status'] == 'tested'])
    
    print(f"   With PDF URLs: {with_pdf}/{len(subjects)}")
    print(f"   Already tested: {tested}")
    print(f"   Ready to scrape: {len(subjects) - tested}")


def main():
    """Main execution."""
    
    # Scrape all subjects
    subjects = scrape_all_subjects()
    
    if not subjects:
        print("\n⚠️  No subjects found!")
        return
    
    # Save to JSON
    save_subjects_json(subjects)
    
    print("\n" + "=" * 60)
    print("COMPLETE!")
    print("=" * 60)
    print("\n💡 Next: Run overnight scraper with this subject list!")
    print("   python run-all-edexcel-alevel.py")


if __name__ == '__main__':
    main()

