"""
GCSE Computer Science - Dedicated Scraper
==========================================

Structure from PDF analysis:
- Level 0: Topic 1-6 (main topics)
- Level 1: X.Y Subtopics (2.1 Binary, 2.2 Data representation)
- Level 2: X.Y.Z Learning outcomes (2.1.1 understand that...)

Topics are clearly numbered in tables with "Students should:" column.
Multi-line learning outcomes need to be merged.

CRITICAL: Only extracts content that exists in PDF. Does NOT invent.
"""

import os
import sys
import re
import requests
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv
from supabase import create_client

try:
    from pypdf import PdfReader
    PDF_LIBRARY = 'pypdf'
except ImportError:
    import PyPDF2
    PdfReader = PyPDF2.PdfReader
    PDF_LIBRARY = 'PyPDF2'

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT = {
    'code': 'GCSE-ComputerScience',
    'name': 'Computer Science',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Computer%20Science/2020/specification-and-sample-assessments/GCSE_L1_L2_Computer_Science_2020_Specification.pdf'
}

# The 5 main topics (Level 0)
MAIN_TOPICS = [
    {
        'code': 'Topic1',
        'title': 'Topic 1: Computational thinking',
        'description': 'understanding of what algorithms are, what they are used for and how they work; ability to follow, amend and write algorithms; ability to construct truth tables',
        'level': 0,
        'parent': None
    },
    {
        'code': 'Topic2',
        'title': 'Topic 2: Data',
        'description': 'understanding of binary, data representation, data storage and compression',
        'level': 0,
        'parent': None
    },
    {
        'code': 'Topic3',
        'title': 'Topic 3: Computers',
        'description': 'understanding of hardware and software components of computer systems and characteristics of programming languages',
        'level': 0,
        'parent': None
    },
    {
        'code': 'Topic4',
        'title': 'Topic 4: Networks',
        'description': 'understanding of computer networks and network security',
        'level': 0,
        'parent': None
    },
    {
        'code': 'Topic5',
        'title': 'Topic 5: Issues and impact',
        'description': 'awareness of emerging trends in computing technologies, and the impact of computing on individuals, society and the environment, including ethical, legal and ownership issues',
        'level': 0,
        'parent': None
    },
    {
        'code': 'Topic6',
        'title': 'Topic 6: Problem solving with programming',
        'description': 'practical programming skills',
        'level': 0,
        'parent': None
    }
]


def download_pdf():
    """Download PDF and extract text."""
    print(f"\n[INFO] Downloading PDF...")
    
    try:
        response = requests.get(SUBJECT['pdf_url'], timeout=60)
        response.raise_for_status()
        
        print(f"[OK] Downloaded {len(response.content):,} bytes")
        
        pdf_file = BytesIO(response.content)
        reader = PdfReader(pdf_file)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        print(f"[OK] Extracted {len(text):,} characters from {len(reader.pages)} pages")
        
        # Save debug
        debug_path = Path(__file__).parent / "debug-gcse-cs-final.txt"
        debug_path.write_text(text, encoding='utf-8')
        print(f"[OK] Saved debug to {debug_path.name}")
        
        return text
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        raise


