"""
OCR GCSE Food Preparation and Nutrition (J309) Manual Scraper
==============================================================

Extracts topics from OCR GCSE Food Preparation and Nutrition J309 specification.

Structure:
- Level 0: The 4 Sections (Section A: Nutrition, Section B: Food, Section C: Cooking and food preparation, Section D: Skills requirements)
- Level 1: Bulleted topics under each section (e.g., "The relationship between diet and health", "Protein", "Fat", etc.)
- Level 2+: Detailed content from the specification (learning outcomes, sub-topics, etc.)

CRITICAL: 
- DO NOT create "Food Preparation and Nutrition (J309)" as Level 0 - start with Sections
- DO NOT extract "Why choose OCR", "Assessment", "Admin", "Appendices" sections
- Extract ONLY the 4 content sections (A, B, C, D) and their detailed content
- Extract ALL depth from each section (Level 2, 3, 4+)

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-food-preparation-nutrition-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/234806-specification-accredited-gcse-food-preparation-and-nutrition-j309.pdf'
SUBJECT_CODE = 'J309'
SUBJECT_NAME = 'Food Preparation and Nutrition'

SECTIONS = [
    {
        'code': 'A',
        'name': 'Section A: Nutrition',
        'section_pattern': r'Content\s+of\s+Section\s+A:\s+Nutrition',
    },
    {
        'code': 'B',
        'name': 'Section B: Food (food provenance and food choice)',
        'section_pattern': r'Content\s+of\s+Section\s+B:\s+Food',
    },
    {
        'code': 'C',
        'name': 'Section C: Cooking and food preparation',
        'section_pattern': r'Content\s+of\s+Section\s+C:\s+Cooking',
    },
    {
        'code': 'D',
        'name': 'Section D: Skills requirements (preparation and cooking techniques)',
        'section_pattern': r'Content\s+of\s+Section\s+D:\s+Skills',
    },
]


class FoodPreparationNutritionScraper:
    """Scraper for OCR GCSE Food Preparation and Nutrition."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent.parent / "A-Level" / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_text = None
    
    def scrape_all(self):
        """Scrape all topics."""
        print("\n" + "🍎 "*40)
        print("OCR GCSE FOOD PREPARATION AND NUTRITION SCRAPER")
        print("🍎 "*40)
        
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
        
        # Extract each section
        all_topics = []
        
        for section in SECTIONS:
            print("\n" + "="*80)
            print(f"[EXTRACTING] {section['name']}")
            print("="*80)
            
            # Find section content
            section_text = self._find_section_content(section)
            if not section_text:
                print(f"[WARN] Could not find section for {section['name']}")
                continue
            
            print(f"[OK] Found section: {len(section_text)} chars")
            
            # Level 0: Section
            section_code = f"{SUBJECT_CODE}_{section['code']}"
            section_topic = {
                'code': section_code,
                'title': section['name'],
                'level': 0,
                'parent': None
            }
            all_topics.append(section_topic)
            
            # Extract content using AI
            print(f"[INFO] Extracting section content...")
            ai_output = self._extract_with_ai(section_text, section_code, section['name'])
            
            if ai_output:
                # Save AI output for debugging
                debug_file = self.debug_dir / f"{SUBJECT_CODE}-{section['code']}-ai-output.txt"
                debug_file.write_text(ai_output, encoding='utf-8')
                print(f"[DEBUG] Saved AI output to {debug_file.name}")
                
                parsed = self._parse_hierarchy(ai_output, section_code)
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
    
    def _find_section_content(self, section: Dict) -> Optional[str]:
        """Find section content."""
        # Look for the section pattern
        pattern = section['section_pattern']
        matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE))
        
        if not matches:
            print(f"[WARN] Could not find section pattern: {pattern}")
            return None
        
        # Find actual content (not TOC entry)
        content_start = None
        for match in matches:
            pos = match.start()
            after_text = self.pdf_text[pos:pos + 3000]
            before_text = self.pdf_text[max(0, pos - 200):pos]
            
            # Check if TOC entry (has page number immediately after)
            # TOC format: "Content of Section X: Title 9" (page number at end)
            if re.search(r'\d+\s*$', before_text[-50:]) or re.search(r'Content\s+of\s+Section\s+[A-D]:[^\n]+\d+\s*$', before_text[-100:]):
                print(f"[DEBUG] Skipping TOC entry at position {pos}")
                continue
            
            # Check if actual content (has descriptive text or table structure)
            if re.search(r'Learners\s+should|Topic|Points\s+to\s+cover|demonstrate|apply|table|The\s+relationship', after_text, re.IGNORECASE):
                content_start = pos
                print(f"[DEBUG] Found actual content at position {pos}")
                break
        
        if not content_start:
            # Fallback: use last match
            if matches:
                content_start = matches[-1].start()
                print(f"[DEBUG] Using fallback: last match")
            else:
                return None
        
        # Extract section (next 200000 chars or until next section)
        start_pos = content_start
        end_patterns = [
            r'\n\s*Content\s+of\s+Section\s+B:',  # Next section
            r'\n\s*Content\s+of\s+Section\s+C:',  # Next section
            r'\n\s*Content\s+of\s+Section\s+D:',  # Next section
            r'\n\s*Content\s+of\s+Section\s+E:',  # Next section (if exists)
            r'\n\s*Content\s+of\s+non-examined',  # NEA section
            r'\n\s*3\.\s+Assessment',  # Assessment section
            r'\n\s*2c\.\s+Content\s+of\s+non-examined',  # NEA section (alternative format)
        ]
        
        end_pos = min(start_pos + 200000, len(self.pdf_text))
        for pattern in end_patterns:
            end_match = re.search(pattern, self.pdf_text[start_pos:start_pos + 200000], re.IGNORECASE)
            if end_match:
                end_pos = start_pos + end_match.start()
                break
        
        section_text = self.pdf_text[start_pos:end_pos]
        
        # Save snippet for debugging
        snippet_file = self.debug_dir / f"{SUBJECT_CODE}-{section['code']}-section.txt"
        snippet_file.write_text(section_text[:10000], encoding='utf-8')
        print(f"[DEBUG] Saved section snippet ({len(section_text)} chars)")
        
        return section_text
    
    def _extract_with_ai(self, text: str, parent_code: str, section_name: str) -> Optional[str]:
        """Extract content using AI."""
        # Limit text size
        text = text[:200000]  # 200k chars max
        
        prompt = f"""Extract the complete topic hierarchy from this OCR GCSE Food Preparation and Nutrition specification section.

SECTION: {section_name}
PARENT CODE: {parent_code}

CRITICAL REQUIREMENTS:
1. DO NOT create "Food Preparation and Nutrition (J309)" or subject name as Level 0 - sections are already Level 0
2. DO NOT extract "Why choose OCR", "Assessment", "Admin", "Appendices", "NEA", or any non-content sections
3. Extract ONLY the actual content topics from this section

4. STRUCTURE REQUIREMENTS:
   Level 1: Main topics from the bulleted list (e.g., "The relationship between diet and health", "Protein", "Fat", "Carbohydrate", "Vitamins", "Minerals", "Water", "Nutritional content of the main commodity groups" for Section A)
   Level 2: Sub-topics and learning outcomes under each Level 1 topic
   Level 3: Detailed points, examples, and specific content items
   Level 4: Further detail, specific examples, or sub-items

5. OUTPUT FORMAT: Numbered hierarchy (NOT markdown)
   CRITICAL: Use numbered format ONLY, NOT markdown headers (### or ####)
   CRITICAL: You MUST include Level 1 topics first, then extract ALL depth below them
   
   Format:
   1. Level 1 Topic (e.g., "The relationship between diet and health")
   1.1. Level 2 Sub-topic or learning outcome
   1.1.1. Level 3 Detail or point
   1.1.1.1. Level 4 Specific example or sub-item
   1.2. Level 2 Sub-topic or learning outcome
   1.2.1. Level 3 Detail or point
   2. Level 1 Topic (e.g., "Protein")
   2.1. Level 2 Sub-topic or learning outcome
   (continue for ALL topics with FULL depth)
   
   IMPORTANT: 
   - ALWAYS include Level 1 topics (main bulleted topics)
   - THEN extract ALL depth (Level 2, 3, 4+) from the detailed content
   - Extract learning outcomes, "Learners should be able to" items, "Points to cover", etc.
   - Don't skip any levels or content!
   
   DO NOT use:
   - ### or #### headers
   - Bullet points with dashes
   - Markdown formatting
   
   USE ONLY:
   - Numbered format: "1.", "1.1.", "1.1.1.", "1.1.1.1.", etc.

6. DEPTH REQUIREMENTS:
   - Extract ALL learning outcomes, "Learners should be able to" items, "Points to cover"
   - Extract ALL sub-topics, examples, and detailed content
   - Create Level 2, 3, 4+ items for comprehensive coverage
   - Ensure you extract the full depth from tables and detailed descriptions

7. FILTERING:
   - DO NOT extract section headers like "Content of Section A: Nutrition" as topics
   - DO NOT extract "Topic", "Learners should be able to", "Points to cover" as topic titles
   - Extract the actual content, not the column headers

8. DO NOT ask for confirmation. Extract EVERYTHING NOW.

CONTENT:
{text}

Extract the complete hierarchy now:"""

        return self._call_ai(prompt, max_tokens=16000)
    
    def _parse_hierarchy(self, text: str, base_code: str) -> List[Dict]:
        """Parse AI numbered output (handles both numbered and markdown formats)."""
        all_topics = []
        parent_stack = {-1: None}
        
        # Filter out subject-level topics and section markers
        excluded_patterns = [
            r'^food\s+preparation\s+and\s+nutrition\s+\(j309\)$',
            r'^food\s+preparation\s+and\s+nutrition$',
            r'^content\s+of\s+section\s+[a-d]:',
            r'^section\s+[a-d]:',
            r'^why\s+choose',
            r'^assessment',
            r'^admin',
            r'^appendices',
            r'^nea',
            r'^non-examined',
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
                level = len(parts)  # 3.1 = Level 2, 3 = Level 1
                
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
                parts = number_str.split('.')
                level = len(parts)  # 1.1.1 = Level 3
                
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
    scraper = FoodPreparationNutritionScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)

