"""
Universal GCSE Scraper - One scraper to rule them all!
======================================================

Uses YAML config files to define subject-specific extraction rules.
No more duplicate code - just update the config for each subject.

Usage:
    python universal-gcse-scraper.py configs/citizenship.yaml
    python universal-gcse-scraper.py configs/computer_science.yaml
    python universal-gcse-scraper.py configs/business.yaml
"""

import os
import sys
import re
import yaml
import requests
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv
from supabase import create_client

try:
    from pypdf import PdfReader
    PDF_LIBRARY = 'pypdf'
except ImportError:
    import PyPDF2
    PdfReader = PyPDF2.PdfReader
    PDF_LIBRARY = 'PyPDF2'

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))


class UniversalGCSEScraper:
    """Universal scraper that works for any GCSE subject with proper config."""
    
    def __init__(self, config_path):
        """Load config from YAML file."""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.subject = self.config['subject']
        self.main_topics = self.config.get('main_topics', [])
        self.patterns = self.config.get('patterns', {})
        self.skip_patterns = self.config.get('skip_patterns', [])
    
    def download_pdf(self):
        """Download PDF and extract text."""
        print(f"\n[INFO] Downloading PDF for {self.subject['name']}...")
        
        try:
            response = requests.get(self.subject['pdf_url'], timeout=60)
            response.raise_for_status()
            
            print(f"[OK] Downloaded {len(response.content):,} bytes")
            
            pdf_file = BytesIO(response.content)
            reader = PdfReader(pdf_file)
            
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            print(f"[OK] Extracted {len(text):,} characters from {len(reader.pages)} pages")
            
            # Save debug
            debug_name = f"debug-{self.subject['code']}-universal.txt"
            debug_path = Path(__file__).parent / debug_name
            debug_path.write_text(text, encoding='utf-8')
            print(f"[OK] Saved debug to {debug_name}")
            
            return text
            
        except Exception as e:
            print(f"[ERROR] Download failed: {e}")
            raise
    
    def should_skip_line(self, line):
        """Check if line should be skipped based on skip patterns."""
        for pattern in self.skip_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False
    
    def parse_topics(self, text):
        """Parse topics based on config patterns."""
        print(f"\n[INFO] Parsing {self.subject['name']} topics...")
        
        topics = []
        
        # Add main topics (Level 0) if provided
        if self.main_topics:
            topics.extend(self.main_topics)
            print(f"[OK] Added {len(self.main_topics)} main topics (Level 0)")
        
        lines = text.split('\n')
        
        # Track state
        current_theme = None
        current_section = None
        current_topic = None
        topic_counter = {}
        seen_sections = set()  # Track sections to avoid duplicates
        
        # Get patterns
        theme_pattern = self.patterns.get('theme')
        section_pattern = self.patterns.get('section')
        topic_pattern = self.patterns.get('topic')
        bullet_pattern = self.patterns.get('bullet', r'^[●•]\s+')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # Skip lines matching skip patterns
            if self.should_skip_line(line):
                i += 1
                continue
            
            # Pattern 1: Theme detection
            if theme_pattern:
                theme_match = re.match(theme_pattern, line, re.IGNORECASE)
                if theme_match:
                    theme_id = theme_match.group(1)
                    current_theme = f'Theme{theme_id}'
                    topic_counter[current_theme] = 0
                    seen_sections = set()  # Reset seen sections for new theme
                    print(f"\n[INFO] Entering {current_theme}")
                    i += 1
                    continue
            
            if not current_theme and self.main_topics:
                i += 1
                continue
            
            # Pattern 2: Section detection (Level 1)
            if section_pattern:
                section_match = re.match(section_pattern, line, re.IGNORECASE)
                if section_match:
                    # Check if we've already seen this section (avoid duplicates)
                    section_text = line.strip()
                    if section_text in seen_sections:
                        print(f"  [SKIP] Duplicate section: {section_text[:50]}")
                        i += 1
                        continue
                    
                    seen_sections.add(section_text)
                    
                    section_num = len([t for t in topics if t.get('parent') == current_theme and t['level'] == 1]) + 1
                    section_code = f"{current_theme}_S{section_num}"
                    current_section = section_code
                    
                    topics.append({
                        'code': section_code,
                        'title': section_text,
                        'level': 1,
                        'parent': current_theme
                    })
                    print(f"  [OK] Level 1: {section_text[:70]}")
                    i += 1
                    continue
            
            # Pattern 3: Topic detection (Level 2)
            if topic_pattern and current_section:
                topic_match = re.match(topic_pattern, line)
                if topic_match:
                    num = topic_match.group(1)
                    title_parts = [topic_match.group(2).strip()]
                    
                    # Look ahead for multi-line titles
                    j = i + 1
                    while j < len(lines) and j < i + 5:
                        next_line = lines[j].strip()
                        
                        if not next_line:
                            break
                        if re.match(bullet_pattern, next_line):
                            break
                        if re.match(topic_pattern, next_line):
                            break
                        if section_pattern and re.match(section_pattern, next_line, re.IGNORECASE):
                            break
                        
                        title_parts.append(next_line)
                        j += 1
                    
                    full_title = ' '.join(title_parts).strip()
                    topic_counter[current_theme] += 1
                    
                    topic_code = f"{current_theme}_T{topic_counter[current_theme]}"
                    current_topic = topic_code
                    
                    topics.append({
                        'code': topic_code,
                        'title': f"{num}. {full_title}",
                        'level': 2,
                        'parent': current_section
                    })
                    print(f"    [OK] Level 2: {num}. {full_title[:60]}")
                    i += 1
                    continue
            
            # Pattern 4: Bullets (Level 3)
            if re.match(bullet_pattern, line) and current_topic:
                bullet_text = line.lstrip('●•').strip()
                
                if len(bullet_text) < 5:
                    i += 1
                    continue
                
                # Look ahead for multi-line bullets
                bullet_lines = [bullet_text]
                j = i + 1
                while j < len(lines) and j < i + 10:
                    next_line = lines[j].strip()
                    
                    if not next_line:
                        break
                    if re.match(bullet_pattern, next_line):
                        break
                    if topic_pattern and re.match(topic_pattern, next_line):
                        break
                    if section_pattern and re.match(section_pattern, next_line, re.IGNORECASE):
                        break
                    
                    bullet_lines.append(next_line)
                    j += 1
                
                full_bullet = ' '.join(bullet_lines).strip()
                
                existing_bullets = [t for t in topics if t.get('parent') == current_topic and t['level'] == 3]
                bullet_num = len(existing_bullets) + 1
                
                topics.append({
                    'code': f"{current_topic}_B{bullet_num}",
                    'title': full_bullet,
                    'level': 3,
                    'parent': current_topic
                })
                print(f"      [OK] Level 3: {full_bullet[:70]}")
                i = j
                continue
            
            i += 1
        
        return topics
    
    def upload_topics(self, topics):
        """Upload topics to Supabase."""
        print("\n[INFO] Uploading to Supabase...")
        
        try:
            # Create/update subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': f"{self.subject['name']} ({self.subject['qualification']})",
                'subject_code': self.subject['code'],
                'qualification_type': self.subject['qualification'],
                'specification_url': self.subject['pdf_url'],
                'exam_board': self.subject['exam_board']
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            subject_id = subject_result.data[0]['id']
            print(f"[OK] Subject ID: {subject_id}")
            
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
            
            # Link parent relationships
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
            
            print(f"[OK] Linked {linked} parent-child relationships")
            
            # Summary
            levels = {}
            for t in topics:
                levels[t['level']] = levels.get(t['level'], 0) + 1
            
            print("\n" + "=" * 80)
            print(f"[SUCCESS] {self.subject['name'].upper()} UPLOADED!")
            print("=" * 80)
            for level in sorted(levels.keys()):
                level_name = self.config.get('level_names', {}).get(level, f"Level {level}")
                print(f"   {level_name}: {levels[level]}")
            print(f"\n   Total: {len(topics)} topics")
            print("=" * 80)
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run(self):
        """Main scraping pipeline."""
        print("=" * 80)
        print(f"UNIVERSAL GCSE SCRAPER - {self.subject['name'].upper()}")
        print("=" * 80)
        
        try:
            text = self.download_pdf()
            topics = self.parse_topics(text)
            
            if len(topics) < 10:
                print(f"\n[WARNING] Only {len(topics)} topics found!")
                response = input("\nContinue? (y/n): ")
                if response.lower() != 'y':
                    return False
            
            return self.upload_topics(topics)
            
        except Exception as e:
            print(f"\n[FATAL ERROR] {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python universal-gcse-scraper.py <config_file>")
        print("\nExample:")
        print("  python universal-gcse-scraper.py configs/citizenship.yaml")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    if not Path(config_path).exists():
        print(f"[ERROR] Config file not found: {config_path}")
        sys.exit(1)
    
    scraper = UniversalGCSEScraper(config_path)
    success = scraper.run()
    
    if success:
        print("\n✅ SCRAPING COMPLETE!")
    else:
        print("\n❌ SCRAPING FAILED")


if __name__ == '__main__':
    main()

