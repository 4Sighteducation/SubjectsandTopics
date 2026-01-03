"""
Edexcel A-Level - Universal Topic Scraper
Intelligently parses different PDF structures

Handles:
- Topics with numbered items (Biology style: 1.1, 1.2, i), ii))
- Topics with sub-topics (Chemistry style: Topic 2A, Topic 15B)
- Topics with learning outcomes
- 3-4 level hierarchies

Usage:
    python scrape-edexcel-universal.py <subject_code> <subject_name> <pdf_url>
"""

import os
import sys
import re
import requests
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv
from supabase import create_client

# Try to import PDF library
try:
    from pypdf import PdfReader
    PDF_LIBRARY = 'pypdf'
except ImportError:
    try:
        import PyPDF2
        PdfReader = PyPDF2.PdfReader
        PDF_LIBRARY = 'PyPDF2'
    except ImportError:
        print("❌ No PDF library found! Install with: pip install pypdf")
        sys.exit(1)

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

# NOTE: Avoid printing non-ASCII at import time (Windows consoles may default to cp1252).


def download_pdf(url, subject_code):
    """Download PDF and extract text."""
    print(f"\n[INFO] Downloading PDF...")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        print(f"[OK] Downloaded {len(response.content):,} bytes")
        
        # Parse PDF
        print("[INFO] Extracting text from PDF...")
        pdf_file = BytesIO(response.content)
        reader = PdfReader(pdf_file)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        print(f"[OK] Extracted {len(text):,} characters from {len(reader.pages)} pages")
        
        # Save for debugging
        debug_path = Path(__file__).parent / f"debug-{subject_code.lower()}-spec.txt"
        debug_path.write_text(text, encoding='utf-8')
        print(f"   Saved to {debug_path.name}")
        
        return text
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        raise


def detect_structure(text):
    """Analyze PDF to detect its structure."""
    print("\n[INFO] Analyzing PDF structure...")
    
    lines = text.split('\n')
    
    # Count different patterns
    patterns = {
        'topics': 0,          # Topic X:
        'sub_topics': 0,      # Topic XA:, Topic XB:
        'papers': 0,          # Paper X:
        'numbered_items': 0,  # 1.1, 1.2, 2.3
        'three_part_items': 0, # 1.1.1, 2.3.4
        'deep_items': 0,      # 1.1.1.1+ (rare, but exists in some specs)
        'roman_items': 0,     # i), ii), iii)
        'lettered_items': 0,  # a), b), c)
        'learning_outcomes': 0 # "be able to", "know that"
    }
    
    for line in lines[:3000]:  # First 3000 lines
        line = line.strip()
        
        # Topics
        if re.match(r'^Topic\s+(\d+):\s+', line):
            patterns['topics'] += 1
        
        # Sub-topics (Topic 2A:, Topic 15B:)
        if re.match(r'^Topic\s+(\d+[A-Z]):\s+', line):
            patterns['sub_topics'] += 1
        
        # Papers
        if re.match(r'^Paper\s+(\d+):\s+', line):
            patterns['papers'] += 1
        
        # Numbered items (1.1, 1.2)
        if re.match(r'^(\d+)\.(\d+)\s+', line):
            patterns['numbered_items'] += 1

        # Three-part numeric items (1.1.1)
        if re.match(r'^(\d+)\.(\d+)\.(\d+)\b', line):
            patterns['three_part_items'] += 1

        # Deeper numeric items (1.1.1.1 etc)
        if re.match(r'^\d+(?:\.\d+){3,}\b', line):
            patterns['deep_items'] += 1
        
        # Roman numerals (i), ii))
        if re.match(r'^([ivx]+)\)\s+', line, re.IGNORECASE):
            patterns['roman_items'] += 1
        
        # Learning outcomes
        if re.match(r'^\d+\.\s+(be able to|know that|understand)', line, re.IGNORECASE):
            patterns['learning_outcomes'] += 1
    
    print("   Pattern detection:")
    for pattern, count in patterns.items():
        if count > 0:
            print(f"   - {pattern}: {count}")
    
    return patterns


