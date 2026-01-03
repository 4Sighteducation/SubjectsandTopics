"""
OCR A-Level Further Mathematics A Manual Structure Scraper
==========================================================

Extracts topics from OCR Further Mathematics A H245 specification.

Structure:
- Level 0: Main sections (Mandatory papers, Optional papers)
- Level 1: Subject areas (Pure mathematics, Statistics, Mechanics, etc.)
- Level 2: Topics (Proof, Complex numbers, etc.)
- Level 3: OCR Ref items (4.01a, 4.01b, etc.) combining Stage 1 & Stage 2

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-further-maths-a-manual.py
"""

import os
import sys
import re
import time
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
openai_key = os.getenv('OPENAI_API_KEY')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

# AI provider - use OpenAI like the working Maths scraper
AI_PROVIDER = None
if openai_key:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=openai_key)
        AI_PROVIDER = "openai"
        print("[INFO] Using OpenAI GPT-4 API")
    except ImportError:
        pass

if not AI_PROVIDER and anthropic_key:
    try:
        import anthropic
        claude = anthropic.Anthropic(api_key=anthropic_key)
        AI_PROVIDER = "anthropic"
        print("[INFO] Using Anthropic Claude API")
    except ImportError:
        pass

if not AI_PROVIDER:
    print("[ERROR] No AI API keys found!")
    sys.exit(1)


# ================================================================
# CONFIGURATION
# ================================================================

PDF_URL = 'https://www.ocr.org.uk/Images/308752-specification-accredited-a-level-gce-further-mathematics-a-h245.pdf'

# Structure overview
STRUCTURE = {
    'mandatory': {
        'name': 'Mandatory papers',
        'topics': ['Pure mathematics']
    },
    'optional': {
        'name': 'Optional papers',
        'topics': ['Statistics', 'Mechanics', 'Discrete mathematics', 'Additional pure mathematics']
    }
}


class FurtherMathsAScraper:
    """Scraper for OCR A-Level Further Mathematics A."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_pages = []
    
    def scrape_all(self):
        """Scrape all topics."""
        print("\n" + "📐➕ "*35)
        print("OCR FURTHER MATHEMATICS A SCRAPER")
        print("📐➕ "*35)
        
        # Download PDF
        print("\n[INFO] Downloading PDF...")
        try:
            response = requests.get(PDF_URL, timeout=60)
            response.raise_for_status()
            pdf_content = response.content
            print(f"[OK] Downloaded {len(pdf_content)/1024/1024:.1f} MB")
        except Exception as e:
            print(f"[ERROR] PDF download failed: {e}")
            return False
        
        # Extract PDF text by page
        self.pdf_pages = self._extract_pdf_pages(pdf_content)
        if not self.pdf_pages:
            return False
        
        # Debug: Save snippet from page 17
        debug_file = self.debug_dir / "H245-pdf-snippet.txt"
        if len(self.pdf_pages) >= 18:
            snippet = "\n=== PAGE 17 ===\n" + self.pdf_pages[16] + "\n=== PAGE 18 ===\n" + self.pdf_pages[17]
            debug_file.write_text(snippet, encoding='utf-8')
            print(f"[DEBUG] Saved PDF snippet to {debug_file.name}")
        
        # Get content from page 15 onwards (tables start page 17)
        content_pages = self.pdf_pages[14:]  # Start from page 15 (0-indexed)
        content_text = "\n".join(content_pages)
        
        # Extract all topics
        all_topics = self._extract_all_topics(content_text)
        if not all_topics:
            print("[ERROR] No topics extracted")
            return False
        
        # Count by level
        level_counts = {}
        for t in all_topics:
            level_counts[t['level']] = level_counts.get(t['level'], 0) + 1
        level_str = ", ".join([f"L{k}:{v}" for k, v in sorted(level_counts.items())])
        print(f"[OK] Extracted {len(all_topics)} topics ({level_str})")
        
        # Upload
        return self._upload_all(all_topics)
    
    def _extract_pdf_pages(self, pdf_content: bytes) -> List[str]:
        """Extract text from PDF, returning per-page text."""
        try:
            import pdfplumber
            from io import BytesIO
            
            print("[INFO] Extracting PDF text...")
            page_texts = []
            
            with pdfplumber.open(BytesIO(pdf_content)) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    page_texts.append(page_text)
                    
                    if i % 20 == 0 and i > 0:
                        print(f"[INFO] Processed {i+1}/{len(pdf.pages)} pages...")
            
            print(f"[OK] Extracted {len(page_texts)} pages")
            return page_texts
        except Exception as e:
            print(f"[ERROR] PDF extraction failed: {e}")
            return []
    
    def _extract_all_topics(self, content_text: str) -> List[Dict]:
        """Extract all topics using AI."""
        
        prompt = f"""You must extract the COMPLETE hierarchy from OCR Further Mathematics A (H245) specification starting from page 15.

