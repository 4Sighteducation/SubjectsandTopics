"""
Eduqas A-Level Universal Scraper
==================================

A universal scraper for ALL Eduqas A-Level courses that:
1. Finds PDF URLs using the PDF URL scraper
2. Downloads PDFs
3. Analyzes PDF structure (Components, Tiers, Options, Appendices)
4. Extracts content using AI with appropriate prompts
5. Handles special cases: Components, Tiers, Options, Appendices

Requirements:
    pip install requests pdfplumber openai anthropic

Usage:
    python eduqas-alevel-universal-scraper.py [--subject SUBJECT] [--limit N]
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
from io import BytesIO

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

# Import PDF URL scraper
import importlib.util
pdf_url_scraper_path = Path(__file__).parent / "eduqas-pdf-url-scraper.py"
spec = importlib.util.spec_from_file_location("eduqas_pdf_url_scraper", pdf_url_scraper_path)
eduqas_pdf_url_scraper_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eduqas_pdf_url_scraper_module)
EduqasPDFURLScraper = eduqas_pdf_url_scraper_module.EduqasPDFURLScraper

# ================================================================
# CONFIGURATION
# ================================================================

QUALIFICATIONS_FILE = Path(__file__).parent / "Eduqas Qualifications - All.md"
PDF_URLS_FILE = Path(__file__).parent / "eduqas-pdf-urls.json"
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class EduqasALevelUniversalScraper:
    """Universal scraper for all Eduqas A-Level courses - uses same proven approach as GCSE scraper."""
    
    def __init__(self):
        self.reports_dir = REPORTS_DIR
        self.reports_dir.mkdir(exist_ok=True)
        self.subjects = []
        self.all_reports = []
        self.pdf_url_scraper = EduqasPDFURLScraper(headless=True)
    
    def load_alevel_subjects(self) -> List[Dict]:
        """Load A-Level subjects from qualifications file."""
        subjects = []
        
        if not QUALIFICATIONS_FILE.exists():
            print(f"[ERROR] Qualifications file not found: {QUALIFICATIONS_FILE}")
            return []
        
        # First, try to load PDF URLs if they exist
        pdf_urls = {}
        if PDF_URLS_FILE.exists():
            try:
                with open(PDF_URLS_FILE, 'r', encoding='utf-8') as f:
                    pdf_urls_data = json.load(f)
                    for key, data in pdf_urls_data.items():
                        subject_name = data.get('subject', '')
                        level = data.get('level', '')
                        if level == 'A-Level':
                            pdf_urls[subject_name] = data.get('pdf_url', '')
            except Exception as e:
                print(f"[WARN] Could not load PDF URLs file: {e}")
        
        # Parse qualifications file
        current_section = None
        
        with open(QUALIFICATIONS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Detect section headers
                if 'GCSE' in line.upper() and 'Eduqas Qualifications' in line:
                    current_section = 'GCSE'
                    continue
                elif 'ALEVEL' in line.upper() or 'A-LEVEL' in line.upper():
                    current_section = 'A-Level'
                    continue
                
                # Skip empty lines and section headers
                if not line or line.startswith('#'):
                    continue
                
                # Only process A-Level subjects
                if current_section != 'A-Level':
                    continue
                
                # Parse subject lines
                separator = None
                if ' - ' in line:
                    separator = ' - '
                elif ' = ' in line:
                    separator = ' = '
                
                if separator:
                    parts = line.split(separator)
                    if len(parts) >= 2:
                        subject = parts[0].strip()
                        level_part = parts[1].strip()
                        
                        # Handle special cases
                        if subject == "Drama (and Theatre)":
                            subject = "Drama"
                        
                        # Only add A-Level subjects
                        # Handle "A", "GCSE / A" (when in A-Level section), and "Level 3 Extended Project" (skip Extended Project)
                        if level_part == "A":
                            pdf_url = pdf_urls.get(subject, '')
                            subjects.append({
                                'name': subject,
                                'level': 'A-Level',
                                'pdf_url': pdf_url,
                                'subject_page_url': pdf_urls.get(f"{subject}_page", '')
                            })
                        elif level_part == "GCSE / A" and current_section == 'A-Level':
                            # In A-Level section, "GCSE / A" means it's available at A-Level too
                            pdf_url = pdf_urls.get(subject, '')
                            subjects.append({
                                'name': subject,
                                'level': 'A-Level',
                                'pdf_url': pdf_url,
                                'subject_page_url': pdf_urls.get(f"{subject}_page", '')
                            })
                        elif "Extended Project" in level_part:
                            # Skip Extended Project
                            continue
        
        print(f"[INFO] Loaded {len(subjects)} A-Level subjects")
        return subjects
    
    def scrape_all(self, subject_filter: Optional[str] = None, limit: Optional[int] = None):
        """Scrape all A-Level subjects."""
        print("\n" + "🎓 "*40)
        print("EDUQAS A-LEVEL UNIVERSAL SCRAPER")
        print("🎓 "*40)
        
        # Load subjects
        self.subjects = self.load_alevel_subjects()
        if not self.subjects:
            print("[ERROR] No subjects loaded!")
            return False
        
        # Filter if needed (before exclusions, so specific subject tests still work)
        if subject_filter:
            self.subjects = [s for s in self.subjects if subject_filter.lower() in s['name'].lower()]
            if not self.subjects:
                print(f"[ERROR] No subject found matching '{subject_filter}'")
                return False
        
        # Exclude subjects that are already perfect (only when running all subjects, not when testing specific ones)
        # Start with empty list - can add subjects here as they're completed
        if not subject_filter:
            excluded_subjects = []  # Add subjects here as they're completed
            original_count = len(self.subjects)
            self.subjects = [s for s in self.subjects if s['name'] not in excluded_subjects]
            excluded_count = original_count - len(self.subjects)
            if excluded_count > 0:
                print(f"[INFO] Excluded {excluded_count} already-perfect subject(s): {', '.join(excluded_subjects)}")
        
        # Limit if specified
        if limit:
            self.subjects = self.subjects[:limit]
        
        print(f"\n[INFO] Processing {len(self.subjects)} subjects")
        print("="*80)
        
        # Process each subject
        success_count = 0
        fail_count = 0
        
        for i, subject in enumerate(self.subjects, 1):
            print(f"\n{'='*80}")
            print(f"[{i}/{len(self.subjects)}] {subject['name']} (A-Level)")
            print("="*80)
            
            try:
                # STEP 1: Find PDF URL using PDF URL scraper (always do this first)
                print(f"[INFO] Step 1: Finding PDF URL for {subject['name']}...")
                
                try:
                    # Find subject page URL
                    subject_page_url = self.pdf_url_scraper.find_subject_page_url(subject['name'], 'A-Level')
                    
                    if not subject_page_url:
                        print(f"[ERROR] Could not find subject page for {subject['name']}")
                        fail_count += 1
                        continue
                    
                    print(f"[OK] Found subject page: {subject_page_url}")
                    
                    # Find PDF URL from subject page
                    pdf_url = self.pdf_url_scraper.find_pdf_url_from_subject_page(
                        subject_page_url, subject['name'], 'A-Level'
                    )
                    
                    if not pdf_url:
                        print(f"[ERROR] Could not find PDF URL on subject page")
                        fail_count += 1
                        continue
                    
                    print(f"[OK] Found PDF URL: {pdf_url}")
                    
                    # Save to subject dict
                    subject['pdf_url'] = pdf_url
                    subject['subject_page_url'] = subject_page_url
                    
                    # Save to PDF URLs file for future reference
                    self._save_pdf_url_to_file(subject['name'], 'A-Level', subject_page_url, pdf_url)
                
                except Exception as e:
                    print(f"[ERROR] Failed to find PDF URL: {e}")
                    import traceback
                    traceback.print_exc()
                    fail_count += 1
                    continue
                
                # STEP 2: Process subject (download PDF and extract content)
                print(f"[INFO] Step 2: Processing PDF content for {subject['name']}...")
                result = self._process_subject(subject)
                
                if result['success']:
                    success_count += 1
                    print(f"[OK] ✓ Successfully processed {subject['name']}")
                else:
                    fail_count += 1
                    print(f"[FAIL] ✗ Failed: {result.get('error', 'Unknown error')}")
                
                self.all_reports.append(result)
                self._save_report(subject['name'], result)
                
                # Rate limiting
                if i < len(self.subjects):
                    print(f"\n[INFO] Waiting 5 seconds before next subject...")
                    time.sleep(5)
            
            except Exception as e:
                fail_count += 1
                print(f"[ERROR] Exception processing {subject['name']}: {e}")
                import traceback
                traceback.print_exc()
                self.all_reports.append({
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
        """Process one subject: Download → Analyze → Extract → Upload."""
        
        start_time = time.time()
        report = {
            'subject_name': subject['name'],
            'level': subject['level'],
            'pdf_url': subject.get('pdf_url', ''),
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
            print(f"[INFO] Downloading PDF from {subject['pdf_url']}...")
            pdf_content = self._download_pdf(subject['pdf_url'])
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
                report['error'] = "Could not find Subject Content section"
                report['issues'].append("Subject Content section not found")
                return report
            
            # PHASE 2: EXTRACT HIERARCHY
            print("[INFO] Phase 2: Extracting topic hierarchy...")
            topics_text = self._extract_hierarchy(subject, pdf_text, analysis)
            
            if not topics_text:
                report['error'] = "No topics extracted"
                report['issues'].append("Extraction returned no topics")
                return report
            
            # Parse and count topics
            parsed_topics = self._parse_hierarchy(topics_text, subject['name'])
            
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
        """Download PDF from URL."""
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            if response.content[:4] == b'%PDF':
                print(f"[OK] Downloaded PDF: {len(response.content)/1024/1024:.1f} MB")
                return response.content
            else:
                print(f"[ERROR] Downloaded content is not a PDF")
                return None
        except Exception as e:
            print(f"[ERROR] Download failed: {e}")
            return None
    
    def _extract_pdf_text(self, pdf_content: bytes) -> Optional[str]:
        """Extract text from PDF using pdfplumber."""
        try:
            import pdfplumber
        except ImportError:
            print("[ERROR] pdfplumber not installed. Run: pip install pdfplumber")
            return None
        
        print("[INFO] Extracting text from PDF...")
        
        try:
            pdf_file = BytesIO(pdf_content)
            text = ""
            
            with pdfplumber.open(pdf_file) as pdf:
                total_pages = len(pdf.pages)
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    if i % 10 == 0 and i > 0:
                        print(f"[INFO] Processed {i+1}/{total_pages} pages...")
            
            print(f"[OK] Extracted {len(text)} characters from {total_pages} pages")
            return text
            
        except Exception as e:
            print(f"[ERROR] PDF extraction failed: {e}")
            return None
    
    def _analyze_pdf_structure(self, subject: Dict, pdf_text: str) -> Dict:
        """Analyze PDF structure to understand its organization."""
        
        analysis = {
            'content_found': False,
            'has_components': False,
            'has_tiers': False,
            'has_options': False,
            'has_appendices': False,
            'components': [],
            'tiers': [],
            'options': [],
            'appendices': [],
            'structure_type': 'unknown'
        }
        
        # Look for Subject Content section (simple patterns like GCSE scraper)
        content_patterns = [
            r'2\s+SUBJECT\s+CONTENT',
            r'Subject\s+Content',
            r'Content\s+of',
            r'2\.\s+Content',
            r'2\.\d+\s+Component'  # Section 2.1 Component (if Subject Content header missing)
        ]
        
        # Debug: search for "SUBJECT" and "CONTENT" to see what's actually there
        subject_found = re.search(r'SUBJECT|Subject', pdf_text[:10000], re.IGNORECASE)
        content_found_text = re.search(r'CONTENT|Content', pdf_text[:10000], re.IGNORECASE)
        if subject_found:
            context = pdf_text[max(0, subject_found.start()-50):subject_found.end()+50]
            print(f"[DEBUG] Found 'SUBJECT' at position {subject_found.start()}: ...{context}...")
        if content_found_text:
            context = pdf_text[max(0, content_found_text.start()-50):content_found_text.end()+50]
            print(f"[DEBUG] Found 'CONTENT' at position {content_found_text.start()}: ...{context}...")
        
        for pattern in content_patterns:
            match = re.search(pattern, pdf_text, re.IGNORECASE)
            if match:
                analysis['content_found'] = True
                context = pdf_text[max(0, match.start()-50):match.end()+50]
                print(f"[DEBUG] Content section found using pattern: {pattern[:30]} at position {match.start()}")
                print(f"[DEBUG] Context: ...{context}...")
                break
        
        # Detect Components - look for "2.1 Component 1: Title" pattern specifically
        # Eduqas uses format: "2.1 Component 1: Programming and System Development"
        component_patterns = [
            r'2\.\d+\s+Component\s+(\d+)[:\s]+([A-Z][^\n]{10,80})',  # "2.1 Component 1: Title"
            r'Component\s+(\d+)[:\s]+([A-Z][^\n]{10,80})',  # "Component 1: Title" (Title starts with capital)
        ]
        
        components = []
        seen_numbers = set()
        for pattern in component_patterns:
            matches = re.finditer(pattern, pdf_text, re.IGNORECASE)
            for match in matches:
                comp_num = match.group(1)
                comp_name = match.group(2).strip()
                
                # Filter out false matches:
                # - Skip if name is just percentages/numbers (e.g., "17.5% 16% 6.5%")
                # - Skip if name is too short (less than 10 chars) - likely not a real component name
                # - Skip if name contains only digits, spaces, %, -, or common false patterns
                # - Skip if name doesn't start with capital letter (not a real title)
                if (len(comp_name) < 10 or 
                    re.match(r'^[\d\s%\-\.]+$', comp_name) or
                    '%' in comp_name or
                    not comp_name[0].isupper() or
                    comp_name.lower().startswith(('for the', 'will take', 'should be', 'must include', 'the work'))):
                    continue
                
                # Only keep first occurrence of each component number
                if comp_num not in seen_numbers:
                    seen_numbers.add(comp_num)
                    components.append({'number': comp_num, 'name': comp_name})
                    print(f"[DEBUG] Found Component {comp_num}: {comp_name[:50]}")
        
        if components:
            analysis['has_components'] = True
            analysis['components'] = components
            print(f"[INFO] Found {len(components)} components: {', '.join([f'Component {c['number']}: {c['name'][:40]}' for c in components])}")
            # If components found but no explicit "Subject Content" header, 
            # assume content exists (components indicate content section exists)
            if not analysis['content_found']:
                analysis['content_found'] = True
                print("[INFO] Content found via Component detection (no explicit Subject Content header found)")
        
        # Detect Tiers (Mathematics Foundation/Higher) - less common at A-Level but possible
        tier_patterns = [
            r'Foundation\s+tier',
            r'Higher\s+tier',
            r'Foundation\s+Tier',
            r'Higher\s+Tier'
        ]
        
        tiers = []
        for pattern in tier_patterns:
            if re.search(pattern, pdf_text, re.IGNORECASE):
                tier_name = re.search(pattern, pdf_text, re.IGNORECASE).group(0)
                if tier_name not in tiers:
                    tiers.append(tier_name)
        
        if tiers:
            analysis['has_tiers'] = True
            analysis['tiers'] = tiers
            print(f"[INFO] Found tiers: {', '.join(tiers)}")
        
        # Detect Options (Geography options, History periods)
        option_patterns = [
            r'Option\s+(\d+)[:\s]+([^\n]+)',
            r'Learners\s+should\s+study\s+one\s+of\s+these\s+options',
            r'Options?\s*[:\-]\s*([^\n]+)'
        ]
        
        options = []
        for pattern in option_patterns:
            matches = re.finditer(pattern, pdf_text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 1:
                    option_name = match.group(1).strip() if match.groups() else match.group(0)
                    if option_name not in options:
                        options.append(option_name)
        
        if options:
            analysis['has_options'] = True
            analysis['options'] = options
            print(f"[INFO] Found {len(options)} options")
        
        # Detect Appendices (English Literature prescribed texts)
        appendix_patterns = [
            r'APPENDIX\s+[A-Z]',
            r'Appendix\s+[A-Z]',
            r'Prescribed\s+texts',
            r'Text\s+list'
        ]
        
        appendices = []
        for pattern in appendix_patterns:
            if re.search(pattern, pdf_text, re.IGNORECASE):
                appendix_match = re.search(pattern, pdf_text, re.IGNORECASE)
                appendix_text = appendix_match.group(0)
                if appendix_text not in appendices:
                    appendices.append(appendix_text)
        
        if appendices:
            analysis['has_appendices'] = True
            analysis['appendices'] = appendices
            print(f"[INFO] Found appendices: {', '.join(appendices[:3])}")
        
        # Determine structure type
        if analysis['has_components']:
            analysis['structure_type'] = 'component-based'
        elif analysis['has_tiers']:
            analysis['structure_type'] = 'tier-based'
        elif analysis['has_options']:
            analysis['structure_type'] = 'option-based'
        else:
            analysis['structure_type'] = 'standard'
        
        return analysis
    
    def _extract_hierarchy(self, subject: Dict, pdf_text: str, analysis: Dict) -> Optional[str]:
        """Extract topic hierarchy using AI."""
        
        # Build extraction prompt based on analysis
        prompt = self._build_extraction_prompt(subject, pdf_text, analysis)
        
        # Call AI
        print("[INFO] Calling AI for extraction...")
        result = self._call_ai(prompt, max_tokens=16000)
        
        if result:
            print(f"[OK] AI extraction complete: {len(result)} characters")
            return result
        else:
            print("[ERROR] AI extraction failed")
            return None
    
    def _build_extraction_prompt(self, subject: Dict, pdf_text: str, analysis: Dict) -> str:
        """Build extraction prompt based on analysis."""
        
        # Find content section - Eduqas uses "2.1 Component 1" style
        content_patterns = [
            r'2\.1\s+Component\s+1',  # Eduqas: "2.1 Component 1" (most reliable)
            r'\n\s*2\s+SUBJECT\s+CONTENT',  # Generic: Section 2 SUBJECT CONTENT
            r'\n\s*2\.\s+SUBJECT\s+CONTENT',  # Generic: Section 2. SUBJECT CONTENT
            r'Component\s+1[:\s]+\w+',  # Component 1: [Title] - match actual component start
            r'(?:^|\n)Component\s+1\s*\n',  # Component 1 on its own line
        ]
        
        content_match = None
        content_start = None
        
        # For Eduqas Computer Science, look for "2 SUBJECT CONTENT" first, then "2.1 Component 1"
        # Try "2 SUBJECT CONTENT" pattern first (most reliable)
        subject_content_match = re.search(r'2\s+SUBJECT\s+CONTENT|Subject\s+Content', pdf_text, re.IGNORECASE)
        if subject_content_match:
            potential_start = subject_content_match.start()
            # Verify we're in the actual content section (should have curriculum content nearby)
            next_5000 = pdf_text[potential_start:potential_start+5000]
            # Look for typical Eduqas content indicators
            if re.search(r'Component\s+\d+|data structure|algorithm|programming|learners', next_5000, re.IGNORECASE):
                content_start = potential_start
                print(f"[DEBUG] Found 'Subject Content' section at position {content_start}")
        
        # If not found, try "2.1 Component 1" pattern (Eduqas style)
        if content_start is None:
            eduqas_pattern = r'2\.1\s+Component\s+1'
            content_match = re.search(eduqas_pattern, pdf_text)
            if content_match:
                potential_start = content_match.start()
                # Verify we're in the actual content section (should have curriculum content nearby)
                next_2000 = pdf_text[potential_start:potential_start+2000]
                # Look for typical Eduqas content indicators (bullets with content descriptions)
                if any(indicator in next_2000.lower() for indicator in ['data structure', 'algorithm', 'programming', 'learners', 'candidates should', 'describe']):
                    content_start = potential_start
                    print(f"[DEBUG] Found Eduqas '2.1 Component 1' section at position {content_start}")
        
        # Fallback to other patterns if Eduqas pattern doesn't work
        if content_start is None:
            for pattern in content_patterns:
                content_match = re.search(pattern, pdf_text, re.IGNORECASE | re.MULTILINE)
                if content_match:
                    # Verify this isn't in TOC - should have substantial content after it
                    potential_start = content_match.start()
                    # Check if there's substantial content (not just TOC entries)
                    next_5000 = pdf_text[potential_start:potential_start+5000]
                    if re.search(r'Component\s+\d+|Theme|Topic|Learners\s+should', next_5000, re.IGNORECASE):
                        content_start = potential_start
                        print(f"[DEBUG] Found content section at position {content_start} using pattern: {pattern[:40]}")
                        break
        
        if content_start is None:
            # Fallback 1: Look for "Component 1" specifically (not Component 3 which is assessment)
            if analysis.get('has_components'):
                # Look for "2.1 Component 1" or "Component 1:" with a proper title
                component1_match = re.search(r'2\.1\s+Component\s+1[:\s]+([A-Z][^\n]{10,})|Component\s+1[:\s]+([A-Z][^\n]{10,})', pdf_text, re.IGNORECASE)
                if component1_match:
                    potential_start = component1_match.start()
                    # Verify this is actual content, not assessment info
                    next_2000 = pdf_text[potential_start:potential_start+2000]
                    # Skip if it's assessment-related (Component 3, percentages, etc.)
                    if not re.search(r'Component\s+3|%\s+%\s+%|assessment|examination', next_2000, re.IGNORECASE):
                        # Look backwards for "2 SUBJECT CONTENT" or "2.1"
                        lookback = pdf_text[max(0, potential_start-1000):potential_start]
                        section_match = re.search(r'2\s+SUBJECT\s+CONTENT|2\.1\s+Component', lookback, re.IGNORECASE)
                        if section_match:
                            content_start = max(0, potential_start-1000) + section_match.start()
                        else:
                            content_start = potential_start
                        print(f"[DEBUG] Using Component 1 as content start at position {content_start}")
            
            # Fallback 2: look for any "Subject Content" but require it to have content after
            if content_start is None:
                fallback_match = re.search(r'Subject\s+Content|2\s+SUBJECT\s+CONTENT', pdf_text, re.IGNORECASE)
                if fallback_match:
                    potential_start = fallback_match.start()
                    # Check next 10000 chars for actual content
                    next_10000 = pdf_text[potential_start:potential_start+10000]
                    if len(next_10000) > 1000 and re.search(r'Component|Theme|Topic', next_10000, re.IGNORECASE):
                        content_start = potential_start
                        print(f"[DEBUG] Using fallback content section at position {content_start}")
            
            # Fallback 3: If components exist, use first component as start
            if content_start is None and analysis.get('has_components'):
                component_match = re.search(r'Component\s+\d+', pdf_text, re.IGNORECASE)
                if component_match:
                    content_start = component_match.start()
                    print(f"[DEBUG] Using first Component as content start at position {content_start}")
        
        if content_start is not None:
            # Find where content section ends (look for common end markers)
            # Only match section headers that appear AFTER substantial content
            end_markers = [
                r'\n\s*3\s+ASSESSMENT',  # Section 3: Assessment (must be at start of line)
                r'\n\s*APPENDIX\s+[A-Z]',  # Appendix headers
                r'\n\s*Appendix\s+[A-Z]',  # Appendix headers (lowercase)
                r'\n\s*GLOSSARY',  # Glossary section header
                r'\n\s*REFERENCES',  # References section header
            ]
            
            content_end = content_start + 200000  # Default: 200k chars
            # Require end markers to be at least 5000 chars after content start (avoid TOC matches)
            min_end_distance = 5000
            for marker in end_markers:
                end_match = re.search(marker, pdf_text[content_start+min_end_distance:content_start+300000], re.IGNORECASE)
                if end_match:
                    potential_end = content_start + min_end_distance + end_match.start()
                    if potential_end < content_end:
                        content_end = potential_end
                        print(f"[DEBUG] Found end marker at position {potential_end}: {marker[:50]}")
            
            content_section = pdf_text[content_start:content_end]
            print(f"[DEBUG] Content section: {len(content_section)} characters (from {content_start} to {content_end})")
            
            # Save debug snippet
            debug_file = self.reports_dir / f"{subject['name'].replace(' ', '-')}-content-section.txt"
            try:
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(content_section[:50000])  # First 50k chars
                print(f"[DEBUG] Saved content section snippet to {debug_file.name}")
            except Exception as e:
                print(f"[DEBUG] Could not save debug file: {e}")
        else:
            # Fallback: use a large section from the PDF
            content_section = pdf_text[:200000]  # First 200k chars
            print(f"[WARN] No content section found, using first 200k chars")
        
        # Build component instructions
        component_instructions = ""
        if analysis.get('has_components'):
            components = analysis.get('components', [])
            component_list = ', '.join([f"Component {c['number']}: {c['name']}" for c in components[:5]])
            component_instructions = f"""
