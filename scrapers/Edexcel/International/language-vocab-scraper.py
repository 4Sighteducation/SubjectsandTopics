"""
International GCSE Language Vocabulary Scraper
==============================================

For languages with standard structure: French, Spanish, German, Tamil, Bangla, 
Sinhala, Swahili (NOT Arabic First Language, Greek First Language, or ESL)

Uses HARDCODED theme structure + AI vocabulary extraction.
Ensures native scripts (Tamil, Bangla, etc.) are preserved in database.

Usage:
    python language-vocab-scraper.py --subject IG-French
    python language-vocab-scraper.py --subject IG-Bangla
    python language-vocab-scraper.py --all
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

# Force UTF-8 throughout
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


# STANDARD LANGUAGE STRUCTURE (same for all standard languages)
STANDARD_THEMES = {
    "Theme 1: Home and abroad": [
        "Life in the town and rural life",
        "Holidays, tourist information and directions",
        "Services (e.g. bank, post office)",
        "Customs",
        "Everyday life, traditions and communities"
    ],
    "Theme 2: Education and employment": [
        "School life and routine",
        "School rules and pressures",
        "School trips, events and exchanges",
        "Work, careers and volunteering",
        "Future plans"
    ],
    "Theme 3: Personal life and relationships": [
        "House and home",
        "Daily routines and helping at home",
        "Role models",
        "Relationships with family and friends",
        "Childhood"
    ],
    "Theme 4: The world around us": [
        "Environmental issues",
        "Weather and climate",
        "Travel and transport",
        "The media",
        "Information and communication technology"
    ],
    "Theme 5: Social activities, fitness and health": [
        "Special occasions",
        "Hobbies, interests, sports and exercise",
        "Shopping and money matters",
        "Accidents, injuries, common ailments and health issues",
        "Food and drink"
    ]
}


VOCAB_PROMPT = """Extract ALL vocabulary from this language specification appendix.

The appendix contains vocabulary lists. Extract EVERY word with its translation.

Group by theme matching these categories:
- Home and abroad (town, rural life, holidays, services, customs, traditions)
- Education (school, work, careers, future)
- Personal life (house, family, relationships, childhood)
- World (environment, weather, travel, media, technology)
- Social activities (occasions, hobbies, shopping, health, food)

For EACH sub-topic, extract relevant vocabulary.

Output as JSON with this structure:
{
  "Theme 1: Home and abroad": {
    "Life in the town and rural life": ["word1 (translation)", "word2 (translation)"],
    "Holidays, tourist information and directions": ["word3", "word4"],
    "Services": ["word5", "word6"],
    "Customs": ["word7"],
    "Everyday life, traditions and communities": ["word8"]
  },
  "Theme 2: Education and employment": {
    "School life and routine": ["word9"],
    "School rules and pressures": ["word10"],
    ...
  },
  ...
}

CRITICAL: Preserve ALL native scripts exactly as they appear:
- Tamil: வீடு, குடும்பம், அறை
- Bangla: বাড়ি, পরিবার, ঘর
- Arabic: بيت, عائلة, غرفة
- Chinese: 家, 家庭, 房间

