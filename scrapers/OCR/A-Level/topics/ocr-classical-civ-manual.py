"""
OCR A-Level Classical Civilisation Manual Structure Scraper
============================================================

APPROACH:
1. Manually define Level 0 (Components) and Level 1 (Topics + Prescribed Books)
2. Scrape PDF to extract Level 2 (Key topics) and Level 3 (Learning outcomes)

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-classical-civ-manual.py
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
openai_key = os.getenv('OPENAI_API_KEY')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')
gemini_key = os.getenv('GEMINI2.5_API_KEY') or os.getenv('GEMINI_API_KEY')

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found!")
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
    'name': 'Classical Civilisation',
    'code': 'H408',
    'qualification': 'A-Level',
    'exam_board': 'OCR',
    'pdf_url': 'https://www.ocr.org.uk/Images/315133-specification-accredited-a-level-classical-civilisation-h408.pdf'
}

# MANUAL STRUCTURE
MANUAL_STRUCTURE = [
    {
        'code': 'Component11',
        'title': 'Component 11: The world of the hero',
        'level': 0,
        'parent': None,
        'children': [
            {'code': 'Component11_PrescribedBooks', 'title': 'Prescribed Books', 'level': 1, 'parent': 'Component11', 'is_special': True},
            {'code': 'Component11_Iliad', 'title': "Homer's Iliad", 'level': 1, 'parent': 'Component11'},
            {'code': 'Component11_Odyssey', 'title': "Homer's Odyssey", 'level': 1, 'parent': 'Component11'},
            {'code': 'Component11_Aeneid', 'title': "Virgil's Aeneid", 'level': 1, 'parent': 'Component11'},
        ]
    },
    {
        'code': 'ComponentGroup2',
        'title': 'Component group 2: Culture and the arts',
        'level': 0,
        'parent': None,
        'children': [
            {'code': 'ComponentGroup2_PrescribedBooks', 'title': 'Prescribed Books', 'level': 1, 'parent': 'ComponentGroup2', 'is_special': True},
            {'code': 'ComponentGroup2_21', 'title': 'Greek Theatre (H408/21)', 'level': 1, 'parent': 'ComponentGroup2'},
            {'code': 'ComponentGroup2_22', 'title': 'Imperial Image (H408/22)', 'level': 1, 'parent': 'ComponentGroup2'},
            {'code': 'ComponentGroup2_23', 'title': 'Invention of the Barbarian (H408/23)', 'level': 1, 'parent': 'ComponentGroup2'},
            {'code': 'ComponentGroup2_24', 'title': 'Greek Art (H408/24)', 'level': 1, 'parent': 'ComponentGroup2'},
        ]
    },
    {
        'code': 'ComponentGroup3',
        'title': 'Component group 3: Beliefs and ideas',
        'level': 0,
        'parent': None,
        'children': [
            {'code': 'ComponentGroup3_PrescribedBooks', 'title': 'Prescribed Books', 'level': 1, 'parent': 'ComponentGroup3', 'is_special': True},
            {'code': 'ComponentGroup3_31', 'title': 'Greek Religion (H408/31)', 'level': 1, 'parent': 'ComponentGroup3'},
            {'code': 'ComponentGroup3_32', 'title': 'Love and Relationships (H408/32)', 'level': 1, 'parent': 'ComponentGroup3'},
            {'code': 'ComponentGroup3_33', 'title': 'Politics of the Late Republic (H408/33)', 'level': 1, 'parent': 'ComponentGroup3'},
            {'code': 'ComponentGroup3_34', 'title': 'Democracy and the Athenians (H408/34)', 'level': 1, 'parent': 'ComponentGroup3'},
        ]
    }
]


class ClassicalCivScraper:
    """Manual structure + PDF detail scraper for Classical Civilisation."""
    
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
            # Add Level 0
            topics.append({
                'code': component['code'],
                'title': component['title'],
                'level': component['level'],
                'parent': component['parent']
            })
            print(f"[L0] {component['code']}: {component['title']}")
            
            # Add Level 1
            for child in component.get('children', []):
                topics.append({
                    'code': child['code'],
                    'title': child['title'],
                    'level': child['level'],
                    'parent': child['parent'],
                    'is_special': child.get('is_special', False)
                })
                prefix = "  [L1-SPECIAL]" if child.get('is_special') else "  [L1]"
                print(f"{prefix} {child['code']}: {child['title']}")
        
        print(f"\n[OK] Manual structure: {len(topics)} topics")
        return topics
    
    def scrape_pdf_details(self, manual_topics: List[Dict]) -> List[Dict]:
        """Download PDF and extract details."""
        print("\n" + "="*80)
        print("STEP 2: Scraping PDF for Key Topics & Prescribed Books")
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
            return manual_topics
        
        all_topics = manual_topics.copy()
        
        # Process Prescribed Books sections first
        print("\n[INFO] Processing Prescribed Books sections...")
        prescribed_topics = [t for t in manual_topics if t.get('is_special')]
        for topic in prescribed_topics:
            details = self._extract_prescribed_books(topic['code'], pdf_text, topic['code'], 2)
            if details:
                print(f"[OK] Found {len(details)} book categories for {topic['code']}")
                all_topics.extend(details)
        
        # Process regular L1 topics (not Prescribed Books)
        print("\n[INFO] Processing regular topics...")
        regular_topics = [t for t in manual_topics if t['level'] == 1 and not t.get('is_special')]
        for topic in regular_topics:
            print(f"\n[INFO] Processing: {topic['title']}")
            details = self._extract_key_topics(topic['title'], pdf_text, topic['code'], 2)
            if details:
                # Count by level
                level_counts = {}
                for d in details:
                    level_counts[d['level']] = level_counts.get(d['level'], 0) + 1
                level_str = ", ".join([f"L{k}:{v}" for k, v in sorted(level_counts.items())])
                print(f"[OK] Found {len(details)} items for {topic['code']} ({level_str})")
                all_topics.extend(details)
            time.sleep(1)
        
        print(f"\n[OK] Total topics: {len(all_topics)}")
        return all_topics
    
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
            self.debug_dir.joinpath(f"{self.subject['code']}-spec.txt").write_text(text, encoding='utf-8')
            return text
        except Exception as e:
            print(f"[ERROR] PDF extraction failed: {e}")
            return None
    
    def _extract_prescribed_books(self, section_name: str, pdf_text: str, parent_code: str, base_level: int) -> List[Dict]:
        """Extract prescribed books from section 5d."""
        
        # Find section 5d
        match = re.search(r'5d\.?\s*Suggested secondary sources.*?(?=\n5[a-z]\.|\nSummary of updates|$)', pdf_text, re.DOTALL | re.IGNORECASE)
        if not match:
            print(f"[WARN] Could not find section 5d")
            return []
        
        section_5d = match.group(0)
        
        # Use AI to extract book categories
        prompt = f"""Extract the book categories and books from this OCR Classical Civilisation prescribed books section.

