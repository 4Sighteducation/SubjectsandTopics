"""
Universal International Qualification Topic Scraper
===================================================

Extracts topic hierarchies from International GCSE and International A Level PDFs.

Usage:
    python universal-international-scraper.py --subject IG-Biology
    python universal-international-scraper.py --all-igcse
    python universal-international-scraper.py --all-ial
    python universal-international-scraper.py --all

Features:
    - Extracts hierarchical topic structure
    - Auto-detects Papers, Topics, Sub-topics
    - Generates standardized topic codes
    - Uploads to Supabase staging tables
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
    import PyPDF2
except ImportError:
    print("[WARNING] PyPDF2 not installed. Run: pip install PyPDF2")
    PyPDF2 = None

try:
    import pdfplumber
except ImportError:
    print("[WARNING] pdfplumber not installed. Run: pip install pdfplumber")
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


class InternationalTopicScraper:
    """Universal scraper for International GCSE and A Level specifications."""
    
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
        """Extract text from PDF using available libraries."""
        text = ""
        
        # Try pdfplumber first (better for tables)
        if pdfplumber:
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
                print(f"[WARNING] pdfplumber failed: {str(e)}")
        
        # Fallback to PyPDF2
        if PyPDF2:
            try:
                print("[INFO] Extracting text with PyPDF2...")
                pdf_file = BytesIO(pdf_content)
                reader = PyPDF2.PdfReader(pdf_file)
                for i, page in enumerate(reader.pages):
                    text += page.extract_text() + "\n"
                    if i % 10 == 0:
                        print(f"[INFO] Processed {i+1}/{len(reader.pages)} pages...")
                print(f"[OK] Extracted {len(text)} characters")
                return text
            except Exception as e:
                print(f"[ERROR] PyPDF2 failed: {str(e)}")
        
        print("[ERROR] No PDF extraction library available")
        return ""
    
    def parse_topics(self, text: str) -> List[Dict]:
        """Parse hierarchical topics from PDF text."""
        print("\n[INFO] Parsing topics...")
        
        topics = []
        lines = text.split('\n')
        seen_codes = set()  # Track seen codes to avoid duplicates
        
        # Patterns to detect different levels
        patterns = {
            'paper': re.compile(r'^(Paper|Component|Unit)\s+(\d+)[:\s]*(.+)', re.IGNORECASE),
            'topic': re.compile(r'^Topic\s+(\d+)[:\s–-]*(.+)', re.IGNORECASE),
            'numbered': re.compile(r'^(\d+(?:\.\d+)*)\s+(.+)'),
            'bullet': re.compile(r'^[•●○■▪▫]\s*(.+)'),
        }
        
        current_paper = None
        current_topic = None
        topic_counter = {}
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Check for Paper/Component (Level 0)
            match = patterns['paper'].match(line)
            if match:
                paper_num = match.group(2)
                paper_title = match.group(3).strip()
                current_paper = f"P{paper_num}"
                
                if current_paper not in seen_codes:
                    topics.append({
                        'code': current_paper,
                        'title': f"Paper {paper_num}: {paper_title}",
                        'level': 0,
                        'parent': None
                    })
                    seen_codes.add(current_paper)
                current_topic = None
                topic_counter[current_paper] = 0
                continue
            
            # Check for Topic (Level 1)
            match = patterns['topic'].match(line)
            if match:
                topic_num = match.group(1)
                topic_title = match.group(2).strip()
                
                if current_paper:
                    current_topic = f"{current_paper}.T{topic_num}"
                else:
                    current_topic = f"T{topic_num}"
                
                if current_topic not in seen_codes:
                    topics.append({
                        'code': current_topic,
                        'title': topic_title,
                        'level': 1,
                        'parent': current_paper
                    })
                    seen_codes.add(current_topic)
                topic_counter[current_topic] = 0
                continue
            
            # Check for numbered items (Level 2+)
            match = patterns['numbered'].match(line)
            if match:
                number = match.group(1)
                content = match.group(2).strip()
                
                # Determine level by counting dots
                level = len(number.split('.'))
                
                # Generate code with safe prefix
                if current_topic:
                    code = f"{current_topic}.{number}"
                    parent = current_topic if level == 1 else self._find_parent(topics, code)
                elif current_paper:
                    code = f"{current_paper}.{number}"
                    parent = current_paper
                else:
                    # Standalone numbered items - prefix with 'S' for safety
                    code = f"S{number}"
                    parent = None
                
                if code not in seen_codes:
                    topics.append({
                        'code': code,
                        'title': content,
                        'level': min(level + 1, 3),  # Cap at level 3
                        'parent': parent
                    })
                    seen_codes.add(code)
                continue
            
            # Check for bullet points (Level 3)
            match = patterns['bullet'].match(line)
            if match:
                content = match.group(1).strip()
                
                if current_topic:
                    topic_counter[current_topic] = topic_counter.get(current_topic, 0) + 1
                    code = f"{current_topic}.{topic_counter[current_topic]}"
                    parent = current_topic
                elif current_paper:
                    topic_counter[current_paper] = topic_counter.get(current_paper, 0) + 1
                    code = f"{current_paper}.{topic_counter[current_paper]}"
                    parent = current_paper
                else:
                    continue
                
                if code not in seen_codes:
                    topics.append({
                        'code': code,
                        'title': content,
                        'level': 3,
                        'parent': parent
                    })
                    seen_codes.add(code)
        
        print(f"[OK] Parsed {len(topics)} topics")
        return topics
    
    def _find_parent(self, topics: List[Dict], code: str) -> Optional[str]:
        """Find parent topic code based on numbering."""
        parts = code.split('.')
        if len(parts) <= 2:
            return parts[0] if len(parts) > 1 else None
        
        # Find most specific parent
        for i in range(len(parts) - 1, 1, -1):
            parent_code = '.'.join(parts[:i])
            for topic in reversed(topics):
                if topic['code'] == parent_code:
                    return parent_code
        
        return parts[0]
    
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
            
            for level_num in [1, 2, 3]:
                level_topics = [t for t in topics if t['level'] == level_num and t['parent']]
                
                for topic in level_topics:
                    if topic['code'] in code_to_id and topic['parent'] in code_to_id:
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
        print(f"SCRAPING: {self.subject['name']} ({self.subject['qualification']})")
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
    parser = argparse.ArgumentParser(description='Scrape International qualification topics')
    parser.add_argument('--subject', help='Subject code (e.g., IG-Biology)')
    parser.add_argument('--all-igcse', action='store_true', help='Scrape all International GCSE subjects')
    parser.add_argument('--all-ial', action='store_true', help='Scrape all International A Level subjects')
    parser.add_argument('--all', action='store_true', help='Scrape all International subjects')
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    
    # Determine which subjects to scrape
    subjects_to_scrape = []
    
    if args.subject:
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
        
        subjects_to_scrape = [subject]
    
    elif args.all_igcse:
        subjects_file = script_dir / "International-GCSE" / "international-gcse-subjects.json"
        subjects_to_scrape = load_subjects(subjects_file)
    
    elif args.all_ial:
        subjects_file = script_dir / "International-A-Level" / "international-a-level-subjects.json"
        subjects_to_scrape = load_subjects(subjects_file)
    
    elif args.all:
        ig_file = script_dir / "International-GCSE" / "international-gcse-subjects.json"
        ial_file = script_dir / "International-A-Level" / "international-a-level-subjects.json"
        subjects_to_scrape = load_subjects(ig_file) + load_subjects(ial_file)
    
    else:
        parser.print_help()
        sys.exit(1)
    
    # Scrape each subject
    print(f"\n[INFO] Will scrape {len(subjects_to_scrape)} subject(s)")
    
    results = {'success': 0, 'failed': 0, 'total': len(subjects_to_scrape)}
    
    for subject in subjects_to_scrape:
        scraper = InternationalTopicScraper(subject)
        success = scraper.scrape()
        
        if success:
            results['success'] += 1
        else:
            results['failed'] += 1
        
        print("\n" + "-" * 60)
    
    # Summary
    print("\n" + "=" * 60)
    print("SCRAPING COMPLETE")
    print("=" * 60)
    print(f"Total: {results['total']}")
    print(f"Success: {results['success']}")
    print(f"Failed: {results['failed']}")
    print("=" * 60)


if __name__ == '__main__':
    main()

