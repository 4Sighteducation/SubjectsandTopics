"""
EDEXCEL GCSE - OVERNIGHT BATCH SCRAPER V2
Improved with:
- Better topic extraction (uses A-Level proven patterns)
- Proper deduplication
- Subject-type detection
- Error recovery
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

# Paths
script_dir = Path(__file__).parent
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
from supabase import create_client
from pypdf import PdfReader

load_dotenv(env_path)
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

# Upload helper
import importlib.util
upload_helper_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\upload_papers_to_staging.py")
spec = importlib.util.spec_from_file_location("upload_papers_to_staging", upload_helper_path)
upload_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload_module)
upload_papers_to_staging = upload_module.upload_papers_to_staging

# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def download_pdf(url, code):
    """Download PDF."""
    try:
        response = requests.get(url, timeout=30)
        pdf = PdfReader(BytesIO(response.content))
        text = '\n'.join(page.extract_text() for page in pdf.pages)
        
        # Save debug
        debug_dir = script_dir / 'debug-gcse'
        debug_dir.mkdir(exist_ok=True)
        (debug_dir / f'{code}.txt').write_text(text, encoding='utf-8')
        
        return text
    except Exception as e:
        log(f"ERROR downloading {code}: {e}")
        return None


def parse_gcse_topics(text, code, name):
    """Smarter GCSE topic extraction."""
    
    topics = []
    lines = text.split('\n')
    
    # Detect subject type
    is_language = any(lang in name for lang in ['Arabic', 'Chinese', 'French', 'German', 'Greek', 
                                                  'Gujarati', 'Italian', 'Japanese', 'Persian', 
                                                  'Portuguese', 'Russian', 'Spanish', 'Turkish', 'Urdu'])
    
    is_science = 'Science' in name or 'Astronomy' in name
    is_table_based = any(word in name for word in ['Business', 'Geography', 'Psychology', 'Religious'])
    
    # Pattern 1: Papers/Components (Level 0)
    paper_pattern = r'^(?:Paper|Component)\s+(\d+):?\s*(.{5,150})$'
    papers_found = {}
    for line in lines:
        match = re.match(paper_pattern, line.strip(), re.IGNORECASE)
        if match:
            num = match.group(1)
            title = re.sub(r'\s+', ' ', match.group(2)).strip()
            if num not in papers_found and len(title) > 5:
                papers_found[num] = title
    
    if papers_found:
        for num in sorted(papers_found.keys(), key=int):
            topics.append({
                'code': f'Paper{num}',
                'title': f'Paper {num}: {papers_found[num]}',
                'level': 0,
                'parent': None
            })
    
    # Pattern 2: For languages - look for themes
    if is_language:
        theme_pattern = r'Theme\s+(\d+):?\s*(.{10,100})'
        for line in lines:
            match = re.search(theme_pattern, line, re.IGNORECASE)
            if match:
                num = match.group(1)
                title = re.sub(r'\s+', ' ', match.group(2)).strip()[:150]
                code_str = f'Theme{num}'
                if not any(t['code'] == code_str for t in topics) and len(title) > 5:
                    parent = topics[0]['code'] if topics else None
                    topics.append({
                        'code': code_str,
                        'title': f'Theme {num}: {title}',
                        'level': 1,
                        'parent': parent
                    })
    
    # Pattern 3: Science-style "Topic X:"
    if is_science or len(topics) < 5:
        topic_pattern = r'^Topic\s+(\d+[A-Z]?):\s*(.{10,150})$'
        for line in lines:
            match = re.match(topic_pattern, line.strip(), re.IGNORECASE)
            if match:
                num = match.group(1)
                title = re.sub(r'\s+', ' ', match.group(2)).strip()
                code_str = f'Topic{num}'
                if not any(t['code'] == code_str for t in topics):
                    parent = topics[0]['code'] if topics else None
                    topics.append({
                        'code': code_str,
                        'title': f'Topic {num}: {title}',
                        'level': 1 if topics else 0,
                        'parent': parent
                    })
    
    # Pattern 4: Numbered sections (1.1, 1.2, 2.1)
    if is_table_based or len(topics) < 5:
        sections = {}
        for line in lines:
            match = re.match(r'^(\d{1,2})\.(\d{1,2})\s+(.{10,300})$', line.strip())
            if match:
                major, minor, title = match.groups()
                title = re.sub(r'\s+', ' ', title).strip()
                
                # Skip appendices
                if any(skip in title.lower() for skip in ['introduction', 'assessment', 'appendix']):
                    continue
                
                if major not in sections:
                    sections[major] = []
                sections[major].append((minor, title[:300]))
        
        if sections and len(sections) >= 3:
            # Create topics if we don't have many yet
            if not topics:
                topics.append({'code': 'Content', 'title': 'Subject Content', 'level': 0, 'parent': None})
            
            parent = topics[0]['code']
            for major in sorted(sections.keys(), key=int)[:15]:
                section_code = f'S{major}'
                if not any(t['code'] == section_code for t in topics):
                    topics.append({
                        'code': section_code,
                        'title': f'Section {major}',
                        'level': 1,
                        'parent': parent
                    })
                
                for minor, title in sections[major][:12]:
                    sub_code = f'S{major}_{minor}'
                    if not any(t['code'] == sub_code for t in topics):
                        topics.append({
                            'code': sub_code,
                            'title': f'{major}.{minor} {title}',
                            'level': 2,
                            'parent': section_code
                        })
    
    # Final deduplication
    unique_topics = []
    seen_codes = set()
    for t in topics:
        if t['code'] not in seen_codes:
            unique_topics.append(t)
            seen_codes.add(t['code'])
    
    return unique_topics


def upload_topics(code, name, pdf_url, topics):
    """Upload with error handling."""
    try:
        result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{name} (GCSE)",
            'subject_code': code,
            'qualification_type': 'GCSE',
            'specification_url': pdf_url,
            'exam_board': 'Edexcel'
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = result.data[0]['id']
        
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
        
        inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        
        # Link
        code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
        for topic in topics:
            if topic['parent']:
                parent_id = code_to_id.get(topic['parent'])
                child_id = code_to_id.get(topic['code'])
                if parent_id and child_id:
                    supabase.table('staging_aqa_topics').update({
                        'parent_topic_id': parent_id
                    }).eq('id', child_id).execute()
        
        return len(inserted.data)
    except Exception as e:
        log(f"ERROR uploading {code}: {e}")
        return 0


def main():
    """Overnight processing."""
    
    start = datetime.now()
    print("\n" + "=" * 80)
    print("🌙 GCSE OVERNIGHT SCRAPER V2")
    print("=" * 80)
    print(f"Started: {start.strftime('%H:%M:%S')}\n")
    
    # Load subjects
    subjects_file = script_dir / 'gcse-subjects.json'
    with open(subjects_file, 'r') as f:
        subjects = json.load(f)
    
    log(f"Processing {len(subjects)} GCSE subjects")
    
    results = {'success': [], 'failed': [], 'low_topics': []}
    
    # TOPICS ONLY for now (papers would add 2+ hours)
    for idx, subj in enumerate(subjects, 1):
        code, name, pdf_url = subj['code'], subj['name'], subj['pdf_url']
        
        log(f"[{idx}/{len(subjects)}] {name}...")
        
        try:
            text = download_pdf(pdf_url, code)
            if not text:
                results['failed'].append(name)
                continue
            
            topics = parse_gcse_topics(text, code, name)
            
            if len(topics) >= 3:
                uploaded = upload_topics(code, name, pdf_url, topics)
                if uploaded > 0:
                    results['success'].append({'name': name, 'topics': uploaded})
                    log(f"   ✅ {uploaded} topics")
                else:
                    results['failed'].append(name)
            else:
                log(f"   ⚠️  Only {len(topics)} topics")
                results['low_topics'].append(name)
        
        except Exception as e:
            log(f"   ❌ {e}")
            results['failed'].append(name)
    
    # Summary
    print("\n" + "=" * 80)
    print("GCSE TOPICS SUMMARY")
    print("=" * 80)
    print(f"✅ Success: {len(results['success'])}")
    total = sum(r['topics'] for r in results['success'])
    for r in results['success']:
        print(f"   {r['name']}: {r['topics']}")
    print(f"\nTOTAL: {total} topics")
    
    if results['low_topics']:
        print(f"\n⚠️  Low topics ({len(results['low_topics'])}): Need manual review")
    if results['failed']:
        print(f"\n❌ Failed ({len(results['failed'])})")
    
    duration = datetime.now() - start
    print(f"\nDuration: {duration}")
    print("=" * 80)


if __name__ == '__main__':
    main()

