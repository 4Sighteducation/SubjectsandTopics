"""
GCSE SMART BATCH SCRAPER
Focuses on EXAMINED CONTENT ONLY
- Finds "Paper X" sections (examined components)
- Extracts content from exam specifications
- Skips non-examined components (NEA, coursework, practical)
- Uses proven A-Level patterns

Excludes: Languages (done), Art (done), Astronomy (done), Drama (done)
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

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
from supabase import create_client
from pypdf import PdfReader

load_dotenv(env_path)
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

# Subjects to process (excluding already-done ones)
SUBJECTS = [
    {'code': 'GCSE-Business', 'name': 'Business', 'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Business/2017/specification-and-sample-assessments/gcse-business-spec-2017.pdf'},
    {'code': 'GCSE-Citizenship', 'name': 'Citizenship Studies', 'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Citizenship%20Studies/2016/Specification%20and%20sample%20assessments/specification-gcse-l1-l2-in-citizenship.pdf'},
    {'code': 'GCSE-CompSci', 'name': 'Computer Science', 'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Computer%20Science/2020/specification-and-sample-assessments/GCSE_L1_L2_Computer_Science_2020_Specification.pdf'},
    {'code': 'GCSE-DT', 'name': 'Design and Technology', 'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/design-and-technology/2017/specification-and-sample-assessments/Pearson_Edexcel_GCSE_9_to_1_in_Design_and_Technology_Specification_issue3.pdf'},
    {'code': 'GCSE-GeoA', 'name': 'Geography A', 'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Geography-A/2016/specification-and-sample-assessments/gcse-2016-l12-geography-a-spec.pdf'},
    {'code': 'GCSE-GeoB', 'name': 'Geography B', 'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Geography-B/2016/specification-and-sample-assessments/gcse-2016-l12-geography-b-spec.pdf'},
    {'code': 'GCSE-History', 'name': 'History', 'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/History/2016/specification-and-sample-assessments/gcse-9-1-history-specification.pdf'},
    {'code': 'GCSE-Maths', 'name': 'Mathematics', 'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/mathematics/2015/specification-and-sample-assesment/gcse-maths-2015-specification.pdf'},
    {'code': 'GCSE-Music', 'name': 'Music', 'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Music/2016/specification/Pearson_Edexcel_GCSE_9_to_1_in_Music_Specification_issue4.pdf'},
    {'code': 'GCSE-PE', 'name': 'Physical Education', 'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Physical%20Education/2016/Specification%20and%20sample%20assessments/GCSE-physical-education-2016-specification.pdf'},
    {'code': 'GCSE-Psychology', 'name': 'Psychology', 'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Psychology/2017/Specification%20and%20sample%20assessments/gcse-psychology-specification.pdf'},
    {'code': 'GCSE-RSA', 'name': 'Religious Studies A', 'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Religious%20Studies/2016/Specification%20and%20sample%20assessments/specification-gcse-l1-l2-religious-studies-a-june-2016-draft-4.pdf'},
    {'code': 'GCSE-RSB', 'name': 'Religious Studies B', 'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Religious%20Studies/2016/Specification%20and%20sample%20assessments/specification-gcse-l1-l2-religious-studies-b-june-2016-draft-4.pdf'},
    {'code': 'GCSE-Science', 'name': 'Combined Science', 'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Science/2016/Specification/gcse-combinedscience-spec.pdf'},
    {'code': 'GCSE-Statistics', 'name': 'Statistics', 'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Statistics/2017/specification-and-sample-assessments/gcse-9-1-statistics-specification.pdf'},
]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def download_pdf(url, code):
    """Download PDF and save debug."""
    try:
        response = requests.get(url, timeout=30)
        pdf = PdfReader(BytesIO(response.content))
        text = '\n'.join(page.extract_text() for page in pdf.pages)
        
        debug_dir = Path('debug-gcse-batch')
        debug_dir.mkdir(exist_ok=True)
        (debug_dir / f'{code}.txt').write_text(text, encoding='utf-8')
        
        return text
    except Exception as e:
        log(f"ERROR download {code}: {e}")
        return None


def extract_examined_content(text, code, name):
    """Smart extraction focusing on EXAMINED content."""
    
    topics = []
    lines = text.split('\n')
    
    # Step 1: Find Papers (examined components)
    papers_found = {}
    for line in lines:
        # Match "Paper X:" with description
        match = re.match(r'^Paper\s+(\d+):\s*(.{10,150})$', line.strip(), re.IGNORECASE)
        if match:
            num = match.group(1)
            title = re.sub(r'\s+', ' ', match.group(2)).strip()
            # Skip if it's a practical/NEA component
            if not any(skip in title.lower() for skip in ['practical', 'coursework', 'nea', 'non-examined']):
                if num not in papers_found or len(title) > len(papers_found.get(num, '')):
                    papers_found[num] = title
    
    # Add papers as Level 0
    for num in sorted(papers_found.keys(), key=int):
        topics.append({
            'code': f'Paper{num}',
            'title': f'Paper {num}: {papers_found[num]}',
            'level': 0,
            'parent': None
        })
    
    # Step 2: Extract topics/themes from examined papers
    # Look for Topic patterns
    topic_matches = re.findall(r'^Topic\s+(\d+[A-Z]?)\s*[–:-]\s*(.{10,150})$', text, re.MULTILINE | re.IGNORECASE)
    
    if topic_matches and len(topic_matches) >= 3:
        unique = {}
        for num, title in topic_matches:
            if num not in unique:
                unique[num] = re.sub(r'\s+', ' ', title).strip()
        
        parent = topics[0]['code'] if topics else None
        for num in sorted(unique.keys(), key=lambda x: int(re.search(r'\d+', x).group())):
            topics.append({
                'code': f'Topic{num}',
                'title': f'Topic {num}: {unique[num]}',
                'level': 1,
                'parent': parent
            })
    
    # Step 3: Look for numbered sections (table-based subjects)
    elif 'Geography' in name or 'Business' in name or 'Psychology' in name or 'Religious' in name:
        sections = {}
        for line in lines:
            match = re.match(r'^(\d{1,2})\.(\d{1,2})\s+(.{10,500})$', line.strip())
            if match:
                major, minor, title = match.groups()
                title = re.sub(r'\s+', ' ', title).strip()
                
                # Skip non-content sections
                if any(skip in title.lower() for skip in ['introduction', 'assessment', 'appendix']):
                    continue
                
                if major not in sections:
                    sections[major] = []
                if len(title) > 10:
                    sections[major].append((minor, title[:400]))
        
        if sections:
            if not topics:
                topics.append({'code': 'Content', 'title': 'Examined Content', 'level': 0, 'parent': None})
            
            parent = topics[0]['code']
            for major in sorted(sections.keys(), key=int)[:12]:
                section_code = f'S{major}'
                topics.append({
                    'code': section_code,
                    'title': f'Section {major}',
                    'level': 1,
                    'parent': parent
                })
                
                for minor, title in sections[major][:10]:
                    topics.append({
                        'code': f'S{major}_{minor}',
                        'title': f'{major}.{minor} {title}',
                        'level': 2,
                        'parent': section_code
                    })
    
    # Step 4: Look for Theme patterns
    else:
        theme_matches = re.findall(r'^Theme\s+(\d+)[:\s]+(.{10,100})$', text, re.MULTILINE | re.IGNORECASE)
        if theme_matches and len(theme_matches) >= 2:
            unique = {}
            for num, title in theme_matches:
                if num not in unique:
                    unique[num] = re.sub(r'\s+', ' ', title).strip()[:200]
            
            parent = topics[0]['code'] if topics else None
            for num in sorted(unique.keys(), key=int):
                topics.append({
                    'code': f'Theme{num}',
                    'title': f'Theme {num}: {unique[num]}',
                    'level': 1,
                    'parent': parent
                })
    
    # Deduplicate
    unique_topics = []
    seen = set()
    for t in topics:
        if t['code'] not in seen:
            unique_topics.append(t)
            seen.add(t['code'])
    
    return unique_topics


def upload_topics(code, name, pdf_url, topics):
    """Upload to database."""
    try:
        result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{name} (GCSE)",
            'subject_code': code,
            'qualification_type': 'GCSE',
            'specification_url': pdf_url,
            'exam_board': 'Edexcel'
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = result.data[0]['id']
        
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'exam_board': 'Edexcel'
        } for t in topics]
        
        inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        
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
        log(f"ERROR upload {code}: {e}")
        return 0


def main():
    """Process remaining GCSE subjects."""
    
    start = datetime.now()
    
    print("=" * 80)
    print("GCSE SMART BATCH SCRAPER - EXAMINED CONTENT ONLY")
    print("=" * 80)
    print(f"Started: {start.strftime('%H:%M:%S')}")
    print(f"Processing {len(SUBJECTS)} subjects\n")
    
    results = {'success': [], 'failed': []}
    
    for idx, subj in enumerate(SUBJECTS, 1):
        code, name, pdf_url = subj['code'], subj['name'], subj['pdf_url']
        
        log(f"[{idx}/{len(SUBJECTS)}] {name}...")
        
        try:
            text = download_pdf(pdf_url, code)
            if not text:
                results['failed'].append(name)
                continue
            
            topics = extract_examined_content(text, code, name)
            
            if len(topics) >= 2:
                uploaded = upload_topics(code, name, pdf_url, topics)
                if uploaded > 0:
                    results['success'].append({'name': name, 'topics': uploaded})
                    log(f"   ✅ {uploaded} topics (examined content)")
                else:
                    results['failed'].append(name)
            else:
                log(f"   ⚠️  Only {len(topics)} topics - needs manual")
                results['failed'].append(name)
        
        except Exception as e:
            log(f"   ❌ {e}")
            results['failed'].append(name)
        
        time.sleep(0.5)
    
    # Summary
    duration = datetime.now() - start
    
    print("\n" + "=" * 80)
    print("GCSE BATCH SCRAPER - SUMMARY")
    print("=" * 80)
    print(f"Duration: {duration}")
    
    if results['success']:
        print(f"\n✅ Success: {len(results['success'])}/{len(SUBJECTS)}")
        total = sum(r['topics'] for r in results['success'])
        for r in results['success']:
            print(f"   • {r['name']}: {r['topics']} topics")
        print(f"\n   TOTAL: {total} topics (examined content)")
    
    if results['failed']:
        print(f"\n⚠️  Failed/Manual needed: {len(results['failed'])}")
        for name in results['failed']:
            print(f"   • {name}")
    
    print("\n" + "=" * 80)
    
    # Save report
    report = Path('GCSE-BATCH-REPORT.txt')
    with open(report, 'w') as f:
        f.write(f"GCSE Smart Batch Scraper Report\n")
        f.write(f"Duration: {duration}\n")
        f.write(f"Success: {len(results['success'])}/{len(SUBJECTS)}\n")
        f.write(f"Total topics: {sum(r['topics'] for r in results['success'])}\n")
    
    log(f"Report saved: {report}")


if __name__ == '__main__':
    main()

