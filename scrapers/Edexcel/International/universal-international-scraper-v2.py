"""
Universal International Qualification Topic Scraper V2
=====================================================

IMPROVED version that better handles International GCSE/A Level structure:
- Recognizes that Papers are assessments, not topic containers
- Properly parses numbered topics (1, 2, 3...)
- Handles lettered sub-topics ((a), (b), (c))
- Better hierarchy detection

Usage:
    python universal-international-scraper-v2.py --subject IG-Biology
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

# PDF extraction
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)


class InternationalTopicScraperV2:
    """Improved scraper for International GCSE and A Level specifications."""
    
    def __init__(self, subject_info: Dict):
        self.subject = subject_info
        self.topics = []
        
    def download_pdf(self) -> Optional[bytes]:
        """Download PDF from URL."""
        print(f"\n[INFO] Downloading PDF from {self.subject['pdf_url']}...")
        
        try:
            response = requests.get(self.subject['pdf_url'], timeout=30)
            response.raise_for_status()
            print(f"[OK] Downloaded {len(response.content)} bytes")
            return response.content
        except Exception as e:
            print(f"[ERROR] Failed to download PDF: {str(e)}")
            return None
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Extract text from PDF using pdfplumber."""
        if not pdfplumber:
            print("[ERROR] pdfplumber not installed. Run: pip install pdfplumber")
            return ""
            
        text = ""
        try:
            print("[INFO] Extracting text with pdfplumber...")
            pdf_file = BytesIO(pdf_content)
            with pdfplumber.open(pdf_file) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    if i % 10 == 0:
                        print(f"[INFO] Processed {i+1}/{len(pdf.pages)} pages...")
            print(f"[OK] Extracted {len(text)} characters")
            return text
        except Exception as e:
            print(f"[ERROR] PDF extraction failed: {str(e)}")
            return ""
    
    def parse_topics(self, text: str) -> List[Dict]:
        """Parse hierarchical topics with improved logic."""
        print("\n[INFO] Parsing topics...")
        
        topics = []
        lines = text.split('\n')
        seen_codes = set()
        
        # Patterns
        patterns = {
            # Main numbered topics: "1 Topic name" or "1. Topic name"
            'main_topic': re.compile(r'^(\d+)\s+(.+)'),
            # Lettered sub-topics: "(a) Sub-topic" or "a) Sub-topic"  
            'sub_topic': re.compile(r'^\(?([a-z])\)?\s+(.+)', re.IGNORECASE),
            # Numbered points: "1.1" or "2.3.4"
            'numbered': re.compile(r'^(\d+(?:\.\d+)+)\s+(.+)'),
            # Bullet points
            'bullet': re.compile(r'^[•●○■▪▫-]\s*(.+)'),
        }
        
        current_main_topic = None
        current_sub_topic = None
        bullet_counter = {}
        
        # Skip to content section
        content_started = False
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Skip header/footer
            if 'Pearson Edexcel' in line or 'Specification' in line or line.startswith('©'):
                continue
                
            # Detect content start
            if not content_started:
                if re.match(r'^\d+\s+(The|Topic|Paper)', line, re.IGNORECASE):
                    content_started = True
                else:
                    continue
            
            # Skip assessment description lines
            if line.startswith('Paper 1') or line.startswith('Paper 2') or 'Paper code' in line:
                continue
            if 'Content summary' in line or 'Assessment' in line:
                continue
            if line.startswith('Externally assessed') or 'written examination' in line:
                continue
            
            # Check for main numbered topic (Level 0)
            match = patterns['main_topic'].match(line)
            if match and len(match.group(1)) <= 2:  # Only single or double digit
                topic_num = match.group(1)
                topic_title = match.group(2).strip()
                
                # Skip if it's just a page reference
                if topic_title.isdigit():
                    continue
                    
                # Filter out common non-topic lines
                if any(skip in topic_title.lower() for skip in ['biology content', 'assessment', 'qualification']):
                    continue
                
                code = f"T{topic_num}"
                
                if code not in seen_codes and len(topic_title) > 10:  # Must be substantial
                    current_main_topic = code
                    current_sub_topic = None
                    
                    topics.append({
                        'code': code,
                        'title': topic_title,
                        'level': 0,
                        'parent': None
                    })
                    seen_codes.add(code)
                    bullet_counter[code] = 0
                continue
            
            # Check for lettered sub-topic (Level 1)
            match = patterns['sub_topic'].match(line)
            if match and current_main_topic:
                letter = match.group(1).lower()
                sub_title = match.group(2).strip()
                
                # Must be substantial and not "Students should:"
                if len(sub_title) > 5 and 'students should' not in sub_title.lower():
                    code = f"{current_main_topic}.{letter}"
                    
                    if code not in seen_codes:
                        current_sub_topic = code
                        
                        topics.append({
                            'code': code,
                            'title': sub_title,
                            'level': 1,
                            'parent': current_main_topic
                        })
                        seen_codes.add(code)
                        bullet_counter[code] = 0
                continue
            
            # Check for numbered sub-points (Level 2)
            match = patterns['numbered'].match(line)
            if match and (current_sub_topic or current_main_topic):
                number = match.group(1)
                content = match.group(2).strip()
                
                if len(content) > 10:  # Substantial content
                    parent = current_sub_topic or current_main_topic
                    code = f"{parent}.{number}"
                    
                    if code not in seen_codes:
                        topics.append({
                            'code': code,
                            'title': content,
                            'level': 2,
                            'parent': parent
                        })
                        seen_codes.add(code)
                continue
            
            # Check for bullet points or learning objectives (Level 2/3)
            match = patterns['bullet'].match(line)
            if match and (current_sub_topic or current_main_topic):
                content = match.group(1).strip()
                
                if len(content) > 15:  # Must be substantial
                    parent = current_sub_topic or current_main_topic
                    bullet_counter[parent] = bullet_counter.get(parent, 0) + 1
                    code = f"{parent}.{bullet_counter[parent]}"
                    
                    level = 2 if current_sub_topic else 1
                    
                    if code not in seen_codes:
                        topics.append({
                            'code': code,
                            'title': content,
                            'level': level,
                            'parent': parent
                        })
                        seen_codes.add(code)
        
        print(f"[OK] Parsed {len(topics)} topics")
        return topics
    
    def upload_to_supabase(self, topics: List[Dict]) -> bool:
        """Upload topics to Supabase staging tables."""
        print("\n[INFO] Uploading to Supabase...")
        
        try:
            # Create/update subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': f"{self.subject['name']} ({self.subject['qualification']})",
                'subject_code': self.subject['code'],
                'qualification_type': self.subject['qualification'],
                'specification_url': self.subject['pdf_url'],
                'exam_board': self.subject['exam_board']
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            if not subject_result.data:
                print("[ERROR] Failed to create/update subject")
                return False
            
            subject_id = subject_result.data[0]['id']
            print(f"[OK] Subject ID: {subject_id}")
            
            # Clear old topics
            supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
            print("[OK] Cleared old topics")
            
            # Insert topics in batches
            BATCH_SIZE = 500
            all_inserted = []
            
            for i in range(0, len(topics), BATCH_SIZE):
                batch = topics[i:i+BATCH_SIZE]
                to_insert = [{
                    'subject_id': subject_id,
                    'topic_code': t['code'],
                    'topic_name': t['title'],
                    'topic_level': t['level'],
                    'exam_board': self.subject['exam_board']
                } for t in batch]
                
                inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
                all_inserted.extend(inserted.data)
                print(f"[OK] Uploaded batch {i//BATCH_SIZE + 1}: {len(inserted.data)} topics")
            
            print(f"[OK] Total uploaded: {len(all_inserted)} topics")
            
            # Link parent relationships
            code_to_id = {t['topic_code']: t['id'] for t in all_inserted}
            
            for topic in topics:
                if topic['parent'] and topic['code'] in code_to_id and topic['parent'] in code_to_id:
                    try:
                        supabase.table('staging_aqa_topics').update({
                            'parent_topic_id': code_to_id[topic['parent']]
                        }).eq('id', code_to_id[topic['code']]).execute()
                    except Exception as e:
                        print(f"[WARNING] Failed to link {topic['code']}: {str(e)}")
            
            print(f"[OK] Linked parent relationships")
            return True
            
        except Exception as e:
            print(f"[ERROR] Upload failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def scrape(self) -> bool:
        """Main scraping workflow."""
        print("\n" + "=" * 60)
        print(f"SCRAPING V2: {self.subject['name']} ({self.subject['qualification']})")
        print("=" * 60)
        
        # Download PDF
        pdf_content = self.download_pdf()
        if not pdf_content:
            return False
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_content)
        if not text:
            return False
        
        # Parse topics
        self.topics = self.parse_topics(text)
        if not self.topics:
            print("[WARNING] No topics found")
            return False
        
        # Upload to Supabase
        success = self.upload_to_supabase(self.topics)
        
        if success:
            print("\n[SUCCESS] Scraping complete!")
        else:
            print("\n[FAILED] Scraping failed")
        
        return success


def load_subjects(json_file: Path) -> List[Dict]:
    """Load subjects from JSON file."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load {json_file}: {str(e)}")
        return []


def main():
    parser = argparse.ArgumentParser(description='Scrape International qualification topics (V2 - Improved)')
    parser.add_argument('--subject', help='Subject code (e.g., IG-Biology)')
    
    args = parser.parse_args()
    
    if not args.subject:
        parser.print_help()
        sys.exit(1)
    
    script_dir = Path(__file__).parent
    
    # Load the appropriate file based on code prefix
    if args.subject.startswith('IG-'):
        subjects_file = script_dir / "International-GCSE" / "international-gcse-subjects.json"
    elif args.subject.startswith('IAL-'):
        subjects_file = script_dir / "International-A-Level" / "international-a-level-subjects.json"
    else:
        print(f"[ERROR] Unknown subject code format: {args.subject}")
        sys.exit(1)
    
    subjects = load_subjects(subjects_file)
    subject = next((s for s in subjects if s['code'] == args.subject), None)
    
    if not subject:
        print(f"[ERROR] Subject not found: {args.subject}")
        sys.exit(1)
    
    # Scrape
    scraper = InternationalTopicScraperV2(subject)
    success = scraper.scrape()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

