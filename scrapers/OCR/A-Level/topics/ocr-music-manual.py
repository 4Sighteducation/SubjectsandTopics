"""
OCR A-Level Music Manual Structure Scraper
===========================================

Extracts topics from OCR Music H543 specification.

Structure:
- Level 0: Main sections (Core Content, Areas of Study 1-6, Listening and appraising)
- Level 1: Subsections (Outline, Focus for learning, Set Works, etc.)
- Level 2: Bold text categories or List A/List B
- Level 3: Bullet points or prescribed works
- Level 4: Sub-bullets (open circles) or individual pieces

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-music-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/219397-specification-accredited-a-level-gce-music-h543.pdf'


class MusicScraper:
    """Scraper for OCR A-Level Music."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_pages = []
    
    def scrape_all(self):
        """Scrape all topics."""
        print("\n" + "🎵 "*40)
        print("OCR MUSIC SCRAPER")
        print("🎵 "*40)
        
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
        
        # Debug: Save snippets from key pages
        debug_file = self.debug_dir / "H543-pdf-snippet.txt"
        if len(self.pdf_pages) >= 42:
            snippet = "\n=== PAGE 30 (Area of Study 1 Focus) ===\n" + self.pdf_pages[29][:2000]
            snippet += "\n\n=== PAGE 39 (Section 5c - Prescribed Works Areas 1-2) ===\n" + self.pdf_pages[38][:2000]
            snippet += "\n\n=== PAGE 40 (Section 5d - Suggested Repertoire Areas 3-6) ===\n" + self.pdf_pages[39][:2000]
            debug_file.write_text(snippet, encoding='utf-8')
            print(f"[DEBUG] Saved PDF snippet to {debug_file.name}")
        
        # Get content from page 20 onwards
        content_pages = self.pdf_pages[19:]  # Start from page 20
        content_text = "\n".join(content_pages)
        
        # Extract all topics
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
        
        prompt = f"""Please extract the curriculum structure from the OCR Music (H543) specification document below.

Extract the complete topic hierarchy using numbered format (1, 1.1, 1.1.1, etc.). 

Extract the actual text content - do not use placeholders like "(first bold category)" or "(continue...)". Include the real topic names and learning content from the document.

Output format: Simple numbered lines with no bullets or markdown.

STRUCTURE (5 levels):

Level 0: Main sections (8 total)
  1 Core Content (section 2b)
  2 Area of Study 1: Instrumental Music of Haydn, Mozart and Beethoven
  3 Area of Study 2: Popular Song - Blues, Jazz, Swing and Big Band
  4 Area of Study 3: Developments in Instrumental Jazz 1910 to present
  5 Area of Study 4: Religious Music of the Baroque Period
  6 Area of Study 5: Programme Music 1820-1910
  7 Area of Study 6: Innovations in Music 1900 to present
  8 Listening and appraising (section 2g)

IMPORTANT NOTES ON PRESCRIBED/SUGGESTED WORKS:
- Areas 1 & 2: Prescribed works are in section 5c (page 39), organized by YEAR (2025, 2026, 2027, 2028, 2029, 2030)
- Areas 3-6: Suggested repertoire is in section 5d (pages 40+), organized by List A and List B
- Extract ALL works from BOTH sections 5c and 5d

Level 1: Categories within each Area/section
  For Areas 1-6: The BOLD TEXT from Focus for learning section (e.g., "instrumental style", "musical elements")
  For Areas 3-6 ALSO: "Set Works" as a separate L1
  For Core Content: Main categories like "Musical elements and their interdependence"
  For Listening and appraising: "Appraise"
  
  IMPORTANT: Do NOT create "Outline" or "Focus for learning" as topics - go DIRECTLY to the bold text items

Level 2: Content items or List headings
  For bold categories: The bullet points (•) under each bold heading
  For Set Works: "List A" and "List B"

Level 3: Sub-bullets or prescribed works
  For bullet items: Open circle sub-bullets (○)
  For Set Works: Individual composer entries like "Jelly Roll Morton: (i) Wolverine Blues (ii) Black Bottom Stomp"

Level 4: Individual pieces (for multi-piece entries)
  Examples: "Wolverine Blues", "Black Bottom Stomp" (extracted from multi-piece entries)

EXAMPLE OUTPUT:
1 Core Content
1.1 Musical elements and their interdependence
1.1.1 organisation of pitch (melodically and harmonically) including
1.1.1.1 harmonic change
1.1.1.2 cadences e.g. interrupted
1.1.1.3 melodic and harmonic devices
1.1.1.4 complex chord progressions
1.1.1.5 melodic devices such as augmentation
1.1.2 tonality including
1.1.2.1 how keys are related to each other e.g. circle of fifths
1.1.2.2 complex and remote key relationships e.g. enharmonic
(continue for all Core Content...)
2 Area of Study 1: Instrumental Music of Haydn, Mozart and Beethoven
2.1 instrumental style
2.1.1 the characteristics and principles of instrumental music in the Classical period
2.1.2 the forms and style of the Classical period as found in the music of Haydn, Mozart and Beethoven
2.2 musical elements
2.2.1 the orchestra and instruments of the Classical period
2.2.2 the use of instrumental techniques including articulation
2.2.3 instrumentation and texture
2.3 Prescribed Works
2.3.1 2025
2.3.1.1 Haydn: Symphony No. 103 in E flat major, 'Drum Roll' (1795), first and second movements
2.3.2 2026
2.3.2.1 Mozart: Sinfonia Concertante in E flat major, K. 364 (1779-80), first movement
2.3.3 2027
2.3.3.1 Beethoven: Piano Sonata No. 32 in C minor, Op. 111 (1821-22)
2.3.4 2028
2.3.4.1 Haydn: Symphony No. 39 in G minor, Hob. I:39 (1765)
2.3.5 2029
2.3.5.1 Beethoven: Symphony No. 7 in A major, Op. 92 (1811-12), first movement
2.3.6 2030
2.3.6.1 Mozart: Piano Concerto No. 22 in E flat major, K.482 (1785), third movement
3 Area of Study 2: Popular Song - Blues, Jazz, Swing and Big Band
3.1 melody and rhythm
3.1.1 the characteristics of melody and rhythm in blues, jazz, swing and big band
3.1.2 use of syncopation and swing rhythms
3.2 harmony and tonality
3.2.1 the use of blues scales and harmony
3.3 Prescribed Works
3.2.1 2025
3.2.1.1 Cécile McLorin Salvant: For One To Love (2015): (i) Wives And Lovers (ii) The Trolley Song (iii) What's The Matter Now? (iv) Le Mal De Vivre
3.2.1.1.1 Wives And Lovers
3.2.1.1.2 The Trolley Song
3.2.1.1.3 What's The Matter Now?
3.2.1.1.4 Le Mal De Vivre
3.2.2 2026
3.2.2.1 Bessie Smith: (i) Young Woman's Blues (ii) Back Water Blues (iii) Alexander's Rag Time Band (iv) Nobody Knows You When You're Down And Out
(continue...)
4 Area of Study 3: Developments in Instrumental Jazz 1910 to present
4.1 (first bold category from Focus for learning)
4.1.1 (bullet points)
4.2 (next bold category)
4.3 Suggested Repertoire
4.3.1 List A
4.3.1.1 Jelly Roll Morton: (i) Wolverine Blues (ii) Black Bottom Stomp
4.3.1.1.1 Wolverine Blues
4.3.1.1.2 Black Bottom Stomp
4.3.1.2 James P. Johnson: You've got to be modernistic
4.3.1.3 Duke Ellington: (i) Ko-ko (ii) Harlem Airshaft (iii) Cottontail (iv) Prelude to a Kiss
4.3.1.3.1 Ko-ko
4.3.1.3.2 Harlem Airshaft
4.3.1.3.3 Cottontail
4.3.1.3.4 Prelude to a Kiss
4.3.2 List B
4.3.2.1 Bix Beiderbecke: Singin' the Blues
4.3.2.2 Louis Armstrong: (i) Hotter than that (ii) West End Blues (iii) Heebie Jeebies (iv) Alligator Crawl
(continue for all List B...)
5 Area of Study 4: Religious Music of the Baroque Period
5.1 sacred music contexts
5.1.1 the characteristics of Baroque sacred music
5.2 Suggested Repertoire
5.2.1 List A
5.2.1.1 Schütz: Symphoniae sacrae I (1629)
5.2.1.2 Carissimi: Jephte
5.2.2 List B
5.2.2.1 Monteverdi: Vespers (1610)
6 Area of Study 5: Programme Music 1820-1910
6.1 programme music characteristics
6.2 Suggested Repertoire
6.2.1 List A
6.2.1.1 Mendelssohn: Hebrides overture Fingal's Cave
6.2.2 List B
7 Area of Study 6: Innovations in Music 1900 to present
7.1 innovations in music
7.2 Suggested Repertoire
7.2.1 List A
7.2.2 List B
8 Listening and appraising
8.1 Appraise
8.1.1 analyse and evaluate music in aural and written form
(continue...)
3 Area of Study 2: Popular Song - Blues, Jazz, Swing and Big Band
(continue...)
4 Area of Study 3: Developments in Instrumental Jazz 1910 to present
4.1 Outline
(outline content...)
4.2 Focus for learning
(focus content...)
4.3 Set Works
4.3.1 List A
4.3.1.1 Jelly Roll Morton: (i) Wolverine Blues (ii) Black Bottom Stomp
4.3.1.1.1 Wolverine Blues
4.3.1.1.2 Black Bottom Stomp
4.3.1.2 James P. Johnson: You've got to be modernistic
4.3.1.3 Duke Ellington: (i) Ko-ko (ii) Harlem Airshaft (iii) Cottontail (iv) Prelude to a Kiss
4.3.1.3.1 Ko-ko
4.3.1.3.2 Harlem Airshaft
4.3.1.3.3 Cottontail
4.3.1.3.4 Prelude to a Kiss
4.3.1.4 Dizzy Gillespie: (i) Things to come (ii) Manteca
4.3.1.5 Miles Davis: So What from Kind of Blue
4.3.1.6 Herbie Hancock: (i) Maiden Voyage (ii) Chameleon
4.3.1.7 Ornette Coleman: Civilization Day
4.3.2 List B
4.3.2.1 Bix Beiderbecke: Singin' the Blues
4.3.2.2 Louis Armstrong: (i) Hotter than that (ii) West End Blues (iii) Heebie Jeebies (iv) Alligator Crawl
4.3.2.2.1 Hotter than that
4.3.2.2.2 West End Blues
4.3.2.2.3 Heebie Jeebies
4.3.2.2.4 Alligator Crawl
(continue for all List B...)
5 Area of Study 4: Religious Music of the Baroque Period
5.1 Outline
5.2 Focus for learning
5.3 Set Works
5.3.1 List A
5.3.1.1 Schütz: Symphoniae sacrae I (1629)
5.3.1.2 Carissimi: Jephte
5.3.1.3 Pelham Humfrey: By the waters of Babylon
5.3.1.4 Purcell: Anthem My heart is inditing
5.3.1.5 Alessandro Scarlatti: Sedecia, Re Di Gerusalemme (1706)
5.3.1.6 Bach: cantata Christ unser Herr zum Jordan kam, BWV 7
5.3.1.7 Handel: Chandos anthem, O Praise the Lord with one consent
5.3.1.8 Handel: Messiah
5.3.2 List B
5.3.2.1 Monteverdi: Vespers (1610)
5.3.2.2 Allegri: Missa Vidi Turbam Magnam
5.3.2.3 Schütz: St Matthew Passion (1666)
5.3.2.4 Purcell: Hear my prayer, O Lord
5.3.2.5 Vivaldi: Gloria in D major
5.3.2.6 Bach: Magnificat in D
5.3.2.7 Bach: St Matthew Passion
5.3.2.8 Rameau: grand motet Quam dilecta
5.3.2.9 Handel: Jeptha
6 Area of Study 5: Programme Music 1820-1910
6.1 Outline
6.2 Focus for learning
6.3 Set Works
6.3.1 List A
(extract all from List A...)
6.3.2 List B
(extract all from List B...)
7 Area of Study 6: Innovations in Music 1900 to present
7.1 Outline
7.2 Focus for learning
7.3 Set Works
7.3.1 List A
(extract all from List A...)
7.3.2 List B
(extract all from List B...)
(continue for all areas...)
8 Listening and appraising
8.1 Appraise
8.1.1 analyse and evaluate music in aural and written form
8.1.1.1 repertoire within the Areas of Study
8.1.1.2 musical interpretations
8.1.1.3 others' work including unfamiliar music
(continue...)

Key extraction points:
- Extract 8 main sections as shown in the example
- For Areas of Study: Extract the bold text categories (like "instrumental style", "musical elements")
- Under each bold category: Extract the bullet points
- Include "Prescribed Works" or "Suggested Repertoire" sections with all the musical works listed
- For Core Content: Extract "Musical elements and their interdependence" with all sub-items
- Extract all the actual text - not placeholders

FORMAT: Plain text with numbers only (1, 1.1, 1.1.1, 1.1.1.1, 1.1.1.1.1).

CONTENT (includes sections 2b-2g AND sections 5c-5d with all prescribed/suggested works):
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
                ai_file = self.debug_dir / "H543-ai-output.txt"
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
        """Parse AI numbered output."""
        all_topics = []
        parent_stack = {-1: None}
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Match hierarchical numbers (up to 5 levels: 1.1.1.1.1)
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
            
            dots = number.count('.')
            level = dots
            
            # Generate code
            code = f"H543_{number.replace('.', '_')}"
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
            print("\n[INFO] Clearing old Music topics...")
            try:
                temp_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', 'H543').eq('qualification_type', 'A-Level').eq('exam_board', 'OCR').execute()
                if temp_result.data:
                    temp_id = temp_result.data[0]['id']
                    supabase.table('staging_aqa_topics').delete().eq('subject_id', temp_id).execute()
                    print(f"[OK] Cleared old topics for H543")
            except Exception as e:
                print(f"[WARN] Could not clear old topics: {e}")
            
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': "Music (A-Level)",
                'subject_code': 'H543',
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
    scraper = MusicScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

