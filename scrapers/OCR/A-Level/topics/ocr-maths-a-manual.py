"""
OCR A-Level Mathematics A Manual Structure Scraper
===================================================

Extracts topics from OCR Mathematics A H240 specification.

Structure:
- Level 0: Main categories (Pure Mathematics, Statistics, Mechanics)
- Level 1: Topics (e.g., 1.01 Proof, 1.02 Algebra and functions)
- Level 2: Subject Content headings (e.g., Indices, Surds, Proof)
- Level 3: OCR Ref items (e.g., 1.02a, 1.02b, 1.02c) combining Stage 1 & Stage 2

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-maths-a-manual.py
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

# AI provider - use OpenAI like PE scraper (which works perfectly)
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

PDF_URL = 'https://www.ocr.org.uk/Images/308723-specification-accredited-a-level-gce-mathematics-a-h240.pdf'

# 3 main categories with their topics
CATEGORIES = [
    {
        'name': 'Pure Mathematics',
        'number': '1',
        'topics': [
            '1.01 Proof',
            '1.02 Algebra and functions',
            '1.03 Coordinate geometry in the x-y plane',
            '1.04 Sequences and series',
            '1.05 Trigonometry',
            '1.06 Exponentials and logarithms',
            '1.07 Differentiation',
            '1.08 Integration',
            '1.09 Numerical methods',
            '1.10 Vectors'
        ]
    },
    {
        'name': 'Statistics',
        'number': '2',
        'topics': [
            '2.01 Statistical sampling',
            '2.02 Data presentation and interpretation',
            '2.03 Probability',
            '2.04 Statistical distributions',
            '2.05 Statistical hypothesis testing'
        ]
    },
    {
        'name': 'Mechanics',
        'number': '3',
        'topics': [
            '3.01 Quantities and units in mechanics',
            '3.02 Kinematics',
            '3.03 Forces and Newton\'s laws',
            '3.04 Moments'
        ]
    }
]


class MathsAScraper:
    """Scraper for OCR A-Level Mathematics A."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_pages = []
    
    def scrape_all(self):
        """Scrape all 3 categories."""
        print("\n" + "📐 "*40)
        print("OCR MATHEMATICS A SCRAPER")
        print("📐 "*40)
        
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
        
        # Debug: Save snippet from page 20
        debug_file = self.debug_dir / "H240-pdf-snippet.txt"
        if len(self.pdf_pages) >= 22:
            snippet = "\n=== PAGE 20 ===\n" + self.pdf_pages[19] + "\n=== PAGE 21 ===\n" + self.pdf_pages[20]
            debug_file.write_text(snippet, encoding='utf-8')
            print(f"[DEBUG] Saved PDF snippet to {debug_file.name}")
        
        # Get content from page 20 onwards (DON'T delete old topics until we successfully scrape new ones)
        content_pages = self.pdf_pages[19:]  # Start from page 20 (0-indexed)
        content_text = "\n".join(content_pages)
        
        # Extract all topics in one go
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
        
        # Build category/topic structure
        structure_desc = ""
        for cat in CATEGORIES:
            structure_desc += f"\n{cat['number']}. {cat['name']}:\n"
            for topic in cat['topics']:
                structure_desc += f"  - {topic}\n"
        
        prompt = f"""You must extract the COMPLETE hierarchy from OCR Mathematics A (H240) specification starting from page 20.

CRITICAL: Extract EVERYTHING you can see in the content below. Do NOT stop partway. Do NOT ask "Would you like me to continue?" - just extract ALL topics visible in the content. Do NOT ask for confirmation. Do NOT ask questions. Extract EVERYTHING NOW.

OUTPUT FORMAT: Use ONLY numbered format (1, 1.1, 1.1.1, 1.1.1.1) - NO bullets, NO markdown.

STRUCTURE (4 levels):

Level 0: Main categories (3 total)
  1 Pure Mathematics
  2 Statistics
  3 Mechanics

Level 1: Numbered topics under each category:
{structure_desc}

Level 2: Subject Content headings
  - These appear in the "Subject/Content" column in tables
  - Examples from the PDF:
    * Under "1.01 Proof": the heading is "Proof" (same as Level 1)
    * Under "1.02 Algebra and functions": headings are "Indices", "Surds", "Simultaneous equations", "Quadratic functions", "Inequalities"

Level 3: OCR Ref items with letter codes
  - Format: [OCR Ref code] + [combined Stage 1 & Stage 2 content]
  - Examples: "1.01a", "1.01b", "1.01c", "1.01d", "1.02a", "1.02b", "1.02c", "1.02d", "1.02e", "1.02f", "1.02g", "1.02h"
  - CRITICAL: Letter codes (a, b, c, d, e, f, g, h...) may NOT be sequential! Extract ALL letters you find
  - Each letter code represents ONE Level 3 item
  - Combine both "Stage 1" AND "Stage 2" columns into single description

EXAMPLE OUTPUT:
1 Pure Mathematics
1.1 1.01 Proof
1.1.1 Proof
1.1.1.1 1.01a Understand and be able to use the structure of mathematical proof, proceeding from given assumptions through a series of logical steps to a conclusion. In particular, learners should use methods of proof including proof by deduction and proof by exhaustion.
1.1.1.2 1.01b Understand and be able to use the logical connectives ⇒, ⇔. Learners should be familiar with the language associated with the logical connectives.
1.1.1.3 1.01c Be able to show disproof by counter example.
1.1.1.4 1.01d Understand and be able to use proof by contradiction.
1.2 1.02 Algebra and functions
1.2.1 Indices
1.2.1.1 1.02a Understand and be able to use the laws of indices for all rational exponents. Includes negative and zero indices.
1.2.2 Surds
1.2.2.1 1.02b Be able to use and manipulate surds, including rationalising the denominator.
1.2.3 Simultaneous equations
1.2.3.1 1.02c Be able to solve simultaneous equations in two variables by elimination and by substitution.
1.2.4 Quadratic functions
1.2.4.1 1.02d Be able to work with quadratic functions and their graphs, and the discriminant.
1.2.4.2 1.02e Be able to complete the square of the quadratic polynomial.
1.2.4.3 1.02f Be able to solve quadratic equations.
1.2.5 Inequalities
1.2.5.1 1.02g Be able to solve linear and quadratic inequalities in a single variable.
1.2.5.2 1.02h Be able to express solutions through correct use of 'and' and 'or'.
1.3 1.03 Coordinate geometry in the x-y plane
(continue for all topics...)
2 Statistics
2.1 2.01 Statistical sampling
(continue...)
3 Mechanics
3.1 3.01 Quantities and units in mechanics
(continue...)

CRITICAL EXTRACTION RULES:
1. Extract ALL 3 Level 0 categories
2. Extract ALL Level 1 topics (numbered like 1.01, 1.02, etc.)
3. For each Level 1 topic, extract ALL Level 2 Subject Content headings
4. For each Level 2 heading, extract EVERY OCR Ref item (1.01a, 1.01b, 1.02a, 1.02b, 1.02c, etc.)
5. IMPORTANT: Letters may skip (e.g., you might see 1.02d, 1.02e, 1.02f under one heading, then 1.02g, 1.02h under the next)
6. Extract ALL letter codes you find - don't assume sequential lettering
7. Combine Stage 1 and Stage 2 text for each Level 3 item
8. Keep OCR Ref code as part of Level 3 title
9. When a topic appears as both Level 1 and Level 2 (like "Proof"), include it at both levels

FORMAT: Output plain text with numbers and dots only (1, 1.1, 1.1.1, 1.1.1.1).
NO bullets (-), NO asterisks (*), NO markdown (**).

CONTENT (from page 20):
{content_text[:80000]}"""
        
        # Retry logic - simple and clean
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if AI_PROVIDER == "openai":
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=16000,
                        temperature=0,
                        timeout=240  # Increased to 4 minutes
                    )
                    ai_output = response.choices[0].message.content
                else:  # anthropic
                    response = claude.messages.create(
                        model="claude-3-5-haiku-20241022",
                        max_tokens=8192,
                        messages=[{"role": "user", "content": prompt}],
                        timeout=240  # Increased to 4 minutes
                    )
                    ai_output = response.content[0].text
                
                # Save AI output
                ai_file = self.debug_dir / "H240-ai-output.txt"
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
            code = f"H240_{number.replace('.', '_')}"
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
            print("\n[INFO] Clearing old Mathematics A topics...")
            try:
                temp_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', 'H240').eq('qualification_type', 'A-Level').eq('exam_board', 'OCR').execute()
                if temp_result.data:
                    temp_id = temp_result.data[0]['id']
                    supabase.table('staging_aqa_topics').delete().eq('subject_id', temp_id).execute()
                    print(f"[OK] Cleared old topics for H240")
            except Exception as e:
                print(f"[WARN] Could not clear old topics: {e}")
            
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': "Mathematics A (A-Level)",
                'subject_code': 'H240',
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
    scraper = MathsAScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
