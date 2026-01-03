#!/usr/bin/env python3
"""
GCSE Business Topics Scraper - FIXED VERSION
Parses the text-based PDF format (not tables)

CRITICAL: Extracts ONLY what's in the PDF. NO INVENTION.
"""

import os
import sys
import re
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

SUBJECT = {
    'code': 'GCSE-Business',
    'name': 'Business',
    'level': 'GCSE',
    'exam_board': 'Edexcel',
    'spec_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Business/2017/specification-and-sample-assessments/gcse-business-spec-2017.pdf'
}

def download_pdf(url, output_path='temp_spec.pdf'):
    """Download PDF specification"""
    print(f"[INFO] Downloading PDF...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers, allow_redirects=True)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        f.write(response.content)
    
    return output_path

def extract_topics_from_pdf(pdf_path):
    """Extract topics from text-based PDF format"""
    
    topics = []
    
    # Level 0: Themes (hardcoded from spec)
    topics.append({
        'code': 'Theme1',
        'title': 'Theme 1: Investigating small business',
        'parent_code': None,
        'level': 0
    })
    topics.append({
        'code': 'Theme2',
        'title': 'Theme 2: Building a business',
        'parent_code': None,
        'level': 0
    })
    
    print(f" Extracting from PDF...")
    
    with pdfplumber.open(pdf_path) as pdf:
        # Extract all text
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        
        # Save debug
        debug_file = f'debug_gcse_business_fixed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(full_text)
        print(f" Debug: {debug_file}")
    
    # Stop at appendices to avoid junk (actual appendix, not TOC mention)
    if "Appendix 1: Command word" in full_text:
        full_text = full_text.split("Appendix 1: Command word")[0]
    
    # Parse topics from text
    lines = full_text.split('\n')
    
    current_topic_code = None
    current_content_code = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Match "Topic X.X Something" (Level 1)
        topic_match = re.match(r'^Topic\s+([\d\.]+)\s+(.+)$', line)
        if topic_match:
            topic_num = topic_match.group(1)  # e.g. "1.1"
            topic_title = topic_match.group(2).strip()
            
            # Determine parent theme
            parent_code = 'Theme1' if topic_num.startswith('1.') else 'Theme2'
            topic_code = f'T{topic_num.replace(".", "_")}'  # e.g. "T1_1"
            
            topics.append({
                'code': topic_code,
                'title': f'{topic_num} {topic_title}',
                'parent_code': parent_code,
                'level': 1
            })
            current_topic_code = topic_code
            print(f"   Topic: {topic_num} {topic_title}")
            continue
        
        # Match content codes "X.X.X" at start of line (Level 2)
        # Format: "1.1.1" then title like "The dynamic nature of business"
        content_match = re.match(r'^([\d]+\.[\d]+\.[\d]+)\s+(.*)$', line)
        if content_match and current_topic_code:
            content_num = content_match.group(1)  # e.g. "1.1.1"
            content_title = content_match.group(2).strip()
            
            # IMPORTANT: If the rest of line ends with colon, it's a learning outcome (Level 3)
            # NOT a content code title. Skip this and handle as Level 3 below.
            if content_title.endswith(':'):
                # This is actually "1.1.1 Why new business ideas come about:" 
                # We need to find the REAL 1.1.1 title first
                # Look backwards or use generic title
                if not current_content_code or not current_content_code.endswith(content_num.replace(".", "_")):
                    # Create the Level 2 entry with generic title from next line
                    for j in range(i+1, min(i+5, len(lines))):
                        next_line = lines[j].strip()
                        # Look for title line (not bullet, not colon-ending)
                        if (next_line and len(next_line) > 3 and 
                            not next_line.startswith('') and 
                            not next_line.endswith(':') and
                            not re.match(r'^[\d]+\.[\d]+\.[\d]+', next_line)):
                            content_title = next_line
                            break
                    
                    if not content_title or content_title.endswith(':'):
                        content_title = f"Content {content_num}"
                    
                    content_code = f'C{content_num.replace(".", "_")}'
                    topics.append({
                        'code': content_code,
                        'title': f'{content_num} {content_title}',
                        'parent_code': current_topic_code,
                        'level': 2
                    })
                    current_content_code = content_code
                    print(f"     {content_num} {content_title}")
                
                # Now handle the learning outcome that was on the same line
                learning_outcome = content_title.rstrip(':').strip() if content_title.endswith(':') else line.split(content_num)[1].rstrip(':').strip()
                if learning_outcome and len(learning_outcome) > 5:
                    level_3_count = sum(1 for t in topics if t.get('parent_code') == current_content_code and t['level'] == 3)
                    learning_code = f'{current_content_code}_{level_3_count + 1}'
                    topics.append({
                        'code': learning_code,
                        'title': learning_outcome,
                        'parent_code': current_content_code,
                        'level': 3
                    })
                    print(f"       {learning_outcome}")
                continue
            
            # Normal case: "1.1.1 The dynamic nature of business"
            content_code = f'C{content_num.replace(".", "_")}'
            topics.append({
                'code': content_code,
                'title': f'{content_num} {content_title}',
                'parent_code': current_topic_code,
                'level': 2
            })
            current_content_code = content_code
            print(f"     {content_num} {content_title}")
            continue
        
        # Match learning points ending with colon (Level 3)
        if current_content_code and line.endswith(':') and not line.startswith(''):
            # Remove any leading numbering or bullets
            learning_point = line.rstrip(':').strip()
            
            # Filter out junk from appendices and general text
            skip_terms = ['Subject content', 'What students need to learn', 'The role of', 'The concept', 
                         'The purpose', 'The importance', 'The impact', 'How businesses', 'Methods of',
                         'The use of', 'details of how', 'We are committed', 'Pearson follows',
                         'Command word', 'Calculations in', 'Calculators must', 'We have developed',
                         '[1]', 'qualification is', 'educational needs', 'business decisions, including']
            
            # Additional filters for junk
            junk_keywords = ['policy', 'DfE website', 'disabilities', 'JCQ', 'Qualifications Regulated',
                            'calculator.', 'process that', 'qualification will']
            
            # Only add if it's a specific learning outcome
            if (len(learning_point) > 10 and 
                not any(learning_point.startswith(term) for term in skip_terms) and
                not any(keyword in learning_point for keyword in junk_keywords) and
                current_content_code.startswith('C')):  # Must be under a valid content code
                
                # Create code
                # Count existing level 3 under this parent
                level_3_count = sum(1 for t in topics if t.get('parent_code') == current_content_code and t['level'] == 3)
                learning_code = f'{current_content_code}_{level_3_count + 1}'
                
                topics.append({
                    'code': learning_code,
                    'title': learning_point,
                    'parent_code': current_content_code,
                    'level': 3
                })
                print(f"       {learning_point}")
    
    return topics

def upload_to_supabase(topics):
    """Upload topics to Supabase"""
    
    if not topics:
        print(" FAILED - No topics extracted!")
        return False
    
    print(f"\n Total extracted: {len(topics)} topics")
    
    # Show breakdown
    levels = {}
    for topic in topics:
        level = topic.get('level', 0)
        levels[level] = levels.get(level, 0) + 1
    
    print("\n Breakdown:")
    print(f"  Level 0 (Themes): {levels.get(0, 0)}")
    print(f"  Level 1 (Topics): {levels.get(1, 0)}")
    print(f"  Level 2 (Content): {levels.get(2, 0)}")
    print(f"  Level 3 (Learning): {levels.get(3, 0)}")
    
    try:
        # Get/create subject
        print("\n[1/3] Creating subject...")
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT['name']} (GCSE)",
            'subject_code': SUBJECT['code'],
            'qualification_type': 'GCSE',
            'specification_url': SUBJECT['spec_url'],
            'exam_board': 'Edexcel'
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f" Subject ID: {subject_id}")
        
        # Clear old
        print("\n[2/3] Clearing old topics...")
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print(" Cleared")
        
        # Insert topics (without parent links first)
        print(f"\n[3/3] Uploading {len(topics)} topics...")
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level']
        } for t in topics]
        
        inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f" Uploaded {len(inserted.data)} topics")
        
        # Link parent relationships
        code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
        linked = 0
        for topic in topics:
            if topic['parent_code']:
                parent_id = code_to_id.get(topic['parent_code'])
                child_id = code_to_id.get(topic['code'])
                if parent_id and child_id:
                    supabase.table('staging_aqa_topics').update({
                        'parent_topic_id': parent_id
                    }).eq('id', child_id).execute()
                    linked += 1
        
        print(f" Linked {linked} parent relationships")
        
        print("\n" + "="*80)
        print(" GCSE BUSINESS - UPLOAD COMPLETE!")
        print("="*80)
        print(f"Total: {len(topics)} topics across 4 levels")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main execution"""
    print("="*80)
    print("GCSE BUSINESS SCRAPER - FIXED VERSION")
    print("="*80)
    
    # Download
    pdf_path = download_pdf(SUBJECT['spec_url'])
    
    # Extract
    topics = extract_topics_from_pdf(pdf_path)
    
    # Upload automatically
    upload_to_supabase(topics)
    
    # Cleanup
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

if __name__ == '__main__':
    main()

