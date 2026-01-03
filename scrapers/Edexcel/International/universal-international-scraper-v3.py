"""
Universal International Qualification Topic Scraper V3
=====================================================

TWO-PHASE APPROACH:
Phase 1: Extract qualification structure from "Qualification at a glance"
Phase 2: Parse detailed topic content and assign to correct papers

This properly handles:
- Papers as Level 0 containers
- Topics 1-5 as Level 1 under each paper
- Sub-topics as Level 2+

Usage:
    python universal-international-scraper-v3.py --subject IG-Biology
"""

import os
import sys
import re
import json
import argparse
import requests
from pathlib import Path
from io import BytesIO
from typing import List, Dict, Optional, Tuple
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


class InternationalTopicScraperV3:
    """Two-phase scraper for International GCSE and A Level."""
    
    def __init__(self, subject_info: Dict):
        self.subject = subject_info
        self.papers = []  # Extracted paper structure
        self.topics = []  # Final topic list
        
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
    
    def extract_paper_structure(self, text: str) -> List[Dict]:
        """Phase 1: Extract paper structure from qualification overview."""
        print("\n[PHASE 1] Extracting paper structure...")
        
        papers = []
        lines = text.split('\n')
        
        current_paper = None
        capturing_topics = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Detect paper definition
            paper_match = re.match(r'^(Biology|Mathematics|Physics|Chemistry|History|Geography|Business|Economics|[\w\s]+)\s+(Paper|Component|Unit)\s+(\d+)', line, re.IGNORECASE)
            if paper_match:
                subject_name = paper_match.group(1).strip()
                paper_num = paper_match.group(3)
                
                # Only capture if it's the right subject or generic
                if current_paper:
                    papers.append(current_paper)
                
                current_paper = {
                    'number': int(paper_num),
                    'title': f"Paper {paper_num}",
                    'topics': [],
                    'description': ''
                }
                capturing_topics = False
                continue
            
            # Look for "Content summary" to start capturing topics
            if current_paper and ('Content summary' in line or 'Questions may come from' in line):
                capturing_topics = True
                continue
            
            # Capture numbered topics under current paper
            if current_paper and capturing_topics:
                # Stop at "Assessment" section
                if line.startswith('Assessment') or line.startswith('□ The paper'):
                    capturing_topics = False
                    continue
                
                # Match topic numbers: "1 Topic name" or "1. Topic name"
                topic_match = re.match(r'^(\d+)\s+(.+)$', line)
                if topic_match and len(topic_match.group(1)) <= 2:
                    topic_num = topic_match.group(1)
                    topic_title = topic_match.group(2).strip()
                    
                    # Filter out page numbers and short titles
                    if len(topic_title) > 15 and not topic_title.isdigit():
                        current_paper['topics'].append({
                            'number': int(topic_num),
                            'title': topic_title
                        })
        
        # Add last paper
        if current_paper:
            papers.append(current_paper)
        
        # Deduplicate papers by number (keep first occurrence)
        seen = set()
        unique_papers = []
        for paper in papers:
            if paper['number'] not in seen and len(paper['topics']) > 0:
                seen.add(paper['number'])
                unique_papers.append(paper)
        
        print(f"[OK] Found {len(unique_papers)} papers:")
        for paper in unique_papers:
            print(f"  - Paper {paper['number']}: {len(paper['topics'])} topics")
        
        return unique_papers
    
    def parse_detailed_topics(self, text: str, papers: List[Dict]) -> List[Dict]:
        """Phase 2: Parse detailed topic content and assign to papers."""
        print("\n[PHASE 2] Parsing detailed topic content...")
        
        all_topics = []
        seen_codes = set()
        
        # Create Paper entries (Level 0)
        for paper in papers:
            paper_code = f"P{paper['number']}"
            paper_topic = {
                'code': paper_code,
                'title': paper['title'],
                'level': 0,
                'parent': None
            }
            all_topics.append(paper_topic)
            seen_codes.add(paper_code)
            
            # Add topics for this paper (Level 1)
            for topic_info in paper['topics']:
                topic_code = f"{paper_code}.T{topic_info['number']}"
                topic_entry = {
                    'code': topic_code,
                    'title': topic_info['title'],
                    'level': 1,
                    'parent': paper_code
                }
                all_topics.append(topic_entry)
                seen_codes.add(topic_code)
        
        # Now parse detailed content and assign to topics
        lines = text.split('\n')
        current_main_topic = None
        current_sub_topic = None
        bullet_counter = {}
        
        # Skip to main content section
        content_started = False
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Skip headers/footers
            if 'Pearson Edexcel' in line or 'Specification' in line or line.startswith('©'):
                continue
            
            # Detect main content start (after "Biology content" or similar)
            if not content_started:
                if re.match(r'^\d+\s+[A-Z]', line) and len(line) > 20:
                    content_started = True
                else:
                    continue
            
            # Skip paper overview sections
            if 'Paper code' in line or 'Content summary' in line or 'Assessment' in line:
                continue
            
            # Try to match this line to one of our Level 1 topics
            main_topic_match = re.match(r'^(\d+)\s+(.+)$', line)
            if main_topic_match and len(main_topic_match.group(1)) <= 2:
                topic_num = int(main_topic_match.group(1))
                topic_title = main_topic_match.group(2).strip()
                
                # Find this topic in our papers (it should exist in Paper 1 at minimum)
                for topic in all_topics:
                    if topic['level'] == 1 and f"T{topic_num}" in topic['code']:
                        current_main_topic = topic['code']
                        current_sub_topic = None
                        bullet_counter[current_main_topic] = 0
                        break
                continue
            
            # Lettered sub-topics (Level 2)
            sub_match = re.match(r'^\(?([a-z])\)?\s+(.+)', line, re.IGNORECASE)
            if sub_match and current_main_topic:
                letter = sub_match.group(1).lower()
                sub_title = sub_match.group(2).strip()
                
                if len(sub_title) > 5 and 'students should' not in sub_title.lower():
                    code = f"{current_main_topic}.{letter}"
                    
                    if code not in seen_codes:
                        current_sub_topic = code
                        all_topics.append({
                            'code': code,
                            'title': sub_title,
                            'level': 2,
                            'parent': current_main_topic
                        })
                        seen_codes.add(code)
                        bullet_counter[code] = 0
                continue
            
            # Numbered sub-points (Level 3)
            num_match = re.match(r'^(\d+(?:\.\d+)+)\s+(.+)', line)
            if num_match and (current_sub_topic or current_main_topic):
                number = num_match.group(1)
                content = num_match.group(2).strip()
                
                if len(content) > 10:
                    parent = current_sub_topic or current_main_topic
                    code = f"{parent}.{number}"
                    
                    if code not in seen_codes:
                        all_topics.append({
                            'code': code,
                            'title': content,
                            'level': 3,
                            'parent': parent
                        })
                        seen_codes.add(code)
                continue
            
            # Bullet points (Level 3/4)
            bullet_match = re.match(r'^[•●○■▪▫-]\s*(.+)', line)
            if bullet_match and (current_sub_topic or current_main_topic):
                content = bullet_match.group(1).strip()
                
                if len(content) > 15:
                    parent = current_sub_topic or current_main_topic
                    bullet_counter[parent] = bullet_counter.get(parent, 0) + 1
                    code = f"{parent}.{bullet_counter[parent]}"
                    
                    level = 3 if current_sub_topic else 2
                    
                    if code not in seen_codes:
                        all_topics.append({
                            'code': code,
                            'title': content,
                            'level': level,
                            'parent': parent
                        })
                        seen_codes.add(code)
        
        print(f"[OK] Parsed {len(all_topics)} total topics")
        
        # Show breakdown by level
        by_level = {}
        for topic in all_topics:
            level = topic['level']
            by_level[level] = by_level.get(level, 0) + 1
        
        print(f"[OK] Level breakdown:")
        for level in sorted(by_level.keys()):
            print(f"  - Level {level}: {by_level[level]} topics")
        
        return all_topics
    
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
                        pass  # Parent linking can fail if parent doesn't exist
            
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
        print(f"SCRAPING V3: {self.subject['name']} ({self.subject['qualification']})")
        print("=" * 60)
        
        # Download PDF
        pdf_content = self.download_pdf()
        if not pdf_content:
            return False
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_content)
        if not text:
            return False
        
        # Phase 1: Extract paper structure
        self.papers = self.extract_paper_structure(text)
        if not self.papers:
            print("[WARNING] No papers found in structure")
            return False
        
        # Phase 2: Parse detailed topics
        self.topics = self.parse_detailed_topics(text, self.papers)
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
    parser = argparse.ArgumentParser(description='Scrape International qualification topics (V3 - Two-Phase)')
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
    scraper = InternationalTopicScraperV3(subject)
    success = scraper.scrape()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

