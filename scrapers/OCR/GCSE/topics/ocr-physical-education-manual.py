"""
OCR GCSE Physical Education (J587) Manual Scraper
=================================================

Extracts topics from OCR GCSE Physical Education J587 specification.

Structure:
- Level 0: Components (Component 01, Component 02)
- Level 1: Sections (e.g., "Section 1.1: Applied anatomy and physiology")
- Level 2: Topic Areas (e.g., "Lever systems", "Planes of movement and axes of rotation")
- Level 3: "Learners must:" items (extracted from the "Learners must:" column, NOT prefixed with "Content:")

CRITICAL: 
- DO NOT create "Physical Education (J587)" as Level 0 - start with Components
- Extract "Learners must:" items from the table and append them to Topic Area parents
- DO NOT prefix topics with "Content:" - use the actual "Learners must:" text
- Ignore icons/images in PDF tables

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-physical-education-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/234822-specification-accredited-gcse-physical-education-j587.pdf'
SUBJECT_CODE = 'J587'
SUBJECT_NAME = 'Physical Education'

COMPONENTS = [
    {
        'code': '01',
        'name': 'Component 01: Physical factors affecting performance',
        'section_pattern': r'Content\s+of\s+Physical\s+factors\s+affecting\s+performance\s+\(J587/01\)',
    },
    {
        'code': '02',
        'name': 'Component 02: Socio-cultural issues and sports psychology',
        'section_pattern': r'Content\s+of\s+Socio-cultural\s+issues\s+and\s+sports\s+psychology\s+\(J587/02\)',
    },
]


class PhysicalEducationScraper:
    """Scraper for OCR GCSE Physical Education."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent.parent / "A-Level" / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_text = None
    
    def scrape_all(self):
        """Scrape all topics."""
        print("\n" + "🏃 "*40)
        print("OCR GCSE PHYSICAL EDUCATION SCRAPER")
        print("🏃 "*40)
        
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
        
        # Extract each component
        all_topics = []
        
        for component in COMPONENTS:
            print("\n" + "="*80)
            print(f"[EXTRACTING] {component['name']}")
            print("="*80)
            
            # Find component section
            component_section = self._find_component_section(component)
            if not component_section:
                print(f"[WARN] Could not find section for {component['name']}")
                continue
            
            print(f"[OK] Found component section: {len(component_section)} chars")
            
            # Level 0: Component
            component_code = f"{SUBJECT_CODE}_{component['code']}"
            component_topic = {
                'code': component_code,
                'title': component['name'],
                'level': 0,
                'parent': None
            }
            all_topics.append(component_topic)
            
            # Extract content using AI
            print(f"[INFO] Extracting component content...")
            ai_output = self._extract_with_ai(component_section, component_code, component['name'])
            
            if ai_output:
                # Save AI output for debugging
                debug_file = self.debug_dir / f"{SUBJECT_CODE}-{component['code']}-ai-output.txt"
                debug_file.write_text(ai_output, encoding='utf-8')
                print(f"[DEBUG] Saved AI output to {debug_file.name}")
                
                parsed = self._parse_hierarchy(ai_output, component_code)
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
    
    def _find_component_section(self, component: Dict) -> Optional[str]:
        """Find component section."""
        pattern = component['section_pattern']
        matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE))
        
        if not matches:
            print(f"[DEBUG] No matches for pattern: {pattern}")
            return None
        
        print(f"[DEBUG] Found {len(matches)} matches for component pattern")
        
        # Find actual content (not TOC entry)
        for match in matches:
            pos = match.start()
            after_text = self.pdf_text[pos:pos + 3000]
            before_text = self.pdf_text[max(0, pos - 200):pos]
            
            # Check if TOC entry (has page number immediately before or after)
            if re.search(r'\d+\s*$', before_text[-50:]) or re.search(r'^\d+', after_text[:50]):
                print(f"[DEBUG] Skipping TOC entry at position {pos}")
                continue
            
            # Check if actual content (has descriptive text or table structure)
            if re.search(r'Section|Topic\s+area|Learners\s+must|table|This\s+component', after_text, re.IGNORECASE):
                print(f"[DEBUG] Found actual content at position {pos}")
                # Extract large section (200k chars or until next component)
                start_pos = pos
                end_patterns = [
                    r'\n\s*Content\s+of\s+Socio-cultural',
                    r'\n\s*Content\s+for\s+non-exam',
                    r'\n\s*2d\.\s+Content\s+for',
                    r'\n\s*2e\.\s+Content\s+for',
                    r'\n\s*2f\.\s+Prior\s+knowledge',
                    r'\n\s*3\.\s+Assessment',
                ]
                
                end_pos = min(start_pos + 200000, len(self.pdf_text))
                for end_pattern in end_patterns:
                    end_match = re.search(end_pattern, self.pdf_text[start_pos:start_pos + 200000], re.IGNORECASE)
                    if end_match:
                        end_pos = start_pos + end_match.start()
                        print(f"[DEBUG] Found end pattern at position {end_pos}")
                        break
                
                content = self.pdf_text[start_pos:end_pos]
                print(f"[DEBUG] Extracted {len(content)} chars for component")
                return content
        
        # Fallback: use last match if no content found
        if matches:
            print(f"[DEBUG] Using fallback: last match")
            pos = matches[-1].start()
            start_pos = pos
            end_pos = min(start_pos + 200000, len(self.pdf_text))
            return self.pdf_text[start_pos:end_pos]
        
        return None
    
    def _extract_with_ai(self, text: str, parent_code: str, component_name: str) -> Optional[str]:
        """Extract content using AI."""
        # Limit text size
        text = text[:200000]  # 200k chars max
        
        prompt = f"""Extract the complete topic hierarchy from this OCR GCSE Physical Education specification component.

COMPONENT: {component_name}
PARENT CODE: {parent_code}

CRITICAL REQUIREMENTS - READ CAREFULLY:
1. The COMPONENT is already Level 0 - DO NOT include it in your output
2. Start ONLY with Sections (the major divisions within the component)
3. DO NOT create "Physical Education (J587)", component names, or subject names in output
4. Extract from tables with two columns: "Topic area" and "Learners must:"
5. DO NOT prefix topics with "Content:" or "Topic Area:" - use the actual titles directly
6. **CORRECT NUMBERING IS CRITICAL** - Follow the exact format shown below

STRUCTURE REQUIREMENTS:
   Level 1: Sections numbered as "1.", "2.", etc.
   Level 2: Topic Areas numbered as "1.1.", "1.2.", "2.1.", "2.2.", etc. (NOT 1.1.1!)
   Level 3: "Learners must:" items numbered as "1.1.1.", "1.1.2.", "2.1.1.", etc.
   Level 4: Sub-items if "Learners must:" has nested bullets, numbered as "1.1.1.1.", etc.

OUTPUT FORMAT - EXACT NUMBERING REQUIRED:
   
   CORRECT EXAMPLE:
   1. Section 1.1: Applied anatomy and physiology
   1.1. The structure and function of the skeletal system
   1.1.1. know the name and location of the following bones in the human body: cranium, vertebrae, ribs, sternum, clavicle, scapula, pelvis, humerus, ulna, radius, carpals, metacarpals, phalanges, femur, patella, tibia, fibula, tarsals, metatarsals
   1.1.2. understand and be able to apply examples of how the skeleton provides or allows: support, posture, protection, movement, blood cell production, storage of minerals
   1.1.3. know the definition of a synovial joint
   1.2. The structure and function of the muscular system
   1.2.1. know the name and location of the following muscle groups in the human body and be able to apply their use to examples from physical activity/sport: deltoid, trapezius, latissimus dorsi, pectorals, biceps, triceps, abdominals, quadriceps, hamstrings, gluteals, gastrocnemius
   1.3. Movement analysis
   1.3.1. know the three classes of lever and their use in physical activity and sport: 1st class – neck, 2nd class – ankle, 3rd class – elbow
   1.3.2. know the definition of mechanical advantage
   2. Section 1.2: Physical training
   2.1. Components of fitness
   2.1.1. know the definition of cardiovascular endurance/stamina
   2.1.2. be able to apply practical examples where this component is particularly important
   
   WRONG EXAMPLE (DO NOT DO THIS):
   1. Section 1.1: Applied anatomy and physiology
   1.1.1. Topic Area: The structure and function of the skeletal system  <-- WRONG! Should be 1.1.
   1.1.1.1. know the name and location...  <-- WRONG! Should be 1.1.1.
   
   KEY RULES:
   - Sections: Single number (1., 2., 3.)
   - Topic Areas: Two numbers (1.1., 1.2., 2.1.) - NOT three numbers!
   - Learners must items: Three numbers (1.1.1., 1.1.2., 2.1.1.)
   - Sub-items: Four numbers (1.1.1.1., 1.1.1.2.)
   - DO NOT use "Topic Area:" prefix - just the topic name
   - DO NOT use "Content:" prefix
   - Extract ALL content from tables
   - Match "Learners must:" items to their correct Topic Area parent

DO NOT use markdown headers, bullets, or any other format. Use ONLY the numbered format above.

TABLE EXTRACTION GUIDE:
   - Find tables with "Topic area" and "Learners must:" columns
   - Each row in "Topic area" becomes a Level 2 item (numbered 1.1., 1.2., etc.)
   - Each bullet/item in "Learners must:" becomes a Level 3 item under its Topic Area
   - If a bullet has sub-bullets (indicated by indentation or circles), make those Level 4

Extract EVERYTHING from the component - don't skip any sections, topic areas, or learners must items.

CONTENT:
{text}

Extract the complete hierarchy now with CORRECT numbering:"""

        return self._call_ai(prompt, max_tokens=16000)
    
    def _parse_hierarchy(self, text: str, base_code: str) -> List[Dict]:
        """Parse AI numbered output (handles both numbered and markdown formats)."""
        all_topics = []
        parent_stack = {-1: None}
        
        # Filter out subject-level and component-level topics
        excluded_patterns = [
            r'^physical\s+education\s+\(j587\)$',
            r'^physical\s+education$',
            r'^subject:',
            r'^component\s+\d+:',  # Filter "Component 01:" or "Component 02:"
            r'^j587/\d+',  # Filter "J587/01" or "J587/02"
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
                # Remove "Content:" prefix if present
                title = re.sub(r'^Content:\s*', '', title, flags=re.IGNORECASE)
                parts = number_str.split('.')
                level = len(parts)
                
                # Find parent
                parent_level = level - 1
                parent_code = parent_stack.get(parent_level)
                
                # If Level 1 and no parent found, use base_code
                if level == 1 and parent_code is None:
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
                # Remove "Content:" prefix if present
                title = re.sub(r'^Content:\s*', '', title, flags=re.IGNORECASE)
                parts = number_str.split('.')
                level = len(parts)
                
                # Find parent
                parent_level = level - 1
                parent_code = parent_stack.get(parent_level)
                
                # If Level 1 and no parent found, use base_code
                if level == 1 and parent_code is None:
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
                # Remove "Content:" prefix if present
                title = re.sub(r'^Content:\s*', '', title, flags=re.IGNORECASE)
                parts = number_str.split('.')
                level = len(parts)
                
                # Find parent
                parent_level = level - 1
                parent_code = parent_stack.get(parent_level)
                
                # If Level 1 and no parent found, use base_code
                if level == 1 and parent_code is None:
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
    scraper = PhysicalEducationScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)



