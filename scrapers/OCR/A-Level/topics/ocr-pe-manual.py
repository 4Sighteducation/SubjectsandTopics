"""
OCR A-Level Physical Education Manual Structure Scraper
========================================================

Extracts topics from OCR Physical Education H555 specification.

Structure:
- Level 0: Components (3 total)
- Level 1: Main topics (e.g., 1.1.a, 1.2.a)
- Level 2: Topic Area headings
- Level 3: Solid bullet points
- Level 4: Open circle bullets (sub-bullets)

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-pe-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/234833-specification-accredited-a-level-gce-physical-education-h555.pdf'

# 3 components
COMPONENTS = [
    {
        'name': 'Physiological factors affecting performance',
        'code': 'H555_01',
        'section_pattern': r'Content\s+of\s+Physiological\s+factors\s+affecting\s+performance.*?\(H555/?01\)'
    },
    {
        'name': 'Psychological factors affecting performance',
        'code': 'H555_02',
        'section_pattern': r'Content\s+of\s+Psychological\s+factors\s+affecting\s+performance.*?\(H555/?02\)'
    },
    {
        'name': 'Socio-cultural issues in physical activity and sport',
        'code': 'H555_03',
        'section_pattern': r'Content\s+of\s+Socio-cultural\s+issues.*?\(H555/?03\)'
    }
]


class PEScraper:
    """Scraper for OCR A-Level Physical Education."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_text = None
    
    def scrape_all(self):
        """Scrape all 3 components."""
        print("\n" + "🏃 "*40)
        print("OCR PHYSICAL EDUCATION SCRAPER")
        print("🏃 "*40)
        
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
        self.pdf_text = self._extract_pdf_text(pdf_content)
        if not self.pdf_text:
            return False
        
        # Debug: Save snippet of PDF text to check component 1
        debug_file = self.debug_dir / "H555-pdf-snippet.txt"
        # Find area around "Physiological"
        idx = self.pdf_text.lower().find('physiological factors affecting performance')
        if idx > 0:
            snippet = self.pdf_text[max(0, idx-200):idx+500]
            debug_file.write_text(snippet, encoding='utf-8')
            print(f"[DEBUG] Saved PDF snippet to {debug_file.name}")
        
        # Don't clear topics yet - wait until successful extraction
        
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
    
    def _extract_pdf_text(self, pdf_content: bytes) -> Optional[str]:
        """Extract text from PDF."""
        try:
            import pdfplumber
            from io import BytesIO
            
            print("[INFO] Extracting PDF text...")
            text = ""
            with pdfplumber.open(BytesIO(pdf_content)) as pdf:
                for i, page in enumerate(pdf.pages):
                    if page.extract_text():
                        text += page.extract_text() + "\n"
                    if i % 20 == 0 and i > 0:
                        print(f"[INFO] Processed {i+1}/{len(pdf.pages)} pages...")
            
            print(f"[OK] Extracted {len(text)} characters")
            return text
        except Exception as e:
            print(f"[ERROR] PDF extraction failed: {e}")
            return None
    
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
        
        pattern = component['section_pattern']
        matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE | re.DOTALL))
        
        if not matches:
            # Debug: Try finding with slash instead of underscore
            code_with_slash = component['code'].replace('_', '/')
            debug_pattern = rf'Content of.*?\({code_with_slash}\)'
            debug_matches = list(re.finditer(debug_pattern, self.pdf_text, re.IGNORECASE | re.DOTALL))
            if debug_matches:
                print(f"[DEBUG] Found with fallback pattern: {debug_pattern}")
                matches = debug_matches
            else:
                print(f"[DEBUG] Pattern not found: {pattern}")
                print(f"[DEBUG] Also tried: {debug_pattern}")
                return None
        
        if not matches:
            return None
        
        # Skip TOC matches - only use matches after position 10000 (past the TOC)
        valid_matches = [m for m in matches if m.start() > 10000]
        
        # If no valid matches, try all matches and take the longest
        if not valid_matches:
            valid_matches = matches
        
        # Take the longest match
        best_section = None
        best_length = 0
        
        for match in valid_matches:
            start = match.start()
            # Find end: next section or end marker
            end_patterns = [r'\n2[cdef]\.\s+Content of', r'\n3\s+Assessment', r'\nVersion \d+\.\d+']
            end_pos = len(self.pdf_text)
            for ep in end_patterns:
                end_match = re.search(ep, self.pdf_text[start+1000:start+40000])
                if end_match:
                    end_pos = start + 1000 + end_match.start()
                    break
            
            section = self.pdf_text[start:end_pos]
            if len(section) > best_length:
                best_length = len(section)
                best_section = section
        
        return best_section if best_length > 2000 else None
    
    def _extract_topics(self, component: Dict, section_text: str) -> List[Dict]:
        """Extract topics using AI."""
        
        prompt = f"""Extract the complete hierarchy from this OCR Physical Education component.

COMPONENT: {component['name']} ({component['code']})

PDF TABLE STRUCTURE:
- Tables have two columns: "Topic Area" and "Content"
- Topic Area column: Contains heading text (not labeled, just plain text) = Level 2
- Content column: Contains bullet points with two types:
  * Solid bullets (●) = Level 3
  * Open circle bullets (○) under solid bullets = Level 4

STRUCTURE (5 levels):
- Level 0: Component name
- Level 1: Main topics (e.g., "1.1.a. Skeletal and muscular systems")
- Level 2: Topic Area headings (e.g., "Joints, movements and muscles")
- Level 3: Solid bullet points (e.g., "shoulder:")
- Level 4: Open circle sub-bullets (e.g., "flexion, extension, abduction...")

OUTPUT FORMAT:
1 {component['name']}
1.1 1.1.a. Skeletal and muscular systems
1.1.1 Joints, movements and muscles
1.1.1.1 shoulder:
1.1.1.1.1 flexion, extension, abduction, adduction, horizontal flexion/abduction
1.1.1.1.2 extension, medial and lateral rotation, circumduction
1.1.1.1.3 deltoid, latissimus dorsi, pectoralis major, trapezius, teres minor
1.1.1.2 elbow:
1.1.1.2.1 flexion, extension
1.1.1.2.2 biceps brachii, triceps brachii
1.1.1.3 wrist:
1.1.1.3.1 flexion, extension
1.1.1.3.2 wrist flexors, wrist extensors
1.1.2 [Next Topic Area from table]
1.2 1.1.b. [Next main topic]
(continue...)

CRITICAL RULES:
- Extract ALL main topics from this component
- Extract ALL Topic Area headings from tables (remove any leading asterisks *)
- Extract ALL solid bullet points as Level 3
- Extract ALL open circle sub-bullets as Level 4
- Maintain complete hierarchy
- Ignore icons/images in the PDF
- Remove leading asterisks (*) from topic names

SECTION TEXT:
{section_text[:25000]}"""
        
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
            
            # Remove leading asterisks (used as markers in some topic areas)
            title = title.lstrip('*').strip()
            
            # Skip short titles
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
            for l in list(parent_stack.keys()):
                if l > level:
                    del parent_stack[l]
        
        return all_topics
    
    def _upload_component(self, component: Dict, topics: List[Dict]) -> bool:
        """Upload one component to Supabase."""
        
        try:
            # Upsert subject (ONE subject for all components)
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': "Physical Education (A-Level)",
                'subject_code': 'H555',
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
            return False


def main():
    scraper = PEScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

