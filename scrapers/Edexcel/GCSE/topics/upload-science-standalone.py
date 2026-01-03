"""
GCSE Science Standalone Subjects Uploader
=========================================

Uploads Biology, Chemistry, and Physics as separate subjects.
Extracts content from edexcel science gcse.md automatically.

Usage:
    python upload-science-standalone.py biology
    python upload-science-standalone.py chemistry
    python upload-science-standalone.py physics
    python upload-science-standalone.py all
"""

import os
import sys
import re
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

SUBJECTS = {
    'biology': {
        'code': 'GCSE-Biology',
        'name': 'Biology',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Science/2016/Specification/gcse-biology-spec.pdf',
        'papers': ['Paper 1: Biology', 'Paper 2: Biology'],
        'stop_at': 'Paper 3: Chemistry'
    },
    'chemistry': {
        'code': 'GCSE-Chemistry',
        'name': 'Chemistry',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Science/2016/Specification/gcse-chemistry-spec.pdf',
        'papers': ['Paper 3: Chemistry', 'Paper 4: Chemistry'],
        'stop_at': 'Paper 5: Physics'
    },
    'physics': {
        'code': 'GCSE-Physics',
        'name': 'Physics',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Science/2016/Specification/gcse-physics-spec.pdf',
        'papers': ['Paper 5: Physics', 'Paper 6: Physics'],
        'stop_at': None
    }
}


def sanitize_code(text):
    """Convert text to safe code format."""
    safe = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    safe = re.sub(r'\s+', '_', safe.strip())
    return safe[:50]


def extract_subject_content(subject_key):
    """Extract content for a specific subject from the combined markdown file."""
    md_file = Path(__file__).parent / "edexcel science gcse.md"
    full_content = md_file.read_text(encoding='utf-8')
    
    subject = SUBJECTS[subject_key]
    start_paper = subject['papers'][0]
    stop_at = subject['stop_at']
    
    lines = full_content.split('\n')
    extracted_lines = []
    in_subject = False
    
    for line in lines:
        if line.startswith(start_paper):
            in_subject = True
        elif stop_at and line.startswith(stop_at):
            break
        
        if in_subject:
            extracted_lines.append(line)
    
    return '\n'.join(extracted_lines)


def parse_hierarchy(text):
    """Parse hierarchical text into topic structure."""
    lines = [line.rstrip() for line in text.strip().split('\n') if line.strip()]
    
    topics = []
    current_paper = None
    current_topic = None
    current_section = None
    
    for line in lines:
        # Detect "Paper X:" format (Level 0)
        if re.match(r'^Paper\s+\d+:', line, re.IGNORECASE):
            paper_match = re.match(r'^Paper\s+(\d+):\s*(.+)$', line, re.IGNORECASE)
            if paper_match:
                paper_num = paper_match.group(1)
                paper_code = f"Paper{paper_num}"
                
                topics.append({
                    'code': paper_code,
                    'title': line.strip(),
                    'level': 0,
                    'parent': None
                })
                
                current_paper = paper_code
                current_topic = None
                current_section = None
                print(f"[L0] {line.strip()}")
                continue
        
        # Detect "Topic X –" format (Level 1)
        if re.match(r'^Topic\s+\d+\s*[:\-–]', line, re.IGNORECASE):
            topic_match = re.match(r'^Topic\s+(\d+)\s*[:\-–]\s*(.*)$', line, re.IGNORECASE)
            if topic_match and current_paper:
                topic_num = topic_match.group(1)
                topic_code = f"{current_paper}_Topic{topic_num}"
                
                topics.append({
                    'code': topic_code,
                    'title': line.strip(),
                    'level': 1,
                    'parent': current_paper
                })
                
                current_topic = topic_code
                current_section = None
                print(f"  [L1] {line.strip()}")
                continue
        
        # Detect "1.1" format (Level 2)
        if re.match(r'^\d+\.\d+[\s:]', line) and current_topic:
            section_match = re.match(r'^(\d+\.\d+)[\s:]+(.+)$', line)
            if section_match:
                section_number = section_match.group(1)
                section_title = section_match.group(2).strip()
                section_code = f"{current_topic}_S{section_number.replace('.', '_')}"
                
                topics.append({
                    'code': section_code,
                    'title': f"{section_number} {section_title}",
                    'level': 2,
                    'parent': current_topic
                })
                
                current_section = section_code
                print(f"    [L2] {section_number} {section_title}")
                continue
        
        # Everything else is Level 3 detail
        if line and current_section:
            item_code = f"{current_section}_Item{len([t for t in topics if t.get('parent') == current_section]) + 1}"
            
            topics.append({
                'code': item_code,
                'title': line.strip(),
                'level': 3,
                'parent': current_section
            })
            
            print(f"      [L3] {line.strip()[:60]}...")
    
    return topics