This is section 5d "Suggested secondary sources, scholars and academic works"

The format has category headings followed by book references.

EXAMPLE:
Homer's 'Iliad' and 'Odyssey'
Edwards, M. W. (1987) Homer: Poet of the Iliad, John Hopkins
Fowler, R. (ed) (2004) The Cambridge Companion to Homer, Cambridge University Press

Virgil's 'Aeneid'
Camps, W. A. (1969) An Introduction to Virgil's Aeneid, Oxford University Press

YOUR TASK:
Extract as a numbered list where:
- Level 1 = Category heading (e.g., "Homer's 'Iliad' and 'Odyssey'")
- Level 2 = Each book reference under that category

OUTPUT FORMAT:
1. Homer's 'Iliad' and 'Odyssey'
1.1 Edwards, M. W. (1987) Homer: Poet of the Iliad, John Hopkins
1.2 Fowler, R. (ed) (2004) The Cambridge Companion to Homer, Cambridge University Press
2. Virgil's 'Aeneid'
2.1 Camps, W. A. (1969) An Introduction to Virgil's Aeneid, Oxford University Press

SECTION TEXT:
{section_5d[:30000]}"""
        
        try:
            if AI_PROVIDER == "openai":
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=8000,
                    temperature=0
                )
                ai_output = response.choices[0].message.content
            elif AI_PROVIDER == "anthropic":
                response = claude.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=8000,
                    messages=[{"role": "user", "content": prompt}]
                )
                ai_output = response.content[0].text
            elif AI_PROVIDER == "gemini":
                response = gemini_model.generate_content(prompt)
                ai_output = response.text
            
            return self._parse_numbered_hierarchy(ai_output, parent_code, base_level)
        except Exception as e:
            print(f"[ERROR] AI extraction failed: {e}")
            return []
    
    def _extract_key_topics(self, topic_name: str, pdf_text: str, parent_code: str, base_level: int) -> List[Dict]:
        """Extract key topics table for a specific topic."""
        
        # Build flexible search patterns (handle italics, possessives, etc.)
        search_terms = []
        if "Iliad" in topic_name:
            search_terms = ["Iliad", "Homer's Iliad", "Homer's 'Iliad'"]
        elif "Odyssey" in topic_name:
            search_terms = ["Odyssey", "Homer's Odyssey", "Homer's 'Odyssey'"]
        elif "Aeneid" in topic_name:
            search_terms = ["Aeneid", "Virgil's Aeneid", "Virgil's 'Aeneid'"]
        else:
            # For other topics, use the code in parentheses (e.g., H408/21)
            code_match = re.search(r'\(H408/\d+\)', topic_name)
            if code_match:
                search_terms = [code_match.group(0), topic_name.split('(')[0].strip()]
            else:
                search_terms = [topic_name]
        
        section_text = None
        for search_term in search_terms:
            # Look for the section with Key topics table
            # Include "Content of" prefix that appears in the PDF
            search_patterns = [
                rf'Content of {re.escape(search_term)}.*?Key topics.*?Learners should have studied',
                rf'Content of {re.escape(search_term)}.*?Key topics',
                rf'{re.escape(search_term)}.*?Key topics.*?Learners should have studied',
                rf'{re.escape(search_term)}.*?Key topics',
                # For epics, also try without possessive/quotes
                rf'Content of {search_term}.*?Key topics' if len(search_term) > 5 else None,
                rf'{search_term}.*?Key topics' if len(search_term) > 5 else None
            ]
            
            for pattern in [p for p in search_patterns if p]:
                matches = list(re.finditer(pattern, pdf_text, re.DOTALL | re.IGNORECASE))
                if matches:
                    # Take longest match (avoid TOC)
                    for match in matches:
                        start = match.start()
                        # Find end
                        end_patterns = [r'\n\d+[a-z]\.', r'Version \d+\.\d+', r'\nPrescribed', r'\n2[a-z]\.']
                        end_pos = len(pdf_text)
                        for ep in end_patterns:
                            end_match = re.search(ep, pdf_text[start+500:start+25000])
                            if end_match:
                                end_pos = start + 500 + end_match.start()
                                break
                        
                        potential_section = pdf_text[start:end_pos]
                        # Make sure it has substantive content
                        if len(potential_section) > 800 and 'Key topics' in potential_section:
                            section_text = potential_section
                            break
                    if section_text:
                        break
            if section_text:
                break
        
        if not section_text:
            print(f"[WARN] Could not find section for {topic_name}")
            return []
        
        print(f"[DEBUG] Found section: {len(section_text)} chars")
        
        # Use AI to extract the table
        prompt = f"""Extract ALL content from this OCR Classical Civilisation table.

