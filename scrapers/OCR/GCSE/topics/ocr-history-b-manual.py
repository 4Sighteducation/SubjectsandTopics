"""
OCR GCSE History B (J411) Manual Scraper
=========================================

Extracts topics from OCR GCSE History B J411 specification.

Structure:
- Level 0: Component Groups (Component Group 1, Component Group 2, Component Group 3)
- Level 1: All studies (ALL thematic studies, ALL British depth studies, History Around Us, ALL period studies, ALL world depth studies)
- Level 2+: Detailed content from each study

CRITICAL: 
- DO NOT create "History B (Schools History Project) (J411)" as Level 0 - start with Component Groups
- Extract ALL options, not just one:
  * Component Group 1: ALL 3 thematic studies + ALL 3 British depth studies
  * Component Group 2: History Around Us
  * Component Group 3: ALL 3 period studies + ALL 3 world depth studies
- Extract ALL depth - detailed content, sub-topics, learning objectives

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-history-b-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/207164-specification-accredited-gcse-history-b-.pdf'
SUBJECT_CODE = 'J411'
SUBJECT_NAME = 'History B (Schools History Project)'

COMPONENT_GROUPS = [
    {
        'code': '1',
        'name': 'Component Group 1: British History',
        'section_pattern': r'Introduction\s+to\s+the\s+Thematic\s+Study',
        'studies': [
            {
                'type': 'thematic',
                'name': 'The People\'s Health, c.1250 to present',
                'pattern': r'The\s+People\'s\s+Health,\s+c\.1250\s+to\s+present',
            },
            {
                'type': 'thematic',
                'name': 'Crime and Punishment, c.1250 to present',
                'pattern': r'Crime\s+and\s+Punishment,\s+c\.1250\s+to\s+present',
            },
            {
                'type': 'thematic',
                'name': 'Migrants to Britain, c.1250 to present',
                'pattern': r'Migrants\s+to\s+Britain,\s+c\.1250\s+to\s+present',
            },
            {
                'type': 'depth',
                'name': 'The Norman Conquest, 1065–1087',
                'pattern': r'The\s+Norman\s+Conquest,\s+1065[–-]1087',
            },
            {
                'type': 'depth',
                'name': 'The Elizabethans, 1580–1603',
                'pattern': r'The\s+Elizabethans,\s+1580[–-]1603',
            },
            {
                'type': 'depth',
                'name': 'Britain in Peace and War, 1900–1918',
                'pattern': r'Britain\s+in\s+Peace\s+and\s+War,\s+1900[–-]1918',
            },
        ]
    },
    {
        'code': '2',
        'name': 'Component Group 2: History Around Us',
        'section_pattern': r'Introduction\s+to\s+History\s+Around\s+Us',
        'studies': [
            {
                'type': 'site',
                'name': 'History Around Us',
                'pattern': r'History\s+Around\s+Us',
            },
        ]
    },
    {
        'code': '3',
        'name': 'Component Group 3: World History',
        'section_pattern': r'Introduction\s+to\s+the\s+Period\s+Study',
        'studies': [
            {
                'type': 'period',
                'name': 'Viking Expansion, c.750–c.1050',
                'pattern': r'Viking\s+Expansion,\s+c\.750[–-]c\.1050',
            },
            {
                'type': 'period',
                'name': 'The Mughal Empire, 1526–1707',
                'pattern': r'The\s+Mughal\s+Empire,\s+1526[–-]1707',
            },
            {
                'type': 'period',
                'name': 'The Making of America, 1789–1900',
                'pattern': r'The\s+Making\s+of\s+America,\s+1789[–-]1900',
            },
            {
                'type': 'depth',
                'name': 'The First Crusade, c.1070–1100',
                'pattern': r'The\s+First\s+Crusade,\s+c\.1070[–-]1100',
            },
            {
                'type': 'depth',
                'name': 'Aztecs and the Spanish Conquest, 1519–1535',
                'pattern': r'Aztecs\s+and\s+the\s+Spanish\s+Conquest,\s+1519[–-]1535',
            },
            {
                'type': 'depth',
                'name': 'Living under Nazi Rule, 1933–1945',
                'pattern': r'Living\s+under\s+Nazi\s+Rule,\s+1933[–-]1945',
            },
        ]
    },
]


class HistoryBScraper:
    """Scraper for OCR GCSE History B."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent.parent / "A-Level" / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_text = None
    
    def scrape_all(self):
        """Scrape all topics."""
        print("\n" + "📚 "*40)
        print("OCR GCSE HISTORY B SCRAPER")
        print("📚 "*40)
        
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
        
        # Extract each component group
        all_topics = []
        
        for group in COMPONENT_GROUPS:
            print("\n" + "="*80)
            print(f"[EXTRACTING] {group['name']}")
            print("="*80)
            
            # Level 0: Component Group
            group_code = f"{SUBJECT_CODE}_G{group['code']}"
            group_topic = {
                'code': group_code,
                'title': group['name'],
                'level': 0,
                'parent': None
            }
            all_topics.append(group_topic)
            
            # Find group section
            group_section = self._find_group_section(group)
            if not group_section:
                print(f"[WARN] Could not find section for {group['name']}")
                # Still try to extract individual studies
                pass
            
            # Extract each study in this group
            for study in group['studies']:
                print(f"\n[EXTRACTING] {study['name']}")
                
                # Find study section
                study_section = self._find_study_section(study, group_section)
                if not study_section:
                    print(f"[WARN] Could not find section for {study['name']}")
                    continue
                
                print(f"[OK] Found study section: {len(study_section)} chars")
                
                # Level 1: Study
                # Create a safe code from study name
                study_safe_name = re.sub(r'[^\w\s-]', '', study['name']).replace(' ', '_')[:30]
                study_code = f"{group_code}_{study_safe_name}"
                study_topic = {
                    'code': study_code,
                    'title': study['name'],
                    'level': 1,
                    'parent': group_code
                }
                all_topics.append(study_topic)
                
                # Extract content using AI
                print(f"[INFO] Extracting study content...")
                ai_output = self._extract_with_ai(study_section, study_code, study['name'], study['type'])
                
                if ai_output:
                    # Save AI output for debugging
                    safe_name = re.sub(r'[^\w\s-]', '', study['name'])[:50]
                    debug_file = self.debug_dir / f"{SUBJECT_CODE}-G{group['code']}-{safe_name}-ai-output.txt"
                    debug_file.write_text(ai_output, encoding='utf-8')
                    print(f"[DEBUG] Saved AI output to {debug_file.name}")
                    
                    parsed = self._parse_hierarchy(ai_output, study_code)
                    all_topics.extend(parsed)
                    print(f"[OK] Extracted {len(parsed)} topics")
                else:
                    print("[WARN] AI extraction failed")
        
        print(f"\n[OK] Extracted {len(all_topics)} topics total")
        
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
        success = self._upload_topics(all_topics)
        
        if success:
            print(f"\n[OK] ✓ Successfully uploaded {len(all_topics)} topics")
        else:
            print(f"\n[FAIL] ✗ Failed to upload topics")
        
        return success
    
    def _find_group_section(self, group: Dict) -> Optional[str]:
        """Find component group section."""
        pattern = group['section_pattern']
        matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE))
        
        if not matches:
            return None
        
        # Find actual content (not TOC entry)
        for match in matches:
            pos = match.start()
            after_text = self.pdf_text[pos:pos + 2000]
            before_text = self.pdf_text[max(0, pos - 200):pos]
            
            # Check if TOC entry
            if re.search(r'\d+\s*$', before_text[-50:]):
                continue
            
            # Check if actual content
            if re.search(r'Learners|Content|Study|Introduction|Thematic|Depth|Period|World', after_text, re.IGNORECASE):
                # Extract large section (500k chars or until next major section)
                start_pos = pos
                end_patterns = [
                    r'\n\s*Introduction\s+to\s+the\s+British\s+Depth',
                    r'\n\s*Introduction\s+to\s+History\s+Around\s+Us',
                    r'\n\s*Introduction\s+to\s+the\s+Period\s+Study',
                    r'\n\s*The\s+World\s+Depth\s+Study',
                    r'\n\s*2d\.\s+Prior\s+knowledge',
                    r'\n\s*3\.\s+Assessment',
                ]
                
                end_pos = min(start_pos + 500000, len(self.pdf_text))
                for end_pattern in end_patterns:
                    end_match = re.search(end_pattern, self.pdf_text[start_pos:start_pos + 500000], re.IGNORECASE)
                    if end_match:
                        end_pos = start_pos + end_match.start()
                        break
                
                return self.pdf_text[start_pos:end_pos]
        
        return None
    
    def _find_study_section(self, study: Dict, group_section: Optional[str]) -> Optional[str]:
        """Find individual study section."""
        search_text = group_section if group_section else self.pdf_text
        pattern = study['pattern']
        matches = list(re.finditer(pattern, search_text, re.IGNORECASE))
        
        if not matches:
            return None
        
        # Find actual content (not TOC entry)
        for match in matches:
            pos = match.start()
            after_text = search_text[pos:pos + 3000]
            before_text = search_text[max(0, pos - 200):pos]
            
            # Check if TOC entry
            if re.search(r'\d+\s*$', before_text[-50:]):
                continue
            
            # Check if actual content
            if re.search(r'Learners|Content|Study|will|should|understand|explore|Medieval|Early\s+Modern|Industrial|Britain|periods|issues|factors', after_text, re.IGNORECASE):
                # Extract section (200k chars or until next study)
                start_pos = pos
                end_patterns = [
                    r'\n\s*The\s+People\'s\s+Health',
                    r'\n\s*Crime\s+and\s+Punishment',
                    r'\n\s*Migrants\s+to\s+Britain',
                    r'\n\s*The\s+Norman\s+Conquest',
                    r'\n\s*The\s+Elizabethans',
                    r'\n\s*Britain\s+in\s+Peace\s+and\s+War',
                    r'\n\s*Viking\s+Expansion',
                    r'\n\s*The\s+Mughal\s+Empire',
                    r'\n\s*The\s+Making\s+of\s+America',
                    r'\n\s*The\s+First\s+Crusade',
                    r'\n\s*Aztecs\s+and\s+the\s+Spanish\s+Conquest',
                    r'\n\s*Living\s+under\s+Nazi\s+Rule',
                    r'\n\s*Introduction\s+to\s+the',
                    r'\n\s*The\s+World\s+Depth\s+Study',
                    r'\n\s*Content\s+of\s+GCSE',
                    r'\n\s*2d\.\s+Prior',
                    r'\n\s*3\.\s+Assessment',
                ]
                
                end_pos = min(start_pos + 200000, len(search_text))
                for end_pattern in end_patterns:
                    end_match = re.search(end_pattern, search_text[start_pos:start_pos + 200000], re.IGNORECASE)
                    if end_match:
                        end_pos = start_pos + end_match.start()
                        break
                
                return search_text[start_pos:end_pos]
        
        return None
    
    def _extract_with_ai(self, text: str, parent_code: str, study_name: str, study_type: str) -> Optional[str]:
        """Extract content using AI."""
        # Limit text size
        text = text[:200000]  # 200k chars max
        
        prompt = f"""Extract the complete topic hierarchy from this OCR GCSE History B specification section.

STUDY: {study_name}
STUDY TYPE: {study_type}
PARENT CODE: {parent_code}

CRITICAL REQUIREMENTS:
1. DO NOT create "History B (Schools History Project) (J411)" or subject name as Level 0 - component groups are already Level 0, studies are Level 1
2. Extract ALL content with FULL depth - don't skip any topics, sub-topics, or learning objectives

3. STRUCTURE REQUIREMENTS:
   Level 2: Main topics/sections (e.g., time periods like "Medieval Britain c.1250–c.1500", themes, major events, issues, factors)
   Level 3: Sub-topics (e.g., specific events, policies, developments, bullet points)
   Level 4: Detailed points, learning objectives, specific content items
   Level 5+: Further detail, examples, specific facts

4. OUTPUT FORMAT: Numbered hierarchy (NOT markdown)
   CRITICAL: Use numbered format ONLY, NOT markdown headers (### or ####)
   CRITICAL: Extract EVERYTHING - don't skip any content!
   
   Format:
   1. Level 2 Topic (e.g., "Medieval Britain c.1250–c.1500" or "England on the eve of the conquest")
   1.1. Level 3 Sub-topic (e.g., specific bullet points, events, developments)
   1.1.1. Level 4 Detail (e.g., specific learning objectives, points to cover)
   1.1.1.1. Level 5 Further detail (if applicable)
   1.2. Level 3 Sub-topic (next sub-topic)
   1.2.1. Level 4 Detail
   (continue for ALL topics with FULL depth)
   
   IMPORTANT: 
   - Extract ALL time periods, themes, events, policies, developments
   - Extract ALL learning objectives and detailed content points
   - Extract ALL bullet points, issues, factors, sub-topics
   - Extract ALL specific examples and facts
   - Don't skip any levels or content!
   
   DO NOT use:
   - ### or #### headers
   - Bullet points with dashes
   - Markdown formatting
   
   USE ONLY:
   - Numbered format: "1.", "1.1.", "1.1.1.", "1.1.1.1.", etc.

5. DEPTH REQUIREMENTS:
   - Extract ALL learning objectives, "Learners will", "Learners should" items
   - Extract ALL detailed points, examples, and specific content
   - Extract ALL sub-topics, events, policies, developments
   - Extract ALL bullet points from each period/section
   - Extract ALL issues and factors mentioned
   - Ensure comprehensive coverage of the entire study

6. DO NOT ask for confirmation. Extract EVERYTHING NOW.

CONTENT:
{text}

Extract the complete hierarchy now:"""

        return self._call_ai(prompt, max_tokens=16000)
    
    def _parse_hierarchy(self, text: str, base_code: str) -> List[Dict]:
        """Parse AI numbered output (handles both numbered and markdown formats)."""
        all_topics = []
        parent_stack = {-1: None}
        
        # Filter out subject-level topics
        excluded_patterns = [
            r'^history\s+b\s+\(schools\s+history\s+project\)\s+\(j411\)$',
            r'^history\s+b$',
            r'^subject:',
        ]
        
        lines = text.split('\n')
        for line in lines:
            original_line = line
            line = line.strip()
            if not line:
                continue
            
            # Check if excluded
            excluded = False
            for pattern in excluded_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    excluded = True
                    break
            
            if excluded:
                continue
            
            # Handle markdown headers: ### Level 1, #### Level 2
            markdown_match = re.match(r'^#{3,4}\s+(\d+(?:\.\d+)*)\.?\s+(.+)$', line)
            if markdown_match:
                number_str = markdown_match.group(1)
                title = markdown_match.group(2).strip()
                parts = number_str.split('.')
                level = len(parts) + 1  # Add 1 because studies are Level 1
                
                # Find parent
                parent_level = level - 1
                parent_code = parent_stack.get(parent_level)
                
                # If Level 2 and no parent found, use base_code
                if level == 2 and parent_code is None:
                    parent_code = base_code
                
                # Generate code
                if parent_code:
                    topic_code = f"{parent_code}_{parts[-1]}"
                else:
                    topic_code = f"{base_code}_{parts[0]}"
                
                topic = {
                    'code': topic_code,
                    'title': title,
                    'level': level,
                    'parent': parent_code
                }
                
                all_topics.append(topic)
                parent_stack[level] = topic_code
                continue
            
            # Handle bullet points with numbers: "- 1.1.1. Title"
            bullet_match = re.match(r'^[-•]\s+(\d+(?:\.\d+)*)\.\s+(.+)$', line)
            if bullet_match:
                number_str = bullet_match.group(1)
                title = bullet_match.group(2).strip()
                parts = number_str.split('.')
                level = len(parts) + 1  # Add 1 because studies are Level 1
                
                # Find parent
                parent_level = level - 1
                parent_code = parent_stack.get(parent_level)
                
                # If Level 2 and no parent found, use base_code
                if level == 2 and parent_code is None:
                    parent_code = base_code
                
                # Generate code
                if parent_code:
                    topic_code = f"{parent_code}_{parts[-1]}"
                else:
                    topic_code = f"{base_code}_{parts[0]}"
                
                topic = {
                    'code': topic_code,
                    'title': title,
                    'level': level,
                    'parent': parent_code
                }
                
                all_topics.append(topic)
                parent_stack[level] = topic_code
                continue
            
            # Handle regular numbered format: "1. Title" or "1.1. Title" or "1.1.1. Title"
            match = re.match(r'^(\d+(?:\.\d+)*)\.\s+(.+)$', line)
            if match:
                number_str = match.group(1)
                title = match.group(2).strip()
                parts = number_str.split('.')
                level = len(parts) + 1  # Add 1 because studies are Level 1
                
                # Find parent
                parent_level = level - 1
                parent_code = parent_stack.get(parent_level)
                
                # If Level 2 and no parent found, use base_code
                if level == 2 and parent_code is None:
                    parent_code = base_code
                
                # Generate code
                if parent_code:
                    topic_code = f"{parent_code}_{parts[-1]}"
                else:
                    topic_code = f"{base_code}_{parts[0]}"
                
                topic = {
                    'code': topic_code,
                    'title': title,
                    'level': level,
                    'parent': parent_code
                }
                
                all_topics.append(topic)
                parent_stack[level] = topic_code
        
        return all_topics
    
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
                wait_time = (attempt + 1) * 5
                print(f"[WARN] AI call failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"[INFO] Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print("[ERROR] All AI retries failed")
                    return None
        
        return None
    
    def _download_pdf(self, url: str) -> Optional[bytes]:
        """Download PDF from URL."""
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            if response.content[:4] == b'%PDF':
                print(f"[OK] Downloaded PDF: {len(response.content)/1024/1024:.1f} MB")
                return response.content
            else:
                print("[ERROR] Downloaded content is not a PDF")
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
    
    def _upload_topics(self, topics: List[Dict]) -> bool:
        """Upload topics to database."""
        if not topics:
            print("[WARN] No topics to upload")
            return False
        
        try:
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': f"{SUBJECT_NAME} (GCSE)",
                'subject_code': SUBJECT_CODE,
                'qualification_type': 'GCSE',
                'specification_url': PDF_URL,
                'exam_board': 'OCR'
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            subject_id = subject_result.data[0]['id']
            
            # Clear old topics for this subject
            print("[INFO] Clearing old topics...")
            supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).eq('exam_board', 'OCR').execute()
            
            # Remove duplicates and check for issues
            seen_codes = set()
            unique_topics = []
            duplicate_codes = []
            for t in topics:
                if t['code'] not in seen_codes:
                    seen_codes.add(t['code'])
                    unique_topics.append(t)
                else:
                    duplicate_codes.append(t['code'])
            
            if duplicate_codes:
                print(f"[WARN] Found {len(duplicate_codes)} duplicate codes: {duplicate_codes[:10]}")
            
            print(f"[INFO] After deduplication: {len(unique_topics)} unique topics from {len(topics)} total")
            
            # Insert topics in batches to catch errors
            to_insert = [{
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': t['title'],
                'topic_level': t['level'],
                'exam_board': 'OCR'
            } for t in unique_topics]
            
            print(f"[INFO] Attempting to insert {len(to_insert)} topics...")
            
            # Insert in batches to catch errors
            batch_size = 50
            all_inserted = []
            failed_items = []
            
            for i in range(0, len(to_insert), batch_size):
                batch = to_insert[i:i + batch_size]
                try:
                    inserted = supabase.table('staging_aqa_topics').insert(batch).execute()
                    all_inserted.extend(inserted.data)
                    print(f"[INFO] Inserted batch {i//batch_size + 1} ({len(batch)} topics)")
                except Exception as e:
                    print(f"[ERROR] Batch {i//batch_size + 1} failed: {e}")
                    # Try inserting one by one to find the problem
                    for item in batch:
                        try:
                            single_insert = supabase.table('staging_aqa_topics').insert([item]).execute()
                            all_inserted.extend(single_insert.data)
                        except Exception as e2:
                            print(f"[ERROR] Failed to insert topic {item['topic_code']} ({item['topic_name'][:50]}): {e2}")
                            failed_items.append(item)
            
            print(f"[INFO] Successfully inserted {len(all_inserted)} topics, {len(failed_items)} failed")
            if failed_items:
                print(f"[DEBUG] Failed topics: {[item['topic_code'] for item in failed_items[:10]]}")
            
            # Link hierarchy
            code_to_id = {t['topic_code']: t['id'] for t in all_inserted}
            linked_count = 0
            failed_links = 0
            
            for topic in unique_topics:
                if topic['parent']:
                    parent_id = code_to_id.get(topic['parent'])
                    child_id = code_to_id.get(topic['code'])
                    if parent_id and child_id:
                        try:
                            supabase.table('staging_aqa_topics').update({
                                'parent_topic_id': parent_id
                            }).eq('id', child_id).execute()
                            linked_count += 1
                        except Exception as e:
                            print(f"[WARN] Failed to link {topic['code']} to {topic['parent']}: {e}")
                            failed_links += 1
                    elif not parent_id:
                        print(f"[WARN] Parent {topic['parent']} not found for {topic['code']}")
                        failed_links += 1
            
            print(f"[INFO] Linked {linked_count} parent-child relationships, {failed_links} failed")
            print(f"[OK] Successfully uploaded {len(all_inserted)} topics")
            return True
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    scraper = HistoryBScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)



