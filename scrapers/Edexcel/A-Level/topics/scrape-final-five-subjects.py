"""
Edexcel A-Level Final Five Subjects - Batch Topic Scraper
Scrapes: History of Art, Mathematics, Politics, Religious Studies, Statistics

Uses Business scraper pattern for table-based subjects with adaptations.
"""

import os
import sys
import re
import requests
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv
from supabase import create_client
from pypdf import PdfReader

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

# Final 5 subjects to scrape
SUBJECTS = {
    '9HT0': {
        'name': 'History of Art',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/history-of-art/2017/specification-and-sample-assessments/specification-and-sample-assessments-GCE-HISOFART-SPEC.pdf'
    },
    '9MA0': {
        'name': 'Mathematics',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Mathematics/2017/specification-and-sample-assesment/a-level-l3-mathematics-specification-issue4.pdf'
    },
    '9PL0': {
        'name': 'Politics',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Politics/2017/Specification%20and%20sample%20assessments/A-level-Politics-Specification.pdf'
    },
    '9RS0': {
        'name': 'Religious Studies',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Religious%20Studies/2016/Specification%20and%20sample%20assessments/Specification_GCE_A_Level_in_Religious_Studies.pdf'
    },
    '9ST0': {
        'name': 'Statistics',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/statistics/2017/Specification%20and%20Sample%20assessment%20material/a-level-statistics-specification.pdf'
    }
}


