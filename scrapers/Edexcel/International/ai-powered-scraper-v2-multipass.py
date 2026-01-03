"""
AI-Powered Scraper V2 - Multi-Pass with Schema
==============================================

UPGRADED APPROACH:
- Schema-first JSON extraction
- Multi-pass: scaffold → section details → merge
- Proper table extraction
- Page-scoped chunks (10-15 pages)
- JSON validation
- Provenance tracking (page numbers)

Usage:
    python ai-powered-scraper-v2-multipass.py --subject IG-Biology
    python ai-powered-scraper-v2-multipass.py --subject IG-Tamil
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
from datetime import datetime
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
    print("[ERROR] Missing credentials in .env!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

try:
    from openai import OpenAI
    import pdfplumber
except ImportError as e:
    print(f"[ERROR] {e}")
    print("Run: pip install openai pdfplumber")
    sys.exit(1)

client = OpenAI(api_key=openai_key)


# OUTPUT SCHEMA
SCHEMA = {
    "meta": {
        "exam_board": "",
        "qualification": "",
        "subject": "",
        "spec_code": "",
        "source_pdf": ""
    },
    "structure": {
        "papers": [
            {
                "paper_code": "",
                "paper_name": "",
                "weighting_percent": None,
                "sections": [
                    {
                        "section_code": "",
                        "section_name": "",
                        "page_span": [0, 0],
                        "topics": [
                            {
                                "title": "",
                                "learning_objectives": [],
                                "examples_or_cases": [],
                                "page_refs": []
                            }
                        ],
                        "subgroups": [
                            {
                                "group_name": "",
                                "page_span": [0, 0],
                                "items": [
                                    {
                                        "title": "",
                                        "learning_objectives": [],
                                        "page_refs": []
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    },
    "appendices": [],
    "warnings": []
}


# PASS-1 PROMPT: Build scaffold
PASS1_PROMPT = """Task: Build ONLY the high-level scaffold for this specification PDF. Identify papers/components, their sections, section descriptions, and page spans. DO NOT extract fine-grained bullets yet.

Guidelines:
- Derive Paper/Section names from headings and overview tables
- Capture page numbers as [start, end] spans for each section
- Detect any per-religion/per-route blocks or language appendices (vocabulary/grammar) and represent them as `subgroups` with their page spans
- Note any tables we should parse later (add to `warnings` with page numbers)

Return JSON following this schema:
{schema}

Context chunks (each begins with ===PAGE n=== and may include table text):
{chunks}"""


# PASS-2 PROMPT: Section details (ENHANCED)
PASS2_PROMPT = """Task: Extract COMPLETE content for this section (learning objectives, named themes, case studies, examples). 
Merge bullets with table rows. Keep concise titles; put explanations into `notes`. Capture page_refs for each item.

Coverage target:
- If tables are present, map EVERY row into an item
- If a cell contains multiple bullets or numbers, split into separate learning_objectives
- Aim for at least 30+ items across topics/subgroups unless the section is genuinely short

Rules:
- Ignore aims/admin/entries/policies. Keep subject content only
- Normalize inconsistent numbering into a clean hierarchy
- If table columns look like [Topic|Content|Guidance|Examples], map to:
  - title = Topic
  - learning_objectives = split Content/Guidance into atomic objectives
  - examples_or_cases = split Examples on separators (;•, newlines)
- For religion- or route-specific rows, use `subgroups[].items`
- Put any ambiguous fragments into `unmapped_fragments` with page_refs

SECTION_META:
{section_meta}

SECTION_PAGES (clean text + any tables converted to pipe-delimited rows):
{section_text}