CRITICAL: Extract EVERYTHING you can see in the content below. Do NOT stop partway. Do NOT ask "Would you like me to continue?" - just extract ALL topics visible in the content. Do NOT ask for confirmation. Do NOT ask questions. Extract EVERYTHING NOW.

OUTPUT FORMAT: Use ONLY numbered format (1, 1.1, 1.1.1, 1.1.1.1) - NO bullets, NO markdown.

STRUCTURE (4 levels):

Level 0: Main sections (2 total)
  1 Mandatory papers (Pure Core)
  2 Optional papers

Level 1: Subject areas
  Under Mandatory:
    1.1 Pure mathematics
  Under Optional:
    2.1 Statistics
    2.2 Mechanics
    2.3 Discrete mathematics
    2.4 Additional pure mathematics

Level 2: Topic headings (Subject Content column)
  Examples under Pure mathematics: "Proof", "Complex numbers", "Matrices", "Further vectors", "Further algebra", "Series", "Hyperbolic functions", "Further calculus", "Polar coordinates", "Differential equations"
  Examples under Statistics: "Probability", "Discrete random variables", "Continuous random variables", etc.

Level 3: OCR Ref items with letter codes
  - Format: [OCR Ref code] + [combined Stage 1 & Stage 2 content]
  - IMPORTANT: Numbering starts at 4 (e.g., 4.01a, 4.01b, 4.02a, 4.02b...)
  - Letter codes may NOT be sequential
  - Combine both "Stage 1" AND "Stage 2" columns into single description

EXAMPLE OUTPUT (START WITH SECTION 4, NOT SECTION 7):
1 Mandatory papers
1.1 Pure mathematics
1.1.1 Proof
1.1.1.1 4.01a Be able to construct proofs using mathematical induction.
1.1.1.2 4.01b Be able to construct proofs of a more demanding nature, including conjecture followed by proof.
1.1.2 Complex numbers
1.1.2.1 4.02a Understand and be able to use De Moivre's theorem...
1.1.2.2 4.02b Be able to use complex numbers to solve geometric problems...
1.1.3 Matrices
1.1.3.1 4.03a [content]
(continue for ALL Pure mathematics topics - sections 4.01 through 4.10...)
2 Optional papers
2.1 Statistics
2.1.1 Probability
2.1.1.1 5.01a [content from section 5]
(continue for all Statistics...)
2.2 Mechanics
2.2.1 Dimensional analysis
2.2.1.1 6.01a [content from section 6]
(continue for all Mechanics...)
2.3 Discrete mathematics
2.3.1 Mathematical preliminaries
2.3.1.1 7.01a [content from section 7]
(continue for all Discrete...)
2.4 Additional pure mathematics
2.4.1 Sequences and series
2.4.1.1 8.01a [content from section 8]
(continue for all Additional pure...)

