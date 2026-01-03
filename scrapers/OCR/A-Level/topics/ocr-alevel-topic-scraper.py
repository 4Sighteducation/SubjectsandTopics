"""
OCR A-Level Topic Scraper - AI-Powered
=======================================

Uses AI (Claude/GPT-4/Gemini) to intelligently extract hierarchical topic structure 
from OCR A-Level specification PDFs.

Features:
- Downloads OCR specification PDFs
- Extracts text using PyPDF/pdfplumber
- Uses AI to parse curriculum structure
- Uploads to Supabase with proper hierarchy

Requirements:
    pip install anthropic openai google-generativeai pdfplumber pypdf

Setup:
    1. Get API key from Claude/OpenAI/Gemini
    2. Add to .env file: ANTHROPIC_API_KEY=your_key_here
    3. Run: python ocr-alevel-topic-scraper.py AL-BiologyA

Usage:
    python ocr-alevel-topic-scraper.py AL-BiologyA
    python ocr-alevel-topic-scraper.py AL-ChemistryA
    python ocr-alevel-topic-scraper.py --all  # All subjects
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

# Force UTF-8 output for Windows console
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
openai_key = os.getenv('OPENAI_API_KEY')
gemini_key = os.getenv('GEMINI2.5_API_KEY') or os.getenv('GEMINI_API_KEY')

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found in .env!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

# Determine which AI API to use
AI_PROVIDER = None
if anthropic_key:
    try:
        import anthropic
        claude = anthropic.Anthropic(api_key=anthropic_key)
        AI_PROVIDER = "anthropic"
        print("[INFO] Using Anthropic Claude API")
    except ImportError:
        print("[WARN] anthropic library not installed. Run: pip install anthropic")

if not AI_PROVIDER and openai_key:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=openai_key)
        AI_PROVIDER = "openai"
        print("[INFO] Using OpenAI GPT-4 API")
    except ImportError:
        print("[WARN] openai library not installed. Run: pip install openai")

if not AI_PROVIDER and gemini_key:
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        gemini_model = genai.GenerativeModel('gemini-1.5-pro')
        AI_PROVIDER = "gemini"
        print("[INFO] Using Google Gemini API")
    except ImportError:
        print("[WARN] google-generativeai library not installed. Run: pip install google-generativeai")

if not AI_PROVIDER:
    print("[ERROR] No AI API keys found in .env!")
    print("Please add one of: ANTHROPIC_API_KEY, OPENAI_API_KEY, or GEMINI2.5_API_KEY")
    sys.exit(1)


# ================================================================
# AI EXTRACTION PROMPT
# ================================================================

EXTRACTION_PROMPT = """I need you to extract the curriculum content structure from this OCR A-Level specification PDF.

Please create a hierarchical numbered list of ALL the content topics and specifications, organized as follows:

1. Start with Components/Papers (if they exist - e.g., "Component 01: Development of practical skills")
2. Then main topic/module areas (e.g., "Module 1: Development of practical skills in biology")
3. Then sub-sections (e.g., "1.1 Practical skills assessed in a written examination")
4. Then specific learning objectives and content points
5. Include practical investigations where mentioned

Use this numbering format:
1. Component/Module Name
1.1 Main Topic Name
1.1.1 Sub-topic Name
1.1.1.1 Specific content point
1.1.1.2 Another content point

Rules:
- Include ONLY the actual curriculum content (skip aims, assessment info, administrative sections)
- Use consistent decimal numbering (1.1.1.1 style)
- Keep topic titles concise but descriptive
- Include all levels of detail from the specification
- If there are no components/modules, start directly with main topics as "1. Topic Name"
- For OCR specs, pay attention to the content section which usually has detailed topic breakdowns

