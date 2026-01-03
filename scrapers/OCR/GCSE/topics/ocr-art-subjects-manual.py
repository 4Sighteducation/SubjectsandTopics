"""
OCR GCSE Art Subjects Manual Scraper
=====================================

Extracts topics from OCR GCSE Art subjects (J170-J176) specification.

Structure (per subject):
- Level 0: Three main sections
  1. Areas of Study
  2. Skills
  3. Knowledge and Understanding
- Level 1: Sub-sections (e.g., "Techniques" under Skills)
- Level 2+: Content items extracted from tables/bullets

Each subject has its own section in the PDF:
- J170: "2c(i). Content of Art and Design: Art, Craft and Design (J170)"
- J171: "2c(ii). Content of Art and Design: Fine Art (J171)"
- J172: "2c(iii). Content of Art and Design: Graphic Communication (J172)"
- J173: "2c(iv). Content of Art and Design: Photography (J173)"
- J174: "2c(v). Content of Art and Design: Textile Design (J174)"
- J175: "2c(vi). Content of Art and Design: Three-Dimensional Design (J175)"
- J176: "2c(vii). Content of Art and Design: Critical and Contextual Studies (J176)"

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-art-subjects-manual.py [--subject-code JXXX]
"""

import os
import sys
import re
import time
import requests
import argparse
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

PDF_URL = 'https://www.ocr.org.uk/Images/220463-specification-accredited-gcse-art-and-design-j170-j176.pdf'

SUBJECTS = {
    'J170': {
        'name': 'Art, Craft and Design',
        'section_pattern': r'2c\(i\)\.\s+Content\s+of\s+Art\s+and\s+Design:\s+Art,\s+Craft\s+and\s+Design\s+\(J170\)',
    },
    'J171': {
        'name': 'Fine Art',
        'section_pattern': r'2c\(ii\)\.\s+Content\s+of\s+Art\s+and\s+Design:\s+Fine\s+Art\s+\(J171\)',
    },
    'J172': {
        'name': 'Graphic Communication',
        'section_pattern': r'2c\(iii\)\.\s+Content\s+of\s+Art\s+and\s+Design:\s+Graphic\s+Communication\s+\(J172\)',
    },
    'J173': {
        'name': 'Photography',
        'section_pattern': r'2c\(iv\)\.\s+Content\s+of\s+Art\s+and\s+Design:\s+Photography\s+\(J173\)',
    },
    'J174': {
        'name': 'Textile Design',
        'section_pattern': r'2c\(v\)\.\s+Content\s+of\s+Art\s+and\s+Design:\s+Textile\s+Design\s+\(J174\)',
    },
    'J175': {
        'name': 'Three-Dimensional Design',
        'section_pattern': r'2c\(vi\)\.\s+Content\s+of\s+Art\s+and\s+Design:\s+Three-Dimensional\s+Design\s+\(J175\)',
    },
    'J176': {
        'name': 'Critical and Contextual Studies',
        'section_pattern': r'2c\(vii\)\.\s+Content\s+of\s+Art\s+and\s+Design:\s+Critical\s+and\s+Contextual\s+Studies\s+\(J176\)',
    }
}

LEVEL_0_TOPICS = [
    'Areas of Study',
    'Skills',
    'Knowledge and Understanding'
]


