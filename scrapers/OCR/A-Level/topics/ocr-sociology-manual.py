"""
OCR A-Level Sociology Manual Structure Scraper
===============================================

Extracts topics from OCR Sociology specification.

Structure:
- Level 0: Components (01, 02, 03)
- Level 1: Main topics/sections (clearly labeled)
- Level 2: Key questions (from "Key questions" column in tables)
- Level 3: Content items (from "Content" column)
- Level 4: Sub-items (bullets under Content) + "Learners should:" items (matched to Content parent)

Component 01: Socialisation, culture and identity
- Section A: Introducing socialisation, culture and identity
- Section B: One of three options (Families and relationships, Youth subcultures, Media)

Component 02: Researching and understanding social inequalities
- Methods of sociological enquiry
- Social difference and inequality (class, gender, ethnicity, age)

Component 03: Debates in contemporary society
- Section A: Globalisation and the digital social world (compulsory)
- Section B: One of three options (Crime and deviance, Education, Religion, belief and faith)

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-sociology-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/170212-specification-accredited-a-level-gce-sociology.pdf'

# Components structure
COMPONENTS = [
    {
        'name': 'Component 01: Socialisation, culture and identity',
        'code': 'H580_01',
        'short_name': 'Socialisation, culture and identity',
        'section_pattern': r'Content\s+of\s+Socialisation,\s+culture\s+and\s+identity'
    },
    {
        'name': 'Component 02: Researching and understanding social inequalities',
        'code': 'H580_02',
        'short_name': 'Researching and understanding social inequalities',
        'section_pattern': r'Content\s+of\s+Researching\s+and\s+understanding\s+social\s+inequalities'
    },
    {
        'name': 'Component 03: Debates in contemporary society',
        'code': 'H580_03',
        'short_name': 'Debates in contemporary society',
        'section_pattern': r'Content\s+of\s+Debates\s+in\s+contemporary\s+society'
    }
]


class SociologyScraper:
    """Scraper for OCR A-Level Sociology."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_pages = []
        self.pdf_text = None
    
    def scrape_all(self):
        """Scrape all components."""
        print("\n" + "👥 "*40)
        print("OCR SOCIOLOGY SCRAPER")
        print("👥 "*40)
        
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
            rf'{re.escape(component["short_name"])}\s*\(H580/0[1-3]\)',
            rf'Component\s+0[1-3]:\s+{re.escape(component["short_name"])}',
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
                    r'\nContent\s+of\s+(Socialisation|Researching|Debates)',  # Next component
                    r'\nComponent\s+0[1-3]:',  # Next component
                    r'\n\d+[a-z]\.\s+Prior\s+knowledge',  # Next main section
                    r'\n\d+\.\s+Assessment',  # Assessment section
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
        
        prompt = f"""You must extract the COMPLETE hierarchy from OCR Sociology {component['name']}.

CRITICAL: Extract EVERYTHING you can see. Do NOT stop partway. Do NOT ask questions. Extract EVERYTHING NOW.
OUTPUT FORMAT: Use ONLY numbered format (1, 1.1, 1.1.1) - NO bullets (-), NO asterisks (*), NO markdown (**), NO bold markers.
Do NOT use markdown formatting. Do NOT use bullets. Use ONLY numbers and dots.

COMPONENT: {component['name']}

PDF TABLE STRUCTURE:
The content is organized in tables with three columns: "Key questions", "Content", and "Learners should:"

STRUCTURE (5 levels):
- Level 0: Component name (e.g., "Component 01: Socialisation, culture and identity")
- Level 1: Main topics/sections (clearly labeled, e.g., "Section A: Introducing socialisation, culture and identity", "Section B Option 1: Families and relationships")
- Level 2: Key questions from the "Key questions" column (e.g., "1. What is culture?", "2. What is socialisation?")
- Level 3: Content items from the "Content" column (e.g., "Culture, norms and values", "Primary and secondary socialisation")
- Level 4: Sub-items from Content (bullets under Content) AND "Learners should:" items (matched to their Content parent)

CRITICAL: "Learners should:" Matching
- The "Learners should:" column contains learning objectives that are adjacent to their Content parent
- Match each "Learners should:" item to its correct Level 3 Content parent based on position and context
- These become Level 4 children of the Content item

CRITICAL: Topics Spanning Pages
- Some topics span multiple pages - look for "cont." indicators or continuation of table rows
- Extract complete topics even if they continue across page boundaries
- Maintain hierarchy when topics continue

OUTPUT FORMAT EXAMPLE:
1 Component 01: Socialisation, culture and identity
1.1 Section A: Introducing socialisation, culture and identity
1.1.1 1. What is culture?
1.1.1.1 Culture, norms and values
1.1.1.1.1 be able to understand the relative nature of culture, norms and values. Cross-Cultural material should be used here.
1.1.1.2 Types of culture:
1.1.1.2.1 subculture
1.1.1.2.2 high culture
1.1.1.2.3 popular culture
1.1.1.2.4 global culture
1.1.1.2.5 consumer culture
1.1.1.3 Cultural diversity
1.1.1.4 Cultural hybridity
1.1.2 2. What is socialisation?
1.1.2.1 Primary and secondary socialisation
1.1.2.1.1 be able to link definitions of primary socialisation and secondary socialisation to relevant agencies of socialisation, understanding that socialisation is a lifelong process.
1.1.2.2 Agencies of socialisation:
1.1.2.2.1 family
1.1.2.2.2 peer group
1.1.2.2.3 media
1.1.2.2.4 religion
1.1.2.2.5 understand the link between socialisation and the creation of identities.
1.2 Section B Option 1: Families and relationships
1.2.1 How diverse are modern families?
1.2.1.1 The diversity of family and household types in the contemporary UK:
1.2.1.1.1 nuclear families
1.2.1.1.2 extended families
1.2.1.1.3 lone parent families
1.2.1.1.4 reconstituted families
1.2.1.1.5 same-sex families
1.2.1.1.6 non-family households
1.2.1.1.7 also consider newer/emerging types of families and households.
1.2.1.2 Aspects of and reasons for family and household diversity in the contemporary UK, including:
1.2.1.2.1 trends in marriage, divorce and cohabitation
1.2.1.2.2 demographic changes
1.2.1.2.3 birth rate
1.2.1.2.4 have an overview of trends over the last 30 years and consider the key reasons for these changes. Detailed knowledge of statistics on marriage, divorce and demographic changes is not required.
(continue for ALL topics...)

CRITICAL RULES:
1. Discover and extract ALL Level 1 topics/sections from the PDF (Section A, Section B options, etc.)
2. Extract ALL Level 2 topics from the "Key questions" column in tables
3. Extract ALL Level 3 items from the "Content" column
4. Extract ALL Level 4 sub-items (bullets under Content) AND "Learners should:" items - match "Learners should:" to their correct Content parent based on position
5. Handle topics that span multiple pages - look for "cont." or continuation indicators
6. Maintain complete hierarchy
7. OUTPUT MUST BE PLAIN TEXT WITH NUMBERS ONLY - NO MARKDOWN FORMATTING
8. Include BOTH Content sub-items (bullets) AND "Learners should:" items as Level 4

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
            'key questions',
            'content',
            'discussion opportunities',
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
            
            # Only exclude if it's a standalone header (short and matches exactly)
            for excluded in EXCLUDED_HEADERS:
                if excluded == title_lower and len(title_lower) < 30:
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
            print("\n[INFO] Clearing old Sociology topics...")
            try:
                temp_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', 'H580').eq('qualification_type', 'A-Level').eq('exam_board', 'OCR').execute()
                if temp_result.data:
                    temp_id = temp_result.data[0]['id']
                    supabase.table('staging_aqa_topics').delete().eq('subject_id', temp_id).execute()
                    print(f"[OK] Cleared old topics for H580")
            except Exception as e:
                print(f"[WARN] Could not clear old topics: {e}")
            
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': "Sociology (A-Level)",
                'subject_code': 'H580',
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
    scraper = SociologyScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