Output ONLY the numbered hierarchy, nothing else."""


# ================================================================
# SCRAPER CLASS
# ================================================================

class OCRALevelScraper:
    """AI-powered scraper for OCR A-Level specifications."""
    
    def __init__(self, subject_info: Dict):
        self.subject = subject_info
        self.topics = []
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        
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
        """Extract text from PDF using pdfplumber or pypdf."""
        # Try pdfplumber first (better quality)
        try:
            import pdfplumber
            print("\n[INFO] Extracting text from PDF using pdfplumber...")
            
            from io import BytesIO
            pdf_file = BytesIO(pdf_content)
            text = ""
            
            with pdfplumber.open(pdf_file) as pdf:
                total_pages = len(pdf.pages)
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    if i % 10 == 0:
                        print(f"[INFO] Processed {i+1}/{total_pages} pages...")
            
            print(f"[OK] Extracted {len(text)} characters from PDF")
            
            # Save debug copy
            debug_file = self.debug_dir / f"{self.subject['code']}-spec.txt"
            debug_file.write_text(text, encoding='utf-8')
            print(f"[DEBUG] Saved to {debug_file.name}")
            
            return text
            
        except ImportError:
            print("[INFO] pdfplumber not available, trying pypdf...")
        except Exception as e:
            print(f"[WARN] pdfplumber extraction failed: {str(e)}, trying pypdf...")
        
        # Fallback to pypdf
        try:
            from pypdf import PdfReader
            print("\n[INFO] Extracting text from PDF using pypdf...")
            
            from io import BytesIO
            pdf_file = BytesIO(pdf_content)
            reader = PdfReader(pdf_file)
            
            text = ""
            total_pages = len(reader.pages)
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                if i % 10 == 0:
                    print(f"[INFO] Processed {i+1}/{total_pages} pages...")
            
            print(f"[OK] Extracted {len(text)} characters from PDF")
            
            # Save debug copy
            debug_file = self.debug_dir / f"{self.subject['code']}-spec.txt"
            debug_file.write_text(text, encoding='utf-8')
            print(f"[DEBUG] Saved to {debug_file.name}")
            
            return text
            
        except ImportError:
            print("[ERROR] Neither pdfplumber nor pypdf is installed!")
            print("Run: pip install pdfplumber pypdf")
            return None
        except Exception as e:
            print(f"[ERROR] PDF extraction failed: {str(e)}")
            return None
    
    def extract_with_ai(self, pdf_text: str) -> Optional[str]:
        """Send PDF text to AI API for structure extraction."""
        print(f"\n[INFO] Sending to {AI_PROVIDER.upper()} API...")
        
        # Limit text size to avoid API limits
        max_chars = 150000 if AI_PROVIDER == "openai" else 80000
        if len(pdf_text) > max_chars:
            print(f"[WARNING] Truncating {len(pdf_text)} → {max_chars} chars")
            pdf_text = pdf_text[:max_chars]
        
        try:
            if AI_PROVIDER == "anthropic":
                response = claude.messages.create(
                    model="claude-3-5-haiku-20241022",  # Fast and cheap
                    max_tokens=8192,
                    messages=[{"role": "user", "content": f"{EXTRACTION_PROMPT}\n\nPDF:\n\n{pdf_text}"}]
                )
                hierarchy = response.content[0].text
                print(f"[OK] Extracted {len(hierarchy)} chars")
                
            elif AI_PROVIDER == "openai":
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": f"{EXTRACTION_PROMPT}\n\nPDF:\n\n{pdf_text}"}],
                    max_tokens=8192,
                    temperature=0
                )
                hierarchy = response.choices[0].message.content
                print(f"[OK] Extracted {len(hierarchy)} chars")
                
            elif AI_PROVIDER == "gemini":
                response = gemini_model.generate_content(f"{EXTRACTION_PROMPT}\n\nPDF:\n\n{pdf_text}")
                hierarchy = response.text
                print(f"[OK] Extracted {len(hierarchy)} chars")
            
            # Save AI output
            ai_output_file = self.debug_dir / f"{self.subject['code']}-ai-output.txt"
            ai_output_file.write_text(hierarchy, encoding='utf-8')
            print(f"[DEBUG] Saved to {ai_output_file.name}")
            
            return hierarchy
            
        except Exception as e:
            print(f"[ERROR] AI extraction failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def parse_hierarchy(self, text: str) -> List[Dict]:
        """Parse AI output into structured topic list."""
        print("\n[INFO] Parsing hierarchy...")
        
        topics = []
        parent_stack = {}
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Match numbered items: 1. Title, 1.1 Title, 1.1.1 Title, etc.
            match = re.match(r'^([\d.]+)\s+(.+)$', line)
            if not match:
                continue
            
            number = match.group(1).rstrip('.')
            title = match.group(2).strip()
            
            # Calculate level based on dots
            level = number.count('.')
            
            # Create code from number
            code = number.replace('.', '_')
            
            # Determine parent
            parent_code = None
            if level > 0:
                # Parent is the last item at level-1
                parent_code = parent_stack.get(level - 1)
            
            topics.append({
                'code': code,
                'title': title,
                'level': level,
                'parent': parent_code
            })
            
            # Update parent stack
            parent_stack[level] = code
            
            # Clear deeper levels
            for l in list(parent_stack.keys()):
                if l > level:
                    del parent_stack[l]
        
        print(f"[OK] Parsed {len(topics)} topics")
        
        # Show distribution
        levels = {}
        for t in topics:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("   Distribution:")
        for l in sorted(levels.keys()):
            print(f"   Level {l}: {levels[l]} topics")
        
        return topics
    
    def upload_to_supabase(self, topics: List[Dict]) -> bool:
        """Upload topics to Supabase."""
        print("\n[INFO] Uploading to database...")
        
        try:
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': f"{self.subject['name']} ({self.subject['qualification']})",
                'subject_code': self.subject['code'],
                'qualification_type': self.subject['qualification'],
                'specification_url': self.subject['pdf_url'],
                'exam_board': self.subject['exam_board']
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            subject_id = subject_result.data[0]['id']
            print(f"[OK] Subject: {subject_result.data[0]['subject_name']} (ID: {subject_id})")
            
            # Clear old topics
            supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
            print("[OK] Cleared old topics")
            
            # Insert topics
            to_insert = [{
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': t['title'],
                'topic_level': t['level'],
                'exam_board': self.subject['exam_board']
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
            print(f"[ERROR] Upload failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def scrape(self) -> bool:
        """Main scraping workflow."""
        print("\n" + "=" * 80)
        print(f"OCR A-LEVEL: {self.subject['name']} ({self.subject['code']})")
        print("=" * 80)
        
        # Download PDF
        pdf_content = self.download_pdf()
        if not pdf_content:
            return False
        
        # Extract text
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
            print("\n[SUCCESS] ✅ Scraping complete!")
        else:
            print("\n[FAILED] ❌ Scraping failed")
        
        return success


# ================================================================
# MAIN
# ================================================================

def load_subjects() -> Dict:
    """Load subjects from JSON file."""
    subjects_file = Path(__file__).parent.parent / "ocr-alevel-subjects.json"
    
    if not subjects_file.exists():
        print(f"[ERROR] Subjects file not found: {subjects_file}")
        sys.exit(1)
    
    with open(subjects_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description='OCR A-Level topic scraper')
    parser.add_argument('subject', nargs='?', help='Subject code (e.g., AL-BiologyA) or --all for all subjects')
    parser.add_argument('--all', action='store_true', help='Scrape all subjects')
    args = parser.parse_args()
    
    # Load subjects
    subjects = load_subjects()
    
    print("\n" + "🔬 " * 20)
    print("OCR A-LEVEL TOPIC SCRAPER - AI POWERED")
    print("🔬 " * 20)
    
    if args.all:
        # Scrape all subjects
        print(f"\nScraping ALL {len(subjects)} OCR A-Level subjects...")
        
        success_count = 0
        failed = []
        
        for subject_code, subject_info in subjects.items():
            print(f"\n\n{'=' * 80}")
            print(f"Processing {subject_code} ({subject_info['name']})")
            print(f"{'=' * 80}")
            
            scraper = OCRALevelScraper(subject_info)
            if scraper.scrape():
                success_count += 1
            else:
                failed.append(subject_code)
            
            # Delay between subjects
            if subject_code != list(subjects.keys())[-1]:
                print("\n[INFO] Waiting 5 seconds before next subject...")
                import time
                time.sleep(5)
        
        # Summary
        print("\n\n" + "=" * 80)
        print("BATCH COMPLETE")
        print("=" * 80)
        print(f"✅ Success: {success_count}")
        print(f"❌ Failed: {len(failed)}")
        if failed:
            print(f"Failed subjects: {', '.join(failed)}")
        
    else:
        # Scrape single subject
        subject_code = args.subject
        
        if not subject_code:
            print("\n[ERROR] Please specify a subject code or use --all")
            print(f"Available subjects: {', '.join(subjects.keys())}")
            sys.exit(1)
        
        if subject_code not in subjects:
            print(f"\n[ERROR] Unknown subject: {subject_code}")
            print(f"Available subjects: {', '.join(subjects.keys())}")
            sys.exit(1)
        
        scraper = OCRALevelScraper(subjects[subject_code])
        success = scraper.scrape()
        
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

