"""
Edexcel History A-Level - Past Papers Scraper (Direct URL Construction)
Code: 9HI0

Constructs URLs directly based on predictable Pearson pattern
Much faster than Selenium scraping!
"""

import os
import sys
import re
from pathlib import Path
import requests
from collections import Counter

# Calculate project root (4 levels up from this file)
# This file: scrapers/Edexcel/A-Level/papers/scrape-history-papers-direct.py
# Project root: ../../../../
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from supabase import create_client

# Load .env
env_path = project_root / 'flash-curriculum-pipeline' / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env from {env_path}")
else:
    # Try direct path
    env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded .env from {env_path}")
    else:
        print(f"❌ .env not found at {env_path}")

# Import upload helper
upload_papers_to_staging = None
upload_helper_path = project_root / 'flash-curriculum-pipeline' / 'upload_papers_to_staging.py'

if not upload_helper_path.exists():
    # Try direct path
    upload_helper_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\upload_papers_to_staging.py")

if upload_helper_path.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("upload_papers_to_staging", upload_helper_path)
    upload_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(upload_module)
    upload_papers_to_staging = upload_module.upload_papers_to_staging
    print(f"✅ Upload helper imported from {upload_helper_path}")
else:
    print(f"⚠️  Upload helper not found at {upload_helper_path}")


def get_component_codes_from_db():
    """
    Get all component codes from the topics we just scraped.
    Returns list like: ['1A', '1B', '2A.1', '2B.1', '30', '31', etc.]
    """
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials!")
        return []
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Get History subject
    subject = supabase.table('staging_aqa_subjects')\
        .select('id')\
        .eq('subject_code', '9HI0')\
        .eq('qualification_type', 'A-Level')\
        .eq('exam_board', 'Edexcel')\
        .execute()
    
    if not subject.data:
        print("❌ History subject not found in database!")
        return []
    
    subject_id = subject.data[0]['id']
    
    # Get all Options (Level 1) which correspond to exam papers
    options = supabase.table('staging_aqa_topics')\
        .select('topic_code, topic_name')\
        .eq('subject_id', subject_id)\
        .eq('topic_level', 1)\
        .execute()
    
    # Extract component codes from Option codes
    # "Option1A" -> "1A", "Option2B.1" -> "2B.1", "Option30" -> "30"
    components = []
    for opt in options.data:
        code = opt['topic_code'].replace('Option', '')
        components.append(code)
    
    print(f"✅ Found {len(components)} component codes from database")
    print(f"   Sample: {components[:10]}")
    
    return sorted(components)


def check_url_exists(url):
    """
    Check if a URL exists without downloading the full file.
    Uses HEAD request and checks for redirects to 404 pages.
    """
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        
        # Check status code
        if response.status_code != 200:
            return False
        
        # Check if we were redirected to a 404 page
        if '/404' in response.url or '/campaigns/404' in response.url:
            return False
        
        # Check content type (should be PDF)
        content_type = response.headers.get('Content-Type', '')
        if 'pdf' not in content_type.lower():
            return False
        
        return True
    except:
        return False


