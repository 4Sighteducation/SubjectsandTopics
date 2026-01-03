"""
OCR A-Level Psychology Manual Structure Scraper
================================================

Extracts topics from OCR Psychology H167/H567 specification.

Structure:
- Level 0: Components (3 total)
- Level 1: Topics/Sections under each component
- Level 2-5: Varies by component (see below)

Component 01: Research methods
- Level 1: Main topics (Self-report, Experiment, Observation, Correlation)
- Level 2: Sub-topics
- Level 3: Solid bullet points
- Level 4: Open bullet points

Component 02: Psychological themes through core studies
- Section A: Core Studies (table-based)
  - Level 1: Section A: Core Studies
  - Level 2: Area (Social, Cognitive, etc.)
  - Level 3: Key Theme
  - Level 4: Classic Study (separate item)
  - Level 4: Contemporary Study (separate item)
- Section B: Areas, Perspectives and debates
- Section C: Practical applications

Component 03: Applied psychology
- Level 1: Section name (Issues in mental health, Child psychology, etc.)
- Level 2: Topic (from Topic column)
- Level 3: Background bullet points
- Level 4: Key research items
- Level 5: Application items

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-psychology-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/171732-specification-accredited-a-level-gce-psychology-h567.pdf'

# 3 components with their structure
COMPONENTS = [
    {
        'name': 'Component 01: Research methods',
        'code': 'H567_01',
        'topics': [
            'Self-report',
            'Experiment',
            'Observation',
            'Correlation'
        ]
    },
    {
        'name': 'Component 02: Psychological themes through core studies',
        'code': 'H567_02',
        'sections': ['Section A: Core Studies', 'Section B: Areas, Perspectives and debates', 'Section C: Practical applications']
    },
    {
        'name': 'Component 03: Applied psychology',
        'code': 'H567_03',
        'sections': [
            'Issues in mental health',
            'Child psychology',
            'Criminal psychology',
            'Environmental psychology',
            'Sports and exercise psychology'
        ]
    }
]


class PsychologyScraper:
    """Scraper for OCR A-Level Psychology."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_pages = []
        self.pdf_text = None
    
    def scrape_all(self):
        """Scrape all 3 components."""
        print("\n" + "🧠 "*40)
        print("OCR PSYCHOLOGY SCRAPER")
        print("🧠 "*40)
        
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
        
        if component['code'] == 'H567_01':
            return self._process_component_01(component)
        elif component['code'] == 'H567_02':
            return self._process_component_02(component)
        elif component['code'] == 'H567_03':
            return self._process_component_03(component)
        else:
            print(f"[ERROR] Unknown component: {component['code']}")
            return []
    
    def _process_component_01(self, component: Dict) -> List[Dict]:
        """Process Component 01: Research methods."""
        
        # Find section
        section_text = self._find_section(component['name'])
        if not section_text:
            print(f"[WARN] Could not find section for {component['code']}")
            return []
        
        print(f"[DEBUG] Found section: {len(section_text)} chars")
        
        # Extract topics
        topics = self._extract_component_01_topics(component, section_text)
        return topics
    
    def _process_component_02(self, component: Dict) -> List[Dict]:
        """Process Component 02: Psychological themes through core studies."""
        
        # Find section
        section_text = self._find_section(component['name'])
        if not section_text:
            print(f"[WARN] Could not find section for {component['code']}")
            return []
        
        print(f"[DEBUG] Found section: {len(section_text)} chars")
        
        # Extract topics - handle Section A specially
        topics = self._extract_component_02_topics(component, section_text)
        return topics
    
    def _process_component_03(self, component: Dict) -> List[Dict]:
        """Process Component 03: Applied psychology."""
        
        all_topics = []
        
        # Create Level 0: Component 03: Applied psychology (ONCE)
        component_03_code = component['code']
        component_03_title = component['name']
        
        all_topics.append({
            'code': component_03_code,
            'title': component_03_title,
            'level': 0,
            'parent': None
        })
        
        # Process each section separately
        for section_name in component['sections']:
            print(f"\n[INFO] Processing section: {section_name}")
            
            # Find section
            section_text = self._find_section(section_name)
            if not section_text:
                print(f"[WARN] Could not find section: {section_name}")
                continue
            
            print(f"[DEBUG] Found section: {len(section_text)} chars")
            
            # Extract topics from table (starting from Level 1, not Level 0)
            section_topics = self._extract_component_03_topics(component, section_name, section_text, component_03_code)
            if section_topics:
                all_topics.extend(section_topics)
        
        return all_topics
    
    def _find_section(self, section_name: str) -> Optional[str]:
        """Find a section in the PDF."""
        
        # Extract short name if it's a component name
        short_name = section_name
        component_num = None
        
        if "Component 01" in section_name:
            short_name = "Research methods"
            component_num = "01"
        elif "Component 02" in section_name:
            short_name = "Psychological themes through core studies"
            component_num = "02"
        elif "Component 03" in section_name:
            short_name = "Applied psychology"
            component_num = "03"
        
        # Try different patterns (OCR typically uses "Content of..." format)
        patterns = [
            rf'Content\s+of\s+{re.escape(short_name)}\s*\(Component\s+{component_num}\)',
            rf'Content\s+of\s+{re.escape(short_name)}',
            rf'\d+[cdef]\.\s+Content\s+of\s+{re.escape(short_name)}',
            rf'Component\s+{component_num}:\s+{re.escape(short_name)}',
            rf'{re.escape(section_name)}',
        ]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE | re.DOTALL))
            if matches:
                # Skip TOC matches - only use matches after position 5000
                valid_matches = [m for m in matches if m.start() > 5000]
                if not valid_matches:
                    valid_matches = matches
                
                if not valid_matches:
                    continue
                
                # Take the longest match
                best_match = max(valid_matches, key=lambda m: len(self.pdf_text[m.start():m.start()+50000]))
                start = best_match.start()
                
                # Find end: next component or end marker
                end_patterns = [
                    r'\nComponent\s+0[123]',
                    r'\n\d+[cdef]\.\s+Content',
                    r'\nVersion\s+\d+\.\d+',
                    r'\nAppendix',
                    r'\n2[cdef]\.\s+Content',
                    r'\n3\.\s+Assessment'
                ]
                end_pos = len(self.pdf_text)
                for ep in end_patterns:
                    end_match = re.search(ep, self.pdf_text[start+1000:start+100000])
                    if end_match:
                        end_pos = start + 1000 + end_match.start()
                        break
                
                section = self.pdf_text[start:end_pos]
                if len(section) > 500:
                    print(f"[DEBUG] Found section using pattern: {pattern[:50]}...")
                    return section
        
        # Debug: Try to find what's actually in the PDF
        print(f"[DEBUG] Could not find section: {section_name}")
        print(f"[DEBUG] Searching for: {short_name}")
        # Look for any mention of the section name
        test_match = re.search(rf'{re.escape(short_name[:20])}', self.pdf_text, re.IGNORECASE)
        if test_match:
            print(f"[DEBUG] Found mention of '{short_name[:20]}' at position {test_match.start()}")
            # Show context
            context_start = max(0, test_match.start() - 200)
            context_end = min(len(self.pdf_text), test_match.start() + 200)
            print(f"[DEBUG] Context: ...{self.pdf_text[context_start:context_end]}...")
        
        return None
    
    def _extract_component_01_topics(self, component: Dict, section_text: str) -> List[Dict]:
        """Extract topics from Component 01."""
        
        prompt = f"""You must extract the COMPLETE hierarchy from OCR Psychology Component 01: Research methods.

CRITICAL: Extract EVERYTHING you can see. Do NOT stop partway. Do NOT ask questions. Extract EVERYTHING NOW.
OUTPUT FORMAT: Use ONLY numbered format (1, 1.1, 1.1.1) - NO bullets (-), NO asterisks (*), NO markdown (**), NO bold markers.
Do NOT use markdown formatting. Do NOT use bullets. Use ONLY numbers and dots.

COMPONENT: {component['name']}

STRUCTURE (4-5 levels):
- Level 0: Component 01: Research methods
- Level 1: Main topics: Self-report, Experiment, Observation, Correlation
- Level 2: Sub-topics under each main topic (e.g., under Experiment: laboratory experiment, field experiment, quasi experiment)
- Level 3: Solid bullet points (●)
- Level 4: Open bullet points (○) if present

CRITICAL FILTERING RULES:
- IGNORE any headings or text that says "Learners should..." or "Learners should have experience of the following practical activities:"
- These are just section markers, NOT topics
- Extract the actual content bullet points that follow these headings

OUTPUT FORMAT: Use ONLY numbered format (1, 1.1, 1.1.1, 1.1.1.1) - NO bullets (-), NO asterisks (*), NO markdown (**), NO bold markers.

EXAMPLE:
1 Component 01: Research methods
1.1 Self-report
1.1.1 Questionnaire
1.1.1.1 Structured
1.1.1.2 Semi-structured
1.1.1.3 Unstructured
1.1.2 Interviews
1.1.2.1 Structured
1.1.2.2 Semi-structured
1.1.2.3 Unstructured
1.2 Experiment
1.2.1 laboratory experiment
1.2.1.1 Control of variables
1.2.1.2 Standardized procedures
1.2.2 field experiment
1.2.2.1 Natural environment
1.2.2.2 Real-life context
1.2.3 quasi experiment
1.2.3.1 Pre-existing variables
1.2.3.2 Lack of random assignment
1.3 Observation
1.3.1 structured
1.3.1.1 Pre-determined categories
1.3.2 unstructured
1.3.2.1 Open-ended observation
1.3.3 naturalistic
1.3.3.1 Observing in natural settings
1.4 Correlation
1.4.1 Positive correlation
1.4.1.1 Variables increase together
1.4.2 Negative correlation
1.4.2.1 One variable increases, the other decreases
(continue for ALL content...)

CRITICAL RULES:
1. Extract ALL main topics (Self-report, Experiment, Observation, Correlation)
2. Extract ALL sub-topics under each
3. Extract ALL solid bullet points (●) as Level 3
4. Extract ALL open bullet points (○) as Level 4
5. SKIP "Learners should..." headings - they are NOT topics
6. Maintain complete hierarchy
7. OUTPUT MUST BE PLAIN TEXT WITH NUMBERS ONLY - NO MARKDOWN FORMATTING

SECTION TEXT:
{section_text[:80000]}"""
        
        return self._call_ai_and_parse(prompt, component['code'], "H567_01")
    
    def _extract_component_02_topics(self, component: Dict, section_text: str) -> List[Dict]:
        """Extract topics from Component 02."""
        
        prompt = f"""You must extract the COMPLETE hierarchy from OCR Psychology Component 02: Psychological themes through core studies.

CRITICAL: Extract EVERYTHING you can see. Do NOT stop partway. Do NOT ask questions. Extract EVERYTHING NOW.
OUTPUT FORMAT: Use ONLY numbered format (1, 1.1, 1.1.1) - NO bullets (-), NO asterisks (*), NO markdown (**), NO bold markers.
Do NOT use markdown formatting. Do NOT use bullets. Use ONLY numbers and dots.

COMPONENT: {component['name']}

This component has THREE sections that need different handling:

SECTION A: Core Studies (table-based, around page 17)
- Find the table with columns: Area | Key theme | Classic study | Contemporary study
- Level 0: Component 02: Psychological themes through core studies
- Level 1: Section A: Core Studies
- Level 2: Area (e.g., Social, Cognitive)
- Level 3: Key Theme (e.g., "Responses to people in authority")
- Level 4: Classic Study (e.g., "Milgram (1963) Obedience") - SEPARATE item
- Level 4: Contemporary Study (e.g., "Bocchiaro et al. (2012) Disobedience and whistle-blowing") - SEPARATE item

CRITICAL: After the Core Studies table, there is a "Content" section - STOP EXTRACTION IMMEDIATELY when you see this heading. Do not extract anything from the "Content" section or anything that comes after it within Section A. Only extract from the Core Studies table itself.

SECTION B: Areas, Perspectives and debates
- Extract as normal hierarchy under Component 02

SECTION C: Practical applications
- Extract as normal hierarchy under Component 02

OUTPUT FORMAT: Use ONLY numbered format (1, 1.1, 1.1.1, 1.1.1.1) - NO bullets (-), NO asterisks (*), NO markdown (**), NO bold markers.

EXAMPLE:
1 Component 02: Psychological themes through core studies
1.1 Section A: Core Studies
1.1.1 Social
1.1.1.1 Responses to people in authority
1.1.1.1.1 Milgram (1963) Obedience
1.1.1.1.2 Bocchiaro et al. (2012) Disobedience and whistle-blowing
1.1.1.2 Responses to people in need
1.1.1.2.1 Piliavin et al. (1969) Subway Samaritan
1.1.1.2.2 Levine et al. (2001) Cross-cultural altruism
1.1.2 Cognitive
1.1.2.1 Memory
1.1.2.1.1 Loftus and Palmer (1974) Eyewitness testimony
1.1.2.1.2 Grant et al. (1998) Context-dependent memory
1.1.2.2 Attention
1.1.2.2.1 Moray (1959)
1.1.2.2.2 Simons and Chabris (1999)
(continue for ALL areas, themes, and studies...)
1.2 Section B: Areas, Perspectives and debates
1.2.1 [Extract ALL topics from Section B]
1.3 Section C: Practical applications
1.3.1 [Extract ALL topics from Section C]

CRITICAL RULES:
1. Extract ALL rows from the Core Studies table
2. Classic Study and Contemporary Study are SEPARATE Level 4 items (not combined)
3. IGNORE the "Content" section completely - STOP when you see "Content" heading
4. Extract Sections B and C as normal hierarchy with ALL their content
5. Maintain complete structure
6. OUTPUT MUST BE PLAIN TEXT WITH NUMBERS ONLY - NO MARKDOWN FORMATTING

SECTION TEXT:
{section_text[:100000]}"""
        
        return self._call_ai_and_parse(prompt, component['code'], "H567_02")
    
    def _extract_component_03_topics(self, component: Dict, section_name: str, section_text: str, parent_code: str) -> List[Dict]:
        """Extract topics from Component 03 table."""
        
        prompt = f"""You must extract the COMPLETE hierarchy from OCR Psychology Component 03: Applied psychology.

CRITICAL: Extract EVERYTHING you can see. Do NOT stop partway. Do NOT ask questions. Extract EVERYTHING NOW.
OUTPUT FORMAT: Use ONLY numbered format (1, 1.1, 1.1.1) - NO bullets (-), NO asterisks (*), NO markdown (**), NO bold markers.
Do NOT use markdown formatting. Do NOT use bullets. Use ONLY numbers and dots.

SECTION: {section_name}

CRITICAL: Find the TABLE with 4 columns: Topic | Background | Key research | Application
This table contains the actual content for this section. Do NOT extract from other sections or general text.
Look for a table structure with these exact column headers.

TABLE STRUCTURE:
The content is in a table with 4 columns: Topic | Background | Key research | Application
Each row represents one topic with its background points, key research, and application.

STRUCTURE (starts at Level 1 - section name):
- Level 1: Section name (e.g., "Issues in mental health")
- Level 2: Topic (from Topic column, e.g., "The historical context of mental health")
- Level 3: Background bullet points (from Background column)
- Level 4: Key research items (from Key research column)
- Level 5: Application items (from Application column)

OUTPUT FORMAT: Use ONLY numbered format (1, 1.1, 1.1.1, 1.1.1.1, 1.1.1.1.1) - NO bullets (-), NO asterisks (*), NO markdown (**), NO bold markers.
START FROM LEVEL 1 - Do NOT include "Component 03: Applied psychology" in output.

EXAMPLE:
1 {section_name}
1.1 The historical context of mental health
1.1.1 Historical views of mental illness
1.1.2 Defining abnormality
1.1.3 Categorising mental disorders
1.1.1 Rosenhan (1973) On being sane in insane places
1.1.1.1 Characteristics of an affective disorder, a psychotic disorder and an anxiety disorder
1.2 The medical model
1.2.1 The biochemical explanation of mental illness
1.2.2 The genetic explanation of mental illness
1.2.3 Brain abnormality as an explanation of mental illness
1.2.1 Gottesman et al. (2010) Disorders in offspring with two psychiatrically ill parents
1.2.1.1 Biological treatment of one specific disorder
(continue for ALL topics in this section...)

CRITICAL RULES:
1. START FROM LEVEL 1 (section name) - Do NOT include "Component 03: Applied psychology"
2. Extract ALL rows from the table
3. Each row's Topic column becomes Level 2
4. Background column bullet points become Level 3
5. Key research column items become Level 4
6. Application column items become Level 5
7. Extract ALL 4 columns as separate levels
8. Maintain complete hierarchy
9. OUTPUT MUST BE PLAIN TEXT WITH NUMBERS ONLY - NO MARKDOWN FORMATTING

SECTION TEXT:
{section_text[:80000]}"""
        
        # Sanitize section name for code generation
        safe_section_name = re.sub(r'[^\w\-]', '_', section_name.replace(' ', '_'))
        safe_section_name = re.sub(r'_+', '_', safe_section_name).strip('_')
        
        # Extract topics starting from Level 1, then adjust to be under parent_code
        extracted_topics = self._call_ai_and_parse(prompt, component['code'], f"H567_03_{safe_section_name}")
        
        # Adjust levels: add 1 to each level and set parent for Level 1 items
        adjusted_topics = []
        for topic in extracted_topics:
            # Level 0 items become Level 1, Level 1 become Level 2, etc.
            topic['level'] = topic['level'] + 1
            
            # If this was Level 0, it becomes Level 1 and parent is parent_code
            if topic['level'] == 1:
                topic['parent'] = parent_code
            # Otherwise, parent relationships are maintained from the extraction
            
            # Update code to reflect new level structure
            # The base_code already includes the section name, so codes should be fine
            adjusted_topics.append(topic)
        
        return adjusted_topics
    
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
            'learners should have experience',
            'learners should have experience of the following',
        ]
        
        # Special handling: Skip "Content" section items in Component 02
        # This is detected by checking if we're in Component 02 context
        if 'H567_02' in base_code:
            EXCLUDED_HEADERS.append('content')
        
        for line in text.split('\n'):
            original_line = line
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
            
            # Special case: "Content" - only exclude if it's a standalone heading (very short)
            if 'content' in title_lower and len(title_lower) < 20:
                is_excluded = True
            else:
                # Check other excluded headers
                for excluded in EXCLUDED_HEADERS:
                    if excluded != 'content' and excluded in title_lower and len(title_lower) < 100:
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
            print("\n[INFO] Clearing old Psychology topics...")
            try:
                temp_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', 'H567').eq('qualification_type', 'A-Level').eq('exam_board', 'OCR').execute()
                if temp_result.data:
                    temp_id = temp_result.data[0]['id']
                    supabase.table('staging_aqa_topics').delete().eq('subject_id', temp_id).execute()
                    print(f"[OK] Cleared old topics for H567")
            except Exception as e:
                print(f"[WARN] Could not clear old topics: {e}")
            
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': "Psychology (A-Level)",
                'subject_code': 'H567',
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
    scraper = PsychologyScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

