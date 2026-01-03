"""
Universal International Qualification Topic Scraper V4
=====================================================

FLEXIBLE APPROACH:
- Papers are optional (some subjects have them, some don't)
- Focus on capturing numbered specifications (1.1, 2.7, etc.) - the ACTUAL content
- Handle lettered sub-sections (a), (b), (c)
- Skip qualification aims/objectives sections
- Look for "Students should:" markers

Usage:
    python universal-international-scraper-v4.py --subject IG-Biology
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


class InternationalTopicScraperV4:
    """Flexible scraper focusing on actual numbered specifications."""
    
    def __init__(self, subject_info: Dict):
        self.subject = subject_info
        self.papers = []  # Optional paper structure
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
    
    def extract_optional_papers(self, text: str) -> List[Dict]:
        """Extract paper structure if it exists (from qualification overview)."""
        print("\n[INFO] Looking for paper structure...")
        
        papers = []
        lines = text.split('\n')
        
        current_paper = None
        capturing_topics = False
        
        for line in lines:
            line = line.strip()
            
            # Detect paper definition
            paper_match = re.match(r'^[\w\s]+(Paper|Component|Unit)\s+(\d+)', line, re.IGNORECASE)
            if paper_match and 'Paper code' not in line:
                paper_num = paper_match.group(2)
                
                if current_paper and len(current_paper.get('topics', [])) > 0:
                    papers.append(current_paper)
                
                current_paper = {
                    'number': int(paper_num),
                    'title': f"Paper {paper_num}",
                    'topics': []
                }
                capturing_topics = False
                continue
            
            # Look for topic list under papers
            if current_paper and ('Content summary' in line or 'Questions may come from' in line):
                capturing_topics = True
                continue
            
            # Capture numbered topics
            if current_paper and capturing_topics:
                if line.startswith('Assessment') or line.startswith('□ The paper'):
                    capturing_topics = False
                    continue
                
                topic_match = re.match(r'^(\d+)\s+(.+)$', line)
                if topic_match and len(topic_match.group(1)) <= 2:
                    topic_num = topic_match.group(1)
                    topic_title = topic_match.group(2).strip()
                    
                    if len(topic_title) > 15 and not topic_title.isdigit():
                        current_paper['topics'].append({
                            'number': int(topic_num),
                            'title': topic_title
                        })
        
        if current_paper and len(current_paper.get('topics', [])) > 0:
            papers.append(current_paper)
        
        # Deduplicate
        seen = set()
        unique_papers = []
        for paper in papers:
            if paper['number'] not in seen:
                seen.add(paper['number'])
                unique_papers.append(paper)
        
        if unique_papers:
            print(f"[OK] Found {len(unique_papers)} papers")
            for paper in unique_papers:
                print(f"  - Paper {paper['number']}: {len(paper['topics'])} topics listed")
        else:
            print("[OK] No paper structure found (single assessment)")
        
        return unique_papers
    
    def parse_content_specifications(self, text: str, papers: List[Dict]) -> List[Dict]:
        """Parse the actual numbered content specifications."""
        print("\n[INFO] Parsing content specifications...")
        
        all_topics = []
        seen_codes = set()
        
        # If papers exist, create them (Level 0)
        paper_map = {}
        if papers:
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
                paper_map[paper['number']] = paper_code
                
                # Add main topics for this paper (Level 1)
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
        
        # Parse actual content
        lines = text.split('\n')
        
        current_main_topic = None
        current_sub_section = None
        in_content_area = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Skip header/footer
            if 'Pearson Edexcel' in line or 'Specification' in line or line.startswith('©'):
                continue
            
            # Detect content area start
            if not in_content_area:
                # Look for main topic headers (after aims/objectives section)
                if re.match(r'^(\d+)\s+[A-Z]', line) and len(line) > 20:
                    # Check if we're past the aims section
                    if i > 50 and 'aim' not in line.lower():  # Rough heuristic
                        in_content_area = True
                    else:
                        continue
                else:
                    continue
            
            # Skip assessment/overview sections
            if any(skip in line.lower() for skip in ['paper code', 'content summary', 'assessment overview', 'qualification at a glance']):
                continue
            
            # Detect main topic (Level 1 or top-level if no papers)
            main_topic_match = re.match(r'^(\d+)\s+(.+)$', line)
            if main_topic_match and len(main_topic_match.group(1)) <= 2:
                topic_num = int(main_topic_match.group(1))
                topic_title = main_topic_match.group(2).strip()
                
                # Filter out short titles, page numbers
                if len(topic_title) > 15 and not topic_title.isdigit():
                    # Check if this matches a paper topic
                    topic_code = None
                    if papers:
                        # Find matching paper topic
                        for topic in all_topics:
                            if topic['level'] == 1 and f"T{topic_num}" in topic['code']:
                                current_main_topic = topic['code']
                                current_sub_section = None
                                break
                    else:
                        # No papers - create top-level topic
                        topic_code = f"T{topic_num}"
                        if topic_code not in seen_codes:
                            current_main_topic = topic_code
                            current_sub_section = None
                            all_topics.append({
                                'code': topic_code,
                                'title': topic_title,
                                'level': 0,
                                'parent': None
                            })
                            seen_codes.add(topic_code)
                continue
            
            # Detect sub-section with letter: (a), (b), (c) - Level 2
            sub_section_match = re.match(r'^\(?([a-z])\)?\s+(.+)', line, re.IGNORECASE)
            if sub_section_match and current_main_topic:
                letter = sub_section_match.group(1).lower()
                section_title = sub_section_match.group(2).strip()
                
                # Must be substantial title, not "Students should"
                if len(section_title) > 5 and 'students should' not in section_title.lower():
                    code = f"{current_main_topic}.{letter}"
                    
                    if code not in seen_codes:
                        current_sub_section = code
                        all_topics.append({
                            'code': code,
                            'title': section_title,
                            'level': 2,
                            'parent': current_main_topic
                        })
                        seen_codes.add(code)
                continue
            
            # **KEY: Detect numbered specifications (1.1, 2.7, etc.) - Level 3**
            # This is the ACTUAL content!
            spec_match = re.match(r'^(\d+\.\d+)\s+(.+)', line)
            if spec_match:
                spec_num = spec_match.group(1)
                spec_content = spec_match.group(2).strip()
                
                # Must have substantial content
                if len(spec_content) > 10:
                    parent = current_sub_section or current_main_topic
                    
                    if parent:
                        code = f"{parent}.{spec_num}"
                        
                        if code not in seen_codes:
                            all_topics.append({
                                'code': code,
                                'title': spec_content,
                                'level': 3,
                                'parent': parent
                            })
                            seen_codes.add(code)
                continue
        
        print(f"[OK] Parsed {len(all_topics)} total items")
        
        # Show breakdown
        by_level = {}
        for topic in all_topics:
            level = topic['level']
            by_level[level] = by_level.get(level, 0) + 1
        
        print(f"[OK] Level breakdown:")
        for level in sorted(by_level.keys()):
            print(f"  - Level {level}: {by_level[level]} items")
        
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
            
            # Clear old topics - do it properly
            try:
                delete_result = supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
                print(f"[OK] Cleared {len(delete_result.data) if delete_result.data else 0} old topics")
            except Exception as e:
                print(f"[WARNING] Clear operation: {str(e)}")
            
            # Deduplicate topics by code before inserting
            unique_topics = {}
            for t in topics:
                if t['code'] not in unique_topics:
                    unique_topics[t['code']] = t
            
            topics = list(unique_topics.values())
            print(f"[OK] Deduplicated to {len(topics)} unique items")
            
            # Insert topics
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
                print(f"[OK] Uploaded batch {i//BATCH_SIZE + 1}: {len(inserted.data)} items")
            
            print(f"[OK] Total uploaded: {len(all_inserted)} items")
            
            # Link parent relationships
            code_to_id = {t['topic_code']: t['id'] for t in all_inserted}
            
            for topic in topics:
                if topic['parent'] and topic['code'] in code_to_id and topic['parent'] in code_to_id:
                    try:
                        supabase.table('staging_aqa_topics').update({
                            'parent_topic_id': code_to_id[topic['parent']]
                        }).eq('id', code_to_id[topic['code']]).execute()
                    except:
                        pass
            
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
        print(f"SCRAPING V4: {self.subject['name']} ({self.subject['qualification']})")
        print("=" * 60)
        
        # Download PDF
        pdf_content = self.download_pdf()
        if not pdf_content:
            return False
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_content)
        if not text:
            return False
        
        # Look for paper structure (optional)
        self.papers = self.extract_optional_papers(text)
        
        # Parse content specifications (the actual numbered items)
        self.topics = self.parse_content_specifications(text, self.papers)
        if not self.topics:
            print("[WARNING] No content specifications found")
            return False
        
        # Upload
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
    parser = argparse.ArgumentParser(description='Scrape International topics (V4 - Flexible, focuses on specs)')
    parser.add_argument('--subject', help='Subject code (e.g., IG-Biology)')
    
    args = parser.parse_args()
    
    if not args.subject:
        parser.print_help()
        sys.exit(1)
    
    script_dir = Path(__file__).parent
    
    # Load the appropriate file
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
    scraper = InternationalTopicScraperV4(subject)
    success = scraper.scrape()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