def upload_topics(subject_info, topics):
    """Upload parsed topics to Supabase."""
    print(f"\n[INFO] Uploading {len(topics)} topics for {subject_info['name']}...")
    
    try:
        # Create/update subject
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{subject_info['name']} ({subject_info['qualification']})",
            'subject_code': subject_info['code'],
            'qualification_type': subject_info['qualification'],
            'specification_url': subject_info['pdf_url'],
            'exam_board': subject_info['exam_board']
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        # Clear old topics
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared old topics")
        
        # Insert topics in batches
        BATCH_SIZE = 500
        all_inserted = []
        
        for i in range(0, len(topics), BATCH_SIZE):
            batch = topics[i:i+BATCH_SIZE]
            to_insert = [{
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': t['title'],
                'topic_level': t['level'],
                'exam_board': subject_info['exam_board']
            } for t in batch]
            
            inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
            all_inserted.extend(inserted.data)
            print(f"[OK] Uploaded batch {i//BATCH_SIZE + 1}: {len(inserted.data)} topics")
        
        print(f"[OK] Total uploaded: {len(all_inserted)} topics")
        
        # Link parent relationships
        code_to_id = {t['topic_code']: t['id'] for t in all_inserted}
        
        for level_num in [1, 2, 3]:
            level_topics = [t for t in topics if t['level'] == level_num and t['parent']]
            linked = 0
            
            for topic in level_topics:
                parent_id = code_to_id.get(topic['parent'])
                child_id = code_to_id.get(topic['code'])
                if parent_id and child_id:
                    supabase.table('staging_aqa_topics').update({
                        'parent_topic_id': parent_id
                    }).eq('id', child_id).execute()
                    linked += 1
            
            if linked > 0:
                print(f"[OK] Linked {linked} Level {level_num} parent relationships")
        
        # Summary
        levels = defaultdict(int)
        for t in topics:
            levels[t['level']] += 1
        
        print("\n" + "=" * 80)
        print(f"[SUCCESS] {subject_info['name'].upper()} - UPLOAD COMPLETE!")
        print("=" * 80)
        for level in sorted(levels.keys()):
            print(f"   Level {level}: {levels[level]} topics")
        print(f"\n   Total: {len(topics)} topics")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python upload-science-standalone.py <biology|chemistry|physics|all>")
        print("\nExamples:")
        print("  python upload-science-standalone.py biology")
        print("  python upload-science-standalone.py all")
        sys.exit(1)
    
    subject_key = sys.argv[1].lower()
    
    if subject_key == 'all':
        subjects_to_upload = ['biology', 'chemistry', 'physics']
    elif subject_key in SUBJECTS:
        subjects_to_upload = [subject_key]
    else:
        print(f"[ERROR] Unknown subject: {subject_key}")
        print(f"Available: biology, chemistry, physics, all")
        sys.exit(1)
    
    for key in subjects_to_upload:
        subject = SUBJECTS[key]
        
        print("=" * 80)
        print(f"GCSE {subject['name'].upper()} (STANDALONE)")
        print("=" * 80)
        print(f"Code: {subject['code']}")
        print(f"Papers: {', '.join(subject['papers'])}")
        print("=" * 80)
        print()
        
        # Extract content
        print(f"[INFO] Extracting {subject['name']} content from markdown file...")
        content = extract_subject_content(key)
        
        # Parse
        print(f"[INFO] Parsing hierarchy...")
        topics = parse_hierarchy(content)
        
        if not topics:
            print(f"[ERROR] No topics found for {subject['name']}!")
            continue
        
        print(f"\n[OK] Parsed {len(topics)} topics")
        
        # Upload
        subject_info = {
            'code': subject['code'],
            'name': subject['name'],
            'qualification': 'GCSE',
            'exam_board': 'Edexcel',
            'pdf_url': subject['pdf_url']
        }
        
        success = upload_topics(subject_info, topics)
        
        if success:
            print(f"\n✅ {subject['name'].upper()} COMPLETE!")
        else:
            print(f"\n❌ {subject['name'].upper()} FAILED!")
        
        print("\n" + "=" * 80 + "\n")


if __name__ == '__main__':
    main()

