"""
OCR GCSE Media Studies (J200) Manual Scraper
============================================

Extracts topics from OCR GCSE Media Studies J200 specification.

Structure:
- Level 0: Components (Component 01, Component 02, Component 03/04)
- Level 1: Sections (Section A, Section B) for Components 01 and 02
- Level 2: Media forms or theoretical framework areas (e.g., "Television", "Film", "Media language", "Media representations")
- Level 3+: Set products, detailed content, learning objectives

CRITICAL: 
- DO NOT create "Media Studies (J200)" as Level 0 - start with Components
- Component 01 has Section A (Television) and Section B (Promoting Media)
- Component 02 has Section A (Music) and Section B (The News)
- Component 03/04 is Creating media (NEA)
- Extract ALL set products and theoretical framework content
- Extract ALL learning objectives and detailed content

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-media-studies-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/687701-specification-accredited-gcse-media-studies-j200.pdf'
SUBJECT_CODE = 'J200'
SUBJECT_NAME = 'Media Studies'

COMPONENTS = [
    {
        'code': '01',
        'name': 'Component 01: Television and promoting media',
        'section_pattern': r'Content\s+of\s+Television\s+and\s+promoting\s+media\s+\(01\)',
        'sections': [
            {
                'code': 'A',
                'name': 'Section A: Television',
                'pattern': r'Section\s+A:\s+Television',
            },
            {
                'code': 'B',
                'name': 'Section B: Promoting Media',
                'pattern': r'Section\s+B:\s+Promoting\s+Media',
            },
        ]
    },
    {
        'code': '02',
        'name': 'Component 02: Music and news',
        'section_pattern': r'Content\s+of\s+Music\s+and\s+news\s+\(02\)',
        'sections': [
            {
                'code': 'A',
                'name': 'Section A: Music',
                'pattern': r'Section\s+A:\s+Music',
            },
            {
                'code': 'B',
                'name': 'Section B: The News',
                'pattern': r'Section\s+B:\s+[Tt]he\s+News',
            },
        ]
    },
    {
        'code': '03',
        'name': 'Component 03/04: Creating media',
        'section_pattern': r'Content\s+of\s+non-exam\s+assessment\s+content\s+-\s+Creating\s+media\s+\(03/04\)',
        'sections': [
            {
                'code': 'NEA',
                'name': 'Creating media',
                'pattern': r'Creating\s+media',
            },
        ]
    },
]


class MediaStudiesScraper:
    """Scraper for OCR GCSE Media Studies."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent.parent / "A-Level" / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_text = None
    
    def scrape_all(self):
        """Scrape all topics."""
        print("\n" + "📺 "*40)
        print("OCR GCSE MEDIA STUDIES SCRAPER")
        print("📺 "*40)
        
        # Download PDF
        print(f"\n[INFO] Downloading PDF from {PDF_URL}...")
        pdf_content = self._download_pdf(PDF_URL)
        if not pdf_content:
            print("[ERROR] Failed to download PDF")
            return False
        
        # Extract PDF text
        print("[INFO] Extracting PDF text...")
        self.pdf_text = self._extract_pdf_text(pdf_content)
        if not self.pdf_text:
            print("[ERROR] Failed to extract PDF text")
            return False
        
        print(f"[OK] Extracted {len(self.pdf_text)} characters from PDF")
        
        # Initialize topics list
        all_topics = []
        
        # Extract subject content table (theoretical framework) first
        print("\n" + "="*80)
        print("[EXTRACTING] Subject Content (Theoretical Framework)")
        print("="*80)
        
        subject_content = self._find_subject_content_table()
        if subject_content:
            print(f"[OK] Found subject content table: {len(subject_content)} chars")
            # Extract theoretical framework topics
            framework_code = f"{SUBJECT_CODE}_FRAMEWORK"
            framework_topic = {
                'code': framework_code,
                'title': 'Theoretical Framework',
                'level': 0,
                'parent': None
            }
            all_topics.append(framework_topic)
            
            ai_output = self._extract_framework_with_ai(subject_content, framework_code)
            if ai_output:
                debug_file = self.debug_dir / f"{SUBJECT_CODE}-FRAMEWORK-ai-output.txt"
                debug_file.write_text(ai_output, encoding='utf-8')
                parsed = self._parse_hierarchy(ai_output, framework_code)
                all_topics.extend(parsed)
                print(f"[OK] Extracted {len(parsed)} framework topics")
        else:
            print("[WARN] Could not find subject content table")
        
        # Extract each component
        for component in COMPONENTS:
            print("\n" + "="*80)
            print(f"[EXTRACTING] {component['name']}")
            print("="*80)
            
            # Find component section
            component_section = self._find_component_section(component)
            if not component_section:
                print(f"[WARN] Could not find section for {component['name']}")
                continue
            
            print(f"[OK] Found component section: {len(component_section)} chars")
            
            # Level 0: Component
            component_code = f"{SUBJECT_CODE}_{component['code']}"
            component_topic = {
                'code': component_code,
                'title': component['name'],
                'level': 0,
                'parent': None
            }
            all_topics.append(component_topic)
            
            # Extract each section in this component
            for section in component['sections']:
                print(f"\n[EXTRACTING] {section['name']}")
                
                # Find section content
                section_content = self._find_section_content(section, component_section)
                if not section_content:
                    print(f"[WARN] Could not find section content for {section['name']}")
                    continue
                
                print(f"[OK] Found section content: {len(section_content)} chars")
                
                # Level 1: Section
                section_code = f"{component_code}_{section['code']}"
                section_topic = {
                    'code': section_code,
                    'title': section['name'],
                    'level': 1,
                    'parent': component_code
                }
                all_topics.append(section_topic)
                
                # Extract content using AI
                print(f"[INFO] Extracting section content...")
                ai_output = self._extract_with_ai(section_content, section_code, section['name'], component['name'])
                
                if ai_output:
                    # Save AI output for debugging
                    safe_name = re.sub(r'[^\w\s-]', '', section['name'])[:50]
                    debug_file = self.debug_dir / f"{SUBJECT_CODE}-{component['code']}-{section['code']}-ai-output.txt"
                    debug_file.write_text(ai_output, encoding='utf-8')
                    print(f"[DEBUG] Saved AI output to {debug_file.name}")
                    
                    parsed = self._parse_hierarchy(ai_output, section_code)
                    all_topics.extend(parsed)
                    print(f"[OK] Extracted {len(parsed)} topics")
                else:
                    print("[WARN] AI extraction failed")
        
        print(f"\n[OK] Extracted {len(all_topics)} topics total")
        
        # Count by level
        level_counts = {}
        for t in all_topics:
            level = t['level']
            level_counts[level] = level_counts.get(level, 0) + 1
        
        print("\n[INFO] Topic distribution by level:")
        for level in sorted(level_counts.keys()):
            print(f"  Level {level}: {level_counts[level]} topics")
        
        # Upload to database
        print("\n[INFO] Uploading to database...")
        success = self._upload_topics(all_topics)
        
        if success:
            print(f"\n[OK] ✓ Successfully uploaded {len(all_topics)} topics")
        else:
            print(f"\n[FAIL] ✗ Failed to upload topics")
        
        return success
    
    def _find_component_section(self, component: Dict) -> Optional[str]:
        """Find component section."""
        pattern = component['section_pattern']
        matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE))
        
        if not matches:
            print(f"[DEBUG] No matches for pattern: {pattern}")
            return None
        
        print(f"[DEBUG] Found {len(matches)} matches for component pattern")
        
        # Find actual content (not TOC entry)
        for match in matches:
            pos = match.start()
            after_text = self.pdf_text[pos:pos + 3000]
            before_text = self.pdf_text[max(0, pos - 200):pos]
            
            # Check if TOC entry (has page number immediately before or after)
            if re.search(r'\d+\s*$', before_text[-50:]) or re.search(r'^\d+', after_text[:50]):
                print(f"[DEBUG] Skipping TOC entry at position {pos}")
                continue
            
            # Check if actual content (has descriptive text)
            if re.search(r'Section\s+[AB]:|Learners|Media|Television|Music|News|This\s+section|consists|in-depth|study', after_text, re.IGNORECASE):
                print(f"[DEBUG] Found actual content at position {pos}")
                # Extract large section (300k chars or until next component)
                start_pos = pos
                end_patterns = [
                    r'\n\s*2d\.\s+Content\s+of\s+Music\s+and\s+news',
                    r'\n\s*2e\.\s+Content\s+of\s+non-exam\s+assessment',
                    r'\n\s*Content\s+of\s+Creating\s+media',
                    r'\n\s*2f\.\s+Prior\s+knowledge',
                    r'\n\s*3\.\s+Assessment',
                ]
                
                end_pos = min(start_pos + 300000, len(self.pdf_text))
                for end_pattern in end_patterns:
                    end_match = re.search(end_pattern, self.pdf_text[start_pos:start_pos + 300000], re.IGNORECASE)
                    if end_match:
                        end_pos = start_pos + end_match.start()
                        print(f"[DEBUG] Found end pattern at position {end_pos}")
                        break
                
                content = self.pdf_text[start_pos:end_pos]
                print(f"[DEBUG] Extracted {len(content)} chars for component")
                return content
        
        # Fallback: use last match if no content found
        if matches:
            print(f"[DEBUG] Using fallback: last match")
            pos = matches[-1].start()
            start_pos = pos
            end_pos = min(start_pos + 300000, len(self.pdf_text))
            return self.pdf_text[start_pos:end_pos]
        
        return None
    
    def _find_section_content(self, section: Dict, component_section: Optional[str]) -> Optional[str]:
        """Find section content within component section."""
        search_text = component_section if component_section else self.pdf_text
        pattern = section['pattern']
        matches = list(re.finditer(pattern, search_text, re.IGNORECASE))
        
        if not matches:
            print(f"[DEBUG] No matches for section pattern: {pattern}")
            # Try searching full PDF if not found in component section
            if component_section:
                print(f"[DEBUG] Trying full PDF search for section: {section['name']}")
                full_matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE))
                if full_matches:
                    print(f"[DEBUG] Found {len(full_matches)} matches in full PDF")
                    search_text = self.pdf_text
                    matches = full_matches
                else:
                    return None
            else:
                return None
        
        print(f"[DEBUG] Found {len(matches)} matches for section pattern")
        
        # Find actual content (not TOC entry)
        for match in matches:
            pos = match.start()
            after_text = search_text[pos:pos + 5000]  # Increased to 5000 for better detection
            before_text = search_text[max(0, pos - 200):pos]
            
            # Check if TOC entry (has page number immediately before or after)
            if re.search(r'\d+\s*$', before_text[-50:]) or re.search(r'^\d+', after_text[:50]):
                print(f"[DEBUG] Skipping TOC entry at position {pos}")
                continue
            
            # Check if actual content (has descriptive text or table structure)
            if re.search(r'Learners|Media|Television|Music|News|Vigil|Avengers|Lego|Magazines|Radio|Observer|Creating|This\s+section|consists|in-depth|study|table|Set\s+Media|Media\s+Form', after_text, re.IGNORECASE):
                print(f"[DEBUG] Found actual content at position {pos}")
                # Extract section (200k chars or until next section)
                start_pos = pos
                end_patterns = [
                    r'\n\s*Section\s+A:\s+[^T]',  # Section A but not "The News"
                    r'\n\s*Section\s+B:\s+',
                    r'\n\s*2d\.\s+Content\s+of\s+Music',
                    r'\n\s*2e\.\s+Content\s+of\s+non-exam',
                    r'\n\s*Content\s+of\s+Creating\s+media',
                    r'\n\s*2f\.\s+Prior',
                    r'\n\s*3\.\s+Assessment',
                ]
                
                end_pos = min(start_pos + 200000, len(search_text))
                for end_pattern in end_patterns:
                    end_match = re.search(end_pattern, search_text[start_pos:start_pos + 200000], re.IGNORECASE)
                    if end_match:
                        end_pos = start_pos + end_match.start()
                        print(f"[DEBUG] Found end pattern at position {end_pos}")
                        break
                
                content = search_text[start_pos:end_pos]
                print(f"[DEBUG] Extracted {len(content)} chars for section")
                if len(content) < 100:
                    print(f"[WARN] Content too short ({len(content)} chars), skipping")
                    continue
                return content
        
        # Fallback: use last match if no content found
        if matches:
            print(f"[DEBUG] Using fallback: last match for section")
            pos = matches[-1].start()
            start_pos = pos
            end_pos = min(start_pos + 200000, len(search_text))
            content = search_text[start_pos:end_pos]
            if len(content) < 100:
                print(f"[WARN] Fallback content too short ({len(content)} chars)")
                return None
            return content
        
        return None
    
    def _find_subject_content_table(self) -> Optional[str]:
        """Find the subject content table (theoretical framework)."""
        # Look for "In Component 01, learners will develop knowledge" or similar
        patterns = [
            r'In\s+Component\s+01,\s+learners\s+will\s+develop',
            r'Topic\s+Key\s+idea\s+Learners\s+must',
            r'Media\s+language\s+Media\s+language\s+elements',
        ]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE))
            if matches:
                for match in matches:
                    pos = match.start()
                    # Extract large section (100k chars or until next major section)
                    start_pos = pos
                    end_patterns = [
                        r'\n\s*2c\.\s+Content\s+of\s+Television',
                        r'\n\s*2d\.\s+Content\s+of\s+Music',
                        r'\n\s*2e\.\s+Content\s+of\s+non-exam',
                        r'\n\s*2f\.\s+Prior',
                        r'\n\s*3\.\s+Assessment',
                    ]
                    
                    end_pos = min(start_pos + 100000, len(self.pdf_text))
                    for end_pattern in end_patterns:
                        end_match = re.search(end_pattern, self.pdf_text[start_pos:start_pos + 100000], re.IGNORECASE)
                        if end_match:
                            end_pos = start_pos + end_match.start()
                            break
                    
                    content = self.pdf_text[start_pos:end_pos]
                    if len(content) > 1000:  # Must be substantial
                        return content
        
        return None
    
    def _extract_framework_with_ai(self, text: str, parent_code: str) -> Optional[str]:
        """Extract theoretical framework content."""
        text = text[:150000]  # 150k chars max
        
        prompt = f"""Extract the complete topic hierarchy from this OCR GCSE Media Studies subject content table (theoretical framework).

PARENT CODE: {parent_code}

CRITICAL REQUIREMENTS:
1. Extract from the table with columns: "Topic", "Key idea", "Learners must demonstrate and apply their knowledge and understanding of:"
2. Extract ALL topics: Media language, Media representations, Media industries, Media audiences
3. Extract ALL key ideas under each topic
4. Extract ALL learning objectives from the "Learners must..." column

STRUCTURE REQUIREMENTS:
   Level 1: Topics (Media language, Media representations, Media industries, Media audiences)
   Level 2: Key ideas (e.g., "Media language elements", "Media language and meaning", "Genre", "Narrative")
   Level 3: Learning objectives (each bullet point from "Learners must..." column)
   Level 4: Theoretical perspectives (if mentioned, e.g., "Propp", "semiotic analysis")

OUTPUT FORMAT: Numbered hierarchy ONLY (NOT markdown)
   1. Media language
   1.1. Media language elements
   1.1.1. the various forms of media language used to create and communicate meanings in media products
   1.1.2. fundamental principles of semiotic analysis, including denotation and connotation
   1.2. Media language and meaning
   1.2.1. how choice (selection, combination and exclusion) of elements of media language influences meaning...
   (continue for ALL topics with FULL depth)

Extract EVERYTHING from the table now:

{text}"""

        return self._call_ai(prompt, max_tokens=16000)
    
    def _extract_with_ai(self, text: str, parent_code: str, section_name: str, component_name: str) -> Optional[str]:
        """Extract content using AI."""
        # Limit text size
        text = text[:200000]  # 200k chars max
        
        prompt = f"""Extract the complete topic hierarchy from this OCR GCSE Media Studies specification section.

COMPONENT: {component_name}
SECTION: {section_name}
PARENT CODE: {parent_code}

CRITICAL REQUIREMENTS:
1. DO NOT create "Media Studies (J200)" or subject name as Level 0 - components are Level 0, sections are Level 1
2. Extract ALL content with FULL depth - don't skip any topics, media forms, set products, or learning objectives

3. STRUCTURE REQUIREMENTS:
   Level 2: Media forms or theoretical framework areas (e.g., "Television", "Film", "Advertising and marketing", "Video games", "Magazines", "Music video", "Radio", "Online, social and participatory media", "Newspapers", "Media language", "Media representations", "Media industries", "Media audiences")
   Level 3: Set products or sub-topics (e.g., "Vigil", "The Avengers", "The Lego Movie", "MOJO Magazine", "The Observer")
   Level 4: Detailed content, learning objectives, theoretical perspectives, contexts
   Level 5+: Further detail, specific points, examples

4. OUTPUT FORMAT: Numbered hierarchy (NOT markdown)
   CRITICAL: Use numbered format ONLY, NOT markdown headers (### or ####)
   CRITICAL: Extract EVERYTHING - don't skip any content!
   
   Format:
   1. Level 2 Media Form or Topic (e.g., "Television" or "Media language")
   1.1. Level 3 Set Product or Sub-topic (e.g., "Vigil" or "Media language elements")
   1.1.1. Level 4 Detail (e.g., learning objectives, theoretical perspectives)
   1.1.1.1. Level 5 Further detail (if applicable)
   1.2. Level 3 Set Product or Sub-topic (e.g., "The Avengers")
   1.2.1. Level 4 Detail
   2. Level 2 Media Form (e.g., "Film")
   2.1. Level 3 Set Product (e.g., "The Lego Movie")
   2.1.1. Level 4 Detail
   (continue for ALL media forms, set products, and content with FULL depth)
   
   IMPORTANT: 
   - Extract ALL media forms mentioned in the section
   - Extract ALL set products (e.g., Vigil, The Avengers, The Lego Movie, MOJO Magazine, etc.)
   - Extract ALL theoretical framework areas (Media language, Media representations, Media industries, Media audiences)
   - Extract ALL learning objectives and detailed content points
   - Extract ALL contexts (Social, Cultural, Historical, Political)
   - Don't skip any levels or content!
   
   DO NOT use:
   - ### or #### headers
   - Bullet points with dashes
   - Markdown formatting
   
   USE ONLY:
   - Numbered format: "1.", "1.1.", "1.1.1.", "1.1.1.1.", etc.

5. SET PRODUCTS EXTRACTION:
   - Extract ALL set products mentioned (e.g., "Vigil Series 1, Episode 1", "The Avengers Series 4, Episode 2", "The Lego Movie", "MOJO Magazine", "The Observer")
   - Extract which theoretical framework areas apply to each product
   - Extract which contexts apply to each product

6. THEORETICAL FRAMEWORK EXTRACTION:
   - Extract Media language, Media representations, Media industries, Media audiences
   - Extract theoretical perspectives (e.g., semiotic analysis, genre theory, narrative theory, Uses and Gratifications)
   - Extract learning objectives under each area

7. CONTEXTS EXTRACTION:
   - Extract Social, Cultural, Historical, Political contexts
   - Extract how contexts relate to set products

8. DO NOT ask for confirmation. Extract EVERYTHING NOW.

CONTENT:
{text}

Extract the complete hierarchy now:"""

        return self._call_ai(prompt, max_tokens=16000)
    
    def _parse_hierarchy(self, text: str, base_code: str) -> List[Dict]:
        """Parse AI numbered output (handles both numbered and markdown formats)."""
        all_topics = []
        parent_stack = {-1: None}
        
        # Filter out subject-level topics
        excluded_patterns = [
            r'^media\s+studies\s+\(j200\)$',
            r'^media\s+studies$',
            r'^subject:',
        ]
        
        lines = text.split('\n')
        for line in lines:
            original_line = line
            line = line.strip()
            if not line:
                continue
            
            # Check if excluded
            excluded = False
            for pattern in excluded_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    excluded = True
                    break
            
            if excluded:
                continue
            
            # Handle markdown headers: ### Level 1, #### Level 2
            markdown_match = re.match(r'^#{3,4}\s+(\d+(?:\.\d+)*)\.?\s+(.+)$', line)
            if markdown_match:
                number_str = markdown_match.group(1)
                title = markdown_match.group(2).strip()
                parts = number_str.split('.')
                level = len(parts) + 1  # Add 1 because sections are Level 1
                
                # Find parent
                parent_level = level - 1
                parent_code = parent_stack.get(parent_level)
                
                # If Level 2 and no parent found, use base_code
                if level == 2 and parent_code is None:
                    parent_code = base_code
                
                # Generate code
                if parent_code:
                    topic_code = f"{parent_code}_{parts[-1]}"
                else:
                    topic_code = f"{base_code}_{parts[0]}"
                
                topic = {
                    'code': topic_code,
                    'title': title,
                    'level': level,
                    'parent': parent_code
                }
                
                all_topics.append(topic)
                parent_stack[level] = topic_code
                continue
            
            # Handle bullet points with numbers: "- 1.1.1. Title"
            bullet_match = re.match(r'^[-•]\s+(\d+(?:\.\d+)*)\.\s+(.+)$', line)
            if bullet_match:
                number_str = bullet_match.group(1)
                title = bullet_match.group(2).strip()
                parts = number_str.split('.')
                level = len(parts) + 1  # Add 1 because sections are Level 1
                
                # Find parent
                parent_level = level - 1
                parent_code = parent_stack.get(parent_level)
                
                # If Level 2 and no parent found, use base_code
                if level == 2 and parent_code is None:
                    parent_code = base_code
                
                # Generate code
                if parent_code:
                    topic_code = f"{parent_code}_{parts[-1]}"
                else:
                    topic_code = f"{base_code}_{parts[0]}"
                
                topic = {
                    'code': topic_code,
                    'title': title,
                    'level': level,
                    'parent': parent_code
                }
                
                all_topics.append(topic)
                parent_stack[level] = topic_code
                continue
            
            # Handle regular numbered format: "1. Title" or "1.1. Title" or "1.1.1. Title"
            match = re.match(r'^(\d+(?:\.\d+)*)\.\s+(.+)$', line)
            if match:
                number_str = match.group(1)
                title = match.group(2).strip()
                parts = number_str.split('.')
                level = len(parts) + 1  # Add 1 because sections are Level 1
                
                # Find parent
                parent_level = level - 1
                parent_code = parent_stack.get(parent_level)
                
                # If Level 2 and no parent found, use base_code
                if level == 2 and parent_code is None:
                    parent_code = base_code
                
                # Generate code
                if parent_code:
                    topic_code = f"{parent_code}_{parts[-1]}"
                else:
                    topic_code = f"{base_code}_{parts[0]}"
                
                topic = {
                    'code': topic_code,
                    'title': title,
                    'level': level,
                    'parent': parent_code
                }
                
                all_topics.append(topic)
                parent_stack[level] = topic_code
        
        return all_topics
    
    def _call_ai(self, prompt: str, max_tokens: int = 16000) -> Optional[str]:
        """Call AI API."""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if AI_PROVIDER == "openai":
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens,
                        temperature=0,
                        timeout=240
                    )
                    return response.choices[0].message.content
                else:  # anthropic
                    response = claude.messages.create(
                        model="claude-3-5-haiku-20241022",
                        max_tokens=min(max_tokens, 8192),
                        messages=[{"role": "user", "content": prompt}],
                        timeout=240
                    )
                    return response.content[0].text
            except Exception as e:
                wait_time = (attempt + 1) * 5
                print(f"[WARN] AI call failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"[INFO] Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print("[ERROR] All AI retries failed")
                    return None
        
        return None
    
    def _download_pdf(self, url: str) -> Optional[bytes]:
        """Download PDF from URL."""
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            if response.content[:4] == b'%PDF':
                print(f"[OK] Downloaded PDF: {len(response.content)/1024/1024:.1f} MB")
                return response.content
            else:
                print("[ERROR] Downloaded content is not a PDF")
                return None
        except Exception as e:
            print(f"[ERROR] Download failed: {e}")
            return None
    
    def _extract_pdf_text(self, pdf_content: bytes) -> Optional[str]:
        """Extract text from PDF."""
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
            
            pdf_text = "\n".join(page_texts)
            print(f"[OK] Extracted {len(pdf_text)} chars from {len(page_texts)} pages")
            return pdf_text
        except Exception as e:
            print(f"[ERROR] PDF extraction failed: {e}")
            return None
    
    def _upload_topics(self, topics: List[Dict]) -> bool:
        """Upload topics to database."""
        if not topics:
            print("[WARN] No topics to upload")
            return False
        
        try:
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': f"{SUBJECT_NAME} (GCSE)",
                'subject_code': SUBJECT_CODE,
                'qualification_type': 'GCSE',
                'specification_url': PDF_URL,
                'exam_board': 'OCR'
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            subject_id = subject_result.data[0]['id']
            
            # Clear old topics for this subject
            print("[INFO] Clearing old topics...")
            supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).eq('exam_board', 'OCR').execute()
            
            # Remove duplicates and check for issues
            seen_codes = set()
            unique_topics = []
            duplicate_codes = []
            for t in topics:
                if t['code'] not in seen_codes:
                    seen_codes.add(t['code'])
                    unique_topics.append(t)
                else:
                    duplicate_codes.append(t['code'])
            
            if duplicate_codes:
                print(f"[WARN] Found {len(duplicate_codes)} duplicate codes: {duplicate_codes[:10]}")
            
            print(f"[INFO] After deduplication: {len(unique_topics)} unique topics from {len(topics)} total")
            
            # Insert topics in batches to catch errors
            to_insert = [{
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': t['title'],
                'topic_level': t['level'],
                'exam_board': 'OCR'
            } for t in unique_topics]
            
            print(f"[INFO] Attempting to insert {len(to_insert)} topics...")
            
            # Insert in batches to catch errors
            batch_size = 50
            all_inserted = []
            failed_items = []
            
            for i in range(0, len(to_insert), batch_size):
                batch = to_insert[i:i + batch_size]
                try:
                    inserted = supabase.table('staging_aqa_topics').insert(batch).execute()
                    all_inserted.extend(inserted.data)
                    print(f"[INFO] Inserted batch {i//batch_size + 1} ({len(batch)} topics)")
                except Exception as e:
                    print(f"[ERROR] Batch {i//batch_size + 1} failed: {e}")
                    # Try inserting one by one to find the problem
                    for item in batch:
                        try:
                            single_insert = supabase.table('staging_aqa_topics').insert([item]).execute()
                            all_inserted.extend(single_insert.data)
                        except Exception as e2:
                            print(f"[ERROR] Failed to insert topic {item['topic_code']} ({item['topic_name'][:50]}): {e2}")
                            failed_items.append(item)
            
            print(f"[INFO] Successfully inserted {len(all_inserted)} topics, {len(failed_items)} failed")
            if failed_items:
                print(f"[DEBUG] Failed topics: {[item['topic_code'] for item in failed_items[:10]]}")
            
            # Link hierarchy
            code_to_id = {t['topic_code']: t['id'] for t in all_inserted}
            linked_count = 0
            failed_links = 0
            
            for topic in unique_topics:
                if topic['parent']:
                    parent_id = code_to_id.get(topic['parent'])
                    child_id = code_to_id.get(topic['code'])
                    if parent_id and child_id:
                        try:
                            supabase.table('staging_aqa_topics').update({
                                'parent_topic_id': parent_id
                            }).eq('id', child_id).execute()
                            linked_count += 1
                        except Exception as e:
                            print(f"[WARN] Failed to link {topic['code']} to {topic['parent']}: {e}")
                            failed_links += 1
                    elif not parent_id:
                        print(f"[WARN] Parent {topic['parent']} not found for {topic['code']}")
                        failed_links += 1
            
            print(f"[INFO] Linked {linked_count} parent-child relationships, {failed_links} failed")
            print(f"[OK] Successfully uploaded {len(all_inserted)} topics")
            return True
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    scraper = MediaStudiesScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)

