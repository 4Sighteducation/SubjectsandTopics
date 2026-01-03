"""
OCR A-Level Computer Science Manual Structure Scraper
======================================================

APPROACH:
1. Manually define Level 0 (Components)
2. Scrape PDF to extract 4-level hierarchy from tables

Hierarchy in PDF:
- Level 1: Labeled as "1.1" (e.g., "1.1 The characteristics of contemporary processors...")
- Level 2: Unlabeled row headers (e.g., "Components of a computer and their uses")
- Level 3: Labeled as "1.1.1" (e.g., "1.1.1 Structure and function of the processor")
- Level 4: Labeled as "(a), (b), (c)" (learning outcomes)

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-computer-science-manual.py
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
openai_key = os.getenv('OPENAI_API_KEY')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')
gemini_key = os.getenv('GEMINI2.5_API_KEY') or os.getenv('GEMINI_API_KEY')

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

# Determine AI provider - PREFER OPENAI
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
    print("[ERROR] No AI API keys found!")
    sys.exit(1)


# ================================================================
# MANUAL STRUCTURE DEFINITION
# ================================================================

SUBJECT_INFO = {
    'name': 'Computer Science',
    'code': 'H446',
    'qualification': 'A-Level',
    'exam_board': 'OCR',
    'pdf_url': 'https://www.ocr.org.uk/Images/170844-specification-accredited-a-level-gce-computer-science-h446.pdf'
}

# MANUAL STRUCTURE: Level 0 only
MANUAL_STRUCTURE = [
    {
        'code': 'Component01',
        'title': 'Component 01: Computer systems',
        'level': 0,
        'parent': None
    },
    {
        'code': 'Component02',
        'title': 'Component 02: Algorithms and programming',
        'level': 0,
        'parent': None
    }
]


class ComputerScienceScraper:
    """Manual structure + PDF detail scraper for Computer Science."""
    
    def __init__(self):
        self.subject = SUBJECT_INFO
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
    
    def build_manual_structure(self) -> List[Dict]:
        """Build the manual Level 0 structure."""
        print("\n" + "="*80)
        print("STEP 1: Building Manual Structure (Level 0)")
        print("="*80)
        
        topics = []
        for component in MANUAL_STRUCTURE:
            topics.append({
                'code': component['code'],
                'title': component['title'],
                'level': component['level'],
                'parent': component['parent']
            })
            print(f"[L0] {component['code']}: {component['title']}")
        
        print(f"\n[OK] Manual structure: {len(topics)} topics")
        return topics
    
    def scrape_pdf_details(self, manual_topics: List[Dict]) -> List[Dict]:
        """Download PDF and extract all level hierarchy."""
        print("\n" + "="*80)
        print("STEP 2: Scraping PDF for Content Hierarchy")
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
            return manual_topics
        
        # Extract PDF text
        pdf_text = self._extract_pdf_text(pdf_content)
        if not pdf_text:
            return manual_topics
        
        all_topics = manual_topics.copy()
        
        # Process each component
        for component in manual_topics:
            if component['level'] == 0:
                print(f"\n[INFO] Processing: {component['title']}")
                details = self._extract_component_content(
                    component['title'],
                    pdf_text,
                    component['code'],
                    base_level=1
                )
                if details:
                    # Count by level
                    level_counts = {}
                    for d in details:
                        level_counts[d['level']] = level_counts.get(d['level'], 0) + 1
                    level_str = ", ".join([f"L{k}:{v}" for k, v in sorted(level_counts.items())])
                    print(f"[OK] Found {len(details)} items for {component['code']} ({level_str})")
                    all_topics.extend(details)
                time.sleep(1)
        
        print(f"\n[OK] Total topics: {len(all_topics)}")
        return all_topics
    
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
            self.debug_dir.joinpath(f"{self.subject['code']}-spec.txt").write_text(text, encoding='utf-8')
            return text
        except Exception as e:
            print(f"[ERROR] PDF extraction failed: {e}")
            return None
    
    def _extract_component_content(self, component_title: str, pdf_text: str, parent_code: str, base_level: int) -> List[Dict]:
        """Extract all content for a component."""
        
        # Extract the short name (e.g., "Computer systems" from "Component 01: Computer systems")
        if ":" in component_title:
            short_name = component_title.split(":", 1)[1].strip()
        else:
            short_name = component_title
        
        component_num = "01" if "01" in parent_code else "02"
        
        # Search for the section with various patterns
        search_patterns = [
            rf'Content of {re.escape(short_name)} \(Component {component_num}\)',
            rf'2c\.\s+Content of {re.escape(short_name)}',
            rf'Content of {re.escape(component_title)}',
        ]
        
        section_text = None
        for pattern in search_patterns:
            matches = list(re.finditer(pattern, pdf_text, re.DOTALL | re.IGNORECASE))
            if matches:
                for match in matches:
                    start = match.start()
                    # Find end: next component or appendix
                    end_patterns = [r'\n3\.', r'\n2d\.', r'Appendix', r'Version \d+\.\d+']
                    end_pos = len(pdf_text)
                    for ep in end_patterns:
                        end_match = re.search(ep, pdf_text[start+1000:start+50000])
                        if end_match:
                            end_pos = start + 1000 + end_match.start()
                            break
                    
                    potential_section = pdf_text[start:end_pos]
                    if len(potential_section) > 2000:
                        section_text = potential_section
                        break
                break
        
        if not section_text:
            print(f"[WARN] Could not find section for {component_title}")
            return []
        
        print(f"[DEBUG] Found section: {len(section_text)} chars")
        
        # Use AI to extract the complex hierarchy
        prompt = f"""Extract the complete hierarchy from this OCR Computer Science component section.

COMPONENT: "{component_title}"

