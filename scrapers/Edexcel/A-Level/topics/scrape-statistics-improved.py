"""
Edexcel Statistics (9ST0) - Improved Topic Scraper
Extracts full topic hierarchy with proper topic names and 3+ levels.
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
    'code': '9ST0',
    'name': 'Statistics',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/statistics/2017/Specification%20and%20Sample%20assessment%20material/a-level-statistics-specification.pdf'
}


def download_pdf():
    """Download and extract PDF text."""
    print("[INFO] Downloading PDF...")
    try:
        response = requests.get(SUBJECT['pdf_url'], timeout=30)
        response.raise_for_status()
        
        pdf = PdfReader(BytesIO(response.content))
        print(f"[OK] Downloaded {len(pdf.pages)} pages")
        
        full_text = '\n'.join(page.extract_text() for page in pdf.pages)
        
        # Save debug
        Path('debug-statistics-spec.txt').write_text(full_text, encoding='utf-8')
        print(f"[OK] Saved debug file")
        
        return full_text
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return None


def parse_statistics_topics(text):
    """Parse Statistics topics with full hierarchy."""
    
    print("\n[INFO] Parsing Statistics topics...")
    topics = []
    
    # Find the subject content section
    lines = text.split('\n')
    
    # Look for major topics (1  Topic name, 2  Topic name, etc.)
    # Pattern: number followed by 2+ spaces then capital letter
    major_topics = {}
    
    for i, line in enumerate(lines):
        # Match: "1  Numerical measures" or "1 Numerical measures"  
        # Look for: number, whitespace, then capital letter starting a title
        match = re.match(r'^(\d{1,2})\s+([A-Z][a-zA-Z\s,]+?)$', line)
        if match:
            topic_num = match.group(1)
            topic_title = match.group(2).strip()
            
            # Clean up title
            topic_title = re.sub(r'\s+', ' ', topic_title)
            
            # Filter out table of contents and other non-topic lines
            skip_words = ['Introduction', 'Subject content', 'Assessment', 'Administration', 
                          'Appendix', 'Formula', 'General information']
            if not any(word in topic_title for word in skip_words) and len(topic_title) > 5 and len(topic_title) < 100:
                major_topics[topic_num] = {
                    'title': topic_title,
                    'line': i,
                    'subtopics': []
                }
    
    print(f"[OK] Found {len(major_topics)} major topics")
    
    # Now find subtopics (1.1, 1.2, etc.) with FULL content
    for i, line in enumerate(lines):
        match = re.match(r'^(\d{1,2})\.(\d{1,2})\s+(.+)$', line)  # Greedy match!
        if match:
            major = match.group(1)
            minor = match.group(2)
            title = match.group(3).strip()
            
            # Build FULL title by looking ahead for continuation lines
            full_title = title
            for j in range(i+1, min(i+8, len(lines))):
                next_line = lines[j].strip()
                
                # Stop if we hit another numbered section or empty line
                if re.match(r'^\d+\.?\d*\s', next_line) or not next_line:
                    break
                
                # Append continuation
                full_title += ' ' + next_line
                
                # Stop if getting very long
                if len(full_title) > 700:
                    break
            
            # Clean but preserve full content
            full_title = re.sub(r'\s+', ' ', full_title).strip()
            
            if major in major_topics and len(full_title) > 5:
                major_topics[major]['subtopics'].append({
                    'num': minor,
                    'title': full_title
                })
    
    # Build hierarchy
    # Level 0: Papers
    topics.append({
        'code': 'Paper1',
        'title': 'Paper 1: Statistics in Practice',
        'level': 0,
        'parent': None
    })
    
    topics.append({
        'code': 'Paper2',
        'title': 'Paper 2: Statistical Methods',
        'level': 0,
        'parent': None
    })
    
    # Level 1: Major topics (1, 2, 3, etc.)
    # Topics 1-11 typically go under Paper 1, 12+ under Paper 2
    for topic_num in sorted(major_topics.keys(), key=int):
        topic_info = major_topics[topic_num]
        
        # Assign to paper based on topic number
        parent_paper = 'Paper1' if int(topic_num) <= 11 else 'Paper2'
        
        topic_code = f'Topic{topic_num}'
        topics.append({
            'code': topic_code,
            'title': f'{topic_num} - {topic_info["title"]}',
            'level': 1,
            'parent': parent_paper
        })
        
        # Level 2: Subtopics (1.1, 1.2, etc.)
        for subtopic in topic_info['subtopics']:
            topics.append({
                'code': f'T{topic_num}_{subtopic["num"]}',
                'title': f'{topic_num}.{subtopic["num"]} {subtopic["title"]}',
                'level': 2,
                'parent': topic_code
            })
    
    return topics


def upload_topics(topics):
    """Upload to Supabase."""
    
    print(f"\n[INFO] Uploading {len(topics)} topics to database...")
    
    try:
        # Get/create subject
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT['name']} (A-Level)",
            'subject_code': SUBJECT['code'],
            'qualification_type': 'A-Level',
            'specification_url': SUBJECT['pdf_url'],
            'exam_board': 'Edexcel'
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        # Clear old topics
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared old topics")
        
        # Insert topics
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'exam_board': 'Edexcel'
        } for t in topics]
        
        inserted_result = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted_result.data)} topics")
        
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
        
        print(f"[OK] Linked {linked} relationships")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main execution."""
    
    print("=" * 80)
    print("EDEXCEL STATISTICS (9ST0) - IMPROVED TOPIC SCRAPER")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}\n")
    
    try:
        # Download PDF
        text = download_pdf()
        if not text:
            return
        
        # Parse topics
        topics = parse_statistics_topics(text)
        
        print(f"\n[OK] Extracted {len(topics)} topics")
        
        # Show breakdown
        levels = {}
        for t in topics:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("\n[INFO] Level breakdown:")
        for level in sorted(levels.keys()):
            print(f"   Level {level}: {levels[level]} topics")
        
        # Upload
        if upload_topics(topics):
            print("\n" + "=" * 80)
            print("[OK] STATISTICS COMPLETE!")
            print("=" * 80)
            print(f"\nTotal: {len(topics)} topics with {max(levels.keys())+1} levels")
        
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
