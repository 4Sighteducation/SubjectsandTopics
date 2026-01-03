"""
OCR GCSE Drama (J316) Manual Scraper
====================================

Extracts topics from OCR GCSE Drama J316 specification.

Structure:
- Level 0: Drama: Performance and response (04) - ONLY this component (examined material)
- Level 1: Main topics (solid bullets from "Learners should:" column)
- Level 2: Sub-topics (solid bullets from "Learners must know and understand:" column)
- Level 3: Detailed items (open bullets from "Learners must know and understand:" column)
- Level 4: Synthesized content from "Learners should be able to:" column

CRITICAL: 
- Extract ONLY Component 04 (Performance and response) - the examined component
- EXCLUDE Components 01/02 (Devising drama) and 03 (Presenting and performing texts) - these are non-exam assessment
- Extract from the 3-column table structure
- Synthesize "Learners should be able to" content as Level 4 items

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-drama-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/242630-specification-accredited-gcse-drama-j316.pdf'
SUBJECT_CODE = 'J316'
SUBJECT_NAME = 'Drama'


class DramaScraper:
    """Scraper for OCR GCSE Drama."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent.parent / "A-Level" / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_text = None
    
    def scrape_all(self):
        """Scrape all topics."""
        print("\n" + "🎭 "*40)
        print("OCR GCSE DRAMA SCRAPER")
        print("🎭 "*40)
        
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
        
        # Find Component 04 section ONLY
        print("\n[INFO] Finding Component 04: Performance and response section...")
        component04_section = self._find_component04_section()
        
        if not component04_section:
            print("[ERROR] Could not find Component 04 section")
            return False
        
        print(f"[OK] Found Component 04 section: {len(component04_section)} chars")
        
        # Extract topics
        all_topics = []
        
        # Level 0: Drama: Performance and response (04)
        component04_code = f"{SUBJECT_CODE}_04"
        component04_topic = {
            'code': component04_code,
            'title': 'Drama: Performance and response (04)',
            'level': 0,
            'parent': None
        }
        all_topics.append(component04_topic)
        
        # Extract content using AI
        print(f"\n[INFO] Extracting Component 04 content ({len(component04_section)} chars)...")
        ai_output = self._extract_with_ai(component04_section, component04_code)
        
        if ai_output:
            # Save AI output for debugging
            debug_file = self.debug_dir / f"{SUBJECT_CODE}-ai-output.txt"
            debug_file.write_text(ai_output, encoding='utf-8')
            print(f"[DEBUG] Saved AI output to {debug_file.name}")
            
            parsed = self._parse_hierarchy(ai_output, component04_code)
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
    
    def _find_component04_section(self) -> Optional[str]:
        """Find Component 04: Performance and response section."""
        # Look for "2c. Content of Drama: Performance and response (04)"
        # Need to distinguish TOC entries from actual content
        patterns = [
            r'2c\.\s+Content\s+of\s+Drama:\s+Performance\s+and\s+response\s+\(04\)',
            r'Content\s+of\s+Drama:\s+Performance\s+and\s+response\s+\(04\)',
        ]
        
        # Find all matches to distinguish TOC from content
        all_matches = []
        for pattern in patterns:
            matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE))
            all_matches.extend(matches)
        
        if not all_matches:
            print("[WARN] Could not find Component 04 content section")
            return None
        
        # Find the actual content (not TOC entry)
        # TOC entries usually have page numbers after them
        # Actual content has descriptive text nearby
        content_start = None
        for match in all_matches:
            pos = match.start()
            after_text = self.pdf_text[pos:pos + 2000]
            before_text = self.pdf_text[max(0, pos - 200):pos]
            
            # Check if this is actual content (has descriptive text) vs TOC (has page number)
            # Actual content should have text like "For this component" or "Learners should" nearby
            if re.search(r'For\s+this\s+component|Learners\s+should|Section\s+A|Section\s+B', after_text, re.IGNORECASE):
                content_start = pos
                print(f"[DEBUG] Found actual content section at position {pos}")
                print(f"[DEBUG] Context preview: {after_text[:300]}")
                break
            elif re.search(r'\d+\s*$', before_text[-50:]):  # Page number before = TOC
                print(f"[DEBUG] Skipping TOC entry at position {pos}")
                continue
        
        if not content_start:
            # Fallback: use the last match (content usually comes after TOC)
            if len(all_matches) > 1:
                content_start = all_matches[-1].start()
                print(f"[DEBUG] Using fallback: last match at position {content_start}")
            else:
                content_start = all_matches[0].start()
                print(f"[DEBUG] Using only match at position {content_start}")
        
        # Extract section (next 150000 chars or until next major section)
        start_pos = content_start
        end_patterns = [
            r'\n\s*2d\.\s+Prior\s+knowledge',  # Next major section
            r'\n\s*3\.\s+Assessment',  # Assessment section
            r'\n\s*Appendix',  # Appendices
        ]
        
        end_pos = min(start_pos + 150000, len(self.pdf_text))
        for pattern in end_patterns:
            end_match = re.search(pattern, self.pdf_text[start_pos:start_pos + 150000], re.IGNORECASE)
            if end_match:
                end_pos = start_pos + end_match.start()
                print(f"[DEBUG] Found end marker: {pattern}")
                break
        
        section = self.pdf_text[start_pos:end_pos]
        
        # Save snippet for debugging
        snippet_file = self.debug_dir / f"{SUBJECT_CODE}-section-snippet.txt"
        snippet_file.write_text(section[:10000], encoding='utf-8')
        print(f"[DEBUG] Saved section snippet ({len(section)} chars) to {snippet_file.name}")
        
        return section
    
    def _extract_with_ai(self, text: str, parent_code: str) -> Optional[str]:
        """Extract content using AI."""
        # Limit text size
        text = text[:200000]  # 200k chars max
        
        prompt = f"""Extract the complete topic hierarchy from this OCR GCSE Drama specification section.

COMPONENT: Drama: Performance and response (04)
PARENT CODE: {parent_code}

CRITICAL REQUIREMENTS:
1. Extract ONLY Component 04 content. DO NOT extract:
   - Component 01/02 (Devising drama) - this is non-exam assessment
   - Component 03 (Presenting and performing texts) - this is non-exam assessment
   - "Forms of assessment"
   - "Assessment objectives"
   - Any other components or administrative sections

2. STRUCTURE REQUIREMENTS - Extract from the 3-column table:
   
   COLUMN 1: "Learners should:" 
   → Extract main topics as Level 1 (these are the main sections)
   → Examples: "in Section A: study a whole performance text"
   
   COLUMN 2: "Learners must know and understand:"
   → Solid bullets (main items) = Level 2 topics
   → Open bullets (indented sub-items) = Level 3 topics
   → Extract ALL content including:
     * Contexts (social, historical, cultural)
     * Theatrical conventions
     * Characteristics of performance text (genres, structure, characters, etc.)
     * How meaning is communicated
   
   COLUMN 3: "Learners should be able to:"
   → Synthesize these as Level 4 items
   → Match each "should be able to" item to its relevant Level 2 or Level 3 parent
   → Create specific, actionable Level 4 items
   → Examples: "define how social contexts affect the performance text"
   
   IMPORTANT: The table rows are connected - extract the full relationship:
   - Row 1 Column 1 → Level 1
   - Row 1 Column 2 (solid bullet) → Level 2 under Level 1
   - Row 1 Column 2 (open bullet) → Level 3 under Level 2
   - Row 1 Column 3 → Level 4 under the relevant Level 2/3

3. PERFORMANCE TEXTS:
   Extract the list of performance texts as a Level 1 topic "Performance Texts"
   Each text as Level 2 (e.g., "Blood Brothers – Willy Russell")

4. OUTPUT FORMAT: Numbered hierarchy
   1. Level 1 Topic (from "Learners should:" column or "Performance Texts")
   1.1. Level 2 Topic (solid bullet from Column 2)
   1.1.1. Level 3 Topic (open bullet from Column 2)
   1.1.1.1. Level 4 Item (synthesized from Column 3)

5. DEPTH REQUIREMENTS:
   - Extract ALL levels - don't stop at Level 2 or 3
   - Ensure Level 4 items are created for every relevant "should be able to" statement
   - Create comprehensive hierarchy with full depth

6. DO NOT ask for confirmation. Extract EVERYTHING NOW.

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
            r'^component\s+0[123]',  # Components 01, 02, 03
            r'^devising\s+drama',
            r'^presenting\s+and\s+performing',
            r'^sections\s+within\s+component',
        ]
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip markdown formatting
            line = re.sub(r'^\*\*|\*\*$', '', line)  # Remove bold markers
            line = re.sub(r'^[-•]\s+', '', line)  # Remove bullets
            
            # Check if excluded
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
    scraper = DramaScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)

