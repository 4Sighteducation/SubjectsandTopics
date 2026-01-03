"""
EDEXCEL GCSE - OVERNIGHT BATCH SCRAPER
Scrapes TOPICS and PAPERS for all 35 GCSE subjects while you sleep!

Strategy:
1. Download all PDFs first (parallel possible but sequential is safer)
2. Try multiple parsing patterns per subject (table, science, paper-based)
3. Upload successful topic extractions
4. Scrape all papers using proven Selenium approach
5. Generate comprehensive summary report

Run time: 2-4 hours for complete dataset
"""

import os
import sys
import json
import re
import time
import requests
from pathlib import Path
from io import BytesIO
from datetime import datetime
from collections import Counter

# Setup paths
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from supabase import create_client
from pypdf import PdfReader

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

# Load upload helper
import importlib.util
upload_helper_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\upload_papers_to_staging.py")
spec = importlib.util.spec_from_file_location("upload_papers_to_staging", upload_helper_path)
upload_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload_module)
upload_papers_to_staging = upload_module.upload_papers_to_staging


def log_progress(message):
    """Log with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def download_pdf(url, subject_code):
    """Download PDF and save debug file."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        pdf = PdfReader(BytesIO(response.content))
        full_text = '\n'.join(page.extract_text() for page in pdf.pages)
        
        # Save debug
        debug_path = script_dir / 'debug-files' / f'{subject_code.lower()}-spec.txt'
        debug_path.parent.mkdir(exist_ok=True)
        debug_path.write_text(full_text, encoding='utf-8')
        
        return full_text
    except Exception as e:
        log_progress(f"[ERROR] Failed to download {subject_code}: {e}")
        return None


def try_parse_topics(text, subject_code, subject_name):
    """Try multiple parsing patterns and return best result."""
    
    topics = []
    
    # Pattern 1: Paper/Component structure (most GCSE have 1-2 papers)
    paper_matches = re.findall(r'^(?:Paper|Component)\s+(\d+):?\s*(.{10,100})$', text, re.MULTILINE | re.IGNORECASE)
    if paper_matches and len(paper_matches) >= 1:
        unique_papers = {}
        for num, title in paper_matches[:5]:  # Limit to first 5
            if num not in unique_papers:
                title = re.sub(r'\s+', ' ', title).strip()[:200]
                unique_papers[num] = title
        
        for num in sorted(unique_papers.keys(), key=int):
            topics.append({
                'code': f'Paper{num}',
                'title': f'Paper {num}: {unique_papers[num]}',
                'level': 0,
                'parent': None
            })
    
    # Pattern 2: Topic X: headers (Science style)
    topic_matches = re.findall(r'^Topic\s+(\d+[A-Z]?):\s*(.{10,100})$', text, re.MULTILINE | re.IGNORECASE)
    if topic_matches and len(topic_matches) >= 3:
        for num, title in topic_matches[:20]:  # Limit
            title = re.sub(r'\s+', ' ', title).strip()[:200]
            topics.append({
                'code': f'Topic{num}',
                'title': f'Topic {num}: {title}',
                'level': 1 if topics else 0,
                'parent': topics[0]['code'] if topics else None
            })
    
    # Pattern 3: Numbered sections (1.1, 1.2, 2.1, etc.)
    section_matches = re.findall(r'^(\d{1,2})\.(\d{1,2})\s+(.{10,300})$', text, re.MULTILINE)
    if section_matches and len(section_matches) >= 5:
        sections = {}
        for major, minor, title in section_matches[:100]:
            title = re.sub(r'\s+', ' ', title).strip()
            # Skip if looks like notation/appendix
            if any(skip in title.lower() for skip in ['introduction', 'assessment', 'appendix', 'formula']):
                continue
            if len(title) > 10:
                if major not in sections:
                    sections[major] = []
                sections[major].append((minor, title[:300]))
        
        # Create hierarchy
        for major_num in sorted(sections.keys(), key=int)[:15]:
            parent = topics[0]['code'] if topics else None
            section_code = f'S{major_num}'
            topics.append({
                'code': section_code,
                'title': f'Section {major_num}',
                'level': 1 if topics else 0,
                'parent': parent
            })
            
            for minor_num, title in sections[major_num][:10]:
                topics.append({
                    'code': f'S{major_num}_{minor_num}',
                    'title': f'{major_num}.{minor_num} {title}',
                    'level': 2 if topics else 1,
                    'parent': section_code
                })
    
    # Pattern 4: Theme structure
    theme_matches = re.findall(r'^Theme\s+(\d+):?\s*(.{10,100})$', text, re.MULTILINE | re.IGNORECASE)
    if theme_matches and len(theme_matches) >= 2:
        for num, title in theme_matches[:10]:
            title = re.sub(r'\s+', ' ', title).strip()[:200]
            topics.append({
                'code': f'Theme{num}',
                'title': f'Theme {num}: {title}',
                'level': 1 if topics else 0,
                'parent': topics[0]['code'] if topics else None
            })
    
    return topics