CRITICAL: COMPONENT HANDLING
- This specification has COMPONENTS: {component_list}
- Create Level 0 topics for EACH component: "1 Component 1: [Name]", "2 Component 2: [Name]", etc.
- Extract ALL content under each component
- Components may have Core themes and Options - extract BOTH
- A-Level specifications often have more complex component structures - extract ALL components
"""
        
        # Build tier instructions
        tier_instructions = ""
        if analysis.get('has_tiers'):
            tiers = analysis.get('tiers', [])
            tier_list = ', '.join(tiers)
            tier_instructions = f"""
CRITICAL: TIER HANDLING
- This specification has TIERS: {tier_list}
- Create Level 0 topics for each tier
- Each tier will have similar Level 1 structure but different Level 2-4 content
- Extract content for ALL tiers separately
"""
        
        # Build options instructions
        options_instructions = ""
        if analysis.get('has_options'):
            options = analysis.get('options', [])
            options_list = ', '.join(options[:5])
            options_instructions = f"""
CRITICAL: OPTIONS HANDLING
- This specification has OPTIONS: {options_list}
- Extract ALL optional units/components - do NOT skip optional content
- Mark optional units clearly in the hierarchy
- Options may be under Components - extract them under the appropriate Component
- A-Level specifications often have more options - extract ALL of them
"""
        
        # Build appendices instructions
        appendices_instructions = ""
        if analysis.get('has_appendices'):
            appendices = analysis.get('appendices', [])
            appendices_list = ', '.join(appendices[:3])
            appendices_instructions = f"""
