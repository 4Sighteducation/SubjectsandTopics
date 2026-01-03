"""
International GCSE Language Scraper - Template Based
===================================================

ALL International GCSE languages share the same structure:
- Paper 1: Listening
- Paper 2: Reading and Writing
- (Paper 3: Speaking for some)

With 5 identical themes:
A. Home and abroad
B. Education and employment
C. Personal life and relationships
D. The world around us
E. Social activities, fitness and health

This scraper:
1. Uses HARDCODED structure (no AI needed for structure)
2. Uses AI ONLY to extract vocabulary from appendices
3. Maps vocabulary to themes

Much faster and more reliable!

Usage:
    python language-scraper-template.py --subject IG-French
    python language-scraper-template.py --subject IG-Spanish
    python language-scraper-template.py --subject IG-Tamil
"""

import os
import sys
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

if not all([supabase_url, supabase_key, openai_key]):
    print("[ERROR] Missing credentials!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

try:
    from openai import OpenAI
    import pdfplumber
except ImportError:
    print("[ERROR] Run: pip install openai pdfplumber")
    sys.exit(1)

client = OpenAI(api_key=openai_key)


# HARDCODED STRUCTURE - Same for all languages
LANGUAGE_STRUCTURE = {
    "Paper 1: Listening": {
        "Home and abroad": [
            "Life in the town and rural life",
            "Holidays, tourist information and directions",
            "Services (e.g. bank, post office)",
            "Customs",
            "Everyday life, traditions and communities"
        ],
        "Education and employment": [
            "School life and routine",
            "School rules and pressures",
            "School trips, events and exchanges",
            "Work, careers and volunteering",
            "Future plans"
        ],
        "Personal life and relationships": [
            "House and home",
            "Daily routines and helping at home",
            "Role models",
            "Relationships with family and friends",
            "Childhood"
        ],
        "The world around us": [
            "Environmental issues",
            "Weather and climate",
            "Travel and transport",
            "The media",
            "Information and communication technology"
        ],
        "Social activities, fitness and health": [
            "Special occasions",
            "Hobbies, interests, sports and exercise",
            "Shopping and money matters",
            "Accidents, injuries, common ailments and health issues",
            "Food and drink"
        ]
    }
}


VOCAB_EXTRACTION_PROMPT = """Extract vocabulary from this language specification appendix.

The appendix contains vocabulary lists organized by themes. Extract ALL vocabulary words with translations.

For each theme, create a list of vocabulary entries in this format:
Theme: Home and abroad
- Life in town: ville (town), maison (house), habiter (to live), rue (street)...
- Holidays: vacances (holidays), plage (beach), hôtel (hotel), voyager (to travel)...

Theme: Education
- School: école (school), professeur (teacher), étudier (to study), cahier (notebook)...

Theme: Personal life
- Family: famille (family), père (father), mère (mother), frère (brother)...

Output as JSON:
{
  "Home and abroad": {
    "Life in town": ["ville (town)", "maison (house)", "habiter (to live)"],
    "Holidays": ["vacances (holidays)", "plage (beach)"]
  },
  "Education": {
    "School": ["école (school)", "professeur (teacher)"]
  }
}

Extract ALL vocabulary, preserving native scripts (Tamil: வீடு, Arabic: بيت, Chinese: 家)."""


class LanguageScraper:
    """Template-based language scraper."""
    
    def __init__(self, subject_info: Dict):
        self.subject = subject_info
        self.topics = []
        
    def download_pdf(self) -> Optional[bytes]:
        print(f"\n[INFO] Downloading PDF...")
        try:
            response = requests.get(self.subject['pdf_url'], timeout=60)
            response.raise_for_status()
            print(f"[OK] Downloaded {len(response.content)/1024/1024:.1f} MB")
            return response.content
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return None
    
    def extract_vocab_section(self, pdf_content: bytes) -> Optional[str]:
        """Extract just the vocabulary appendix (last 20-30 pages)."""
        print("\n[INFO] Extracting vocabulary appendix...")
        
        try:
            with pdfplumber.open(BytesIO(pdf_content)) as pdf:
                total_pages = len(pdf.pages)
                # Get last 30 pages (where vocab usually is)
                start_page = max(0, total_pages - 30)
                
                vocab_text = ""
                for i in range(start_page, total_pages):
                    page_text = pdf.pages[i].extract_text()
                    if page_text:
                        vocab_text += page_text + "\n"
                
                print(f"[OK] Extracted vocabulary section ({len(vocab_text)} chars from last 30 pages)")
                return vocab_text
                
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return None
    
    def extract_vocab_with_ai(self, vocab_text: str) -> Optional[Dict]:
        """Use AI to extract and organize vocabulary."""
        print("\n[INFO] Extracting vocabulary with GPT-4-mini (this may take 30-60 seconds)...")
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Cheaper for vocab extraction
                messages=[{
                    "role": "user",
                    "content": f"{VOCAB_EXTRACTION_PROMPT}\n\nVocabulary Appendix:\n\n{vocab_text[:50000]}"
                }],
                max_tokens=8000,
                response_format={"type": "json_object"},
                temperature=0,
                timeout=120  # 2 minute timeout
            )
            
            print(f"[OK] GPT-4 responded ({response.usage.completion_tokens} tokens)")
            vocab_json = json.loads(response.choices[0].message.content)
            print(f"[OK] Extracted vocabulary for {len(vocab_json)} themes")
            
            # Save for debugging
            debug_file = Path(__file__).parent / "adobe-ai-output" / f"{self.subject['code']}-vocab.json"
            debug_file.write_text(json.dumps(vocab_json, indent=2, ensure_ascii=False), encoding='utf-8')
            
            return vocab_json
            
        except Exception as e:
            print(f"[ERROR] Vocab extraction failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def build_topics_with_vocab(self, vocab_map: Dict) -> List[Dict]:
        """Build topic hierarchy using template + extracted vocabulary."""
        print("\n[INFO] Building topic hierarchy with vocabulary...")
        
        topics = []
        topic_counter = 0
        
        # Paper 1 (just use structure, vocab will be same for all papers)
        paper_code = f"T{topic_counter}"
        topic_counter += 1
        topics.append({
            'code': paper_code,
            'title': 'Paper 1: Listening',
            'level': 0,
            'parent': None
        })
        
        # Iterate through hardcoded structure
        for theme_idx, (theme_name, subtopics) in enumerate(LANGUAGE_STRUCTURE["Paper 1: Listening"].items(), 1):
            # Theme level
            theme_code = f"T{topic_counter}"
            topic_counter += 1
            topics.append({
                'code': theme_code,
                'title': theme_name,
                'level': 1,
                'parent': paper_code
            })
            
            # Sub-topics
            for subtopic_name in subtopics:
                subtopic_code = f"T{topic_counter}"
                topic_counter += 1
                topics.append({
                    'code': subtopic_code,
                    'title': subtopic_name,
                    'level': 2,
                    'parent': theme_code
                })
                
                # Try to find matching vocabulary
                vocab_entry = self._find_vocab_for_subtopic(vocab_map, theme_name, subtopic_name)
                if vocab_entry:
                    vocab_code = f"T{topic_counter}"
                    topic_counter += 1
                    topics.append({
                        'code': vocab_code,
                        'title': f"Vocabulary: {vocab_entry}",
                        'level': 3,
                        'parent': subtopic_code
                    })
        
        print(f"[OK] Built {len(topics)} topics")
        return topics
    
    def _find_vocab_for_subtopic(self, vocab_map: Dict, theme: str, subtopic: str) -> Optional[str]:
        """Find relevant vocabulary for a subtopic."""
        # Look for matching theme in vocab map
        for key in vocab_map.keys():
            if theme.lower() in key.lower():
                # Found matching theme
                theme_vocab = vocab_map[key]
                if isinstance(theme_vocab, dict):
                    # Look for matching subtopic
                    for subkey, words in theme_vocab.items():
                        if any(word in subtopic.lower() for word in subkey.lower().split()):
                            if isinstance(words, list) and len(words) > 0:
                                return ", ".join(words[:10])  # Limit to 10 words
                    # If no exact match, return first available
                    for words in theme_vocab.values():
                        if isinstance(words, list) and len(words) > 0:
                            return ", ".join(words[:10])
        return None
    
    def upload(self, topics: List[Dict]) -> bool:
        """Upload to Supabase."""
        print("\n[INFO] Uploading...")
        try:
            result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': f"{self.subject['name']} ({self.subject['qualification']})",
                'subject_code': self.subject['code'],
                'qualification_type': self.subject['qualification'],
                'specification_url': self.subject['pdf_url'],
                'exam_board': self.subject['exam_board']
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            subject_id = result.data[0]['id']
            supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
            
            to_insert = [{
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': t['title'],
                'topic_level': t['level'],
                'exam_board': self.subject['exam_board']
            } for t in topics]
            
            inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
            code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
            
            for topic in topics:
                if topic['parent'] and topic['code'] in code_to_id and topic['parent'] in code_to_id:
                    try:
                        supabase.table('staging_aqa_topics').update({
                            'parent_topic_id': code_to_id[topic['parent']]
                        }).eq('id', code_to_id[topic['code']]).execute()
                    except:
                        pass
            
            print(f"[OK] Uploaded {len(topics)} topics")
            return True
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return False
    
    def scrape(self) -> bool:
        print(f"\n{'='*60}")
        print(f"LANGUAGE SCRAPING: {self.subject['name']}")
        print('='*60)
        
        pdf = self.download_pdf()
        if not pdf:
            return False
        
        vocab_text = self.extract_vocab_section(pdf)
        if not vocab_text:
            return False
        
        vocab_map = self.extract_vocab_with_ai(vocab_text)
        if not vocab_map:
            print("[WARNING] No vocabulary extracted, using structure only")
            vocab_map = {}
        
        topics = self.build_topics_with_vocab(vocab_map)
        
        success = self.upload(topics)
        print(f"\n{'[SUCCESS]' if success else '[FAILED]'}")
        return success


def load_subjects(file: Path):
    with open(file, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subject', required=True)
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    file = script_dir / "International-GCSE" / "international-gcse-subjects.json"
    
    subjects = load_subjects(file)
    subject = next((s for s in subjects if s['code'] == args.subject), None)
    
    if not subject:
        print(f"[ERROR] Subject not found")
        sys.exit(1)
    
    # Check if it's a language subject
    language_subjects = ['French', 'Spanish', 'German', 'Tamil', 'Arabic', 'Chinese', 'Bangla', 
                        'Sinhala', 'Swahili', 'Greek']
    
    if not any(lang in subject['name'] for lang in language_subjects):
        print(f"[ERROR] {subject['name']} is not a language subject")
        print("Use ai-powered-scraper-openai-WORKING.py for non-language subjects")
        sys.exit(1)
    
    scraper = LanguageScraper(subject)
    sys.exit(0 if scraper.scrape() else 1)


if __name__ == '__main__':
    main()