def download_pdf(url, subject_code):
    """Download PDF and extract text."""
    print(f"[INFO] Downloading PDF...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        pdf = PdfReader(BytesIO(response.content))
        print(f"[OK] Downloaded {len(pdf.pages)} pages")
        
        # Extract text from all pages
        full_text = []
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            full_text.append(text)
        
        combined_text = '\n'.join(full_text)
        
        # Save debug file
        debug_path = Path(f'debug-{subject_code.lower()}-spec.txt')
        debug_path.write_text(combined_text, encoding='utf-8')
        print(f"[OK] Saved debug file: {debug_path}")
        
        return combined_text
        
    except Exception as e:
        print(f"[ERROR] Failed to download PDF: {e}")
        return None


def extract_topics_generic(text, subject_code, subject_name):
    """Generic topic extraction - looks for common patterns."""
    
    print(f"[INFO] Extracting topics for {subject_name}...")
    
    topics = []
    
    # Look for different topic patterns
    
    # Pattern 1: Check for "Topic X:" headers (Science style)
    topic_matches = re.findall(r'^Topic\s+(\d+[A-Z]?):\s*(.+?)$', text, re.MULTILINE | re.IGNORECASE)
    
    if topic_matches and len(topic_matches) >= 3:
        print(f"[OK] Found {len(topic_matches)} Science-style topics")
        for num, title in topic_matches:
            clean_title = re.sub(r'\s+', ' ', title).strip()
            topics.append({
                'code': f'Topic{num}',
                'title': f'Topic {num}: {clean_title}',
                'level': 0,
                'parent': None
            })
        return topics
    
    # Pattern 2: Check for numbered sections (1.1, 2.1, etc.) - Table style
    section_pattern = r'^(\d+)\.(\d+)\s+(.+?)$'
    section_matches = re.findall(section_pattern, text, re.MULTILINE)
    
    if section_matches and len(section_matches) >= 5:
        print(f"[OK] Found {len(section_matches)} table-style sections")
        
        # Group by major section
        sections = {}
        for major, minor, title in section_matches:
            clean_title = re.sub(r'\s+', ' ', title).strip()
            if len(clean_title) > 100:
                clean_title = clean_title[:100] + '...'
            
            if major not in sections:
                sections[major] = []
            sections[major].append((minor, clean_title))
        
        # Create hierarchy with unique codes
        used_codes = set()
        for major_num in sorted(sections.keys(), key=int):
            # Level 0: Major sections
            section_code = f'Section{major_num}'
            topics.append({
                'code': section_code,
                'title': f'Section {major_num}',
                'level': 0,
                'parent': None
            })
            used_codes.add(section_code)
            
            # Level 1: Sub-sections with globally unique codes
            for minor_num, title in sections[major_num][:15]:  # Limit to prevent explosion
                # Use full section number to ensure uniqueness
                subsection_code = f'S{major_num}_{minor_num}'
                if subsection_code not in used_codes:
                    topics.append({
                        'code': subsection_code,
                        'title': f'{major_num}.{minor_num} {title}',
                        'level': 1,
                        'parent': section_code
                    })
                    used_codes.add(subsection_code)
        
        return topics
    
    # Pattern 3: Check for "Paper" or "Component" structure
    paper_matches = re.findall(r'^(?:Paper|Component)\s+(\d+):?\s*(.+?)$', text, re.MULTILINE | re.IGNORECASE)
    
    if paper_matches and len(paper_matches) >= 2:
        # Deduplicate papers (they appear multiple times in PDFs)
        unique_papers = {}
        for num, title in paper_matches:
            if num not in unique_papers:
                clean_title = re.sub(r'\s+', ' ', title).strip()
                # Take first 100 chars
                if len(clean_title) > 100:
                    clean_title = clean_title[:100]
                unique_papers[num] = clean_title
        
        print(f"[OK] Found {len(unique_papers)} unique Papers/Components")
        for num in sorted(unique_papers.keys(), key=int):
            topics.append({
                'code': f'Paper{num}',
                'title': f'Paper {num}: {unique_papers[num]}',
                'level': 0,
                'parent': None
            })
        return topics
    
    # Pattern 4: Look for "Theme" structure
    theme_matches = re.findall(r'^Theme\s+(\d+):?\s*(.+?)$', text, re.MULTILINE | re.IGNORECASE)
    
    if theme_matches and len(theme_matches) >= 2:
        print(f"[OK] Found {len(theme_matches)} themes")
        for num, title in theme_matches:
            clean_title = re.sub(r'\s+', ' ', title).strip()
            if len(clean_title) > 80:
                clean_title = clean_title[:80] + '...'
            topics.append({
                'code': f'Theme{num}',
                'title': f'Theme {num}: {clean_title}',
                'level': 0,
                'parent': None
            })
        return topics
    
    print("[WARN] No standard patterns found")
    return topics


def scrape_subject(subject_code):
    """Scrape a single subject."""
    
    if subject_code not in SUBJECTS:
        print(f"[ERROR] Unknown subject: {subject_code}")
        return None
    
    subject = SUBJECTS[subject_code]
    
    print("=" * 80)
    print(f"EDEXCEL {subject['name'].upper()} ({subject_code}) - TOPIC SCRAPER")
    print("=" * 80)
    print(f"\nSubject: {subject['name']}")
    print(f"Code: {subject_code}")
    print()
    
    # Download PDF
    text = download_pdf(subject['pdf_url'], subject_code)
    if not text:
        return None
    
    # Extract topics
    topics = extract_topics_generic(text, subject_code, subject['name'])
    
    if len(topics) < 3:
        print(f"\n[WARN] Only found {len(topics)} topics - needs manual review")
        print(f"[INFO] Check debug-{subject_code.lower()}-spec.txt")
        return None
    
    print(f"\n[OK] Extracted {len(topics)} topics")
    
    # Show breakdown
    levels = {}
    for t in topics:
        levels[t['level']] = levels.get(t['level'], 0) + 1
    
    print("\n[INFO] Level breakdown:")
    for level in sorted(levels.keys()):
        print(f"   Level {level}: {levels[level]} topics")
    
    return topics


def upload_topics(subject_code, topics):
    """Upload topics to Supabase."""
    
    if not topics:
        return False
    
    subject = SUBJECTS[subject_code]
    
    print(f"\n[INFO] Uploading to database...")
    
    try:
        # Get/create subject
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{subject['name']} (A-Level)",
            'subject_code': subject_code,
            'qualification_type': 'A-Level',
            'specification_url': subject['pdf_url'],
            'exam_board': 'Edexcel'
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        # Clear old topics
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared old topics")
        
        # Insert topics
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'exam_board': 'Edexcel'
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
        
        print(f"[OK] Linked {linked} relationships")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main execution - process all 5 subjects."""
    
    print("=" * 80)
    print("EDEXCEL A-LEVEL - FINAL FIVE SUBJECTS BATCH SCRAPER")
    print("=" * 80)
    print("\nSubjects to process:")
    for code, info in SUBJECTS.items():
        print(f"   {code}: {info['name']}")
    
    print("\n" + "=" * 80 + "\n")
    
    results = {'success': [], 'failed': [], 'manual': []}
    
    for subject_code in sorted(SUBJECTS.keys()):
        try:
            print(f"\n{'=' * 80}\n")
            topics = scrape_subject(subject_code)
            
            if topics and len(topics) >= 3:
                # Attempt upload
                if upload_topics(subject_code, topics):
                    results['success'].append({
                        'code': subject_code,
                        'name': SUBJECTS[subject_code]['name'],
                        'topics': len(topics)
                    })
                    print(f"\n[OK] {SUBJECTS[subject_code]['name']} COMPLETE!")
                else:
                    results['failed'].append(subject_code)
            else:
                results['manual'].append(subject_code)
                print(f"\n[MANUAL] {SUBJECTS[subject_code]['name']} needs manual extraction")
            
        except Exception as e:
            print(f"\n[ERROR] {SUBJECTS[subject_code]['name']} failed: {e}")
            results['failed'].append(subject_code)
            import traceback
            traceback.print_exc()
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    if results['success']:
        print(f"\n✅ Successfully scraped: {len(results['success'])}")
        total_topics = 0
        for result in results['success']:
            print(f"   • {result['code']}: {result['name']} - {result['topics']} topics")
            total_topics += result['topics']
        print(f"\n   TOTAL: {total_topics} topics uploaded!")
    
    if results['manual']:
        print(f"\n⚠️  Need manual extraction: {len(results['manual'])}")
        for code in results['manual']:
            print(f"   • {code}: {SUBJECTS[code]['name']}")
            print(f"      → Check debug-{code.lower()}-spec.txt")
    
    if results['failed']:
        print(f"\n❌ Failed: {len(results['failed'])}")
        for code in results['failed']:
            print(f"   • {code}: {SUBJECTS[code]['name']}")
    
    print("\n" + "=" * 80)
    
    return len(results['success'])


if __name__ == '__main__':
    total = main()
    print(f"\nCompleted: {total} subjects scraped successfully!")

