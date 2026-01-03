"""
OCR A-Level Media Studies Manual Structure Scraper
===================================================

Extracts topics from OCR Media Studies H409 specification.

This scraper extracts TWO hierarchies:
1. Assessment Content - what students study (set products)
2. Subject Content - theoretical framework (for flashcards)

Structure - Assessment Content:
- Level 0: Components (H409/01, H409/02)
- Level 1: Sections (Section A, Section B)
- Level 2: Media forms (Newspapers, Film, Radio, etc.)
- Level 3: Set products and requirements

Structure - Subject Content:
- Level 0: Subject Content Framework
- Level 1: Topics (Contexts of Media, Media Language, etc.)
- Level 2: Key Ideas
- Level 3: Learner requirements (bullet points)

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

# AI provider - use OpenAI like the working scrapers
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

PDF_URL = 'https://www.ocr.org.uk/Images/687703-specification-accredited-a-level-gce-media-studies-h409.pdf'


class MediaStudiesScraper:
    """Scraper for OCR A-Level Media Studies."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_pages = []
    
    def scrape_all(self):
        """Scrape all topics."""
        print("\n" + "🎬 "*40)
        print("OCR MEDIA STUDIES SCRAPER")
        print("🎬 "*40)
        
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
        
        # Extract PDF text by page
        self.pdf_pages = self._extract_pdf_pages(pdf_content)
        if not self.pdf_pages:
            return False
        
        # Debug: Save snippet from pages with content
        debug_file = self.debug_dir / "H409-pdf-snippet.txt"
        if len(self.pdf_pages) >= 25:
            snippet = "\n=== PAGE 14 (Content tables start) ===\n" + self.pdf_pages[13] + "\n=== PAGE 23 (Subject content) ===\n" + self.pdf_pages[22]
            debug_file.write_text(snippet, encoding='utf-8')
            print(f"[DEBUG] Saved PDF snippet to {debug_file.name}")
        
        # Get content - starts around page 12-14
        content_pages = self.pdf_pages[11:]  # Start from page 12
        content_text = "\n".join(content_pages)
        
        # Extract all topics (both hierarchies)
        all_topics = self._extract_all_topics(content_text)
        if not all_topics:
            print("[ERROR] No topics extracted")
            return False
        
        # Count by level
        level_counts = {}
        for t in all_topics:
            level_counts[t['level']] = level_counts.get(t['level'], 0) + 1
        level_str = ", ".join([f"L{k}:{v}" for k, v in sorted(level_counts.items())])
        print(f"[OK] Extracted {len(all_topics)} topics ({level_str})")
        
        # Upload
        return self._upload_all(all_topics)
    
    def _extract_pdf_pages(self, pdf_content: bytes) -> List[str]:
        """Extract text from PDF, returning per-page text."""
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
            
            print(f"[OK] Extracted {len(page_texts)} pages")
            return page_texts
        except Exception as e:
            print(f"[ERROR] PDF extraction failed: {e}")
            return []
    
    def _extract_all_topics(self, content_text: str) -> List[Dict]:
        """Extract all topics using AI."""
        
        prompt = f"""You must extract the COMPLETE hierarchy from OCR Media Studies (H409) Subject Content table (section 2e).

CRITICAL: Extract EVERYTHING you can see. Do NOT stop partway. Do NOT ask questions. Extract EVERYTHING NOW.

OUTPUT FORMAT: Use ONLY numbered format (1, 1.1, 1.1.1, 1.1.1.1) - NO bullets, NO markdown.

FIND THE TABLE in section "2e. Subject content for components H409/01 and H409/02"

The table has 3 columns: Topic | Key Idea | Learners must have studied

STRUCTURE (3-4 levels):

Level 0: The 5 main topics from the "Topic" column
Level 1: The "Key Idea" text for each topic
Level 2: Each bullet point from "Learners must have studied" column
Level 3: Theories listed under each topic (if present)

EXAMPLE OUTPUT:
1 Contexts of Media
1.1 Social, cultural, political, economic and historical contexts
1.1.1 how the media products studied differ in institutional backgrounds and use of media language to create meaning
1.1.2 how media products studied can act as a means of reflecting social, cultural and political attitudes towards wider issues and beliefs
1.1.3 how media products studied can act as a means of constructing social, cultural and political attitudes
1.1.4 how media products studied can act as a means of reflecting historical issues and events
1.1.5 how media products studied can potentially be an agent in facilitating social, cultural and political developments
1.1.6 how media products studied are influenced by contexts through intertextual references
1.1.7 how media products studied reflect their economic contexts through production and technological opportunities
2 Media Language
2.1 How the media through their forms, codes, conventions and techniques communicate meanings
2.1.1 how the different modes and language associated with different media forms communicate multiple meanings
2.1.2 how the combination of elements of media language influence meaning
2.1.3 how developing technologies affect media language
2.1.4 the codes and conventions of media forms and products
2.1.5 the dynamic and historically relative nature of genre
2.1.6 the processes through which meanings are established through intertextuality
2.1.7 how audiences respond to and interpret aspects of media language
2.1.8 how genre conventions are socially and historically relative
2.1.9 the significance of challenging or subverting genre conventions
2.1.10 the significance of intertextuality
2.1.11 the way media language incorporates viewpoints and ideologies
2.2 Theories of media language
2.2.1 Semiotics including Barthes
2.2.2 Narratology including Todorov
2.2.3 Genre theory including Neale
2.2.4 Structuralism including Lévi-Strauss
2.2.5 Postmodernism including Baudrillard
3 Media Representations
3.1 How the media portray events, issues, individuals and social groups
3.1.1 (all bullet points)
3.2 Theories of representation
3.2.1 Hall representation theory
3.2.2 Gauntlett theories of identity
3.2.3 Bell Hooks feminist theory
3.2.4 Van Zoonen feminist theory
3.2.5 Butler gender performativity
3.2.6 Gilroy ethnicity and postcolonial theory
4 Media Industries
4.1 (Key idea text)
4.1.1 (all bullet points)
4.2 Theories of media industries
4.2.1 Curran and Seaton
4.2.2 Livingstone and Lunt
4.2.3 Hesmondhalgh
5 Media Audiences
5.1 (Key idea text)
5.1.1 (all bullet points)
5.2 Theories of media audiences
5.2.1 Bandura
5.2.2 Gerbner
5.2.3 Hall reception theory
5.2.4 Jenkins
5.2.5 Shirky

CRITICAL RULES:
1. ONLY extract from the subject content table (section 2e)
2. Extract ALL 5 main topics: Contexts of Media, Media Language, Media Representations, Media Industries, Media Audiences
3. Extract the Key Idea for each topic as Level 1
4. Extract EVERY bullet point from "Learners must have studied" as Level 2
5. Extract theories as separate Level 1 subsections under each topic
6. Do NOT extract the set products sections (2c, 2d) - ONLY the table

FORMAT: Plain text with numbers only (1, 1.1, 1.1.1).

CONTENT:
{content_text[:100000]}"""
        
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
                        timeout=240
                    )
                    ai_output = response.choices[0].message.content
                else:
                    response = claude.messages.create(
                        model="claude-3-5-haiku-20241022",
                        max_tokens=8192,
                        messages=[{"role": "user", "content": prompt}],
                        timeout=240
                    )
                    ai_output = response.content[0].text
                
                # Save AI output
                ai_file = self.debug_dir / "H409-ai-output.txt"
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
        
        return []
    
    def _parse_hierarchy(self, text: str) -> List[Dict]:
        """Parse AI numbered output with special handling for 1000.x and 2000.x prefixes."""
        all_topics = []
        parent_stack = {-1: None}
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Match hierarchical numbers (including 1000.x.x and 2000.x.x format)
            match = re.match(r'^([\d.]+)\s+(.+)$', line)
            if not match:
                continue
            
            number = match.group(1).rstrip('.')
            title = match.group(2).strip()
            
            # Clean title
            title = title.lstrip('*☐✓□■●○-').strip()
            
            # Skip very short titles
            if len(title) < 2:
                continue
            
            # Calculate level: count dots in the number
            dots = number.count('.')
            level = dots
            
            # Generate code
            code = f"H409_{number.replace('.', '_')}"
            parent_code = parent_stack.get(level - 1)
            
            all_topics.append({
                'code': code,
                'title': title,
                'level': level,
                'parent': parent_code
            })
            
            parent_stack[level] = code
            # Clear deeper levels
            for l in list(parent_stack.keys()):
                if l > level:
                    del parent_stack[l]
        
        return all_topics
    
    def _upload_all(self, topics: List[Dict]) -> bool:
        """Upload all topics to Supabase."""
        
        try:
            # Clear old topics NOW (after successful extraction)
            print("\n[INFO] Clearing old Media Studies topics...")
            try:
                temp_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', 'H409').eq('qualification_type', 'A-Level').eq('exam_board', 'OCR').execute()
                if temp_result.data:
                    temp_id = temp_result.data[0]['id']
                    supabase.table('staging_aqa_topics').delete().eq('subject_id', temp_id).execute()
                    print(f"[OK] Cleared old topics for H409")
            except Exception as e:
                print(f"[WARN] Could not clear old topics: {e}")
            
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': "Media Studies (A-Level)",
                'subject_code': 'H409',
                'qualification_type': 'A-Level',
                'specification_url': PDF_URL,
                'exam_board': 'OCR'
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            subject_id = subject_result.data[0]['id']
            print(f"[OK] Subject ID: {subject_id}")
            
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
            import traceback
            traceback.print_exc()
            return False


def main():
    scraper = MediaStudiesScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

