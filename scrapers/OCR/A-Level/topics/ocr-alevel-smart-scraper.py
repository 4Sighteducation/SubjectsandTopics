"""
OCR A-Level Smart Two-Stage Topic Scraper
==========================================

STAGE 1: Scrapes "specification at a glance" HTML page for clean module structure
STAGE 2: Scrapes PDF specification for detailed sub-topics within each module

This two-stage approach is MUCH more reliable than PDF-only scraping!

Requirements:
    pip install selenium beautifulsoup4 anthropic openai pdfplumber

Usage:
    python ocr-alevel-smart-scraper.py AL-BiologyA
    python ocr-alevel-smart-scraper.py --all
"""

import os
import sys
import re
import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
from supabase import create_client
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

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
anthropic_key = os.getenv('ANTHROPIC_API_KEY')
openai_key = os.getenv('OPENAI_API_KEY')
gemini_key = os.getenv('GEMINI2.5_API_KEY') or os.getenv('GEMINI_API_KEY')

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found in .env!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

# Determine AI provider
AI_PROVIDER = None
if anthropic_key:
    try:
        import anthropic
        claude = anthropic.Anthropic(api_key=anthropic_key)
        AI_PROVIDER = "anthropic"
        print("[INFO] Using Anthropic Claude API for Stage 2")
    except ImportError:
        pass

if not AI_PROVIDER and openai_key:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=openai_key)
        AI_PROVIDER = "openai"
        print("[INFO] Using OpenAI GPT-4 API for Stage 2")
    except ImportError:
        pass

if not AI_PROVIDER and gemini_key:
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        gemini_model = genai.GenerativeModel('gemini-1.5-pro')
        AI_PROVIDER = "gemini"
        print("[INFO] Using Google Gemini API for Stage 2")
    except ImportError:
        pass

if not AI_PROVIDER:
    print("[ERROR] No AI API keys found! Need one of: ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI2.5_API_KEY")
    sys.exit(1)


# ================================================================
# STAGE 2 AI PROMPT (for detailed sub-topics)
# ================================================================

DETAIL_PROMPT_TEMPLATE = """I need you to extract ONLY the detailed sub-topics for this specific unit/module from the OCR A-Level specification PDF.

UNIT/MODULE TO EXTRACT: "{module_name}"

Please find this section in the specification and extract ALL its detailed content in a hierarchical numbered list.

CRITICAL: Start numbering from 1, regardless of the unit/module number. Examples:
- "Module 2: Foundations in biology" → use 1, 1.1, 1.1.1 (NOT 2.1, 2.1.1)
- "Unit group 3" → use 1, 1.1, 1.1.1 (NOT 3.1, 3.1.1)
- "Component 01" → use 1, 1.1, 1.1.1 (NOT 1.1, 1.1.1)

Format:
1. First main topic
1.1 Sub-topic
1.1.1 Detailed point
2. Second main topic
2.1 Sub-topic

Rules:
- Extract ONLY content for "{module_name}" - ignore other sections
- START numbering from 1 (never use section number prefix)
- Include ALL learning objectives and content points
- Use consistent decimal numbering
- Skip introductory/assessment text

Output ONLY the numbered hierarchy, nothing else.

PDF TEXT:
{pdf_text}"""


# ================================================================
# SCRAPER CLASS
# ================================================================