CRITICAL: APPENDICES HANDLING
- This specification has APPENDICES: {appendices_list}
- Appendices typically contain prescribed texts (English Literature) or vocabulary lists (Languages)
- For English Literature: Extract ALL prescribed texts from appendices
- For Languages: Extract vocabulary and integrate into relevant themes
- Appendices should be integrated into the main hierarchy, not separate Level 0 topics
"""
        
        # Subject-specific instructions
        subject_name = subject['name'].lower()
        subject_specific = ""
        
        if 'geography' in subject_name:
            subject_specific = """
SPECIAL INSTRUCTIONS FOR GEOGRAPHY:
- Components have Core themes (required) and Options (choose one)
- Extract ALL Core themes under each Component
- Extract ALL Options under each Component (even though students choose one)
- Options add breadth/depth to the core themes
- A-Level Geography may have more complex option structures
"""
        elif 'english' in subject_name and 'literature' in subject_name:
            subject_specific = """
SPECIAL INSTRUCTIONS FOR ENGLISH LITERATURE:
- Extract Components and Sections
- Extract ALL prescribed texts from Appendices
- Include text lists under appropriate Components/Sections
- Preserve exact text titles and authors
- A-Level may have more prescribed texts than GCSE
"""
        elif 'mathematics' in subject_name or 'maths' in subject_name:
            subject_specific = """