def parse_topics_universal(text, subject_code, subject_name):
    """Universal parser that adapts to PDF structure."""
    print("\n[INFO] Parsing topics...")
    
    topics = []
    lines = text.split('\n')

    def build_topic_to_paper_map(lines_list):
        """
        Some Edexcel specs don't restate paper structure in the main content; instead it appears in
        "Paper X" overview boxes with an "Overview of content" section listing Topic N: ...

        This pass attempts to discover Topic->Paper mapping from those overview blocks so we can
        parent Topic* nodes under Paper1/Paper2/Paper3 correctly.
        """
        topic_to_paper = {}
        current_paper_local = None
        in_overview = False

        for raw in lines_list:
            line0 = (raw or "").strip()
            if not line0:
                continue

            # Paper header
            # - Psychology-style: "Paper 2: Applications of psychology *Paper code: 9PS0/02"
            # - Geography-style:  "Paper 2 (Paper code: 9GE0/02)"
            m_paper = re.match(r'^Paper\s+(\d+)\b', line0)
            if m_paper:
                current_paper_local = f"Paper{m_paper.group(1)}"
                in_overview = False
                continue

            # Enter / exit overview-of-content section
            # Geography uses "Content overview1" (no word-boundary after "overview"), so use substring checks.
            if ("Overview of content" in line0) or ("Content overview" in line0):
                in_overview = True
                continue
            if ("Overview of assessment" in line0) or ("Assessment overview" in line0):
                in_overview = False
                continue

            if not in_overview or not current_paper_local:
                continue

            # Topics listed inside the overview:
            # - Psychology-style bullets: "• Topic 6: Criminological psychology"
            # - Geography-style bullets:  "● Area of study 2, Topic 3: Globalisation"
            # Also sometimes "Topic 2A:" appears, but our Topic nodes are Topic2 etc; we map numeric part.
            m_topic = re.search(r'\bTopic\s+(\d+)([A-Z])?(?::|\b)', line0)
            if m_topic:
                tn = m_topic.group(1)
                key = f"Topic{tn}"
                # Some specs list the same topic under multiple papers (e.g., Biology B topics 1-4 in Paper 1 and Paper 2).
                # We keep the FIRST assignment to avoid bouncing topics around and accidentally dumping everything under Paper3.
                if key not in topic_to_paper:
                    topic_to_paper[key] = current_paper_local

        return topic_to_paper

    topic_to_paper = build_topic_to_paper_map(lines)
    
    # Detect structure
    structure = detect_structure(text)
    
    # Parse Papers (Level 0)
    papers_found = []
    for i, line in enumerate(lines):
        line = line.strip()
        paper_match = re.match(r'^Paper\s+(\d+):\s+(.+)', line)
        if paper_match:
            paper_num = paper_match.group(1)
            paper_title = paper_match.group(2).strip()
            # Clean up paper title (remove continuation)
            if len(paper_title) > 100:
                paper_title = paper_title[:100].rsplit(' ', 1)[0] + '...'
            
            paper_code = f'Paper{paper_num}'
            if paper_code not in [p['code'] for p in papers_found]:
                papers_found.append({
                    'code': paper_code,
                    'title': f'Paper {paper_num}: {paper_title}',
                    'level': 0,
                    'parent': None
                })
                print(f"   [OK] Found {paper_code}: {paper_title[:50]}")
    
    topics.extend(papers_found)
    
    # Parse Topics (Level 1)
    topic_pattern_found = {}
    current_topic = None
    current_subtopic = None
    current_paper = None  # Paper1/Paper2/Paper3 while scanning contents
    # Geography (and similar) has optional subtopics like 2A/2B, 4A/4B, 8A/8B
    current_option = None  # e.g., "2A", "2B", "4A" ...
    # Track last numeric code seen by depth so we can parent deeper codes correctly (e.g., 1.1.1 under 1.1)
    last_numeric_by_depth = {}  # depth(int) -> code(str)
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line or len(line) < 5:
            i += 1
            continue
        
        # Skip unwanted sections
        if any(skip in line for skip in ['CORE PRACTICAL', 'Appendix', 'Assessment Objectives', 
                                          'Sample assessment', 'administration']):
            i += 1
            continue

        # Track which paper we're currently within (helps attach Topic1..Topic9 to Paper1/2/3 correctly)
        # This typically appears in the contents section, e.g. "Paper 2: Applications of psychology"
        paper_section_match = re.match(r'^Paper\s+(\d+):\s+(.+)', line)
        if paper_section_match:
            paper_num = paper_section_match.group(1)
            current_paper = f'Paper{paper_num}'
            i += 1
            continue
        
        # Pattern 1: Main Topics (Topic X:)
        topic_match = re.match(r'^Topic\s+(\d+):\s+(.+)', line)
        if topic_match:
            topic_num = topic_match.group(1)
            topic_title = topic_match.group(2).strip()
            
            # Clean up title
            # Avoid aggressive truncation; long titles are meaningful in curriculum
            if len(topic_title) > 500:
                topic_title = topic_title[:500].rsplit(' ', 1)[0] + '...'
            
            topic_code = f'Topic{topic_num}'
            current_topic = topic_code
            current_subtopic = None
            last_numeric_by_depth = {}

            # Avoid inserting duplicate Topic nodes (PDFs often repeat contents headings),
            # BUT keep the context update above so numeric items attach to the correct Topic.
            if topic_code in topic_pattern_found:
                i += 1
                continue
            
            # Determine parent (Paper 1, 2, or 3)
            # Prefer the Paper section currently being scanned (from contents); fallback to Paper1.
            parent = topic_to_paper.get(topic_code) or current_paper or 'Paper1'
            
            topics.append({
                'code': topic_code,
                'title': f'Topic {topic_num}: {topic_title}',
                'level': 1,
                'parent': parent
            })
            
            topic_pattern_found[topic_code] = True
            print(f"   [OK] Topic {topic_num}: {topic_title[:60]}")
            i += 1
            continue
        
        # Pattern 2: Sub-topics (Topic 2A:, Topic 15B:)
        subtopic_match = re.match(r'^Topic\s+(\d+)([A-Z]):\s+(.+)', line)
        if subtopic_match:
            topic_num = subtopic_match.group(1)
            letter = subtopic_match.group(2)
            subtopic_title = subtopic_match.group(3).strip()
            
            if len(subtopic_title) > 500:
                subtopic_title = subtopic_title[:500].rsplit(' ', 1)[0] + '...'
            
            subtopic_code = f'Topic{topic_num}{letter}'
            parent_topic = f'Topic{topic_num}'
            current_subtopic = subtopic_code
            current_option = f"{topic_num}{letter}"
            last_numeric_by_depth = {}
            
            topics.append({
                'code': subtopic_code,
                'title': f'Topic {topic_num}{letter}: {subtopic_title}',
                'level': 2,
                'parent': parent_topic
            })
            
            print(f"      - {subtopic_code}: {subtopic_title[:50]}")
            i += 1
            continue

        # Geography-style option headers appear as "Option 2A: Glaciated Landscapes and Change"
        option_match = re.match(r'^(Option\s+)?(\d+)([A-Z])[:\s]+(.+)$', line)
        if option_match:
            opt_num = option_match.group(2)
            opt_letter = option_match.group(3)
            opt_title = option_match.group(4).strip()
            opt_code = f"{opt_num}{opt_letter}"
            # Attach option to its parent Topic (e.g., 2A under Topic2)
            parent_topic_code = f"Topic{opt_num}"
            option_node_code = f"Topic{opt_code}"
            current_option = opt_code
            current_subtopic = option_node_code
            last_numeric_by_depth = {}

            if option_node_code not in topic_pattern_found:
                topics.append({
                    'code': option_node_code,
                    'title': f"Option {opt_code}: {opt_title}",
                    'level': 2,
                    'parent': parent_topic_code
                })
                topic_pattern_found[option_node_code] = True
            i += 1
            continue
        
        # Pattern 3: Numeric hierarchy items (1.1, 1.1.1, 1.1.1.1...) - common in table-based subjects (e.g., Psychology)
        # Only parse numeric codes when we're inside a topic context.
        if current_topic and (structure['numbered_items'] > 10 or structure['three_part_items'] > 10 or structure['deep_items'] > 0):
            numeric_match = re.match(r'^(?P<code>\d+(?:\.\d+){1,6})(?:\s+|$)(?P<rest>.*)$', line)
            if numeric_match:
                code = numeric_match.group('code').strip()
                rest = (numeric_match.group('rest') or '').strip()

                # Filter out common stats-table artifacts like 0.05 / 0.10 etc.
                try:
                    major_int = int(code.split('.')[0])
                except Exception:
                    major_int = 1
                if major_int == 0:
                    i += 1
                    continue

                def is_geog_assessment_junk(text: str) -> bool:
                    t = (text or "").strip()
                    if not t:
                        return False
                    if "Total for GCE" in t or "Synoptic assessment" in t:
                        return True
                    # Lots of digits is a strong indicator of assessment mark/weight tables.
                    if re.match(r'^\d', t) and len(re.findall(r'\d', t)) >= 8:
                        return True
                    return False

                # Filter out assessment table artifacts (common in Geography), e.g. "2.5 15 20 Total for GCE A Level ..."
                if is_geog_assessment_junk(rest):
                    i += 1
                    continue

                parts = code.split('.')
                depth = len(parts)  # 2 => 1.1, 3 => 1.1.1, etc.

                def split_bullets(text_blob: str):
                    """
                    Split a blob that may contain bullet markers into bullet items.
                    Returns (prefix, items) where prefix is any leading non-bullet text.
                    """
                    s = (text_blob or "").strip()
                    if not s:
                        return "", []

                    # Normalize common bullet chars to "●"
                    s = s.replace("•", "●")

                    if "●" not in s:
                        return s, []

                    before, after = s.split("●", 1)
                    prefix = before.strip()
                    raw_items = ["●" + after]

                    # Split remaining bullets
                    joined = "●".join(raw_items)
                    items = [p.strip() for p in joined.split("●") if p.strip()]
                    return prefix, items

                def split_lettered_subpoints(text_blob: str):
                    """
                    Split a blob that contains lettered subpoints like:
                      "Physical processes... a. Earthquake... b. Volcanoes... c. Tsunamis..."
                    Returns (prefix, items) where items are list of (letter, text).
                    """
                    s = (text_blob or "").strip()
                    if not s:
                        return "", []
                    # Normalize whitespace
                    s = " ".join(s.split())
                    # Match "a. The ..." where next token begins with uppercase to avoid matching "e.g."
                    hits = list(re.finditer(r"\b([a-z])\.\s+(?=[A-Z])", s))
                    if not hits:
                        return s, []
                    prefix = s[: hits[0].start()].strip()
                    items = []
                    for idx, hit in enumerate(hits):
                        letter = hit.group(1)
                        start = hit.end()
                        end = hits[idx + 1].start() if idx + 1 < len(hits) else len(s)
                        chunk = s[start:end].strip()
                        if chunk:
                            items.append((letter, chunk))
                    return prefix, items

                def split_roman_subpoints(text_blob: str):
                    """
                    Split a blob that contains roman numeral subpoints like:
                      "Carbohydrates i Know ... ii Know ... iii Understand ..."
                    Returns (prefix, items) where items are list of (roman, text).
                    """
                    s = (text_blob or "").strip()
                    if not s:
                        return "", []
                    s = " ".join(s.split())
                    roman_re = r"(?:i|ii|iii|iv|v|vi|vii|viii|ix|x)"
                    # Require next token to begin with uppercase to avoid matching e.g. i.e.
                    hits = list(re.finditer(rf"(?:(?<=^)|(?<=\s))({roman_re})\s+(?=[A-Z])", s))
                    if not hits:
                        return s, []
                    prefix = s[: hits[0].start()].strip()
                    items = []
                    for idx, hit in enumerate(hits):
                        roman = hit.group(1)
                        start = hit.end()
                        end = hits[idx + 1].start() if idx + 1 < len(hits) else len(s)
                        chunk = s[start:end].strip()
                        if chunk:
                            items.append((roman, chunk))
                    return prefix, items

                def is_new_pattern(s: str) -> bool:
                    s = (s or '').strip()
                    if not s:
                        return False
                    if re.match(r'^Topic\s+\d+', s):
                        return True
                    if re.match(r'^\d+(?:\.\d+){1,6}\b', s):
                        return True
                    if re.match(r'^[ivx]+\)\s+', s, re.IGNORECASE):
                        return True
                    return False

                def append_bullet(bullets: list, line_text: str) -> None:
                    """Append a bullet line, merging wrapped continuation lines into the previous bullet."""
                    if not line_text:
                        return
                    s = line_text.replace("•", "●").strip()
                    if not s:
                        return
                    if s.startswith("●"):
                        bullets.append(s.lstrip("●").strip())
                    else:
                        # Continuation of previous bullet (line-wrapped in PDF extraction)
                        if bullets:
                            bullets[-1] = (bullets[-1] + " " + s).strip()
                        else:
                            bullets.append(s)

                # If title is on following lines (code-only line), collect a few lines forward.
                if not rest:
                    title_lines = []
                    bullet_items = []
                    j = i + 1
                    # Allow more lines here because some headings are followed by a long bullet list.
                    while j < len(lines) and (len(title_lines) < 40) and (len(bullet_items) < 60):
                        nxt = (lines[j] or '').strip()
                        if is_new_pattern(nxt):
                            break
                        # Bullet lines should become child rows, not be appended into the parent title.
                        if nxt.startswith(("●", "•")):
                            append_bullet(bullet_items, nxt)
                            j += 1
                            continue
                        # Wrapped bullet continuation lines (no leading bullet) should attach to last bullet if we’re in a list.
                        if bullet_items and nxt and len(nxt) > 2:
                            append_bullet(bullet_items, nxt)
                            j += 1
                            continue
                        if nxt and len(nxt) > 2:
                            title_lines.append(nxt)
                        j += 1
                    rest = ' '.join(title_lines).strip()
                    i = j
                    if is_geog_assessment_junk(rest):
                        continue
                else:
                    # Multi-line continuation (but STOP when a deeper numeric code begins!)
                    content_parts = [rest]
                    bullet_items = []
                    j = i + 1
                    while j < len(lines) and (len(content_parts) < 40) and (len(bullet_items) < 60):
                        nxt = (lines[j] or '').strip()
                        if is_new_pattern(nxt):
                            break
                        if not nxt or len(nxt) < 3:
                            j += 1
                            continue
                        if nxt.startswith(("●", "•")):
                            append_bullet(bullet_items, nxt)
                            j += 1
                            continue
                        # Wrapped bullet continuation lines
                        if bullet_items and nxt and len(nxt) > 2:
                            append_bullet(bullet_items, nxt)
                            j += 1
                            continue
                        content_parts.append(nxt)
                        j += 1
                    rest = ' '.join(content_parts).strip()
                    i = j
                    if is_geog_assessment_junk(rest):
                        continue

                # Special case: some PDFs embed deeper codes on the SAME LINE as the 2-part code (Psychology does this).
                # Example: "1.1 Content Obedience 1.1.1 Theories of obedience ... 1.1.2 Research into obedience ..."
                if depth == 2 and rest:
                    embedded = list(re.finditer(r'\b(\d+\.\d+\.\d+(?:\.\d+)*)\b', rest))
                    if embedded:
                        first = embedded[0].start()
                        section_title = rest[:first].strip()
                        rest_after = rest[first:].strip()

                        # Create the 2-part row with the pre-embedded title.
                        parent_for_2 = current_subtopic if current_subtopic else current_topic
                        topics.append({
                            'code': code,
                            'title': section_title or rest,  # fallback if split yields empty
                            'level': 2 if not current_subtopic else 3,
                            'parent': parent_for_2
                        })
                        last_numeric_by_depth = {2: code}

                        # Now split embedded subcodes into child rows.
                        # Build segments: [(subcode, subtitle_text), ...]
                        sub_hits = list(re.finditer(r'\b(\d+\.\d+\.\d+(?:\.\d+)*)\b', rest_after))
                        for idx, hit in enumerate(sub_hits):
                            subcode = hit.group(1)
                            start = hit.end()
                            end = sub_hits[idx + 1].start() if idx + 1 < len(sub_hits) else len(rest_after)
                            subtitle = rest_after[start:end].strip()
                            if not subtitle:
                                continue
                            sub_depth = len(subcode.split('.'))
                            # If subtitle contains bullets, keep the heading as the row title and emit bullets as children.
                            sub_prefix, sub_bullets = split_bullets(subtitle)
                            topics.append({
                                'code': subcode,
                                'title': sub_prefix or subtitle,
                                'level': 3 if not current_subtopic else 4,
                                'parent': code
                            })
                            last_numeric_by_depth[sub_depth] = subcode
                            if sub_bullets:
                                for b_idx, b_item in enumerate(sub_bullets, 1):
                                    topics.append({
                                        'code': f"{subcode}.{b_idx}",
                                        'title': b_item,
                                        'level': 4 if not current_subtopic else 5,
                                        'parent': subcode
                                    })
                        continue

                # Normal numeric handling (no embedded deeper codes on same line)
                if depth == 2:
                    parent_for_2 = current_subtopic if current_subtopic else current_topic
                    # If this row contains (or is followed by) bullet lists, split into children.
                    prefix, bullet_items_inline = split_bullets(rest)
                    bullet_items_following = bullet_items if 'bullet_items' in locals() else []

                    # If there are lettered subpoints (a./b./c.), use ONLY the prefix (key idea) for the L2 title.
                    # This prevents the L2 row from displaying the entire detailed content column.
                    letter_prefix, letter_items = split_lettered_subpoints(rest)
                    roman_prefix, roman_items = split_roman_subpoints(rest)

                    topics.append({
                        'code': code,
                        'title': (
                            letter_prefix if letter_items else
                            roman_prefix if roman_items else
                            (prefix or rest)
                        ),
                        'level': 2 if not current_subtopic else 3,
                        'parent': parent_for_2
                    })
                    last_numeric_by_depth = {2: code}

                    bullet_items = [b.strip() for b in (bullet_items_inline + bullet_items_following) if b.strip()]
                    if bullet_items:
                        for idx, item in enumerate(bullet_items, 1):
                            # Child code like 2.6.1, 2.6.2, ...
                            child_code = f"{code}.{idx}"
                            topics.append({
                                'code': child_code,
                                'title': item,
                                'level': 3 if not current_subtopic else 4,
                                'parent': code
                            })
                        last_numeric_by_depth[3] = f"{code}.1"
                        continue

                    # If no bullets, try lettered subpoints (common in Geography tables: a., b., c. ...)
                    if letter_items:
                        for idx, (letter, chunk) in enumerate(letter_items, 1):
                            child_code = f"{code}.{idx}"
                            topics.append({
                                'code': child_code,
                                'title': f"{letter}. {chunk}",
                                'level': 3 if not current_subtopic else 4,
                                'parent': code
                            })
                        last_numeric_by_depth[3] = f"{code}.1"
                        continue

                    # If no bullets/letters, try roman numeral subpoints (common in Biology specs: i/ii/iii...)
                    if roman_items:
                        for idx, (roman, chunk) in enumerate(roman_items, 1):
                            child_code = f"{code}.{idx}"
                            topics.append({
                                'code': child_code,
                                'title': f"{roman} {chunk}",
                                'level': 3 if not current_subtopic else 4,
                                'parent': code
                            })
                        last_numeric_by_depth[3] = f"{code}.1"
                        continue

                    continue

                # Depth >= 3: parent is most recent depth-1 numeric code if available; otherwise fall back to current topic.
                parent_numeric = last_numeric_by_depth.get(depth - 1)
                fallback_parent = current_subtopic if current_subtopic else current_topic
                prefix, bullet_items_inline = split_bullets(rest)
                topics.append({
                    'code': code,
                    'title': prefix or rest,
                    'level': (depth if not current_subtopic else depth + 1),  # keep relative depth under subtopics
                    'parent': parent_numeric or fallback_parent
                })
                # If a depth>=3 row has bullets (common in some Methods sections), emit depth+1 children.
                if bullet_items_inline:
                    for idx, item in enumerate(bullet_items_inline, 1):
                        child_code = f"{code}.{idx}"
                        topics.append({
                            'code': child_code,
                            'title': item,
                            'level': (depth + 1 if not current_subtopic else depth + 2),
                            'parent': code
                        })
                # update numeric stack
                last_numeric_by_depth[depth] = code
                # drop deeper levels if present
                for d in list(last_numeric_by_depth.keys()):
                    if d > depth:
                        del last_numeric_by_depth[d]
                continue

        # Pattern 3b: Alphanumeric hierarchy items for options (2A.1, 2B.3, 4A.12, 8B.7 ...)
        # These are key for Geography option subtopics. Only parse when inside a topic context.
        if current_topic:
            alpha_match = re.match(r'^(?P<code>\d+[A-Z](?:\.\d+){1,6})(?:\s+|$)(?P<rest>.*)$', line)
            if alpha_match:
                code = alpha_match.group('code').strip()
                rest = (alpha_match.group('rest') or '').strip()

                # Skip obvious non-content artifacts
                if "Total for GCE" in rest or "Synoptic assessment" in rest:
                    i += 1
                    continue

                # Determine which option this belongs to (prefix before first dot, e.g., 2A)
                opt_prefix = code.split('.')[0]  # "2A"
                # Ensure current_subtopic points to the option node if we have it
                option_node_code = f"Topic{opt_prefix}"
                parent_fallback = current_subtopic if current_subtopic else current_topic
                parent_for_alpha = option_node_code if (current_subtopic == option_node_code) else parent_fallback

                # Reuse existing helper logic for continuation + bullets/letters by delegating to the same flow:
                # We'll treat alphanumeric code as depth=2 within its option and split lettered subpoints into children.
                # Collect continuation lines similarly to numeric branch (but a bit shorter).
                content_parts = [rest] if rest else []
                bullet_items = []
                j = i + 1
                while j < len(lines) and (len(content_parts) < 40) and (len(bullet_items) < 60):
                    nxt = (lines[j] or '').strip()
                    if is_new_pattern(nxt) or re.match(r'^\d+[A-Z](?:\.\d+){1,6}\b', nxt):
                        break
                    if not nxt or len(nxt) < 3:
                        j += 1
                        continue
                    # bullet continuation support
                    if nxt.startswith(("●", "•")):
                        append_bullet(bullet_items, nxt)
                        j += 1
                        continue
                    if bullet_items and nxt and len(nxt) > 2:
                        append_bullet(bullet_items, nxt)
                        j += 1
                        continue
                    content_parts.append(nxt)
                    j += 1
                rest_joined = " ".join([p for p in content_parts if p]).strip()
                i = j

                # Create the alphanumeric L2-ish row under the option (store only key idea prefix if it contains a/b/c)
                letter_prefix, letter_items = split_lettered_subpoints(rest_joined)
                topics.append({
                    'code': code,
                    'title': letter_prefix or rest_joined,
                    'level': 3 if not current_subtopic else 4,
                    'parent': parent_for_alpha
                })

                # Split lettered items as children (a/b/c)
                if letter_items:
                    for idx2, (letter, chunk) in enumerate(letter_items, 1):
                        topics.append({
                            'code': f"{code}.{idx2}",
                            'title': f"{letter}. {chunk}",
                            'level': 4 if not current_subtopic else 5,
                            'parent': code
                        })
                # Split bullets as children
                if bullet_items:
                    for idx2, item in enumerate(bullet_items, 1):
                        topics.append({
                            'code': f"{code}.{idx2}",
                            'title': item,
                            'level': 4 if not current_subtopic else 5,
                            'parent': code
                        })
                continue
        
        # Pattern 4: Learning outcomes (numbered statements)
        if current_topic and structure['learning_outcomes'] > 5:
            outcome_match = re.match(r'^(\d+)\.\s+(be able to|know that|understand|can)(.+)', line, re.IGNORECASE)
            if outcome_match:
                outcome_num = outcome_match.group(1)
                outcome_text = outcome_match.group(2) + outcome_match.group(3).strip()
                
                # Multi-line continuation
                j = i + 1
                content = [outcome_text]
                while j < len(lines) and len(content) < 4:
                    next_line = lines[j].strip()
                    
                    if re.match(r'^\d+\.\s+(be able to|know that)', next_line, re.IGNORECASE):
                        break
                    if re.match(r'^Topic\s+\d+', next_line):
                        break
                    if not next_line or len(next_line) < 3:
                        j += 1
                        continue
                    
                    content.append(next_line)
                    j += 1
                
                full_text = ' '.join(content)[:200]  # Limit length
                
                parent = current_subtopic if current_subtopic else current_topic
                outcome_code = f'{parent}.{outcome_num}'
                
                topics.append({
                    'code': outcome_code,
                    'title': full_text,
                    'level': 2 if not current_subtopic else 3,
                    'parent': parent
                })
                
                i = j
                continue
        
        # Pattern 5: Roman numerals (i), ii), iii)) - Biology style sub-items
        if current_topic and structure['roman_items'] > 5:
            roman_match = re.match(r'^([ivx]+)\)\s+(.+)', line, re.IGNORECASE)
            if roman_match:
                roman = roman_match.group(1).lower()
                content = [roman_match.group(2).strip()]
                
                # Multi-line continuation
                j = i + 1
                while j < len(lines) and len(content) < 6:
                    next_line = lines[j].strip()
                    
                    if re.match(r'^[ivx]+\)\s+', next_line, re.IGNORECASE):
                        break
                    if re.match(r'^(\d+)\.(\d+)\s+', next_line):
                        break
                    if not next_line or len(next_line) < 3:
                        j += 1
                        continue
                    
                    content.append(next_line)
                    j += 1
                
                roman_map = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6, 'vii': 7}
                sub_num = roman_map.get(roman, 1)
                
                # Find appropriate parent
                # Look for most recent numbered item
                recent_numbered = None
                for t in reversed(topics):
                    if re.match(r'^\d+\.\d+$', t['code']):
                        recent_numbered = t['code']
                        break
                
                parent = recent_numbered if recent_numbered else current_topic
                item_code = f'{parent}.{sub_num}'
                full_text = ' '.join(content)
                
                topics.append({
                    'code': item_code,
                    'title': full_text,
                    'level': 3,
                    'parent': parent
                })
                
                i = j
                continue
        
        i += 1
    
    # Deduplicate by code
    unique = []
    seen = set()
    for t in topics:
        if t['code'] not in seen:
            unique.append(t)
            seen.add(t['code'])
    
    print(f"\n[OK] Parsed {len(unique)} unique topics (removed {len(topics) - len(unique)} duplicates)")
    
    # Show distribution
    levels = {}
    for t in unique:
        levels[t['level']] = levels.get(t['level'], 0) + 1
    
    print("\n[INFO] Level distribution:")
    for l in sorted(levels.keys()):
        print(f"  - Level {l}: {levels[l]} topics")
    
    return unique


