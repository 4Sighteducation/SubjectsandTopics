#!/usr/bin/env python3
"""
GCSE Business Topics Scraper - GCSE Business (1BS0)

CRITICAL: This scraper ONLY extracts content from the PDF.
If extraction fails, it will STOP and report failure.
NEVER invent or guess topics!

Structure (from user investigation):
- 2 Level 0 themes: Theme 1 & Theme 2
- Each theme has 5 topics (1.1-1.5, 2.1-2.5)
- Each topic has h3 heading + 2-column table
- Extract from "Subject content" column (numbered 1.1.1, etc.)
- Extract from "What students need to learn" - sentences UP TO THE COLON only
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

import requests
import pdfplumber
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

# Subject configuration
SUBJECT = {
    'code': 'GCSE-Business',
    'name': 'Business',
    'level': 'GCSE',
    'exam_board': 'Edexcel',
    'spec_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Business/2017/specification-and-sample-assessments/gcse-business-spec-2017.pdf'
}

def download_pdf(url, output_path='temp_spec.pdf'):
    """Download PDF specification"""
    print(f"📥 Downloading PDF from: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers, allow_redirects=True)
    response.raise_for_status()
    
    # Check if we got HTML instead of PDF
    content_type = response.headers.get('content-type', '')
    if 'html' in content_type.lower():
        print(f"⚠️  Warning: Got HTML instead of PDF (Content-Type: {content_type})")
        print(f"⚠️  URL may be incorrect or require browser access")
    
    with open(output_path, 'wb') as f:
        f.write(response.content)
    
    print(f"✅ PDF downloaded: {output_path}")
    return output_path

def extract_topics_from_pdf(pdf_path):
    """
    Extract topics from GCSE Business PDF
    
    Structure:
    - Theme 1: Investigating small business (1.1-1.5)
    - Theme 2: Building a business (2.1-2.5)
    
    Each topic has:
    - h3 heading (e.g., "1.1 Enterprise and entrepreneurship")
    - 2-column table: "Subject content" | "What students need to learn"
    - Subject content numbered (1.1.1)
    - Learning outcomes: text up to colon (e.g., "Why new business ideas come about:")
    """
    
    topics = []
    
    # Level 0: Themes
    themes = [
        {
            'code': 'Theme1',
            'title': 'Theme 1: Investigating small business',
            'topics': ['1.1', '1.2', '1.3', '1.4', '1.5']
        },
        {
            'code': 'Theme2',
            'title': 'Theme 2: Building a business',
            'topics': ['2.1', '2.2', '2.3', '2.4', '2.5']
        }
    ]
    
    # Add themes as level 0
    for theme in themes:
        topics.append({
            'code': theme['code'],
            'title': theme['title'],
            'parent_code': None,
            'level': 0
        })
    
    print(f"📖 Extracting content from PDF...")
    
    with pdfplumber.open(pdf_path) as pdf:
        # Save all text for debugging
        debug_text = []
        
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text:
                debug_text.append(f"\n{'='*80}\nPAGE {page_num}\n{'='*80}\n{text}")
        
        # Save debug file
        debug_file = f'debug_gcse_business_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(debug_text))
        print(f"💾 Debug file saved: {debug_file}")
        
        # Now extract tables
        all_text = '\n'.join(debug_text)
        
        # Look for topic headings and tables
        current_topic = None
        
        for page in pdf.pages:
            text = page.extract_text() or ''
            tables = page.extract_tables()
            
            # Look for topic headings (e.g., "1.1 Enterprise and entrepreneurship")
            lines = text.split('\n')
            for i, line in enumerate(lines):
                # Check if line matches topic pattern (e.g., "1.1 Enterprise")
                if line.strip().startswith(('1.1 ', '1.2 ', '1.3 ', '1.4 ', '1.5 ',
                                            '2.1 ', '2.2 ', '2.3 ', '2.4 ', '2.5 ')):
                    topic_code = line.strip().split()[0]  # e.g., "1.1"
                    topic_title = line.strip()  # Full title
                    
                    # Determine parent theme
                    parent_code = 'Theme1' if topic_code.startswith('1.') else 'Theme2'
                    
                    # Add topic (Level 1)
                    topic_entry = {
                        'code': f'Topic{topic_code}',
                        'title': topic_title,
                        'parent_code': parent_code,
                        'level': 1
                    }
                    topics.append(topic_entry)
                    current_topic = topic_code
                    print(f"  📌 Found topic: {topic_title}")
            
            # Extract from tables
            if tables and current_topic:
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    
                    # Check if this is a "Subject content" / "What students need to learn" table
                    header = table[0] if table[0] else []
                    header_text = ' '.join([str(cell or '') for cell in header]).lower()
                    
                    if 'subject content' in header_text and 'what students need to learn' in header_text:
                        # Process table rows
                        for row in table[1:]:
                            if not row or len(row) < 2:
                                continue
                            
                            subject_content = str(row[0] or '').strip()
                            what_to_learn = str(row[1] or '').strip()
                            
                            # Skip empty or header rows
                            if not subject_content or subject_content.lower() in ['subject content', 'topic']:
                                continue
                            
                            # Extract subject content code and title
                            # Format: "1.1.1\nThe dynamic nature of business" or "1.1.1 The dynamic nature of business"
                            if current_topic in subject_content:
                                # This is a subtopic (Level 2)
                                parts = subject_content.split('\n', 1)
                                if len(parts) >= 2:
                                    code = parts[0].strip()
                                    title_part = parts[1].strip()
                                else:
                                    # Try splitting by space after code
                                    words = subject_content.split(maxsplit=1)
                                    if len(words) >= 2 and words[0].count('.') >= 2:
                                        code = words[0]
                                        title_part = words[1]
                                    else:
                                        continue
                                
                                # Add Level 2 topic
                                topics.append({
                                    'code': code,
                                    'title': f"{code} {title_part}",
                                    'parent_code': f'Topic{current_topic}',
                                    'level': 2
                                })
                                print(f"    📎 Found subtopic: {code} {title_part}")
                                
                                # Now extract learning outcomes from "What students need to learn"
                                # Format: bullet points, extract text UP TO THE COLON
                                if what_to_learn:
                                    lines = what_to_learn.split('\n')
                                    outcome_counter = 1
                                    
                                    for line in lines:
                                        line = line.strip()
                                        if not line or line.startswith(('•', '-', '●')) == False:
                                            # Not a bullet point, might be continuation
                                            if ':' not in line:
                                                continue
                                        
                                        # Remove bullet point
                                        line = line.lstrip('•-● ').strip()
                                        
                                        # Extract text up to colon
                                        if ':' in line:
                                            outcome_text = line.split(':')[0].strip()
                                            
                                            if outcome_text:
                                                outcome_code = f"{code}.{outcome_counter}"
                                                topics.append({
                                                    'code': outcome_code,
                                                    'title': outcome_text,
                                                    'parent_code': code,
                                                    'level': 3
                                                })
                                                print(f"      ✓ Learning outcome: {outcome_text}")
                                                outcome_counter += 1
    
    return topics

def upload_to_supabase(topics):
    """Upload topics to Supabase"""
    
    if not topics:
        print("❌ No topics to upload!")
        return False
    
    print(f"\n📊 Preparing to upload {len(topics)} topics...")
    
    # Show hierarchy summary
    levels = {}
    for topic in topics:
        level = topic.get('level', 0)
        levels[level] = levels.get(level, 0) + 1
    
    print("\n📈 Hierarchy breakdown:")
    for level in sorted(levels.keys()):
        print(f"  Level {level}: {levels[level]} topics")
    
    # Deduplicate by code
    unique_topics = []
    seen_codes = set()
    for topic in topics:
        if topic['code'] not in seen_codes:
            unique_topics.append(topic)
            seen_codes.add(topic['code'])
        else:
            print(f"⚠️  Skipping duplicate: {topic['code']}")
    
    print(f"\n📤 Uploading {len(unique_topics)} unique topics...")
    
    try:
        # Get/create subject
        print("[INFO] Creating/updating subject...")
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT['name']} (GCSE)",
            'subject_code': SUBJECT['code'],
            'qualification_type': 'GCSE',
            'specification_url': SUBJECT['spec_url'],
            'exam_board': 'Edexcel'
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        # Clear old topics
        print("\n[INFO] Clearing old topics...")
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared")
        
        # Insert topics
        print(f"\n[INFO] Uploading {len(unique_topics)} topics...")
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'parent_topic_code': t['parent_code']
        } for t in unique_topics]
        
        # Upload in batches
        batch_size = 100
        for i in range(0, len(to_insert), batch_size):
            batch = to_insert[i:i+batch_size]
            result = supabase.table('staging_aqa_topics').insert(batch).execute()
            print(f"  ✅ Uploaded batch {i//batch_size + 1} ({len(batch)} topics)")
        
        print(f"\n✅ Successfully uploaded {len(unique_topics)} topics!")
        return True
        
    except Exception as e:
        print(f"❌ Error uploading: {e}")
        return False

def main():
    """Main execution"""
    print("="*80)
    print("GCSE BUSINESS TOPICS SCRAPER")
    print("="*80)
    print(f"Subject: {SUBJECT['name']} ({SUBJECT['code']})")
    print(f"Exam Board: {SUBJECT['exam_board']}")
    print(f"Level: {SUBJECT['level']}")
    print("="*80)
    
    # Download PDF
    pdf_path = download_pdf(SUBJECT['spec_url'])
    
    # Extract topics
    print("\n🔍 Extracting topics from PDF...")
    topics = extract_topics_from_pdf(pdf_path)
    
    if not topics:
        print("\n❌ EXTRACTION FAILED!")
        print("⚠️  Could not extract topics from PDF.")
        print("⚠️  Check the debug file and ask user for help.")
        print("⚠️  DO NOT INVENT TOPICS!")
        return False
    
    print(f"\n✅ Extracted {len(topics)} topics")
    
    # Show sample
    print("\n📋 Sample topics:")
    for topic in topics[:10]:
        indent = "  " * topic['level']
        print(f"{indent}[L{topic['level']}] {topic['code']}: {topic['title'][:80]}")
    
    # Upload
    response = input("\n⚠️  Upload to Supabase? (yes/no): ")
    if response.lower() == 'yes':
        upload_to_supabase(topics)
    else:
        print("❌ Upload cancelled")
    
    # Cleanup
    os.remove(pdf_path)
    print("\n🧹 Cleaned up temporary files")

if __name__ == '__main__':
    main()
