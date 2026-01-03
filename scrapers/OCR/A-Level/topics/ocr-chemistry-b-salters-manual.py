"""
OCR A-Level Chemistry B (Salters) Manual Structure Scraper
===========================================================

APPROACH:
1. Manually define Level 0 (Components) and Level 1 (Storylines)
2. Scrape PDF to extract Level 2 (Chemical ideas bullet points)

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-chemistry-b-salters-manual.py
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
anthropic_key = os.getenv('ANTHROPIC_API_KEY')
openai_key = os.getenv('OPENAI_API_KEY')
gemini_key = os.getenv('GEMINI2.5_API_KEY') or os.getenv('GEMINI_API_KEY')

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found in .env!")
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
    'name': 'Chemistry B (Salters)',
    'code': 'H433',
    'qualification': 'A-Level',
    'exam_board': 'OCR',
    'pdf_url': 'https://www.ocr.org.uk/Images/171723-specification-accredited-a-level-gce-chemistry-b-salters-h433.pdf'
}

# MANUAL STRUCTURE: Level 0 and Level 1
MANUAL_STRUCTURE = [
    {
        'code': 'Component01',
        'title': 'Fundamentals of chemistry (01)',
        'level': 0,
        'parent': None,
        'children': [
            {'code': 'Storyline01', 'title': 'Elements of life', 'level': 1, 'parent': 'Component01'},
            {'code': 'Storyline02', 'title': 'Developing fuels', 'level': 1, 'parent': 'Component01'},
            {'code': 'Storyline03', 'title': 'Elements from the sea', 'level': 1, 'parent': 'Component01'},
            {'code': 'Storyline04', 'title': 'The ozone story', 'level': 1, 'parent': 'Component01'},
            {'code': 'Storyline05', 'title': "What's in a medicine?", 'level': 1, 'parent': 'Component01'},
            {'code': 'Storyline06', 'title': 'The chemical industry', 'level': 1, 'parent': 'Component01'},
            {'code': 'Storyline07', 'title': 'Polymers and life', 'level': 1, 'parent': 'Component01'},
            {'code': 'Storyline08', 'title': 'Oceans', 'level': 1, 'parent': 'Component01'},
            {'code': 'Storyline09', 'title': 'Developing metals', 'level': 1, 'parent': 'Component01'},
            {'code': 'Storyline10', 'title': 'Colour by design', 'level': 1, 'parent': 'Component01'},
        ]
    },
    {
        'code': 'Component02',
        'title': 'Scientific literacy in chemistry (02)',
        'level': 0,
        'parent': None,
        'children': []
    },
    {
        'code': 'Component03',
        'title': 'Practical skills in chemistry (03)',
        'level': 0,
        'parent': None,
        'children': []
    }
]


# ================================================================
# SCRAPER CLASS
# ================================================================

class ChemistryBSaltersScraper:
    """Manual structure + PDF detail scraper for Chemistry B (Salters)."""
    
    def __init__(self):
        self.subject = SUBJECT_INFO
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
    
    def build_manual_structure(self) -> List[Dict]:
        """Build the manual Level 0 and Level 1 structure."""
        print("\n" + "="*80)
        print("STEP 1: Building Manual Structure (Levels 0-1)")
        print("="*80)
        
        topics = []
        
        for component in MANUAL_STRUCTURE:
            # Add Level 0 component
            topics.append({
                'code': component['code'],
                'title': component['title'],
                'level': component['level'],
                'parent': component['parent']
            })
            print(f"[L0] {component['code']}: {component['title']}")
            
            # Add Level 1 children
            for child in component.get('children', []):
                topics.append({
                    'code': child['code'],
                    'title': child['title'],
                    'level': child['level'],
                    'parent': child['parent']
                })
                print(f"  [L1] {child['code']}: {child['title']}")
        
        print(f"\n[OK] Manual structure: {len(topics)} topics")
        return topics
    
    def scrape_pdf_details(self, manual_topics: List[Dict]) -> List[Dict]:
        """Download PDF and extract Level 2+ details for each storyline."""
        print("\n" + "="*80)
        print("STEP 2: Scraping PDF for Chemical Ideas (Level 2+)")
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
            print("[ERROR] Could not extract PDF text")
            return manual_topics
        
        # Process each Level 1 storyline
        all_topics = manual_topics.copy()
        storylines = [t for t in manual_topics if t['level'] == 1 and 'Storyline' in t['code']]
        
        for storyline in storylines:
            print(f"\n[INFO] Processing: {storyline['title']}")
            
            # Extract chemical ideas with AI
            details = self._extract_chemical_ideas(
                storyline_name=storyline['title'],
                pdf_text=pdf_text,
                parent_code=storyline['code'],
                base_level=2
            )
            
            if details:
                print(f"[OK] Found {len(details)} chemical ideas for {storyline['code']}")
                all_topics.extend(details)
            else:
                print(f"[WARN] No chemical ideas found for {storyline['code']}")
            
            time.sleep(1)  # Be nice to API
        
        print(f"\n[OK] Total topics: {len(all_topics)}")
        return all_topics
    
    def _extract_pdf_text(self, pdf_content: bytes) -> Optional[str]:
        """Extract text from PDF."""
        try:
            import pdfplumber
            from io import BytesIO
            
            print("[INFO] Extracting PDF text...")
            pdf_file = BytesIO(pdf_content)
            text = ""
            
            with pdfplumber.open(pdf_file) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    if i % 20 == 0 and i > 0:
                        print(f"[INFO] Processed {i+1}/{len(pdf.pages)} pages...")
            
            print(f"[OK] Extracted {len(text)} characters from {len(pdf.pages)} pages")
            
            # Save debug copy
            debug_file = self.debug_dir / f"{self.subject['code']}-spec.txt"
            debug_file.write_text(text, encoding='utf-8')
            
            return text
            
        except ImportError:
            print("[ERROR] pdfplumber not installed")
            return None
        except Exception as e:
            print(f"[ERROR] PDF extraction failed: {e}")
            return None
    
    def _find_storyline_section(self, storyline_name: str, pdf_text: str) -> Optional[str]:
        """Find and extract the section for a specific storyline."""
        
        # Search for the storyline name followed by "The chemical ideas in this module are:"
        # The PDF format is: Storyline heading, then "The chemical ideas in this module are:", then bullet list
        
        # Try to find the storyline section
        pattern = rf'{re.escape(storyline_name)}.*?The chemical ideas in this module are:'
        matches = list(re.finditer(pattern, pdf_text, re.IGNORECASE | re.DOTALL))
        
        if not matches:
            print(f"[WARN] Could not find '{storyline_name}' section")
            return None
        
        print(f"[DEBUG] Found {len(matches)} occurrences")
        
        # Take the longest match (real content, not TOC)
        best_match = None
        best_length = 0
        
        for match in matches:
            start_pos = match.start()
            
            # Find end: next storyline or section marker
            end_patterns = [
                r'\nLearning outcomes',  # Next section
                r'\nActivities',
                r'\nStorylines',
                r'Version \d+\.\d+',
                r'\n[A-Z][a-z]+ [a-z]+ [a-z]+ \([A-Z]+\)'  # Next storyline title
            ]
            
            end_pos = len(pdf_text)
            for ep in end_patterns:
                end_match = re.search(ep, pdf_text[start_pos + 100:start_pos + 5000], re.IGNORECASE)
                if end_match:
                    end_pos = start_pos + 100 + end_match.start()
                    break
            
            section_length = end_pos - start_pos
            if section_length > best_length:
                best_length = section_length
                best_match = match
                section = pdf_text[start_pos:end_pos]
        
        if best_match and best_length > 100:
            section = pdf_text[best_match.start():best_match.start() + best_length]
            print(f"[DEBUG] Extracted section: {len(section)} characters")
            return section
        
        return None
    
    def _extract_chemical_ideas(self, storyline_name: str, pdf_text: str, parent_code: str, base_level: int = 2) -> List[Dict]:
        """Extract chemical ideas bullet points for a storyline."""
        
        # Find the storyline section
        section_text = self._find_storyline_section(storyline_name, pdf_text)
        
        if not section_text:
            return []
        
        # Save section for debugging
        safe_filename = re.sub(r'[^\w\-]', '_', parent_code)
        section_file = self.debug_dir / f"{safe_filename}-section.txt"
        section_file.write_text(section_text[:5000], encoding='utf-8')
        
        # Use AI to extract the bullet points
        prompt = f"""Extract the chemical ideas from this OCR A-Level Chemistry B (Salters) storyline section.

