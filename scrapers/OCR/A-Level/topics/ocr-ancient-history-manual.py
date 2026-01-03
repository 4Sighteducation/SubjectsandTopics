"""
OCR A-Level Ancient History Manual Structure Scraper
=====================================================

APPROACH:
1. Manually define Level 0 (Component Groups) and Level 1 (Depth Studies)
2. Scrape PDF to extract Level 2+ (Time periods, content details)

This replaces the two-stage HTML+PDF approach for subjects where we manually 
have the overview structure already.

Requirements:
    pip install requests pdfplumber anthropic openai

Usage:
    python ocr-ancient-history-manual.py
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

# Determine AI provider - PREFER OPENAI (works best for this task)
AI_PROVIDER = None

if openai_key:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=openai_key)
        AI_PROVIDER = "openai"
        print("[INFO] Using OpenAI GPT-4 API (preferred)")
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

if not AI_PROVIDER and gemini_key:
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        gemini_model = genai.GenerativeModel('gemini-1.5-pro')
        AI_PROVIDER = "gemini"
        print("[INFO] Using Google Gemini API")
    except ImportError:
        pass

if not AI_PROVIDER:
    print("[ERROR] No AI API keys found! Need one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI2.5_API_KEY")
    sys.exit(1)


# ================================================================
# MANUAL STRUCTURE DEFINITION
# ================================================================

SUBJECT_INFO = {
    'name': 'Ancient History',
    'code': 'H407',
    'qualification': 'A-Level',
    'exam_board': 'OCR',
    'pdf_url': 'https://www.ocr.org.uk/Images/313570-specification-accredited-a-level-ancient-history-h407.pdf'
}

# MANUAL STRUCTURE: Level 0 and Level 1
MANUAL_STRUCTURE = [
    # Component Group 1: Greek History
    {
        'code': 'ComponentGroup1',
        'title': 'Component group 1: Greek history',
        'level': 0,
        'parent': None,
        'children': [
            # COMPULSORY Period Study
            {
                'code': 'ComponentGroup1_Period',
                'title': 'Relations between Greek states and between Greek and non-Greek states, 492–404 BC',
                'level': 1,
                'parent': 'ComponentGroup1'
            },
            # DEPTH STUDIES (choose one)
            {
                'code': 'ComponentGroup1_Depth1',
                'title': 'The Society and Politics of Sparta, 478–404 BC',
                'level': 1,
                'parent': 'ComponentGroup1'
            },
            {
                'code': 'ComponentGroup1_Depth2',
                'title': 'The Culture and Politics of Athens, c.460–399 BC',
                'level': 1,
                'parent': 'ComponentGroup1'
            },
            {
                'code': 'ComponentGroup1_Depth3',
                'title': 'The Rise of Macedon, 359–323 BC',
                'level': 1,
                'parent': 'ComponentGroup1'
            }
        ]
    },
    # Component Group 2: Roman History
    {
        'code': 'ComponentGroup2',
        'title': 'Component group 2: Roman history',
        'level': 0,
        'parent': None,
        'children': [
            # COMPULSORY Period Study
            {
                'code': 'ComponentGroup2_Period',
                'title': 'The Julio-Claudian Emperors, 31 BC–AD 68',
                'level': 1,
                'parent': 'ComponentGroup2'
            },
            # DEPTH STUDIES (choose one)
            {
                'code': 'ComponentGroup2_Depth1',
                'title': 'The breakdown of the Late Republic, 88–31 BC',
                'level': 1,
                'parent': 'ComponentGroup2'
            },
            {
                'code': 'ComponentGroup2_Depth2',
                'title': 'The Flavians, AD 68–96',
                'level': 1,
                'parent': 'ComponentGroup2'
            },
            {
                'code': 'ComponentGroup2_Depth3',
                'title': 'Ruling Roman Britain, AD 43–c.128',
                'level': 1,
                'parent': 'ComponentGroup2'
            }
        ]
    }
]


# ================================================================
# AI EXTRACTION PROMPT
# ================================================================

DETAIL_PROMPT_TEMPLATE = """Extract the content from this OCR A-Level Ancient History specification section.

TOPIC: "{topic_name}"

The PDF has a table with this structure:
- Header row: "Key time spans | Learners should have studied the following content:"
- Multiple data rows, each with:
  - LEFT COLUMN: Time period name + date range (e.g., "The challenge of the Persian Empire 492–479")
  - RIGHT COLUMN: Long paragraph of learning content, with points separated by semicolons

