"""
OCR GCSE Religious Studies (J625) Manual Scraper
=================================================

Extracts topics from OCR GCSE Religious Studies J625 specification.

Structure:
- Level 0: Component Groups (Component Group 1, Component Group 2)
- Level 1: Individual religions/components (all 5 religions for each group)
  * Component Group 1: Christianity (J625/01), Islam (J625/02), Judaism (J625/03), Buddhism (J625/04), Hinduism (J625/05)
  * Component Group 2: Christianity (J625/06), Islam (J625/07), Judaism (J625/08), Buddhism (J625/09), Hinduism (J625/10)
- Level 2+: Detailed content for each religion (beliefs, teachings, practices, themes, etc.)

CRITICAL: 
- DO NOT create "Religious Studies (J625)" as Level 0 - start with Component Groups
- Extract ALL religions/components, not just one - users can choose which ones to study
- Component Group 1: Extract beliefs, teachings, and practices for each religion
- Component Group 2: Extract the four themes (Relationships and families, The existence of God/gods/ultimate reality, Religion/peace/conflict, Dialogue) for each religion
- Extract ALL depth - detailed content, sub-topics, learning objectives

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

PDF_URL = 'https://www.ocr.org.uk/Images/240547-specification-accredited-gcse-religious-studies-j625.pdf'
SUBJECT_CODE = 'J625'
SUBJECT_NAME = 'Religious Studies'

COMPONENT_GROUPS = [
    {
        'code': '1',
        'name': 'Component Group 1: Beliefs and teachings & Practices',
        'section_pattern': r'Content\s+of\s+Beliefs\s+and\s+teachings\s+(?:&|and)\s+Practices|Beliefs\s+and\s+teachings\s+(?:&|and)\s+Practices\s+\(J625/01',
        'religions': [
            {
                'code': '01',
                'name': 'Christianity (J625/01)',
                'pattern': r'Content\s+of\s+Christianity\s+\(J625/01\)|Christianity\s+\(J625/01\)',
            },
            {
                'code': '02',
                'name': 'Islam (J625/02)',
                'pattern': r'Content\s+of\s+Islam\s+\(J625/02\)|Islam\s+\(J625/02\)',
            },
            {
                'code': '03',
                'name': 'Judaism (J625/03)',
                'pattern': r'Content\s+of\s+Judaism\s+\(J625/03\)|Judaism\s+\(J625/03\)',
            },
            {
                'code': '04',
                'name': 'Buddhism (J625/04)',
                'pattern': r'Content\s+of\s+Buddhism\s+\(J625/04\)|Buddhism\s+\(J625/04\)',
            },
            {
                'code': '05',
                'name': 'Hinduism (J625/05)',
                'pattern': r'Content\s+of\s+Hinduism\s+\(J625/05\)|Hinduism\s+\(J625/05\)',
            },
        ]
    },
    {
        'code': '2',
        'name': 'Component Group 2: Religion, philosophy and ethics in the modern world from a religious perspective',
        'section_pattern': r'Content\s+of\s+Religion,\s+philosophy\s+and\s+ethics\s+in\s+the\s+modern\s+world',
        'religions': [
            {
                'code': '06',
                'name': 'Christianity (J625/06)',
                'pattern': r'Content\s+of\s+Christianity\s+\(J625/06\)|Christianity\s+\(J625/06\)',
            },
            {
                'code': '07',
                'name': 'Islam (J625/07)',
                'pattern': r'Content\s+of\s+Islam\s+\(J625/07\)|Islam\s+\(J625/07\)',
            },
            {
                'code': '08',
                'name': 'Judaism (J625/08)',
                'pattern': r'Content\s+of\s+Judaism\s+\(J625/08\)|Judaism\s+\(J625/08\)',
            },
            {
                'code': '09',
                'name': 'Buddhism (J625/09)',
                'pattern': r'Content\s+of\s+Buddhism\s+\(J625/09\)|Buddhism\s+\(J625/09\)',
            },
            {
                'code': '10',
                'name': 'Hinduism (J625/10)',
                'pattern': r'Content\s+of\s+Hinduism\s+\(J625/10\)|Hinduism\s+\(J625/10\)',
            },
        ]
    },
]


class ReligiousStudiesScraper:
    """Scraper for OCR GCSE Religious Studies."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent.parent / "A-Level" / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_text = None
    
    def scrape_all(self):
        """Scrape all topics."""
        print("\n" + "🕊️ "*40)
        print("OCR GCSE RELIGIOUS STUDIES SCRAPER")
        print("🕊️ "*40)
        
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
        
        # Extract each component group
        all_topics = []
        
        for group in COMPONENT_GROUPS:
            print("\n" + "="*80)
            print(f"[EXTRACTING] {group['name']}")
            print("="*80)
            
            # Level 0: Component Group
            group_code = f"{SUBJECT_CODE}_G{group['code']}"
            group_topic = {
                'code': group_code,
                'title': group['name'],
                'level': 0,
                'parent': None
            }
            all_topics.append(group_topic)
            
            # Find group section
            group_section = self._find_group_section(group)
            if not group_section:
                print(f"[WARN] Could not find section for {group['name']}")
                # Still try to extract individual religions
                pass
            
            # Extract each religion in this group
            for religion in group['religions']:
                print(f"\n[EXTRACTING] {religion['name']}")
                
                # Find religion section
                religion_section = self._find_religion_section(religion, group_section, group['code'])
                if not religion_section:
                    print(f"[WARN] Could not find section for {religion['name']}")
                    continue
                
                print(f"[OK] Found religion section: {len(religion_section)} chars")
                
                # Level 1: Religion
                religion_code = f"{group_code}_{religion['code']}"
                religion_topic = {
                    'code': religion_code,
                    'title': religion['name'],
                    'level': 1,
                    'parent': group_code
                }
                all_topics.append(religion_topic)
                
                # Extract content using AI
                print(f"[INFO] Extracting religion content...")
                ai_output = self._extract_with_ai(religion_section, religion_code, religion['name'], group['name'])
                
                if ai_output:
                    # Save AI output for debugging
                    debug_file = self.debug_dir / f"{SUBJECT_CODE}-{group['code']}-{religion['code']}-ai-output.txt"
                    debug_file.write_text(ai_output, encoding='utf-8')
                    print(f"[DEBUG] Saved AI output to {debug_file.name}")
                    
                    parsed = self._parse_hierarchy(ai_output, religion_code)
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
    
    def _find_group_section(self, group: Dict) -> Optional[str]:
        """Find component group section."""
        pattern = group['section_pattern']
        matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE))
        
        if not matches:
            print(f"[DEBUG] No matches for pattern: {pattern}")
            return None
        
        print(f"[DEBUG] Found {len(matches)} matches for group pattern")
        
        # Use first match (group sections are usually unique)
        pos = matches[0].start()
        start_pos = pos
        # Extract large section (300k chars or until next group)
        end_pos = min(start_pos + 300000, len(self.pdf_text))
        
        # Try to find end of group section
        end_patterns = [
            r'\n\s*Content\s+of\s+Religion,\s+philosophy',
            r'\n\s*2c\.\s+Content\s+of\s+Religion',
            r'\n\s*3\.\s+Assessment',
        ]
        
        for end_pattern in end_patterns:
            end_match = re.search(end_pattern, self.pdf_text[start_pos:start_pos + 300000], re.IGNORECASE)
            if end_match:
                end_pos = start_pos + end_match.start()
                print(f"[DEBUG] Found end pattern at position {end_pos}")
                break
        
        content = self.pdf_text[start_pos:end_pos]
        print(f"[DEBUG] Extracted {len(content)} chars for group")
        return content
    
    def _find_religion_section(self, religion: Dict, group_section: Optional[str], group_code: str) -> Optional[str]:
        """Find religion section within group section or full PDF."""
        pattern = religion['pattern']
        
        # First try within group section
        search_text = group_section if group_section else self.pdf_text
        matches = list(re.finditer(pattern, search_text, re.IGNORECASE))
        
        if not matches:
            # Fallback: search full PDF
            print(f"[DEBUG] No matches in group section, searching full PDF...")
            matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE))
        
        if not matches:
            print(f"[DEBUG] No matches for pattern: {pattern}")
            return None
        
        print(f"[DEBUG] Found {len(matches)} matches for religion pattern")
        
        # Determine which component codes belong to this group
        if group_code == '1':
            # Component Group 1: codes 01-05
            same_group_codes = ['01', '02', '03', '04', '05']
            exclude_patterns = [
                r'\n\s*Content\s+of\s+Religion,\s+philosophy',  # Component Group 2
            ]
        else:
            # Component Group 2: codes 06-10
            same_group_codes = ['06', '07', '08', '09', '10']
            exclude_patterns = [
                r'\n\s*Content\s+of\s+Beliefs\s+and\s+teachings',  # Component Group 1
            ]
        
        # Find actual content (not TOC entry)
        for match in matches:
            pos = match.start()
            after_text = self.pdf_text[pos:pos + 5000]
            before_text = self.pdf_text[max(0, pos - 200):pos]
            
            # Check if TOC entry (has page number immediately before or after)
            if re.search(r'\d+\s*$', before_text[-50:]) or re.search(r'^\d+', after_text[:50]):
                print(f"[DEBUG] Skipping TOC entry at position {pos}")
                continue
            
            # Check if actual content (has descriptive text or section structure)
            if re.search(r'Beliefs|Teachings|Practices|Theme|Content|Learners|This\s+component', after_text, re.IGNORECASE):
                print(f"[DEBUG] Found actual content at position {pos}")
                # Extract section (150k chars or until next religion in same group)
                start_pos = pos
                end_patterns = [
                    r'\n\s*Content\s+of\s+(?:Christianity|Islam|Judaism|Buddhism|Hinduism)\s+\(J625/(\d{2})\)',
                ]
                
                end_pos = min(start_pos + 150000, len(self.pdf_text))
                for end_pattern in end_patterns:
                    end_match = re.search(end_pattern, self.pdf_text[start_pos:start_pos + 150000], re.IGNORECASE)
                    if end_match:
                        match_start = start_pos + end_match.start()
                        match_text = self.pdf_text[match_start:match_start + 150]
                        # Extract the component code from the match
                        code_match = re.search(r'J625/(\d{2})', match_text)
                        if code_match:
                            found_code = code_match.group(1)
                            # Only end if it's a different religion in the SAME component group
                            if found_code in same_group_codes and found_code != religion['code']:
                                end_pos = match_start
                                print(f"[DEBUG] Found end pattern (next religion in same group) at position {end_pos}")
                                break
                
                # Also check for Component Group boundaries (but only if we haven't found a same-group religion)
                if end_pos == min(start_pos + 150000, len(self.pdf_text)):
                    for exclude_pattern in exclude_patterns:
                        exclude_match = re.search(exclude_pattern, self.pdf_text[start_pos:start_pos + 150000], re.IGNORECASE)
                        if exclude_match:
                            end_pos = start_pos + exclude_match.start()
                            print(f"[DEBUG] Found Component Group boundary at position {end_pos}")
                            break
                
                content = self.pdf_text[start_pos:end_pos]
                print(f"[DEBUG] Extracted {len(content)} chars for religion")
                return content
        
        # Fallback: use last match if no content found
        if matches:
            print(f"[DEBUG] Using fallback: last match")
            pos = matches[-1].start()
            start_pos = pos
            end_pos = min(start_pos + 150000, len(self.pdf_text))
            return self.pdf_text[start_pos:end_pos]
        
        return None
    
    def _extract_with_ai(self, text: str, parent_code: str, religion_name: str, group_name: str) -> Optional[str]:
        """Extract content using AI."""
        # Limit text size
        text = text[:200000]  # 200k chars max
        
        # Determine content type based on group
        if 'Group 1' in group_name or 'Beliefs and teachings' in group_name:
            content_type = "beliefs, teachings, and practices"
            structure_guide = """
   Level 2: Areas of study from the "Area of study" column (e.g., "Nature of God", "Life after death", "Worship", "Festivals")
   Level 3: Content items from the "Content" column
     * Extract ALL specific content points, terms, concepts, beliefs, teachings, and practices
     * Each distinct content item becomes a Level 3 topic (e.g., "The meaning of the terms: benevolent", "The meaning of the terms: omniscient", "The Trinity: Father, Son, and Holy Spirit")
     * Extract ALL bullet points and learning objectives from the Content column
   Level 4: Suggested sources of wisdom and authority from the "Suggested sources" column
     * Extract ALL sources listed in the "Suggested sources of wisdom and authority" column
     * Each source becomes a separate Level 4 item (e.g., "The Lord's Prayer Matthew 6:9-15", "The Ten Commandments Exodus 20", "The Parable of the Lost Son Luke 15:11-32")
     * These sources are CRITICAL and must be extracted - they support the Area of study
     * Link sources to their corresponding Area of study (Level 2)"""
        else:
            content_type = "four themes: Relationships and families, The existence of God/gods/ultimate reality, Religion/peace/conflict, Dialogue between religious and non-religious beliefs"
            structure_guide = """
   Level 2: Themes (e.g., "Relationships and families", "The existence of God, gods and the ultimate reality", "Religion, peace and conflict", "Dialogue between religious and non-religious beliefs and attitudes")
   Level 3: Sub-topics/Areas of study within each theme
   Level 4: Specific content points, arguments, perspectives, learning objectives, and suggested sources
     * Extract ALL specific arguments (e.g., "The cosmological argument", "The design argument")
     * Extract ALL perspectives (religious and non-religious)
     * Extract ALL detailed content points and learning objectives
     * Extract ALL suggested sources of wisdom and authority if present"""
        
        prompt = f"""Extract content from OCR GCSE Religious Studies specification for {religion_name}.

COMPONENT GROUP: {group_name}
RELIGION: {religion_name}
PARENT CODE: {parent_code}

CRITICAL REQUIREMENTS:
1. Extract ONLY content that is ACTUALLY PRESENT in the PDF text below
2. DO NOT generate, extrapolate, invent, or create variations
3. If you see "benevolent, omniscient, omnipotent" - extract those specific terms only, NOT hundreds of variations
4. STOP when you finish extracting all actual content - DO NOT continue generating
5. If you find yourself creating similar patterns with different words, STOP - you are hallucinating

EXTRACTION METHOD:
   PREFERRED: Look for tables with columns:
   - "Area of study" (or similar)
   - "Content" (or similar)  
   - "Suggested sources of wisdom and authority" (or similar)
   
   If tables found:
   - Level 2: Extract each "Area of study" from table rows (number as "1.", "2.", "3.", etc.)
   - Level 3: Extract each distinct item from the "Content" column (number as "1.1.", "1.2.", "1.3.", etc. - children of Level 2)
   - Level 4: Extract each source from the "Suggested sources" column (number as "1.1.1.", "1.1.2.", "1.1.3.", etc. - children of Level 2)
     * CRITICAL: Use 3-part numbering for Level 4 (X.Y.Z format)
     * After extracting all Level 3 items for an Area of study, extract all Level 4 sources for that same Area of study
     * Use the FIRST Level 3 number (1.1) as the base for Level 4 numbering (1.1.1, 1.1.2, etc.)
   
   If NO tables found, look for structured content sections:
   - Level 2: Extract main topic headings (e.g., "Nature of God", "Life after death")
   - Level 3: Extract content items listed under each topic
   - Level 4: Extract suggested sources if listed
   
   IMPORTANT: Extract ONLY what is explicitly written - DO NOT add variations or synonyms

4. OUTPUT FORMAT: Numbered hierarchy (NOT markdown)
   CRITICAL: Use numbered format ONLY, NOT markdown headers (### or ####)
   CRITICAL: Extract ALL content - don't skip any!
   
   Format (Component Group 1 example):
   1. Level 2 Area of study (e.g., "Nature of God")
   1.1. Level 3 Content item (e.g., "The meaning of the terms: benevolent")
   1.2. Level 3 Content item (e.g., "The meaning of the terms: omniscient")
   1.3. Level 3 Content item (e.g., "The meaning of the terms: omnipotent")
   1.4. Level 3 Content item (e.g., "The meaning of the terms: monotheistic")
   ... (continue all Level 3 content items)
   1.10. Level 3 Content item (e.g., "The meaning of the terms: forgiving")
   1.1.1. Level 4 Suggested source (e.g., "The Lord's Prayer Matthew 6:9-15")
   1.1.2. Level 4 Suggested source (e.g., "The Ten Commandments Exodus 20")
   1.1.3. Level 4 Suggested source (e.g., "The Parable of the Lost Son Luke 15:11-32")
   2. Level 2 Area of study (e.g., "Life after death")
   2.1. Level 3 Content item
   2.1.1. Level 4 Suggested source
   (continue for ALL areas of study, content items, and suggested sources)
   
   CRITICAL NUMBERING RULES:
   - Level 2 (Area of study): Use 1-part numbering (1., 2., 3., etc.)
   - Level 3 (Content items): Use 2-part numbering (1.1., 1.2., 1.3., etc.) - children of Level 2
   - Level 4 (Suggested sources): Use 3-part numbering (1.1.1., 1.1.2., 1.1.3., etc.) - children of Level 2
   - DO NOT create Level 5 or deeper - maximum depth is Level 4
   - Suggested sources are children of the Area of study (Level 2), numbered after all Level 3 content items
   - After extracting all Level 3 items for an Area of study, then extract all Level 4 sources for that same Area of study
   - DO NOT reuse numbering - if you have sub-items like "1.6.1.", "1.6.2.", then sources should be "1.1.1.", "1.1.2." (not "1.6.1." again)
   
   Format (Component Group 2 example):
   1. Level 2 Theme (e.g., "Relationships and families")
   1.1. Level 3 Sub-topic/Area of study (e.g., "Sexual relationships")
   1.1.1. Level 4 Content point (e.g., "Christian views on sexual relationships before marriage")
   1.1.2. Level 4 Suggested source (if present)
   2. Level 2 Theme
   (continue for ALL themes and content with FULL depth)
   
   IMPORTANT: 
   - Extract ALL areas of study/themes within the religion
   - Extract ALL content items from the "Content" column as Level 3
   - Extract ALL suggested sources from the "Suggested sources of wisdom and authority" column as Level 4
   - Suggested sources are CRITICAL - they must be extracted!
   - Link suggested sources to their corresponding Area of study (Level 2)
   - For Component Group 1: Extract from tables with "Area of study", "Content", and "Suggested sources" columns
   - For Component Group 2: Extract all four themes with full depth
   
   DO NOT use:
   - ### or #### headers
   - Bullet points with dashes
   - Markdown formatting
   
   USE ONLY:
   - Numbered format: "1.", "1.1.", "1.1.1.", "1.1.1.1.", etc.

5. TABLE STRUCTURE (Component Group 1):
   The PDF contains tables with three columns:
   - "Area of study": Contains topic names (e.g., "Nature of God", "Life after death")
   - "Content": Contains learning objectives, terms, concepts, beliefs, teachings, practices
   - "Suggested sources of wisdom and authority": Contains biblical references, religious texts, etc.
   
   CRITICAL FOR TABLES:
   - Extract each "Area of study" as Level 2
   - Extract each content item from the "Content" column as Level 3
   - Extract each source from the "Suggested sources" column as Level 4
   - Suggested sources apply to the entire Area of study row - link them to Level 2
   - DO NOT skip the "Suggested sources" column - it's very important!

6. CONTENT TYPE:
   This component covers {content_type}.
   Extract ALL related content with full depth, including ALL suggested sources, but ONLY what is actually in the PDF.

7. ANTI-HALLUCINATION RULES - CRITICAL:
   - Extract ONLY what is explicitly written in the PDF text below
   - Extract content EXACTLY as written - do not paraphrase, expand, or create variations
   - If content lists "benevolent, omniscient, omnipotent" - extract ONLY those specific terms
   - DO NOT create "The concept of God as a [word]" for every word you can think of
   - DO NOT generate synonyms, variations, or related concepts
   - COUNT the actual topics/sections - extract ONLY that many Level 2 topics
   - When you finish extracting all actual content, STOP immediately
   - If output exceeds 200 topics, you are likely hallucinating - STOP and review
   - If you cannot find any content in the text below, return empty output (do not generate)

8. EXAMPLE - CORRECT EXTRACTION:
   Table row 1:
   Area of study: "Nature of God"
   Content: "The meaning of the terms: benevolent, omniscient, omnipotent, monotheistic, judge, eternal, transcendent, immanent, personal, forgiving"
   Suggested sources: "The Lord's Prayer Matthew 6:9-15", "The Ten Commandments Exodus 20"
   
   CORRECT output:
   1. Nature of God
   1.1. The meaning of the terms: benevolent
   1.2. The meaning of the terms: omniscient
   1.3. The meaning of the terms: omnipotent
   1.4. The meaning of the terms: monotheistic
   1.5. The meaning of the terms: judge
   1.6. The meaning of the terms: eternal
   1.7. The meaning of the terms: transcendent
   1.8. The meaning of the terms: immanent
   1.9. The meaning of the terms: personal
   1.10. The meaning of the terms: forgiving
   1.1.1. The Lord's Prayer Matthew 6:9-15
   1.1.2. The Ten Commandments Exodus 20
   1.1.3. The Parable of the Lost Son Luke 15:11-32
   
   NOTE: Suggested sources (1.1.1, 1.1.2, 1.1.3) are Level 4, numbered as children of the Area of study (1.)
   
   WRONG output (hallucination):
   - Creating 1000+ variations like "The concept of God as a creator", "The concept of God as a maker", etc.
   - STOP after extracting all table rows - do not continue

9. EXTRACTION PROCESS:
   Step 1: Find all tables in the PDF text
   Step 2: For each table, count the rows
   Step 3: Extract row by row - one Level 2 topic per row
   Step 4: Extract Content cell items as Level 3 (number as 1.1, 1.2, 1.3, etc.)
   Step 5: Extract Suggested sources as Level 4 (number as 1.1.1, 1.1.2, 1.1.3, etc. - children of Level 2)
   Step 6: CRITICAL - Suggested sources must use 3-part numbering (X.Y.Z) to be Level 4, NOT 2-part (X.Y)
   Step 7: STOP when all table rows are extracted

10. IF NO CONTENT FOUND:
   If the PDF text below does not contain any tables or structured content for {religion_name}, 
   return empty output. DO NOT generate content that is not in the text.

11. DO NOT ask for confirmation. Extract ONLY actual content from the PDF text below NOW.

CONTENT:
{text}

Extract the complete hierarchy now:"""

        return self._call_ai(prompt, max_tokens=16000)
    
    def _parse_hierarchy(self, text: str, base_code: str) -> List[Dict]:
        """Parse AI numbered output (handles both numbered and markdown formats)."""
        all_topics = []
        parent_stack = {0: base_code}  # Level 1 is base_code
        
        # Filter out subject-level topics
        excluded_patterns = [
            r'^religious\s+studies\s+\(j625\)$',
            r'^religious\s+studies$',
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
            
            # Handle markdown headers: ### Level 2, #### Level 3
            markdown_match = re.match(r'^#{3,4}\s+(\d+(?:\.\d+)*)\.?\s+(.+)$', line)
            if markdown_match:
                number_str = markdown_match.group(1)
                title = markdown_match.group(2).strip()
                parts = number_str.split('.')
                level = len(parts) + 1  # +1 because Level 1 is already base_code
                
                # Find parent
                parent_level = level - 1
                parent_code = parent_stack.get(parent_level, base_code)
                
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
            
            # Handle bullet points with numbers: "- 1.1. Title"
            bullet_match = re.match(r'^[-•]\s+(\d+(?:\.\d+)*)\.\s+(.+)$', line)
            if bullet_match:
                number_str = bullet_match.group(1)
                title = bullet_match.group(2).strip()
                parts = number_str.split('.')
                level = len(parts) + 1  # +1 because Level 1 is already base_code
                
                # Find parent
                parent_level = level - 1
                parent_code = parent_stack.get(parent_level, base_code)
                
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
                level = len(parts) + 1  # +1 because Level 1 is already base_code
                
                # Cap at Level 4 - don't create Level 5+
                if level > 4:
                    level = 4
                    # Use the last 3 parts for Level 4
                    if len(parts) > 3:
                        parts = parts[-3:]
                
                # Find parent
                parent_level = level - 1
                parent_code = parent_stack.get(parent_level, base_code)
                
                # Generate code
                if parent_code:
                    topic_code = f"{parent_code}_{parts[-1]}"
                else:
                    topic_code = f"{base_code}_{parts[0]}"
                
                # Check for duplicates - if code already exists, append suffix
                existing_codes = {t['code'] for t in all_topics}
                original_code = topic_code
                suffix = 1
                while topic_code in existing_codes:
                    topic_code = f"{original_code}_dup{suffix}"
                    suffix += 1
                    if suffix > 100:  # Safety limit
                        print(f"[WARN] Too many duplicates for {original_code}, using last attempt")
                        break
                
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
            total_batches = (len(to_insert) + batch_size - 1) // batch_size
            
            for i in range(0, len(to_insert), batch_size):
                batch = to_insert[i:i + batch_size]
                try:
                    inserted = supabase.table('staging_aqa_topics').insert(batch).execute()
                    all_inserted.extend(inserted.data)
                    batch_num = i//batch_size + 1
                    if batch_num % 10 == 0 or batch_num == total_batches:
                        print(f"[INFO] Inserted batch {batch_num}/{total_batches} ({len(batch)} topics)")
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
    scraper = ReligiousStudiesScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)