def upload_topics(topics, subject_code, subject_name, pdf_url):
    """Upload to Supabase."""
    print("\n[INFO] Uploading to database...")
    
    # Get/create subject
    subject_result = supabase.table('staging_aqa_subjects').upsert({
        'subject_name': f"{subject_name} (A-Level)",
        'subject_code': subject_code,
        'qualification_type': 'A-Level',
        'specification_url': pdf_url,
        # Use canonical casing to avoid duplicate subject rows (viewer treats EDEXCEL + Edexcel as same board)
        'exam_board': 'EDEXCEL'
    }, on_conflict='subject_code,qualification_type,exam_board').execute()
    
    subject_id = subject_result.data[0]['id']
    print(f"[OK] Subject: {subject_result.data[0]['subject_name']}")
    
    # Clear old
    supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
    print("[OK] Cleared old topics")
    
    # Insert
    to_insert = [{
        'subject_id': subject_id,
        'topic_code': t['code'],
        'topic_name': t['title'],
        'topic_level': t['level'],
        'exam_board': 'EDEXCEL'
    } for t in topics]
    
    inserted_result = supabase.table('staging_aqa_topics').insert(to_insert).execute()
    print(f"[OK] Uploaded {len(inserted_result.data)} topics")
    
    # Link hierarchy
    code_to_id = {t['topic_code']: t['id'] for t in inserted_result.data}
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
    
    return subject_id