YOUR TASK:
1. Extract each time period row from the table
2. For each row:
   - Level 1: Time period name + dates (from left column)
   - Level 2: Split the right column content by semicolons, each becomes a separate item

OUTPUT FORMAT (numbered list):
1. The challenge of the Persian Empire 492–479
1.1 Mardonius' expedition of 492 BC
1.2 Persian approaches to the Greek states
1.3 the Battle of Marathon
1.4 Greek and Persian strategy
1.5 the threat of Greek medising
(continue for all semicolon-separated points)
2. Greece in conflict 479–446 BC
2.1 The consequences of victory for the Greek states
2.2 especially relations between Sparta and Athens
(continue...)

CRITICAL RULES:
- Start numbering from 1
- Time periods = level 1 (1, 2, 3, etc.)
- Content points = level 2 (1.1, 1.2, 2.1, etc.)
- Split the long paragraphs by semicolons to get individual learning points
- Include the date range with each time period title
- Extract ALL rows from the table

PDF SECTION:
{pdf_text}"""


# ================================================================
# SCRAPER CLASS
# ================================================================

class AncientHistoryScraper:
    """Manual structure + PDF detail scraper for Ancient History."""
    
    def __init__(self):
        self.subject = SUBJECT_INFO
        self.manual_topics = []
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
    
    def build_manual_structure(self) -> List[Dict]:
        """Build the manual Level 0 and Level 1 structure."""
        print("\n" + "="*80)
        print("STEP 1: Building Manual Structure (Levels 0-1)")
        print("="*80)
        
        topics = []
        
        for component in MANUAL_STRUCTURE:
            # Add Level 0 component
            topics.append({
                'code': component['code'],
                'title': component['title'],
                'level': component['level'],
                'parent': component['parent']
            })
            print(f"[L0] {component['code']}: {component['title']}")
            
            # Add Level 1 children
            for child in component.get('children', []):
                topics.append({
                    'code': child['code'],
                    'title': child['title'],
                    'level': child['level'],
                    'parent': child['parent']
                })
                print(f"  [L1] {child['code']}: {child['title']}")
        
        print(f"\n[OK] Manual structure: {len(topics)} topics (2 L0 + {len(topics)-2} L1)")
        return topics
    
    def scrape_pdf_details(self, manual_topics: List[Dict]) -> List[Dict]:
        """Download PDF and extract Level 2+ details for each L1 topic."""
        print("\n" + "="*80)
        print("STEP 2: Scraping PDF for Detailed Time Periods (Level 2+)")
        print("="*80)
        
        # Download PDF
        print(f"[INFO] Downloading PDF from {self.subject['pdf_url']}...")
        try:
            response = requests.get(self.subject['pdf_url'], timeout=60)
            response.raise_for_status()
            pdf_content = response.content
            print(f"[OK] Downloaded {len(pdf_content)/1024/1024:.1f} MB")
        except Exception as e:
            print(f"[ERROR] PDF download failed: {e}")
            print(f"[WARN] Continuing with manual structure only")
            return manual_topics
        
        # Extract PDF text
        pdf_text = self._extract_pdf_text(pdf_content)
        if not pdf_text:
            print("[ERROR] Could not extract PDF text")
            return manual_topics
        
        # Process each Level 1 topic
        all_topics = manual_topics.copy()
        l1_topics = [t for t in manual_topics if t['level'] == 1]
        
        for topic in l1_topics:
            print(f"\n[INFO] Processing: {topic['title']}")
            
            # Extract details with AI
            details = self._extract_topic_details_with_ai(
                topic_name=topic['title'],
                pdf_text=pdf_text,
                parent_code=topic['code'],
                base_level=2  # Start from Level 2
            )
            
            if details:
                print(f"[OK] Found {len(details)} items for {topic['code']}")
                all_topics.extend(details)
            else:
                print(f"[WARN] No details found for {topic['code']}")
            
            time.sleep(1)  # Be nice to API
        
        print(f"\n[OK] Total topics after PDF scraping: {len(all_topics)}")
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
                    if i % 20 == 0 and i > 0:
                        print(f"[INFO] Processed {i+1}/{len(pdf.pages)} pages...")
            
            print(f"[OK] Extracted {len(text)} characters from {len(pdf.pages)} pages")
            
            # Save debug copy
            debug_file = self.debug_dir / f"{self.subject['code']}-spec.txt"
            debug_file.write_text(text, encoding='utf-8')
            print(f"[DEBUG] Saved PDF text to {debug_file.name}")
            
            return text
            
        except ImportError:
            print("[ERROR] pdfplumber not installed. Run: pip install pdfplumber")
            return None
        except Exception as e:
            print(f"[ERROR] PDF extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _find_topic_section_in_pdf(self, topic_name: str, pdf_text: str) -> Optional[str]:
        """Find and extract the section for a specific topic from the PDF."""
        
        # For the PERIOD study, search for "Relations between Greek states"
        # For DEPTH studies, search for the actual title
        
        # Build search patterns
        search_terms = []
        if 'Relations between Greek states' in topic_name:
            search_terms = [
                'Relations between Greek states and between Greek and non-Greek states',
                'Relations between Greek states'
            ]
        elif 'Julio-Claudian' in topic_name:
            search_terms = [
                'The Julio-Claudian Emperors',
                'Julio-Claudian Emperors'
            ]
        elif 'Society and Politics of Sparta' in topic_name:
            search_terms = [
                'The Society and Politics of Sparta',
                'Society and Politics of Sparta'
            ]
        elif 'Culture and Politics of Athens' in topic_name:
            search_terms = [
                'The Culture and Politics of Athens',
                'Culture and Politics of Athens'
            ]
        elif 'Rise of Macedon' in topic_name:
            search_terms = [
                'The Rise of Macedon',
                'Rise of Macedon'
            ]
        elif 'breakdown of the Late Republic' in topic_name:
            search_terms = [
                'The Breakdown of the Late Republic',
                'Breakdown of the Late Republic'
            ]
        elif 'Flavians' in topic_name:
            search_terms = [
                'The Flavians'
            ]
        elif 'Ruling Roman Britain' in topic_name:
            search_terms = [
                'Ruling Roman Britain'
            ]
        else:
            search_terms = [topic_name]
        
        # Find best match
        best_section = None
        best_length = 0
        
        for search_term in search_terms:
            matches = []
            # Look for the heading followed by either "Key time spans" OR "Key topics"
            # Try both patterns
            patterns = [
                rf'{re.escape(search_term)}[^\n]*\n[^\n]*\nKey time spans',
                rf'{re.escape(search_term)}[^\n]*\n[^\n]*\nKey topics',
                # Also try with more flexible spacing
                rf'{re.escape(search_term)}.*?Key time spans',
                rf'{re.escape(search_term)}.*?Key topics'
            ]
            
            for pattern in patterns:
                for match in re.finditer(pattern, pdf_text, re.IGNORECASE | re.DOTALL):
                    matches.append(match)
            
            for match in matches:
                start_pos = match.start()
                
                # Find end: next depth/period study or version marker
                end_patterns = [
                    r'\nDepth study in H407',  # Next depth study
                    r'Version \d+\.\d+',
                    r'Ancient source material',
                    r'\n3 Assessment'  # Assessment section
                ]
                
                end_pos = len(pdf_text)
                for ep in end_patterns:
                    end_match = re.search(ep, pdf_text[start_pos + 500:start_pos + 30000], re.IGNORECASE)
                    if end_match:
                        end_pos = start_pos + 500 + end_match.start()
                        break
                
                section = pdf_text[start_pos:end_pos]
                if len(section) > best_length:
                    best_length = len(section)
                    best_section = section
        
        if best_section and best_length > 300:
            print(f"[DEBUG] Extracted section: {best_length} characters")
            return best_section
        
        print(f"[WARN] Could not find content table for '{topic_name}'")
        return None
    
    def _parse_table_directly(self, section_text: str, parent_code: str, base_level: int = 2) -> List[Dict]:
        """Parse the 'Key time spans' table directly from the PDF text."""
        topics = []
        
        # Find "Key time spans" table start
        table_match = re.search(r'Key time spans\s+Learners should have studied the following content:', section_text, re.IGNORECASE)
        if not table_match:
            print("[WARN] Could not find 'Key time spans' table")
            return []
        
        # Extract text after the table header
        table_text = section_text[table_match.end():]
        
        # Save for debugging
        safe_filename = re.sub(r'[^\w\-]', '_', parent_code)
        debug_file = self.debug_dir / f"{safe_filename}-table.txt"
        debug_file.write_text(table_text[:5000], encoding='utf-8')
        
        # The table has rows with:
        # - Time period name (e.g., "The challenge of the Persian Empire")
        # - Date range (e.g., "492–479")
        # - Content (long paragraph with semicolon-separated points)
        
        # Pattern: Look for lines that are likely time period names
        # They typically:
        # - Start with capital letter or "The"
        # - Are relatively short (not full sentences)
        # - Are followed by a date range or content
        
        # Split into lines and process
        lines = table_text.split('\n')
        
        current_period = None
        current_period_code = None
        current_content = []
        period_counter = 1
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Stop at version markers or next major section
            if re.match(r'Version \d+\.\d+', line) or 'Ancient source material' in line:
                break
            
            if not line or len(line) < 3:
                continue
            
            # Check if this looks like a time period name
            # Characteristics: Short, starts with capital or "The", not a number, not too long
            is_period_name = (
                len(line) < 80 and
                (line[0].isupper() or line.startswith('The')) and
                not re.match(r'^\d', line) and
                not line.endswith(';') and
                'should' not in line.lower() and
                'learners' not in line.lower()
            )
            
            # Check if this is a date range (e.g., "492–479" or "31 BC–AD 14")
            is_date_range = bool(re.match(r'^\d+\s*(?:BC)?(?:–|-)(?:AD)?\s*\d+', line))
            
            # If we see a date range after collecting some content, finalize the previous period
            if is_date_range and current_period and current_content:
                # Create Level 2 topic for the time period
                period_code = f"{parent_code}_{period_counter}"
                topics.append({
                    'code': period_code,
                    'title': f"{current_period} {line}",  # e.g., "The challenge of the Persian Empire 492-479"
                    'level': base_level,
                    'parent': parent_code
                })
                
                # Split content by semicolons for Level 3
                full_content = ' '.join(current_content)
                content_points = [p.strip() for p in full_content.split(';') if p.strip() and len(p.strip()) > 10]
                
                for j, point in enumerate(content_points, 1):
                    topics.append({
                        'code': f"{period_code}_{j}",
                        'title': point,
                        'level': base_level + 1,
                        'parent': period_code
                    })
                
                print(f"[DEBUG] Period: {current_period} {line} ({len(content_points)} content points)")
                
                # Reset
                current_period = None
                current_content = []
                period_counter += 1
                continue
            
            # If this looks like a period name
            if is_period_name and not is_date_range:
                # Save previous period if exists
                if current_period and current_content:
                    period_code = f"{parent_code}_{period_counter}"
                    topics.append({
                        'code': period_code,
                        'title': current_period,
                        'level': base_level,
                        'parent': parent_code
                    })
                    
                    full_content = ' '.join(current_content)
                    content_points = [p.strip() for p in full_content.split(';') if p.strip() and len(p.strip()) > 10]
                    
                    for j, point in enumerate(content_points, 1):
                        topics.append({
                            'code': f"{period_code}_{j}",
                            'title': point,
                            'level': base_level + 1,
                            'parent': period_code
                        })
                    
                    print(f"[DEBUG] Period: {current_period} ({len(content_points)} content points)")
                    period_counter += 1
                
                # Start new period
                current_period = line
                current_content = []
            else:
                # This is content - add to current period
                if current_period:
                    current_content.append(line)
        
        # Don't forget the last period
        if current_period and current_content:
            period_code = f"{parent_code}_{period_counter}"
            topics.append({
                'code': period_code,
                'title': current_period,
                'level': base_level,
                'parent': parent_code
            })
            
            full_content = ' '.join(current_content)
            content_points = [p.strip() for p in full_content.split(';') if p.strip() and len(p.strip()) > 10]
            
            for j, point in enumerate(content_points, 1):
                topics.append({
                    'code': f"{period_code}_{j}",
                    'title': point,
                    'level': base_level + 1,
                    'parent': period_code
                })
            
            print(f"[DEBUG] Period: {current_period} ({len(content_points)} content points)")
        
        return topics
    
    def _extract_topic_details_with_ai(self, topic_name: str, pdf_text: str, parent_code: str, base_level: int = 2) -> List[Dict]:
        """Extract detailed content for a specific topic - uses appropriate method based on format."""
        
        # Find the specific section in the PDF
        section_text = self._find_topic_section_in_pdf(topic_name, pdf_text)
        
        if not section_text:
            return []
        
        # Save section for debugging
        safe_filename = re.sub(r'[^\w\-]', '_', parent_code)
        section_file = self.debug_dir / f"{safe_filename}-section.txt"
        section_file.write_text(section_text[:10000], encoding='utf-8')
        print(f"[DEBUG] Saved section to {section_file.name}")
        
        # DETECT FORMAT: Does it have "Key time spans" or "Key topics"?
        has_time_spans = 'Key time spans' in section_text
        has_key_topics = 'Key topics' in section_text
        
        if has_time_spans:
            print(f"[INFO] Detected 'Key time spans' table - using AI extraction")
            return self._extract_time_spans_with_ai(section_text, topic_name, parent_code, base_level)
        elif has_key_topics:
            print(f"[INFO] Detected 'Key topics' section - using AI extraction")
            return self._extract_key_topics_with_ai(section_text, topic_name, parent_code, base_level)
        else:
            print(f"[WARN] Unknown format - trying AI")
            return self._extract_key_topics_with_ai(section_text, topic_name, parent_code, base_level)
    
    def _extract_time_spans_with_ai(self, section_text: str, topic_name: str, parent_code: str, base_level: int) -> List[Dict]:
        """Use AI to extract 'Key time spans' format content."""
        
        # Prompt specifically for time spans table
        prompt = f"""Extract content from this OCR A-Level Ancient History period study section.

