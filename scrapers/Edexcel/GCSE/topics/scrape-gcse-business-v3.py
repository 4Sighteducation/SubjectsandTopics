#!/usr/bin/env python3
"""
GCSE Business Topics Scraper - V3 FINAL
Correctly extracts learning outcomes without over-filtering
"""

import os
import re
import requests
import pdfplumber
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

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
    print("[INFO] Downloading PDF...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(url, headers=headers, allow_redirects=True)
    response.raise_for_status()
    with open(output_path, 'wb') as f:
        f.write(response.content)
    return output_path

def extract_topics_from_pdf(pdf_path):
    topics = []
    
    # Level 0: Themes
    topics.append({'code': 'Theme1', 'title': 'Theme 1: Investigating small business', 'parent_code': None, 'level': 0})
    topics.append({'code': 'Theme2', 'title': 'Theme 2: Building a business', 'parent_code': None, 'level': 0})
    
    print("[INFO] Extracting from PDF...")
    
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    
    # Stop at appendices
    if "Appendix 1" in full_text:
        full_text = full_text.split("Appendix 1")[0]
    
    lines = full_text.split('\n')
    
    current_topic_code = None
    current_content_code = None
    in_valid_section = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Match "Topic X.X Something"
        topic_match = re.match(r'^Topic\s+([\d\.]+)\s+(.+)$', line)
        if topic_match:
            topic_num = topic_match.group(1)
            topic_title = topic_match.group(2).strip()
            parent_code = 'Theme1' if topic_num.startswith('1.') else 'Theme2'
            topic_code = f'T{topic_num.replace(".", "_")}'
            
            topics.append({
                'code': topic_code,
                'title': f'{topic_num} {topic_title}',
                'parent_code': parent_code,
                'level': 1
            })
            current_topic_code = topic_code
            in_valid_section = True
            print(f"  [L1] {topic_num} {topic_title}")
            continue
        
        # Match content codes "X.X.X"
        content_match = re.match(r'^([\d]+\.[\d]+\.[\d]+)\s+(.*)$', line)
        if content_match and current_topic_code:
            content_num = content_match.group(1)
            content_title = content_match.group(2).strip()
            
            if not content_title or len(content_title) < 3:
                for j in range(i+1, min(i+3, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith('●') and len(next_line) > 3:
                        content_title = next_line
                        break
            
            content_code = f'C{content_num.replace(".", "_")}'
            topics.append({
                'code': content_code,
                'title': f'{content_num} {content_title}',
                'parent_code': current_topic_code,
                'level': 2
            })
            current_content_code = content_code
            print(f"    [L2] {content_num} {content_title}")
            continue
        
        # Match learning points (text ending with colon)
        if (in_valid_section and current_content_code and 
            line.endswith(':') and not line.startswith('●') and 
            len(line) > 15 and len(line) < 100):
            
            learning_point = line.rstrip(':').strip()
            
            # Filter obvious junk (appendix content, policy text, etc.)
            junk_indicators = [
                'Subject content', 'What students need to learn',
                'details of how', 'please refer', 'DfE website',
                'We are committed', 'Pearson follows', 'JCQ policy',
                'Command word', 'Calculators must', 'calculator.',
                'qualification is', 'qualification will', 'disabilities',
                'Regulated Qualifications', 'World Class', 'Edexcel Level'
            ]
            
            if any(indicator in learning_point for indicator in junk_indicators):
                continue
            
            # Must contain meaningful business-related words
            business_keywords = [
                'business', 'market', 'customer', 'finance', 'cash', 'revenue',
                'profit', 'cost', 'price', 'product', 'promotion', 'stakeholder',
                'technology', 'legislation', 'economic', 'growth', 'operational',
                'employee', 'organisational', 'quality', 'supplier', 'motivation',
                'recruitment', 'globalisation', 'ethical', 'competitive',
                'entrepreneurship', 'franchise', 'ownership'
            ]
            
            learning_lower = learning_point.lower()
            has_business_content = any(keyword in learning_lower for keyword in business_keywords)
            
            if has_business_content:
                level_3_count = sum(1 for t in topics if t.get('parent_code') == current_content_code and t['level'] == 3)
                learning_code = f'{current_content_code}_{level_3_count + 1}'
                
                topics.append({
                    'code': learning_code,
                    'title': learning_point,
                    'parent_code': current_content_code,
                    'level': 3
                })
                print(f"      [L3] {learning_point}")
    
    return topics

def upload_to_supabase(topics):
    if not topics:
        print("[ERROR] No topics extracted!")
        return False
    
    print(f"\n[INFO] Total extracted: {len(topics)} topics")
    
    levels = {}
    for topic in topics:
        level = topic.get('level', 0)
        levels[level] = levels.get(level, 0) + 1
    
    print(f"  Level 0 (Themes): {levels.get(0, 0)}")
    print(f"  Level 1 (Topics): {levels.get(1, 0)}")
    print(f"  Level 2 (Content): {levels.get(2, 0)}")
    print(f"  Level 3 (Learning): {levels.get(3, 0)}")
    
    try:
        print("\n[1/3] Creating subject...")
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT['name']} (GCSE)",
            'subject_code': SUBJECT['code'],
            'qualification_type': 'GCSE',
            'specification_url': SUBJECT['spec_url'],
            'exam_board': 'Edexcel'
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        print("\n[2/3] Clearing old topics...")
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared")
        
        print(f"\n[3/3] Uploading {len(topics)} topics...")
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level']
        } for t in topics]
        
        inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted.data)} topics")
        
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
        
        print(f"[OK] Linked {linked} parent relationships")
        
        print("\n" + "="*80)
        print("[SUCCESS] GCSE BUSINESS - UPLOAD COMPLETE!")
        print("="*80)
        print(f"Total: {len(topics)} topics | Levels: {levels.get(0,0)} + {levels.get(1,0)} + {levels.get(2,0)} + {levels.get(3,0)}")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*80)
    print("GCSE BUSINESS SCRAPER - V3 FINAL")
    print("="*80)
    
    pdf_path = download_pdf(SUBJECT['spec_url'])
    topics = extract_topics_from_pdf(pdf_path)
    upload_to_supabase(topics)
    
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

if __name__ == '__main__':
    main()