Extract comprehensively - include ALL vocabulary from the appendix."""


class LanguageVocabScraper:
    """Scraper for standard structure languages with vocab extraction."""
    
    def __init__(self, subject_info: Dict):
        self.subject = subject_info
        self.topics = []
        
    def download_pdf(self) -> Optional[bytes]:
        print(f"\n[INFO] Downloading {self.subject['name']} PDF...")
        try:
            response = requests.get(self.subject['pdf_url'], timeout=60)
            response.raise_for_status()
            print(f"[OK] Downloaded {len(response.content)/1024/1024:.1f} MB")
            return response.content
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return None
    
    def extract_vocab_appendix(self, pdf_content: bytes) -> Optional[str]:
        """Extract vocabulary appendix (usually last 20-40 pages)."""
        print("\n[INFO] Extracting vocabulary appendix...")
        
        try:
            with pdfplumber.open(BytesIO(pdf_content)) as pdf:
                total_pages = len(pdf.pages)
                # Get last 40 pages where vocab usually is
                start_page = max(0, total_pages - 40)
                
                vocab_text = ""
                for i in range(start_page, total_pages):
                    page_text = pdf.pages[i].extract_text()
                    if page_text:
                        vocab_text += page_text + "\n"
                
                print(f"[OK] Extracted {len(vocab_text)} chars from pages {start_page+1}-{total_pages}")
                return vocab_text
                
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return None
    
    def extract_vocab_with_ai(self, vocab_text: str) -> Optional[Dict]:
        """Use GPT-4 to extract and organize vocabulary with retries."""
        print(f"\n[INFO] Extracting vocabulary with GPT-4 (may take 60-120s)...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"[INFO] Attempt {attempt + 1}/{max_retries}...")
                
                response = client.chat.completions.create(
                    model="gpt-4o",  # Full GPT-4 for native script handling
                    messages=[{
                        "role": "user",
                        "content": f"{VOCAB_PROMPT}\n\nVocabulary Appendix Text:\n\n{vocab_text[:80000]}"  # Reduced size
                    }],
                    max_tokens=12000,  # Reduced from 16k
                    response_format={"type": "json_object"},
                    temperature=0,
                    timeout=240  # 4 minutes
                )
                
                vocab_json = json.loads(response.choices[0].message.content)
                print(f"[OK] Extracted vocabulary ({response.usage.completion_tokens} tokens)")
                
                # Save with UTF-8
                debug_file = Path(__file__).parent / "adobe-ai-output" / f"{self.subject['code']}-vocab.json"
                debug_file.write_text(json.dumps(vocab_json, indent=2, ensure_ascii=False), encoding='utf-8')
                print(f"[OK] Saved vocab JSON")
                
                return vocab_json
                
            except Exception as e:
                error_msg = str(e)[:100]
                print(f"[WARNING] Attempt {attempt + 1} failed: {error_msg}")
                
                if attempt < max_retries - 1:
                    print(f"[INFO] Retrying in 10 seconds...")
                    import time
                    time.sleep(10)
                else:
                    print(f"[ERROR] All attempts failed after {max_retries} tries")
                    return None
        
        return None
    
    def build_topics_with_vocab(self, vocab_map: Optional[Dict]) -> List[Dict]:
        """Build topic hierarchy using template + extracted vocabulary."""
        print("\n[INFO] Building topic hierarchy...")
        
        topics = []
        code_counter = 0
        
        def next_code():
            nonlocal code_counter
            code_counter += 1
            return f"L{code_counter}"  # L for Language
        
        # Level 0: Single root (no papers listed explicitly)
        root_code = next_code()
        topics.append({
            'code': root_code,
            'title': f"{self.subject['name']} - Themes",
            'level': 0,
            'parent': None
        })
        
        # Level 1: Themes (5 standard themes)
        for theme_name, subtopics in STANDARD_THEMES.items():
            theme_code = next_code()
            topics.append({
                'code': theme_code,
                'title': theme_name,
                'level': 1,
                'parent': root_code
            })
            
            # Level 2: Sub-topics
            for subtopic_name in subtopics:
                subtopic_code = next_code()
                topics.append({
                    'code': subtopic_code,
                    'title': subtopic_name,
                    'level': 2,
                    'parent': theme_code
                })
                
                # Level 3: Vocabulary (if available)
                if vocab_map:
                    vocab_words = self._find_vocab(vocab_map, theme_name, subtopic_name)
                    if vocab_words and len(vocab_words) > 0:
                        # Create one vocab entry with multiple words
                        vocab_code = next_code()
                        # Ensure UTF-8 encoding in title
                        vocab_title = f"Vocabulary: {', '.join(vocab_words[:15])}"  # Limit to 15 words
                        topics.append({
                            'code': vocab_code,
                            'title': vocab_title,
                            'level': 3,
                            'parent': subtopic_code
                        })
        
        print(f"[OK] Built {len(topics)} topics")
        return topics
    
    def _find_vocab(self, vocab_map: Dict, theme_name: str, subtopic_name: str) -> List[str]:
        """Find vocabulary for a specific sub-topic."""
        # Try to match theme
        for theme_key, theme_data in vocab_map.items():
            if self._theme_matches(theme_key, theme_name):
                if isinstance(theme_data, dict):
                    # Try to match subtopic
                    for subtopic_key, words in theme_data.items():
                        if self._subtopic_matches(subtopic_key, subtopic_name):
                            if isinstance(words, list):
                                return words
                    # If no exact subtopic match, return first available
                    for words in theme_data.values():
                        if isinstance(words, list) and len(words) > 0:
                            return words
                            break
                elif isinstance(theme_data, list):
                    return theme_data
        return []
    
    def _theme_matches(self, theme_key: str, theme_name: str) -> bool:
        """Check if theme keys match."""
        key_lower = theme_key.lower()
        name_lower = theme_name.lower()
        
        # Check for key words
        if 'home' in name_lower and 'home' in key_lower:
            return True
        if 'education' in name_lower and 'education' in key_lower:
            return True
        if 'personal' in name_lower and 'personal' in key_lower:
            return True
        if 'world' in name_lower and 'world' in key_lower:
            return True
        if 'social' in name_lower and 'social' in key_lower:
            return True
        return False
    
    def _subtopic_matches(self, subtopic_key: str, subtopic_name: str) -> bool:
        """Check if subtopic keys match."""
        key_words = set(subtopic_key.lower().split())
        name_words = set(subtopic_name.lower().split())
        
        # Check for word overlap
        overlap = key_words & name_words
        return len(overlap) >= 1
    
    def upload(self, topics: List[Dict]) -> bool:
        """Upload to Supabase with UTF-8 encoding."""
        print("\n[INFO] Uploading to Supabase...")
        
        try:
            # Create/update subject
            result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': f"{self.subject['name']} ({self.subject['qualification']})",
                'subject_code': self.subject['code'],
                'qualification_type': self.subject['qualification'],
                'specification_url': self.subject['pdf_url'],
                'exam_board': self.subject['exam_board']
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            subject_id = result.data[0]['id']
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
            
            # Insert with proper UTF-8 encoding
            to_insert = []
            for t in topics:
                # Ensure title is properly encoded UTF-8 string
                title = t['title']
                if not isinstance(title, str):
                    title = str(title)
                
                to_insert.append({
                    'subject_id': subject_id,
                    'topic_code': t['code'],
                    'topic_name': title,  # Native scripts preserved here
                    'topic_level': t['level'],
                    'exam_board': self.subject['exam_board']
                })
            
            # Insert in batches
            BATCH_SIZE = 100
            all_inserted = []
            
            for i in range(0, len(to_insert), BATCH_SIZE):
                batch = to_insert[i:i+BATCH_SIZE]
                inserted = supabase.table('staging_aqa_topics').insert(batch).execute()
                all_inserted.extend(inserted.data)
                print(f"[OK] Batch {i//BATCH_SIZE + 1}: {len(inserted.data)} topics")
            
            print(f"[OK] Uploaded {len(all_inserted)} topics total")
            
            # Link parents
            code_to_id = {t['topic_code']: t['id'] for t in all_inserted}
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
            
            print(f"[OK] Linked {linked} parent relationships")
            return True
            
        except Exception as e:
            print(f"[ERROR] Upload failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def scrape(self) -> bool:
        """Main workflow."""
        print(f"\n{'='*60}")
        print(f"LANGUAGE SCRAPING: {self.subject['name']}")
        print('='*60)
        
        # Download
        pdf = self.download_pdf()
        if not pdf:
            return False
        
        # Extract vocab section
        vocab_text = self.extract_vocab_appendix(pdf)
        if not vocab_text:
            print("[WARNING] No vocabulary section found, using structure only")
            vocab_map = None
        else:
            # Extract vocab with AI
            vocab_map = self.extract_vocab_with_ai(vocab_text)
            if not vocab_map:
                print("[WARNING] Vocab extraction failed, using structure only")
        
        # Build topics
        topics = self.build_topics_with_vocab(vocab_map)
        
        # Show breakdown
        by_level = {}
        for t in topics:
            by_level[t['level']] = by_level.get(t['level'], 0) + 1
        
        print(f"\n[INFO] Topic breakdown:")
        for level in sorted(by_level.keys()):
            print(f"  Level {level}: {by_level[level]} topics")
        
        # Upload
        success = self.upload(topics)
        print(f"\n{'[SUCCESS]' if success else '[FAILED]'}")
        return success


def load_subjects(file: Path):
    with open(file, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subject', help='Subject code (e.g., IG-French)')
    parser.add_argument('--all', action='store_true', help='All standard language subjects')
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    file = script_dir / "International-GCSE" / "international-gcse-subjects.json"
    all_subjects = load_subjects(file)
    
    # Standard structure languages (exclude Arabic First Lang, Greek First Lang, ESL)
    standard_languages = ['French', 'Spanish', 'German', 'Tamil', 'Bangla', 'Sinhala', 'Swahili', 'Chinese']
    
    if args.subject:
        subject = next((s for s in all_subjects if s['code'] == args.subject), None)
        if not subject:
            print(f"[ERROR] Subject not found: {args.subject}")
            sys.exit(1)
        subjects_to_scrape = [subject]
        
    elif args.all:
        subjects_to_scrape = [s for s in all_subjects if any(lang in s['name'] for lang in standard_languages)]
        print(f"\n[INFO] Found {len(subjects_to_scrape)} standard language subjects")
        
    else:
        parser.print_help()
        sys.exit(1)
    
    print(f"\n[INFO] Will scrape {len(subjects_to_scrape)} language subject(s)")
    
    results = {'success': 0, 'failed': 0}
    
    for subject in subjects_to_scrape:
        scraper = LanguageVocabScraper(subject)
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