TOPIC: "{topic_name}"

This section has a 2-column table:
- Header: "Key time spans | Learners should have studied the following content:"
- LEFT column has time period names + date ranges
- RIGHT column has learning content (semicolon-separated points)

EXAMPLE from the PDF:
Row 1:
- LEFT: "The challenge of the Persian Empire 492–479"
- RIGHT: "Mardonius' expedition of 492 BC; Persian approaches to the Greek states; the Battle of Marathon; Greek and Persian strategy; the threat of Greek medising; Sparta's response..."

Row 2:
- LEFT: "Greece in conflict 479–446 BC"
- RIGHT: "The consequences of victory for the Greek states, especially relations between Sparta and Athens; the growth of Athenian power in the Delian League..."

OUTPUT FORMAT (numbered list):
1. The challenge of the Persian Empire 492–479
1.1 Mardonius' expedition of 492 BC
1.2 Persian approaches to the Greek states
1.3 the Battle of Marathon
1.4 Greek and Persian strategy
1.5 the threat of Greek medising
1.6 Sparta's response
(continue for ALL semicolon-separated points from right column)
2. Greece in conflict 479–446 BC
2.1 The consequences of victory for the Greek states
2.2 especially relations between Sparta and Athens
2.3 the growth of Athenian power in the Delian League
2.4 Sparta's concerns
(continue...)