STORYLINE: "{storyline_name}"

The section has this format:
- Title: "{storyline_name}"
- Heading: "The chemical ideas in this module are:"
- Bullet list of chemical topics

EXAMPLE from the PDF:
"The chemical ideas in this module are:
• atomic structure, atomic spectra and electron configurations
• fusion reactions
• mass spectrometry and isotopes
• the periodic table and Group 2 chemistry
• bonding and the shapes of molecules"

YOUR TASK:
Extract ONLY the bullet points under "The chemical ideas in this module are:"
Output as a simple numbered list (1, 2, 3, etc.)

OUTPUT FORMAT:
1. atomic structure, atomic spectra and electron configurations
2. fusion reactions
3. mass spectrometry and isotopes
4. the periodic table and Group 2 chemistry
5. bonding and the shapes of molecules

CRITICAL RULES:
- Extract ONLY the bullet points (the chemical ideas)
- Start numbering from 1
- One idea per line
- Keep the exact wording from the PDF
- Include ALL bullet points in the list

SECTION TEXT:
{section_text[:10000]}"""
        
        try:
            # Call AI
            if AI_PROVIDER == "openai":
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4096,
                    temperature=0
                )
                ai_output = response.choices[0].message.content
                
            elif AI_PROVIDER == "anthropic":
                response = claude.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}]
                )
                ai_output = response.content[0].text
                
            elif AI_PROVIDER == "gemini":
                response = gemini_model.generate_content(prompt)
                ai_output = response.text
            
            # Save AI output
            ai_file = self.debug_dir / f"{safe_filename}-ai-output.txt"
            ai_file.write_text(ai_output, encoding='utf-8')
            
            # Parse the output into topics
            details = self._parse_simple_list(ai_output, parent_code, base_level)
            
            return details
            
        except Exception as e:
            print(f"[ERROR] AI extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_simple_list(self, text: str, parent_code: str, base_level: int) -> List[Dict]:
        """Parse simple numbered list into topics."""
        topics = []
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Match numbered items: 1. Title, 2. Title, etc.
            match = re.match(r'^(\d+)[\.\)]\s+(.+)$', line)
            if not match:
                continue
            
            number = match.group(1)
            title = match.group(2).strip()
            
            if len(title) < 3:
                continue
            
            code = f"{parent_code}_{number}"
            
            topics.append({
                'code': code,
                'title': title,
                'level': base_level,
                'parent': parent_code
            })
        
        return topics
    
    def upload_to_supabase(self, topics: List[Dict]) -> bool:
        """Upload all topics to Supabase."""
        print("\n" + "="*80)
        print("STEP 3: Uploading to Supabase")
        print("="*80)
        
        # Deduplicate
        seen_codes = {}
        for topic in topics:
            code = topic['code']
            if code not in seen_codes:
                seen_codes[code] = topic
        
        topics = list(seen_codes.values())
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
            print(f"[OK] Subject: {subject_result.data[0]['subject_name']} (ID: {subject_id})")
            
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
            
            inserted_result = supabase.table('staging_aqa_topics').insert(to_insert).execute()
            print(f"[OK] Uploaded {len(inserted_result.data)} topics")
            
            # Build code -> id mapping
            code_to_id = {t['topic_code']: t['id'] for t in inserted_result.data}
            
            # Link hierarchy
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
            
            print(f"[OK] Linked {linked} parent-child relationships")
            
            # Show stats
            levels = {}
            for t in topics:
                levels[t['level']] = levels.get(t['level'], 0) + 1
            
            print("\n[INFO] Hierarchy distribution:")
            for level in sorted(levels.keys()):
                print(f"  Level {level}: {levels[level]} topics")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def scrape(self) -> bool:
        """Main scraping workflow."""
        print("\n" + "🧪 "*40)
        print(f"OCR CHEMISTRY B (SALTERS) SCRAPER: {self.subject['name']} ({self.subject['code']})")
        print("🧪 "*40)
        
        # Step 1: Build manual structure
        manual_topics = self.build_manual_structure()
        
        # Step 2: Scrape PDF for chemical ideas
        all_topics = self.scrape_pdf_details(manual_topics)
        
        if not all_topics:
            print("[ERROR] No topics found")
            return False
        
        # Step 3: Upload
        success = self.upload_to_supabase(all_topics)
        
        if success:
            print("\n[SUCCESS] ✅ Chemistry B (Salters) scraping complete!")
            print(f"Total topics: {len(all_topics)}")
        else:
            print("\n[FAILED] ❌ Upload failed")
        
        return success


# ================================================================
# MAIN
# ================================================================

def main():
    scraper = ChemistryBSaltersScraper()
    success = scraper.scrape()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