CRITICAL EXTRACTION RULES:
1. START from section 4.01 (Pure Core/Mandatory papers) - this is the FIRST section
2. Extract BOTH Level 0 sections (Mandatory and Optional)
3. Extract ALL Level 1 subject areas: Pure mathematics (section 4), Statistics (section 5), Mechanics (section 6), Discrete mathematics (section 7), Additional pure (section 8)
4. For each subject area, extract ALL Level 2 topics from the Subject/Content column
5. For each Level 2 topic, extract EVERY OCR Ref item (4.01a, 4.01b, 4.02a, etc.)
6. Letter codes may skip - extract ALL letters you find
7. Combine Stage 1 and Stage 2 text for each Level 3 item
8. Keep OCR Ref code as part of Level 3 title
9. The content includes sections 4, 5, 6, 7, 8 - extract ALL of them
10. Do NOT skip sections 4, 5, 6 - they come BEFORE section 7!

FORMAT: Output plain text with numbers and dots only (1, 1.1, 1.1.1, 1.1.1.1).
NO bullets (-), NO asterisks (*), NO markdown (**).

CONTENT (from page 15, STARTING WITH SECTION 4.01 PROOF):
{content_text[:120000]}"""
        
        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if AI_PROVIDER == "openai":
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=16000,
                        temperature=0,
                        timeout=240
                    )
                    ai_output = response.choices[0].message.content
                else:
                    response = claude.messages.create(
                        model="claude-3-5-haiku-20241022",
                        max_tokens=8192,
                        messages=[{"role": "user", "content": prompt}],
                        timeout=240
                    )
                    ai_output = response.content[0].text
                
                # Save AI output
                ai_file = self.debug_dir / "H245-ai-output.txt"
                ai_file.write_text(ai_output, encoding='utf-8')
                print(f"[DEBUG] Saved to {ai_file.name}")
                
                return self._parse_hierarchy(ai_output)
                
            except Exception as e:
                print(f"[WARN] Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"[INFO] Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"[ERROR] All {max_retries} attempts failed")
                    import traceback
                    traceback.print_exc()
                    return []
        
        return []
    
    def _parse_hierarchy(self, text: str) -> List[Dict]:
        """Parse AI numbered output."""
        all_topics = []
        parent_stack = {-1: None}
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Match hierarchical numbers
            match = re.match(r'^([\d.]+)\s+(.+)$', line)
            if not match:
                continue
            
            number = match.group(1).rstrip('.')
            title = match.group(2).strip()
            
            # Clean title
            title = title.lstrip('*☐✓□■●○-').strip()
            
            # Skip very short titles
            if len(title) < 2:
                continue
            
            dots = number.count('.')
            level = dots
            
            # Generate code
            code = f"H245_{number.replace('.', '_')}"
            parent_code = parent_stack.get(level - 1)
            
            all_topics.append({
                'code': code,
                'title': title,
                'level': level,
                'parent': parent_code
            })
            
            parent_stack[level] = code
            # Clear deeper levels
            for l in list(parent_stack.keys()):
                if l > level:
                    del parent_stack[l]
        
        return all_topics
    
    def _upload_all(self, topics: List[Dict]) -> bool:
        """Upload all topics to Supabase."""
        
        try:
            # Clear old topics NOW (after successful extraction)
            print("\n[INFO] Clearing old Further Mathematics A topics...")
            try:
                temp_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', 'H245').eq('qualification_type', 'A-Level').eq('exam_board', 'OCR').execute()
                if temp_result.data:
                    temp_id = temp_result.data[0]['id']
                    supabase.table('staging_aqa_topics').delete().eq('subject_id', temp_id).execute()
                    print(f"[OK] Cleared old topics for H245")
            except Exception as e:
                print(f"[WARN] Could not clear old topics: {e}")
            
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': "Further Mathematics A (A-Level)",
                'subject_code': 'H245',
                'qualification_type': 'A-Level',
                'specification_url': PDF_URL,
                'exam_board': 'OCR'
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            subject_id = subject_result.data[0]['id']
            print(f"[OK] Subject ID: {subject_id}")
            
            # Insert topics
            to_insert = [{
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': t['title'],
                'topic_level': t['level'],
                'exam_board': 'OCR'
            } for t in topics]
            
            inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
            print(f"[OK] Uploaded {len(inserted.data)} topics")
            
            # Link hierarchy
            code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
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
            print(f"[ERROR] Upload failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    scraper = FurtherMathsAScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