def upload_subject_topics(subject_code, subject_name, pdf_url, topics):
    """Upload topics for a subject."""
    try:
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{subject_name} (GCSE)",
            'subject_code': subject_code,
            'qualification_type': 'GCSE',
            'specification_url': pdf_url,
            'exam_board': 'Edexcel'
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        
        # Clear old
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        
        # Insert
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'exam_board': 'Edexcel'
        } for t in topics]
        
        inserted_result = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        
        # Link hierarchy
        code_to_id = {t['topic_code']: t['id'] for t in inserted_result.data}
        for topic in topics:
            if topic['parent']:
                parent_id = code_to_id.get(topic['parent'])
                child_id = code_to_id.get(topic['code'])
                if parent_id and child_id:
                    supabase.table('staging_aqa_topics').update({
                        'parent_topic_id': parent_id
                    }).eq('id', child_id).execute()
        
        return len(inserted_result.data)
    except Exception as e:
        log_progress(f"[ERROR] Upload failed for {subject_code}: {e}")
        return 0


def scrape_papers_for_subject(subject_code, subject_name, url, driver, paper_code_override=None):
    """Scrape papers for one GCSE subject."""
    
    papers = []
    
    try:
        driver.get(url)
        time.sleep(4)
        
        # Expand
        try:
            expand = driver.find_elements(By.XPATH, "//*[contains(text(), 'EXPAND ALL')]")
            if expand:
                driver.execute_script("arguments[0].click();", expand[0])
                time.sleep(2)
        except:
            pass
        
        # Scroll
        for _ in range(12):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.3)
        
        # Scrape
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        
        # Determine paper code to search for
        search_code = paper_code_override if paper_code_override else subject_code.lower().replace('gcse-', '')
        
        for link in pdf_links:
            href = link.get('href', '')
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = 'https://qualifications.pearson.com' + href
            
            # Check if this is a paper for this subject
            filename = href.split('/')[-1].lower()
            
            # Try to find paper pattern
            # GCSE papers often use format: 1abc0-01h-que-20240524.pdf
            paper_pattern = r'(\w+)[-_](\d+[a-z]?)[-_]([a-z]{3})[-_](\d{8})'
            match = re.search(paper_pattern, filename)
            
            if match:
                file_code = match.group(1)
                # Check if this matches our subject
                if search_code not in file_code:
                    continue
                
                paper_num_str = match.group(2)
                doc_type_code = match.group(3)
                date_str = match.group(4)
                
                # Extract just numeric paper number
                paper_num = int(re.search(r'\d+', paper_num_str).group())
                
                year = int(date_str[:4])
                month = int(date_str[4:6])
                series = 'June' if month in [5, 6] else 'November' if month == 11 else 'January' if month == 1 else 'June'
                
                doc_types = {'que': 'Question Paper', 'rms': 'Mark Scheme', 'msc': 'Mark Scheme', 'pef': 'Examiner Report'}
                doc_type = doc_types.get(doc_type_code, 'Question Paper')
                
                papers.append({
                    'year': year,
                    'exam_series': series,
                    'paper_number': paper_num,
                    'component_code': f'{paper_num:02d}',
                    'tier': None,
                    'doc_type': doc_type,
                    'url': href
                })
    
    except Exception as e:
        log_progress(f"[ERROR] Paper scrape failed for {subject_code}: {e}")
    
    return papers


