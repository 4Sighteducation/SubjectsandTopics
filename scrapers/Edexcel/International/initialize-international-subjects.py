"""
Initialize International Qualifications in Supabase
====================================================

This script:
1. Ensures 'International GCSE' and 'International A Level' qualification types exist
2. Uploads all International GCSE and International A Level subjects to Supabase
3. Creates the basic structure ready for topic scraping

Usage:
    python initialize-international-subjects.py
"""

import os
import sys
import json
from pathlib import Path
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

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

def ensure_qualification_types():
    """Ensure International qualification types exist in the database."""
    print("\n[INFO] Checking qualification types...")
    
    qual_types = [
        {
            'code': 'INTERNATIONAL_GCSE',
            'name': 'International GCSE'
        },
        {
            'code': 'INTERNATIONAL_A_LEVEL',
            'name': 'International A Level'
        }
    ]
    
    for qual in qual_types:
        try:
            # Check if exists
            result = supabase.table('qualification_types').select('id').eq('code', qual['code']).execute()
            
            if result.data and len(result.data) > 0:
                print(f"[OK] {qual['name']} already exists")
            else:
                # Create it
                insert_result = supabase.table('qualification_types').insert(qual).execute()
                if insert_result.data:
                    print(f"[OK] Created {qual['name']}")
                else:
                    print(f"[WARNING] Could not create {qual['name']}")
        except Exception as e:
            print(f"[ERROR] Error with {qual['name']}: {str(e)}")

def ensure_exam_board():
    """Ensure Edexcel exam board exists."""
    print("\n[INFO] Checking Edexcel exam board...")
    
    try:
        result = supabase.table('exam_boards').select('id').eq('code', 'Edexcel').execute()
        
        if result.data and len(result.data) > 0:
            print(f"[OK] Edexcel exam board exists (ID: {result.data[0]['id']})")
            return result.data[0]['id']
        else:
            # Create it
            board_data = {
                'code': 'Edexcel',
                'full_name': 'Edexcel (Pearson)',
                'country': 'UK'
            }
            insert_result = supabase.table('exam_boards').insert(board_data).execute()
            if insert_result.data:
                print(f"[OK] Created Edexcel exam board (ID: {insert_result.data[0]['id']})")
                return insert_result.data[0]['id']
            else:
                print(f"[ERROR] Could not create Edexcel exam board")
                return None
    except Exception as e:
        print(f"[ERROR] Error checking exam board: {str(e)}")
        return None

def upload_subjects(subjects_file, qualification_code):
    """Upload subjects from JSON file to Supabase."""
    print(f"\n[INFO] Loading subjects from {subjects_file}...")
    
    try:
        with open(subjects_file, 'r', encoding='utf-8') as f:
            subjects = json.load(f)
        
        print(f"[OK] Loaded {len(subjects)} subjects")
        
        # Get qualification_type_id
        qual_result = supabase.table('qualification_types').select('id').eq('code', qualification_code).execute()
        if not qual_result.data:
            print(f"[ERROR] Qualification type {qualification_code} not found")
            return 0
        
        qualification_type_id = qual_result.data[0]['id']
        
        # Get exam_board_id
        board_result = supabase.table('exam_boards').select('id').eq('code', 'Edexcel').execute()
        if not board_result.data:
            print(f"[ERROR] Edexcel exam board not found")
            return 0
        
        exam_board_id = board_result.data[0]['id']
        
        # Upload each subject
        uploaded = 0
        updated = 0
        
        for subject in subjects:
            try:
                # Check if subject already exists
                existing = supabase.table('exam_board_subjects').select('id').eq(
                    'subject_name', subject['name']
                ).eq(
                    'exam_board_id', exam_board_id
                ).eq(
                    'qualification_type_id', qualification_type_id
                ).execute()
                
                subject_data = {
                    'exam_board_id': exam_board_id,
                    'qualification_type_id': qualification_type_id,
                    'subject_name': subject['name'],
                    'subject_code': subject['code'],
                    'specification_url': subject['pdf_url'],
                    'is_current': True
                }
                
                if existing.data and len(existing.data) > 0:
                    # Update existing
                    update_result = supabase.table('exam_board_subjects').update(subject_data).eq(
                        'id', existing.data[0]['id']
                    ).execute()
                    updated += 1
                    print(f"[OK] Updated: {subject['name']}")
                else:
                    # Insert new
                    insert_result = supabase.table('exam_board_subjects').insert(subject_data).execute()
                    uploaded += 1
                    print(f"[OK] Created: {subject['name']}")
                    
            except Exception as e:
                print(f"[ERROR] Failed to upload {subject['name']}: {str(e)}")
        
        print(f"\n[SUMMARY] Created: {uploaded}, Updated: {updated}")
        return uploaded + updated
        
    except FileNotFoundError:
        print(f"[ERROR] File not found: {subjects_file}")
        return 0
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in {subjects_file}: {str(e)}")
        return 0
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        return 0

def main():
    """Main execution."""
    print("=" * 60)
    print("INITIALIZE EDEXCEL INTERNATIONAL QUALIFICATIONS")
    print("=" * 60)
    
    # Step 1: Ensure qualification types exist
    ensure_qualification_types()
    
    # Step 2: Ensure exam board exists
    exam_board_id = ensure_exam_board()
    if not exam_board_id:
        print("\n[ERROR] Cannot proceed without exam board")
        sys.exit(1)
    
    # Step 3: Upload International GCSE subjects
    script_dir = Path(__file__).parent
    ig_file = script_dir / "International-GCSE" / "international-gcse-subjects.json"
    ig_count = upload_subjects(ig_file, 'INTERNATIONAL_GCSE')
    
    # Step 4: Upload International A Level subjects
    ial_file = script_dir / "International-A-Level" / "international-a-level-subjects.json"
    ial_count = upload_subjects(ial_file, 'INTERNATIONAL_A_LEVEL')
    
    # Summary
    print("\n" + "=" * 60)
    print("INITIALIZATION COMPLETE")
    print("=" * 60)
    print(f"International GCSE subjects: {ig_count}")
    print(f"International A Level subjects: {ial_count}")
    print(f"Total: {ig_count + ial_count}")
    print("\nNext steps:")
    print("1. Run the PDF scraper to extract topics")
    print("2. Review and refine topics as needed")
    print("=" * 60)

if __name__ == '__main__':
    main()