CRITICAL RULES:
- Extract the FULL time period name + dates from the LEFT column (e.g., "The challenge of the Persian Empire 492–479")
- Split the RIGHT column content by semicolons
- Each semicolon-separated phrase becomes a separate numbered item
- Time periods = Level 1 (1, 2, 3...)
- Content points = Level 2 (1.1, 1.2, 2.1, 2.2...)
- Start numbering from 1
- Include ALL rows from the table

SECTION TEXT:
{section_text[:50000]}"""
        
        safe_filename = re.sub(r'[^\w\-]', '_', parent_code)
        
        try:
            # Call AI
            if AI_PROVIDER == "anthropic":
                response = claude.messages.create(
                    model="claude-3-5-haiku-20241022",  # Using Haiku - faster and cheaper
                    max_tokens=8192,  # More tokens for comprehensive extraction
                    messages=[{"role": "user", "content": prompt}]
                )
                ai_output = response.content[0].text
                
            elif AI_PROVIDER == "openai":
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=16000,  # Generous token limit for comprehensive extraction
                    temperature=0
                )
                ai_output = response.choices[0].message.content
                
            elif AI_PROVIDER == "gemini":
                response = gemini_model.generate_content(prompt)
                ai_output = response.text
            
            # Save AI output
            ai_file = self.debug_dir / f"{safe_filename}-ai-output.txt"
            ai_file.write_text(ai_output, encoding='utf-8')
            print(f"[DEBUG] Saved AI output to {ai_file.name}")
            
            # Parse numbered hierarchy
            details = self._parse_numbered_hierarchy(ai_output, parent_code, base_level)
            
            return details
            
        except Exception as e:
            print(f"[ERROR] AI extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_key_topics_with_ai(self, section_text: str, topic_name: str, parent_code: str, base_level: int) -> List[Dict]:
        """Use AI to extract 'Key topics' format content."""
        
        # Different prompt for Key topics format
        prompt = f"""Extract the content from this OCR A-Level Ancient History depth study section.