class ArtSubjectsScraper:
    """Scraper for OCR GCSE Art subjects."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent.parent / "A-Level" / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_text = None
    
    def scrape_all(self, subject_code_filter: Optional[str] = None):
        """Scrape all Art subjects or one specific subject."""
        print("\n" + "🎨 "*40)
        print("OCR GCSE ART SUBJECTS SCRAPER")
        print("🎨 "*40)
        
        # Determine which subjects to process
        if subject_code_filter:
            if subject_code_filter not in SUBJECTS:
                print(f"[ERROR] Invalid subject code: {subject_code_filter}")
                return False
            subjects_to_process = {subject_code_filter: SUBJECTS[subject_code_filter]}
        else:
            subjects_to_process = SUBJECTS
        
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
        
        # Process each subject
        success_count = 0
        for subject_code, subject_info in subjects_to_process.items():
            print(f"\n{'='*80}")
            print(f"[SUBJECT] {subject_info['name']} ({subject_code})")
            print("="*80)
            
            all_topics = self._extract_subject(subject_code, subject_info)
            
            if all_topics:
                print(f"\n[OK] Extracted {len(all_topics)} topics for {subject_code}")
                
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
                if self._upload_topics(subject_code, subject_info['name'], all_topics):
                    success_count += 1
                    print(f"[OK] ✓ Successfully uploaded {subject_code}")
                else:
                    print(f"[FAIL] ✗ Failed to upload {subject_code}")
            else:
                print(f"[FAIL] ✗ No topics extracted for {subject_code}")
        
        print(f"\n{'='*80}")
        print(f"SUMMARY: {success_count}/{len(subjects_to_process)} subjects succeeded")
        print(f"{'='*80}")
        
        return success_count > 0
    
    def _extract_subject(self, subject_code: str, subject_info: Dict) -> List[Dict]:
        """Extract topics for one subject."""
        all_topics = []
        
        # Find subject section in PDF
        section_match = re.search(subject_info['section_pattern'], self.pdf_text, re.IGNORECASE)
        if not section_match:
            print(f"[ERROR] Could not find section for {subject_info['name']}")
            return []
        
        section_start = section_match.start()
        print(f"[DEBUG] Found section at position {section_start}")
        
        # Find end of section (next subject section or end of document)
        next_section_patterns = []
        for code, info in SUBJECTS.items():
            if code != subject_code:
                next_section_patterns.append(info['section_pattern'])
        
        section_end = len(self.pdf_text)
        for pattern in next_section_patterns:
            match = re.search(pattern, self.pdf_text[section_start + 1000:], re.IGNORECASE)
            if match:
                section_end = section_start + 1000 + match.start()
                print(f"[DEBUG] Found next section at position {section_end}")
                break
        
        section_text = self.pdf_text[section_start:section_end]
        print(f"[DEBUG] Extracted section: {len(section_text)} characters")
        
        # Level 0: Subject
        subject_topic = {
            'code': subject_code,
            'title': f"Art and Design - {subject_info['name']} (GCSE)",
            'level': 0,
            'parent': None
        }
        all_topics.append(subject_topic)
        
        # Extract content for each Level 0 topic
        for idx, level0_topic in enumerate(LEVEL_0_TOPICS):
            print(f"\n[INFO] Extracting: {level0_topic}")
            level0_code = f"{subject_code}_{idx + 1}"
            level0_topic_obj = {
                'code': level0_code,
                'title': level0_topic,
                'level': 0,
                'parent': subject_code
            }
            all_topics.append(level0_topic_obj)
            
            # Extract content for this Level 0 topic
            content = self._extract_level0_content(section_text, level0_topic, level0_code, subject_code)
            
            # Filter out any duplicates of Level 0 topic names
            filtered_content = []
            for topic in content:
                title_lower = topic['title'].lower()
                # Skip if this topic matches any Level 0 topic name
                if title_lower not in [t.lower() for t in LEVEL_0_TOPICS]:
                    filtered_content.append(topic)
                else:
                    print(f"[FILTER] Removed duplicate Level 0 topic from content: {topic['title']}")
            all_topics.extend(filtered_content)
        
        return all_topics
    
    def _extract_level0_content(self, section_text: str, level0_topic: str, parent_code: str, subject_code: str) -> List[Dict]:
        """Extract content for a Level 0 topic (Areas of Study, Skills, Knowledge and Understanding)."""
        topics = []
        
        # Find the section for this Level 0 topic within the subject-specific section
        # Look for heading like "Areas of Study", "Skills", "Knowledge and Understanding"
        # Make sure it's a standalone heading (not part of another word)
        pattern = rf"(?:^|\n)\s*{re.escape(level0_topic)}\s*(?:\n|$)"
        match = re.search(pattern, section_text, re.IGNORECASE | re.MULTILINE)
        
        if not match:
            # Try without requiring newlines (might be in a table or formatted differently)
            pattern = rf"\b{re.escape(level0_topic)}\b"
            match = re.search(pattern, section_text, re.IGNORECASE)
        
        if not match:
            print(f"[WARN] Could not find section for {level0_topic}")
            print(f"[DEBUG] Searching in section of length {len(section_text)}")
            print(f"[DEBUG] First 500 chars: {section_text[:500]}")
            return []
        
        # Extract section content (until next Level 0 topic or end)
        section_start = match.start()
        next_level0_patterns = [rf"(?:^|\n)\s*{re.escape(topic)}\s*(?:\n|$)" for topic in LEVEL_0_TOPICS if topic != level0_topic]
        
        section_end = len(section_text)
        for pattern in next_level0_patterns:
            next_match = re.search(pattern, section_text[section_start + 200:], re.IGNORECASE | re.MULTILINE)
            if next_match:
                potential_end = section_start + 200 + next_match.start()
                if potential_end < section_end:
                    section_end = potential_end
                    break
        
        level0_section = section_text[section_start:section_end]
        print(f"[DEBUG] Extracted {level0_topic} section: {len(level0_section)} characters")
        print(f"[DEBUG] First 300 chars: {level0_section[:300]}")
        
        # Save section snippet for debugging
        safe_name = re.sub(r'[^\w\-]', '_', level0_topic)[:50]
        snippet_file = self.debug_dir / f"{subject_code}-{safe_name}-section.txt"
        snippet_file.write_text(level0_section[:5000], encoding='utf-8')
        print(f"[DEBUG] Saved section snippet to {snippet_file.name}")
        
        # Extract content using AI
        print(f"[INFO] Extracting content from {level0_topic} section...")
        extracted_content = self._extract_content_with_ai(level0_section, level0_topic, parent_code, subject_code)
        
        if extracted_content:
            parsed_content = self._parse_content(extracted_content, parent_code)
            topics.extend(parsed_content)
            print(f"[OK] Extracted {len(parsed_content)} topics from {level0_topic}")
        else:
            print(f"[WARN] No content extracted for {level0_topic}")
        
        return topics
    
    def _extract_content_with_ai(self, section_text: str, level0_topic: str, parent_code: str, subject_code: str) -> Optional[str]:
        """Extract content using AI."""
        
        subject_name = SUBJECTS[subject_code]['name']
        
        prompt = f"""You must extract ONLY the content for {subject_name} ({subject_code}) from this OCR GCSE Art and Design specification section.

