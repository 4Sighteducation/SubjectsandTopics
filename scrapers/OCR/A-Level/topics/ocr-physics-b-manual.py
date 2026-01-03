"""
OCR A-Level Physics B (Advancing Physics) Manual Structure Scraper
==================================================================

Extracts topics from OCR Physics B (Advancing Physics) H157/H557 specification.

Structure:
- Level 0: Modules (6 total)
- Level 1: Topics (displayed as H2 headings)
- Level 2: Child topics of L1 (labeled as children)
- Level 3: Under "learning outcomes" heading, usually bold with no letter/numbering bullet points
- Level 4: Lettered/numbered list below Level 3

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-physics-b-manual.py
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

# AI provider
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

PDF_URL = 'https://www.ocr.org.uk/Images/171729-specification-accredited-a-level-gce-physics-b-advancing-physics-h557.pdf'

# 6 modules with their key topics
MODULES = [
    {
        'name': 'Module 1: Development of practical skills in physics',
        'number': '1',
        'topics': [
            'Practical skills assessed in a written examination',
            'Practical skills assessed in the practical endorsement'
        ]
    },
    {
        'name': 'Module 2: Fundamental data analysis',
        'number': '2',
        'topics': []
    },
    {
        'name': 'Module 3: Physics in action',
        'number': '3',
        'topics': [
            'Imaging and signalling',
            'Sensing',
            'Mechanical properties of materials'
        ]
    },
    {
        'name': 'Module 4: Understanding processes',
        'number': '4',
        'topics': [
            'Waves and quantum behaviour',
            'Space, time and motion'
        ]
    },
    {
        'name': 'Module 5: Rise and fall of the clockwork universe',
        'number': '5',
        'topics': [
            'Creating models',
            'Out into space',
            'Our place in the universe',
            'Matter: very simple',
            'Matter: hot and cold'
        ]
    },
    {
        'name': 'Module 6: Field and particle',
        'number': '6',
        'topics': [
            'Electromagnetism',
            'Charge and field',
            'Probing deep into matter',
            'Ionising radiation and risk'
        ]
    }
]


class PhysicsBScraper:
    """Scraper for OCR A-Level Physics B (Advancing Physics)."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_pages = []
    
    def scrape_all(self):
        """Scrape all modules."""
        print("\n" + "⚛️ "*40)
        print("OCR PHYSICS B (ADVANCING PHYSICS) SCRAPER")
        print("⚛️ "*40)
        
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
        
        # Find where content starts (after content overview)
        # Content overview provides Level 0 and Level 1 hierarchy
        # Then content starts with modules arranged in units
        content_start_page = self._find_content_start()
        if content_start_page is None:
            print("[WARN] Could not find content start, using page 20")
            content_start_page = 19  # 0-indexed, so page 20
        
        # Debug: Save snippet
        debug_file = self.debug_dir / "H557-pdf-snippet.txt"
        if len(self.pdf_pages) > content_start_page:
            snippet = f"\n=== PAGE {content_start_page + 1} ===\n" + self.pdf_pages[content_start_page]
            if len(self.pdf_pages) > content_start_page + 1:
                snippet += f"\n=== PAGE {content_start_page + 2} ===\n" + self.pdf_pages[content_start_page + 1]
            debug_file.write_text(snippet, encoding='utf-8')
            print(f"[DEBUG] Saved PDF snippet to {debug_file.name}")
        
        # Get content from content start page onwards
        content_pages = self.pdf_pages[content_start_page:]
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
    
    def _find_content_start(self) -> Optional[int]:
        """Find where the main content starts (after content overview)."""
        # Look for patterns like "Module 1" or "1.2 Practical skills"
        for i, page_text in enumerate(self.pdf_pages):
            # Look for module markers or practical skills section
            if re.search(r'Module\s+[1-6]|Practical\s+skills\s+assessed', page_text, re.IGNORECASE):
                # Make sure it's not in the TOC
                if i > 5:  # Skip first few pages (cover, TOC)
                    return i
        return None
    
    def _extract_all_topics(self, content_text: str) -> List[Dict]:
        """Extract all topics using AI."""
        
        # Build module structure description
        structure_desc = ""
        for module in MODULES:
            structure_desc += f"\n{module['number']}. {module['name']}"
            if module['topics']:
                for topic in module['topics']:
                    structure_desc += f"\n  - {topic}"
            structure_desc += "\n"
        
        prompt = f"""You must extract the COMPLETE hierarchy from OCR Physics B (Advancing Physics) H557 specification.

CRITICAL: Extract EVERYTHING you can see in the content below. Do NOT stop partway. Do NOT ask "Would you like me to continue?" - just extract ALL topics visible in the content. Do NOT ask for confirmation. Do NOT ask questions. Extract EVERYTHING NOW.

OUTPUT FORMAT: Use ONLY numbered format (1, 1.1, 1.1.1, 1.1.1.1, 1.1.1.1.1) - NO bullets, NO markdown.

STRUCTURE (5 levels):

Level 0: Modules (6 total)
{structure_desc}

Level 1: Topics (displayed as H2 headings in PDF)
  - These are the main topics under each module
  - Examples: "Practical skills assessed in a written examination", "Imaging and signalling", "Waves and quantum behaviour"
  - They appear as section headings (H2 style) in the PDF

Level 2: Child topics of Level 1
  - These are labeled as children/subtopics of the Level 1 topic
  - They appear as subsections under the Level 1 heading

Level 3: Under "Learning outcomes" heading
  - These appear under a "Learning outcomes" heading
  - Usually bold text with no letter/numbering bullet points
  - They are the main learning outcome statements

Level 4: Lettered/numbered list below Level 3
  - These are lettered (a, b, c) or numbered (1, 2, 3) items
  - They appear as sub-items under Level 3 learning outcomes
  - Extract ALL lettered/numbered items you find

EXAMPLE OUTPUT:
1 Module 1: Development of practical skills in physics
1.1 Practical skills assessed in a written examination
1.1.1 [Level 2 child topic if present]
1.1.1.1 [Level 3 learning outcome - bold, no letter/number]
1.1.1.1.1 a) [Level 4 lettered item]
1.1.1.1.2 b) [Level 4 lettered item]
1.1.1.2 [Next Level 3 learning outcome]
1.1.1.2.1 a) [Level 4 lettered item]
1.1.2 Practical skills assessed in the practical endorsement
1.1.2.1 [Level 2 child topic]
1.1.2.1.1 [Level 3 learning outcome]
1.1.2.1.1.1 a) [Level 4 item]
2 Module 2: Fundamental data analysis
2.1 [Level 1 topic - H2 heading]
2.1.1 [Level 2 child topic]
2.1.1.1 [Level 3 learning outcome]
2.1.1.1.1 a) [Level 4 item]
3 Module 3: Physics in action
3.1 Imaging and signalling
3.1.1 [Level 2 child topic]
3.1.1.1 [Level 3 learning outcome under "Learning outcomes"]
3.1.1.1.1 a) [Level 4 lettered item]
3.1.1.1.2 b) [Level 4 lettered item]
3.1.1.2 [Next Level 3 learning outcome]
3.1.1.2.1 a) [Level 4 item]
3.2 Sensing
(continue for all modules and topics...)

CRITICAL EXTRACTION RULES:
1. Extract ALL 6 Level 0 modules
2. Extract ALL Level 1 topics (H2 headings) under each module
3. Extract ALL Level 2 child topics (subsections under Level 1)
4. Extract ALL Level 3 learning outcomes (under "Learning outcomes" headings, usually bold)
5. Extract ALL Level 4 lettered/numbered items (a, b, c or 1, 2, 3) under Level 3
6. If a module has no Level 1 topics listed in the overview, extract them from the PDF content
7. Maintain complete hierarchy - every item must have a parent
8. If "Learning outcomes" heading appears, extract everything under it as Level 3
9. Level 4 items are always lettered (a, b, c) or numbered (1, 2, 3) sub-items

FORMAT: Output plain text with numbers and dots only (1, 1.1, 1.1.1, 1.1.1.1, 1.1.1.1.1).
NO bullets (-), NO asterisks (*), NO markdown (**).

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
                        timeout=240  # 4 minutes
                    )
                    ai_output = response.choices[0].message.content
                else:  # anthropic
                    response = claude.messages.create(
                        model="claude-3-5-haiku-20241022",
                        max_tokens=8192,
                        messages=[{"role": "user", "content": prompt}],
                        timeout=240  # 4 minutes
                    )
                    ai_output = response.content[0].text
                
                # Save AI output
                ai_file = self.debug_dir / "H557-ai-output.txt"
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
        
        # Headers to exclude from topics (these are just section markers)
        EXCLUDED_HEADERS = ['learning outcomes']
        
        # Track which levels were skipped so we can adjust child levels
        skipped_levels = set()
        
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
            original_level = dots
            
            # FILTER OUT: Skip "Learning outcomes" header (it's just a section marker)
            if title.lower() in EXCLUDED_HEADERS:
                print(f"[DEBUG] Skipped excluded header: {title}")
                # Mark this level as skipped
                skipped_levels.add(original_level)
                # Still update parent_stack so children can find grandparent
                # This allows children to skip this level and connect to grandparent
                parent_stack[original_level] = parent_stack.get(original_level - 1)
                for l in list(parent_stack.keys()):
                    if l > original_level:
                        del parent_stack[l]
                continue
            
            # Adjust level: count how many skipped levels are less than current level
            # and decrement by that count
            level = original_level
            skipped_count = sum(1 for sl in skipped_levels if sl < original_level)
            level -= skipped_count
            
            # Generate code
            code = f"H557_{number.replace('.', '_')}"
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
            print("\n[INFO] Clearing old Physics B topics...")
            try:
                temp_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', 'H557').eq('qualification_type', 'A-Level').eq('exam_board', 'OCR').execute()
                if temp_result.data:
                    temp_id = temp_result.data[0]['id']
                    supabase.table('staging_aqa_topics').delete().eq('subject_id', temp_id).execute()
                    print(f"[OK] Cleared old topics for H557")
            except Exception as e:
                print(f"[WARN] Could not clear old topics: {e}")
            
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': "Physics B (Advancing Physics) (A-Level)",
                'subject_code': 'H557',
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
    scraper = PhysicsBScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

