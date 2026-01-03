"""
OCR GCSE Mathematics (J560) Manual Scraper
==========================================

Extracts topics from OCR GCSE Mathematics J560 specification.

Structure:
- Level 0: Tiers (Foundation tier, Higher tier)
- Level 1: Topic areas (e.g., "Number operations and integers", "Fractions, decimals and percentages")
- Level 2: Sub-topics (e.g., "Calculations with integers", "Whole number theory")
- Level 3: Specific content items (e.g., "Four rules", "Definitions and terms", "Prime numbers")
- Level 4: Learning objectives from table columns (Initial learning, Foundation tier, Higher tier)

CRITICAL: 
- DO NOT create "Mathematics (J560)" as Level 0 - start with Tiers
- Foundation tier: Gets Initial learning + Foundation tier column content
- Higher tier: Gets Initial learning + Foundation tier + Higher tier column content (all three columns)
- Extract ALL content from the table structure with reference codes (e.g., 1.01, 1.01a, 1.02a, 1.02b)
- Extract learning objectives from all three columns as Level 4 items

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-mathematics-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/168982-specification-gcse-mathematics.pdf'
SUBJECT_CODE = 'J560'
SUBJECT_NAME = 'Mathematics'

TIERS = [
    {
        'code': 'F',
        'name': 'Foundation tier',
        'section_pattern': r'Foundation\s+tier|Content\s+of\s+GCSE.*Mathematics',
    },
    {
        'code': 'H',
        'name': 'Higher tier',
        'section_pattern': r'Higher\s+tier|Content\s+of\s+GCSE.*Mathematics',
    },
]


class MathematicsScraper:
    """Scraper for OCR GCSE Mathematics."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent.parent / "A-Level" / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_text = None
    
    def scrape_all(self):
        """Scrape all topics."""
        print("\n" + "🔢 "*40)
        print("OCR GCSE MATHEMATICS SCRAPER")
        print("🔢 "*40)
        
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
        
        # Find content section
        content_section = self._find_content_section()
        if not content_section:
            print("[ERROR] Could not find content section")
            return False
        
        print(f"[OK] Found content section: {len(content_section)} chars")
        
        # Extract topics for both tiers
        all_topics = []
        
        for tier in TIERS:
            print("\n" + "="*80)
            print(f"[EXTRACTING] {tier['name']}")
            print("="*80)
            
            # Level 0: Tier
            tier_code = f"{SUBJECT_CODE}_{tier['code']}"
            tier_topic = {
                'code': tier_code,
                'title': tier['name'],
                'level': 0,
                'parent': None
            }
            all_topics.append(tier_topic)
            
            # Extract content using AI
            print(f"[INFO] Extracting tier content...")
            ai_output = self._extract_with_ai(content_section, tier_code, tier['name'], tier['code'])
            
            if ai_output:
                # Save AI output for debugging
                debug_file = self.debug_dir / f"{SUBJECT_CODE}-{tier['code']}-ai-output.txt"
                debug_file.write_text(ai_output, encoding='utf-8')
                print(f"[DEBUG] Saved AI output to {debug_file.name}")
                
                parsed = self._parse_hierarchy(ai_output, tier_code)
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
    
    def _find_content_section(self) -> Optional[str]:
        """Find the main content section."""
        # Look for "Content of GCSE (9-1) in Mathematics" or table structure
        patterns = [
            r'Content\s+of\s+GCSE\s+\(9[–-]1\)\s+in\s+Mathematics\s+\(J560\)',
            r'Number\s+operations\s+and\s+integers',
            r'GCSE\s+\(9[–-]1\)\s+content\s+Ref\.',
        ]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE))
            if matches:
                # Find actual content (not TOC entry)
                for match in matches:
                    pos = match.start()
                    after_text = self.pdf_text[pos:pos + 2000]
                    before_text = self.pdf_text[max(0, pos - 200):pos]
                    
                    # Check if TOC entry
                    if re.search(r'\d+\s*$', before_text[-50:]):
                        continue
                    
                    # Check if actual content (has table structure or reference codes)
                    if re.search(r'GCSE\s+\(9[–-]1\)\s+content\s+Ref\.|1\.01|Subject\s+content|Initial\s+learning', after_text, re.IGNORECASE):
                        # Extract large section (500k chars or until end of content)
                        start_pos = pos
                        end_patterns = [
                            r'\n\s*6\.\s+Formulae',
                            r'\n\s*2d\.\s+Prior\s+knowledge',
                            r'\n\s*3\.\s+Assessment',
                            r'\n\s*Appendix',
                        ]
                        
                        end_pos = min(start_pos + 500000, len(self.pdf_text))
                        for end_pattern in end_patterns:
                            end_match = re.search(end_pattern, self.pdf_text[start_pos:start_pos + 500000], re.IGNORECASE)
                            if end_match:
                                end_pos = start_pos + end_match.start()
                                break
                        
                        return self.pdf_text[start_pos:end_pos]
        
        return None
    
    def _extract_with_ai(self, text: str, parent_code: str, tier_name: str, tier_code: str) -> Optional[str]:
        """Extract content using AI."""
        # Limit text size
        text = text[:200000]  # 200k chars max
        
        tier_instruction = ""
        if tier_code == 'F':
            tier_instruction = """
   Foundation tier: Extract content from:
   - "Initial learning for this qualification will enable learners to..." column
   - "Foundation tier learners should also be able to..." column
   DO NOT extract "Higher tier learners should additionally be able to..." column content"""
        else:  # Higher tier
            tier_instruction = """
   Higher tier: Extract content from ALL THREE columns:
   - "Initial learning for this qualification will enable learners to..." column
   - "Foundation tier learners should also be able to..." column
   - "Higher tier learners should additionally be able to..." column
   Higher tier includes everything from Foundation tier PLUS additional Higher tier content"""
        
        prompt = f"""Extract the complete topic hierarchy from this OCR GCSE Mathematics specification.

TIER: {tier_name}
PARENT CODE: {parent_code}

CRITICAL REQUIREMENTS:
1. DO NOT create "Mathematics (J560)" or subject name as Level 0 - tiers are already Level 0
2. Extract from the table structure with columns:
   - "GCSE (9-1) content Ref." (e.g., 1.01, 1.01a, 1.02a, 1.02b)
   - "Subject content" (e.g., "Calculations with integers", "Four rules", "Definitions and terms")
   - "Initial learning for this qualification will enable learners to..."
   - "Foundation tier learners should also be able to..."
   - "Higher tier learners should additionally be able to..."
{tier_instruction}

3. STRUCTURE REQUIREMENTS:
   Level 1: Topic areas (e.g., "Number operations and integers", "Fractions, decimals and percentages", "Algebra", "Basic geometry")
   Level 2: Sub-topics from "Subject content" column (e.g., "Calculations with integers", "Whole number theory", "Fractions")
   Level 3: Specific content items from "Subject content" column (e.g., "Four rules", "Definitions and terms", "Prime numbers")
   Level 4: Learning objectives from the appropriate columns:
     * Extract ALL learning objectives from the columns specified above
     * Each distinct learning objective becomes a Level 4 item
     * If a learning objective has multiple sentences or bullet points, split them into separate Level 4 items
     * Match each Level 4 item to its correct Level 3 parent based on the reference code

4. OUTPUT FORMAT: Numbered hierarchy (NOT markdown)
   CRITICAL: Use numbered format ONLY, NOT markdown headers (### or ####)
   CRITICAL: Extract EVERYTHING - don't skip any content!
   
   Format:
   1. Level 1 Topic Area (e.g., "Number operations and integers")
   1.1. Level 2 Sub-topic (e.g., "Calculations with integers")
   1.1.1. Level 3 Content Item (e.g., "Four rules")
   1.1.1.1. Level 4 Learning Objective (from Initial learning column)
   1.1.1.2. Level 4 Learning Objective (from Foundation/Higher tier column)
   1.1.2. Level 3 Content Item (e.g., next item from Subject content)
   1.1.2.1. Level 4 Learning Objective
   1.2. Level 2 Sub-topic (e.g., "Whole number theory")
   1.2.1. Level 3 Content Item (e.g., "Definitions and terms")
   1.2.1.1. Level 4 Learning Objective
   1.2.2. Level 3 Content Item (e.g., "Prime numbers")
   1.2.2.1. Level 4 Learning Objective (from Initial learning)
   1.2.2.2. Level 4 Learning Objective (from Foundation/Higher tier)
   (continue for ALL topics with FULL depth)
   
   IMPORTANT: 
   - Extract ALL topic areas, sub-topics, and content items
   - Extract ALL learning objectives from the appropriate columns
   - Match learning objectives to their correct content items using reference codes
   - Don't skip any levels or content!
   
   DO NOT use:
   - ### or #### headers
   - Bullet points with dashes
   - Markdown formatting
   
   USE ONLY:
   - Numbered format: "1.", "1.1.", "1.1.1.", "1.1.1.1.", etc.

5. REFERENCE CODE MATCHING:
   - Use reference codes (e.g., 1.01, 1.01a, 1.02a) to match learning objectives to content items
   - Reference codes show the hierarchy: 1.01 = Level 2, 1.01a = Level 3
   - Learning objectives under reference code 1.01a belong to that Level 3 content item

6. LEARNING OBJECTIVES EXTRACTION:
   - Extract EVERY learning objective from the appropriate columns
   - Split multiple sentences or bullet points into separate Level 4 items
   - Examples of Level 4 items:
     * "Use non-calculator methods to calculate the sum, difference, product and quotient of positive and negative whole numbers."
     * "Identify prime numbers less than 20."
     * "Express a whole number as a product of its prime factors."

7. DO NOT ask for confirmation. Extract EVERYTHING NOW.

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
            r'^mathematics\s+\(j560\)$',
            r'^mathematics$',
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
                level = len(parts)  # Level 1, 2, 3, 4
                
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
    scraper = MathematicsScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)



