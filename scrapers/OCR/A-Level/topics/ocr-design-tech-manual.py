"""
OCR A-Level Design and Technology Manual Structure Scraper
===========================================================

Extracts 3 separate subjects from one PDF:
- Design Engineering (H404)
- Fashion and Textiles (H405)
- Product Design (H406)

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-design-tech-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/304609-specification-accredited-a-level-gce-design-and-technology-h404-h406.pdf'

# 3 subjects in one PDF
SUBJECTS = [
    {
        'name': 'Design and Technology: Design Engineering',
        'code': 'H404',
        'section_marker': '2e. Design Engineering',
        'section_pattern': r'2e\.\s+Design Engineering'
    },
    {
        'name': 'Design and Technology: Fashion and Textiles',
        'code': 'H405',
        'section_marker': '2f. Fashion and Textiles',
        'section_pattern': r'2f\.\s+Fashion and Textiles'
    },
    {
        'name': 'Design and Technology: Product Design',
        'code': 'H406',
        'section_marker': '2g. Product Design',
        'section_pattern': r'2g\.\s+Product Design'
    }
]

# Topic areas (shared across all 3 subjects)
TOPIC_AREAS = [
    'Identifying requirements',
    'Learning from existing products and practice',
    'Implications of wider issues',
    'Design thinking and communication',
    'Material and component considerations',
    'Technical understanding',
    'Manufacturing processes and techniques',
    'Viability of design solutions',
    'Health and safety'
]


class DesignTechScraper:
    """Scraper for all 3 Design & Technology subjects."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_text = None
    
    def scrape_all(self):
        """Scrape all 3 subjects."""
        print("\n" + "🎨 "*40)
        print("OCR DESIGN & TECHNOLOGY SCRAPER")
        print("🎨 "*40)
        
        # Download PDF once
        print("\n[INFO] Downloading PDF...")
        try:
            response = requests.get(PDF_URL, timeout=60)
            response.raise_for_status()
            pdf_content = response.content
            print(f"[OK] Downloaded {len(pdf_content)/1024/1024:.1f} MB")
        except Exception as e:
            print(f"[ERROR] PDF download failed: {e}")
            return False
        
        # Extract PDF text once
        self.pdf_text = self._extract_pdf_text(pdf_content)
        if not self.pdf_text:
            return False
        
        # Process each subject
        success_count = 0
        for subject in SUBJECTS:
            print("\n" + "="*80)
            print(f"Processing: {subject['name']} ({subject['code']})")
            print("="*80)
            
            if self._process_subject(subject):
                success_count += 1
            time.sleep(2)
        
        print("\n" + "="*80)
        print(f"✅ Completed: {success_count}/{len(SUBJECTS)} subjects successful")
        print("="*80)
        return success_count == len(SUBJECTS)
    
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
    
    def _process_subject(self, subject: Dict) -> bool:
        """Process one subject."""
        
        # Find the section in PDF
        section_text = self._find_section(subject)
        if not section_text:
            print(f"[WARN] Could not find section for {subject['code']}")
            return False
        
        print(f"[DEBUG] Found section: {len(section_text)} chars")
        
        # Extract topics with AI
        topics = self._extract_topics(subject, section_text)
        if not topics:
            print(f"[WARN] No topics extracted for {subject['code']}")
            return False
        
        # Count by level
        level_counts = {}
        for t in topics:
            level_counts[t['level']] = level_counts.get(t['level'], 0) + 1
        level_str = ", ".join([f"L{k}:{v}" for k, v in sorted(level_counts.items())])
        print(f"[OK] Extracted {len(topics)} topics ({level_str})")
        
        # Upload
        return self._upload_subject(subject, topics)
    
    def _find_section(self, subject: Dict) -> Optional[str]:
        """Find the section for this subject in the PDF."""
        
        pattern = subject['section_pattern']
        matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE))
        
        if not matches:
            return None
        
        # Take the longest match (main content, not TOC)
        best_section = None
        best_length = 0
        
        for match in matches:
            start = match.start()
            # Find end: next section (2f, 2g, 2h, etc.)
            end_patterns = [r'\n2[fgh]\.\s+', r'\nVersion \d+\.\d+']
            end_pos = len(self.pdf_text)
            for ep in end_patterns:
                end_match = re.search(ep, self.pdf_text[start+2000:start+80000])
                if end_match:
                    end_pos = start + 2000 + end_match.start()
                    break
            
            section = self.pdf_text[start:end_pos]
            if len(section) > best_length:
                best_length = len(section)
                best_section = section
        
        return best_section if best_length > 3000 else None
    
    def _extract_topics(self, subject: Dict, section_text: str) -> List[Dict]:
        """Extract topics using AI."""
        
        prompt = f"""Extract the complete hierarchy from this OCR Design & Technology specification section.

SUBJECT: {subject['name']} ({subject['code']})

STRUCTURE (4 levels):
- Level 0: Topic areas (e.g., "1. Identifying requirements")
- Level 1: Main sections (e.g., "Considerations")
- Level 2: Numbered items (e.g., "1.1 What can be learnt by exploring contexts...")
- Level 3: Learning outcomes (labeled "a.", with sub-points "i.", "ii.", "iii.", "iv.")

OUTPUT FORMAT:
1. Identifying requirements
1.1 Considerations
1.1.1 What can be learnt by exploring contexts that design solutions are intended for?
1.1.1.1 Understand that all design practice is context dependent and that investigations are required to identify what makes a context distinct in relation to environment and surroundings
1.1.1.2 user requirements
1.1.1.3 economic and market considerations
1.1.1.4 product opportunities
1.1.2 What can be learnt by undertaking stakeholder analysis?
1.1.2.1 Demonstrate an understanding of methods used for investigating stakeholder requirements
2. Learning from existing products and practice
(continue...)

CRITICAL INSTRUCTIONS:
1. Extract ALL 9 topic areas
2. For each topic area, extract ALL subsections
3. For each subsection, extract ALL numbered items (1.1, 1.2, etc.)
4. For each numbered item, extract ALL learning outcomes (a., b., c.) and their sub-points (i., ii., iii.)
5. Convert to sequential numbering (ignore PDF's original labels)
6. Must maintain 4-level hierarchy

SECTION TEXT:
{section_text[:60000]}"""
        
        try:
            if AI_PROVIDER == "openai":
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=16000,
                    temperature=0
                )
                ai_output = response.choices[0].message.content
            else:
                response = claude.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=8000,
                    messages=[{"role": "user", "content": prompt}]
                )
                ai_output = response.content[0].text
            
            # Save AI output
            safe_code = re.sub(r'[^\w\-]', '_', subject['code'])
            ai_file = self.debug_dir / f"{safe_code}-ai-output.txt"
            ai_file.write_text(ai_output, encoding='utf-8')
            print(f"[DEBUG] Saved AI output to {ai_file.name}")
            
            return self._parse_hierarchy(ai_output, subject['code'])
        except Exception as e:
            print(f"[ERROR] AI extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_hierarchy(self, text: str, subject_code: str) -> List[Dict]:
        """Parse AI numbered output."""
        all_topics = []
        parent_stack = {-1: None}  # -1 maps to None (root)
        
        # Headers to exclude from topics
        EXCLUDED_HEADERS = ['considerations', 'maths & science', 'maths and science']
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            match = re.match(r'^([\d.]+)[\.\):]?\s+(.+)$', line)
            if not match:
                continue
            
            number = match.group(1).rstrip('.')
            title = match.group(2).strip()
            
            # Skip if title is too short
            if len(title) < 3:
                continue
            
            dots = number.count('.')
            level = dots  # 0 dots = L0, 1 dot = L1, etc.
            code = f"{subject_code}_{number.replace('.', '_')}"
            parent_code = parent_stack.get(level - 1)
            
            # FILTER OUT: Skip "Considerations" and "Maths & Science" headers
            if title.lower() in EXCLUDED_HEADERS:
                print(f"[DEBUG] Skipped excluded header: {title}")
                # Still update parent_stack so children can find grandparent
                parent_stack[level] = parent_code  # Pass through grandparent
                for l in list(parent_stack.keys()):
                    if l > level:
                        del parent_stack[l]
                continue
            
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
    
    def _upload_subject(self, subject: Dict, topics: List[Dict]) -> bool:
        """Upload one subject to Supabase."""
        
        try:
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': f"{subject['name']} (A-Level)",
                'subject_code': subject['code'],
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
    scraper = DesignTechScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