SPECIAL INSTRUCTIONS FOR MATHEMATICS:
- A-Level Mathematics may have different structures (Pure, Applied, Statistics, Mechanics)
- Extract content for ALL components/options separately
- Preserve mathematical notation and formulas exactly
"""
        elif any(lang in subject_name for lang in ['french', 'spanish', 'german', 'latin']):
            subject_specific = """
SPECIAL INSTRUCTIONS FOR LANGUAGES:
- Extract themes and sub-themes
- Extract vocabulary from appendices and integrate into themes
- Include grammar points where relevant
- Preserve foreign language text exactly
- A-Level languages may have more complex grammar structures
"""
        elif 'business' in subject_name:
            subject_specific = """
SPECIAL INSTRUCTIONS FOR BUSINESS:
- EXCLUDE Assessment Objectives, Assessment Weightings, and other assessment metadata from Component content
- The specification may use a two-column format: "Content" (left column) and "Amplification" (right column)
- "Content" column items = Level 2 topics (main learning objectives/statements)
- "Amplification" column items = Level 3 topics (detailed explanations/examples that clarify the Content)
- Structure: Component (Level 0) -> Theme/Topic (Level 1) -> Content statement (Level 2) -> Amplification details (Level 3)
- Only extract actual curriculum CONTENT, NOT assessment information
- Assessment Objectives (AO1, AO2, AO3) should NOT appear as topics under Component content
"""
        elif 'psychology' in subject_name:
            subject_specific = """
