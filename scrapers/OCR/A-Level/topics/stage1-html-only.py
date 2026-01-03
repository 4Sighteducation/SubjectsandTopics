"""
OCR A-Level Stage 1 Only - HTML Structure Scraper
==================================================

Gets ONLY the clean structure from "specification at a glance" HTML.
No PDF, no AI - just the baseline hierarchy.

This is useful for:
1. Quick baseline scraping of all subjects
2. Debugging which subjects have unusual structures
3. Getting foundation before attempting PDF extraction

Usage:
    python stage1-html-only.py AL-BiologyA
    python stage1-html-only.py --all
"""

import os
import sys
import re
import json
import time
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from supabase import create_client
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))


class Stage1Scraper:
    """HTML-only scraper for baseline structure."""
    
    def __init__(self, subject_info: Dict):
        self.subject = subject_info
        self.topics = []
        
        # Setup Selenium
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def __del__(self):
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except:
                pass
    
    def scrape_html(self) -> List[Dict]:
        """Scrape HTML for structure."""
        print(f"\n{'='*80}")
        print(f"STAGE 1 ONLY: {self.subject['name']} ({self.subject['code']})")
        print(f"{'='*80}")
        
        url = self.subject['at_a_glance_url']
        print(f"[INFO] Loading: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(5)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find content overview
            content_heading = None
            for heading in soup.find_all(['h2', 'h3', 'h4']):
                if 'content' in heading.get_text().lower() and 'overview' in heading.get_text().lower():
                    content_heading = heading
                    break
            
            if not content_heading:
                print("[WARN] No 'Content overview' found, trying all headings...")
            
            # Extract all module/unit/component headings with their lists
            topics = []
            seen_units = set()
            
            headings = soup.find_all(['h3', 'h4'])
            
            for heading in headings:
                heading_text = heading.get_text().strip()
                
                # Pattern 1: "Module X: Title"
                module_match = re.match(r'Module (\d+):\s*(.+)', heading_text, re.IGNORECASE)
                if module_match and module_match.group(1) not in seen_units:
                    num = module_match.group(1)
                    seen_units.add(num)
                    code = f'Module{num}'
                    
                    topics.append({'code': code, 'title': heading_text, 'level': 0, 'parent': None})
                    print(f"[L0] {code}: {heading_text}")
                    
                    # Get L1 bullet points
                    ul = heading.find_next_sibling('ul')
                    if ul:
                        for i, li in enumerate(ul.find_all('li', recursive=False), 1):
                            topics.append({
                                'code': f'{code}_{i}',
                                'title': li.get_text().strip(),
                                'level': 1,
                                'parent': code
                            })
                    continue
                
                # Pattern 2: "Unit group X"
                unit_match = re.match(r'Unit\s+(?:group\s+)?(\d+)', heading_text, re.IGNORECASE)
                if unit_match and unit_match.group(1) not in seen_units:
                    num = unit_match.group(1)
                    seen_units.add(num)
                    code = f'Unit{num}'
                    
                    topics.append({'code': code, 'title': heading_text, 'level': 0, 'parent': None})
                    print(f"[L0] {code}: {heading_text}")
                    
                    ul = heading.find_next_sibling('ul')
                    if ul:
                        for i, li in enumerate(ul.find_all('li', recursive=False), 1):
                            topics.append({
                                'code': f'{code}_{i}',
                                'title': li.get_text().strip(),
                                'level': 1,
                                'parent': code
                            })
                    continue
                
                # Pattern 3: "Component X"
                comp_match = re.match(r'(?:Component|Paper)\s+(\d+)', heading_text, re.IGNORECASE)
                if comp_match and comp_match.group(1) not in seen_units:
                    num = comp_match.group(1)
                    seen_units.add(num)
                    code = f'Component{num}'
                    
                    topics.append({'code': code, 'title': heading_text, 'level': 0, 'parent': None})
                    print(f"[L0] {code}: {heading_text}")
                    
                    ul = heading.find_next_sibling('ul')
                    if ul:
                        for i, li in enumerate(ul.find_all('li', recursive=False), 1):
                            topics.append({
                                'code': f'{code}_{i}',
                                'title': li.get_text().strip(),
                                'level': 1,
                                'parent': code
                            })
                    continue
            
            l0_count = len([t for t in topics if t['level'] == 0])
            l1_count = len([t for t in topics if t['level'] == 1])
            
            print(f"\n[OK] Extracted: {l0_count} L0 units + {l1_count} L1 topics = {len(topics)} total")
            
            return topics
            
        except Exception as e:
            print(f"[ERROR] Failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def upload(self, topics: List[Dict]) -> bool:
        """Upload to Supabase."""
        if not topics:
            return False
        
        try:
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': f"{self.subject['name']} ({self.subject['qualification']})",
                'subject_code': self.subject['code'],
                'qualification_type': self.subject['qualification'],
                'specification_url': self.subject['pdf_url'],
                'exam_board': self.subject['exam_board']
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
                'exam_board': self.subject['exam_board']
            } for t in topics]
            
            inserted_result = supabase.table('staging_aqa_topics').insert(to_insert).execute()
            
            # Link hierarchy
            code_to_id = {t['topic_code']: t['id'] for t in inserted_result.data}
            linked = 0
            
            for topic in topics:
                if topic['parent']:
                    parent_id = code_to_id.get(topic['parent'])
                    child_id = code_to_id.get(topic['code'])
                    if parent_id and child_id:
                        supabase.table('staging_aqa_topics').update({
                            'parent_topic_id': parent_id
                        }).eq('id', child_id).execute()
                        linked += 1
            
            print(f"[OK] Uploaded {len(topics)} topics, linked {linked} relationships")
            return True
            
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            return False
    
    def run(self) -> bool:
        topics = self.scrape_html()
        if topics:
            return self.upload(topics)
        return False


def load_subjects():
    subjects_file = Path(__file__).parent.parent / "ocr-alevel-subjects.json"
    with open(subjects_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('subject', nargs='?')
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()
    
    subjects = load_subjects()
    
    if args.all:
        print(f"Scraping HTML structure for all {len(subjects)} subjects...\n")
        for code, info in subjects.items():
            scraper = Stage1Scraper(info)
            scraper.run()
            time.sleep(2)
    else:
        if not args.subject or args.subject not in subjects:
            print(f"Available: {', '.join(subjects.keys())}")
            sys.exit(1)
        
        scraper = Stage1Scraper(subjects[args.subject])
        sys.exit(0 if scraper.run() else 1)


if __name__ == '__main__':
    main()

