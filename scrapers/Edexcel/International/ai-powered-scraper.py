"""
AI-Powered International Qualification Scraper
==============================================

Uses Claude API to intelligently extract hierarchical topic structure from PDFs.

Requirements:
    pip install anthropic

Setup:
    1. Get Claude API key from: https://console.anthropic.com/
    2. Add to .env file: ANTHROPIC_API_KEY=your_key_here
    3. Run: python ai-powered-scraper.py --subject IG-Biology

Cost: ~$0.50-1.00 per subject (very reasonable)
"""

import os
import sys
import re
import json
import argparse
import requests
from pathlib import Path
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
anthropic_key = os.getenv('ANTHROPIC_API_KEY')

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found in .env!")
    sys.exit(1)

if not anthropic_key:
    print("[ERROR] ANTHROPIC_API_KEY not found in .env!")
    print("Get your key from: https://console.anthropic.com/")
    print("Add to .env: ANTHROPIC_API_KEY=your_key_here")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

try:
    import anthropic
except ImportError:
    print("[ERROR] anthropic library not installed!")
    print("Run: pip install anthropic")
    sys.exit(1)

claude = anthropic.Anthropic(api_key=anthropic_key)


EXTRACTION_PROMPT = """I need you to extract the curriculum content structure from this International GCSE/A Level specification PDF.

Please create a hierarchical numbered list of ALL the content topics and specifications, organized as follows:

1. Start with Papers/Components (if they exist)
2. Then main topic areas (e.g., "The nature and variety of living organisms")
3. Then sub-sections (e.g., "Characteristics of living organisms")
4. Then specific learning objectives and content points
5. Include practical investigations where mentioned

Use this numbering format:
1. Paper/Component Name
1.1 Main Topic Name
1.1.1 Sub-topic Name
1.1.1.1 Specific content point
1.1.1.2 Another content point

Rules:
- Include ONLY the actual curriculum content (skip aims, assessment info, administrative sections)
- Use consistent decimal numbering (1.1.1.1 style)
- Keep topic titles concise but descriptive
- Include all levels of detail from the specification
- If there are no papers, start directly with main topics as "1. Topic Name"

Output ONLY the numbered hierarchy, nothing else."""


