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

print(f"✓ Using {PDF_LIBRARY} for PDF parsing")


def download_pdf(url, subject_code):
    """Download PDF and extract text."""
    print(f"\n📥 Downloading PDF...")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        print(f"✓ Downloaded {len(response.content):,} bytes")
        
        # Parse PDF
        print("📄 Extracting text from PDF...")
        pdf_file = BytesIO(response.content)
        reader = PdfReader(pdf_file)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        print(f"✓ Extracted {len(text):,} characters from {len(reader.pages)} pages")
        
        # Save for debugging
        debug_path = Path(__file__).parent / f"debug-{subject_code.lower()}-spec.txt"
        debug_path.write_text(text, encoding='utf-8')
        print(f"   Saved to {debug_path.name}")
        
        return text
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        raise


def detect_structure(text):
    """Analyze PDF to detect its structure."""
    print("\n🔍 Analyzing PDF structure...")
    
    lines = text.split('\n')
    
    # Count different patterns
    patterns = {
        'topics': 0,          # Topic X:
        'sub_topics': 0,      # Topic XA:, Topic XB:
        'papers': 0,          # Paper X:
        'numbered_items': 0,  # 1.1, 1.2, 2.3
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
        
        # Roman numerals (i), ii))
        if re.match(r'^([ivx]+)\)\s+', line, re.IGNORECASE):
            patterns['roman_items'] += 1
        
        # Learning outcomes
        if re.match(r'^\d+\.\s+(be able to|know that|understand)', line, re.IGNORECASE):
            patterns['learning_outcomes'] += 1
    
    print("   Pattern detection:")
    for pattern, count in patterns.items():
        if count > 0:
            print(f"   • {pattern}: {count}")
    
    return patterns


def parse_topics_universal(text, subject_code, subject_name):
    """Universal parser that adapts to PDF structure."""
    print("\n⚙️ Parsing topics...")
    
    topics = []
    lines = text.split('\n')
    
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
                print(f"   📋 Found {paper_code}: {paper_title[:50]}")
    
    topics.extend(papers_found)
    
    # Parse Topics (Level 1)
    topic_pattern_found = {}
    current_topic = None
    current_subtopic = None
    
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
        
        # Pattern 1: Main Topics (Topic X:)
        topic_match = re.match(r'^Topic\s+(\d+):\s+(.+)', line)
        if topic_match:
            topic_num = topic_match.group(1)
            topic_title = topic_match.group(2).strip()
            
            # Clean up title
            if len(topic_title) > 150:
                topic_title = topic_title[:150].rsplit(' ', 1)[0] + '...'
            
            topic_code = f'Topic{topic_num}'
            current_topic = topic_code
            current_subtopic = None
            
            # Determine parent (Paper 1, 2, or 3)
            # Default to Paper1 unless specified otherwise
            parent = 'Paper1'  # Default
            
            topics.append({
                'code': topic_code,
                'title': f'Topic {topic_num}: {topic_title}',
                'level': 1,
                'parent': parent
            })
            
            topic_pattern_found[topic_code] = True
            print(f"   📚 Topic {topic_num}: {topic_title[:60]}")
            i += 1
            continue
        
        # Pattern 2: Sub-topics (Topic 2A:, Topic 15B:)
        subtopic_match = re.match(r'^Topic\s+(\d+)([A-Z]):\s+(.+)', line)
        if subtopic_match:
            topic_num = subtopic_match.group(1)
            letter = subtopic_match.group(2)
            subtopic_title = subtopic_match.group(3).strip()
            
            if len(subtopic_title) > 150:
                subtopic_title = subtopic_title[:150].rsplit(' ', 1)[0] + '...'
            
            subtopic_code = f'Topic{topic_num}{letter}'
            parent_topic = f'Topic{topic_num}'
            current_subtopic = subtopic_code
            
            topics.append({
                'code': subtopic_code,
                'title': f'Topic {topic_num}{letter}: {subtopic_title}',
                'level': 2,
                'parent': parent_topic
            })
            
            print(f"      └─ {subtopic_code}: {subtopic_title[:50]}")
            i += 1
            continue
        
        # Pattern 3: Numbered items (1.1, 1.2) - Biology style
        if current_topic and structure['numbered_items'] > 10:
            item_match = re.match(r'^(\d+)\.(\d+)\s+(.+)', line)
            if item_match:
                major = item_match.group(1)
                minor = item_match.group(2)
                content = [item_match.group(3).strip()]
                
                # Multi-line continuation
                j = i + 1
                while j < len(lines) and len(content) < 6:
                    next_line = lines[j].strip()
                    
                    # Stop on new pattern
                    if re.match(r'^(\d+)\.(\d+)\s+', next_line):
                        break
                    if re.match(r'^Topic\s+\d+', next_line):
                        break
                    if re.match(r'^[ivx]+\)\s+', next_line, re.IGNORECASE):
                        break
                    if not next_line or len(next_line) < 3:
                        j += 1
                        continue
                    
                    content.append(next_line)
                    j += 1
                
                item_code = f'{major}.{minor}'
                full_content = ' '.join(content)
                
                parent = current_subtopic if current_subtopic else current_topic
                
                topics.append({
                    'code': item_code,
                    'title': full_content,
                    'level': 2 if not current_subtopic else 3,
                    'parent': parent
                })
                
                i = j
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
    
    print(f"\n✓ Parsed {len(unique)} unique topics (removed {len(topics) - len(unique)} duplicates)")
    
    # Show distribution
    levels = {}
    for t in unique:
        levels[t['level']] = levels.get(t['level'], 0) + 1
    
    print("\n   Level distribution:")
    for l in sorted(levels.keys()):
        print(f"   • Level {l}: {levels[l]} topics")
    
    return unique


def upload_topics(topics, subject_code, subject_name, pdf_url):
    """Upload to Supabase."""
    print("\n📤 Uploading to database...")
    
    # Get/create subject
    subject_result = supabase.table('staging_aqa_subjects').upsert({
        'subject_name': f"{subject_name} (A-Level)",
        'subject_code': subject_code,
        'qualification_type': 'A-Level',
        'specification_url': pdf_url,
        'exam_board': 'Edexcel'
    }, on_conflict='subject_code,qualification_type,exam_board').execute()
    
    subject_id = subject_result.data[0]['id']
    print(f"✓ Subject: {subject_result.data[0]['subject_name']}")
    
    # Clear old
    supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
    print("✓ Cleared old topics")
    
    # Insert
    to_insert = [{
        'subject_id': subject_id,
        'topic_code': t['code'],
        'topic_name': t['title'],
        'topic_level': t['level'],
        'exam_board': 'Edexcel'
    } for t in topics]
    
    inserted_result = supabase.table('staging_aqa_topics').insert(to_insert).execute()
    print(f"✓ Uploaded {len(inserted_result.data)} topics")
    
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
    
    print(f"✓ Linked {linked} parent-child relationships")
    
    return subject_id


def main():
    """Main execution."""
    
    # Force UTF-8 output
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
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
            print("\n❌ ERROR: No topics found!")
            print("   Check the debug file to see what was extracted.")
            sys.exit(1)
        
        # Upload
        upload_topics(topics, subject_code, subject_name, pdf_url)
        
        print("\n" + "=" * 80)
        print(f"✅ {subject_name.upper()} COMPLETE!")
        print("=" * 80)
        print(f"\nTotal: {len(topics)} topics")
        print(f"\nNext: Run papers scraper for {subject_code}")
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