class OCRSmartScraper:
    """Two-stage scraper: HTML for structure, PDF for details."""
    
    def __init__(self, subject_info: Dict):
        self.subject = subject_info
        self.topics = []
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        
        # Load History Y-codes if this is History
        if 'History' in subject_info['name']:
            y_codes_file = Path(__file__).parent / "history-y-codes.json"
            if y_codes_file.exists():
                with open(y_codes_file, 'r', encoding='utf-8') as f:
                    self._history_y_codes = json.load(f)
                print("[INFO] Loaded History Y-code mappings")
        
        # Setup Selenium
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        self.driver = webdriver.Chrome(options=chrome_options)
        
    def __del__(self):
        """Clean up driver."""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except:
                pass
    
    def scrape_stage1_html(self) -> List[Dict]:
        """STAGE 1: Scrape 'at a glance' page for module structure."""
        print("\n" + "="*80)
        print("STAGE 1: Scraping HTML 'specification at a glance' page")
        print("="*80)
        
        url = self.subject['at_a_glance_url']
        print(f"[INFO] Loading: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(8)  # Wait longer for JavaScript pages
            
            # Get page source
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Save debug copy
            debug_file = self.debug_dir / f"{self.subject['code']}-at-a-glance.html"
            debug_file.write_text(page_source, encoding='utf-8')
            print(f"[DEBUG] Saved to {debug_file.name}")
            
            # Find content overview section
            topics = []
            
            # Try to find "Content overview" or similar heading
            content_heading = None
            for heading in soup.find_all(['h2', 'h3', 'h4']):
                if 'content' in heading.get_text().lower() and 'overview' in heading.get_text().lower():
                    content_heading = heading
                    break
            
            if content_heading:
                print(f"[OK] Found 'Content overview' section")
                
                # Extract modules with their key topics from the overview section
                modules = self._extract_modules_from_content_overview(soup, content_heading)
                topics.extend(modules)
                
                print(f"[OK] Stage 1 extracted {len(topics)} topics from HTML")
                
                # Show what we found
                for topic in topics[:10]:
                    print(f"  - {topic['code']} (L{topic['level']}): {topic['title']}")
                if len(topics) > 10:
                    print(f"  ... and {len(topics) - 10} more")
                
                return topics
            else:
                print("[ERROR] Could not find content structure in HTML")
                return []
                
        except Exception as e:
            print(f"[ERROR] Stage 1 failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_modules_from_content_overview(self, soup: BeautifulSoup, content_heading) -> List[Dict]:
        """Extract modules/units from HTML - handles different OCR patterns."""
        topics = []
        seen_units = set()
        
        # Find all headings (h3, h4) that might contain unit/module info
        headings = soup.find_all(['h3', 'h4'])
        
        for heading in headings:
            heading_text = heading.get_text().strip()
            
            # Try multiple patterns that OCR uses:
            
            # Pattern 0: "Storylines" heading (Chemistry B Salters)
            if re.match(r'Storylines?', heading_text, re.IGNORECASE):
                # This is the storylines section - extract the list
                ul = heading.find_next_sibling('ul')
                if ul:
                    lis = ul.find_all('li', recursive=False)
                    for i, li in enumerate(lis, 1):
                        storyline_title = li.get_text().strip()
                        code = f'Storyline{i}'
                        topics.append({
                            'code': code,
                            'title': storyline_title,
                            'level': 0,
                            'parent': None
                        })
                        print(f"[DEBUG] Storyline {i}: {storyline_title}")
                continue
            
            # Pattern 1: "Module X: Title"
            module_match = re.match(r'Module (\d+):\s*(.+)', heading_text, re.IGNORECASE)
            if module_match:
                num = module_match.group(1)
                title = module_match.group(2).strip()
                
                if num not in seen_units:
                    seen_units.add(num)
                    code = f'Module{num}'
                    topics.append({
                        'code': code,
                        'title': f'Module {num}: {title}',
                        'level': 0,
                        'parent': None
                    })
                    print(f"[DEBUG] Module {num}: {title}")
                    
                    # Extract key topics from <ul> if present
                    ul = heading.find_next_sibling('ul')
                    if ul:
                        lis = ul.find_all('li', recursive=False)
                        for i, li in enumerate(lis, 1):
                            topic_title = li.get_text().strip()
                            topic_code = f'{code}_{i}'
                            topics.append({
                                'code': topic_code,
                                'title': topic_title,
                                'level': 1,
                                'parent': code
                            })
                            print(f"[DEBUG]   - {topic_title}")
                continue
            
            # Pattern 2: "Unit group X" or "Unit X"
            unit_match = re.match(r'Unit\s+(?:group\s+)?(\d+)', heading_text, re.IGNORECASE)
            if unit_match:
                num = unit_match.group(1)
                
                if num not in seen_units:
                    seen_units.add(num)
                    code = f'Unit{num}'
                    topics.append({
                        'code': code,
                        'title': heading_text,
                        'level': 0,
                        'parent': None
                    })
                    print(f"[DEBUG] {heading_text}")
                    
                    # Find the next <ul> sibling to extract topic options
                    ul = heading.find_next_sibling('ul')
                    if ul:
                        lis = ul.find_all('li', recursive=False)
                        for i, li in enumerate(lis, 1):
                            option_title = li.get_text().strip()
                            option_code = f'{code}_{i}'
                            topics.append({
                                'code': option_code,
                                'title': option_title,
                                'level': 1,
                                'parent': code
                            })
                            print(f"[DEBUG]   - {option_title}")
                continue
            
            # Pattern 3: "Component X" or "Component 01: Title" or "Paper X"
            component_match = re.match(r'(?:Component|Paper)\s+(\d+)(?::\s*(.+))?', heading_text, re.IGNORECASE)
            if component_match:
                num = component_match.group(1)
                comp_title = component_match.group(2)
                
                if num not in seen_units:
                    seen_units.add(num)
                    code = f'Component{num.zfill(2)}'  # Pad: 01, 02, 03
                    topics.append({
                        'code': code,
                        'title': heading_text,
                        'level': 0,
                        'parent': None
                    })
                    print(f"[DEBUG] {heading_text}")
                    
                    # Extract topics from <ul> if present (won't exist for Economics)
                    ul = heading.find_next_sibling('ul')
                    if ul:
                        lis = ul.find_all('li', recursive=False)
                        for i, li in enumerate(lis, 1):
                            topic_title = li.get_text().strip()
                            topic_code = f'{code}_{i}'
                            topics.append({
                                'code': topic_code,
                                'title': topic_title,
                                'level': 1,
                                'parent': code
                            })
                            print(f"[DEBUG]   - {topic_title}")
                continue
        
        print(f"[INFO] Extracted {len(seen_units)} units/modules (PDF Stage 2 will add sub-topics)")
        return topics
    
    def scrape_stage2_pdf(self, stage1_topics: List[Dict]) -> List[Dict]:
        """STAGE 2: Scrape PDF for detailed sub-topics for each module."""
        print("\n" + "="*80)
        print("STAGE 2: Scraping PDF for detailed sub-topics")
        print("="*80)
        
        # Download PDF
        print(f"[INFO] Downloading PDF...")
        try:
            response = requests.get(self.subject['pdf_url'], timeout=60)
            response.raise_for_status()
            pdf_content = response.content
            print(f"[OK] Downloaded {len(pdf_content)/1024/1024:.1f} MB")
        except Exception as e:
            print(f"[ERROR] PDF download failed: {e}")
            print(f"[WARN] Continuing with HTML data only (Stage 1: {len(stage1_topics)} topics)")
            return stage1_topics  # Return what we have from Stage 1
        
        # Extract PDF text
        pdf_text = self._extract_pdf_text(pdf_content)
        if not pdf_text:
            print("[ERROR] Could not extract PDF text")
            return stage1_topics
        
        # Decide what to process based on structure
        all_topics = stage1_topics.copy()
        
        l0_items = [t for t in stage1_topics if t['level'] == 0]
        l1_items = [t for t in stage1_topics if t['level'] == 1]
        
        # If there are MANY L1 items (>30, like History's 58 options), process them individually
        # Otherwise, just process L0 and let AI extract all sub-content
        if len(l1_items) > 30:
            print(f"[INFO] Many topic options detected ({len(l1_items)}), processing each individually...")
            items_to_process = l0_items + l1_items
        else:
            print(f"[INFO] Standard module structure, processing {len(l0_items)} modules...")
            items_to_process = l0_items
        
        for item in items_to_process:
            print(f"\n[INFO] Processing: {item['title'][:80]}...")
            
            # Base level = item level + 1 (so children go one level deeper)
            item_details = self._extract_module_details_with_ai(
                module_name=item['title'],
                pdf_text=pdf_text,
                parent_code=item['code'],
                base_level=item['level'] + 1
            )
            
            if item_details:
                print(f"[OK] Found {len(item_details)} sub-topics for {item['code']}")
                all_topics.extend(item_details)
            else:
                print(f"[WARN] No details found for {item['code']}")
        
        print(f"\n[OK] Stage 2 complete: {len(all_topics)} total topics")
        return all_topics
    
    def _extract_pdf_text(self, pdf_content: bytes) -> Optional[str]:
        """Extract text from PDF."""
        try:
            import pdfplumber
            from io import BytesIO
            
            print("[INFO] Extracting PDF text with pdfplumber...")
            pdf_file = BytesIO(pdf_content)
            text = ""
            
            with pdfplumber.open(pdf_file) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    if i % 20 == 0:
                        print(f"[INFO] Processed {i+1}/{len(pdf.pages)} pages...")
            
            print(f"[OK] Extracted {len(text)} characters")
            
            # Save debug copy
            debug_file = self.debug_dir / f"{self.subject['code']}-spec.txt"
            debug_file.write_text(text, encoding='utf-8')
            
            return text
            
        except ImportError:
            print("[WARN] pdfplumber not available, trying pypdf...")
            try:
                from pypdf import PdfReader
                from io import BytesIO
                
                pdf_file = BytesIO(pdf_content)
                reader = PdfReader(pdf_file)
                text = ""
                
                for i, page in enumerate(reader.pages):
                    text += page.extract_text() + "\n"
                
                return text
            except Exception as e:
                print(f"[ERROR] PDF extraction failed: {e}")
                return None
    
    def _find_module_section_in_pdf(self, module_name: str, pdf_text: str, parent_code: str = None) -> Optional[str]:
        """Extract just the section for a specific module/unit from the PDF."""
        
        # SPECIAL HANDLING FOR HISTORY Y-CODES
        # Check if this is a History topic that needs Y-code lookup
        if hasattr(self, '_history_y_codes'):
            for group, mappings in self._history_y_codes.items():
                for title, y_code in mappings.items():
                    # Fuzzy match (strip punctuation differences)
                    clean_module = re.sub(r'[—\-\s]+', ' ', module_name.lower())
                    clean_title = re.sub(r'[—\-\s]+', ' ', title.lower())
                    if clean_module in clean_title or clean_title in clean_module:
                        print(f"[DEBUG] Matched to Y-code: {y_code}")
                        # Find this Y-code in the PDF
                        pattern = rf'Unit {y_code}[:\s]'
                        match = re.search(pattern, pdf_text, re.IGNORECASE)
                        if match:
                            # Find end (next Y-code or end)
                            next_y = f"Y{int(y_code[1:]) + 1}"
                            end_patterns = [rf'Unit {next_y}[:\s]', r'Appendix', r'Version \d+\.\d+']
                            end_pos = len(pdf_text)
                            for ep in end_patterns:
                                end_match = re.search(ep, pdf_text[match.start():], re.IGNORECASE)
                                if end_match:
                                    end_pos = match.start() + end_match.start()
                                    break
                            return pdf_text[match.start():end_pos]
        
        # STANDARD HANDLING FOR MODULE/UNIT/COMPONENT/STORYLINE
        # Try to extract number from the name
        unit_match = re.search(r'(?:Module|Unit|Component|Paper|Storyline)\s+(?:group\s+)?(\d+)', module_name, re.IGNORECASE)
        if not unit_match:
            return None
        
        module_num = unit_match.group(1)
        
        # Extract the title part (e.g., "Foundations in biology" from "Module 2: Foundations in biology")
        title_part = None
        if ':' in module_name:
            title_part = module_name.split(':', 1)[1].strip()
        
        # For Storylines, search for the actual storyline name (Chemistry B Salters)
        if parent_code and 'Storyline' in parent_code:
            # module_name is the title (e.g., "Elements of life")
            # In PDF it appears as "Elements of life (EL)" so search flexibly
            # Look for lines starting with the title
            pattern = rf'^{re.escape(module_name)}\s*(?:\([A-Z]+\))?'
            matches_found = list(re.finditer(pattern, pdf_text, re.IGNORECASE | re.MULTILINE))
            
            if not matches_found:
                # Fallback: search without anchoring to line start
                pattern = re.escape(module_name)
                matches_found = list(re.finditer(pattern, pdf_text, re.IGNORECASE))
            
            if matches_found:
                print(f"[DEBUG] Found {len(matches_found)} occurrences of '{module_name}'")
                # Use the match with the longest following section
                best_match = None
                best_length = 0
                for m in matches_found:
                    # Look for next major heading
                    end_match = re.search(r'(?:Appendix|Version \d|^[A-Z][a-z]+ [a-z]+ [a-z]+\s+\([A-Z]+\))', 
                                         pdf_text[m.start()+500:m.start()+30000], 
                                         re.IGNORECASE | re.MULTILINE)
                    section_len = end_match.start() if end_match else 20000
                    if section_len > best_length:
                        best_length = section_len
                        best_match = m
                
                if best_match and best_length > 100:
                    print(f"[DEBUG] Using section with {best_length} chars")
                    end_pos = best_match.start() + 500 + best_length
                    return pdf_text[best_match.start():min(end_pos, len(pdf_text))]
            
            print(f"[DEBUG] Could not find '{module_name}' in PDF")
        
        # Find ALL occurrences in the PDF
        patterns = [
            rf'Module {module_num}:\s*{re.escape(title_part)}' if title_part else None,
            rf'Module {module_num}\s+–\s+{re.escape(title_part)}' if title_part else None,
            rf'Module {module_num}[:\s]',
            rf'Unit group {module_num}',
            rf'Component\s+{module_num.zfill(2)}:\s*{re.escape(title_part)}' if title_part else None,
            rf'Component\s+{module_num.zfill(2)}',
        ]
        
        matches = []
        for pattern in patterns:
            if pattern:
                for match in re.finditer(pattern, pdf_text, re.IGNORECASE):
                    matches.append(match)
        
        if not matches:
            return None
        
        # Find the match with the LONGEST section after it (skip TOC entries)
        best_match = None
        best_length = 0
        
        for match in matches:
            # Check how much content follows this match
            next_module_num = int(module_num) + 1
            end_patterns = [
                rf'Module {next_module_num}[:\s–]',
                rf'Unit group {next_module_num}',
                r'Appendix',
                r'Assessment',
            ]
            
            end_pos = len(pdf_text)
            for ep in end_patterns:
                end_match = re.search(ep, pdf_text[match.start():], re.IGNORECASE)
                if end_match:
                    end_pos = match.start() + end_match.start()
                    break
            
            section_length = end_pos - match.start()
            if section_length > best_length:
                best_length = section_length
                best_match = match
        
        if not best_match:
            return None
        
        start_pos = best_match.start()
        
        # Find the end - next unit/module or end of content section
        next_module_num = int(module_num) + 1
        end_patterns = [
            rf'Module {next_module_num}[:\s]',
            rf'Unit group {next_module_num}',
            rf'Unit {next_module_num}[:\s]',
            rf'Component {next_module_num}[:\s]',
            r'Appendix',
            r'Assessment',
            r'(?:^|\n)Glossary',
        ]
        
        end_pos = len(pdf_text)
        for pattern in end_patterns:
            match = re.search(pattern, pdf_text[start_pos:], re.IGNORECASE | re.MULTILINE)
            if match:
                end_pos = start_pos + match.start()
                break
        
        # Extract the section
        module_section = pdf_text[start_pos:end_pos]
        
        return module_section
    
    def _extract_chemical_ideas_list(self, section_text: str, parent_code: str, base_level: int) -> List[Dict]:
        """Extract 'The chemical ideas in this module are:' bullet list for Chemistry B."""
        topics = []
        
        # Find the heading
        match = re.search(r'The chemical ideas in this module are:', section_text, re.IGNORECASE)
        if not match:
            return []
        
        # Extract text after this heading
        text_after = section_text[match.end():]
        lines = text_after.split('\n')
        
        for line in lines[:50]:  # Max 50 lines to search
            line = line.strip()
            
            # Stop if we hit another major heading
            if any(stop in line for stop in ['Learning outcomes', 'Assessment', 'Appendix', 'Additional guidance']):
                break
            
            # Check if it's a bullet point (starts with reasonable text, not too short/long)
            if len(line) > 10 and len(line) < 200 and line[0].isupper():
                # This looks like a chemical idea
                topic_num = len(topics) + 1
                topics.append({
                    'code': f'{parent_code}_{topic_num}',
                    'title': line,
                    'level': base_level,
                    'parent': parent_code
                })
        
        return topics
    
    def _extract_module_details_with_ai(self, module_name: str, pdf_text: str, parent_code: str, base_level: int = 1) -> List[Dict]:
        """Use AI to extract detailed sub-topics for a specific module."""
        
        # FIRST: Find the specific module section in the PDF
        module_section = self._find_module_section_in_pdf(module_name, pdf_text, parent_code)
        
        if not module_section:
            print(f"[WARN] Could not find section for {module_name} in PDF")
            return []
        
        print(f"[DEBUG] Extracted {len(module_section)} chars for this module")
        
        # SPECIAL: Chemistry B Salters has "The chemical ideas in this module are:" lists
        if parent_code and 'Storyline' in parent_code:
            chemical_ideas = self._extract_chemical_ideas_list(module_section, parent_code, base_level)
            if chemical_ideas:
                print(f"[OK] Extracted {len(chemical_ideas)} chemical ideas from structured list")
                return chemical_ideas
        
        # Create prompt with ONLY this module's section
        prompt = DETAIL_PROMPT_TEMPLATE.format(
            module_name=module_name,
            pdf_text=module_section[:50000]  # Much smaller, focused text
        )
        
        try:
            # Call AI
            if AI_PROVIDER == "anthropic":
                response = claude.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}]
                )
                ai_output = response.content[0].text
                
            elif AI_PROVIDER == "openai":
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4096,
                    temperature=0
                )
                ai_output = response.choices[0].message.content
                
            elif AI_PROVIDER == "gemini":
                response = gemini_model.generate_content(prompt)
                ai_output = response.text
            
            # Save AI output for debugging
            ai_file = self.debug_dir / f"{parent_code}-ai-details.txt"
            ai_file.write_text(ai_output, encoding='utf-8')
            
            # Parse numbered hierarchy
            details = self._parse_numbered_hierarchy(ai_output, parent_code, base_level)
            
            return details
            
        except Exception as e:
            print(f"[ERROR] AI extraction failed for {module_name}: {e}")
            return []
    
    def _parse_numbered_hierarchy(self, text: str, parent_code: str, base_level: int) -> List[Dict]:
        """Parse AI output into structured topics."""
        topics = []
        # Parent stack maps level -> code at that level
        # Start with the module as level base_level-1
        parent_stack = {base_level - 1: parent_code}
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Match numbered items: 1. Title, 1.1 Title, 1.1.1 Title
            match = re.match(r'^([\d.]+)\s+(.+)$', line)
            if not match:
                continue
            
            number = match.group(1).rstrip('.')
            title = match.group(2).strip()
            
            # Calculate level based on dots
            # "1" = 0 dots -> base_level (1)
            # "1.1" = 1 dot -> base_level + 1 (2)
            # "1.1.1" = 2 dots -> base_level + 2 (3)
            dots = number.count('.')
            level = base_level + dots
            
            # Create code
            code = f"{parent_code}_{number.replace('.', '_')}"
            
            # Find parent (item at level-1)
            parent_code_for_this = parent_stack.get(level - 1, parent_code)
            
            topics.append({
                'code': code,
                'title': title,
                'level': level,
                'parent': parent_code_for_this
            })
            
            # Update parent stack
            parent_stack[level] = code
            
            # Clear deeper levels
            for l in list(parent_stack.keys()):
                if l > level:
                    del parent_stack[l]
        
        return topics
    
    def upload_to_supabase(self, topics: List[Dict]) -> bool:
        """Upload all topics to Supabase with proper hierarchy."""
        print("\n" + "="*80)
        print("UPLOADING TO SUPABASE")
        print("="*80)
        
        # Deduplicate topics by code (keep the one with more detail/higher level)
        seen_codes = {}
        for topic in topics:
            code = topic['code']
            if code not in seen_codes:
                seen_codes[code] = topic
            else:
                # Keep the one with longer title (more detailed)
                if len(topic['title']) > len(seen_codes[code]['title']):
                    seen_codes[code] = topic
        
        topics = list(seen_codes.values())
        print(f"[INFO] After deduplication: {len(topics)} unique topics")
        
        try:
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': f"{self.subject['name']} ({self.subject['qualification']})",
                'subject_code': self.subject['code'],
                'qualification_type': self.subject['qualification'],
                'specification_url': self.subject['pdf_url'],
                'exam_board': self.subject['exam_board']
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            subject_id = subject_result.data[0]['id']
            print(f"[OK] Subject: {subject_result.data[0]['subject_name']} (ID: {subject_id})")
            
            # Clear old topics
            supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
            print("[OK] Cleared old topics")
            
            # Insert topics (without parent links first)
            to_insert = [{
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': t['title'],
                'topic_level': t['level'],
                'exam_board': self.subject['exam_board']
            } for t in topics]
            
            inserted_result = supabase.table('staging_aqa_topics').insert(to_insert).execute()
            print(f"[OK] Uploaded {len(inserted_result.data)} topics")
            
            # Build code -> id mapping
            code_to_id = {t['topic_code']: t['id'] for t in inserted_result.data}
            
            # Link hierarchy
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
            
            print(f"[OK] Linked {linked} parent-child relationships")
            
            # Show hierarchy stats
            levels = {}
            for t in topics:
                levels[t['level']] = levels.get(t['level'], 0) + 1
            
            print("\n[INFO] Hierarchy distribution:")
            for level in sorted(levels.keys()):
                print(f"  Level {level}: {levels[level]} topics")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def scrape(self) -> bool:
        """Main two-stage scraping workflow."""
        print("\n" + "🔬 "*40)
        print(f"OCR SMART SCRAPER: {self.subject['name']} ({self.subject['code']})")
        print("🔬 "*40)
        
        # STAGE 1: HTML scraping for structure
        stage1_topics = self.scrape_stage1_html()
        if not stage1_topics:
            print("[WARN] Stage 1 HTML failed - falling back to PDF-only mode")
            # Fallback: Use PDF with full AI extraction
            all_topics = self.scrape_pdf_only_fallback()
            if not all_topics:
                print("[ERROR] Both Stage 1 and fallback failed")
                return False
            success = self.upload_to_supabase(all_topics)
            return success
        
        # STAGE 2: PDF scraping for details
        all_topics = self.scrape_stage2_pdf(stage1_topics)
        
        if not all_topics:
            print("[ERROR] No topics found")
            return False
        
        # Upload
        success = self.upload_to_supabase(all_topics)
        
        if success:
            print("\n[SUCCESS] ✅ Two-stage scraping complete!")
            print(f"Total topics: {len(all_topics)}")
        else:
            print("\n[FAILED] ❌ Upload failed")
        
        return success
    
    def scrape_pdf_only_fallback(self) -> List[Dict]:
        """Fallback: Scrape entire PDF when HTML fails."""
        print("\n[INFO] PDF-ONLY FALLBACK MODE")
        print("[INFO] Downloading PDF...")
        
        try:
            response = requests.get(self.subject['pdf_url'], timeout=60)
            response.raise_for_status()
            pdf_content = response.content
            print(f"[OK] Downloaded {len(pdf_content)/1024/1024:.1f} MB")
        except Exception as e:
            print(f"[ERROR] PDF download failed: {e}")
            return []
        
        # Extract text
        pdf_text = self._extract_pdf_text(pdf_content)
        if not pdf_text:
            return []
        
        # Use AI to extract ENTIRE structure from PDF
        print("[INFO] Using AI to extract full structure from PDF...")
        
        full_prompt = f"""Extract the complete curriculum structure from this OCR A-Level specification PDF.

Create a hierarchical numbered list of ALL components, modules, topics, and sub-topics.

Use this format:
1. Component/Module Name
1.1 Topic
1.1.1 Sub-topic
1.1.1.1 Detail

Rules:
- Include ALL curriculum content
- Use decimal numbering
- Skip assessment/admin sections
- Start numbering from 1

PDF TEXT:
{pdf_text[:120000]}"""
        
        try:
            if AI_PROVIDER == "anthropic":
                response = claude.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=8192,
                    messages=[{"role": "user", "content": full_prompt}]
                )
                hierarchy = response.content[0].text
            elif AI_PROVIDER == "openai":
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": full_prompt}],
                    max_tokens=8192,
                    temperature=0
                )
                hierarchy = response.choices[0].message.content
            elif AI_PROVIDER == "gemini":
                response = gemini_model.generate_content(full_prompt)
                hierarchy = response.text
            
            print(f"[OK] AI extracted {len(hierarchy)} chars")
            
            # Parse
            topics = self._parse_numbered_hierarchy(hierarchy, parent_code="", base_level=0)
            print(f"[OK] Parsed {len(topics)} topics from full PDF")
            
            return topics
            
        except Exception as e:
            print(f"[ERROR] Fallback failed: {e}")
            return []


# ================================================================
# MAIN
# ================================================================

def load_subjects() -> Dict:
    """Load subjects from JSON."""
    subjects_file = Path(__file__).parent.parent / "ocr-alevel-subjects.json"
    with open(subjects_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='OCR A-Level smart two-stage scraper')
    parser.add_argument('subject', nargs='?', help='Subject code (e.g., AL-BiologyA)')
    parser.add_argument('--all', action='store_true', help='Scrape all subjects')
    args = parser.parse_args()
    
    subjects = load_subjects()
    
    if args.all:
        print(f"\n[INFO] Scraping ALL {len(subjects)} subjects...")
        success_count = 0
        
        for subject_code, subject_info in subjects.items():
            scraper = OCRSmartScraper(subject_info)
            if scraper.scrape():
                success_count += 1
            time.sleep(5)
        
        print(f"\n[SUMMARY] ✅ {success_count}/{len(subjects)} successful")
    
    else:
        subject_code = args.subject
        if not subject_code or subject_code not in subjects:
            print(f"[ERROR] Please specify a valid subject code")
            print(f"Available: {', '.join(subjects.keys())}")
            sys.exit(1)
        
        scraper = OCRSmartScraper(subjects[subject_code])
        success = scraper.scrape()
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

