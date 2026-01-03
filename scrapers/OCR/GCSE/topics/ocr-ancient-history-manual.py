"""
OCR GCSE Ancient History Manual Scraper
========================================

Extracts topics from OCR GCSE Ancient History J198 specification.

Structure:
- Level 0: Two components
  1. Greece and Persia (J198/01)
  2. Rome and its neighbours (J198/02)
- Level 1: Compulsory period study + Depth studies
- Level 2: Sections within period studies
- Level 3: Key Time Spans (from table headers)
- Level 4: Content items from "Learners should have studied..." (as bullet points)

Component 01: Greece and Persia
- Compulsory: The Persian Empire, 559–465 BC
- Depth studies (one chosen from):
  - From Tyranny to Democracy, 546–483 BC
  - Athens in the Age of Pericles, 462–429 BC
  - Alexander the Great, 356–323 BC

Component 02: Rome and its neighbours
- Compulsory: The foundations of Rome: from kingship to republic, 753–440 BC
- Depth studies (one chosen from):
  - Hannibal and the Second Punic War, 218–201 BC
  - Cleopatra: Rome and Egypt, 69–30 BC
  - Britannia: from conquest to province, AD 43–c.84

Tables have:
- Column 1: "Key time spans" (Level 3)
- Column 2: "Learners should have studied the following content:" (Level 4 as bullet points)

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-ancient-history-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/313533-specification-accredited-gcse-ancient-history-j198.pdf'
SUBJECT_CODE = 'J198'
SUBJECT_NAME = 'Ancient History'

COMPONENTS = [
    {
        'name': 'Greece and Persia',
        'code': 'J198_01',
        'compulsory': 'The Persian Empire, 559–465 BC',
        'depth_studies': [
            'From Tyranny to Democracy, 546–483 BC',
            'Athens in the Age of Pericles, 462–429 BC',
            'Alexander the Great, 356–323 BC'
        ]
    },
    {
        'name': 'Rome and its neighbours',
        'code': 'J198_02',
        'compulsory': 'The foundations of Rome: from kingship to republic, 753–440 BC',
        'depth_studies': [
            'Hannibal and the Second Punic War, 218–201 BC',
            'Cleopatra: Rome and Egypt, 69–30 BC',
            'Britannia: from conquest to province, AD 43–c.84'
        ]
    }
]


class AncientHistoryScraper:
    """Scraper for OCR GCSE Ancient History."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent.parent / "A-Level" / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_pages = []
        self.pdf_text = None
    
    def scrape_all(self):
        """Scrape all components."""
        print("\n" + "🏛️ "*40)
        print("OCR GCSE ANCIENT HISTORY SCRAPER")
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
        
        # Extract all topics
        all_topics = []
        
        for comp_idx, component in enumerate(COMPONENTS):
            print(f"\n{'='*80}")
            print(f"[COMPONENT {comp_idx + 1}/{len(COMPONENTS)}] {component['name']} ({component['code']})")
            print("="*80)
            
            # Level 0: Component
            comp_code = f"{SUBJECT_CODE}_{comp_idx + 1}"
            comp_topic = {
                'code': comp_code,
                'title': component['name'],
                'level': 0,
                'parent': None
            }
            all_topics.append(comp_topic)
            
            # Extract compulsory period study
            print(f"\n[INFO] Extracting compulsory period study: {component['compulsory']}")
            compulsory_topics = self._extract_period_study(
                component['compulsory'],
                comp_code,
                component['code']
            )
            all_topics.extend(compulsory_topics)
            
            # Extract all depth studies
            # Start at _2 because compulsory is _1
            for depth_idx, depth_study in enumerate(component['depth_studies']):
                print(f"\n[INFO] Extracting depth study {depth_idx + 1}/{len(component['depth_studies'])}: {depth_study}")
                depth_topics = self._extract_depth_study(
                    depth_study,
                    comp_code,
                    component['code'],
                    depth_idx + 2  # +2 because compulsory is _1, so depth studies start at _2
                )
                all_topics.extend(depth_topics)
        
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
    
    def _extract_period_study(self, study_name: str, parent_code: str, component_code: str) -> List[Dict]:
        """Extract a compulsory period study with all its content."""
        topics = []
        
        # Find section in PDF - look for "Content of" sections
        section_patterns = [
            rf"2[c-z]\.\s+Content\s+of.*?{re.escape(study_name.split(',')[0])}",
            rf"Content\s+of.*?{re.escape(study_name.split(',')[0])}",
            rf"{re.escape(study_name)}",
            rf"The\s+{re.escape(study_name.split(':')[0].split(',')[0])}"  # e.g., "The Persian Empire"
        ]
        
        section_start = None
        for pattern in section_patterns:
            match = re.search(pattern, self.pdf_text, re.IGNORECASE)
            if match:
                section_start = match.start()
                print(f"[DEBUG] Found section using pattern: {pattern[:50]}...")
                break
        
        if not section_start:
            print(f"[WARN] Could not find section for {study_name}")
            # Try to find by component code
            comp_match = re.search(rf"Content\s+of\s+{re.escape(component_code)}", self.pdf_text, re.IGNORECASE)
            if comp_match:
                section_start = comp_match.start()
                print(f"[DEBUG] Found section using component code")
            else:
                return []
        
        # Extract section content (next 60000 chars to get full tables)
        section_text = self.pdf_text[section_start:section_start + 60000]
        
        # Level 1: Period study name
        study_code = f"{parent_code}_1"
        study_topic = {
            'code': study_code,
            'title': study_name,
            'level': 1,
            'parent': parent_code
        }
        topics.append(study_topic)
        
        # Extract table content using AI
        print(f"[INFO] Extracting table content from section...")
        table_content = self._extract_table_content(section_text, study_name)
        
        if table_content:
            # Parse the AI output (pass parent title to filter duplicates)
            parsed_content = self._parse_table_content(table_content, study_code, parent_title=study_name)
            topics.extend(parsed_content)
        else:
            print(f"[WARN] No table content extracted for {study_name}")
        
        return topics
    
    def _extract_depth_study(self, study_name: str, parent_code: str, component_code: str, depth_num: int) -> List[Dict]:
        """Extract a depth study with all its content."""
        topics = []
        
        # Find section in PDF - look for depth study titles
        section_patterns = [
            rf"Content\s+of.*?{re.escape(study_name.split(',')[0])}",
            rf"{re.escape(study_name)}",
            rf"Depth\s+study.*?{re.escape(study_name.split(',')[0])}",
            rf"From\s+{re.escape(study_name.split(' ')[1])}" if study_name.startswith('From') else None,
            rf"Athens\s+in\s+the\s+Age" if 'Athens' in study_name else None,
            rf"Alexander\s+the\s+Great" if 'Alexander' in study_name else None,
            rf"Hannibal" if 'Hannibal' in study_name else None,
            rf"Cleopatra" if 'Cleopatra' in study_name else None,
            rf"Britannia" if 'Britannia' in study_name else None
        ]
        
        section_start = None
        for pattern in section_patterns:
            if not pattern:
                continue
            match = re.search(pattern, self.pdf_text, re.IGNORECASE)
            if match:
                section_start = match.start()
                print(f"[DEBUG] Found section using pattern: {pattern[:50]}...")
                break
        
        if not section_start:
            print(f"[WARN] Could not find section for {study_name}")
            return []
        
        # Extract section content (next 40000 chars to get full tables)
        section_text = self.pdf_text[section_start:section_start + 40000]
        
        # Level 1: Depth study name
        study_code = f"{parent_code}_{depth_num}"  # depth_num already accounts for +2 offset
        study_topic = {
            'code': study_code,
            'title': study_name,
            'level': 1,
            'parent': parent_code
        }
        topics.append(study_topic)
        
        # Extract table content using AI
        print(f"[INFO] Extracting table content from section...")
        table_content = self._extract_table_content(section_text, study_name)
        
        if table_content:
            # Parse the AI output (pass parent title to filter duplicates)
            parsed_content = self._parse_table_content(table_content, study_code, parent_title=study_name)
            topics.extend(parsed_content)
        else:
            print(f"[WARN] No table content extracted for {study_name}")
        
        return topics
    
    def _extract_table_content(self, section_text: str, study_name: str) -> Optional[str]:
        """Extract table content using AI."""
        
        prompt = f"""You must extract the COMPLETE content from this OCR GCSE Ancient History section.

STUDY: {study_name}

CRITICAL INSTRUCTIONS:
1. Find tables with TWO columns:
   - Column 1 header: "Key time spans" (or similar)
   - Column 2 header: "Learners should have studied the following content:" (or similar)
2. Extract ALL rows from these tables
3. For each row:
   - Level 3: Extract the "Key time spans" entry (time period title with dates)
   - Level 4: Extract EVERY bullet point from "Learners should have studied..." column as separate Level 4 items
4. If there are Level 2 headings before the tables, extract those too
5. Output format: Use ONLY numbered format (1, 1.1, 1.1.1, 1.1.1.1) - NO bullets (-), NO asterisks (*), NO markdown (**)
6. Do NOT use markdown formatting. Use ONLY numbers and dots.
7. Extract EVERYTHING - do not skip any content, do not summarize

STRUCTURE EXPECTED:
- Level 2: Key time spans entries (e.g., "The rise of the Persian Empire under Cyrus the Great (559-530 BC)")
- Level 3: Content items from "Learners should have studied..." column (each bullet point = separate Level 3 item)

CRITICAL: Do NOT repeat the period study name. Start directly with Key time spans.

EXAMPLE OUTPUT FORMAT:
1.1.1 The rise of the Persian Empire under Cyrus the Great (559-530 BC)
1.1.1.1 The background and accession of Cyrus
1.1.1.2 The conquest of Lydia
1.1.1.3 The conquest of Babylon
1.1.1.4 Cyrus' attitude towards conquered peoples and his liberation of the Jews
1.1.1.5 The construction of Pasargadae
1.1.1.6 The circumstances of Cyrus' death
1.1.2 Cambyses II, Smerdis and the accession of Darius (530-522 BC)
1.1.2.1 Cambyses' conquest of Egypt
1.1.2.2 Cambyses' attitude towards the Egyptians and their culture
1.1.2.3 The circumstances of Cambyses' death
1.1.2.4 Darius' overthrow of Smerdis/Bardiya/Gaumata

SECTION TEXT:
{section_text[:80000]}

EXTRACT NOW - Extract ALL content from tables:"""
        
        result = self._call_ai(prompt, max_tokens=16000)
        
        # Save AI output for debugging
        if result:
            safe_name = re.sub(r'[^\w\-]', '_', study_name)[:50]
            ai_file = self.debug_dir / f"J198-{safe_name}-ai-output.txt"
            ai_file.write_text(result, encoding='utf-8')
            print(f"[DEBUG] Saved AI output to {ai_file.name}")
        
        return result
    
    def _parse_table_content(self, text: str, parent_code: str, parent_title: str = None) -> List[Dict]:
        """Parse AI output into topic structure."""
        topics = []
        parent_stack = {0: parent_code}
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Match hierarchical numbers
            match = re.match(r'^([\d.]+)\s+(.+)$', line)
            if not match:
                match = re.match(r'^\*\*?([\d.]+)\s+(.+?)\*\*?$', line)
            if not match:
                match = re.match(r'^[-•●]\s+([\d.]+)\s+(.+)$', line)
            if not match:
                continue
            
            number = match.group(1).rstrip('.')
            title = match.group(2).strip()
            
            # Clean title
            title = title.lstrip('*☐✓□■●○-•').strip()
            title = title.rstrip('*').strip()
            
            if len(title) < 2:
                continue
            
            # Skip if title matches parent title (duplicate)
            if parent_title and title.lower() == parent_title.lower():
                print(f"[DEBUG] Skipping duplicate title: {title}")
                continue
            
            # Determine level based on number of dots
            dots = number.count('.')
            # Parent is Level 1, so:
            # 1.1.1 = 2 dots → Level 2 (Key time spans)
            # 1.1.1.1 = 3 dots → Level 3 (Content items)
            level = 1 + dots  # Parent level (1) + dots
            
            # Generate code
            code_suffix = number.replace('.', '_')
            code = f"{parent_code}_{code_suffix}"
            
            # Find parent
            parent_level = level - 1
            parent_code_for_level = parent_stack.get(parent_level)
            
            if not parent_code_for_level:
                # Fallback: use immediate parent
                parent_code_for_level = parent_code
            
            topics.append({
                'code': code,
                'title': title,
                'level': level,
                'parent': parent_code_for_level
            })
            
            # Update parent stack
            parent_stack[level] = code
            # Remove deeper levels
            for l in list(parent_stack.keys()):
                if l > level:
                    del parent_stack[l]
        
        return topics
    
    def _download_pdf(self, url: str) -> Optional[bytes]:
        """Download PDF."""
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            if response.content[:4] == b'%PDF':
                print(f"[OK] Downloaded PDF: {len(response.content)/1024/1024:.1f} MB")
                return response.content
            else:
                print(f"[ERROR] URL does not point to a valid PDF")
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
                print(f"[WARN] Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"[INFO] Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"[ERROR] All {max_retries} attempts failed")
                    return None
        
        return None
    
    def _upload_topics(self, topics: List[Dict]) -> bool:
        """Upload topics to database."""
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
            
            # Remove duplicates
            seen_codes = set()
            unique_topics = []
            for t in topics:
                if t['code'] not in seen_codes:
                    seen_codes.add(t['code'])
                    unique_topics.append(t)
            
            # Clear old topics for this subject
            print("[INFO] Clearing old topics...")
            supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).eq('exam_board', 'OCR').execute()
            
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
            
            return True
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    scraper = AncientHistoryScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

