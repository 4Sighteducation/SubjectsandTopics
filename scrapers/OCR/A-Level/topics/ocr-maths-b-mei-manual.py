"""
OCR A-Level Mathematics B (MEI) Manual Structure Scraper
=========================================================

Extracts topics from OCR Mathematics B (MEI) H640 specification.

Structure:
- Level 0: Areas (Pure mathematics, Mechanics, Statistics)
- Level 1: Main topics (Proof, Algebra, Functions, etc.)
- Level 2: Subsections (PROOF (1), PROOF (2), ALGEBRA (1), etc.)
- Level 3: Specification items (Algebraic language, Solution of equations, etc.)
- Level 4: Individual ref codes (Mp1, p2, Ma1, Ma2, a3, a4, etc.)

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-maths-b-mei-manual.py
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

# AI provider - use OpenAI like the working scrapers
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

PDF_URL = 'https://www.ocr.org.uk/Images/308740-specification-accredited-a-level-gce-mathematics-b-mei-h640.pdf'


class MathsBMEIScraper:
    """Scraper for OCR A-Level Mathematics B (MEI)."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_pages = []
    
    def scrape_all(self):
        """Scrape all topics."""
        print("\n" + "📊 "*40)
        print("OCR MATHEMATICS B (MEI) SCRAPER")
        print("📊 "*40)
        
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
        
        # Debug: Save snippet from relevant pages
        debug_file = self.debug_dir / "H640-pdf-snippet.txt"
        if len(self.pdf_pages) >= 25:
            snippet = "\n=== PAGE 23 ===\n" + self.pdf_pages[22] + "\n=== PAGE 24 ===\n" + self.pdf_pages[23]
            debug_file.write_text(snippet, encoding='utf-8')
            print(f"[DEBUG] Saved PDF snippet to {debug_file.name}")
        
        # Get content from content tables (likely starts around page 20-25)
        content_pages = self.pdf_pages[20:]  # Start from page 21
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
        
        prompt = f"""You must extract the COMPLETE hierarchy from OCR Mathematics B (MEI) H640 specification.

CRITICAL: Extract EVERYTHING you can see in the content below. Do NOT stop partway. Do NOT ask "Would you like me to continue?" - just extract ALL topics visible in the content. Do NOT ask for confirmation. Do NOT ask questions. Extract EVERYTHING NOW.

OUTPUT FORMAT: Use ONLY numbered format (1, 1.1, 1.1.1, 1.1.1.1, 1.1.1.1.1) - NO bullets, NO markdown.

DOCUMENT STRUCTURE:
The content has tables with columns: Specification | Ref | Learning outcomes | Notes | Notation | Exclusions

The red headers indicate subsections like "PURE MATHEMATICS: PROOF (1)" and "PURE MATHEMATICS: PROOF (2)"

STRUCTURE (5 levels):

Level 0: Areas (3 total)
  1 Area 1: Pure mathematics
  2 Area 2: Mechanics
  3 Area 3: Statistics

Level 1: Main topics under each area
  Under Area 1: Proof, Algebra, Functions, Graphs, Coordinate geometry, Sequences and series, Trigonometry, Exponentials and logarithms, Calculus, Numerical methods, Vectors
  Under Area 2: Models and quantities, Kinematics in one dimension, Kinematics in two dimensions, Projectiles, Forces, Newton's laws of motion, Rigid bodies
  Under Area 3: Statistical sampling, Data presentation and interpretation, Probability, Probability distributions, Statistical hypothesis testing

Level 2: Subsections (from red headers in tables)
  Examples: "PROOF (1)", "PROOF (2)", "ALGEBRA (1)", etc.
  Note: Not all topics have numbered subsections - if there's no (1), (2), then just use the topic name

Level 3: Specification items (from "Specification" column)
  Examples: "Proof", "Algebraic language", "Solution of equations"

Level 4: Individual ref codes (from "Ref" column)
  Examples: Mp1, p2, p3, Ma1, Ma2, a3, a4, a5, etc.
  Some refs are marked with "*" instead of a code - still extract these as separate items
  Content comes from "Learning outcomes" column

EXAMPLE OUTPUT:
1 Area 1: Pure mathematics
1.1 Proof
1.1.1 PROOF (1)
1.1.1.1 Proof
1.1.1.1.1 Mp1 Understand and be able to use the structure of mathematical proof. Use methods of proof, including proof by deduction and proof by exhaustion.
1.1.1.1.2 p2 Be able to disprove a conjecture by the use of a counter example.
1.1.2 PROOF (2)
1.1.2.1 Proof
1.1.2.1.1 p3 Understand and be able to use proof by contradiction. Including proof of the irrationality of √2 and the infinity of primes...
1.2 Algebra
1.2.1 ALGEBRA (1)
1.2.1.1 Algebraic language
1.2.1.1.1 Ma1 Know and be able to use vocabulary and notation appropriate to the subject at this level.
1.2.1.2 Solution of equations
1.2.1.2.1 * Be able to solve linear equations in one unknown.
1.2.1.2.2 * Be able to change the subject of a formula.
1.2.1.2.3 Ma2 Be able to solve quadratic equations.
1.2.1.2.4 a3 Be able to find the discriminant of a quadratic function and understand its significance.
1.2.1.2.5 a4 Be able to solve linear simultaneous equations in two unknowns.
1.2.1.2.6 a5 Be able to solve simultaneous equations in two unknowns with one equation linear and one quadratic.
(continue for ALL topics...)
2 Area 2: Mechanics
2.1 Models and quantities
(continue...)
3 Area 3: Statistics
3.1 Statistical sampling
(continue...)

CRITICAL EXTRACTION RULES:
1. Extract ALL 3 Level 0 areas
2. Extract ALL Level 1 main topics under each area
3. Extract ALL Level 2 subsections (PROOF (1), PROOF (2), ALGEBRA (1), etc.) - if a topic has no numbered subsections, skip L2 and go straight to L3
4. Extract ALL Level 3 specification items from the "Specification" column
5. Extract EVERY Level 4 ref code from the "Ref" column (Mp1, p2, Ma1, Ma2, a3, a4, a5, *, etc.)
6. IGNORE explanatory notes/examples in boxes that don't have ref codes - these are just clarifications, not learning outcomes
7. Items marked with "*" in the Ref column are still separate L4 items
8. Content for L4 comes from the "Learning outcomes" column
9. Only extract items that have an actual ref code in the Ref column
10. Some topics may only have 1-2 ref codes, others may have many - extract them ALL

FORMAT: Output plain text with numbers and dots only (1, 1.1, 1.1.1, 1.1.1.1, 1.1.1.1.1).
NO bullets (-), NO asterisks (*) at start of lines, NO markdown (**).

CONTENT:
{content_text[:100000]}"""
        
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
                ai_file = self.debug_dir / "H640-ai-output.txt"
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
            
            # Match hierarchical numbers (up to 5 levels: 1.1.1.1.1)
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
            code = f"H640_{number.replace('.', '_')}"
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
            print("\n[INFO] Clearing old Mathematics B (MEI) topics...")
            try:
                temp_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', 'H640').eq('qualification_type', 'A-Level').eq('exam_board', 'OCR').execute()
                if temp_result.data:
                    temp_id = temp_result.data[0]['id']
                    supabase.table('staging_aqa_topics').delete().eq('subject_id', temp_id).execute()
                    print(f"[OK] Cleared old topics for H640")
            except Exception as e:
                print(f"[WARN] Could not clear old topics: {e}")
            
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': "Mathematics B (MEI) (A-Level)",
                'subject_code': 'H640',
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
    scraper = MathsBMEIScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