TOPIC: "{topic_name}"

TABLE FORMAT:
| Key topics | Learners should have studied the following: |
|------------|---------------------------------------------|
| Topic 1    | • bullet point 1                            |
|            | • bullet point 2                            |
|            | • bullet point 3                            |
| Topic 2    | • bullet point 1                            |
|            | • bullet point 2                            |

EXAMPLE INPUT from Greek Theatre:
| Key topics | Learners should have studied the following: |
| Drama and the theatre in ancient Athenian society | • role and significance of drama and the theatre in ancient Athenian society, including the religious context of the dramatic festivals
• the organisation of the City Dionysia, including the make up and involvement of the theatre audience |

REQUIRED OUTPUT (numbered list with BOTH columns):
1. Drama and the theatre in ancient Athenian society
1.1 role and significance of drama and the theatre in ancient Athenian society, including the religious context of the dramatic festivals
1.2 the organisation of the City Dionysia, including the make up and involvement of the theatre audience
1.3 structure of the theatre space, and how this developed during the 5th and 4th centuries BC
1.4 the representation in visual and material culture of theatrical and dramatic scenes
2. Nature of tragedy
2.1 the origins of tragedy and how it developed during the 5th century BC, including its relationship to satyr-plays
2.2 the contributions of Aeschylus, Sophocles and Euripides
2.3 use of actors and the Chorus
2.4 use of masks, costumes and props

