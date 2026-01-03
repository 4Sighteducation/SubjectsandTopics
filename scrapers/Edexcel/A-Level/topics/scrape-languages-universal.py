"""
Edexcel A-Level Languages - Universal Topic Scraper
Extracts themes, sub-themes, and research topics from language specifications.
Preserves native language text with English translations.

Languages supported:
- French, German, Greek, Gujarati, Italian, Japanese, Persian,
  Portuguese, Russian, Spanish, Turkish, Urdu
  
(Arabic and Chinese already completed manually)
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

# Force UTF-8 output for non-Latin scripts
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

# Language subject metadata
LANGUAGES = {
    '9FR0': {
        'name': 'French',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/French/2016/Specification%20and%20sample%20assessments/Specification_GCE_A_level_L3_in_French.pdf',
        'theme_marker': 'Premier thème'  # First theme marker to find section
    },
    '9GN0': {
        'name': 'German',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/German/2016/Specification%20and%20sample%20assessments/Specification_GCE_A_level_L3_in_German.pdf',
        'theme_marker': 'Erstes Thema'
    },
    '9GK0': {
        'name': 'Greek',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Greek/2018/specification/A-level-Greek-specification.pdf',
        'theme_marker': 'Πρώτο Θέμα'
    },
    '9GU0': {
        'name': 'Gujarati',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Gujarati/2018/specification-and-sample-assessments/A-level-Gujarati-Specification.pdf',
        'theme_marker': 'પ્રથમ થીમ'  # First theme in Gujarati
    },
    '9IN0': {
        'name': 'Italian',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Italian/2017/specification-and-sample-assessments/Specification_GCE_A_level_L3_in_Italian_August_2016_Draft.pdf',
        'theme_marker': 'Primo tema'
    },
    '9JA0': {
        'name': 'Japanese',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Japanese/2018/specification-and-sample-assessments/a-level-japanese-specification.pdf',
        'theme_marker': '第一テーマ'  # First theme in Japanese
    },
    '9PE0': {
        'name': 'Persian',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Persian/2018/specification-and-sample-assessments/A-level-Persian-Specification.pdf',
        'theme_marker': 'موضوع اول'  # First theme in Persian
    },
    '9PT0': {
        'name': 'Portuguese',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Portuguese/2018/specification-and-sample-assessments/A-level-Portugese-Specification1.pdf',
        'theme_marker': 'Primeiro tema'
    },
    '9RU0': {
        'name': 'Russian',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Russian/2017/specification-sample-assessments/Specification_GCE_A_level_L3_in_Russian.pdf',
        'theme_marker': 'Первая тема'  # First theme in Russian
    },
    '9SP0': {
        'name': 'Spanish',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Spanish/2016/Specification%20and%20sample%20assessments/Specification_GCE_A_level_L3_in_Spanish.pdf',
        'theme_marker': 'Primer tema'
    },
    '9TU0': {
        'name': 'Turkish',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Turkish/2018/specification-and-sample-assessments/A-level-Turkish-Specification11.pdf',
        'theme_marker': 'Birinci tema'  # First theme in Turkish
    },
    '9UR0': {
        'name': 'Urdu',
        'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Urdu/2018/specification-and-sample-assessments/A-level-Urdu-Specification11.pdf',
        'theme_marker': 'پہلا موضوع'  # First theme in Urdu
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
        
        # Extract all text
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


def extract_themes(text, subject_code, language_name):
    """Extract themes from PDF text.
    
    Pattern in PDFs:
    - Native theme title (e.g., "Πρώτο Θέμα: Greek text")  
    - Blank line
    - English explanation (e.g., "Theme 1 is set in the context...")
    - Sub-themes with bullets (•)
    """
    
    print(f"\n[INFO] Extracting themes for {language_name}...")
    
    topics = []
    
    # Level 0: Papers (standard for all languages)
    topics.extend([
        {'code': 'Paper1', 'title': 'Paper 1: Listening, Reading and Translation', 'level': 0, 'parent': None},
        {'code': 'Paper2', 'title': 'Paper 2: Written Response to Works and Translation', 'level': 0, 'parent': None},
        {'code': 'Paper3', 'title': 'Paper 3: Speaking', 'level': 0, 'parent': None},
    ])
    
    # Language-specific theme markers (case-insensitive where applicable)
    theme_markers = {
        'Greek': r'(Πρώτο|Δεύτερο|Τρίτο|Τέταρτο) [Θθ]έμα:',
        'French': r'(Premier|Deuxième|Troisième|Quatrième) thème:',
        'German': r'(Erstes|Zweites|Drittes|Viertes) [Tt]hema:',
        'Italian': r'(Primo|Secondo|Terzo|Quarto) tema:',
        'Spanish': r'(Primer|Segundo|Tercer|Cuarto) tema:',
        'Portuguese': r'(Primeiro|Segundo|Terceiro|Quarto) tema:',
        'Russian': r'(Первая|Вторая|Третья|Четвертая) тема:',
        'Turkish': r'(Birinci|İkinci|Üçüncü|Dördüncü) tema:',
        'Japanese': r'第[一二三四]テーマ:',
        'Persian': r'موضوع (اول|دوم|سوم|چهارم):',
        'Urdu': r'(پہلا|دوسرا|تیسرا|چوتھا) موضوع:',
        'Gujarati': r'(પ્રથમ|બીજો|ત્રીજો|ચોથો) થીમ:'
    }
    
    pattern = theme_markers.get(language_name)
    if not pattern:
        print(f"[WARN] No pattern defined for {language_name}")
        return topics
    
    # Find all theme titles
    # Two formats:
    # 1. Native-first: "Πρώτο Θέμα: native text" (Greek)
    # 2. English-first: "Theme 1: native text" (French, Spanish, etc.)
    
    theme_lines = []
    lines = text.split('\n')
    
    # Try native-language pattern first (Greek style)
    for i, line in enumerate(lines):
        if re.search(pattern, line):
            native_title = line.strip()
            # Look ahead for "Theme N" English text
            english_part = ""
            for j in range(i+1, min(i+5, len(lines))):
                if re.search(r'Theme \d', lines[j], re.IGNORECASE):
                    english_part = lines[j].strip()
                    break
            
            theme_lines.append({
                'native': native_title,
                'english': english_part,
                'line_num': i
            })
    
    # If no native patterns found, try English "Theme N:" format
    if not theme_lines:
        for i, line in enumerate(lines):
            # Match "Theme 1:", "Theme 2:", etc. at start of line
            if re.match(r'^Theme [1-4]:\s+\S', line):
                full_title = line.strip()
                # Look ahead for English explanation
                english_part = ""
                for j in range(i+1, min(i+3, len(lines))):
                    if re.search(r'Theme \d is set in', lines[j]):
                        english_part = lines[j].strip()
                        break
                
                theme_lines.append({
                    'native': full_title,
                    'english': english_part,
                    'line_num': i
                })
    
    if theme_lines:
        print(f"[OK] Found {len(theme_lines)} themes")
        
        for idx, theme_info in enumerate(theme_lines, 1):
            # Combine native + English
            native = theme_info['native']
            english = theme_info['english']
            
            # Extract just the "Theme N: ..." part if available
            english_clean = ""
            if english:
                match = re.search(r'(Theme \d[^.]*\.)', english)
                if match:
                    english_clean = match.group(1)
                else:
                    english_clean = english[:60] + "..." if len(english) > 60 else english
            
            # Format: "Native Text (English Translation)"
            if english_clean:
                title = f"{native} ({english_clean})"
            else:
                title = native
            
            topics.append({
                'code': f'Theme{idx}',
                'title': title,
                'level': 1,
                'parent': 'Paper1'
            })
            
            print(f"[OK] Theme {idx}: {title[:100]}...")
    
    else:
        print("[WARN] No themes found with standard patterns")
    
    return topics


def scrape_language(subject_code):
    """Scrape a single language specification."""
    
    if subject_code not in LANGUAGES:
        print(f"[ERROR] Unknown subject code: {subject_code}")
        return None
    
    subject = LANGUAGES[subject_code]
    language_name = subject['name']
    
    print("=" * 80)
    print(f"EDEXCEL {language_name.upper()} ({subject_code}) - TOPIC SCRAPER")
    print("=" * 80)
    print(f"\nLanguage: {language_name}")
    print(f"Code: {subject_code}")
    print(f"PDF: {subject['pdf_url'][:70]}...")
    print()
    
    # Download PDF
    text = download_pdf(subject['pdf_url'], subject_code)
    if not text:
        return None
    
    # Extract themes
    topics = extract_themes(text, subject_code, language_name)
    
    if len(topics) <= 3:  # Only papers, no themes
        print(f"\n[WARN] Only found {len(topics)} topics (just papers)")
        print("[INFO] This language needs manual extraction")
        print(f"[INFO] Check debug-{subject_code.lower()}-spec.txt for theme section")
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
        print("[ERROR] No topics to upload")
        return False
    
    subject = LANGUAGES[subject_code]
    
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
    """Main execution - process all languages."""
    
    print("=" * 80)
    print("EDEXCEL A-LEVEL LANGUAGES - UNIVERSAL SCRAPER")
    print("=" * 80)
    print(f"\nLanguages to process: {len(LANGUAGES)}")
    print()
    
    for code in sorted(LANGUAGES.keys()):
        lang = LANGUAGES[code]['name']
        print(f"   {code}: {lang}")
    
    print("\n" + "=" * 80)
    
    # Allow single language or all
    if len(sys.argv) > 1:
        codes = [sys.argv[1].upper()]
        if codes[0] not in LANGUAGES:
            print(f"\n[ERROR] Unknown code: {codes[0]}")
            print(f"[INFO] Available: {', '.join(LANGUAGES.keys())}")
            return
    else:
        codes = sorted(LANGUAGES.keys())
        print(f"\n[INFO] Processing all {len(codes)} languages...")
        print("[INFO] This will take 10-15 minutes\n")
    
    results = {'success': [], 'failed': [], 'manual': []}
    
    for code in codes:
        try:
            print(f"\n{'=' * 80}\n")
            topics = scrape_language(code)
            
            if topics and len(topics) > 3:
                # Attempt upload
                if upload_topics(code, topics):
                    results['success'].append(code)
                    print(f"\n[OK] {LANGUAGES[code]['name']} COMPLETE!")
                else:
                    results['failed'].append(code)
                    print(f"\n[FAIL] {LANGUAGES[code]['name']} upload failed")
            else:
                results['manual'].append(code)
                print(f"\n[MANUAL] {LANGUAGES[code]['name']} needs manual extraction")
            
        except Exception as e:
            print(f"\n[ERROR] {LANGUAGES[code]['name']} failed: {e}")
            results['failed'].append(code)
            import traceback
            traceback.print_exc()
        
        print()
    
    # Final summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n✅ Successfully scraped: {len(results['success'])}")
    for code in results['success']:
        print(f"   • {code}: {LANGUAGES[code]['name']}")
    
    if results['manual']:
        print(f"\n⚠️  Need manual extraction: {len(results['manual'])}")
        for code in results['manual']:
            print(f"   • {code}: {LANGUAGES[code]['name']}")
            print(f"      → Check debug-{code.lower()}-spec.txt")
    
    if results['failed']:
        print(f"\n❌ Failed: {len(results['failed'])}")
        for code in results['failed']:
            print(f"   • {code}: {LANGUAGES[code]['name']}")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()