SPECIAL INSTRUCTIONS FOR PSYCHOLOGY:
- Extract Components and Options
- Extract research studies and theories in detail
- Include methodology and evaluation points
- A-Level Psychology often has extensive research content - extract ALL studies
"""
        elif 'sociology' in subject_name:
            subject_specific = """
SPECIAL INSTRUCTIONS FOR SOCIOLOGY:
- Extract Components and Topics
- Extract theories and research in detail
- Include evaluation and critical analysis points
- A-Level Sociology may have more theoretical depth
"""
        elif 'computer science' in subject_name:
            subject_specific = """
SPECIAL INSTRUCTIONS FOR COMPUTER SCIENCE - CRITICAL FOR DEPTH:
- The specification uses a TWO-COLUMN format:
  * LEFT COLUMN: Topic numbers and names (e.g., "1. Data structures")
  * RIGHT COLUMN: Amplification/details with multiple bullet points
- Extract structure: Component (Level 0) -> Topic number/name (Level 1) -> Each bullet point (Level 2) -> Break down complex bullet points (Level 3+) -> Sub-items (Level 4)
- Extract EVERY numbered topic (e.g., "1.", "2.", "3.", etc.) as Level 1 under each Component
- Extract EVERY bullet point from the right column as Level 2 topics
- CRITICAL: Break down complex bullet points into Level 3 and Level 4 topics:
  * If a bullet point lists multiple items separated by commas (e.g., "arrays, stacks, queues, trees, linked lists and hash tables"), create Level 3 topics for EACH item
  * If a bullet point has items in parentheses (e.g., "(up to three dimensions)"), extract the parenthesized content as Level 4 topics
  * If a bullet point uses phrases like "including", "consisting of", "such as", break down everything after these phrases into separate Level 3 topics
  * If a bullet point lists logical operations (e.g., "AND, OR, NOT, XOR, NAND and NOR"), extract EACH operation as a separate Level 3 topic
  * DO NOT stop at commas or parentheses - continue extracting ALL items in lists
