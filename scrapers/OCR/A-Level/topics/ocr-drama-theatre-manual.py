"""
OCR A-Level Drama and Theatre Manual Structure Scraper
=======================================================

APPROACH:
1. Manually define Component 3 (Analysing performance) - too complex
2. Scrape Component 4 (Deconstructing texts) - 8 text options

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-drama-theatre-manual.py
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

SUBJECT_INFO = {
    'name': 'Drama and Theatre',
    'code': 'H459',
    'qualification': 'A-Level',
    'exam_board': 'OCR',
    'pdf_url': 'https://www.ocr.org.uk/Images/242650-specification-accredited-a-level-gce-drama-and-theatre-h459.pdf'
}

# MANUAL STRUCTURE
MANUAL_STRUCTURE = [
    {
        'code': 'Component3',
        'title': 'Component 3: Analysing performance (31)',
        'level': 0,
        'parent': None,
        'children': [
            {
                'code': 'Component3_SectionA',
                'title': 'Section A: Exploring performance texts',
                'level': 1,
                'parent': 'Component3',
                'children': [
                    {
                        'code': 'Component3_Theme1',
                        'title': 'Theme 1: Conflict',
                        'level': 2,
                        'parent': 'Component3_SectionA',
                        'texts': ['Black Watch – Gregory Burke', 'Hamlet – William Shakespeare', 'Necessary Targets – Eve Ensler', 
                                  'Oh What a Lovely War – Joan Littlewood', 'The Long and the Short and the Tall – Willis Hall']
                    },
                    {
                        'code': 'Component3_Theme2',
                        'title': 'Theme 2: Family dynamics',
                        'level': 2,
                        'parent': 'Component3_SectionA',
                        'texts': ['A Day In The Death Of Joe Egg – Peter Nichols', 'House of Bernarda Alba – Federico García Lorca', 
                                  'King Lear – William Shakespeare', 'Live Like Pigs – John Arden']
                    },
                    {
                        'code': 'Component3_Theme3',
                        'title': 'Theme 3: Heroes and villains',
                        'level': 2,
                        'parent': 'Component3_SectionA',
                        'texts': ['Amadeus – Peter Shaffer', 'Caligula – Albert Camus', 'Caucasian Chalk Circle – Bertolt Brecht', 
                                  'Frankenstein – Nick Dear', 'Othello – William Shakespeare', 'The Love Of The Nightingale – Timberlake Wertenbaker']
                    }
                ]
            },
            {
                'code': 'Component3_SectionB',
                'title': 'Section B: Live theatre analysis and evaluation',
                'level': 1,
                'parent': 'Component3'
            }
        ]
    },
    {
        'code': 'Component4',
        'title': 'Component 4: Deconstructing texts for performance (41-48)',
        'level': 0,
        'parent': None,
        'children': [
            {'code': 'Component4_41', 'title': 'Antigone – Sophocles (Jean Anouilh) (41)', 'level': 1, 'parent': 'Component4'},
            {'code': 'Component4_42', 'title': 'Cloud Nine – Caryl Churchill (42)', 'level': 1, 'parent': 'Component4'},
            {'code': 'Component4_43', 'title': 'Earthquakes in London – Mike Bartlett (43)', 'level': 1, 'parent': 'Component4'},
            {'code': 'Component4_44', 'title': 'Stockholm – Bryony Lavery (44)', 'level': 1, 'parent': 'Component4'},
            {'code': 'Component4_45', 'title': 'Sweeney Todd: The Demon Barber of Fleet Street (45)', 'level': 1, 'parent': 'Component4'},
            {'code': 'Component4_46', 'title': 'The Crucible – Arthur Miller (46)', 'level': 1, 'parent': 'Component4'},
            {'code': 'Component4_47', 'title': 'The Visit – Friedrich Durrenmatt (47)', 'level': 1, 'parent': 'Component4'},
            {'code': 'Component4_48', 'title': 'Woza Albert! (48)', 'level': 1, 'parent': 'Component4'}
        ]
    }
]


class DramaTheatreScraper:
    """Scraper for Drama and Theatre."""
    
    def __init__(self):
        self.subject = SUBJECT_INFO
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
    
    def build_manual_structure(self) -> List[Dict]:
        """Build manual structure."""
        print("\n" + "="*80)
        print("STEP 1: Building Manual Structure")
        print("="*80)
        
        topics = []
        
        def add_recursive(item, parent_code=None):
            topic = {
                'code': item['code'],
                'title': item['title'],
                'level': item['level'],
                'parent': parent_code
            }
            topics.append(topic)
            
            level_prefix = "  " * item['level']
            print(f"{level_prefix}[L{item['level']}] {item['code']}: {item['title']}")
            
            # Add text lists as L3 if present
            if 'texts' in item:
                for i, text in enumerate(item['texts'], 1):
                    text_topic = {
                        'code': f"{item['code']}_Text{i}",
                        'title': text,
                        'level': item['level'] + 1,
                        'parent': item['code']
                    }
                    topics.append(text_topic)
                    print(f"{level_prefix}  [L{text_topic['level']}] {text_topic['code']}: {text}")
            
            # Recurse
            for child in item.get('children', []):
                add_recursive(child, item['code'])
        
        for component in MANUAL_STRUCTURE:
            add_recursive(component)
        
        print(f"\n[OK] Manual structure: {len(topics)} topics")
        return topics
    
    def scrape_component4_details(self, manual_topics: List[Dict]) -> List[Dict]:
        """Scrape Component 4 table content."""
        print("\n" + "="*80)
        print("STEP 2: Scraping Component 4 Content")
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
        
        # Extract text
        pdf_text = self._extract_pdf_text(pdf_content)
        if not pdf_text:
            return manual_topics
        
        # Find Component 4 general content section
        print("\n[INFO] Extracting general Deconstructing texts content...")
        general_content = self._extract_component4_general(pdf_text)
        
        all_topics = manual_topics.copy()
        
        if general_content:
            print(f"[OK] Found {len(general_content)} general items for Component4")
            all_topics.extend(general_content)
        
        print(f"\n[OK] Total topics: {len(all_topics)}")
        return all_topics
    
    def _extract_pdf_text(self, pdf_content: bytes) -> Optional[str]:
        """Extract PDF text."""
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
    
    def _extract_component4_general(self, pdf_text: str) -> List[Dict]:
        """Extract general Deconstructing texts content (applies to all texts)."""
        
        # Find the section
        pattern = r'Deconstructing texts for performance\s+Learners should:'
        match = re.search(pattern, pdf_text, re.IGNORECASE)
        
        if not match:
            print("[WARN] Could not find Deconstructing texts section")
            return []
        
        start = match.start()
        # Find end
        end_patterns = [r'\nVersion \d+\.\d+', r'\n3 Assessment', r'\n2d\.']
        end_pos = len(pdf_text)
        for ep in end_patterns:
            end_match = re.search(ep, pdf_text[start:start+5000])
            if end_match:
                end_pos = start + end_match.start()
                break
        
        section_text = pdf_text[start:end_pos]
        print(f"[DEBUG] Found section: {len(section_text)} chars")
        
        # Use AI to extract the 3-column table
        prompt = f"""Extract content from this OCR Drama and Theatre "Deconstructing texts" section.