def parse_topics(text):
    """
    Parse Computer Science topics from the PDF text.
    
    Expected structure:
    - Level 0: Topic 1-6 (hardcoded from spec)
    - Level 1: X.Y Subtopic (2.1 Binary, 2.2 Data representation)
    - Level 2: X.Y.Z Learning outcome (2.1.1 understand...)
    """
    print("\n[INFO] Parsing Computer Science topics...")
    
    topics = []
    
    # Add the 6 main topics (Level 0)
    topics.extend(MAIN_TOPICS)
    print(f"[OK] Added {len(MAIN_TOPICS)} main topics (Level 0)")
    
    lines = text.split('\n')
    
    # Track state
    current_topic = None  # Topic1-6
    current_subtopic = None  # 2.1, 2.2, etc.
    
    # Process line by line
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Pattern 1: Detect which Topic section we're in
        # "Topic 1: Computational thinking"
        topic_match = re.match(r'^Topic\s+([1-6]):\s*(.+?)$', line, re.IGNORECASE)
        if topic_match:
            topic_num = topic_match.group(1)
            current_topic = f'Topic{topic_num}'
            print(f"\n[INFO] Entering {current_topic}")
            i += 1
            continue
        
        # Skip if we're not in a Topic section yet
        if not current_topic:
            i += 1
            continue
        
        # Pattern 2: Subtopics (Level 1) - format: "X.Y Name"
        # Examples: "1.1 Decomposition", "2.1 Binary", "2.2 Data representation"
        # CRITICAL: Sometimes the first learning outcome is on the same line in table format
        subtopic_match = re.match(r'^(\d+)\.(\d+)\s+(.+?)$', line)
        if subtopic_match:
            major = subtopic_match.group(1)
            minor = subtopic_match.group(2)
            rest_of_line = subtopic_match.group(3).strip()
            
            # Check if this belongs to current topic
            if f'Topic{major}' == current_topic:
                # Check if learning outcome (X.Y.Z) is on same line
                # Pattern: "Subtopic name X.Y.Z outcome text"
                outcome_on_same_line = re.search(r'\s+(\d+)\.(\d+)\.(\d+)\s+(.+)', rest_of_line)
                
                if outcome_on_same_line:
                    # Split: subtopic name is before the X.Y.Z pattern
                    subtopic_name = rest_of_line[:outcome_on_same_line.start()].strip()
                    
                    # Extract the learning outcome details
                    outcome_major = outcome_on_same_line.group(1)
                    outcome_minor = outcome_on_same_line.group(2)
                    outcome_micro = outcome_on_same_line.group(3)
                    outcome_text = outcome_on_same_line.group(4).strip()
                else:
                    subtopic_name = rest_of_line
                    outcome_on_same_line = None
                
                # Look ahead to collect multi-line subtopic names (but only if no outcome on same line)
                full_subtopic_name = subtopic_name
                if not outcome_on_same_line:
                    j = i + 1
                    while j < len(lines) and j < i + 3:
                        next_line = lines[j].strip()
                        
                        # Stop at empty line or next numbered item
                        if not next_line:
                            break
                        if re.match(r'^\d+\.\d+\.', next_line):  # Next learning outcome
                            break
                        if re.match(r'^\d+\.\d+\s+', next_line):  # Next subtopic
                            break
                        
                        # Merge continuation
                        full_subtopic_name += ' ' + next_line
                        j += 1
                
                # Create subtopic (Level 1)
                subtopic_code = f"{current_topic}_{major}_{minor}"
                current_subtopic = subtopic_code
                
                topics.append({
                    'code': subtopic_code,
                    'title': f"{major}.{minor} {full_subtopic_name}",
                    'level': 1,
                    'parent': current_topic
                })
                print(f"  [OK] Level 1: {major}.{minor} {full_subtopic_name[:60]}")
                
                # If learning outcome was on same line, process it now
                if outcome_on_same_line:
                    # Collect multi-line outcome text
                    j = i + 1
                    full_outcome = outcome_text
                    max_lines = 10
                    
                    while j < len(lines) and j < i + max_lines:
                        next_line = lines[j].strip()
                        
                        # Stop at empty line
                        if not next_line:
                            break
                        
                        # Stop at next learning outcome
                        if re.match(r'^\d+\.\d+\.\d+\s+', next_line):
                            break
                        
                        # Stop at next subtopic
                        if re.match(r'^\d+\.\d+\s+[A-Z]', next_line):
                            break
                        
                        # Stop at table headers
                        if 'Subject content' in next_line or 'Students should' in next_line:
                            break
                        
                        # Merge continuation
                        full_outcome += ' ' + next_line
                        j += 1
                    
                    outcome_code = f"{subtopic_code}_{outcome_micro}"
                    
                    topics.append({
                        'code': outcome_code,
                        'title': f"{outcome_major}.{outcome_minor}.{outcome_micro} {full_outcome}",
                        'level': 2,
                        'parent': current_subtopic
                    })
                    print(f"    [OK] Level 2: {outcome_major}.{outcome_minor}.{outcome_micro} {full_outcome[:60]}")
                    i = j  # Skip lines we merged
                    continue
                
                i += 1
                continue
        
        # Pattern 3: Learning outcomes (Level 2) - format: "X.Y.Z description"
        # Examples: "2.1.1 understand that...", "1.2.1 be able to..."
        outcome_match = re.match(r'^(\d+)\.(\d+)\.(\d+)\s+(.+?)$', line)
        if outcome_match:
            major = outcome_match.group(1)
            minor = outcome_match.group(2)
            micro = outcome_match.group(3)
            outcome_text = outcome_match.group(4).strip()
            
            # Check if this belongs to current subtopic
            expected_subtopic = f"Topic{major}_{major}_{minor}"
            if current_subtopic == expected_subtopic:
                # Look ahead to collect multi-line outcomes (CRITICAL!)
                full_outcome = outcome_text
                j = i + 1
                max_lines = 10  # Allow up to 10 continuation lines
                
                while j < len(lines) and j < i + max_lines:
                    next_line = lines[j].strip()
                    
                    # Stop at empty line
                    if not next_line:
                        break
                    
                    # Stop at next learning outcome
                    if re.match(r'^\d+\.\d+\.\d+\s+', next_line):
                        break
                    
                    # Stop at next subtopic
                    if re.match(r'^\d+\.\d+\s+[A-Z]', next_line):
                        break
                    
                    # Stop at table headers
                    if 'Subject content' in next_line or 'Students should' in next_line:
                        break
                    
                    # Merge continuation
                    full_outcome += ' ' + next_line
                    j += 1
                
                outcome_code = f"{current_subtopic}_{micro}"
                
                topics.append({
                    'code': outcome_code,
                    'title': f"{major}.{minor}.{micro} {full_outcome}",
                    'level': 2,
                    'parent': current_subtopic
                })
                print(f"    [OK] Level 2: {major}.{minor}.{micro} {full_outcome[:60]}")
                i = j  # Skip the lines we merged
                continue
        
        i += 1
    
    return topics