THE PDF STRUCTURE (5 levels):
- Level 1: Major sections (labeled "1.1", "1.2" etc in PDF)
  Example: "1.1 The characteristics of contemporary processors, input, output and storage devices"
  
- Level 2: Unlabeled subsection headers (row headers in table)
  Example: "Components of a computer and their uses"
  
- Level 3: Specific topics (labeled "1.1.1", "1.1.2" etc in PDF)
  Example: "1.1.1 Structure and function of the processor"
  
- Level 4: Learning outcomes (labeled (a), (b), (c) etc)
  Example: "(a) The Arithmetic and Logic Unit; ALU, Control Unit..."

YOUR TASK:
Extract as a numbered hierarchy where:
- Level 1 = 1, 2, 3 (major sections - ignore PDF's "1.1" numbering)
- Level 2 = 1.1, 1.2, 2.1 (subsection headers)
- Level 3 = 1.1.1, 1.1.2, 2.1.1 (specific topics - ignore PDF's original numbering)
- Level 4 = 1.1.1.1, 1.1.1.2 (learning outcomes - ignore PDF's (a), (b))

OUTPUT FORMAT EXAMPLE:
1. The characteristics of contemporary processors, input, output and storage devices
1.1 Components of a computer and their uses
1.1.1 Structure and function of the processor
1.1.1.1 The Arithmetic and Logic Unit; ALU, Control Unit and Registers
1.1.1.2 The Fetch-Decode-Execute Cycle; including its effects on registers
1.1.1.3 The factors affecting the performance of the CPU: clock speed, number of cores, cache
1.1.2 Types of processor
1.1.2.1 The differences between and uses of CISC and RISC processors
1.1.2.2 GPUs and their uses
1.1.3 Input, output and storage
1.1.3.1 How different input, output and storage devices can be applied to the solution of different problems

CRITICAL INSTRUCTIONS:
1. Extract ALL major sections (Level 1)
2. Extract ALL subsection headers (Level 2) - these are often in BOLD or are row headers
3. Extract ALL specific topics (Level 3) - these have the detailed numbering
4. Extract ALL learning outcomes (Level 4) - these are the (a), (b), (c) points
5. Renumber everything sequentially starting from 1
6. Must maintain the 4-level hierarchy

SECTION TEXT:
{section_text[:50000]}"""
        
        try:
            if AI_PROVIDER == "openai":
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=16000,
                    temperature=0
                )
                ai_output = response.choices[0].message.content
            elif AI_PROVIDER == "anthropic":
                response = claude.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=8000,
                    messages=[{"role": "user", "content": prompt}]
                )
                ai_output = response.content[0].text
            elif AI_PROVIDER == "gemini":
                response = gemini_model.generate_content(prompt)
                ai_output = response.text
            
            # Save AI output
            safe_filename = re.sub(r'[^\w\-]', '_', parent_code)
            ai_file = self.debug_dir / f"{safe_filename}-ai-output.txt"
            ai_file.write_text(ai_output, encoding='utf-8')
            print(f"[DEBUG] AI returned {len(ai_output)} chars, saved to {ai_file.name}")
            
            return self._parse_numbered_hierarchy(ai_output, parent_code, base_level)
        except Exception as e:
            print(f"[ERROR] AI extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_numbered_hierarchy(self, text: str, parent_code: str, base_level: int) -> List[Dict]:
        """Parse AI numbered output into topics."""
        topics = []
        parent_stack = {base_level - 1: parent_code}
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Match numbered items
            match = re.match(r'^([\d.]+)[\.\):]?\s+(.+)$', line)
            if not match:
                continue
            
            number = match.group(1).rstrip('.')
            title = match.group(2).strip()
            
            if len(title) < 3:
                continue
            
            dots = number.count('.')
            level = base_level + dots
            code = f"{parent_code}_{number.replace('.', '_')}"
            parent_code_for_this = parent_stack.get(level - 1, parent_code)
            
            topics.append({
                'code': code,
                'title': title,
                'level': level,
                'parent': parent_code_for_this
            })
            
            parent_stack[level] = code
            for l in list(parent_stack.keys()):
                if l > level:
                    del parent_stack[l]
        
        return topics
    
    def upload_to_supabase(self, topics: List[Dict]) -> bool:
        """Upload topics to Supabase."""
        print("\n" + "="*80)
        print("STEP 3: Uploading to Supabase")
        print("="*80)
        
        # Deduplicate
        seen = {}
        for t in topics:
            if t['code'] not in seen:
                seen[t['code']] = t
        topics = list(seen.values())
        
        print(f"[INFO] Uploading {len(topics)} topics")
        
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
            print(f"[OK] Subject: {subject_result.data[0]['subject_name']}")
            
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
            
            # Stats
            levels = {}
            for t in topics:
                levels[t['level']] = levels.get(t['level'], 0) + 1
            print("\n[INFO] Hierarchy:")
            for level in sorted(levels.keys()):
                print(f"  Level {level}: {levels[level]} topics")
            
            return True
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def scrape(self) -> bool:
        """Main workflow."""
        print("\n" + "💻 "*40)
        print(f"OCR COMPUTER SCIENCE SCRAPER: {self.subject['name']} ({self.subject['code']})")
        print("💻 "*40)
        
        manual_topics = self.build_manual_structure()
        all_topics = self.scrape_pdf_details(manual_topics)
        
        if not all_topics:
            print("[ERROR] No topics found")
            return False
        
        success = self.upload_to_supabase(all_topics)
        
        if success:
            print("\n[SUCCESS] ✅ Computer Science scraping complete!")
            print(f"Total topics: {len(all_topics)}")
        else:
            print("\n[FAILED] ❌ Upload failed")
        
        return success


def main():
    scraper = ComputerScienceScraper()
    success = scraper.scrape()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

