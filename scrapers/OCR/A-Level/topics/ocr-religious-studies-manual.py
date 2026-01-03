"""
OCR A-Level Religious Studies Manual Structure Scraper
========================================================

Extracts topics from OCR Religious Studies H573 specification.

Structure:
- Level 0: Components (01, 02, 03-07)
- Level 1: Main topics under each component
- Level 2: Topic headings from tables
- Level 3: Content column items (full and open bullet points)
- Level 4: Key Knowledge column items (adjacent to parent)
- Contextual References: Added as L2 children of L1 topics (bullet points only)

Component 01: Philosophy of religion
- Topics: Ancient philosophical influences, the nature of the soul/mind/body, Arguments about existence of God, Religious experience, Problem of evil, Nature of God, Religious language

Component 02: Religion and ethics
- Topics: Normative ethical theories, Application of ethical theory, Ethical language, Conscience, Sexual ethics

Component 03-07: Developments in religious thought
- Christianity (03), Islam (04), Judaism (05), Buddhism (06), Hinduism (07)
- Each has similar structure with religious beliefs, sources, practices, developments, themes

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-religious-studies-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/242913-specification-accredited-a-level-gce-religious-studies-h573.pdf'

# Components structure
COMPONENTS = [
    {
        'name': 'Component 01: Philosophy of religion',
        'code': 'H573_01',
        'short_name': 'Philosophy of religion',
        'section_pattern': r'2c\.\s+Content\s+of\s+Philosophy\s+of\s+religion'
    },
    {
        'name': 'Component 02: Religion and ethics',
        'code': 'H573_02',
        'short_name': 'Religion and ethics',
        'section_pattern': r'2c\.\s+Content\s+of\s+Religion\s+and\s+ethics'
    },
    {
        'name': 'Component 03: Developments in Christian thought',
        'code': 'H573_03',
        'short_name': 'Developments in Christian thought',
        'section_pattern': r'2c\.\s+Content\s+of\s+Developments\s+in\s+Christian\s+thought'
    },
    {
        'name': 'Component 04: Developments in Islamic thought',
        'code': 'H573_04',
        'short_name': 'Developments in Islamic thought',
        'section_pattern': r'2c\.\s+Content\s+of\s+Developments\s+in\s+Islamic\s+thought'
    },
    {
        'name': 'Component 05: Developments in Jewish thought',
        'code': 'H573_05',
        'short_name': 'Developments in Jewish thought',
        'section_pattern': r'2c\.\s+Content\s+of\s+Developments\s+in\s+Jewish\s+thought'
    },
    {
        'name': 'Component 06: Developments in Buddhist thought',
        'code': 'H573_06',
        'short_name': 'Developments in Buddhist thought',
        'section_pattern': r'2c\.\s+Content\s+of\s+Developments\s+in\s+Buddhist\s+thought'
    },
    {
        'name': 'Component 07: Developments in Hindu thought',
        'code': 'H573_07',
        'short_name': 'Developments in Hindu thought',
        'section_pattern': r'2c\.\s+Content\s+of\s+Developments\s+in\s+Hindu\s+thought'
    }
]


class ReligiousStudiesScraper:
    """Scraper for OCR A-Level Religious Studies."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_pages = []
        self.pdf_text = None
    
    def scrape_all(self):
        """Scrape all components."""
        print("\n" + "📿 "*40)
        print("OCR RELIGIOUS STUDIES SCRAPER")
        print("📿 "*40)
        
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
        self.pdf_pages = self._extract_pdf_pages(pdf_content)
        if not self.pdf_pages:
            return False
        
        # Combine all pages for full-text search
        self.pdf_text = "\n".join(self.pdf_pages)
        
        # Process each component
        all_topics = []
        for component in COMPONENTS:
            print("\n" + "="*80)
            print(f"Processing: {component['name']}")
            print("="*80)
            
            component_topics = self._process_component(component)
            if component_topics:
                all_topics.extend(component_topics)
                print(f"[OK] Extracted {len(component_topics)} topics for {component['code']}")
            else:
                print(f"[WARN] No topics extracted for {component['code']}")
            
            time.sleep(2)
        
        if not all_topics:
            print("[ERROR] No topics extracted at all")
            return False
        
        # Count by level
        level_counts = {}
        for t in all_topics:
            level_counts[t['level']] = level_counts.get(t['level'], 0) + 1
        level_str = ", ".join([f"L{k}:{v}" for k, v in sorted(level_counts.items())])
        print(f"\n[OK] Total extracted: {len(all_topics)} topics ({level_str})")
        
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
    
    def _process_component(self, component: Dict) -> List[Dict]:
        """Process one component."""
        
        # Find section
        section_text = self._find_section(component)
        if not section_text:
            print(f"[WARN] Could not find section for {component['code']}")
            return []
        
        print(f"[DEBUG] Found section: {len(section_text)} chars")
        
        # Save PDF snippet for debugging
        safe_code = re.sub(r'[^\w\-]', '_', component['code'])
        pdf_snippet_file = self.debug_dir / f"{safe_code}-pdf-snippet.txt"
        pdf_snippet_file.write_text(section_text[:5000], encoding='utf-8')
        print(f"[DEBUG] Saved PDF snippet to {pdf_snippet_file.name}")
        
        # Extract topics
        topics = self._extract_topics(component, section_text)
        return topics
    
    def _find_section(self, component: Dict) -> Optional[str]:
        """Find the section for this component in the PDF."""
        
        # Try multiple patterns
        patterns = [
            # Pattern from component config
            component.get('section_pattern', ''),
            # Alternative patterns
            rf'Content\s+of\s+{re.escape(component["short_name"])}',
            rf'{re.escape(component["short_name"])}\s*\(H573/0[1-7]\)',
            rf'2c\.\s+Content\s+of\s+{re.escape(component["short_name"])}',
            rf'Component\s+0[1-7]:\s+{re.escape(component["short_name"])}',
            # Just the short name
            rf'{re.escape(component["short_name"])}',
        ]
        
        for pattern in patterns:
            if not pattern:
                continue
            
            matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE | re.DOTALL))
            if matches:
                # Skip TOC matches - only use matches after position 5000
                valid_matches = [m for m in matches if m.start() > 5000]
                if not valid_matches:
                    valid_matches = matches
                
                if not valid_matches:
                    continue
                
                # Take the longest match (or first valid match if multiple)
                best_match = max(valid_matches, key=lambda m: len(self.pdf_text[m.start():m.start()+50000]))
                start = best_match.start()
                
                # Find end: next component section or end marker
                end_patterns = [
                    r'\n2c\.\s+Content\s+of\s+(Philosophy|Religion|Developments)',  # Next component
                    r'\nComponent\s+0[1-7]:',  # Next component
                    r'\n2d\.\s+Prior\s+knowledge',  # Next main section
                    r'\n3\.\s+Assessment',  # Assessment section
                    r'\nVersion\s+\d+\.\d+',  # Version marker
                    r'\nAppendix',  # Appendix
                ]
                end_pos = len(self.pdf_text)
                for ep in end_patterns:
                    end_match = re.search(ep, self.pdf_text[start+1000:start+200000])
                    if end_match:
                        end_pos = start + 1000 + end_match.start()
                        break
                
                section = self.pdf_text[start:end_pos]
                if len(section) > 500:
                    print(f"[DEBUG] Found section using pattern: {pattern[:50]}...")
                    return section
        
        # Debug: Try to find what's actually in the PDF
        print(f"[DEBUG] Could not find section: {component['short_name']}")
        # Look for any mention
        test_match = re.search(rf'{re.escape(component["short_name"][:20])}', self.pdf_text, re.IGNORECASE)
        if test_match:
            print(f"[DEBUG] Found mention of '{component['short_name'][:20]}' at position {test_match.start()}")
            context_start = max(0, test_match.start() - 200)
            context_end = min(len(self.pdf_text), test_match.start() + 200)
            print(f"[DEBUG] Context: ...{self.pdf_text[context_start:context_end]}...")
        
        return None
    
    def _extract_topics(self, component: Dict, section_text: str) -> List[Dict]:
        """Extract topics using AI."""
        
        # Component-specific Level 1 topic guidance
        level1_guidance = ""
        if component['code'] == 'H573_01':
            level1_guidance = """
EXPECTED Level 1 topics (but discover actual structure from PDF):
- 1. Philosophical Language and Thought
- 2. The Existence of God
- 3. Religious Experience (or similar)
- 4. The Problem of Evil (or similar)
- 5. The Nature of God (or similar)
- 6. Religious Language (or similar)
Note: Actual PDF structure may differ - extract what you see."""
        elif component['code'] == 'H573_02':
            level1_guidance = """
EXPECTED Level 1 topics (but discover actual structure from PDF):
- Normative ethical theories
- The application of ethical theory to contemporary issues
- Ethical language and thought
- Conscience
- Sexual ethics
Note: Actual PDF structure may differ - extract what you see."""
        else:
            level1_guidance = """
Level 1 topics will be main sections in the PDF. Discover them from the actual structure.
Common patterns: Religious beliefs, Sources of wisdom, Practices, Developments, Themes, Society, Challenges."""
        
        prompt = f"""You must extract the COMPLETE hierarchy from OCR Religious Studies {component['name']}.

CRITICAL: Extract EVERYTHING you can see. Do NOT stop partway. Do NOT ask questions. Extract EVERYTHING NOW.
OUTPUT FORMAT: Use ONLY numbered format (1, 1.1, 1.1.1) - NO bullets (-), NO asterisks (*), NO markdown (**), NO bold markers.
Do NOT use markdown formatting. Do NOT use bullets. Use ONLY numbers and dots.

COMPONENT: {component['name']}
{level1_guidance}

PDF TABLE STRUCTURE:
The content is organized in tables with three columns: "Topic", "Content", and "Key Knowledge"

STRUCTURE (5 levels):
- Level 0: Component name (e.g., "Component 01: Philosophy of religion")
- Level 1: Main topics (numbered sections like "1. Title", "2. Title" - discover from PDF)
- Level 2: Topic headings from the "Topic" column in tables (e.g., "Ancient philosophical influences", "Arguments based on observation")
- Level 3: Items from the "Content" column (includes both full bullets ● and open bullets ○)
- Level 4: Items from the "Key Knowledge" column (these are adjacent to their parent Level 3 items - match them correctly based on position)

CRITICAL: Contextual References
- At the bottom of each Level 1 topic section, there is a "Contextual references" section
- Extract these as Level 2 children of the Level 1 topic
- Extract ONLY the bullet points (ignore "Learners should..." or "For reference" introductory text)
- Example: If Level 1 is "2. The Existence of God", contextual references become "2.X Contextual references" where X is the next number after the last Level 2 topic

OUTPUT FORMAT EXAMPLE:
1 Component 01: Philosophy of religion
1.1 1. Philosophical Language and Thought
1.1.1 Ancient philosophical influences
1.1.1.1 the philosophical views of Plato
1.1.1.1.1 Plato's reliance on reason as opposed to the senses
1.1.1.1.2 the nature of the Forms; hierarchy of the Forms
1.1.1.2 the philosophical views of Aristotle
1.1.1.2.1 Aristotle's use of teleology
1.1.1.2.2 material, formal, efficient and final causes
1.1.2 Contextual references
1.1.2.1 Plato, Republic Book 474c-480; 506b-509c; 509d-511e; 514a-517c
1.1.2.2 Aristotle, Physics II.3 and Metaphysics V.2
1.2 2. The Existence of God
1.2.1 Arguments based on observation
1.2.1.1 the teleological argument
1.2.1.1.1 details of this argument including reference to: Aquinas' Fifth Way, Paley
1.2.1.2 the cosmological argument
1.2.1.2.1 details of this argument including reference to: Aquinas' first three ways
1.2.1.3 challenges to arguments from observation
1.2.1.3.1 details of Hume's criticisms of these arguments for the existence of God from natural religion
1.2.1.3.2 the challenge of evolution
1.2.2 Contextual references
1.2.2.1 Aquinas, Summa Theologiae, 1.2.3
1.2.2.2 Paley, Natural Theology Chapters 1 and 2
1.2.2.3 Hume, Dialogues Concerning Natural Religion Part II
(continue for ALL topics...)

CRITICAL RULES:
1. Discover and extract ALL Level 1 topics from the PDF (main numbered sections)
2. Extract ALL Level 2 topics from the "Topic" column in tables
3. Extract ALL Level 3 items from the "Content" column (both full ● and open ○ bullets - include BOTH types)
4. Extract ALL Level 4 items from the "Key Knowledge" column - match them to their correct Level 3 parent based on position and context (Key Knowledge items appear adjacent to their Content parent)
5. Extract Contextual References as Level 2 children of each Level 1 topic (add after all other Level 2 topics)
6. In Contextual References, extract ONLY bullet points - ignore "Learners should..." or "For reference" introductory text
7. Maintain complete hierarchy
8. OUTPUT MUST BE PLAIN TEXT WITH NUMBERS ONLY - NO MARKDOWN FORMATTING
9. Include BOTH full bullets (●) and open bullets (○) from Content column as Level 3 items

SECTION TEXT:
{section_text[:120000]}"""
        
        return self._call_ai_and_parse(prompt, component['code'], component['code'])
    
    def _call_ai_and_parse(self, prompt: str, component_code: str, base_code: str) -> List[Dict]:
        """Call AI and parse results."""
        
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
                else:  # anthropic
                    response = claude.messages.create(
                        model="claude-3-5-haiku-20241022",
                        max_tokens=8192,
                        messages=[{"role": "user", "content": prompt}],
                        timeout=240
                    )
                    ai_output = response.content[0].text
                
                # Save AI output
                safe_code = re.sub(r'[^\w\-]', '_', component_code)
                ai_file = self.debug_dir / f"{safe_code}-ai-output.txt"
                ai_file.write_text(ai_output, encoding='utf-8')
                print(f"[DEBUG] Saved to {ai_file.name}")
                
                return self._parse_hierarchy(ai_output, base_code)
                
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
    
    def _parse_hierarchy(self, text: str, base_code: str) -> List[Dict]:
        """Parse AI numbered output."""
        all_topics = []
        parent_stack = {-1: None}
        
        # Headers to exclude (section markers, not topics)
        EXCLUDED_HEADERS = [
            'learners should',
            'learners should have the opportunity',
            'discussion opportunities',
            'suggested scholarly views',
        ]
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Match hierarchical numbers (handle markdown if present)
            # Try plain format first: "1.1 Title"
            match = re.match(r'^([\d.]+)\s+(.+)$', line)
            if not match:
                # Try with markdown bold markers: "**1.1 Title**"
                match = re.match(r'^\*\*?([\d.]+)\s+(.+?)\*\*?$', line)
            if not match:
                # Try with leading dash/bullet: "- 1.1.1 Title" or "  - 1.1.1 Title"
                match = re.match(r'^[-•●]\s+([\d.]+)\s+(.+)$', line)
            if not match:
                # Try indented format: "   - 1.1.1 Title" (with spaces before dash)
                match = re.match(r'^\s*[-•●]\s+([\d.]+)\s+(.+)$', line)
            if not match:
                continue
            
            number = match.group(1).rstrip('.')
            title = match.group(2).strip()
            
            # Clean title - remove markdown, bullets, etc.
            title = title.lstrip('*☐✓□■●○-•').strip()
            title = title.rstrip('*').strip()
            
            # Skip very short titles
            if len(title) < 2:
                continue
            
            # Check if this is an excluded header
            title_lower = title.lower()
            is_excluded = False
            
            for excluded in EXCLUDED_HEADERS:
                if excluded in title_lower and len(title_lower) < 100:
                    is_excluded = True
                    break
            
            if is_excluded:
                print(f"[DEBUG] Skipped excluded header: {title}")
                continue
            
            dots = number.count('.')
            level = dots
            
            # Generate code
            code = f"{base_code}_{number.replace('.', '_')}"
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
            print("\n[INFO] Clearing old Religious Studies topics...")
            try:
                temp_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', 'H573').eq('qualification_type', 'A-Level').eq('exam_board', 'OCR').execute()
                if temp_result.data:
                    temp_id = temp_result.data[0]['id']
                    supabase.table('staging_aqa_topics').delete().eq('subject_id', temp_id).execute()
                    print(f"[OK] Cleared old topics for H573")
            except Exception as e:
                print(f"[WARN] Could not clear old topics: {e}")
            
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': "Religious Studies (A-Level)",
                'subject_code': 'H573',
                'qualification_type': 'A-Level',
                'specification_url': PDF_URL,
                'exam_board': 'OCR'
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            subject_id = subject_result.data[0]['id']
            print(f"[OK] Subject ID: {subject_id}")
            
            # Remove duplicates (keep first occurrence)
            seen_codes = set()
            unique_topics = []
            duplicates_count = 0
            for t in topics:
                if t['code'] not in seen_codes:
                    seen_codes.add(t['code'])
                    unique_topics.append(t)
                else:
                    duplicates_count += 1
            
            if duplicates_count > 0:
                print(f"[WARN] Removed {duplicates_count} duplicate topic codes")
            
            # Insert topics
            to_insert = [{
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': t['title'],
                'topic_level': t['level'],
                'exam_board': 'OCR'
            } for t in unique_topics]
            
            inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
            print(f"[OK] Uploaded {len(inserted.data)} topics")
            
            # Link hierarchy
            code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
            linked = 0
            for topic in unique_topics:
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
    scraper = ReligiousStudiesScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

