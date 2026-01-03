"""
OCR A-Level Geology Manual Structure Scraper
=============================================

Extracts topics from OCR Geology H414 specification.

Structure:
- Level 0: Modules (1-7)
- Level 1: Numbered topics (2.1, 2.2, etc.)
- Level 2: Sub-topics (2.1.1, 2.1.2, etc.)
- Level 3: Letter outcomes (a), (b), (c) from "Learning outcomes" column
- Level 4: Sub-outcomes (i), (ii) - ONLY when parent letter has a title

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-geology-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/322105-specification-accredited-a-level-gce-geology-h414.pdf'


class GeologyScraper:
    """Scraper for OCR A-Level Geology."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_text = None
    
    def scrape_all(self):
        """Scrape all modules."""
        print("\n" + "🪨 "*40)
        print("OCR GEOLOGY SCRAPER")
        print("🪨 "*40)
        
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
        self.pdf_text = self._extract_pdf_text(pdf_content)
        if not self.pdf_text:
            return False
        
        # Extract modules separately to handle large content
        all_topics = []
        module_list = [
            ('Module 1: Development of practical skills in geology', 1),
            ('Module 2: Foundations in geology', 2),
            ('Module 3: Global tectonics', 3),
            ('Module 4: Interpreting the past', 4),
            ('Module 5: Petrology', 5),
            ('Module 6: Geohazards', 6),
            ('Module 7: Basin analysis', 7)
        ]
        
        for module_name, module_num in module_list:
            print(f"\n[INFO] Extracting {module_name}...")
            topics = self._extract_module(module_name, module_num)
            if topics:
                all_topics.extend(topics)
                print(f"[OK] Found {len(topics)} items")
            else:
                print(f"[WARN] No content for {module_name}")
            time.sleep(1)
        
        if not all_topics:
            print("[WARN] No topics extracted")
            return False
        
        # Count by level
        level_counts = {}
        for t in all_topics:
            level_counts[t['level']] = level_counts.get(t['level'], 0) + 1
        level_str = ", ".join([f"L{k}:{v}" for k, v in sorted(level_counts.items())])
        print(f"\n[OK] Total extracted: {len(all_topics)} topics ({level_str})")
        
        # Upload
        return self._upload_subject(all_topics)
    
    def _extract_pdf_text(self, pdf_content: bytes) -> Optional[str]:
        """Extract text from PDF."""
        try:
            import pdfplumber
            from io import BytesIO
            
            print("[INFO] Extracting PDF text...")
            text = ""
            with pdfplumber.open(BytesIO(pdf_content)) as pdf:
                for i, page in enumerate(pdf.pages):
                    if page.extract_text():
                        text += page.extract_text() + "\n"
                    if i % 20 == 0 and i > 0:
                        print(f"[INFO] Processed {i+1}/{len(pdf.pages)} pages...")
            
            print(f"[OK] Extracted {len(text)} characters")
            return text
        except Exception as e:
            print(f"[ERROR] PDF extraction failed: {e}")
            return None
    
    def _extract_module(self, module_name: str, module_num: int) -> List[Dict]:
        """Extract one module using AI."""
        
        # Find this module in the PDF
        pattern = re.escape(module_name)
        match = re.search(pattern, self.pdf_text, re.IGNORECASE)
        
        if not match:
            print(f"[WARN] Could not find {module_name}")
            return []
        
        start = match.start()
        # Find end: next module or end markers
        next_module = module_num + 1
        end_patterns = [
            rf'\nModule {next_module}:',
            r'\nAppendix',
            r'\nSummary of updates',
            r'\n3\s+Assessment'
        ]
        end_pos = len(self.pdf_text)
        for ep in end_patterns:
            end_match = re.search(ep, self.pdf_text[start+100:start+50000])
            if end_match:
                end_pos = start + 100 + end_match.start()
                break
        
        section_text = self.pdf_text[start:end_pos]
        print(f"[DEBUG] Module section: {len(section_text)} chars")
        
        prompt = f"""Extract the complete hierarchy for {module_name}, including ALL content from the "Learning outcomes" column in tables.

MODULE: {module_name}

The specification has tables with these columns:
- Topic column: shows numbered topics (e.g., "2.1.1 Minerals")
- Learning outcomes column: has letter outcomes (a), (b), (c), etc.
- Additional guidance column: IGNORE this

STRUCTURE:
- Level 0: Module name
- Level 1: Main numbered topics (e.g., "2.1 Minerals and rocks")
- Level 2: Sub-topics (e.g., "2.1.1 Minerals", "2.1.3 Sedimentary rocks")
- Level 3: Letter outcomes (a), (b), (c) from Learning outcomes
- Level 4: Roman numerals (i), (ii) when parent ends with colon

OUTPUT FORMAT:
{module_num} {module_name}
{module_num}.1 2.1 Minerals and rocks
{module_num}.1.1 2.1.1 Minerals
{module_num}.1.1.1 (a) minerals as naturally occurring elements and inorganic compounds whose composition can be expressed as a chemical formula
{module_num}.1.1.2 (b) rock-forming silicate minerals as crystalline materials...
{module_num}.1.1.3 (c) the diagnostic physical properties of rock-forming minerals
{module_num}.1.1.3.1 (i) the diagnostic physical properties...
{module_num}.1.1.3.2 (ii) the classification of samples...
{module_num}.1.2 2.1.2 Igneous rocks
{module_num}.1.2.1 (a) crystallisation processes...
(continue for ALL topics in this module...)

CRITICAL:
- Start with "{module_num} {module_name}"
- Extract EVERY letter outcome (a), (b), (c), etc.
- Extract EVERY roman numeral (i), (ii), (iii), etc.
- Include complete descriptive text

SECTION TEXT:
{section_text[:40000]}"""
        
        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if AI_PROVIDER == "openai":
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=16000,
                        temperature=0,
                        timeout=180
                    )
                    ai_output = response.choices[0].message.content
                else:
                    response = claude.messages.create(
                        model="claude-3-5-haiku-20241022",
                        max_tokens=16000,
                        messages=[{"role": "user", "content": prompt}],
                        timeout=180
                    )
                    ai_output = response.content[0].text
                
                # Save AI output for this module
                safe_module = re.sub(r'[^\w\-]', '_', module_name)
                ai_file = self.debug_dir / f"H414-{safe_module}-ai-output.txt"
                ai_file.write_text(ai_output, encoding='utf-8')
                print(f"[DEBUG] Saved to {ai_file.name}")
                
                return self._parse_hierarchy(ai_output)
                
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
    
    def _parse_hierarchy(self, text: str) -> List[Dict]:
        """Parse AI numbered output."""
        all_topics = []
        parent_stack = {-1: None}
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Match lines like: "1.1.1.1 (a) text" or "1.1.1" or "(a) text"
            # Extract the full numbering part and the title
            match = re.match(r'^([\d.]+(?:\s*\([a-z]\)|\s*\([ivx]+\))?)\s+(.+)$', line)
            if not match:
                continue
            
            full_number = match.group(1).strip()
            title = match.group(2).strip()
            
            # Skip short titles (but allow letters and romans without long text)
            if len(title) < 2 and not re.search(r'\([a-z]\)|\([ivx]+\)', full_number):
                continue
            
            # Parse the full number to get level and code
            # Use the FULL AI-generated number as the code - it's already unique!
            if ' (' in full_number:
                # Has letter or roman: "1.1.1.1 (a)" or "2.1.3.5 (i)"
                # Use COMPLETE path: "1.1.1.1 (a)" → "1_1_1_1_a"
                parts = full_number.split(' ')
                base_number = parts[0]
                letter_or_roman = parts[1].strip('()')
                
                # Create code from complete path
                number = f"{base_number}_{letter_or_roman}"
                
                if re.match(r'^[a-z]$', letter_or_roman):
                    # Letter like (a), (b)
                    level = 3
                elif re.match(r'^[ivx]+$', letter_or_roman):
                    # Roman like (i), (ii)
                    # Check if parent (level 3) ends with colon
                    parent_3 = parent_stack.get(3)
                    if parent_3:
                        parent_topic = next((t for t in all_topics if t['code'] == parent_3), None)
                        if parent_topic and parent_topic['title'].rstrip().endswith(':'):
                            level = 4
                        else:
                            level = 3
                    else:
                        level = 3
                else:
                    continue
            else:
                # Just numbers: "1", "1.1", "1.1.1"
                number = full_number
                dots = number.count('.')
                level = dots
            
            # Create unique code using the full path
            code = f"H414_{number.replace('.', '_')}"
            parent_code = parent_stack.get(level - 1)
            
            all_topics.append({
                'code': code,
                'title': title,
                'level': level,
                'parent': parent_code
            })
            
            parent_stack[level] = code
            for l in list(parent_stack.keys()):
                if l > level:
                    del parent_stack[l]
        
        return all_topics
    
    def _upload_subject(self, topics: List[Dict]) -> bool:
        """Upload to Supabase."""
        
        try:
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': "Geology (A-Level)",
                'subject_code': 'H414',
                'qualification_type': 'A-Level',
                'specification_url': PDF_URL,
                'exam_board': 'OCR'
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            subject_id = subject_result.data[0]['id']
            print(f"[OK] Subject ID: {subject_id}")
            
            # Clear old topics
            supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
            
            # Insert topics
            to_insert = [{
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': t['title'],
                'topic_level': t['level'],
                'exam_board': 'OCR'
            } for t in topics]
            
            inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
            print(f"[OK] Uploaded {len(inserted.data)} topics")
            
            # Link hierarchy
            code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
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
            
            print(f"[OK] Linked {linked} relationships")
            return True
            
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            return False


def main():
    scraper = GeologyScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