CRITICAL: You are extracting content for {subject_name} ({subject_code}) ONLY. 
- IGNORE all content from other subjects (J170, J172, J173, J174, J175, J176)
- Extract ONLY content that applies to {subject_name} ({subject_code})
- If you see content mentioning other subjects, SKIP IT

SECTION TO EXTRACT: {level0_topic}

STRUCTURE:
- Level 0: {level0_topic} (already created, parent code: {parent_code})
- Level 1: Headings within {level0_topic} (e.g., "Techniques", "Overview", "Areas of Study" list items)
- Level 2+: Content items under those headings (bullet points, table rows, specific techniques, etc.)

EXTRACTION RULES:
1. Find headings within {level0_topic} section (like "Techniques", "Overview") - these become Level 1 topics
2. Extract all content items under each heading - these become Level 2+ topics
3. For "Areas of Study": Extract the list of areas (e.g., "Drawing", "Painting", "Sculpture")
4. For "Skills": Extract headings like "Techniques" and their content items
5. For "Knowledge and Understanding": Extract all knowledge requirements

CRITICAL: DO NOT extract these as headings or topics:
- "Areas of Study" (this is already the Level 0 parent)
- "Skills" (this is a separate Level 0 topic)
- "Knowledge and Understanding" (this is a separate Level 0 topic)

These three should NEVER appear as Level 1 or Level 2+ topics. Only extract content WITHIN the {level0_topic} section, not the section name itself.

OUTPUT FORMAT:
- Use ONLY numbered format: 1, 1.1, 1.1.1, 1.1.2, etc.
- NO bullets (-), NO asterisks (*), NO markdown (**)
- NO markdown formatting at all
- Each line: NUMBER SPACE TITLE