def main():
    """Main execution."""
    
    # Force UTF-8 output
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    print(f"[OK] Using {PDF_LIBRARY} for PDF parsing")
    
    # Parse arguments
    if len(sys.argv) < 4:
        print("Usage: python scrape-edexcel-universal.py <subject_code> <subject_name> <pdf_url>")
        print("\nExample:")
        print('  python scrape-edexcel-universal.py 9CH0 "Chemistry" "https://..."')
        sys.exit(1)
    
    subject_code = sys.argv[1]
    subject_name = sys.argv[2]
    pdf_url = sys.argv[3]
    
    print("=" * 80)
    print("EDEXCEL A-LEVEL - UNIVERSAL TOPIC SCRAPER")
    print("=" * 80)
    print(f"\nSubject: {subject_name}")
    print(f"Code: {subject_code}")
    print(f"Board: Edexcel\n")
    
    try:
        # Download and parse
        text = download_pdf(pdf_url, subject_code)
        
        # Parse topics
        topics = parse_topics_universal(text, subject_code, subject_name)
        
        if len(topics) == 0:
            print("\n[ERROR] No topics found!")
            print("   Check the debug file to see what was extracted.")
            sys.exit(1)
        
        # Upload
        upload_topics(topics, subject_code, subject_name, pdf_url)
        
        print("\n" + "=" * 80)
        print(f"[OK] {subject_name.upper()} COMPLETE!")
        print("=" * 80)
        print(f"\nTotal: {len(topics)} topics")
        print(f"\nNext: Run papers scraper for {subject_code}")
        
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

