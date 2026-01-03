"""
AI-Powered Scraper - WORKING VERSION (Tamil Success)
====================================================

This is the EXACT version that successfully scraped Tamil with vocabulary.
DO NOT MODIFY THE PROMPT - it works!

Usage:
    python ai-powered-scraper-openai-WORKING.py --subject IG-French
"""

import os
import sys
import re
import json
import argparse
import requests
from pathlib import Path
from io import BytesIO
from typing import List, Dict, Optional
from dotenv import load_dotenv
from supabase import create_client

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')
openai_key = os.getenv('OPENAI_API_KEY')

if not all([supabase_url, supabase_key, openai_key]):
    print("[ERROR] Missing credentials!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

try:
    from openai import OpenAI
    import pdfplumber
except ImportError:
    print("[ERROR] Run: pip install openai pdfplumber")
    sys.exit(1)

client = OpenAI(api_key=openai_key)


WORKING_PROMPT = """Extract ALL curriculum content as a numbered hierarchy.

Read the specification PDF and create a complete topic list following this EXACT format:

1. Paper 1: Listening  
   1.1 Home and abroad
       1.1.1 Life in town and rural life
           1.1.1.1 Vocabulary: la ville (town), le village (village), habiter (to live)
       1.1.2 Holidays and travel
           1.1.2.1 Vocabulary: les vacances (holidays), la plage (beach), voyager (to travel)
   1.2 Education and employment
       1.2.1 School life
           1.2.1.1 Vocabulary: l'école (school), le professeur (teacher), étudier (to study)

Notice: Vocabulary is integrated UNDER each sub-topic, not in separate sections.

FOR ENGLISH LITERATURE/LANGUAGE SUBJECTS:
- Extract ALL paper/unit structures with topics and themes
- CRITICALLY: Find "Required texts", "Set texts", "Prescribed texts" sections
- List each text with full details: "Text: Title by Author (genre/period)"
- Include text options if multiple choices are given
- Example: "1.1.1 Text: Othello by William Shakespeare (Drama, 1604)"
- Example: "1.2.1 Required Texts (Choose 1 from list below)"
           "1.2.1.1 Text: Pride and Prejudice by Jane Austen (Novel, 1813)"
           "1.2.1.2 Text: Frankenstein by Mary Shelley (Novel, 1818)"

FOR LANGUAGE SUBJECTS (French, Spanish, German, Tamil, Arabic, Chinese):
- Find vocabulary appendix (usually last 20-30 pages)
- Distribute vocab words to their matching themes
- Add as children: "1.1.1.1 Vocabulary: word (trans), word2 (trans2)..."
- Preserve native scripts (Tamil characters, Arabic script, Chinese characters)

FOR SCIENCES/OTHER SUBJECTS:
- Extract full text of specifications (e.g., "1.1 use the following SI units: kg, m, s...")
- Include practical investigations
- Extract from tables under "Students should:"

Extract only externally assessed content. Output numbered hierarchy ONLY."""


class WorkingScraper:
    """The scraper version that worked for Tamil."""
    
    def __init__(self, subject_info: Dict):
        self.subject = subject_info
        
    def download_pdf(self) -> Optional[bytes]:
        print(f"\n[INFO] Downloading PDF...")
        try:
            response = requests.get(self.subject['pdf_url'], timeout=60)
            response.raise_for_status()
            print(f"[OK] Downloaded {len(response.content)/1024/1024:.1f} MB")
            return response.content
        except Exception as e:
            print(f"[ERROR] Download failed: {str(e)}")
            return None
    
    def extract_text(self, pdf_content: bytes) -> Optional[str]:
        print("\n[INFO] Extracting text...")
        try:
            pdf_file = BytesIO(pdf_content)
            text = ""
            with pdfplumber.open(pdf_file) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    if i % 10 == 0:
                        print(f"[INFO] Page {i+1}/{len(pdf.pages)}...", end='\r')
            print(f"\n[OK] Extracted {len(text)} chars")
            return text
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return None
    
    def extract_with_ai(self, pdf_text: str) -> Optional[str]:
        print("\n[INFO] Sending to GPT-4...")
        
        max_chars = 200000
        if len(pdf_text) > max_chars:
            pdf_text = pdf_text[:max_chars]
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"{WORKING_PROMPT}\n\nPDF:\n\n{pdf_text}"}],
                max_tokens=16384,
                temperature=0,
                timeout=180
            )
            
            hierarchy = response.choices[0].message.content
            print(f"[OK] Extracted {len(hierarchy)} chars ({response.usage.completion_tokens} tokens)")
            
            # Save
            out_file = Path(__file__).parent / "adobe-ai-output" / f"{self.subject['code']}-WORKING.txt"
            out_file.write_text(hierarchy, encoding='utf-8')
            return hierarchy
            
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return None
    
    def parse_hierarchy(self, text: str) -> List[Dict]:
        topics = []
        parent_stack = {}
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            match = re.match(r'^([\d.]+)\s+(.+)$', line)
            if not match:
                continue
            
            number = match.group(1).rstrip('.')
            title = match.group(2).strip()
            level = number.count('.')
            code = number.replace('.', '_')
            parent_code = parent_stack.get(level - 1) if level > 0 else None
            
            topics.append({'code': code, 'title': title, 'level': level, 'parent': parent_code})
            parent_stack[level] = code
            
            for l in list(parent_stack.keys()):
                if l > level:
                    del parent_stack[l]
        
        return topics
    
    def upload(self, topics: List[Dict]) -> bool:
        try:
            result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': f"{self.subject['name']} ({self.subject['qualification']})",
                'subject_code': self.subject['code'],
                'qualification_type': self.subject['qualification'],
                'specification_url': self.subject['pdf_url'],
                'exam_board': self.subject['exam_board']
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            subject_id = result.data[0]['id']
            supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
            
            unique = {}
            for t in topics:
                if t['code'] not in unique:
                    unique[t['code']] = t
            topics = list(unique.values())
            
            to_insert = [{
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': t['title'],
                'topic_level': t['level'],
                'exam_board': self.subject['exam_board']
            } for t in topics]
            
            inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
            
            code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
            for topic in topics:
                if topic['parent'] and topic['code'] in code_to_id and topic['parent'] in code_to_id:
                    try:
                        supabase.table('staging_aqa_topics').update({
                            'parent_topic_id': code_to_id[topic['parent']]
                        }).eq('id', code_to_id[topic['code']]).execute()
                    except:
                        pass
            
            print(f"[OK] Uploaded {len(topics)} topics")
            return True
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return False
    
    def scrape(self) -> bool:
        print(f"\n{'='*60}")
        print(f"SCRAPING: {self.subject['name']}")
        print('='*60)
        
        pdf = self.download_pdf()
        if not pdf:
            return False
        
        text = self.extract_text(pdf)
        if not text:
            return False
        
        hierarchy = self.extract_with_ai(text)
        if not hierarchy:
            return False
        
        topics = self.parse_hierarchy(hierarchy)
        if not topics:
            return False
        
        print(f"\n[INFO] Parsed {len(topics)} topics")
        by_level = {}
        for t in topics:
            by_level[t['level']] = by_level.get(t['level'], 0) + 1
        for level in sorted(by_level.keys()):
            print(f"  Level {level}: {by_level[level]}")
        
        success = self.upload(topics)
        print(f"\n{'[SUCCESS]' if success else '[FAILED]'}")
        return success


def load_subjects(file: Path):
    with open(file, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subject', required=True)
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    
    if args.subject.startswith('IG-'):
        file = script_dir / "International-GCSE" / "international-gcse-subjects.json"
    else:
        file = script_dir / "International-A-Level" / "international-a-level-subjects.json"
    
    subjects = load_subjects(file)
    subject = next((s for s in subjects if s['code'] == args.subject), None)
    
    if not subject:
        print(f"[ERROR] Subject not found: {args.subject}")
        sys.exit(1)
    
    scraper = WorkingScraper(subject)
    sys.exit(0 if scraper.scrape() else 1)


if __name__ == '__main__':
    main()