This section has a 3-column table:
- Column 1: "Learners should:" (what students do)
- Column 2: "Learners should know and understand:" (knowledge)
- Column 3: "Learners should be able to:" (skills)

Each column has bullet points.

YOUR TASK:
Extract as a flat numbered list, combining all three columns' content:

OUTPUT FORMAT:
1. analyse and interpret their chosen performance text in depth from the perspective of a director
2. the production process and the role of a director
3. directorial methods and techniques in order to establish a vision and make creative and artistic choices
4. demonstrate a clear understanding of the role of the director
5. show how methods and techniques can support interpretations of the creative possibilities for staging the performance text
6. the impact vision has when staging the performance text
7. the performance text narrative and its characters from practical exploration of the text
(continue for ALL bullet points from all 3 columns)

CRITICAL RULES:
- Extract ALL bullet points from all 3 columns
- Output as a simple numbered list (1, 2, 3...)
- Start numbering from 1
- Keep exact wording from PDF
- These will all be Level 2 items under Component 4

SECTION TEXT:
{section_text[:10000]}"""
        
        try:
            if AI_PROVIDER == "openai":
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=8000,
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
            ai_file = self.debug_dir / f"Component4-general-ai-output.txt"
            ai_file.write_text(ai_output, encoding='utf-8')
            
            # Parse simple list
            topics = []
            for line in ai_output.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                match = re.match(r'^(\d+)[\.\)]\s+(.+)$', line)
                if not match:
                    continue
                
                num = match.group(1)
                title = match.group(2).strip()
                
                if len(title) < 5:
                    continue
                
                topics.append({
                    'code': f"Component4_General_{num}",
                    'title': title,
                    'level': 1,  # Under Component 4
                    'parent': 'Component4'
                })
            
            return topics
            
        except Exception as e:
            print(f"[ERROR] AI extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def upload_to_supabase(self, topics: List[Dict]) -> bool:
        """Upload topics."""
        print("\n" + "="*80)
        print("STEP 3: Uploading to Supabase")
        print("="*80)
        
        # Remove 'texts' and 'children' keys
        for topic in topics:
            topic.pop('texts', None)
            topic.pop('children', None)
        
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
        print("\n" + "🎭 "*40)
        print(f"OCR DRAMA & THEATRE SCRAPER: {self.subject['name']} ({self.subject['code']})")
        print("🎭 "*40)
        
        # Build manual structure
        manual_topics = self.build_manual_structure()
        
        # Scrape Component 4 details
        all_topics = self.scrape_component4_details(manual_topics)
        
        if not all_topics:
            print("[ERROR] No topics found")
            return False
        
        # Upload
        success = self.upload_to_supabase(all_topics)
        
        if success:
            print("\n[SUCCESS] ✅ Drama and Theatre scraping complete!")
            print(f"Total topics: {len(all_topics)}")
        else:
            print("\n[FAILED] ❌ Upload failed")
        
        return success


def main():
    scraper = DramaTheatreScraper()
    success = scraper.scrape()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