TOPIC: "{topic_name}"

This section has "Key topics" (not time spans). The format is:
- LEFT COLUMN: Topic names (e.g., "Education in Sparta", "The social structure of Sparta")
- RIGHT COLUMN: Detailed content for each topic (semicolon-separated learning points)

YOUR TASK:
1. Extract each topic row
2. For each topic:
   - Level 1: Topic name
   - Level 2: Split the content by semicolons into individual learning points

OUTPUT FORMAT (numbered list):
1. Education in Sparta
1.1 The education of boys and men
1.2 including details of the organisation and content of the agoge
1.3 the education of girls
1.4 the values the agoge was intended to develop in the Spartans
2. The social structure of Sparta
2.1 The different status, roles and contributions of Spartiates, perioikoi and helots
2.2 the effect the helots had on Spartan policy
(continue...)

CRITICAL RULES:
- Start numbering from 1
- Topics = level 1 (1, 2, 3, etc.)
- Content points = level 2 (1.1, 1.2, 2.1, etc.)
- Split long paragraphs by semicolons
- Extract ALL topics from the section

SECTION TEXT:
{section_text[:50000]}"""
        
        safe_filename = re.sub(r'[^\w\-]', '_', parent_code)
        
        try:
            # Call AI
            if AI_PROVIDER == "anthropic":
                response = claude.messages.create(
                    model="claude-3-5-haiku-20241022",  # Using Haiku
                    max_tokens=8192,
                    messages=[{"role": "user", "content": prompt}]
                )
                ai_output = response.content[0].text
                
            elif AI_PROVIDER == "openai":
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=16000,  # Generous token limit for comprehensive extraction
                    temperature=0
                )
                ai_output = response.choices[0].message.content
                
            elif AI_PROVIDER == "gemini":
                response = gemini_model.generate_content(prompt)
                ai_output = response.text
            
            # Save AI output
            ai_file = self.debug_dir / f"{safe_filename}-ai-output.txt"
            ai_file.write_text(ai_output, encoding='utf-8')
            print(f"[DEBUG] Saved AI output to {ai_file.name}")
            
            # Parse numbered hierarchy
            details = self._parse_numbered_hierarchy(ai_output, parent_code, base_level)
            
            return details
            
        except Exception as e:
            print(f"[ERROR] AI extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_numbered_hierarchy(self, text: str, parent_code: str, base_level: int) -> List[Dict]:
        """Parse AI output into structured topics."""
        topics = []
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
            
            # Skip if title is too short (likely noise)
            if len(title) < 3:
                continue
            
            # Calculate level based on dots
            dots = number.count('.')
            level = base_level + dots
            
            # Create code
            code = f"{parent_code}_{number.replace('.', '_')}"
            
            # Find parent
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
        print("STEP 3: Uploading to Supabase")
        print("="*80)
        
        # Deduplicate
        seen_codes = {}
        for topic in topics:
            code = topic['code']
            if code not in seen_codes:
                seen_codes[code] = topic
            else:
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
            
            # Insert topics
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
        """Main scraping workflow."""
        print("\n" + "🏛️ "*40)
        print(f"OCR ANCIENT HISTORY MANUAL SCRAPER: {self.subject['name']} ({self.subject['code']})")
        print("🏛️ "*40)
        
        # Step 1: Build manual structure
        manual_topics = self.build_manual_structure()
        
        # Step 2: Scrape PDF for details
        all_topics = self.scrape_pdf_details(manual_topics)
        
        if not all_topics:
            print("[ERROR] No topics found")
            return False
        
        # Step 3: Upload
        success = self.upload_to_supabase(all_topics)
        
        if success:
            print("\n[SUCCESS] ✅ Ancient History scraping complete!")
            print(f"Total topics: {len(all_topics)}")
        else:
            print("\n[FAILED] ❌ Upload failed")
        
        return success


# ================================================================
# MAIN
# ================================================================

def main():
    scraper = AncientHistoryScraper()
    success = scraper.scrape()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

