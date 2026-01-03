"""
GCSE Astronomy - Proper Topic Scraper
Extracts full topic names (not just "Topic X")
NO truncation - preserves complete content
"""

import os
import sys
import re
import requests
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv
from supabase import create_client
from pypdf import PdfReader

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT = {
    'code': 'GCSE-Astronomy',
    'name': 'Astronomy',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Astronomy/2017/Specification%20and%20sample%20assessments/gcse-astronomy-specification.pdf'
}


def download_pdf():
    """Download PDF."""
    print("[INFO] Downloading PDF...")
    try:
        response = requests.get(SUBJECT['pdf_url'], timeout=30)
        response.raise_for_status()
        
        pdf = PdfReader(BytesIO(response.content))
        print(f"[OK] Downloaded {len(pdf.pages)} pages")
        
        text = '\n'.join(page.extract_text() for page in pdf.pages)
        
        Path('debug-gcse-astronomy.txt').write_text(text, encoding='utf-8')
        print(f"[OK] Saved debug file")
        
        return text
    except Exception as e:
        print(f"[ERROR] {e}")
        return None


def parse_astronomy_topics(text):
    """Parse Astronomy with FULL topic names - NO truncation."""
    
    print("\n[INFO] Parsing Astronomy topics...")
    topics = []
    
    # Level 0: Papers
    topics.extend([
        {'code': 'Paper1', 'title': 'Paper 1: Naked-eye Astronomy', 'level': 0, 'parent': None},
        {'code': 'Paper2', 'title': 'Paper 2: Telescopic Astronomy', 'level': 0, 'parent': None},
    ])
    
    lines = text.split('\n')
    
    # Find topics with pattern: "Topic X: Full Topic Name"
    # Use greedy matching to get FULL names
    topic_matches = []
    
    for i, line in enumerate(lines):
        # Match: Topic 1 – Planet Earth, Topic 2 – Observational Astronomy, etc.
        # Note: uses en-dash (–) not colon
        match = re.match(r'^Topic\s+(\d+)\s*[–:-]\s*(.+)$', line.strip(), re.IGNORECASE)
        if match:
            num = match.group(1)
            title = match.group(2).strip()
            
            # Clean but don't truncate
            title = re.sub(r'\s+', ' ', title)
            
            # Only add if it looks like a real topic (not a TOC entry)
            if len(title) > 5 and len(title) < 100:
                topic_matches.append((num, title))
    
    # Deduplicate (topics appear multiple times in spec)
    unique_topics = {}
    for num, title in topic_matches:
        if num not in unique_topics:
            unique_topics[num] = title
    
    print(f"[OK] Found {len(unique_topics)} unique topics")
    
    # Add topics as Level 1 - assign to correct paper
    # Topics 1-8 → Paper 1 (Naked-eye)
    # Topics 9-16 → Paper 2 (Telescopic)
    for num in sorted(unique_topics.keys(), key=int):
        parent_paper = 'Paper1' if int(num) <= 8 else 'Paper2'
        topics.append({
            'code': f'Topic{num}',
            'title': f'Topic {num}: {unique_topics[num]}',
            'level': 1,
            'parent': parent_paper
        })
        print(f"   Topic {num}: {unique_topics[num]} → {parent_paper}")
    
    # Now find subtopics (numbered items under each topic)
    # Pattern: numbers like "1.", "2." followed by content
    
    for i, line in enumerate(lines):
        # Match subtopic numbers: "1. Know that...", "2. Understand..."
        match = re.match(r'^(\d+)\.\s+(.+)$', line.strip())
        if match:
            sub_num = match.group(1)
            content = match.group(2).strip()
            
            # Build full content by looking ahead
            full_content = content
            for j in range(i+1, min(i+5, len(lines))):
                next_line = lines[j].strip()
                
                # Stop if hit another numbered item or topic
                if re.match(r'^\d+\.', next_line) or re.match(r'^Topic \d', next_line):
                    break
                
                # Stop if empty
                if not next_line:
                    break
                
                # Append
                if next_line[0].islower() or len(full_content) < 200:
                    full_content += ' ' + next_line
            
            # Clean but preserve full content
            full_content = re.sub(r'\s+', ' ', full_content).strip()
            
            # Find which topic this belongs to (look backward for last Topic match)
            parent_topic = None
            for k in range(i-1, max(0, i-50), -1):
                topic_match = re.match(r'^Topic\s+(\d+)\s*[–:-]', lines[k].strip(), re.IGNORECASE)
                if topic_match:
                    parent_topic = f'Topic{topic_match.group(1)}'
                    break
            
            if parent_topic and len(full_content) > 10:
                # Only add if we haven't seen this exact subtopic
                code = f'{parent_topic}_{sub_num}'
                if not any(t['code'] == code for t in topics):
                    topics.append({
                        'code': code,
                        'title': f'{sub_num}. {full_content}',
                        'level': 2,
                        'parent': parent_topic
                    })
    
    print(f"[OK] Added subtopics")
    
    return topics


def upload_topics(topics):
    """Upload to Supabase."""
    
    print(f"\n[INFO] Uploading {len(topics)} topics...")
    
    try:
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT['name']} (GCSE)",
            'subject_code': SUBJECT['code'],
            'qualification_type': 'GCSE',
            'specification_url': SUBJECT['pdf_url'],
            'exam_board': 'Edexcel'
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared old topics")
        
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'exam_board': 'Edexcel'
        } for t in topics]
        
        inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted.data)} topics")
        
        code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
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
        
        print(f"[OK] Linked {linked} relationships")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 80)
    print("GCSE ASTRONOMY - PROPER TOPIC SCRAPER")
    print("=" * 80)
    print("Full topic names - NO truncation\n")
    
    try:
        text = download_pdf()
        if not text:
            return
        
        topics = parse_astronomy_topics(text)
        
        levels = {}
        for t in topics:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print(f"\n[INFO] Extracted {len(topics)} topics")
        print(f"   Level 0 (Paper): {levels.get(0, 0)}")
        print(f"   Level 1 (Topics): {levels.get(1, 0)}")
        print(f"   Level 2 (Subtopics): {levels.get(2, 0)}")
        
        if upload_topics(topics):
            print("\n" + "=" * 80)
            print("[OK] GCSE ASTRONOMY COMPLETE!")
            print("=" * 80)
            print(f"Total: {len(topics)} topics with proper names")
    
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

