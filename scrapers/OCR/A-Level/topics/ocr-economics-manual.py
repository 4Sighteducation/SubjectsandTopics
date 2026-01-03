"""
OCR A-Level Economics Manual Structure Scraper
===============================================

Extracts topics from OCR Economics H460 specification.

Structure:
- Level 0: Components (Component 1 & 2)
- Level 1: Main topic areas
- Level 2: Numbered topics (1.1, 1.2, etc.)
- Level 3: Learning outcome bullet points

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-economics-manual.py
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

PDF_URL = 'https://www.ocr.org.uk/Images/536455-specification-accredited-a-level-gce-economics-h460.pdf'

# 2 components (skip Component 3 - synoptic)
COMPONENTS = [
    {
        'name': 'Microeconomics',
        'code': 'H460_01',
        'full_name': 'Component 1: Microeconomics',
        'section_pattern': r'2c\.\s+Content of Component 1: Microeconomics',
        'topic_areas': [
            'Introduction to microeconomics',
            'The role of markets',
            'Business objectives',
            'Market structures',
            'The labour market'
        ]
    },
    {
        'name': 'Macroeconomics',
        'code': 'H460_02',
        'full_name': 'Component 2: Macroeconomics',
        'section_pattern': r'2d\.\s+Content of Component 2: Macroeconomics',
        'topic_areas': [
            'Aggregate demand and aggregate supply',
            'Economic policy objectives',
            'Implementing policy',
            'The global context',
            'The financial sector'
        ]
    }
]


class EconomicsScraper:
    """Scraper for OCR A-Level Economics."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.pdf_text = None
    
    def scrape_all(self):
        """Scrape both components."""
        print("\n" + "📊 "*40)
        print("OCR ECONOMICS SCRAPER")
        print("📊 "*40)
        
        # Download PDF
        print("\n[INFO] Downloading PDF...")
        try:
            response = requests.get(PDF_URL, timeout=60)
            response.raise_for_status()
            pdf_content = response.content
            print(f"[OK] Downloaded {len(pdf_content)/1024/1024:.1f} MB")
        except Exception as e:
            print(f"[ERROR] PDF download failed: {e}")
            return False
        
        # Extract PDF text
        self.pdf_text = self._extract_pdf_text(pdf_content)
        if not self.pdf_text:
            return False
        
        # Clear old topics ONCE before processing any components
        print("\n[INFO] Clearing old Economics topics...")
        try:
            subject_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', 'H460').eq('qualification_type', 'A-Level').eq('exam_board', 'OCR').execute()
            if subject_result.data:
                subject_id = subject_result.data[0]['id']
                supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
                print(f"[OK] Cleared old topics for H460")
        except Exception as e:
            print(f"[WARN] Could not clear old topics: {e}")
        
        # Process each component
        success_count = 0
        for component in COMPONENTS:
            print("\n" + "="*80)
            print(f"Processing: {component['full_name']} ({component['code']})")
            print("="*80)
            
            if self._process_component(component):
                success_count += 1
            time.sleep(2)
        
        print("\n" + "="*80)
        print(f"✅ Completed: {success_count}/{len(COMPONENTS)} components successful")
        print("="*80)
        return success_count == len(COMPONENTS)
    
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
            return text
        except Exception as e:
            print(f"[ERROR] PDF extraction failed: {e}")
            return None
    
    def _process_component(self, component: Dict) -> bool:
        """Process one component."""
        
        # Find the section in PDF
        section_text = self._find_section(component)
        if not section_text:
            print(f"[WARN] Could not find section for {component['code']}")
            return False
        
        print(f"[DEBUG] Found section: {len(section_text)} chars")
        
        # Extract topics with AI
        topics = self._extract_topics(component, section_text)
        if not topics:
            print(f"[WARN] No topics extracted for {component['code']}")
            return False
        
        # Count by level
        level_counts = {}
        for t in topics:
            level_counts[t['level']] = level_counts.get(t['level'], 0) + 1
        level_str = ", ".join([f"L{k}:{v}" for k, v in sorted(level_counts.items())])
        print(f"[OK] Extracted {len(topics)} topics ({level_str})")
        
        # Upload
        return self._upload_component(component, topics)
    
    def _find_section(self, component: Dict) -> Optional[str]:
        """Find the section for this component in the PDF."""
        
        pattern = component['section_pattern']
        matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE))
        
        if not matches:
            return None
        
        # Take the longest match (main content, not TOC)
        best_section = None
        best_length = 0
        
        for match in matches:
            start = match.start()
            # Find end: next section (2d, 2e) or version marker
            end_patterns = [r'\n2[de]\.\s+Content of Component', r'\n2[ef]\.\s+', r'\nVersion \d+\.\d+']
            end_pos = len(self.pdf_text)
            for ep in end_patterns:
                end_match = re.search(ep, self.pdf_text[start+1000:start+50000])
                if end_match:
                    end_pos = start + 1000 + end_match.start()
                    break
            
            section = self.pdf_text[start:end_pos]
            if len(section) > best_length:
                best_length = len(section)
                best_section = section
        
        return best_section if best_length > 2000 else None
    
    def _extract_topics(self, component: Dict, section_text: str) -> List[Dict]:
        """Extract topics using AI."""
        
        topic_areas_str = "\n".join([f"- {area}" for area in component['topic_areas']])
        
        prompt = f"""Extract the complete hierarchy from this OCR Economics specification section.

COMPONENT: {component['full_name']} ({component['code']})

STRUCTURE (4 levels):
- Level 0: Component name (just one: "{component['name']}")
- Level 1: Main topic areas (5 total):
{topic_areas_str}
- Level 2: Numbered topics from the "Topic" column (e.g., "1.1 The economic problem")
- Level 3: Bullet points from "Students should be able to:" column

CRITICAL FILTERING RULES:
1. SKIP "Explain:" and "Evaluate:" headers - these are just section labels
2. ONLY extract the actual bullet points under "Students should be able to:"
3. Filter out any standalone words like "Explain:" or "Evaluate:"

OUTPUT FORMAT:
1. {component['name']}
1.1 Introduction to microeconomics
1.1.1 1.1 The economic problem
1.1.1.1 Economic goods and free goods
1.1.1.2 The economic problem: scarcity, choice, needs, and wants
1.1.1.3 Normative and positive statements
1.1.1.4 The role of economic agents: government, firms, and households
1.1.2 1.2 The allocation of resources
1.1.2.1 Incentives
1.1.2.2 Market, planned and mixed economic systems
1.2 The role of markets
1.2.1 2.1 Rational decision making
(continue...)

IMPORTANT:
- Start with "1. {component['name']}" (Level 0)
- List all 5 topic areas as 1.1, 1.2, 1.3, 1.4, 1.5 (Level 1)
- Under each, extract numbered topics like "1.1 The economic problem" (Level 2)
- Under each numbered topic, extract bullet points (Level 3)
- DO NOT include "Explain:" or "Evaluate:" as topics

SECTION TEXT:
{section_text[:50000]}"""
        
        try:
            if AI_PROVIDER == "openai":
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=16000,
                    temperature=0
                )
                ai_output = response.choices[0].message.content
            else:
                response = claude.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=16000,
                    messages=[{"role": "user", "content": prompt}]
                )
                ai_output = response.content[0].text
            
            # Save AI output
            safe_code = re.sub(r'[^\w\-]', '_', component['code'])
            ai_file = self.debug_dir / f"{safe_code}-ai-output.txt"
            ai_file.write_text(ai_output, encoding='utf-8')
            print(f"[DEBUG] Saved AI output to {ai_file.name}")
            
            return self._parse_hierarchy(ai_output, component['code'])
        except Exception as e:
            print(f"[ERROR] AI extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_hierarchy(self, text: str, component_code: str) -> List[Dict]:
        """Parse AI numbered output."""
        all_topics = []
        parent_stack = {-1: None}
        
        # Headers to exclude
        EXCLUDED_HEADERS = ['explain:', 'explain', 'evaluate:', 'evaluate']
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            match = re.match(r'^([\d.]+)[\.\):]?\s+(.+)$', line)
            if not match:
                continue
            
            number = match.group(1).rstrip('.')
            title = match.group(2).strip()
            
            # Skip short titles
            if len(title) < 3:
                continue
            
            # Filter out "Explain:" and "Evaluate:" headers
            if title.lower() in EXCLUDED_HEADERS:
                print(f"[DEBUG] Skipped: {title}")
                continue
            
            dots = number.count('.')
            level = dots
            code = f"{component_code}_{number.replace('.', '_')}"
            parent_code = parent_stack.get(level - 1)
            
            all_topics.append({
                'code': code,
                'title': title,
                'level': level,
                'parent': parent_code
            })
            
            parent_stack[level] = code
            for l in list(parent_stack.keys()):
                if l > level:
                    del parent_stack[l]
        
        return all_topics
    
    def _upload_component(self, component: Dict, topics: List[Dict]) -> bool:
        """Upload one component to Supabase."""
        
        try:
            # Upsert subject (ONE subject for all components)
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': "Economics (A-Level)",
                'subject_code': 'H460',
                'qualification_type': 'A-Level',
                'specification_url': PDF_URL,
                'exam_board': 'OCR'
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            subject_id = subject_result.data[0]['id']
            print(f"[OK] Subject ID: {subject_id}")
            
            # Insert topics (don't delete - already cleared at start)
            to_insert = [{
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': t['title'],
                'topic_level': t['level'],
                'exam_board': 'OCR'
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
            return True
            
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            return False


def main():
    scraper = EconomicsScraper()
    success = scraper.scrape_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