def upload_topics(topics):
    """Upload topics to Supabase."""
    print("\n[INFO] Uploading to Supabase...")
    
    try:
        # Create/update subject
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT['name']} (GCSE)",
            'subject_code': SUBJECT['code'],
            'qualification_type': 'GCSE',
            'specification_url': SUBJECT['pdf_url'],
            'exam_board': 'Edexcel'
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        # Clear old topics
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared old topics")
        
        # Insert topics (NO TRUNCATION!)
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],  # Full content, no truncation
            'topic_level': t['level'],
            'exam_board': 'Edexcel'
        } for t in topics]
        
        inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted.data)} topics")
        
        # Link parent relationships
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
        
        print(f"[OK] Linked {linked} parent-child relationships")
        
        # Summary
        levels = {}
        for t in topics:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("\n" + "=" * 80)
        print("[SUCCESS] GCSE COMPUTER SCIENCE UPLOADED!")
        print("=" * 80)
        print(f"   Level 0 (Main Topics): {levels.get(0, 0)}")
        print(f"   Level 1 (Subtopics): {levels.get(1, 0)}")
        print(f"   Level 2 (Learning Outcomes): {levels.get(2, 0)}")
        print(f"\n   Total: {len(topics)} topics")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 80)
    print("GCSE COMPUTER SCIENCE - DEDICATED SCRAPER")
    print("=" * 80)
    print("Structure:")
    print("  Level 0: 6 Main Topics (Topic 1-6)")
    print("  Level 1: Subtopics (2.1 Binary, 2.2 Data representation)")
    print("  Level 2: Learning outcomes (2.1.1 understand that...)")
    print("=" * 80)
    
    try:
        # Download and parse
        text = download_pdf()
        topics = parse_topics(text)
        
        if len(topics) < 20:
            print(f"\n[WARNING] Only {len(topics)} topics found - this seems too low!")
            print("[WARNING] Expected ~100+ topics (6 main + subtopics + outcomes)")
            response = input("\nContinue with upload anyway? (y/n): ")
            if response.lower() != 'y':
                print("[INFO] Upload cancelled")
                return
        
        # Upload
        success = upload_topics(topics)
        
        if success:
            print("\n✅ SCRAPING COMPLETE!")
        else:
            print("\n❌ SCRAPING FAILED")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