- Example structure with FULL DEPTH:
  1 Component 1: Programming and System Development (Level 0)
    1.1 1. Data structures (Level 1)
      1.1.1 Describe, interpret and manipulate data structures including arrays (up to three dimensions), records, stacks, queues, trees, linked lists and hash tables (Level 2)
        1.1.1.1 Arrays (Level 3)
          1.1.1.1.1 Up to three dimensions (Level 4)
          1.1.1.1.2 One-dimensional arrays (Level 4)
          1.1.1.1.3 Two-dimensional arrays (Level 4)
          1.1.1.1.4 Three-dimensional arrays (Level 4)
        1.1.1.2 Records (Level 3)
        1.1.1.3 Stacks (Level 3)
        1.1.1.4 Queues (Level 3)
        1.1.1.5 Trees (Level 3)
        1.1.1.6 Linked lists (Level 3)
        1.1.1.7 Hash tables (Level 3)
    1.2 2. Logical operations (Level 1)
      1.2.1 Draw truth tables for Boolean expressions consisting of AND, OR, NOT, XOR, NAND and NOR logical operations (Level 2)
        1.2.1.1 AND logical operations (Level 3)
        1.2.1.2 OR logical operations (Level 3)
        1.2.1.3 NOT logical operations (Level 3)
        1.2.1.4 XOR logical operations (Level 3)
        1.2.1.5 NAND logical operations (Level 3)
        1.2.1.6 NOR logical operations (Level 3)
- CRITICAL RULE: When you see a list separated by commas or "and", extract EVERY item as a separate topic
- Extract ONLY what is explicitly written in the PDF - but break down ALL lists and complex statements into their component parts
- DO NOT create variations or extrapolate - but DO break down EVERY list item, parenthesized content, and phrase after "including"/"consisting of" into individual topics
  1.2 Logical operations
  1.2.1 Draw truth tables for Boolean expressions...
- Extract ALL content from the specification tables - do not skip any topics or bullet points
"""
        
        prompt = f"""TASK: Extract curriculum content structure from this Eduqas A-Level {subject['name']} specification PDF.

{component_instructions}
{tier_instructions}
{options_instructions}
{appendices_instructions}
{subject_specific}

STRUCTURE TO CREATE:
1. Component/Tier Name (Level 0)
   1.1 Core Theme/Topic Name (Level 1)
       1.1.1 Sub-topic name (Level 2)
           1.1.1.1 Specific content point (Level 3)
               1.1.1.1.1 Sub-point IF explicitly listed (Level 4)
   1.2 Option Name (if applicable) (Level 1)

EXTRACTION REQUIREMENTS - CRITICAL FOR DEPTH:
1. Extract ALL content that appears in the PDF text below - be thorough and complete
2. Extract content as written in the specification
3. Include ALL topics, subtopics, bullet points, and detailed content
4. A-Level specifications typically have 200-500+ topics when fully extracted with depth
5. Extract the COMPLETE hierarchy - don't stop at Level 2, continue to Level 3 and Level 4
6. CRITICAL: Break down complex statements into their component parts:
   - If a bullet point lists multiple items separated by commas (e.g., "arrays, stacks, queues, trees"), create Level 3 topics for EACH item - DO NOT stop at the first item
   - If a bullet point has items in parentheses (e.g., "(up to three dimensions)"), extract the parenthesized content as Level 4 topics
   - If a bullet point uses phrases like "including", "consisting of", "such as", break down EVERYTHING after these phrases into separate Level 3 topics
   - If a bullet point lists logical operations (e.g., "AND, OR, NOT, XOR, NAND and NOR"), extract EACH operation as a separate Level 3 topic
   - If a statement has multiple parts separated by commas or "and", extract each part as a separate topic
   - DO NOT stop extraction at commas, parentheses, or "and" - continue extracting ALL items in lists
7. Continue until ALL content from the Subject Content section is extracted with FULL DEPTH
8. For Computer Science: Expect 200-400+ topics when fully extracted (Components + Topics + Bullet points + Breakdowns)
9. Extract based on the actual structure and depth you see in the PDF - but break down complex statements
10. DO NOT stop at Level 2 - always look for opportunities to create Level 3 and Level 4 topics

HIERARCHY STRUCTURE - CRITICAL NUMBERING:
Level 0: Components/Tiers - numbered as "1", "2", "3"
Level 1: Main topics/themes - numbered as "1.1", "1.2", "2.1", "2.2"
Level 2: Sub-topics - numbered as "1.1.1", "1.1.2", "2.1.1"
Level 3: Content points/details - numbered as "1.1.1.1", "1.1.1.2"
Level 4: Sub-points (if nested) - numbered as "1.1.1.1.1", "1.1.1.1.2"

CORRECT NUMBERING EXAMPLE:
1 Component 1: Programming
1.1 Data structures
1.1.1 Arrays
1.1.1.1 One-dimensional arrays
1.1.1.2 Two-dimensional arrays
1.1.2 Stacks
1.1.3 Queues
1.2 Algorithms
1.2.1 Searching algorithms
1.2.1.1 Linear search
1.2.1.2 Binary search

EXTRACTION RULES - CRITICAL FOR EDUQAS:
- Eduqas specifications use TABLES with numbered topics and bullet point descriptions
- Extract EVERY numbered item from tables (e.g., "1. Data structures", "2. Logical operations") as Level 1 topics
- Extract EVERY bullet point under each numbered item as Level 2+ topics
- Tables format: Left side has numbered topics, Right side has "Learners should..." bullet points
- Example from table:
  | 1. Data structures | • Describe, interpret and manipulate data structures...
                        | • Describe the manipulation of records and arrays
                        | • Represent the operation of stacks and queues...
  Extract as:
  1.1 Data structures
  1.1.1 Describe, interpret and manipulate data structures...
  1.1.2 Describe the manipulation of records and arrays
  1.1.3 Represent the operation of stacks and queues...
- Continue until ALL numbered topics and ALL bullet points are extracted
- Do NOT skip any table rows or bullet points

EXCLUDE:
- Assessment Objectives, Assessment Weightings, Summary of Assessment
- Metadata sections, page numbers, headers, footers
- Content that is not part of the Subject Content section

VALIDATION:
- Ensure you've extracted ALL content from the Subject Content section
- A-Level specifications vary in depth: simple subjects = 100-200 topics, detailed subjects = 300-500 topics
- Each topic should correspond to actual content in the PDF
- Don't stop early - extract the complete hierarchy at all depth levels

OUTPUT FORMAT:
Use numbered hierarchy (1, 1.1, 1.1.1, 1.1.1.1, etc.)
Output ONLY the numbered hierarchy, nothing else.

PDF CONTENT:
{content_section[:250000]}"""

        return prompt
    
    def _call_ai(self, prompt: str, max_tokens: int = 20000) -> Optional[str]:
        """Call AI API for extraction."""
        
        system_message = """You are an expert at extracting curriculum content from specification documents. 