EXAMPLE FOR "Skills" SECTION:
1 Techniques
1.1 painting (various media)
1.2 drawing (various media)
1.3 printing (e.g., screen printing, etching, aquatint, lithography, block printing)
1.4 stencils
1.5 carving
1.6 modelling
1.7 constructing
2 Use visual language critically
2.1 media
2.2 materials
2.3 techniques
2.4 processes
2.5 technologies

EXAMPLE FOR "Areas of Study" SECTION:
1 Drawing
2 Installation
3 Lens-/Light-based Media
4 Mixed-media
5 Land art
6 Printing
7 Painting
8 Sculpture

REMEMBER:
- Extract ONLY {subject_name} ({subject_code}) content
- Ignore other subjects completely
- Extract EVERYTHING that applies to {subject_name}
- Use numbered format only (1, 1.1, 1.1.1)

SECTION TEXT:
{section_text[:100000]}

EXTRACT NOW - Extract ALL {subject_name} ({subject_code}) content from {level0_topic}:"""
        
        result = self._call_ai(prompt, max_tokens=16000)
        
        # Save AI output for debugging
        if result:
            safe_name = re.sub(r'[^\w\-]', '_', level0_topic)[:50]
            ai_file = self.debug_dir / f"{subject_code}-{safe_name}-ai-output.txt"
            ai_file.write_text(result, encoding='utf-8')
            print(f"[DEBUG] Saved AI output to {ai_file.name}")
        
        return result
    
    def _parse_content(self, text: str, parent_code: str) -> List[Dict]:
        """Parse AI output into topic structure."""
        topics = []
        parent_stack = {0: parent_code}
        
        # Get current subject code from parent_code (e.g., J171_1 -> J171)
        current_subject_code = parent_code.split('_')[0] if '_' in parent_code else parent_code
        
        # Other subject codes to filter out
        other_subject_codes = [code for code in SUBJECTS.keys() if code != current_subject_code]
        other_subject_patterns = [rf'\b{code}\b' for code in other_subject_codes]
        other_subject_names = [info['name'] for code, info in SUBJECTS.items() if code != current_subject_code]
        
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
            
            # Filter out content mentioning other subjects
            title_lower = title.lower()
            skip = False
            for pattern in other_subject_patterns:
                if re.search(pattern, title, re.IGNORECASE):
                    skip = True
                    break
            for other_name in other_subject_names:
                if other_name.lower() in title_lower and current_subject_code not in title:
                    skip = True
                    break
            
            # Skip generic OCR content (Skills Guides, Active Results, etc.)
            generic_patterns = [
                r'skills guides?',
                r'active results',
                r'subject advisor',
                r'ocr\.org\.uk',
                r'download.*guides?',
                r'results analysis',
                r'performance.*students'
            ]
            for pattern in generic_patterns:
                if re.search(pattern, title_lower):
                    skip = True
                    break
            
            # CRITICAL: Filter out Level 0 topic names when they appear as children
            # These should ONLY exist as Level 0 topics, not as sub-topics
            level0_topic_names_lower = [topic.lower() for topic in LEVEL_0_TOPICS]
            if title_lower in level0_topic_names_lower:
                skip = True
                print(f"[FILTER] Skipping duplicate Level 0 topic: {title}")
            
            if skip:
                continue
            
            # Determine level based on number of dots
            dots = number.count('.')
            # Parent is Level 0, so:
            # 1 = 0 dots → Level 1
            # 1.1 = 1 dot → Level 2
            # 1.1.1 = 2 dots → Level 3
            level = dots + 1  # Parent level (0) + dots + 1
            
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
    
    def _upload_topics(self, subject_code: str, subject_name: str, topics: List[Dict]) -> bool:
        """Upload topics to database."""
        try:
            # Format subject name
            formatted_subject_name = f"Art and Design - {subject_name} (GCSE)"
            
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': formatted_subject_name,
                'subject_code': subject_code,
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
    parser = argparse.ArgumentParser(description='OCR GCSE Art Subjects Scraper')
    parser.add_argument('--subject-code', type=str, help='Process only this subject code (e.g., J174)')
    args = parser.parse_args()
    
    scraper = ArtSubjectsScraper()
    success = scraper.scrape_all(subject_code_filter=args.subject_code)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