Return: JSON with only this section filled (same schema shape but scoped to one section)."""


class MultiPassScraper:
    """Multi-pass AI scraper with table extraction."""
    
    def __init__(self, subject_info: Dict):
        self.subject = subject_info
        self.pages = []
        self.scaffold = None
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
    
    def extract_pages_with_tables(self, pdf_bytes: bytes) -> List[Dict]:
        """Extract text + tables from each page."""
        print("\n[INFO] Extracting pages with tables...")
        
        pages = []
        
        try:
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    
                    # Extract tables as pipe-delimited rows
                    table_md = []
                    try:
                        tables = page.extract_tables()
                    except:
                        tables = []
                    
                    for t in tables or []:
                        if not t:
                            continue
                        # Normalize rows
                        max_len = max((len(r) for r in t if r), default=0)
                        norm = []
                        for r in t:
                            r = [(c or "").strip() for c in (r or [])]
                            r += [""] * (max_len - len(r))
                            norm.append(r)
                        # Make pipe format
                        table_md.append("\n".join([" | ".join(r) for r in norm]))
                    
                    pages.append({
                        "page_index": i,
                        "text": text,
                        "tables": table_md
                    })
                    
                    if i % 10 == 0:
                        print(f"[INFO] Page {i+1}/{len(pdf.pages)}...", end='\r')
            
            print(f"\n[OK] Extracted {len(pages)} pages")
            return pages
            
        except Exception as e:
            print(f"[ERROR] Page extraction failed: {str(e)}")
            return []
    
    def build_chunks(self, pages: List[Dict], max_chars: int = 12000) -> List[str]:
        """Build chunks of 10-15 pages each."""
        print("\n[INFO] Building chunks...")
        
        chunks = []
        buf = ""
        
        for p in pages:
            page_header = f"===PAGE {p['page_index']+1}===\n"
            content = p["text"]
            
            # Add tables
            if p["tables"]:
                for ti, tbl in enumerate(p["tables"]):
                    content += f"\n[TABLE {ti+1}]\n{tbl}\n[/TABLE]\n"
            
            entry = page_header + (content or "")
            
            if len(buf) + len(entry) > max_chars and buf:
                chunks.append(buf)
                buf = ""
            
            buf += entry + "\n"
        
        if buf.strip():
            chunks.append(buf)
        
        print(f"[OK] Created {len(chunks)} chunks")
        return chunks
    
    def pass1_scaffold(self, chunks: List[str]) -> Optional[Dict]:
        """Pass 1: Extract high-level structure."""
        print("\n[PASS 1] Building scaffold...")
        
        schema_json = json.dumps(SCHEMA, indent=2)
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Faster/cheaper for scaffold
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "You are a meticulous academic content extractor. Always return strictly valid JSON. No explanations."
                    },
                    {
                        "role": "user",
                        "content": PASS1_PROMPT.format(
                            schema=schema_json,
                            chunks="\n\n".join(chunks)  # USE ALL CHUNKS for full coverage
                        )
                    }
                ],
                max_tokens=8000  # Increased for more sections
            )
            
            scaffold_json = response.choices[0].message.content
            scaffold = json.loads(scaffold_json)
            
            print(f"[OK] Scaffold built - {response.usage.total_tokens} tokens")
            
            # Save for debugging
            debug_file = Path(__file__).parent / "adobe-ai-output" / f"{self.subject['code']}-scaffold.json"
            debug_file.write_text(json.dumps(scaffold, indent=2), encoding='utf-8')
            
            return scaffold
            
        except Exception as e:
            print(f"[ERROR] Pass 1 failed: {str(e)}")
            return None
    
    def pass2_section_details(self, scaffold: Dict, pages: List[Dict]) -> Optional[Dict]:
        """Pass 2: Extract detailed content for each section."""
        print("\n[PASS 2] Extracting section details...")
        
        if not scaffold or 'structure' not in scaffold or 'papers' not in scaffold['structure']:
            print("[ERROR] Invalid scaffold")
            return None
        
        detailed_sections = []
        section_count = 0
        
        for paper in scaffold['structure']['papers']:
            for section in paper.get('sections', []):
                section_count += 1
                page_span = section.get('page_span', [0, 0])
                
                if page_span[0] == 0 or page_span[1] == 0:
                    print(f"[WARNING] Section '{section.get('section_name', 'Unknown')}' has no page span, skipping")
                    continue
                
                # Get pages for this section
                section_text = self.pages_to_text(pages, page_span[0], page_span[1])
                
                section_meta = {
                    "paper_name": paper.get('paper_name', ''),
                    "section_name": section.get('section_name', ''),
                    "page_span": page_span
                }
                
                print(f"[INFO] Section {section_count}: {section_meta['section_name']} (pages {page_span[0]}-{page_span[1]})...")
                
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",  # Full power for details
                        temperature=0,
                        response_format={"type": "json_object"},
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a meticulous academic content extractor. Always return valid JSON. No explanations."
                            },
                            {
                                "role": "user",
                                "content": PASS2_PROMPT.format(
                                    section_meta=json.dumps(section_meta),
                                    section_text=section_text[:120000]  # Cap
                                )
                            }
                        ],
                        max_tokens=8000
                    )
                    
                    section_json = json.loads(response.choices[0].message.content)
                    detailed_sections.append({
                        'section_meta': section_meta,
                        'section_data': section_json,
                        'tokens': response.usage.total_tokens
                    })
                    
                    print(f"[OK] Extracted {response.usage.total_tokens} tokens")
                    
                except Exception as e:
                    print(f"[WARNING] Section failed: {str(e)}")
        
        print(f"[OK] Extracted {len(detailed_sections)} sections")
        return detailed_sections
    
    def pages_to_text(self, pages: List[Dict], start: int, end: int, per_page_cap: int = 8000) -> str:
        """Convert page range to text with tables."""
        segs = []
        
        for i in range(start-1, end):  # 1-based to 0-based
            if i < 0 or i >= len(pages):
                continue
            
            body = pages[i]["text"] or ""
            tbls = "\n".join([f"[TABLE]\n{t}\n[/TABLE]" for t in pages[i]["tables"]])
            page_blob = f"===PAGE {i+1}===\n{body}\n{tbls}\n"
            segs.append(page_blob[:per_page_cap])
        
        return "\n".join(segs)[:120000]  # Hard cap
    
    def convert_to_flat_hierarchy(self, structured_data: Dict) -> List[Dict]:
        """Convert JSON structure to flat topic list for Supabase."""
        print("\n[INFO] Converting to flat hierarchy...")
        
        topics = []
        topic_counter = {'current': 0}
        
        def add_topic(title: str, level: int, parent_code: Optional[str], 
                     learning_objectives: List = None, page_refs: List = None) -> str:
            """Add topic and return its code."""
            topic_counter['current'] += 1
            code = f"T{topic_counter['current']}"
            
            # Build full title with LOs if present
            full_title = title
            if learning_objectives and len(learning_objectives) > 0:
                # Keep title clean, store LOs separately (we'll add to notes)
                pass
            
            topics.append({
                'code': code,
                'title': full_title[:500],  # Cap length
                'level': level,
                'parent': parent_code,
                'page_refs': page_refs or []
            })
            
            return code
        
        structure = structured_data.get('structure', {})
        papers = structure.get('papers', [])
        
        for paper_idx, paper in enumerate(papers):
            # Paper (Level 0)
            paper_code = add_topic(
                paper.get('paper_name', f"Paper {paper_idx+1}"),
                level=0,
                parent_code=None
            )
            
            sections = paper.get('sections', [])
            for section in sections:
                # Section (Level 1)
                section_code = add_topic(
                    section.get('section_name', 'Section'),
                    level=1,
                    parent_code=paper_code,
                    page_refs=section.get('page_span', [])
                )
                
                # Topics (Level 2)
                for topic in section.get('topics', []):
                    topic_code = add_topic(
                        topic.get('title', ''),
                        level=2,
                        parent_code=section_code,
                        learning_objectives=topic.get('learning_objectives', []),
                        page_refs=topic.get('page_refs', [])
                    )
                    
                    # Add LOs as Level 3
                    for lo in topic.get('learning_objectives', [])[:30]:  # Increased cap
                        if lo and len(lo) > 3:
                            add_topic(lo, level=3, parent_code=topic_code)
                    
                    # Add examples as Level 3
                    for ex in topic.get('examples_or_cases', [])[:20]:
                        if ex and len(ex) > 3:
                            add_topic(f"Example: {ex}", level=3, parent_code=topic_code)
                
                # Subgroups (e.g., per-religion, per-language)
                for subgroup in section.get('subgroups', []):
                    # Subgroup header (Level 2)
                    subgroup_code = add_topic(
                        subgroup.get('group_name', 'Subgroup'),
                        level=2,
                        parent_code=section_code,
                        page_refs=subgroup.get('page_span', [])
                    )
                    
                    # Subgroup items (Level 3)
                    for item in subgroup.get('items', []):
                        item_code = add_topic(
                            item.get('title', ''),
                            level=3,
                            parent_code=subgroup_code,
                            page_refs=item.get('page_refs', [])
                        )
                        
                        # Item LOs (Level 4)
                        for lo in item.get('learning_objectives', [])[:20]:  # Increased
                            if lo and len(lo) > 3:
                                add_topic(lo, level=4, parent_code=item_code)
                        
                        # Item examples (Level 4)
                        for ex in item.get('examples_or_cases', [])[:10]:
                            if ex and len(ex) > 3:
                                add_topic(ex, level=4, parent_code=item_code)
        
        # Appendices
        for appendix in structured_data.get('appendices', []):
            append_code = add_topic(
                appendix.get('name', 'Appendix'),
                level=0,
                parent_code=None,
                page_refs=appendix.get('page_span', [])
            )
            
            # Appendix items
            for item in appendix.get('items', [])[:50]:  # Cap
                if isinstance(item, str) and len(item) > 3:
                    add_topic(item, level=1, parent_code=append_code)
        
        print(f"[OK] Converted to {len(topics)} flat topics")
        return topics
    
    def upload_to_supabase(self, topics: List[Dict]) -> bool:
        """Upload to Supabase."""
        print("\n[INFO] Uploading to Supabase...")
        
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
        """Multi-pass scraping workflow."""
        print("\n" + "="*60)
        print(f"MULTI-PASS AI SCRAPING: {self.subject['name']}")
        print("="*60)
        
        # Download
        pdf_bytes = self.download_pdf()
        if not pdf_bytes:
            return False
        
        # Extract pages with tables
        self.pages = self.extract_pages_with_tables(pdf_bytes)
        if not self.pages:
            return False
        
        # Build chunks
        chunks = self.build_chunks(self.pages)
        
        # Pass 1: Scaffold
        self.scaffold = self.pass1_scaffold(chunks)
        if not self.scaffold:
            return False
        
        # Pass 2: Section details (ACTUALLY RUN IT!)
        sections = self.pass2_section_details(self.scaffold, self.pages)
        if not sections:
            print("[WARNING] No section details extracted, using scaffold only")
            final_struct = self.scaffold
        else:
            # Merge section JSONs into final structure
            final_struct = self.scaffold.copy()
            final_struct['structure']['papers'] = []
            paper_map = {}
            
            for s in sections:
                if 'structure' not in s['section_data'] or 'papers' not in s['section_data']['structure']:
                    continue
                if len(s['section_data']['structure']['papers']) == 0:
                    continue
                    
                sec_data = s['section_data']['structure']['papers'][0]['sections'][0]
                paper_name = s['section_meta']['paper_name']
                
                if paper_name not in paper_map:
                    paper_map[paper_name] = {
                        "paper_code": "",
                        "paper_name": paper_name,
                        "weighting_percent": None,
                        "sections": []
                    }
                    final_struct['structure']['papers'].append(paper_map[paper_name])
                
                paper_map[paper_name]['sections'].append(sec_data)
            
            print(f"[OK] Merged {len(sections)} sections into final structure")
        
        # Convert to flat hierarchy (from FINAL structure, not scaffold!)
        self.topics = self.convert_to_flat_hierarchy(final_struct)
        if not self.topics:
            return False
        
        # Sanity check
        if len(self.topics) < 50:
            print(f"[WARNING] Low topic count ({len(self.topics)}). Might need refinement.")
        
        # Upload
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
    
    else:
        parser.print_help()
        sys.exit(1)
    
    print(f"\n[INFO] Scraping {len(subjects_to_scrape)} subjects with Multi-Pass AI")
    
    results = {'success': 0, 'failed': 0}
    
    for subject in subjects_to_scrape:
        scraper = MultiPassScraper(subject)
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

