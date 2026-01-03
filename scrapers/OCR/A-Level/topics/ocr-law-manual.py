"""
OCR A-Level Law Manual Structure Scraper
=========================================

Extracts topics from OCR Law H418 specification.

Structure:
- Level 0: Components (4 total: H418/01, H418/02, H418/03, H418/04)
- Level 1: Sections (Section A, Section B)
- Level 2: Sub-topics (headings under Content column)
- Level 3: Square bullet points (☐) under Content
- Level 4: Tick bullet points (✓) under Guidance

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-law-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/587304-specification-accredited-a-level-gce-law-h418.pdf'

# 4 components (H418/03 and H418/04 are alternatives)
COMPONENTS = [
    {
        'name': 'The legal system and criminal law',
        'code': 'H418_01',
        'sections': ['Section A: The legal system', 'Section B: Criminal law'],
        'section_pattern': r'Content\s+of\s+H418/?01.*?The\s+legal\s+system\s+and\s+criminal\s+law',
        'start_page': 9
    },
    {
        'name': 'Law making and the law of tort',
        'code': 'H418_02',
        'sections': ['Section A: Law making', 'Section B: The law of tort'],
        'section_pattern': r'Content\s+of\s+H418/?02.*?Law\s+making\s+and\s+the\s+law\s+of\s+tort',
        'start_page': None  # To be determined
    },
    {
        'name': 'The nature of law and Human rights',
        'code': 'H418_03',
        'sections': ['Section A: The nature of law', 'Section B: Human rights law'],
        'section_pattern': r'Content\s+of\s+H418/?03.*?The\s+nature\s+of\s+law\s+and\s+Human\s+rights',
        'start_page': None  # To be determined
    },
    {
        'name': 'The nature of law and the law of contract',
        'code': 'H418_04',
        'sections': ['Section A: The nature of law', 'Section B: The law of contract'],
        'section_pattern': r'Content\s+of\s+H418/?04.*?The\s+nature\s+of\s+law\s+and\s+the\s+law\s+of\s+contract',
        'start_page': None  # To be determined
    }
]


class LawScraper:
    """Scraper for OCR A-Level Law."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_text = None
        self.pdf_pages = []  # Store page texts separately
    
    def scrape_all(self):
        """Scrape all 4 components."""
        print("\n" + "⚖️  "*40)
        print("OCR LAW SCRAPER")
        print("⚖️  "*40)
        
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
        
        # Extract PDF text
        self.pdf_text, self.pdf_pages = self._extract_pdf_text(pdf_content)
        if not self.pdf_text:
            return False
        
        # Debug: Save snippet of PDF text to check component 1
        debug_file = self.debug_dir / "H418-pdf-snippet.txt"
        idx = self.pdf_text.lower().find('content of h418/01')
        if idx > 0:
            snippet = self.pdf_text[max(0, idx-200):idx+800]
            debug_file.write_text(snippet, encoding='utf-8')
            print(f"[DEBUG] Saved PDF snippet to {debug_file.name}")
        
        # Clear old topics ONCE
        print("\n[INFO] Clearing old Law topics...")
        try:
            subject_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', 'H418').eq('qualification_type', 'A-Level').eq('exam_board', 'OCR').execute()
            if subject_result.data:
                subject_id = subject_result.data[0]['id']
                supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
                print(f"[OK] Cleared old topics for H418")
        except Exception as e:
            print(f"[WARN] Could not clear old topics: {e}")
        
        # Process each component
        success_count = 0
        for component in COMPONENTS:
            print("\n" + "="*80)
            print(f"Processing: {component['name']} ({component['code']})")
            print("="*80)
            
            if self._process_component(component):
                success_count += 1
            time.sleep(2)
        
        print("\n" + "="*80)
        print(f"✅ Completed: {success_count}/{len(COMPONENTS)} components successful")
        print("="*80)
        return success_count == len(COMPONENTS)
    
    def _extract_pdf_text(self, pdf_content: bytes) -> tuple[Optional[str], List[str]]:
        """Extract text from PDF, returning both full text and per-page text."""
        try:
            import pdfplumber
            from io import BytesIO
            
            print("[INFO] Extracting PDF text...")
            full_text = ""
            page_texts = []
            
            with pdfplumber.open(BytesIO(pdf_content)) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    page_texts.append(page_text)
                    full_text += page_text + "\n"
                    
                    if i % 20 == 0 and i > 0:
                        print(f"[INFO] Processed {i+1}/{len(pdf.pages)} pages...")
            
            print(f"[OK] Extracted {len(full_text)} characters from {len(page_texts)} pages")
            return full_text, page_texts
        except Exception as e:
            print(f"[ERROR] PDF extraction failed: {e}")
            return None, []
    
    def _process_component(self, component: Dict) -> bool:
        """Process one component."""
        
        # Find the section in PDF
        section_text = self._find_section(component)
        if not section_text:
            print(f"[WARN] Could not find section for {component['code']}")
            return False
        
        print(f"[DEBUG] Found section: {len(section_text)} chars")
        
        # Extract topics with AI
        topics = self._extract_topics(component, section_text)
        if not topics:
            print(f"[WARN] No topics extracted for {component['code']}")
            return False
        
        # Count by level
        level_counts = {}
        for t in topics:
            level_counts[t['level']] = level_counts.get(t['level'], 0) + 1
        level_str = ", ".join([f"L{k}:{v}" for k, v in sorted(level_counts.items())])
        print(f"[OK] Extracted {len(topics)} topics ({level_str})")
        
        # Upload
        return self._upload_component(component, topics)
    
    def _find_section(self, component: Dict) -> Optional[str]:
        """Find the section for this component in the PDF."""
        
        # If start_page is provided, start from that page
        if component.get('start_page'):
            start_page = component['start_page'] - 1  # 0-indexed
            print(f"[DEBUG] Starting from page {component['start_page']}")
            search_text = "\n".join(self.pdf_pages[start_page:])
        else:
            search_text = self.pdf_text
        
        pattern = component['section_pattern']
        matches = list(re.finditer(pattern, search_text, re.IGNORECASE | re.DOTALL))
        
        if not matches:
            # Try with slash instead of underscore
            code_with_slash = component['code'].replace('_', '/')
            debug_pattern = rf'Content of {code_with_slash}'
            debug_matches = list(re.finditer(debug_pattern, search_text, re.IGNORECASE))
            if debug_matches:
                print(f"[DEBUG] Found with fallback pattern: {debug_pattern}")
                matches = debug_matches
            else:
                print(f"[DEBUG] Pattern not found: {pattern}")
                print(f"[DEBUG] Also tried: {debug_pattern}")
                return None
        
        if not matches:
            return None
        
        # Take the first match (should be after TOC since we're starting from page 9+)
        best_section = None
        best_length = 0
        
        for match in matches:
            start = match.start()
            # Find end: next component section or end marker
            end_patterns = [
                r'Content\s+of\s+H418/0[1-4]',  # Next component
                r'\n\d+\s+Assessment',  # Assessment section
                r'Version \d+\.\d+'  # Version footer
            ]
            end_pos = len(search_text)
            
            for ep in end_patterns:
                end_match = re.search(ep, search_text[start+500:start+40000])
                if end_match:
                    end_pos = start + 500 + end_match.start()
                    break
            
            section = search_text[start:end_pos]
            if len(section) > best_length:
                best_length = len(section)
                best_section = section
        
        return best_section if best_length > 1000 else None
    
    def _extract_topics(self, component: Dict, section_text: str) -> List[Dict]:
        """Extract topics using AI."""
        
        prompt = f"""Extract the complete hierarchy from this OCR Law component.

COMPONENT: {component['name']} ({component['code']})

PDF TABLE STRUCTURE:
The content is organized in tables with two columns: "Content" and "Guidance"

STRUCTURE (5 levels):
- Level 0: Component name (e.g., "The legal system and criminal law")
- Level 1: Section headings (e.g., "Section A: The legal system", "Section B: Criminal law")
- Level 2: Sub-topic headings that appear under the Content/Guidance column headers
  (e.g., "Civil courts and other forms of dispute resolution", "Criminal courts and lay people")
- Level 3: Square bullet points (☐) under the Content column
  (e.g., "County Court and High Court: jurisdictions, pre-trial procedures, the three tracks")
- Level 4: Tick bullet points (✓) under the Guidance column
  (e.g., "the jurisdictions of the County Court and the three divisions of the High Court")
  
CRITICAL: Level 4 items (tick bullets from Guidance column) must be intelligently assigned to the 
correct Level 3 parent based on their semantic relationship and position in the table.

OUTPUT FORMAT:
1 {component['name']}
1.1 Section A: The legal system
1.1.1 Civil courts and other forms of dispute resolution
1.1.1.1 County Court and High Court: jurisdictions, pre-trial procedures, the three tracks
1.1.1.1.1 the jurisdictions of the County Court and the three divisions of the High Court
1.1.1.1.2 grounds/reasons to appeal
1.1.1.1.3 First appeal from the three tracks, further appeal to the Court of Appeal (Civil Division)
1.1.1.2 Appeals and appellate courts
1.1.1.2.1 [guidance items for this content point]
1.1.1.3 Employment tribunals and Alternative Dispute Resolution
1.1.1.3.1 how employment tribunals work
1.1.1.3.2 negotiation, mediation, conciliation and arbitration
1.1.1.4 Advantages and disadvantages of using the civil courts and Alternative Dispute Resolution
1.1.2 Criminal courts and lay people
1.1.2.1 Criminal process: jurisdiction of the Magistrates' Court and the Crown Court...
1.1.2.1.1 summary offences, triable either-way offences, indictable offences...
1.1.2.2 [next content point]
1.1.2.2.1 [guidance for it]
1.2 Section B: Criminal law
1.2.1 [First sub-topic for Section B]
(continue...)

CRITICAL RULES:
1. Extract ALL sections from this component ({', '.join(component['sections'])})
2. Extract ALL sub-topic headings as Level 2
3. Extract ALL square bullet points (☐) from Content column as Level 3
4. Extract ALL tick bullet points (✓) from Guidance column as Level 4
5. Match Level 4 items to their correct Level 3 parent based on:
   - Position in the table (which Content row they align with)
   - Semantic meaning and relationship
6. Maintain complete hierarchy
7. Remove any asterisks (*) or special markers from topic names
8. Keep the full text of each item

SECTION TEXT:
{section_text[:55000]}"""
        
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
                        timeout=180
                    )
                    ai_output = response.choices[0].message.content
                else:
                    response = claude.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=16000,
                        messages=[{"role": "user", "content": prompt}],
                        timeout=180
                    )
                    ai_output = response.content[0].text
                
                # Save AI output
                safe_code = re.sub(r'[^\w\-]', '_', component['code'])
                ai_file = self.debug_dir / f"{safe_code}-ai-output.txt"
                ai_file.write_text(ai_output, encoding='utf-8')
                print(f"[DEBUG] Saved to {ai_file.name}")
                
                return self._parse_hierarchy(ai_output, component['code'])
                
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
    
    def _parse_hierarchy(self, text: str, component_code: str) -> List[Dict]:
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
            
            # Remove leading asterisks or special markers
            title = title.lstrip('*☐✓□■●○').strip()
            
            # Skip very short titles
            if len(title) < 2:
                continue
            
            dots = number.count('.')
            level = dots
            
            code = f"{component_code}_{number.replace('.', '_')}"
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
    
    def _upload_component(self, component: Dict, topics: List[Dict]) -> bool:
        """Upload one component to Supabase."""
        
        try:
            # Upsert subject (ONE subject for all components)
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': "Law (A-Level)",
                'subject_code': 'H418',
                'qualification_type': 'A-Level',
                'specification_url': PDF_URL,
                'exam_board': 'OCR'
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            subject_id = subject_result.data[0]['id']
            print(f"[OK] Subject ID: {subject_id}")
            
            # Insert topics (don't delete - already cleared at start)
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
    scraper = LawScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