def scrape_edexcel_history_papers_direct(years=None):
    """
    Scrape papers by constructing URLs directly.
    
    Pearson URL pattern:
    https://qualifications.pearson.com/content/dam/pdf/A-Level/History/2015/Exam-materials/
    9hi0-{component}-{type}-{date}.pdf
    
    Where:
    - component: 1a, 1b, 2a-1, 2b-1, 30, 31, etc. (lowercase, dots become hyphens)
    - type: que (question), rms (mark scheme), pef (examiner report)
    - date: YYYYMMDD (varies by type and month)
    """
    
    SUBJECT = {
        'name': 'History',
        'code': '9HI0',
        'qualification': 'A-Level',
        'exam_board': 'Edexcel',
        'years': years or [2024, 2023, 2022, 2021, 2020]
    }
    
    print("=" * 60)
    print("EDEXCEL HISTORY - DIRECT URL CONSTRUCTION")
    print("=" * 60)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Board: {SUBJECT['exam_board']}")
    print(f"Years: {SUBJECT['years']}")
    print(f"\nThis should take 1-2 minutes...\n")
    
    # Get component codes from database
    components = get_component_codes_from_db()
    
    if not components:
        print("❌ No components found! Run topic scraper first.")
        return []
    
    # PDF base URL
    base_url = "https://qualifications.pearson.com/content/dam/pdf/A-Level/History/2015/Exam-materials/"
    
    # Document type codes
    doc_types = {
        'que': 'Question Paper',
        'rms': 'Mark Scheme',
        'pef': 'Examiner Report'
    }
    
    # Common date patterns for each exam series
    # Format: (month, day) - Pearson uses specific dates
    date_patterns = {
        'June': [
            ('05', '24'),  # May 24 (question papers released)
            ('06', '01'),  # June 1
            ('08', '15'),  # August 15 (marks/reports)
            ('08', '20'),  # August 20
        ],
        'November': [
            ('10', '24'),  # October 24
            ('11', '01'),  # November 1
            ('01', '15'),  # January 15 (next year - marks/reports)
        ],
        'January': [
            ('01', '15'),
            ('03', '15'),  # March (marks/reports)
        ]
    }
    
    papers = []
    checked = 0
    found = 0
    
    print("🔍 Checking URLs...\n")
    
    total_checks = len(components) * len(SUBJECT['years']) * len(doc_types) * 4
    print(f"   Will check up to {total_checks} URLs (component × year × type × date pattern)")
    print(f"   This may take a minute...\n")
    
    for component in components:
        # Convert component code for URL (lowercase with hyphens for 2022+, uppercase with underscores for 2020-2021)
        component_lower = component.lower().replace('.', '-')
        component_upper = component.upper().replace('.', '_')
        
        for year in SUBJECT['years']:
            # UK A-Levels only have June session (but COVID years had October)
            series = 'June'
            
            # Generate all possible days (01-31) for each month
            all_days = [f"{d:02d}" for d in range(1, 32)]
            
            # Year-specific month patterns (brute force all days)
            year_patterns = {
                2024: {
                    'que': [('05', day) for day in all_days] + [('06', day) for day in all_days],  # May-June
                    'rms': [('08', day) for day in all_days],  # August
                    'pef': [('08', day) for day in all_days]   # August
                },
                2023: {
                    'que': [('05', day) for day in all_days] + [('06', day) for day in all_days],
                    'rms': [('08', day) for day in all_days],
                    'pef': [('08', day) for day in all_days]
                },
                2022: {
                    'que': [('05', day) for day in all_days] + [('06', day) for day in all_days],
                    'rms': [('08', day) for day in all_days],
                    'pef': [('08', day) for day in all_days]
                },
                # COVID years: October exams, January results
                2021: {
                    'que': [('10', day) for day in all_days],  # October
                    'rms': [('01', day) for day in all_days],  # January
                    'pef': [('01', day) for day in all_days]   # January
                },
                2020: {
                    'que': [('10', day) for day in all_days],  # October
                    'rms': [('01', day) for day in all_days],  # January
                    'pef': [('01', day) for day in all_days]   # January
                },
            }
            
            if year not in year_patterns:
                continue
            
            # Determine filename format (lowercase/hyphens for 2022+, uppercase/underscores for 2020-2021)
            if year >= 2022:
                component_url = component_lower
                separator = '-'
                code_case = '9hi0'
            else:
                component_url = component_upper
                separator = '_'
                code_case = '9HI0'
            
            for type_code, type_name in doc_types.items():
                # Get date patterns for this year and doc type
                dates_to_try = year_patterns[year].get(type_code, [('05', '24')])
                
                for month, day in dates_to_try:
                    # Construct URL
                    date_str = f"{year}{month}{day}"
                    filename = f"{code_case}{separator}{component_url}{separator}{type_code}{separator}{date_str}.pdf"
                    url = base_url + filename
                    
                    checked += 1
                    
                    # Check if URL exists
                    if check_url_exists(url):
                            found += 1
                            
                            # Determine paper number from component code
                            if component[0] == '1':
                                paper_number = 1
                            elif component[0] == '2':
                                paper_number = 2
                            else:
                                paper_number = 3
                            
                            papers.append({
                                'year': year,
                                'exam_series': series,
                                'paper_number': paper_number,
                                'component_code': component,
                                'tier': None,
                                'doc_type': type_name,
                                'url': url,
                                'filename': filename
                            })
                            
                            print(f"   ✓ {year} {series} - {type_name} - {component}")
                            break  # Found it, no need to try other dates
        
        # Progress update every 5 components
        if (components.index(component) + 1) % 5 == 0:
            print(f"   Progress: {components.index(component) + 1}/{len(components)} components checked ({found} papers found)")
    
    print(f"\n✅ Checked {checked} URLs, found {found} papers")
    
    # Breakdown
    print("\n📊 Breakdown:")
    doc_types_found = Counter(p['doc_type'] for p in papers)
    for doc_type, count in doc_types_found.items():
        print(f"   {doc_type}: {count}")
    
    years_found = Counter(p['year'] for p in papers)
    print(f"\n   Years: {dict(sorted(years_found.items(), reverse=True))}")
    
    components_found = Counter(p['component_code'] for p in papers)
    print(f"\n   Components: {len(components_found)} unique")
    
    return papers


def group_papers_by_set(papers):
    """Group papers into complete sets by year + series + component."""
    
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
    papers = scrape_edexcel_history_papers_direct()
    
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
    print(f"   Topics: ✅ 559 topics")
    print(f"   Papers: ✅ {len(paper_sets)} paper sets")
    print(f"\n💡 Can be re-run safely!")
    
    return len(paper_sets)


if __name__ == '__main__':
    main()

