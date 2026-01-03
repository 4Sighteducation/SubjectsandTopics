"""
OCR GCSE Universal Scraper
==========================

A smart, universal scraper for ALL OCR GCSE courses that:
1. Analyzes PDF structure first (Content Overview, tiers, options, etc.)
2. Extracts hierarchy based on analysis
3. Handles complications: Tiers, Options, Texts, Different structures
4. Generates self-assessment reports for each subject
5. Can run for hours processing all subjects

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python ocr-gcse-universal-scraper.py [--subject-code JXXX] [--limit N]
"""

import os
import sys
import re
import time
import json
import argparse
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
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

GCSE_SUBJECTS_FILE = Path(__file__).parent.parent.parent / "A-Level" / "topics" / "OCR GCSE.md"
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Subjects to exclude (already scraped and perfect)
EXCLUDED_SUBJECT_CODES = [
    'J260',  # Science B, Combined - already perfect
    'J383',  # Geography A - already perfect
]


class UniversalGCSEscraper:
    """Universal scraper for all OCR GCSE courses."""
    
    def __init__(self):
        self.debug_dir = Path(__file__).parent.parent.parent / "A-Level" / "debug-output"
        self.debug_dir.mkdir(exist_ok=True)
        self.reports_dir = REPORTS_DIR
        self.reports_dir.mkdir(exist_ok=True)
        self.subjects = []
        self.all_reports = []
    
    def load_subjects(self) -> List[Dict]:
        """Load subjects from markdown file."""
        subjects = []
        
        if not GCSE_SUBJECTS_FILE.exists():
            print(f"[ERROR] Subjects file not found: {GCSE_SUBJECTS_FILE}")
            return []
        
        with open(GCSE_SUBJECTS_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines[1:]:  # Skip header
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse formats:
            # Format 1: "Subject Name (9-1) JXXX - URL"
            # Format 2: "Subject Name (9-1) - Suite Name JXXX - URL"
            # Format 3: "Subject Name (9-1) J170, J171, J172 - URL"
            # Format 4: "Subject Name (9-1) J170-J176 - URL"
            
            # Find the (9-1) marker
            if '(9-1)' not in line:
                continue
            
            # Find all J codes in the line (J followed by 3 digits)
            code_matches = re.findall(r'J\d{3}(?:-\d{3})?', line)
            if not code_matches:
                continue
            
            # Extract subject name (everything before (9-1))
            subject_match = re.match(r'^(.+?)\s+\(9-1\)', line)
            if not subject_match:
                continue
            subject_name = subject_match.group(1).strip()
            
            # Extract URL (everything after the last dash)
            url_match = re.search(r'-\s+(https?://.+)$', line)
            if not url_match:
                continue
            url = url_match.group(1).strip()
            
            # Process codes
            codes = []
            for code_str in code_matches:
                if '-' in code_str:
                    # Handle range like J170-J176
                    code_range = code_str.split('-')
                    base = code_range[0][:-1]  # Remove last char (e.g., "J17" from "J170")
                    start = int(code_range[0][-1])  # Last digit (e.g., 0 from "J170")
                    end = int(code_range[1][-1])  # Last digit (e.g., 6 from "J176")
                    codes.extend([f"{base}{i}" for i in range(start, end + 1)])
                else:
                    codes.append(code_str)
            
            # Remove duplicates and sort
            codes = sorted(list(set(codes)))
            
            for code in codes:
                # Skip excluded subjects
                if code in EXCLUDED_SUBJECT_CODES:
                    print(f"[INFO] Skipping excluded subject: {code} ({subject_name})")
                    continue
                
                subjects.append({
                    'name': subject_name,
                    'code': code,
                    'url': url
                })
        
        return subjects
    
    def scrape_all(self, subject_code_filter: Optional[str] = None, limit: Optional[int] = None):
        """Scrape all subjects."""
        print("\n" + "🎓 "*40)
        print("OCR GCSE UNIVERSAL SCRAPER")
        print("🎓 "*40)
        
        # Load subjects
        self.subjects = self.load_subjects()
        if not self.subjects:
            print("[ERROR] No subjects loaded!")
            return False
        
        # Filter if needed
        if subject_code_filter:
            self.subjects = [s for s in self.subjects if s['code'] == subject_code_filter]
            if not self.subjects:
                print(f"[ERROR] No subject found with code {subject_code_filter}")
                return False
        
        # Limit if specified
        if limit:
            self.subjects = self.subjects[:limit]
        
        # Group subjects by PDF URL to avoid re-scraping same PDF
        url_to_subjects = {}
        for subject in self.subjects:
            url = subject['url']
            if url not in url_to_subjects:
                url_to_subjects[url] = []
            url_to_subjects[url].append(subject)
        
        print(f"\n[INFO] Processing {len(self.subjects)} subjects ({len(url_to_subjects)} unique PDFs)")
        print("="*80)
        
        # Process each unique PDF URL
        success_count = 0
        fail_count = 0
        pdf_cache = {}  # Cache PDF content and extraction results by URL
        
        pdf_index = 0
        for url, subjects_with_same_pdf in url_to_subjects.items():
            pdf_index += 1
            print(f"\n{'='*80}")
            print(f"[PDF {pdf_index}/{len(url_to_subjects)}] Processing PDF: {len(subjects_with_same_pdf)} subject(s) share this PDF")
            for s in subjects_with_same_pdf:
                print(f"  - {s['name']} ({s['code']})")
            print("="*80)
            
            # Process PDF once
            try:
                # Download PDF (if not cached)
                if url not in pdf_cache:
                    print(f"[INFO] Downloading PDF from {url}...")
                    pdf_content = self._download_pdf(url)
                    if not pdf_content:
                        # All subjects fail
                        for subject in subjects_with_same_pdf:
                            fail_count += 1
                            result = {
                                'subject_code': subject['code'],
                                'subject_name': subject['name'],
                                'success': False,
                                'error': 'PDF download failed',
                                'topics_extracted': 0,
                                'levels': {},
                                'issues': ['PDF download failed'],
                                'success_grade': 0
                            }
                            self.all_reports.append(result)
                            self._save_report(subject['code'], result)
                        continue
                    
                    # Extract PDF text
                    pdf_text = self._extract_pdf_text(pdf_content)
                    if not pdf_text:
                        # All subjects fail
                        for subject in subjects_with_same_pdf:
                            fail_count += 1
                            result = {
                                'subject_code': subject['code'],
                                'subject_name': subject['name'],
                                'success': False,
                                'error': 'PDF text extraction failed',
                                'topics_extracted': 0,
                                'levels': {},
                                'issues': ['PDF text extraction failed'],
                                'success_grade': 0
                            }
                            self.all_reports.append(result)
                            self._save_report(subject['code'], result)
                        continue
                    
                    # Analyze PDF structure (once per PDF)
                    print("[INFO] Phase 1: Analyzing PDF structure...")
                    analysis = self._analyze_pdf_structure(subjects_with_same_pdf[0], pdf_text)
                    
                    if not analysis.get('content_found'):
                        # All subjects fail
                        for subject in subjects_with_same_pdf:
                            fail_count += 1
                            result = {
                                'subject_code': subject['code'],
                                'subject_name': subject['name'],
                                'success': False,
                                'error': 'Could not find Content Overview section',
                                'topics_extracted': 0,
                                'levels': {},
                                'issues': ['Content Overview section not found'],
                                'success_grade': 0,
                                'analysis': analysis
                            }
                            self.all_reports.append(result)
                            self._save_report(subject['code'], result)
                        continue
                    
                    # Check if multiple subjects share this PDF (like Art subjects)
                    multiple_subjects = len(subjects_with_same_pdf) > 1
                    
                    if multiple_subjects:
                        # Extract separately for each subject (to filter subject-specific content)
                        print(f"[INFO] Multiple subjects share this PDF - extracting separately for each subject")
                        # Don't cache - extract per subject
                        pdf_cache[url] = {
                            'pdf_text': pdf_text,
                            'analysis': analysis,
                            'extract_per_subject': True
                        }
                    else:
                        # Extract hierarchy (once per PDF)
                        print("[INFO] Phase 2: Extracting topic hierarchy...")
                        topics_text = self._extract_hierarchy(subjects_with_same_pdf[0], pdf_text, analysis)
                        
                        if not topics_text:
                            # All subjects fail
                            for subject in subjects_with_same_pdf:
                                fail_count += 1
                                result = {
                                    'subject_code': subject['code'],
                                    'subject_name': subject['name'],
                                    'success': False,
                                    'error': 'No topics extracted',
                                    'topics_extracted': 0,
                                    'levels': {},
                                    'issues': ['Extraction returned no topics'],
                                    'success_grade': 0,
                                    'analysis': analysis
                                }
                                self.all_reports.append(result)
                                self._save_report(subject['code'], result)
                            continue
                        
                        # Parse topics (once per PDF)
                        parsed_topics = self._parse_hierarchy(topics_text, subjects_with_same_pdf[0]['code'])
                        
                        # Cache results
                        pdf_cache[url] = {
                            'pdf_text': pdf_text,
                            'analysis': analysis,
                            'parsed_topics': parsed_topics,
                            'topics_text': topics_text,
                            'extract_per_subject': False
                        }
                        # Set for use in loop below
                        cached_parsed_topics = parsed_topics
                else:
                    # Use cached results
                    cached = pdf_cache[url]
                    if cached.get('extract_per_subject'):
                        # Need to extract per subject
                        pdf_text = cached['pdf_text']
                        analysis = cached['analysis']
                        multiple_subjects = True
                    else:
                        # Use cached extraction
                        print(f"[INFO] Using cached PDF data for {len(subjects_with_same_pdf)} subject(s)")
                        cached_parsed_topics = cached['parsed_topics']
                        analysis = cached['analysis']
                        multiple_subjects = False
                
                # Process each subject that shares this PDF
                for subject in subjects_with_same_pdf:
                    print(f"\n[INFO] Processing subject: {subject['name']} ({subject['code']})")
                    
                    if multiple_subjects:
                        # Extract separately for this subject (filter subject-specific content)
                        print(f"[INFO] Phase 2: Extracting topic hierarchy for {subject['name']}...")
                        topics_text = self._extract_hierarchy(subject, pdf_text, analysis, filter_by_subject=True)
                        
                        if not topics_text:
                            fail_count += 1
                            result = {
                                'subject_code': subject['code'],
                                'subject_name': subject['name'],
                                'success': False,
                                'error': 'No topics extracted',
                                'topics_extracted': 0,
                                'levels': {},
                                'issues': ['Extraction returned no topics'],
                                'success_grade': 0,
                                'analysis': analysis
                            }
                            self.all_reports.append(result)
                            self._save_report(subject['code'], result)
                            continue
                        
                        # Parse topics for this subject
                        parsed_topics = self._parse_hierarchy(topics_text, subject['code'])
                    else:
                        # Use shared extraction, just update codes
                        # Create subject-specific topics (update codes)
                        # Find the base code used in parsed topics (first subject's code)
                        base_code = subjects_with_same_pdf[0]['code']
                        subject_topics = []
                        code_mapping = {}  # Map old codes to new codes for parent relationships
                        
                        for topic in cached_parsed_topics:
                            # Replace base code with subject code in topic code
                            old_code = topic['code']
                            new_code = old_code.replace(base_code, subject['code'], 1)
                            code_mapping[old_code] = new_code
                            
                            # Update parent code
                            new_parent = None
                            if topic['parent']:
                                new_parent = code_mapping.get(topic['parent'], topic['parent'].replace(base_code, subject['code'], 1))
                            
                            subject_topics.append({
                                'code': new_code,
                                'title': topic['title'],
                                'level': topic['level'],
                                'parent': new_parent
                            })
                        parsed_topics = subject_topics
                    
                    # Count topics by level
                    level_counts = {}
                    for t in parsed_topics:
                        level = t['level']
                        level_counts[level] = level_counts.get(level, 0) + 1
                    
                    subject_topics = parsed_topics
                    
                    # Self-assess
                    print("[INFO] Phase 3: Generating self-assessment report...")
                    assessment = self._self_assess(subject, analysis, subject_topics, level_counts)
                    
                    # Upload to database
                    print("[INFO] Uploading to database...")
                    upload_success = self._upload_topics(subject, subject_topics)
                    
                    # Create report
                    result = {
                        'subject_code': subject['code'],
                        'subject_name': subject['name'],
                        'url': url,
                        'start_time': datetime.now().isoformat(),
                        'success': True,
                        'topics_extracted': len(subject_topics),
                        'levels': level_counts,
                        'issues': assessment.get('issues', []),
                        'warnings': assessment.get('warnings', []),
                        'success_grade': assessment.get('grade', 0),
                        'analysis': analysis,
                        'duration_seconds': 0,
                        'end_time': datetime.now().isoformat()
                    }
                    
                    if not upload_success:
                        result['warnings'].append("Database upload failed")
                    
                    self.all_reports.append(result)
                    self._save_report(subject['code'], result)
                    
                    if result['success']:
                        success_count += 1
                        print(f"[OK] ✓ Successfully processed {subject['code']}")
                    else:
                        fail_count += 1
                        print(f"[FAIL] ✗ Failed to process {subject['code']}: {result.get('error', 'Unknown error')}")
                
                # Rate limiting
                if pdf_index < len(url_to_subjects):
                    print(f"\n[INFO] Waiting 5 seconds before next PDF...")
                    time.sleep(5)
                    
            except Exception as e:
                fail_count += 1
                print(f"[ERROR] Exception processing {subject['code']}: {e}")
                import traceback
                traceback.print_exc()
                self.all_reports.append({
                    'subject_code': subject['code'],
                    'subject_name': subject['name'],
                    'success': False,
                    'error': str(e),
                    'topics_extracted': 0,
                    'levels': {},
                    'issues': [f"Exception: {str(e)}"],
                    'success_grade': 0
                })
        
        # Generate summary report
        self._generate_summary_report(success_count, fail_count)
        
        print(f"\n{'='*80}")
        print(f"SUMMARY: {success_count} succeeded, {fail_count} failed")
        print(f"{'='*80}")
        
        return success_count > 0
    
    def _process_subject(self, subject: Dict) -> Dict:
        """Process one subject: Analyze → Extract → Report."""
        
        start_time = time.time()
        report = {
            'subject_code': subject['code'],
            'subject_name': subject['name'],
            'url': subject['url'],
            'start_time': datetime.now().isoformat(),
            'success': False,
            'topics_extracted': 0,
            'levels': {},
            'issues': [],
            'warnings': [],
            'success_grade': 0,
            'analysis': {},
            'duration_seconds': 0
        }
        
        try:
            # Download PDF
            print(f"[INFO] Downloading PDF from {subject['url']}...")
            pdf_content = self._download_pdf(subject['url'])
            if not pdf_content:
                report['error'] = "PDF download failed"
                return report
            
            # Extract PDF text
            pdf_text = self._extract_pdf_text(pdf_content)
            if not pdf_text:
                report['error'] = "PDF text extraction failed"
                return report
            
            # PHASE 1: ANALYZE PDF STRUCTURE
            print("[INFO] Phase 1: Analyzing PDF structure...")
            analysis = self._analyze_pdf_structure(subject, pdf_text)
            report['analysis'] = analysis
            
            if not analysis.get('content_found'):
                report['error'] = "Could not find Content Overview section"
                report['issues'].append("Content Overview section not found")
                return report
            
            # PHASE 2: EXTRACT HIERARCHY
            print("[INFO] Phase 2: Extracting topic hierarchy...")
            topics = self._extract_hierarchy(subject, pdf_text, analysis)
            
            if not topics:
                report['error'] = "No topics extracted"
                report['issues'].append("Extraction returned no topics")
                return report
            
            # Parse and count topics
            parsed_topics = self._parse_hierarchy(topics, subject['code'])
            
            # Count by level
            level_counts = {}
            for t in parsed_topics:
                level = t['level']
                level_counts[level] = level_counts.get(level, 0) + 1
            
            report['topics_extracted'] = len(parsed_topics)
            report['levels'] = level_counts
            report['success'] = True
            
            # PHASE 3: SELF-ASSESSMENT
            print("[INFO] Phase 3: Generating self-assessment report...")
            assessment = self._self_assess(subject, analysis, parsed_topics, level_counts)
            report['success_grade'] = assessment['grade']
            report['issues'].extend(assessment['issues'])
            report['warnings'].extend(assessment['warnings'])
            
            # Upload to database
            print("[INFO] Uploading to database...")
            upload_success = self._upload_topics(subject, parsed_topics)
            if not upload_success:
                report['warnings'].append("Database upload failed")
            
            report['duration_seconds'] = time.time() - start_time
            report['end_time'] = datetime.now().isoformat()
            
            return report
            
        except Exception as e:
            report['error'] = str(e)
            report['issues'].append(f"Exception: {str(e)}")
            import traceback
            report['traceback'] = traceback.format_exc()
            return report
    
    def _download_pdf(self, url: str) -> Optional[bytes]:
        """Download PDF. If URL is a webpage, try to find PDF link."""
        try:
            # Check if URL is already a PDF
            if url.lower().endswith('.pdf'):
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                # Verify it's actually a PDF
                if response.content[:4] == b'%PDF':
                    print(f"[OK] Downloaded PDF: {len(response.content)/1024/1024:.1f} MB")
                    return response.content
                else:
                    print(f"[WARN] URL ends in .pdf but content is not a PDF")
            
            # URL is a webpage - try to find PDF link
            print(f"[INFO] URL is a webpage, searching for PDF link...")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # Look for PDF links in the HTML
            html_content = response.text
            
            # Common patterns for PDF links on OCR pages
            pdf_patterns = [
                r'href=["\']([^"\']*specification[^"\']*\.pdf[^"\']*)["\']',
                r'href=["\']([^"\']*\.pdf)["\']',
                r'https://www\.ocr\.org\.uk/Images/[^"\']+\.pdf',
            ]
            
            pdf_url = None
            for pattern in pdf_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    # Prefer specification PDFs
                    spec_matches = [m for m in matches if 'specification' in m.lower()]
                    if spec_matches:
                        pdf_url = spec_matches[0]
                    else:
                        pdf_url = matches[0]
                    break
            
            if pdf_url:
                # Make absolute URL if relative
                if pdf_url.startswith('/'):
                    pdf_url = 'https://www.ocr.org.uk' + pdf_url
                elif not pdf_url.startswith('http'):
                    pdf_url = url.rsplit('/', 1)[0] + '/' + pdf_url
                
                print(f"[INFO] Found PDF link: {pdf_url}")
                pdf_response = requests.get(pdf_url, timeout=60)
                pdf_response.raise_for_status()
                if pdf_response.content[:4] == b'%PDF':
                    print(f"[OK] Downloaded PDF: {len(pdf_response.content)/1024/1024:.1f} MB")
                    return pdf_response.content
                else:
                    print(f"[WARN] Link found but content is not a PDF")
            
            print(f"[ERROR] Could not find PDF link on webpage")
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
    
    def _analyze_pdf_structure(self, subject: Dict, pdf_text: str) -> Dict:
        """PHASE 1: Analyze PDF structure to understand it."""
        
        # Find Content Overview section
        content_overview_match = re.search(
            r'Content\s+Overview|Content\s+overview|CONTENT\s+OVERVIEW',
            pdf_text,
            re.IGNORECASE
        )
        
        if not content_overview_match:
            return {'content_found': False}
        
        # Extract Content Overview section (next 5000 chars)
        start_pos = content_overview_match.start()
        content_section = pdf_text[start_pos:start_pos+10000]
        
        # Also get Assessment Overview if present
        assessment_match = re.search(
            r'Assessment\s+Overview|Assessment\s+overview|ASSESSMENT\s+OVERVIEW',
            pdf_text,
            re.IGNORECASE
        )
        
        analysis_prompt = f"""You are analyzing an OCR GCSE specification PDF to understand its structure BEFORE extraction.

SUBJECT: {subject['name']} ({subject['code']})

YOUR TASK: Analyze the PDF structure and provide a detailed analysis in JSON format.

CRITICAL: Focus ONLY on externally examined content (Written Papers). IGNORE coursework, internally assessed, or non-examined content.

ANALYSIS REQUIRED:

1. **Tiers**: Does this subject have Foundation/Higher tiers?
   - Look for "Foundation Tier" and "Higher Tier" mentions
   - Check if content is split by tier
   - If yes: List what's different between tiers

2. **Options**: Are there optional units/components?
   - List ALL optional units/components found
   - Note which are compulsory vs optional

3. **Texts/Lists**: Are there prescribed texts, reading lists, or similar?
   - For English/Drama/Art subjects: Look for text lists
   - Note where these appear in the structure
   - Decide: Should they be separate hierarchies or incorporated?

4. **Structure Type**: What type of structure does this PDF use?
   - Table-based (like Sociology, Religious Studies)
   - Chapter-based (like Combined Science)
   - Topic-based (like Mathematics)
   - Component-based (like Psychology)
   - Other (describe)

5. **Content Overview Analysis**:
   - What main sections/components are listed?
   - How are they organized?
   - What's the expected hierarchy depth?

6. **Assessment Structure**:
   - How many written papers/components?
   - What content does each assess?
   - Any cross-component content?

7. **Known Patterns**: Based on A-Level scrapers, does this match any known pattern?
   - Mathematics (table with ref codes)
   - Sociology (Key questions, Content, Learners should)
   - Religious Studies (Topic, Content, Key Knowledge)
   - PE (Topic Area, Content with bullets)
   - Law (Content, Guidance)
   - Other?

OUTPUT FORMAT (JSON only):
{{
    "tiers": {{
        "has_tiers": true/false,
        "foundation_content": "description",
        "higher_content": "description",
        "differences": ["list of differences"]
    }},
    "options": {{
        "has_options": true/false,
        "compulsory": ["list"],
        "optional": ["list"]
    }},
    "texts": {{
        "has_texts": true/false,
        "text_locations": ["where texts appear"],
        "extraction_strategy": "separate_hierarchy" or "incorporated"
    }},
    "structure_type": "table-based|chapter-based|topic-based|component-based|other",
    "content_overview": {{
        "main_sections": ["list"],
        "organization": "description",
        "expected_depth": 3-6
    }},
    "assessment": {{
        "written_papers": ["list"],
        "content_mapping": {{"paper": "content"}},
        "cross_component": true/false
    }},
    "known_pattern": "mathematics|sociology|religious_studies|pe|law|other",
    "extraction_guidance": "Specific instructions for extraction phase"
}}

CONTENT OVERVIEW SECTION:
{content_section[:8000]}

ASSESSMENT OVERVIEW (if present):
{pdf_text[assessment_match.start():assessment_match.start()+5000] if assessment_match else "Not found"}

CRITICAL: Output ONLY valid JSON. No markdown, no explanations, just JSON."""
        
        analysis_json = self._call_ai(analysis_prompt, max_tokens=4000)
        
        # Save analysis output for debugging
        if analysis_json:
            safe_code = re.sub(r'[^\w\-]', '_', subject['code'])
            analysis_file = self.debug_dir / f"{safe_code}-analysis.json"
            analysis_file.write_text(analysis_json, encoding='utf-8')
            print(f"[DEBUG] Saved analysis to {analysis_file.name}")
        
        if not analysis_json:
            return {'content_found': True, 'analysis_failed': True}
        
        # Parse JSON
        try:
            analysis = json.loads(analysis_json)
            analysis['content_found'] = True
            return analysis
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', analysis_json, re.DOTALL)
            if json_match:
                try:
                    analysis = json.loads(json_match.group(1))
                    analysis['content_found'] = True
                    return analysis
                except:
                    pass
            
            return {'content_found': True, 'analysis_failed': True, 'raw_output': analysis_json[:500]}
    
    def _extract_hierarchy(self, subject: Dict, pdf_text: str, analysis: Dict, filter_by_subject: bool = False) -> Optional[str]:
        """PHASE 2: Extract hierarchy based on analysis."""
        
        # Build extraction prompt based on analysis
        extraction_prompt = self._build_extraction_prompt(subject, pdf_text, analysis, filter_by_subject=filter_by_subject)
        
        result = self._call_ai(extraction_prompt, max_tokens=16000)
        
        # Save AI output for debugging
        if result:
            safe_code = re.sub(r'[^\w\-]', '_', subject['code'])
            ai_file = self.debug_dir / f"{safe_code}-ai-output.txt"
            ai_file.write_text(result, encoding='utf-8')
            print(f"[DEBUG] Saved AI output to {ai_file.name}")
        
        return result
    
    def _build_extraction_prompt(self, subject: Dict, pdf_text: str, analysis: Dict, filter_by_subject: bool = False) -> str:
        """Build extraction prompt based on analysis."""
        
        # Find content sections
        content_match = re.search(
            r'Content\s+of|Content\s+Overview|2[a-z]\.\s+Content',
            pdf_text,
            re.IGNORECASE
        )
        
        if content_match:
            content_start = content_match.start()
            content_section = pdf_text[content_start:content_start+150000]  # Large section
        else:
            content_section = pdf_text[:150000]  # First 150k chars
        
        # Build tier instructions
        tier_instructions = ""
        if analysis.get('tiers', {}).get('has_tiers'):
            tier_instructions = """
CRITICAL: TIER HANDLING
- Create TWO Level 0 topics: "Foundation Tier" and "Higher Tier"
- Each tier will have similar Level 1 structure but different Level 2-4 content
- Foundation Tier: Extract content marked for Foundation or grades 1-5
- Higher Tier: Extract content marked for Higher or grades 4-9
- If content is shared, include it in BOTH tiers
"""
        
        # Build options instructions
        options_instructions = ""
        if analysis.get('options', {}).get('has_options'):
            optional_list = analysis.get('options', {}).get('optional', [])
            options_instructions = f"""
CRITICAL: OPTIONS HANDLING
- Extract ALL optional units/components: {', '.join(optional_list)}
- Do NOT skip optional content - extract everything
- Mark optional units clearly in the hierarchy
"""
        
        # Build texts instructions
        texts_instructions = ""
        if analysis.get('texts', {}).get('has_texts'):
            strategy = analysis.get('texts', {}).get('extraction_strategy', 'incorporated')
            if strategy == 'separate_hierarchy':
                texts_instructions = """
CRITICAL: TEXTS HANDLING
- Extract prescribed texts as a separate Level 1 hierarchy
- Create: "1. Prescribed Texts" or similar
- List all texts with their details
"""
            else:
                texts_instructions = """
CRITICAL: TEXTS HANDLING
- Incorporate text lists into the topics they relate to
- Add texts as sub-items under relevant topics
"""
        
        # Build structure-specific instructions
        structure_type = analysis.get('structure_type', 'unknown')
        structure_instructions = self._get_structure_instructions(structure_type, analysis)
        
        # Add subject filtering instruction if needed
        subject_filter_instruction = ""
        if filter_by_subject:
            # Map subject codes to their full names for better matching
            subject_name_mapping = {
                'J170': 'Art, Craft and Design',
                'J171': 'Fine Art',
                'J172': 'Graphic Communication',
                'J173': 'Photography',
                'J174': 'Textile Design',
                'J175': 'Three-Dimensional Design',
                'J176': 'Critical and Contextual Studies'
            }
            full_subject_name = subject_name_mapping.get(subject['code'], subject['name'])
            
            subject_filter_instruction = f"""
CRITICAL: SUBJECT FILTERING - THIS IS ESSENTIAL
- This PDF contains content for MULTIPLE Art subjects (J170-J176)
- Extract ONLY content specific to: {full_subject_name} ({subject['code']})
- IGNORE ALL content for other subjects:
  * If extracting {full_subject_name} ({subject['code']}), IGNORE:
    - Art, Craft and Design (J170) - unless this IS the subject
    - Fine Art (J171) - unless this IS the subject
    - Graphic Communication (J172) - unless this IS the subject
    - Photography (J173) - unless this IS the subject
    - Textile Design (J174) - unless this IS the subject
    - Three-Dimensional Design (J175) - unless this IS the subject
    - Critical and Contextual Studies (J176) - unless this IS the subject
- Look for section headings that explicitly mention "{full_subject_name}" or "{subject['code']}"
- Only extract content under sections that clearly belong to {full_subject_name}
- If a section doesn't mention {full_subject_name} or {subject['code']}, SKIP IT
- Extract ONLY the content that is specific to {full_subject_name}, not general Art content
"""
        
        prompt = f"""You must extract the COMPLETE hierarchy from OCR GCSE {subject['name']} ({subject['code']}).

CRITICAL: Extract EVERYTHING you can see. Do NOT stop partway. Do NOT ask questions. Extract EVERYTHING NOW.
OUTPUT FORMAT: Use ONLY numbered format (1, 1.1, 1.1.1) - NO bullets (-), NO asterisks (*), NO markdown (**), NO bold markers.
Do NOT use markdown formatting. Do NOT use bullets. Use ONLY numbers and dots.

SUBJECT: {subject['name']} ({subject['code']})
{subject_filter_instruction}

{tier_instructions}
{options_instructions}
{texts_instructions}

{structure_instructions}

CRITICAL RULES:
1. Focus ONLY on externally examined content (Written Papers)
2. IGNORE coursework, internally assessed, or non-examined content
3. IGNORE assessment sections: "Assessment of GCSE", "Admin: what you need to know", "Appendices" - DO NOT extract these
4. Extract ALL topics at ALL levels - INCLUDING Level 4 detailed content items
5. Maintain complete hierarchy - do NOT stop at Level 3, always extract Level 4 sub-items
6. OUTPUT MUST BE PLAIN TEXT WITH NUMBERS ONLY - NO MARKDOWN FORMATTING
7. Handle topics that span multiple pages
8. Extract ALL optional units/components
9. Match related content correctly (e.g., "Learners should:" to Content)
10. For component-based structures: Extract ALL bullet points, sub-items, and detailed learning points as Level 4 topics
11. Look for tables with "Sub topic" and "Guidance" columns - extract all items from these tables as Level 4
12. CRITICAL: Extract "Prescribed Sources" sections (Prescribed Literary Sources, Prescribed Visual/Material Sources) as separate topics with ALL their content:
    - Extract each prescribed source as a Level 4 topic
    - Extract learning objectives under "When studying..." sections as Level 4 topics
    - Include all sub-items, bullet points, and detailed content from Prescribed Sources sections

CONTENT SECTION:
{content_section[:120000]}

EXTRACT NOW:"""
        
        return prompt
    
    def _get_structure_instructions(self, structure_type: str, analysis: Dict) -> str:
        """Get structure-specific extraction instructions."""
        
        known_pattern = analysis.get('known_pattern', '')
        
        if known_pattern == 'mathematics':
            return """
STRUCTURE (similar to A-Level Mathematics):
- Level 0: Subject/Tier
- Level 1: Main topics (e.g., "Number", "Algebra")
- Level 2: Sub-topics
- Level 3: Specific content items
- Level 4: Detailed points
Tables have reference codes - extract these as part of hierarchy.
"""
        elif known_pattern == 'sociology':
            return """
STRUCTURE (similar to A-Level Sociology):
- Level 0: Component/Tier
- Level 1: Sections (e.g., "Section A: ...")
- Level 2: Key questions (from "Key questions" column)
- Level 3: Content items (from "Content" column)
- Level 4: Sub-items + "Learners should:" items (matched to Content parent)
Tables have 3 columns: Key questions, Content, Learners should:
"""
        elif known_pattern == 'religious_studies':
            return """
STRUCTURE (similar to A-Level Religious Studies):
- Level 0: Component/Tier
- Level 1: Main topics
- Level 2: Topic headings (from "Topic" column)
- Level 3: Content items (from "Content" column)
- Level 4: Key Knowledge items (matched to Content parent)
Tables have 3 columns: Topic, Content, Key Knowledge
"""
        elif structure_type == 'chapter-based':
            return """
STRUCTURE (Chapter-based, like Combined Science):
- Level 0: Subject/Tier
- Level 1: Chapters (e.g., "B1: You and your genes", "C1: Air and water")
- Level 2: Main topics within chapters
- Level 3: Sub-topics
- Level 4: Specific content points
Extract all chapters listed in Content Overview.
"""
        elif structure_type == 'component-based':
            return """
STRUCTURE (Component-based):
- Level 0: Subject/Tier
- Level 1: Components (e.g., "Component 01: ...", "Component 02: ...")
- Level 2: Sections/Topics within components (e.g., "1.1 Systems architecture", "1.2 Memory and storage", "Greek and Roman gods")
- Level 3: Sub-topics (e.g., "Architecture of the CPU", "CPU performance", "Greece", "Rome")
- Level 4: Detailed content items (CRITICAL - extract ALL sub-items, bullet points, and specific learning points under each Level 3 topic)

CRITICAL FOR LEVEL 4:
- Extract ALL bullet points, sub-items, and detailed content under each Level 3 topic
- Extract items from tables (e.g., "The purpose of the CPU:", "Common CPU components and their function:")
- Extract all specific learning points, even if they appear as sub-bullets or in guidance columns
- Extract lists of items (e.g., "Zeus, Hera, Demeter, Poseidon..." should be split into separate Level 4 items)
- Do NOT stop at Level 3 - always extract Level 4 content items
- Examples of Level 4 items: "The fetch-execute cycle", "ALU (Arithmetic Logic Unit)", "Clock speed", "Zeus", "Hera", etc.

PRESCRIBED SOURCES (for subjects like Classical Civilisation):
- "Prescribed Literary Sources" and "Prescribed Visual/Material Sources" should be extracted as Level 2 topics under their Content Section
- Extract each prescribed source (e.g., "The Homeric Hymns", "Plutarch, The Parallel Lives") as Level 3 topics
- Extract specific sections/hymns/books (e.g., "Hymn to Demeter: Lines 1-104") as Level 4 topics
- Extract learning objectives under "When studying..." sections as Level 4 topics
- Extract ALL content from Prescribed Sources sections - do NOT skip any sources or learning objectives

Extract all components, sections, topics, AND their detailed content items (Level 4), including Prescribed Sources.
"""
        else:
            return """
STRUCTURE (discover from PDF):
- Level 0: Subject/Tier
- Level 1: Main sections/topics
- Level 2-4: Discover hierarchy from PDF structure
Extract based on the actual structure you see in the PDF.
"""
    
    def _self_assess(self, subject: Dict, analysis: Dict, topics: List[Dict], level_counts: Dict) -> Dict:
        """PHASE 3: Self-assessment of extraction quality."""
        
        assessment_prompt = f"""Assess the quality of this OCR GCSE extraction.

SUBJECT: {subject['name']} ({subject['code']})

ANALYSIS FINDINGS:
- Tiers: {analysis.get('tiers', {}).get('has_tiers', False)}
- Options: {analysis.get('options', {}).get('has_options', False)}
- Structure: {analysis.get('structure_type', 'unknown')}

EXTRACTION RESULTS:
- Total topics: {len(topics)}
- Level distribution: {level_counts}
- Expected depth: {analysis.get('content_overview', {}).get('expected_depth', 'unknown')}

ASSESSMENT CRITERIA:
1. **Completeness** (40%): Are all expected topics extracted?
   - Check against Content Overview
   - Are tiers handled correctly?
   - Are options extracted?
   - Are texts extracted (if applicable)?

2. **Structure Quality** (30%): Is hierarchy correct?
   - Appropriate depth?
   - Logical organization?
   - Parent-child relationships correct?

3. **Content Quality** (20%): Is content accurate?
   - No missing sections?
   - No duplicate topics?
   - Proper level assignment?

4. **Issues/Warnings** (10%): What problems exist?
   - Missing content?
   - Structure problems?
   - Extraction errors?

OUTPUT FORMAT (JSON only):
{{
    "grade": 85,
    "issues": ["list of problems"],
    "warnings": ["list of warnings"],
    "completeness_score": 90,
    "structure_score": 85,
    "content_score": 80,
    "notes": "Overall assessment notes"
}}

CRITICAL: Output ONLY valid JSON. No markdown, no explanations, just JSON."""
        
        assessment_json = self._call_ai(assessment_prompt, max_tokens=2000)
        
        if not assessment_json:
            return {'grade': 50, 'issues': ['Assessment failed'], 'warnings': []}
        
        try:
            assessment = json.loads(assessment_json)
            return assessment
        except json.JSONDecodeError:
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', assessment_json, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except:
                    pass
            
            return {'grade': 50, 'issues': ['Assessment JSON parse failed'], 'warnings': ['Raw output available']}
    
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
                print(f"[WARN] Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"[INFO] Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"[ERROR] All {max_retries} attempts failed")
                    return None
        
        return None
    
    def _parse_hierarchy(self, text: str, base_code: str) -> List[Dict]:
        """Parse AI numbered output."""
        all_topics = []
        parent_stack = {-1: None}
        
        # Section markers that should be filtered out (not actual topics)
        excluded_headers = [
            'components', 'component', 'content', 'content overview', 
            'assessment overview', 'summary', 'overview',
            'sections within components', 'sections within component',
            'sections within', 'sections'
        ]
        
        # Assessment/admin sections that should be completely filtered out
        assessment_sections = [
            'assessment of', 'assessment:', 'admin:', 'admin: what you need to know',
            'appendices', 'appendix', 'forms of assessment', 'assessment objectives',
            'total qualification time', 'qualification availability', 'language',
            'assessment availability', 'retaking', 'synoptic assessment',
            'calculating qualification results', 'pre-assessment', 'special consideration',
            'external assessment arrangements', 'results and certificates',
            'post-results services', 'malpractice', 'grade descriptors',
            'overlap with other qualifications', 'accessibility'
        ]
        
        # Track filtered levels: map level -> parent_code to use for children
        filtered_level_parents = {}
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Match hierarchical numbers
            match = re.match(r'^([\d.]+)\s+(.+)$', line)
            if not match:
                match = re.match(r'^\*\*?([\d.]+)\s+(.+?)\*\*?$', line)
            if not match:
                match = re.match(r'^[-•●]\s+([\d.]+)\s+(.+)$', line)
            if not match:
                continue
            
            number = match.group(1).rstrip('.')
            title = match.group(2).strip()
            
            # Clean title
            title = title.lstrip('*☐✓□■●○-•').strip()
            title = title.rstrip('*').strip()
            
            if len(title) < 2:
                continue
            
            dots = number.count('.')
            level = dots
            
            # Filter out section markers - ONLY exact matches to avoid filtering legitimate topics
            # Don't filter "Component 01:" or "Component 02:" - those are real topics!
            title_lower = title.lower().strip()
            # Remove trailing colon for comparison
            title_clean = title_lower.rstrip(':').strip()
            
            # Check for excluded section markers
            is_excluded = title_clean in [
                'components', 'component', 'content', 
                'content overview', 'assessment overview', 
                'summary', 'overview',
                'sections within components', 'sections within component',
                'sections within', 'sections'
            ]
            
            # Check for assessment/admin sections - filter these out completely
            # Only filter if title starts with or equals assessment section (to avoid false positives)
            if not is_excluded:
                is_excluded = any(
                    title_lower == assessment or
                    title_lower.startswith(assessment + ':') or
                    title_lower.startswith(assessment + ' ') or
                    title_clean == assessment or
                    title_clean.startswith(assessment + ':') or
                    title_clean.startswith(assessment + ' ')
                    for assessment in assessment_sections
                )
            
            if is_excluded:
                # Skip this topic, but record its parent for children to use
                parent_code = parent_stack.get(level - 1)
                filtered_level_parents[level] = parent_code
                # Clear deeper filtered levels since we're skipping this level
                for l in list(filtered_level_parents.keys()):
                    if l > level:
                        del filtered_level_parents[l]
                continue
            
            code = f"{base_code}_{number.replace('.', '_')}"
            # Find parent - check if parent level was filtered
            parent_level = level - 1
            if parent_level in filtered_level_parents:
                # Parent level was filtered, use the filtered parent
                parent_code = filtered_level_parents[parent_level]
            else:
                # Normal parent finding - go up levels
                parent_code = None
                for pl in range(parent_level, -2, -1):
                    if pl in parent_stack:
                        parent_code = parent_stack[pl]
                        break
            
            all_topics.append({
                'code': code,
                'title': title,
                'level': level,
                'parent': parent_code
            })
            
            parent_stack[level] = code
            # Clear filtered level if we've added a real topic at this level
            if level in filtered_level_parents:
                del filtered_level_parents[level]
            for l in list(parent_stack.keys()):
                if l > level:
                    del parent_stack[l]
        
        return all_topics
    
    def _format_subject_name(self, subject: Dict) -> str:
        """Format subject name with appropriate prefix."""
        subject_code = subject['code']
        subject_name = subject['name']
        
        # Art subjects (J170-J176) get "Art and Design - " prefix (GCSE already in brackets)
        if subject_code in ['J170', 'J171', 'J172', 'J173', 'J174', 'J175', 'J176']:
            # Remove any existing prefix if present
            if subject_name.startswith('GCSE Art and Design - '):
                base_name = subject_name.replace('GCSE Art and Design - ', '')
            elif subject_name.startswith('Art and Design - '):
                base_name = subject_name.replace('Art and Design - ', '')
            else:
                base_name = subject_name
            
            # Remove "(9-1)" suffix if present (will add "(GCSE)" at end)
            base_name = re.sub(r'\s*\(9-1\)\s*$', '', base_name).strip()
            
            return f"Art and Design - {base_name} (GCSE)"
        
        # All other subjects - remove "(9-1)" if present, add "(GCSE)"
        subject_name = re.sub(r'\s*\(9-1\)\s*$', '', subject_name).strip()
        return f"{subject_name} (GCSE)"
    
    def _upload_topics(self, subject: Dict, topics: List[Dict]) -> bool:
        """Upload topics to database."""
        try:
            # Format subject name
            formatted_subject_name = self._format_subject_name(subject)
            
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': formatted_subject_name,
                'subject_code': subject['code'],
                'qualification_type': 'GCSE',
                'specification_url': subject['url'],
                'exam_board': 'OCR'
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            subject_id = subject_result.data[0]['id']
            
            # Clear old topics for this subject to avoid duplicates
            print(f"[INFO] Clearing old topics for {subject['code']}...")
            supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).eq('exam_board', 'OCR').execute()
            
            # Remove duplicates
            seen_codes = set()
            unique_topics = []
            for t in topics:
                if t['code'] not in seen_codes:
                    seen_codes.add(t['code'])
                    unique_topics.append(t)
            
            # Insert topics
            to_insert = [{
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': t['title'],
                'topic_level': t['level'],
                'exam_board': 'OCR'
            } for t in unique_topics]
            
            inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
            
            # Link hierarchy
            code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
            for topic in unique_topics:
                if topic['parent']:
                    parent_id = code_to_id.get(topic['parent'])
                    child_id = code_to_id.get(topic['code'])
                    if parent_id and child_id:
                        supabase.table('staging_aqa_topics').update({
                            'parent_topic_id': parent_id
                        }).eq('id', child_id).execute()
            
            return True
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            return False
    
    def _save_report(self, subject_code: str, report: Dict):
        """Save individual subject report."""
        report_file = self.reports_dir / f"{subject_code}-report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"[INFO] Report saved to {report_file.name}")
    
    def _generate_summary_report(self, success_count: int, fail_count: int):
        """Generate summary report."""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_subjects': len(self.subjects),
            'success_count': success_count,
            'fail_count': fail_count,
            'success_rate': (success_count / len(self.subjects) * 100) if self.subjects else 0,
            'reports': self.all_reports
        }
        
        summary_file = self.reports_dir / f"summary-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n[INFO] Summary report saved to {summary_file.name}")


def main():
    parser = argparse.ArgumentParser(description='OCR GCSE Universal Scraper')
    parser.add_argument('--subject-code', type=str, help='Process only this subject code (e.g., J260)')
    parser.add_argument('--limit', type=int, help='Limit number of subjects to process')
    args = parser.parse_args()
    
    scraper = UniversalGCSEscraper()
    success = scraper.scrape_all(
        subject_code_filter=args.subject_code,
        limit=args.limit
    )
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