CRITICAL INSTRUCTIONS:
1. Find EVERY row in the table
2. For each row, extract the LEFT column text as "1. Topic Name"
3. For each row, extract EVERY bullet point from RIGHT column as "1.1", "1.2", "1.3" etc
4. DO NOT skip the bullet points - they are the most important part!
5. Split each bullet point (marked with • or ○) into separate numbered items
6. Must output BOTH the topic names AND all their bullet points

SECTION TEXT:
{section_text[:40000]}"""
        
        try:
            if AI_PROVIDER == "openai":
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=16000,
                    temperature=0
                )
                ai_output = response.choices[0].message.content
            elif AI_PROVIDER == "anthropic":
                response = claude.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=8000,
                    messages=[{"role": "user", "content": prompt}]
                )
                ai_output = response.content[0].text
            elif AI_PROVIDER == "gemini":
                response = gemini_model.generate_content(prompt)
                ai_output = response.text
            
            # Save AI output for debugging
            safe_filename = re.sub(r'[^\w\-]', '_', parent_code)
            ai_file = self.debug_dir / f"{safe_filename}-ai-output.txt"
            ai_file.write_text(ai_output, encoding='utf-8')
            print(f"[DEBUG] AI returned {len(ai_output)} chars, saved to {ai_file.name}")
            
            return self._parse_numbered_hierarchy(ai_output, parent_code, base_level)
        except Exception as e:
            print(f"[ERROR] AI extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_numbered_hierarchy(self, text: str, parent_code: str, base_level: int) -> List[Dict]:
        """Parse AI numbered output into topics."""
        topics = []
        parent_stack = {base_level - 1: parent_code}
        
        for line in text.split('\n'):
            # Don't strip yet - we want to preserve structure for debugging
            original_line = line
            line = line.strip()
            if not line:
                continue
            
            # Match numbered items, allowing for indentation (already stripped)
            match = re.match(r'^([\d.]+)[\.\):]?\s+(.+)$', line)
            if not match:
                continue
            
            number = match.group(1).rstrip('.')
            title = match.group(2).strip()
            
            if len(title) < 3:
                continue
            
            dots = number.count('.')
            level = base_level + dots
            code = f"{parent_code}_{number.replace('.', '_')}"
            parent_code_for_this = parent_stack.get(level - 1, parent_code)
            
            topics.append({
                'code': code,
                'title': title,
                'level': level,
                'parent': parent_code_for_this
            })
            
            parent_stack[level] = code
            for l in list(parent_stack.keys()):
                if l > level:
                    del parent_stack[l]
        
        return topics
    
    def upload_to_supabase(self, topics: List[Dict]) -> bool:
        """Upload topics to Supabase."""
        print("\n" + "="*80)
        print("STEP 3: Uploading to Supabase")
        print("="*80)
        
        # Remove 'is_special' flag before upload
        for topic in topics:
            topic.pop('is_special', None)
        
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
        print("\n" + "🏛️ "*40)
        print(f"OCR CLASSICAL CIVILISATION SCRAPER: {self.subject['name']} ({self.subject['code']})")
        print("🏛️ "*40)
        
        manual_topics = self.build_manual_structure()
        all_topics = self.scrape_pdf_details(manual_topics)
        
        if not all_topics:
            print("[ERROR] No topics found")
            return False
        
        success = self.upload_to_supabase(all_topics)
        
        if success:
            print("\n[SUCCESS] ✅ Classical Civilisation scraping complete!")
            print(f"Total topics: {len(all_topics)}")
        else:
            print("\n[FAILED] ❌ Upload failed")
        
        return success


def main():
    scraper = ClassicalCivScraper()
    success = scraper.scrape()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