def main():
    """Overnight batch processing."""
    
    start_time = datetime.now()
    
    print("\n" + "=" * 80)
    print("🌙 EDEXCEL GCSE - OVERNIGHT BATCH SCRAPER")
    print("=" * 80)
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("Estimated completion: 2-4 hours")
    print("=" * 80 + "\n")
    
    # Load subjects
    subjects_file = script_dir / 'gcse-subjects.json'
    with open(subjects_file, 'r') as f:
        subjects = json.load(f)
    
    log_progress(f"Loaded {len(subjects)} GCSE subjects")
    
    results = {
        'topics': {'success': [], 'failed': []},
        'papers': {'success': [], 'failed': []}
    }
    
    # PHASE 1: TOPICS
    print("\n" + "=" * 80)
    print("PHASE 1: SCRAPING TOPICS")
    print("=" * 80 + "\n")
    
    for idx, subject in enumerate(subjects, 1):
        code = subject['code']
        name = subject['name']
        pdf_url = subject['pdf_url']
        
        log_progress(f"[{idx}/{len(subjects)}] Processing {name} ({code})...")
        
        try:
            # Download PDF
            text = download_pdf(pdf_url, code)
            if not text:
                results['topics']['failed'].append(name)
                continue
            
            # Try parsing
            topics = try_parse_topics(text, code, name)
            
            if len(topics) >= 2:
                # Upload
                uploaded_count = upload_subject_topics(code, name, pdf_url, topics)
                if uploaded_count > 0:
                    results['topics']['success'].append({
                        'name': name,
                        'code': code,
                        'topics': uploaded_count
                    })
                    log_progress(f"   ✅ {name}: {uploaded_count} topics uploaded")
                else:
                    results['topics']['failed'].append(name)
            else:
                log_progress(f"   ⚠️  {name}: Only {len(topics)} topics - needs manual")
                results['topics']['failed'].append(name)
        
        except Exception as e:
            log_progress(f"   ❌ {name}: {e}")
            results['topics']['failed'].append(name)
        
        time.sleep(1)  # Rate limiting
    
    # PHASE 2: PAPERS
    print("\n" + "=" * 80)
    print("PHASE 2: SCRAPING PAPERS")
    print("=" * 80 + "\n")
    
    driver = None
    
    try:
        # Initialize driver once
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        log_progress("WebDriver initialized")
        
        for idx, subject in enumerate(subjects, 1):
            code = subject['code']
            name = subject['name']
            url = subject.get('exam_materials_url')
            
            if not url:
                continue
            
            log_progress(f"[{idx}/{len(subjects)}] Scraping papers: {name}...")
            
            try:
                papers = scrape_papers_for_subject(code, name, url, driver)
                
                if papers:
                    # Group into sets
                    sets = {}
                    for paper in papers:
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
                    
                    paper_sets = list(sets.values())
                    
                    # Upload
                    uploaded = upload_papers_to_staging(
                        subject_code=code,
                        qualification_type='GCSE',
                        papers_data=paper_sets,
                        exam_board='Edexcel'
                    )
                    
                    results['papers']['success'].append({
                        'name': name,
                        'code': code,
                        'sets': uploaded
                    })
                    log_progress(f"   ✅ {name}: {uploaded} paper sets")
                else:
                    log_progress(f"   ⚠️  {name}: No papers found")
                    results['papers']['failed'].append(name)
            
            except Exception as e:
                log_progress(f"   ❌ {name}: {e}")
                results['papers']['failed'].append(name)
            
            time.sleep(0.5)
    
    finally:
        if driver:
            driver.quit()
    
    # FINAL SUMMARY
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 80)
    print("🎉 OVERNIGHT BATCH SCRAPER - FINAL REPORT")
    print("=" * 80)
    print(f"Started:  {start_time.strftime('%H:%M:%S')}")
    print(f"Finished: {end_time.strftime('%H:%M:%S')}")
    print(f"Duration: {duration}")
    print("=" * 80)
    
    print("\n📝 TOPICS:")
    print(f"   ✅ Success: {len(results['topics']['success'])}")
    total_topics = 0
    for result in results['topics']['success']:
        print(f"      • {result['name']}: {result['topics']} topics")
        total_topics += result['topics']
    print(f"   TOTAL: {total_topics} topics")
    
    if results['topics']['failed']:
        print(f"\n   ❌ Failed/Manual: {len(results['topics']['failed'])}")
        for name in results['topics']['failed']:
            print(f"      • {name}")
    
    print("\n📄 PAPERS:")
    print(f"   ✅ Success: {len(results['papers']['success'])}")
    total_sets = 0
    for result in results['papers']['success']:
        print(f"      • {result['name']}: {result['sets']} sets")
        total_sets += result['sets']
    print(f"   TOTAL: {total_sets} paper sets")
    
    if results['papers']['failed']:
        print(f"\n   ❌ No papers: {len(results['papers']['failed'])}")
    
    print("\n" + "=" * 80)
    print(f"🌟 GRAND TOTAL: {total_topics} topics + {total_sets} paper sets!")
    print("=" * 80 + "\n")
    
    # Save report
    report_path = script_dir / f'OVERNIGHT-REPORT-{datetime.now().strftime("%Y%m%d-%H%M")}.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"EDEXCEL GCSE OVERNIGHT BATCH SCRAPER REPORT\n")
        f.write(f"{'=' * 80}\n")
        f.write(f"Duration: {duration}\n")
        f.write(f"Topics: {total_topics}\n")
        f.write(f"Papers: {total_sets}\n")
        f.write(f"Success rate: {len(results['topics']['success'])}/{len(subjects)} topics, ")
        f.write(f"{len(results['papers']['success'])}/{len(subjects)} papers\n")
    
    log_progress(f"Report saved: {report_path}")


if __name__ == '__main__':
    main()