class AIPoweredScraper:
    """Scraper that uses Claude AI to extract curriculum structure."""
    
    def __init__(self, subject_info: Dict):
        self.subject = subject_info
        self.topics = []
        
    def download_pdf(self) -> Optional[bytes]:
        """Download PDF from URL."""
        print(f"\n[INFO] Downloading PDF from {self.subject['pdf_url']}...")
        
        try:
            response = requests.get(self.subject['pdf_url'], timeout=60)
            response.raise_for_status()
            print(f"[OK] Downloaded {len(response.content)} bytes ({len(response.content)/1024/1024:.1f} MB)")
            return response.content
        except Exception as e:
            print(f"[ERROR] Failed to download PDF: {str(e)}")
            return None
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> Optional[str]:
        """Extract text from PDF using pdfplumber."""
        try:
            import pdfplumber
        except ImportError:
            print("[ERROR] pdfplumber not installed. Run: pip install pdfplumber")
            return None
        
        print("\n[INFO] Extracting text from PDF...")
        
        try:
            from io import BytesIO
            pdf_file = BytesIO(pdf_content)
            text = ""
            
            with pdfplumber.open(pdf_file) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    if i % 10 == 0:
                        print(f"[INFO] Processed {i+1}/{len(pdf.pages)} pages...")
            
            print(f"[OK] Extracted {len(text)} characters from PDF")
            return text
            
        except Exception as e:
            print(f"[ERROR] PDF extraction failed: {str(e)}")
            return None
    
    def extract_with_ai(self, pdf_text: str) -> Optional[str]:
        """Send PDF text to Claude API using fast Haiku model."""
        print("\n[INFO] Sending to Claude Haiku (fast model)...")
        
        # Use smaller chunks for reliability
        max_chars = 80000  # ~20k tokens - more reliable
        if len(pdf_text) > max_chars:
            print(f"[WARNING] Truncating {len(pdf_text)} → {max_chars} chars")
            pdf_text = pdf_text[:max_chars]
        
        try:
            # Use Haiku - fastest and most reliable
            message = claude.messages.create(
                model="claude-3-5-haiku-20241022",  # Fast Haiku model
                max_tokens=8192,
                messages=[
                    {
                        "role": "user",
                        "content": f"{EXTRACTION_PROMPT}\n\nPDF Text:\n\n{pdf_text}"
                    }
                ]
            )
            
            # Extract text response
            hierarchy_text = message.content[0].text
            
            print(f"[OK] AI extracted {len(hierarchy_text)} characters")
            print(f"[OK] Tokens used: {message.usage.input_tokens} in, {message.usage.output_tokens} out")
            
            # Save raw output for debugging
            debug_file = Path(__file__).parent / "adobe-ai-output" / f"{self.subject['code']}-ai-output.txt"
            debug_file.parent.mkdir(exist_ok=True)
            debug_file.write_text(hierarchy_text, encoding='utf-8')
            print(f"[OK] Saved AI output to: {debug_file.name}")
            
            return hierarchy_text
            
        except Exception as e:
            print(f"[ERROR] AI extraction failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def parse_hierarchy(self, text: str) -> List[Dict]:
        """Parse AI-generated hierarchy into topic structure."""
        print("\n[INFO] Parsing AI output...")
        
        topics = []
        lines = text.split('\n')
        
        parent_stack = {}  # Track parents at each level
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Match numbered items: 1., 1.1, 1.1.1, 1.1.1.1, etc.
            match = re.match(r'^([\d.]+)\s+(.+)$', line)
            if not match:
                continue
            
            number = match.group(1).rstrip('.')  # Remove trailing dot
            title = match.group(2).strip()
            
            # Determine level by counting dots
            level = number.count('.')
            
            # Generate clean code
            code = number.replace('.', '_')  # 1.1.1 → 1_1_1
            
            # Find parent
            parent_code = None
            if level > 0:
                parent_code = parent_stack.get(level - 1)
            
            # Create topic entry
            topic = {
                'code': code,
                'title': title,
                'level': level,
                'parent': parent_code,
                'number': number
            }
            
            topics.append(topic)
            
            # Update parent stack
            parent_stack[level] = code
            
            # Clear deeper levels
            levels_to_clear = [l for l in parent_stack.keys() if l > level]
            for l in levels_to_clear:
                del parent_stack[l]
        
        print(f"[OK] Parsed {len(topics)} topics")
        
        # Show level breakdown
        by_level = {}
        for topic in topics:
            level = topic['level']
            by_level[level] = by_level.get(level, 0) + 1
        
        print(f"[OK] Level breakdown:")
        for level in sorted(by_level.keys()):
            print(f"  - Level {level}: {by_level[level]} items")
        
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
            try:
                supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
                print(f"[OK] Cleared old topics")
            except Exception as e:
                print(f"[WARNING] Clear operation: {str(e)}")
            
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
                print(f"[OK] Uploaded batch {i//BATCH_SIZE + 1}: {len(inserted.data)} items")
            
            print(f"[OK] Total uploaded: {len(all_inserted)} items")
            
            # Link parent relationships
            code_to_id = {t['topic_code']: t['id'] for t in all_inserted}
            
            linked = 0
            for topic in topics:
                if topic['parent'] and topic['code'] in code_to_id and topic['parent'] in code_to_id:
                    try:
                        supabase.table('staging_aqa_topics').update({
                            'parent_topic_id': code_to_id[topic['parent']]
                        }).eq('id', code_to_id[topic['code']]).execute()
                        linked += 1
                    except:
                        pass
            
            print(f"[OK] Linked {linked} parent relationships")
            return True
            
        except Exception as e:
            print(f"[ERROR] Upload failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def scrape(self) -> bool:
        """Main AI-powered scraping workflow."""
        print("\n" + "=" * 60)
        print(f"AI SCRAPING: {self.subject['name']} ({self.subject['qualification']})")
        print("=" * 60)
        
        # Download PDF
        pdf_content = self.download_pdf()
        if not pdf_content:
            return False
        
        # Extract text from PDF
        pdf_text = self.extract_text_from_pdf(pdf_content)
        if not pdf_text:
            return False
        
        # Extract with AI
        hierarchy_text = self.extract_with_ai(pdf_text)
        if not hierarchy_text:
            return False
        
        # Parse hierarchy
        self.topics = self.parse_hierarchy(hierarchy_text)
        if not self.topics:
            print("[ERROR] No topics found in AI output")
            return False
        
        # Upload
        success = self.upload_to_supabase(self.topics)
        
        if success:
            print("\n[SUCCESS] AI scraping complete!")
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
    parser = argparse.ArgumentParser(description='AI-powered scraper using Claude API')
    parser.add_argument('--subject', help='Subject code (e.g., IG-Biology)')
    parser.add_argument('--all-igcse', action='store_true', help='Scrape all International GCSE')
    parser.add_argument('--all-ial', action='store_true', help='Scrape all International A Level')
    parser.add_argument('--all', action='store_true', help='Scrape all International subjects')
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    
    # Determine subjects to scrape
    subjects_to_scrape = []
    
    if args.subject:
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
    
    # Scrape
    print(f"\n[INFO] Will scrape {len(subjects_to_scrape)} subject(s) using Claude AI")
    print(f"[INFO] Estimated cost: ${len(subjects_to_scrape) * 0.50:.2f} - ${len(subjects_to_scrape) * 1.00:.2f}")
    
    results = {'success': 0, 'failed': 0}
    
    for subject in subjects_to_scrape:
        scraper = AIPoweredScraper(subject)
        success = scraper.scrape()
        
        if success:
            results['success'] += 1
        else:
            results['failed'] += 1
        
        print("\n" + "-" * 60)
    
    # Summary
    print("\n" + "=" * 60)
    print("AI SCRAPING COMPLETE")
    print("=" * 60)
    print(f"Total: {len(subjects_to_scrape)}")
    print(f"Success: {results['success']}")
    print(f"Failed: {results['failed']}")
    print("=" * 60)


if __name__ == '__main__':
    main()

