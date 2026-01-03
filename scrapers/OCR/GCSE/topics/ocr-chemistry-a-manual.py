"""
OCR GCSE Chemistry A (Gateway Science) Manual Scraper
======================================================

Extracts topics from OCR GCSE Chemistry A (Gateway Science) J248 specification.

Structure (same as Biology A):
- Level 0: Subject
- Level 1: Topics (C1-C6, C7 for practical skills)
  - Format: "Topic C1: Particles"
- Level 2: Sub-topics
  - Format: "C1.1 The particle model"
- Level 3: Learning outcomes (with reference codes)
  - Format: "C1.1a", "C1.1b", etc.
- Level 4: Content from "To include" column (extracted as children of Level 3)

Topics:
- C1: Particles
- C2: Elements, compounds and mixtures
- C3: Chemical reactions
- C4: Predicting and identifying reactions and products
- C5: Monitoring and controlling chemical reactions
- C6: Global challenges
- C7: Practical activity skills

CRITICAL: Skip "Content Overview" and "Assessment Overview" sections.
Extract only from "2c. Content of topics C1 to C6" section.

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-chemistry-a-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/234598-specification-accredited-gcse-gateway-science-suite-chemistry-a-j248.pdf'
SUBJECT_CODE = 'J248'
SUBJECT_NAME = 'Chemistry A'

# Topics C1-C6 + C7 (practical skills)
TOPICS = [
    'C1: Particles',
    'C2: Elements, compounds and mixtures',
    'C3: Chemical reactions',
    'C4: Predicting and identifying reactions and products',
    'C5: Monitoring and controlling chemical reactions',
    'C6: Global challenges',
    'C7: Practical activity skills'
]


class ChemistryAScraper:
    """Scraper for OCR GCSE Chemistry A (Gateway Science)."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent.parent / "A-Level" / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_text = None
        self.content_section = None
    
    def scrape_all(self):
        """Scrape all topics."""
        print("\n" + "🧪 "*40)
        print("OCR GCSE CHEMISTRY A (GATEWAY SCIENCE) SCRAPER")
        print("🧪 "*40)
        
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
        
        # Find content section (skip Content Overview and Assessment Overview)
        content_section = self._find_content_section()
        if not content_section:
            print("[ERROR] Could not find content section (2c. Content of topics C1 to C6)")
            return False
        
        print(f"[OK] Found content section: {len(content_section)} characters")
        
        # Store content section for topic extraction
        self.content_section = content_section
        
        # Extract all topics
        all_topics = []
        
        # Level 0: Subject
        subject_topic = {
            'code': SUBJECT_CODE,
            'title': f"{SUBJECT_NAME} (Gateway Science)",
            'level': 0,
            'parent': None
        }
        all_topics.append(subject_topic)
        
        # Extract each topic (C1-C7)
        for topic_idx, topic_name in enumerate(TOPICS):
            topic_code = topic_name.split(':')[0].strip()  # e.g., "C1"
            print(f"\n{'='*80}")
            print(f"[TOPIC {topic_idx + 1}/{len(TOPICS)}] {topic_name}")
            print("="*80)
            
            # Extract topic content
            topic_topics = self._extract_topic(topic_code, topic_name, SUBJECT_CODE, topic_idx + 1)
            all_topics.extend(topic_topics)
        
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
    
    def _find_content_section(self) -> Optional[str]:
        """Find the content section, skipping Content Overview and Assessment Overview."""
        # Look for "2c. Content of topics C1 to C6" - find the ACTUAL content, not TOC entry
        pattern = r'2c\.\s+Content\s+of\s+topics\s+C1\s+to\s+C[67]'
        matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE))
        
        content_start = None
        for match in matches:
            pos = match.start()
            # Check if this is actual content (has "Topic C1:" nearby) vs TOC (has page number)
            after_text = self.pdf_text[pos:pos + 500]
            before_text = self.pdf_text[max(0, pos - 200):pos]
            
            # TOC entries usually have page numbers after them (e.g., "2c. Content... 10")
            # Actual content has "Topic C1:" or "C1.1" nearby
            if re.search(r'Topic\s+C1:', after_text, re.IGNORECASE) or re.search(r'C1\.1\s+', after_text):
                content_start = pos
                print(f"[DEBUG] Found actual content section at position {pos}")
                print(f"[DEBUG] Context: {after_text[:200]}")
                break
            elif re.search(r'\d+\s*$', before_text[-50:]):  # Page number before it = TOC
                print(f"[DEBUG] Skipping TOC entry at position {pos}")
                continue
        
        if not content_start:
            # Fallback: look for first "Topic C1:" occurrence that's NOT in TOC
            match = re.search(r'Topic\s+C1:\s+Particles', self.pdf_text, re.IGNORECASE)
            if match:
                content_start = match.start()
                print(f"[DEBUG] Found content section using fallback: Topic C1: Particles")
            else:
                print("[ERROR] Could not find content section")
                return None
        
        # Extract from content start - use a VERY large chunk (500000 chars) or until Appendix
        end_patterns = [
            r'\n\s*Appendix\s+[A-Z]',  # Appendix with capital letter
            r'\n\s*Appendix\s+\d+',     # Appendix with number
            r'\n\s*2d\.\s+Prior\s+knowledge',  # Next section
        ]
        
        content_end = min(content_start + 500000, len(self.pdf_text))  # Very large chunk
        for pattern in end_patterns:
            match = re.search(pattern, self.pdf_text[content_start:content_start + 500000], re.IGNORECASE)
            if match:
                content_end = content_start + match.start()
                print(f"[DEBUG] Found end marker: {pattern}")
                break
        
        content_section = self.pdf_text[content_start:content_end]
        print(f"[DEBUG] Content section: {len(content_section)} characters")
        
        # Save snippet for debugging
        snippet_file = self.debug_dir / f"J248-content-section.txt"
        snippet_file.write_text(content_section[:10000], encoding='utf-8')
        print(f"[DEBUG] Saved content section snippet to {snippet_file.name}")
        
        return content_section
    
    def _extract_topic(self, topic_code: str, topic_name: str, parent_code: str, topic_num: int) -> List[Dict]:
        """Extract a topic (C1-C7) with all its content."""
        topics = []
        
        # Level 1: Topic (e.g., "Topic C1: Particles")
        topic_level1_code = f"{parent_code}_{topic_num}"
        topic_level1 = {
            'code': topic_level1_code,
            'title': f"Topic {topic_code}: {topic_name.split(':')[1].strip()}" if ':' in topic_name else f"Topic {topic_code}: {topic_name}",
            'level': 1,
            'parent': parent_code
        }
        topics.append(topic_level1)
        
        # Use the content section we already found (not searching entire PDF)
        if not hasattr(self, 'content_section') or not self.content_section:
            print(f"[WARN] No content section available for {topic_code}")
            return topics
        
        # Find topic section in the content section
        topic_title = topic_name.split(':')[1].strip() if ':' in topic_name else topic_name
        topic_patterns = [
            rf"Topic\s+{re.escape(topic_code)}:\s+{re.escape(topic_title)}",
            rf"Topic\s+{re.escape(topic_code)}:",
        ]
        
        topic_section_start = None
        for pattern in topic_patterns:
            match = re.search(pattern, self.content_section, re.IGNORECASE)
            if match:
                # Verify this is actual content (has sub-topic like "C1.1" nearby), not TOC
                after_text = self.content_section[match.start():match.start() + 2000]
                if re.search(rf'{re.escape(topic_code)}\.\d+', after_text):  # Has sub-topic like "C1.1"
                    topic_section_start = match.start()
                    print(f"[DEBUG] Found topic section in content: {pattern[:50]}...")
                    print(f"[DEBUG] Context preview: {after_text[:500]}")
                    break
        
        if not topic_section_start:
            print(f"[WARN] Could not find section for {topic_code} in content section")
            return topics
        
        # Extract topic section (next 200000 chars or until next topic)
        next_topic_pattern = rf"Topic\s+C{topic_num + 1}:" if topic_num < 7 else None
        if next_topic_pattern:
            # Look further ahead for next topic
            search_text = self.content_section[topic_section_start:topic_section_start + 250000]
            next_match = re.search(next_topic_pattern, search_text, re.IGNORECASE)
            if next_match:
                # Verify next match is actual content too
                next_after = search_text[next_match.start():next_match.start() + 1000]
                if re.search(rf'C{topic_num + 1}\.\d+', next_after):
                    topic_section = self.content_section[topic_section_start:topic_section_start + next_match.start()]
                    print(f"[DEBUG] Found next topic, extracted {len(topic_section)} chars")
                else:
                    topic_section = self.content_section[topic_section_start:topic_section_start + 200000]
                    print(f"[DEBUG] Next match was TOC, extracted {len(topic_section)} chars")
            else:
                topic_section = self.content_section[topic_section_start:topic_section_start + 200000]
                print(f"[DEBUG] No next topic found, extracted {len(topic_section)} chars")
        else:
            topic_section = self.content_section[topic_section_start:topic_section_start + 200000]
            print(f"[DEBUG] Last topic, extracted {len(topic_section)} chars")
        
        # Save topic section snippet for debugging
        safe_code = re.sub(r'[^\w\-]', '_', topic_code)[:50]
        snippet_file = self.debug_dir / f"J248-{safe_code}-section.txt"
        snippet_file.write_text(topic_section[:10000], encoding='utf-8')
        print(f"[DEBUG] Saved topic section snippet ({len(topic_section)} chars) to {snippet_file.name}")
        
        # Verify we have actual content
        if len(topic_section) < 1000:
            print(f"[ERROR] Topic section too short ({len(topic_section)} chars) - extraction failed")
            return topics
        
        # Extract table content using AI
        print(f"[INFO] Extracting table content from {topic_code} ({len(topic_section)} chars)...")
        table_content = self._extract_table_content(topic_section, topic_code, topic_name)
        
        if table_content and "sorry" not in table_content.lower() and "can't assist" not in table_content.lower():
            # Parse the AI output
            parsed_content = self._parse_table_content(table_content, topic_level1_code, topic_code)
            topics.extend(parsed_content)
            print(f"[OK] Extracted {len(parsed_content)} sub-topics from {topic_code}")
        else:
            print(f"[WARN] No table content extracted for {topic_code} (AI refused or empty)")
            if table_content:
                print(f"[DEBUG] AI response: {table_content[:200]}")
        
        return topics
    
    def _extract_table_content(self, section_text: str, topic_code: str, topic_name: str) -> Optional[str]:
        """Extract table content using AI."""
        
        # Check if section has actual content
        if len(section_text) < 500:
            print(f"[ERROR] Section text too short ({len(section_text)} chars) - cannot extract")
            return None
        
        prompt = f"""You are extracting educational content from a Chemistry GCSE specification document.

TOPIC: {topic_name} ({topic_code})

Your task is to extract all learning content from tables in this specification section.

The document contains tables with these columns:
- Learning outcomes (with codes like C1.1a, C1.1b)
- To include (lists of items separated by commas)

Extract the content using this structure:
- Level 2: Sub-topic headings (e.g., "C1.1 The particle model")
- Level 3: Learning outcomes (e.g., "C1.1a describe the main features of the particle model...")
- Level 4: Items from "To include" column (split comma-separated items into separate lines)

Output format (numbered only, no bullets or markdown):
1.1 C1.1 The particle model
1.1.1 C1.1a describe the main features of the particle model
1.1.1.1 particles are very small
1.1.1.2 particles are in constant motion
1.1.2 C1.1b explain the differences between solids, liquids and gases
1.1.2.1 arrangement of particles
1.1.2.2 movement of particles

Extract all rows from all tables. Split comma-separated items in "To include" into separate Level 4 items.

SECTION TEXT:
{section_text[:250000]}

Begin extraction:"""
        
        result = self._call_ai(prompt, max_tokens=16000)
        
        # Save AI output for debugging
        if result:
            safe_code = re.sub(r'[^\w\-]', '_', topic_code)[:50]
            ai_file = self.debug_dir / f"J248-{safe_code}-ai-output.txt"
            ai_file.write_text(result, encoding='utf-8')
            print(f"[DEBUG] Saved AI output to {ai_file.name}")
        
        return result
    
    def _parse_table_content(self, text: str, parent_code: str, topic_code: str) -> List[Dict]:
        """Parse AI output into topic structure."""
        topics = []
        parent_stack = {1: parent_code}  # Level 1 is the topic
        
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
            
            # Skip excluded headers and overview sections
            excluded_headers = [
                'content overview', 'assessment overview', 'summary',
                'underlying knowledge and understanding', 'common misconceptions',
                'tiering', 'overview of the content layout', 'mathematical outcomes',
                'mathematical skills', 'reference', 'opportunities to co'
            ]
            title_lower = title.lower()
            if any(title_lower.startswith(excluded) for excluded in excluded_headers):
                print(f"[FILTER] Skipping excluded header: {title[:50]}")
                continue
            
            # Skip if title contains "overview" (unless it's part of a learning outcome)
            if 'overview' in title_lower and not re.search(r'C\d+\.\d+[a-z]', title):
                print(f"[FILTER] Skipping overview section: {title[:50]}")
                continue
            
            # Determine level based on number of dots
            dots = number.count('.')
            # Parent is Level 1, so:
            # 1.1 = 1 dot → Level 2 (Sub-topics)
            # 1.1.1 = 2 dots → Level 3 (Learning outcomes)
            # 1.1.1.1 = 3 dots → Level 4 (To include items)
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
                'subject_name': f"{SUBJECT_NAME} (Gateway Science) (GCSE)",
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
            
            return True
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    scraper = ChemistryAScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

