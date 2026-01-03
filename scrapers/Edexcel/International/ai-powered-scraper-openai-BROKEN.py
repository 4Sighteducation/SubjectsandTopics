"""
AI-Powered Scraper using OpenAI GPT-4
=====================================

More reliable than Claude for large documents.

Requirements:
    pip install openai

Setup:
    Add to .env: OPENAI_API_KEY=sk-xxxxx

Usage:
    python ai-powered-scraper-openai.py --subject IG-Biology
"""

import os
import sys
import re
import json
import argparse
import requests
from pathlib import Path
from io import BytesIO
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

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found!")
    sys.exit(1)

if not openai_key:
    print("[ERROR] OPENAI_API_KEY not found in .env!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

try:
    from openai import OpenAI
except ImportError:
    print("[ERROR] openai library not installed!")
    print("Run: pip install openai")
    sys.exit(1)

client = OpenAI(api_key=openai_key)

try:
    import pdfplumber
except ImportError:
    print("[ERROR] pdfplumber not installed!")
    print("Run: pip install pdfplumber")
    sys.exit(1)


EXTRACTION_PROMPT = """TASK: Extract curriculum content structure from this specification PDF using a strategic two-phase approach.

PHASE 1 - READ STRUCTURE (Do this first!):
1. Find the "Qualification at a glance" or "Paper overview" section (usually pages 7-15)
2. Identify how many PAPERS exist (Paper 1, Paper 2, etc.) - look for "externally assessed"
3. IGNORE any internally assessed components
4. For EACH paper, note which TOPICS it covers - they will be NUMBERED (1, 2, 3, 4, 5, 6, 7, 8...)
   - **CRITICAL:** Papers typically list 5-8 numbered topics like:
     * 1 Forces and motion
     * 2 Electricity
     * 3 Waves
     * 4 Energy resources...
     * (and so on)
   - YOU MUST include ALL of these numbered topics in your output
   - If Paper 1 lists "1 Forces, 2 Electricity, 3 Waves, 4 Energy, 5 Solids, 6 Magnetism, 7 Radioactivity, 8 Astrophysics"
   - Then create 1.1 through 1.8 in your hierarchy
5. **CRITICAL FOR HISTORY/RE:** Look for OPTIONAL ROUTES/PERIODS/THEMES
   - ALL OPTIONS must be included as separate branches
6. This structure will be your hierarchy framework - COMPLETE IT FOR ALL TOPICS!

PHASE 2 - EXTRACT ACTUAL CONTENT TEXT:
Now read the detailed content sections and extract the FULL TEXT of each specification, NOT just "Learning objective X".

CRITICAL - CONTENT EXTRACTION:
- When you see numbered specifications like "1.1 use the following SI units..." or "2.7 identify the chemical elements..."
- Extract the COMPLETE TEXT of that specification as the title
- DO NOT write generic labels like "Learning objective 1.1" or "Specification 2.7"
- WRONG: "1.1.1.1 Learning objective 1.1"
- CORRECT: "1.1.1.1 use the following SI units: kilogram (kg), metre (m), second (s), metre/second (m/s)..."

STRUCTURE TO CREATE:
1. Paper 1 Name (from "Qualification at a glance")
   1.1 Topic 1 Name (e.g., "Forces and motion")
       1.1.1 Units (remove "Sub-section (a)" label, just use the actual name like "Units")
           1.1.1.1 use the following SI units: kilogram (kg), metre (m), second (s)...
           1.1.1.2 recall and use the relationship between average speed, distance and time
       1.1.2 Movement and position (just the name, no "Sub-section" prefix)
           1.1.2.1 understand the differences between scalar and vector quantities
           1.1.2.2 understand that force is a vector quantity
   1.2 Topic 2 Name
       1.2.1 Actual sub-section name (not "Sub-section")
           1.2.1.1 ACTUAL CONTENT TEXT HERE

2. Paper 2 Name (if exists)
   2.1 Topic Name
       2.1.1 Sub-topic name
           2.1.1.1 FULL SPECIFICATION TEXT with all details

CRITICAL RULES FOR OPTIONS:
- HISTORY: Include ALL period options (e.g., Medieval, Early Modern, Modern, etc.)
  * Each period becomes a separate top-level topic: "1.1 Medieval Period (1066-1509)", "1.2 Early Modern (1509-1760)"
  * Extract all depth studies, case studies, key events for each period
- RELIGIOUS STUDIES: Include ALL religions as separate options
  * "1.1 Buddhism", "1.2 Christianity", "1.3 Hinduism", "1.4 Islam", "1.5 Judaism", "1.6 Sikhism"
  * Extract all beliefs, practices, sources of authority for each religion
- Even if students "choose ONE", include ALL in the database

HANDLING LARGE PDFs:
- History/RE specs can be 100+ pages with 10+ options
- Extract EVERYTHING - don't skip options due to length
- Be thorough with each option's sub-topics

**CRITICAL FOR LANGUAGE SUBJECTS** (French, Spanish, German, Arabic, Chinese, Tamil, etc.):

STEP 1: FIND THE VOCABULARY APPENDIX
- Look at the LAST 20-30 pages of the PDF
- Find "Appendix: Vocabulary list" or "Vocabulary" section
- This contains vocabulary organized by themes

STEP 2: MAP VOCABULARY TO THEMES  
- DO NOT create separate "Appendix" sections
- INSTEAD: For each theme you extracted, ADD vocabulary as child topics
- Match vocabulary themes to content themes (Home→Home vocab, School→School vocab)
- **EVERY THEME/SUB-TOPIC MUST HAVE VOCABULARY ENTRIES**

STEP 3: FORMAT CORRECTLY
Example for French:
1. Paper 1
   1.1 Theme: Identity and culture  
       1.1.1 Family and relationships
           1.1.1.1 Vocabulary: la famille (family), le père (father), la mère (mother), le frère (brother), la sœur (sister)
       1.1.2 Technology
           1.1.2.1 Vocabulary: l'ordinateur (computer), le portable (mobile), envoyer (to send), télécharger (download)
   1.2 Theme: Local area
       1.2.1 My neighbourhood
           1.2.1.1 Vocabulary: la maison (house), la ville (town), le magasin (shop), la rue (street)
       1.2.2 Transport
           1.2.2.1 Vocabulary: le train (train), la voiture (car), l'avion (plane)

WITHOUT VOCABULARY MAPPING, THE OUTPUT IS INCOMPLETE.
If you output themes without vocabulary, you failed the task.

- Include grammar (verb tenses, conjugations) where contextually relevant
- For Tamil/Arabic/Chinese: preserve native script characters
- SCIENCES: Extract practical investigations as sub-topics under relevant content
- HISTORY: Extract key events, figures, causes, consequences as hierarchical sub-topics
- GEOGRAPHY: Extract case studies, regions, phenomena as sub-topics
- RELIGIOUS STUDIES: For each religion, extract beliefs, practices, texts, festivals

OUTPUT FORMAT:
1. Paper Name
1.1 Topic Name
1.1.1 Actual sub-topic name (don't add generic "Sub-section" labels)
1.1.1.1 FULL CONTENT TEXT
1.1.1.2 FULL CONTENT TEXT
1.1.1.1.1 Child detail if content has lists or multiple elements

CRITICAL REMINDERS:
- Extract ACTUAL SPECIFICATION CONTENT, not labels
- Each numbered item (1.1, 2.7, 3.4) has REAL TEXT - extract that text
- Look in tables under "Students should:" sections
- Don't add generic prefixes like "Sub-section (a)" - use the actual topic name
- Create deeper levels (4, 5) when content contains multiple items or formulas
- **FOR ALL LANGUAGE SUBJECTS:** You MUST find and distribute vocabulary from appendices to themes

FINAL CHECK BEFORE OUTPUT:
- If this is a LANGUAGE subject (French, Spanish, German, Arabic, Chinese, Tamil, etc.), did you:
  ✓ Find the vocabulary appendix?
  ✓ Distribute vocabulary words to relevant themes?
  ✓ Add grammar examples contextually?
  ✓ If NO - go back and add vocabulary now!

ONLY output the numbered hierarchy. No explanations or commentary."""


class OpenAIScraper:
    """OpenAI-powered scraper."""
    
    def __init__(self, subject_info: Dict):
        self.subject = subject_info
        self.topics = []
        
    def download_pdf(self) -> Optional[bytes]:
        """Download PDF."""
        print(f"\n[INFO] Downloading PDF...")
        
        try:
            response = requests.get(self.subject['pdf_url'], timeout=60)
            response.raise_for_status()
            print(f"[OK] Downloaded {len(response.content)/1024/1024:.1f} MB")
            return response.content
        except Exception as e:
            print(f"[ERROR] Download failed: {str(e)}")
            return None
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> Optional[str]:
        """Extract text from PDF."""
        print("\n[INFO] Extracting PDF text...")
        
        try:
            pdf_file = BytesIO(pdf_content)
            text = ""
            
            with pdfplumber.open(pdf_file) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    if i % 10 == 0:
                        print(f"[INFO] Page {i+1}/{len(pdf.pages)}...", end='\r')
            
            print(f"\n[OK] Extracted {len(text)} chars")
            return text
            
        except Exception as e:
            print(f"[ERROR] Extraction failed: {str(e)}")
            return None
    
    def extract_with_ai(self, pdf_text: str) -> Optional[str]:
        """Send to OpenAI GPT-4 for extraction."""
        print("\n[INFO] Sending to GPT-4 (this may take 30-60 seconds)...")
        
        # Handle large PDFs (History/RE can be 200k+ chars)
        max_chars = 200000  # ~50k tokens - increased for History/RE with many options
        if len(pdf_text) > max_chars:
            print(f"[WARNING] Large PDF ({len(pdf_text)} chars), truncating to {max_chars}")
            print("[WARNING] Some content may be lost - review output")
            pdf_text = pdf_text[:max_chars]
        
        # Retry logic for connection issues
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",  # Latest GPT-4
                    messages=[
                        {
                            "role": "user",
                            "content": f"{EXTRACTION_PROMPT}\n\nPDF Text:\n\n{pdf_text}"
                        }
                    ],
                    max_tokens=16384,  # Maximum for gpt-4o - no cost concerns!
                    temperature=0,  # Deterministic output
                    timeout=180  # 3 minute timeout for large extractions
                )
                
                hierarchy_text = response.choices[0].message.content
                
                print(f"[OK] GPT-4 extracted {len(hierarchy_text)} chars")
                print(f"[OK] Tokens: {response.usage.prompt_tokens} in, {response.usage.completion_tokens} out")
                
                # Check if we hit the token limit
                if response.usage.completion_tokens >= 16000:
                    print(f"[WARNING] Hit token limit! Output may be incomplete.")
                
                break  # Success, exit retry loop
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"[WARNING] Attempt {attempt + 1} failed: {str(e)[:100]}")
                    print(f"[INFO] Retrying in 5 seconds...")
                    import time
                    time.sleep(5)
                    continue
                else:
                    # Final attempt failed
                    print(f"[ERROR] All {max_retries} attempts failed: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return None
        
        # Save output (after successful extraction)
        debug_file = Path(__file__).parent / "adobe-ai-output" / f"{self.subject['code']}-gpt4-output.txt"
        debug_file.parent.mkdir(exist_ok=True)
        debug_file.write_text(hierarchy_text, encoding='utf-8')
        print(f"[OK] Saved to: {debug_file.name}")
        
        return hierarchy_text
    
    def parse_hierarchy(self, text: str) -> List[Dict]:
        """Parse AI output into topics."""
        print("\n[INFO] Parsing hierarchy...")
        
        topics = []
        lines = text.split('\n')
        parent_stack = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Match: 1., 1.1, 1.1.1, etc.
            match = re.match(r'^([\d.]+)\s+(.+)$', line)
            if not match:
                continue
            
            number = match.group(1).rstrip('.')
            title = match.group(2).strip()
            
            level = number.count('.')
            code = number.replace('.', '_')
            
            parent_code = parent_stack.get(level - 1) if level > 0 else None
            
            topics.append({
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
        
        print(f"[OK] Parsed {len(topics)} topics")
        
        by_level = {}
        for t in topics:
            by_level[t['level']] = by_level.get(t['level'], 0) + 1
        
        print("[OK] Breakdown:")
        for level in sorted(by_level.keys()):
            print(f"  Level {level}: {by_level[level]}")
        
        return topics
    
    def upload_to_supabase(self, topics: List[Dict]) -> bool:
        """Upload to Supabase."""
        print("\n[INFO] Uploading...")
        
        try:
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': f"{self.subject['name']} ({self.subject['qualification']})",
                'subject_code': self.subject['code'],
                'qualification_type': self.subject['qualification'],
                'specification_url': self.subject['pdf_url'],
                'exam_board': self.subject['exam_board']
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            subject_id = subject_result.data[0]['id']
            print(f"[OK] Subject ID: {subject_id}")
            
            # Clear old
            supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
            print("[OK] Cleared old topics")
            
            # Deduplicate
            unique = {}
            for t in topics:
                if t['code'] not in unique:
                    unique[t['code']] = t
            topics = list(unique.values())
            print(f"[OK] {len(topics)} unique topics")
            
            # Insert
            to_insert = [{
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': t['title'],
                'topic_level': t['level'],
                'exam_board': self.subject['exam_board']
            } for t in topics]
            
            inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
            print(f"[OK] Uploaded {len(inserted.data)} topics")
            
            # Link parents
            code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
            linked = 0
            
            for topic in topics:
                if topic['parent'] and topic['code'] in code_to_id and topic['parent'] in code_to_id:
                    try:
                        supabase.table('staging_aqa_topics').update({
                            'parent_topic_id': code_to_id[topic['parent']]
                        }).eq('id', code_to_id[topic['code']]).execute()
                        linked += 1
                    except:
                        pass
            
            print(f"[OK] Linked {linked} parents")
            return True
            
        except Exception as e:
            print(f"[ERROR] Upload failed: {str(e)}")
            return False
    
    def scrape(self) -> bool:
        """Main workflow."""
        print("\n" + "="*60)
        print(f"GPT-4 SCRAPING: {self.subject['name']}")
        print("="*60)
        
        pdf_content = self.download_pdf()
        if not pdf_content:
            return False
        
        pdf_text = self.extract_text_from_pdf(pdf_content)
        if not pdf_text:
            return False
        
        hierarchy_text = self.extract_with_ai(pdf_text)
        if not hierarchy_text:
            return False
        
        self.topics = self.parse_hierarchy(hierarchy_text)
        if not self.topics:
            return False
        
        success = self.upload_to_supabase(self.topics)
        
        print(f"\n{'[SUCCESS]' if success else '[FAILED]'}")
        return success


def load_subjects(json_file: Path) -> List[Dict]:
    """Load subjects."""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subject', help='Subject code (e.g., IG-Biology)')
    parser.add_argument('--all-igcse', action='store_true')
    parser.add_argument('--all-ial', action='store_true')
    parser.add_argument('--all', action='store_true')
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    subjects_to_scrape = []
    
    if args.subject:
        if args.subject.startswith('IG-'):
            file = script_dir / "International-GCSE" / "international-gcse-subjects.json"
        else:
            file = script_dir / "International-A-Level" / "international-a-level-subjects.json"
        
        subjects = load_subjects(file)
        subject = next((s for s in subjects if s['code'] == args.subject), None)
        if subject:
            subjects_to_scrape = [subject]
    
    elif args.all_igcse:
        file = script_dir / "International-GCSE" / "international-gcse-subjects.json"
        subjects_to_scrape = load_subjects(file)
    
    elif args.all_ial:
        file = script_dir / "International-A-Level" / "international-a-level-subjects.json"
        subjects_to_scrape = load_subjects(file)
    
    elif args.all:
        ig = load_subjects(script_dir / "International-GCSE" / "international-gcse-subjects.json")
        ial = load_subjects(script_dir / "International-A-Level" / "international-a-level-subjects.json")
        subjects_to_scrape = ig + ial
    
    else:
        parser.print_help()
        sys.exit(1)
    
    print(f"\n[INFO] Scraping {len(subjects_to_scrape)} subjects with GPT-4")
    
    results = {'success': 0, 'failed': 0}
    
    for subject in subjects_to_scrape:
        scraper = OpenAIScraper(subject)
        if scraper.scrape():
            results['success'] += 1
        else:
            results['failed'] += 1
        print("\n" + "-"*60)
    
    print(f"\n{'='*60}")
    print(f"COMPLETE: {results['success']} success, {results['failed']} failed")
    print("="*60)


if __name__ == '__main__':
    main()