CRITICAL RULES FOR DEPTH:
1. Extract ALL content from the Subject Content section - be thorough and complete
2. Extract content as written in the specification
3. Create a proper numbered hierarchy (Level 0-4+) based on the document structure
4. Include ALL topics, subtopics, bullet points, and detailed content items
5. A-Level specifications typically require 200-500+ topics for complete extraction with full depth
6. Continue extraction until all content from the Subject Content section is captured
7. CRITICAL: Break down complex statements into their component parts:
   - Lists of items separated by commas (e.g., "arrays, stacks, queues, trees, linked lists and hash tables") → create Level 3 topic for EACH item - extract ALL items, not just the first few
   - Items in parentheses (e.g., "(up to three dimensions)") → extract as Level 4 topics
   - Phrases like "including", "consisting of", "such as" → break down EVERYTHING after these phrases into separate Level 3 topics
   - Logical operations lists (e.g., "AND, OR, NOT, XOR, NAND and NOR") → extract EACH operation as separate Level 3 topic
   - Complex bullet points with multiple concepts → break into Level 3/4 topics
   - Statements with multiple parts separated by commas or "and" → extract each part as separate topic
8. DO NOT stop at Level 2 - always create Level 3 and Level 4 topics when content supports it
9. DO NOT stop extraction at commas, parentheses, or "and" - continue extracting ALL items in lists until the end
10. For Computer Science: Each bullet point should be broken down into 5-15+ sub-topics depending on complexity - extract EVERY item in lists"""
        
        if AI_PROVIDER == "openai":
            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.1  # Lower temperature to reduce hallucination
                )
                result = response.choices[0].message.content
                
                # Validate result - check for potential issues
                if result:
                    lines = [l.strip() for l in result.split('\n') if l.strip()]
                    topic_lines = [l for l in lines if re.match(r'^\d+(?:\.\d+)*\.?\s+', l)]
                    print(f"[INFO] AI extracted {len(topic_lines)} topics")
                    
                    # Only warn if truly excessive (1000+), don't limit
                    if len(topic_lines) > 1000:
                        print(f"[WARN] Very high topic count ({len(topic_lines)}) - verify extraction quality")
                
                return result
            except Exception as e:
                print(f"[ERROR] OpenAI API error: {e}")
                return None
        
        elif AI_PROVIDER == "anthropic":
            try:
                message = claude.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=max_tokens,
                    temperature=0.1,  # Lower temperature to reduce hallucination
                    system=system_message,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                result = message.content[0].text
                
                # Validate result - check for potential issues
                if result:
                    lines = [l.strip() for l in result.split('\n') if l.strip()]
                    topic_lines = [l for l in lines if re.match(r'^\d+(?:\.\d+)*\.?\s+', l)]
                    print(f"[INFO] AI extracted {len(topic_lines)} topics")
                    
                    # Only warn if truly excessive (1000+), don't limit
                    if len(topic_lines) > 1000:
                        print(f"[WARN] Very high topic count ({len(topic_lines)}) - verify extraction quality")
                
                return result
            except Exception as e:
                print(f"[ERROR] Anthropic API error: {e}")
                return None
        
        return None
    
    def _parse_hierarchy(self, topics_text: str, subject_name: str) -> List[Dict]:
        """Parse numbered hierarchy text into topic dictionaries."""
        
        topics = []
        lines = topics_text.strip().split('\n')
        
        # Generate subject code (simplified - you may want to use actual codes)
        subject_code = self._generate_subject_code(subject_name)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Match numbered hierarchy (1, 1.1, 1.1.1, etc.)
            match = re.match(r'^(\d+(?:\.\d+)*)\.?\s+(.+)$', line)
            if match:
                number = match.group(1)
                title = match.group(2).strip()
                
                # Determine level (count dots)
                level = number.count('.')
                
                # Generate topic code
                code = f"{subject_code}-{number.replace('.', '-')}"
                
                # Find parent
                parent = None
                if '.' in number:
                    parent_parts = number.rsplit('.', 1)[0]
                    parent_code = f"{subject_code}-{parent_parts.replace('.', '-')}"
                    parent = parent_code
                
                topics.append({
                    'code': code,
                    'title': title,
                    'level': level,
                    'parent': parent,
                    'subject': subject_name,
                    'exam_board': 'WJEC',  # Eduqas is part of WJEC
                    'qualification': 'A-Level'
                })
        
        return topics
    
    def _generate_subject_code(self, subject_name: str) -> str:
        """Generate a subject code from subject name."""
        # Simplified - you may want to use actual Eduqas codes
        name_parts = subject_name.upper().replace(' AND ', ' ').split()
        code = ''.join([part[0] for part in name_parts[:3]])
        return f"EDUQAS-{code}"
    
    def _self_assess(self, subject: Dict, analysis: Dict, topics: List[Dict], level_counts: Dict) -> Dict:
        """Generate self-assessment report."""
        
        issues = []
        warnings = []
        grade = 100
        
        # Check topic count - flag unusual counts
        if len(topics) > 800:
            warnings.append(f"Very high topic count ({len(topics)}) - verify extraction quality")
            grade -= 15
        elif len(topics) < 20:
            issues.append("Very few topics extracted")
            grade -= 30
        elif len(topics) < 50:
            warnings.append("Relatively few topics extracted - A-Level typically has 50-300 topics")
            grade -= 10
        
        # Check levels
        if 0 not in level_counts:
            issues.append("No Level 0 topics (Components/Tiers)")
            grade -= 20
        
        max_level = max(level_counts.keys()) if level_counts else 0
        
        if max_level < 3:
            issues.append("Shallow hierarchy (max level < 3)")
            grade -= 20
        elif max_level < 4:
            warnings.append("No Level 4+ topics extracted - may be missing deeper detail (critical for A-Level)")
            grade -= 15
        elif max_level >= 4:
            # Reward deep extraction
            level_4_count = level_counts.get(4, 0)
            level_5_count = level_counts.get(5, 0)
            if level_4_count > 0 or level_5_count > 0:
                # Good depth extraction
                pass
            else:
                warnings.append("Level 4+ structure exists but no Level 4+ topics extracted")
                grade -= 10
        
        # Check for components/tiers if detected
        if analysis.get('has_components') and level_counts.get(0, 0) < len(analysis.get('components', [])):
            warnings.append("Not all components extracted")
            grade -= 15
        
        if analysis.get('has_tiers') and level_counts.get(0, 0) < 2:
            issues.append("Tiers not properly extracted")
            grade -= 25
        
        grade = max(0, grade)
        
        return {
            'grade': grade,
            'issues': issues,
            'warnings': warnings
        }
    
    def _upload_topics(self, subject: Dict, topics: List[Dict]) -> bool:
        """Upload topics to Supabase staging tables."""
        
        if not topics:
            return False
        
        try:
            # Generate subject code (simplified - you may want to use actual Eduqas codes)
            subject_code = self._generate_subject_code(subject['name'])
            
            # Upsert subject to staging_aqa_subjects
            print(f"[INFO] Upserting subject to staging_aqa_subjects...")
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': subject['name'],  # Don't add "(A-Level)" - qualification_type already indicates this
                'subject_code': subject_code,
                'qualification_type': 'A-Level',
                'specification_url': subject.get('pdf_url', ''),  # PDF URL goes in specification_url
                'exam_board': 'EDUQAS'
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            if not subject_result.data:
                print("[ERROR] Failed to create/update subject")
                return False
            
            subject_id = subject_result.data[0]['id']
            print(f"[OK] Subject ID: {subject_id}")
            
            # Clear old topics for this subject
            print(f"[INFO] Clearing old topics...")
            supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).eq('exam_board', 'EDUQAS').execute()
            
            # Remove duplicates by code
            seen_codes = set()
            unique_topics = []
            for t in topics:
                code = t.get('code', '')
                if code and code not in seen_codes:
                    seen_codes.add(code)
                    unique_topics.append(t)
            
            print(f"[INFO] After deduplication: {len(unique_topics)} unique topics from {len(topics)} total")
            
            # Prepare topics for insertion
            to_insert = [{
                'subject_id': subject_id,
                'topic_code': t.get('code', ''),
                'topic_name': t.get('title', ''),
                'topic_level': t.get('level', 0),
                'exam_board': 'EDUQAS'
            } for t in unique_topics]
            
            # Insert topics in batches
            BATCH_SIZE = 500
            all_inserted = []
            
            print(f"[INFO] Inserting {len(to_insert)} topics in batches of {BATCH_SIZE}...")
            for i in range(0, len(to_insert), BATCH_SIZE):
                batch = to_insert[i:i+BATCH_SIZE]
                try:
                    inserted = supabase.table('staging_aqa_topics').insert(batch).execute()
                    all_inserted.extend(inserted.data)
                    print(f"[OK] Inserted batch {i//BATCH_SIZE + 1}: {len(inserted.data)} topics")
                except Exception as e:
                    print(f"[ERROR] Batch {i//BATCH_SIZE + 1} failed: {e}")
                    # Try inserting one by one to find the problem
                    for item in batch:
                        try:
                            single_insert = supabase.table('staging_aqa_topics').insert([item]).execute()
                            all_inserted.extend(single_insert.data)
                        except Exception as e2:
                            print(f"[ERROR] Failed to insert topic {item.get('topic_code', 'unknown')}: {e2}")
            
            print(f"[OK] Successfully inserted {len(all_inserted)} topics")
            
            # Link parent relationships using batched upserts
            code_to_id = {t['topic_code']: t['id'] for t in all_inserted}
            linked_count = 0
            failed_links = 0
            
            print(f"[INFO] Linking parent-child relationships...")
            # Collect all updates first
            updates_to_apply = []
            for topic in unique_topics:
                if topic.get('parent'):
                    parent_id = code_to_id.get(topic['parent'])
                    child_id = code_to_id.get(topic.get('code', ''))
                    if parent_id and child_id:
                        updates_to_apply.append({
                            'id': child_id,
                            'parent_topic_id': parent_id
                        })
                    else:
                        failed_links += 1
            
            # Link parent relationships (same approach as all other scrapers)
            if updates_to_apply:
                print(f"[INFO] Linking {len(updates_to_apply)} parent-child relationships...")
                for update in updates_to_apply:
                    try:
                        supabase.table('staging_aqa_topics').update({
                            'parent_topic_id': update['parent_topic_id']
                        }).eq('id', update['id']).execute()
                        linked_count += 1
                    except Exception as e:
                        failed_links += 1
                
                print(f"[OK] Linked {linked_count} parent-child relationships")
            
            if failed_links > 0:
                print(f"[WARN] {failed_links} parent-child relationships failed to link")
            print(f"[OK] Successfully uploaded {len(all_inserted)} topics to staging")
            return True
            
        except Exception as e:
            print(f"[ERROR] Database upload failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _save_report(self, subject_name: str, report: Dict):
        """Save individual report."""
        safe_name = re.sub(r'[^\w\s-]', '', subject_name).replace(' ', '-')
        report_file = self.reports_dir / f"{safe_name}-report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"[INFO] Report saved to {report_file.name}")
    
    def _save_pdf_url_to_file(self, subject_name: str, level: str, subject_page_url: str, pdf_url: str):
        """Save PDF URL to the JSON file for future use."""
        try:
            # Load existing data
            pdf_urls_data = {}
            if PDF_URLS_FILE.exists():
                try:
                    with open(PDF_URLS_FILE, 'r', encoding='utf-8') as f:
                        pdf_urls_data = json.load(f)
                except:
                    pass
            
            # Add or update this subject
            key = f"{subject_name} - {level}"
            pdf_urls_data[key] = {
                'subject': subject_name,
                'level': level,
                'subject_page_url': subject_page_url,
                'pdf_url': pdf_url
            }
            
            # Save back to file
            with open(PDF_URLS_FILE, 'w', encoding='utf-8') as f:
                json.dump(pdf_urls_data, f, indent=2, ensure_ascii=False)
            
            print(f"[INFO] Saved PDF URL to {PDF_URLS_FILE.name}")
        except Exception as e:
            print(f"[WARN] Could not save PDF URL to file: {e}")
    
    def _generate_summary_report(self, success_count: int, fail_count: int):
        """Generate summary report."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        summary_file = self.reports_dir / f"summary-{timestamp}.json"
        
        summary = {
            'timestamp': timestamp,
            'total_subjects': len(self.subjects),
            'success_count': success_count,
            'fail_count': fail_count,
            'success_rate': success_count / len(self.subjects) * 100 if self.subjects else 0,
            'reports': self.all_reports
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n[INFO] Summary report saved to {summary_file.name}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Eduqas A-Level Universal Scraper')
    parser.add_argument('--subject', type=str, help='Filter by subject name')
    parser.add_argument('--limit', type=int, help='Limit number of subjects to process')
    
    args = parser.parse_args()
    
    scraper = EduqasALevelUniversalScraper()
    success = scraper.scrape_all(subject_filter=args.subject, limit=args.limit)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
