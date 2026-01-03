"""
OCR A-Level Geography Manual Structure Scraper
===============================================

Extracts topics from OCR Geography H481 specification.

Structure:
- Level 0: Components (Physical Systems, Human Interactions, Geographical Debates)
- Level 1: Main topics
- Level 2: Sub-topics/Options
- Level 3: Key Ideas (a, b, c)  (questions are NOT separate nodes)
- Level 4: Content bullets

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-geography-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/223012-specification-accredited-a-level-gce-geography-h481.pdf'

# 3 components
COMPONENTS = [
    {
        'name': 'Physical Systems',
        'code': 'H481_01',
        'full_name': 'Physical systems (01)',
        'section_pattern': r'2c\.\s+Content of Physical systems'
    },
    {
        'name': 'Human Interactions',
        'code': 'H481_02',
        'full_name': 'Human interactions (02)',
        'section_pattern': r'2c\.\s+Content of Human interactions'
    },
    {
        'name': 'Geographical Debates',
        'code': 'H481_03',
        'full_name': 'Geographical debates (03)',
        'section_pattern': r'2c\.\s+Content of Geographical debates'
    }
]


class GeographyScraper:
    """Scraper for OCR A-Level Geography."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_text = None

    def _clear_old_topics_batched(self, subject_id: str, batch_size: int = 1000) -> int:
        """
        Clear old topics for a subject in small batches to avoid statement timeouts
        on large deletes.
        """
        total_deleted = 0
        while True:
            res = (
                supabase.table('staging_aqa_topics')
                .select('id')
                .eq('subject_id', subject_id)
                .limit(batch_size)
                .execute()
            )
            ids = [row['id'] for row in (res.data or []) if 'id' in row]
            if not ids:
                break

            supabase.table('staging_aqa_topics').delete().in_('id', ids).execute()
            total_deleted += len(ids)
            print(f"[INFO] Deleted {total_deleted} old topics so far...")
            time.sleep(0.2)

            # If we got fewer than the batch size, we likely cleared everything.
            if len(ids) < batch_size:
                break

        return total_deleted
    
    def scrape_all(self):
        """Scrape all 3 components."""
        print("\n" + "🗺️  "*40)
        print("OCR GEOGRAPHY SCRAPER")
        print("🗺️  "*40)
        
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
        
        # Clear old topics ONCE
        print("\n[INFO] Clearing old Geography topics...")
        try:
            subject_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', 'H481').eq('qualification_type', 'A-Level').eq('exam_board', 'OCR').execute()
            if subject_result.data:
                subject_id = subject_result.data[0]['id']
                deleted = self._clear_old_topics_batched(subject_id)
                print(f"[OK] Cleared {deleted} old topics for H481")
        except Exception as e:
            print(f"[WARN] Could not clear old topics: {e}")
        
        # Process each component
        success_count = 0
        for component in COMPONENTS:
            print("\n" + "="*80)
            print(f"Processing: {component['full_name']} ({component['code']})")
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
        matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE))
        
        if not matches:
            return None
        
        # Take the longest match (main content, not TOC)
        best_section = None
        best_length = 0
        
        for match in matches:
            start = match.start()
            # Find end: next major section or end marker
            end_patterns = [r'\n2[cd]\.\s+Content of', r'\n2[de]\.\s+', r'\nVersion \d+\.\d+']
            end_pos = len(self.pdf_text)
            for ep in end_patterns:
                end_match = re.search(ep, self.pdf_text[start+1000:start+50000])
                if end_match:
                    end_pos = start + 1000 + end_match.start()
                    break
            
            section = self.pdf_text[start:end_pos]
            if len(section) > best_length:
                best_length = len(section)
                best_section = section
        
        return best_section if best_length > 3000 else None
    
    def _extract_topics(self, component: Dict, section_text: str) -> List[Dict]:
        """Extract topics using AI."""
        
        prompt = f"""Extract the complete hierarchy from this OCR Geography specification section.

COMPONENT: {component['full_name']} ({component['code']})

STRUCTURE (5 levels - extract ALL):
- Level 0: Component name ("{component['name']}")
- Level 1: Main topics (e.g., "Landscape Systems", "Earth's Life Support Systems")
- Level 2: Sub-topics/Options (e.g., "1.1.1 Option A - Coastal Landscapes")
- Level 3: Key Ideas (e.g., "1.a. Coastal landscapes can be viewed as systems")
- Level 4: Content bullets (bullet points AFTER the colon in the Content column)

IMPORTANT:
- Do NOT create a separate node for the numbered question headings (e.g., "1. How can ...?").
  Those are structural prompts in the spec; go straight from the Option (Level 2) into the Key Ideas.

OUTPUT FORMAT:
1. {component['name']}
1.1 Landscape Systems
1.1.1 1.1.1 Option A - Coastal Landscapes
1.1.1.1 1.a. Coastal landscapes can be viewed as systems
1.1.1.1.1 the components of coastal landscape systems, including inputs, processes and outputs
1.1.1.1.2 the flows of energy and material through coastal systems
1.1.1.1.3 sediment cells
1.1.1.2 1.b. Coastal landscape systems are influenced by a range of physical factors
1.1.1.2.1 winds, including speed, direction and frequency
1.1.1.2.2 waves, including wave formation, development and breaking
1.1.1.2.3 tides, including tidal cycles and range
1.1.1.3 1.c. Coastal sediment is supplied from a variety of sources
(continue...)

CRITICAL RULES:
1. Start with "1. {component['name']}" (Level 0)
2. Extract ALL main topics as Level 1
3. Under each, extract sub-topics/options as Level 2
4. Under each sub-topic, extract "Key Ideas" (a., b., c.) as Level 3
5. Under each Key Idea, extract the bullet points from the Content column as Level 4
6. Level 4 bullets appear AFTER text like "A conceptual overview of:" or "Potential influences on..."
7. Extract ONLY the actual bullet points, not the introductory text before the colon

SECTION TEXT:
{section_text[:55000]}"""
        
        # Retry logic with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if AI_PROVIDER == "openai":
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=16000,
                        temperature=0,
                        timeout=120  # 2 minute timeout
                    )
                    ai_output = response.choices[0].message.content
                else:
                    response = claude.messages.create(
                        model="claude-3-5-haiku-20241022",
                        max_tokens=16000,
                        messages=[{"role": "user", "content": prompt}],
                        timeout=120
                    )
                    ai_output = response.content[0].text
                
                # Save AI output
                safe_code = re.sub(r'[^\w\-]', '_', component['code'])
                ai_file = self.debug_dir / f"{safe_code}-ai-output.txt"
                ai_file.write_text(ai_output, encoding='utf-8')
                print(f"[DEBUG] Saved AI output to {ai_file.name}")
                
                topics = self._parse_hierarchy(ai_output, component['code'])
                topics = self._collapse_question_nodes(topics)
                return topics
                
            except Exception as e:
                print(f"[WARN] Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
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
            
            # Match patterns like "1.1.1.1.1" or "1.a." or "1.1.1 Option A"
            match = re.match(r'^([\d.]+[a-z]?)[\.\):]?\s+(.+)$', line)
            if not match:
                continue
            
            number = match.group(1).rstrip('.')
            title = match.group(2).strip()
            
            # Skip short titles
            if len(title) < 3:
                continue
            
            # Count dots and letters for level
            dots = number.count('.')
            has_letter = bool(re.search(r'[a-z]$', number))
            
            if has_letter:
                level = dots + 1  # Letters are one level deeper
            else:
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

    def _collapse_question_nodes(self, topics: List[Dict]) -> List[Dict]:
        """
        Collapse numbered "question" headings (usually ending with '?') which are structural
        and over-complicate the tree in the app.

        Behavior:
        - Remove the question node
        - Promote its children to the question node's parent
        - Decrement topic_level by 1 for the promoted subtree

        We keep topic_code stable; only topic_level and parent linkage change.
        """
        if not topics:
            return topics

        by_code: Dict[str, Dict] = {t["code"]: dict(t) for t in topics}
        children: Dict[str, List[str]] = {}
        for t in topics:
            p = t.get("parent")
            if p:
                children.setdefault(p, []).append(t["code"])

        to_remove: set[str] = set()

        def dec_subtree_levels(root_code: str):
            stack = [root_code]
            while stack:
                c = stack.pop()
                node = by_code.get(c)
                if not node:
                    continue
                node["level"] = max(0, int(node.get("level", 0)) - 1)
                for ch in children.get(c, []):
                    stack.append(ch)

        for t in topics:
            code = t["code"]
            node = by_code.get(code)
            if not node:
                continue
            title = (node.get("title") or "").strip()
            if not title.endswith("?"):
                continue
            if code not in children or not children[code]:
                continue

            parent_code = node.get("parent")
            for child_code in children.get(code, []):
                child = by_code.get(child_code)
                if not child:
                    continue
                child["parent"] = parent_code
                dec_subtree_levels(child_code)

            to_remove.add(code)

        if not to_remove:
            return list(by_code.values())

        collapsed: List[Dict] = []
        for t in topics:
            if t["code"] in to_remove:
                continue
            collapsed.append(by_code[t["code"]])
        return collapsed
    
    def _upload_component(self, component: Dict, topics: List[Dict]) -> bool:
        """Upload one component to Supabase."""
        
        try:
            # Upsert subject (ONE subject for all components)
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': "Geography (A-Level)",
                'subject_code': 'H481',
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
    scraper = GeographyScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

