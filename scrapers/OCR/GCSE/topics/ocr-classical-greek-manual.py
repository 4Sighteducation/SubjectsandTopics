"""
OCR GCSE Classical Greek (J292) Manual Scraper
==============================================

Extracts topics from OCR GCSE Classical Greek J292 specification.

Structure:
- Level 0: Language (J292/01)
- Level 0: Prose Literature and Verse Literature
  - Level 1: Prose Literature A (J292/02)
  - Level 1: Prose Literature B (J292/03)
  - Level 1: Verse Literature A (J292/04)
  - Level 1: Verse Literature B (J292/05)
- Level 0: Literature and Culture (J292/06)

CRITICAL: 
- Filter out assessment/admin sections ("Forms of assessment", "Assessment objectives", "Admin: what you need to know", "Appendices")
- Extract detailed language content from Appendix 5d (Classical Greek Accidence and Syntax) and Appendix 5e (Restricted list)
- Language component should include all accidence and syntax details

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-classical-greek-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/220700-specification-accredited-gcse-classical-greek-j292.pdf'
SUBJECT_CODE = 'J292'
SUBJECT_NAME = 'Classical Greek'


class ClassicalGreekScraper:
    """Scraper for OCR GCSE Classical Greek."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent.parent / "A-Level" / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_text = None
        self.content_section = None
        self.appendix_5d_section = None
        self.appendix_5e_section = None
    
    def scrape_all(self):
        """Scrape all topics."""
        print("\n" + "🏛️ "*40)
        print("OCR GCSE CLASSICAL GREEK SCRAPER")
        print("🏛️ "*40)
        
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
        
        # Find content sections
        print("\n[INFO] Finding content sections...")
        language_section = self._find_language_section()
        prose_verse_section = self._find_prose_verse_section()
        culture_section = self._find_culture_section()
        self.appendix_5d_section = self._find_appendix_5d()
        self.appendix_5e_section = self._find_appendix_5e()
        
        # Debug: Print what sections were found
        print(f"\n[DEBUG] Sections found:")
        print(f"  Language: {'YES' if language_section else 'NO'}")
        print(f"  Prose/Verse: {'YES' if prose_verse_section else 'NO'}")
        print(f"  Culture: {'YES' if culture_section else 'NO'}")
        print(f"  Appendix 5d: {'YES' if self.appendix_5d_section else 'NO'}")
        print(f"  Appendix 5e: {'YES' if self.appendix_5e_section else 'NO'}")
        
        if not language_section and not prose_verse_section and not culture_section:
            print("[ERROR] Could not find any content sections")
            return False
        
        # Extract all topics
        all_topics = []
        
        # Level 0: Language (J292/01)
        if language_section or self.appendix_5d_section or self.appendix_5e_section:
            print("\n" + "="*80)
            print("[EXTRACTING] Language (J292/01)")
            print("="*80)
            language_topics = self._extract_language_content(language_section)
            all_topics.extend(language_topics)
        
        # Level 0: Prose Literature and Verse Literature
        if prose_verse_section:
            print("\n" + "="*80)
            print("[EXTRACTING] Prose Literature and Verse Literature")
            print("="*80)
            prose_verse_topics = self._extract_prose_verse_content(prose_verse_section)
            all_topics.extend(prose_verse_topics)
        
        # Level 0: Literature and Culture (J292/06)
        if culture_section:
            print("\n" + "="*80)
            print("[EXTRACTING] Literature and Culture (J292/06)")
            print("="*80)
            culture_topics = self._extract_culture_content(culture_section)
            all_topics.extend(culture_topics)
        
        print(f"\n[OK] Extracted {len(all_topics)} topics total")
        
        # Count by level
        level_counts = {}
        level0_topics = []
        for t in all_topics:
            level = t['level']
            level_counts[level] = level_counts.get(level, 0) + 1
            if level == 0:
                level0_topics.append(t)
        
        print("\n[INFO] Topic distribution by level:")
        for level in sorted(level_counts.keys()):
            print(f"  Level {level}: {level_counts[level]} topics")
        
        print(f"\n[INFO] Level 0 topics created: {len(level0_topics)}")
        for t in level0_topics:
            print(f"  - {t['code']}: {t['title']}")
        
        # Upload to database
        print("\n[INFO] Uploading to database...")
        success = self._upload_topics(all_topics)
        
        if success:
            print(f"\n[OK] ✓ Successfully uploaded {len(all_topics)} topics")
        else:
            print(f"\n[FAIL] ✗ Failed to upload topics")
        
        return success
    
    def _find_language_section(self) -> Optional[str]:
        """Find Language component content section."""
        # Look for "2c. Content of Language (J292/01)"
        pattern = r'2c\.\s+Content\s+of\s+Language\s+\(J292/01\)'
        match = re.search(pattern, self.pdf_text, re.IGNORECASE)
        
        if not match:
            print("[WARN] Could not find Language content section")
            return None
        
        # Extract section (next 50000 chars or until next section)
        start_pos = match.start()
        end_patterns = [
            r'\n\s*2c\.\s+Content\s+of\s+Literature',  # Next section
            r'\n\s*2d\.\s+Prior\s+knowledge',  # Next major section
            r'\n\s*3\.\s+Assessment',  # Assessment section
        ]
        
        end_pos = min(start_pos + 50000, len(self.pdf_text))
        for pattern in end_patterns:
            end_match = re.search(pattern, self.pdf_text[start_pos:start_pos + 50000], re.IGNORECASE)
            if end_match:
                end_pos = start_pos + end_match.start()
                break
        
        section = self.pdf_text[start_pos:end_pos]
        print(f"[OK] Found Language section: {len(section)} chars")
        return section
    
    def _find_prose_verse_section(self) -> Optional[str]:
        """Find Prose and Verse Literature content section."""
        # Look for "2c. Content of Literature components"
        pattern = r'2c\.\s+Content\s+of\s+Literature\s+components'
        match = re.search(pattern, self.pdf_text, re.IGNORECASE)
        
        if not match:
            print("[WARN] Could not find Literature components section")
            return None
        
        # Extract section (next 100000 chars or until next section)
        start_pos = match.start()
        end_patterns = [
            r'\n\s*2c\.\s+Content\s+of\s+Literature\s+and\s+Culture',  # Next section
            r'\n\s*2d\.\s+Prior\s+knowledge',  # Next major section
            r'\n\s*3\.\s+Assessment',  # Assessment section
        ]
        
        end_pos = min(start_pos + 100000, len(self.pdf_text))
        for pattern in end_patterns:
            end_match = re.search(pattern, self.pdf_text[start_pos:start_pos + 100000], re.IGNORECASE)
            if end_match:
                end_pos = start_pos + end_match.start()
                break
        
        section = self.pdf_text[start_pos:end_pos]
        print(f"[OK] Found Prose/Verse Literature section: {len(section)} chars")
        return section
    
    def _find_culture_section(self) -> Optional[str]:
        """Find Literature and Culture content section."""
        # Look for "2c. Content of Literature and Culture (J292/06)"
        pattern = r'2c\.\s+Content\s+of\s+Literature\s+and\s+Culture\s+\(J292/06\)'
        match = re.search(pattern, self.pdf_text, re.IGNORECASE)
        
        if not match:
            print("[WARN] Could not find Literature and Culture section")
            return None
        
        # Extract section (next 50000 chars or until next section)
        start_pos = match.start()
        end_patterns = [
            r'\n\s*2d\.\s+Prior\s+knowledge',  # Next major section
            r'\n\s*3\.\s+Assessment',  # Assessment section
        ]
        
        end_pos = min(start_pos + 50000, len(self.pdf_text))
        for pattern in end_patterns:
            end_match = re.search(pattern, self.pdf_text[start_pos:start_pos + 50000], re.IGNORECASE)
            if end_match:
                end_pos = start_pos + end_match.start()
                break
        
        section = self.pdf_text[start_pos:end_pos]
        print(f"[OK] Found Literature and Culture section: {len(section)} chars")
        return section
    
    def _find_appendix_5d(self) -> Optional[str]:
        """Find Appendix 5d: Classical Greek Accidence and Syntax."""
        # Look for "5d. Classical Greek Accidence and Syntax" or "5.4. Classical Greek Accidence and Syntax"
        patterns = [
            r'5d\.\s+Classical\s+Greek\s+Accidence\s+and\s+Syntax',
            r'5\.4\.\s+Classical\s+Greek\s+Accidence\s+and\s+Syntax',
            r'Appendix\s+5d',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.pdf_text, re.IGNORECASE)
            if match:
                # Extract section (next 50000 chars or until next appendix)
                start_pos = match.start()
                end_patterns = [
                    r'\n\s*5e\.\s+Restricted',  # Next appendix
                    r'\n\s*5\.5\.\s+Restricted',  # Next appendix
                    r'\n\s*6\.\s+Summary',  # Summary section
                ]
                
                end_pos = min(start_pos + 50000, len(self.pdf_text))
                for end_pattern in end_patterns:
                    end_match = re.search(end_pattern, self.pdf_text[start_pos:start_pos + 50000], re.IGNORECASE)
                    if end_match:
                        end_pos = start_pos + end_match.start()
                        break
                
                section = self.pdf_text[start_pos:end_pos]
                print(f"[OK] Found Appendix 5d: {len(section)} chars")
                return section
        
        print("[WARN] Could not find Appendix 5d")
        return None
    
    def _find_appendix_5e(self) -> Optional[str]:
        """Find Appendix 5e: Restricted Classical Greek Accidence and Syntax list."""
        # Look for "5e. Restricted Classical Greek Accidence and Syntax list"
        patterns = [
            r'5e\.\s+Restricted\s+Classical\s+Greek\s+Accidence\s+and\s+Syntax',
            r'5\.5\.\s+Restricted\s+Classical\s+Greek\s+Accidence\s+and\s+Syntax',
            r'Appendix\s+5e',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.pdf_text, re.IGNORECASE)
            if match:
                # Extract section (next 30000 chars or until next section)
                start_pos = match.start()
                end_patterns = [
                    r'\n\s*6\.\s+Summary',  # Summary section
                    r'\n\s*Summary\s+of\s+Updates',  # Updates section
                ]
                
                end_pos = min(start_pos + 30000, len(self.pdf_text))
                for end_pattern in end_patterns:
                    end_match = re.search(end_pattern, self.pdf_text[start_pos:start_pos + 30000], re.IGNORECASE)
                    if end_match:
                        end_pos = start_pos + end_match.start()
                        break
                
                section = self.pdf_text[start_pos:end_pos]
                print(f"[OK] Found Appendix 5e: {len(section)} chars")
                return section
        
        print("[WARN] Could not find Appendix 5e")
        return None
    
    def _extract_language_content(self, language_section: Optional[str]) -> List[Dict]:
        """Extract Language component content."""
        topics = []
        
        # Level 0: Language (J292/01)
        language_code = f"{SUBJECT_CODE}_01"
        language_topic = {
            'code': language_code,
            'title': 'Language (J292/01)',
            'level': 0,
            'parent': None
        }
        topics.append(language_topic)
        
        # Combine all language-related content
        combined_text = ""
        if language_section:
            combined_text += language_section + "\n\n"
        if self.appendix_5d_section:
            combined_text += "APPENDIX 5d: CLASSICAL GREEK ACCIDENCE AND SYNTAX\n\n" + self.appendix_5d_section + "\n\n"
        if self.appendix_5e_section:
            combined_text += "APPENDIX 5e: RESTRICTED CLASSICAL GREEK ACCIDENCE AND SYNTAX LIST\n\n" + self.appendix_5e_section
        
        if not combined_text:
            print("[WARN] No language content found")
            return topics
        
        # Extract using AI
        print(f"[INFO] Extracting language content ({len(combined_text)} chars)...")
        ai_output = self._extract_with_ai(combined_text, language_code, "Language component", include_appendix=True)
        
        if ai_output:
            # Save AI output for debugging
            safe_code = re.sub(r'[^\w\-]', '_', language_code)
            debug_file = self.debug_dir / f"{SUBJECT_CODE}-language-ai-output.txt"
            debug_file.write_text(ai_output, encoding='utf-8')
            print(f"[DEBUG] Saved AI output to {debug_file.name}")
            
            parsed = self._parse_hierarchy(ai_output, language_code)
            topics.extend(parsed)
            print(f"[OK] Extracted {len(parsed)} language topics")
        else:
            print("[WARN] AI extraction failed for language content")
        
        return topics
    
    def _extract_prose_verse_content(self, prose_verse_section: str) -> List[Dict]:
        """Extract Prose Literature and Verse Literature content."""
        topics = []
        
        # Level 0: Prose Literature and Verse Literature
        prose_verse_code = f"{SUBJECT_CODE}_PROSE_VERSE"
        prose_verse_topic = {
            'code': prose_verse_code,
            'title': 'Prose Literature and Verse Literature',
            'level': 0,
            'parent': None
        }
        topics.append(prose_verse_topic)
        
        # Extract using AI - should create 4 Level 1 topics: Prose A, Prose B, Verse A, Verse B
        print(f"[INFO] Extracting prose/verse literature content ({len(prose_verse_section)} chars)...")
        ai_output = self._extract_with_ai(prose_verse_section, prose_verse_code, "Prose Literature and Verse Literature", include_appendix=False)
        
        if ai_output:
            # Save AI output for debugging
            safe_code = re.sub(r'[^\w\-]', '_', prose_verse_code)
            debug_file = self.debug_dir / f"{SUBJECT_CODE}-prose-verse-ai-output.txt"
            debug_file.write_text(ai_output, encoding='utf-8')
            print(f"[DEBUG] Saved AI output to {debug_file.name}")
            
            parsed = self._parse_hierarchy(ai_output, prose_verse_code)
            topics.extend(parsed)
            print(f"[OK] Extracted {len(parsed)} prose/verse topics")
        else:
            print("[WARN] AI extraction failed for prose/verse content")
        
        return topics
    
    def _extract_culture_content(self, culture_section: str) -> List[Dict]:
        """Extract Literature and Culture content."""
        topics = []
        
        # Level 0: Literature and Culture (J292/06)
        culture_code = f"{SUBJECT_CODE}_06"
        culture_topic = {
            'code': culture_code,
            'title': 'Literature and Culture (J292/06)',
            'level': 0,
            'parent': None
        }
        topics.append(culture_topic)
        
        # Extract using AI
        print(f"[INFO] Extracting culture content ({len(culture_section)} chars)...")
        ai_output = self._extract_with_ai(culture_section, culture_code, "Literature and Culture", include_appendix=False)
        
        if ai_output:
            # Save AI output for debugging
            safe_code = re.sub(r'[^\w\-]', '_', culture_code)
            debug_file = self.debug_dir / f"{SUBJECT_CODE}-culture-ai-output.txt"
            debug_file.write_text(ai_output, encoding='utf-8')
            print(f"[DEBUG] Saved AI output to {debug_file.name}")
            
            parsed = self._parse_hierarchy(ai_output, culture_code)
            topics.extend(parsed)
            print(f"[OK] Extracted {len(parsed)} culture topics")
        else:
            print("[WARN] AI extraction failed for culture content")
        
        return topics
    
    def _extract_with_ai(self, text: str, parent_code: str, section_name: str, include_appendix: bool = False) -> Optional[str]:
        """Extract content using AI."""
        # Limit text size
        text = text[:200000]  # 200k chars max
        
        # Build section-specific instructions
        if section_name == "Prose Literature and Verse Literature":
            structure_instructions = """CRITICAL: You MUST create exactly 4 Level 1 topics under the parent:
   1. Prose Literature A (J292/02)
   2. Prose Literature B (J292/03)
   3. Verse Literature A (J292/04)
   4. Verse Literature B (J292/05)

   Under each Level 1 topic, extract:
   - Prescribed texts (as Level 2)
   - Specific sections/lines (as Level 3)
   - Study requirements and assessment details (as Level 3-4)"""
        elif section_name == "Language component":
            structure_instructions = """CRITICAL: Create a detailed hierarchy for language content:
   Level 1: Main categories
     - Accidence
     - Syntax
   Level 2: Subcategories
     - Under Accidence: Verbs, Nouns and Pronouns, Adjectives and Adverbs
     - Under Syntax: Standard uses of cases, Expressions of time and place, Genitive of comparison, etc.
   Level 3-4: Specific items with full details
     - Extract ALL Greek examples (preserve Greek characters exactly)
     - Extract ALL specific forms, rules, and exceptions
     - Include ALL content from Appendix 5d and 5e if provided
   
   CRITICAL: Do NOT create separate Level 1 topics for "Appendix 5d" or "Appendix 5e". 
   The appendices contain detailed accidence and syntax rules - integrate ALL their content 
   into the appropriate sections under "Accidence" and "Syntax".
   
   For example:
   - Appendix 5d verb forms → integrate into "Accidence > Verbs"
   - Appendix 5d syntax rules → integrate into "Syntax > [appropriate subcategory]"
   - Appendix 5e restricted forms → integrate into relevant sections"""
        else:  # Literature and Culture
            structure_instructions = """CRITICAL: Extract all topics, themes, and prescribed sources:
   Level 1: Main themes/topics
   Level 2: Sub-topics and specific areas
   Level 3-4: Detailed content, sources, and study requirements"""
        
        prompt = f"""Extract the complete topic hierarchy from this OCR GCSE Classical Greek specification section.

SECTION: {section_name}
PARENT CODE: {parent_code}

CRITICAL REQUIREMENTS:
1. Extract ONLY content topics. DO NOT extract:
   - "Forms of assessment"
   - "Assessment objectives"
   - "Assessment of GCSE"
   - "Admin: what you need to know"
   - "Appendices" (unless specifically extracting appendix content)
   - Any assessment or administrative sections
   - Topics that start with "Assessment", "Admin", "Appendix" (unless extracting appendix content)

2. STRUCTURE REQUIREMENTS:
{structure_instructions}

3. Output format: Numbered hierarchy
   1. Level 1 Topic
   1.1. Level 2 Topic
   1.1.1. Level 3 Topic
   1.1.1.1. Level 4 Topic

4. DO NOT ask for confirmation. Extract EVERYTHING NOW.
5. Preserve Greek characters exactly as they appear in the text.

CONTENT:
{text}

Extract the complete hierarchy now:"""

        return self._call_ai(prompt, max_tokens=16000)
    
    def _parse_hierarchy(self, text: str, base_code: str) -> List[Dict]:
        """Parse AI numbered output."""
        all_topics = []
        parent_stack = {-1: None}
        
        # Assessment/admin sections to filter out
        excluded_patterns = [
            r'^forms\s+of\s+assessment',
            r'^assessment\s+objectives',
            r'^admin:',
            r'^appendices?$',
            r'^assessment\s+of',
            r'^total\s+qualification',
            r'^qualification\s+availability',
            r'^assessment\s+availability',
            r'^retaking',
            r'^synoptic\s+assessment',
            r'^calculating\s+qualification',
            r'^pre-assessment',
            r'^special\s+consideration',
            r'^external\s+assessment',
            r'^results\s+and\s+certificates',
            r'^post-results',
            r'^malpractice',
            r'^grade\s+descriptors',
            r'^overlap\s+with',
            r'^accessibility',
        ]
        
        # Filter out topics that are actually appendices (should be integrated, not separate)
        excluded_titles = [
            'appendix 5d',
            'appendix 5e',
            'classical greek accidence and syntax',
            'restricted classical greek accidence and syntax',
        ]
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip markdown formatting
            line = re.sub(r'^\*\*|\*\*$', '', line)  # Remove bold markers
            line = re.sub(r'^[-•]\s+', '', line)  # Remove bullets
            
            # Check if excluded by patterns
            excluded = False
            for pattern in excluded_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    excluded = True
                    break
            
            if excluded:
                continue
            
            # Parse numbered format: "1. Title" or "1.1. Title" or "1.1.1. Title"
            match = re.match(r'^(\d+(?:\.\d+)*)\.\s+(.+)$', line)
            if not match:
                continue
            
            number_str = match.group(1)
            title = match.group(2).strip()
            
            # Check if title matches excluded titles (now that we have the title)
            title_excluded = False
            title_lower = title.lower()
            for excluded_title in excluded_titles:
                if excluded_title in title_lower:
                    title_excluded = True
                    break
            
            if title_excluded:
                continue
            
            # Determine level from number
            parts = number_str.split('.')
            level = len(parts)
            
            # Find parent
            parent_level = level - 1
            parent_code = parent_stack.get(parent_level)
            
            # If Level 1 and no parent found, use base_code (the Level 0 parent)
            if level == 1 and parent_code is None:
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
            
            # Remove duplicates
            seen_codes = set()
            unique_topics = []
            for t in topics:
                if t['code'] not in seen_codes:
                    seen_codes.add(t['code'])
                    unique_topics.append(t)
            
            # Insert topics
            to_insert = [{
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': t['title'],
                'topic_level': t['level'],
                'exam_board': 'OCR'
            } for t in unique_topics]
            
            inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
            
            # Link hierarchy
            code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
            for topic in unique_topics:
                if topic['parent']:
                    parent_id = code_to_id.get(topic['parent'])
                    child_id = code_to_id.get(topic['code'])
                    if parent_id and child_id:
                        supabase.table('staging_aqa_topics').update({
                            'parent_topic_id': parent_id
                        }).eq('id', child_id).execute()
            
            print(f"[OK] Successfully uploaded {len(unique_topics)} topics")
            return True
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    scraper = ClassicalGreekScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)

