"""
Check International Qualifications Data in Supabase
====================================================

Quick script to verify what data was uploaded and where to find it.
"""

import os
import sys
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

def check_qualification_types():
    """Check if International qualification types exist."""
    print("\n" + "="*60)
    print("QUALIFICATION TYPES")
    print("="*60)
    
    try:
        result = supabase.table('qualification_types').select('*').in_(
            'code', ['INTERNATIONAL_GCSE', 'INTERNATIONAL_A_LEVEL']
        ).execute()
        
        if result.data:
            for qual in result.data:
                print(f"✓ {qual['name']} (code: {qual['code']}, id: {qual['id']})")
        else:
            print("✗ No International qualification types found")
            
        return result.data
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return []

def check_exam_board():
    """Check if Edexcel exam board exists."""
    print("\n" + "="*60)
    print("EXAM BOARD")
    print("="*60)
    
    try:
        result = supabase.table('exam_boards').select('*').eq('code', 'Edexcel').execute()
        
        if result.data:
            board = result.data[0]
            print(f"✓ {board.get('full_name', 'Edexcel')} (id: {board['id']})")
            return board['id']
        else:
            print("✗ Edexcel exam board not found")
            return None
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None

def check_subjects(exam_board_id):
    """Check subjects in exam_board_subjects table."""
    print("\n" + "="*60)
    print("SUBJECTS (exam_board_subjects table)")
    print("="*60)
    
    if not exam_board_id:
        print("✗ Cannot check subjects without exam_board_id")
        return
    
    try:
        # Get qualification type IDs
        qual_result = supabase.table('qualification_types').select('id,code,name').in_(
            'code', ['INTERNATIONAL_GCSE', 'INTERNATIONAL_A_LEVEL']
        ).execute()
        
        qual_map = {q['id']: q['name'] for q in qual_result.data}
        
        # Get all Edexcel subjects
        result = supabase.table('exam_board_subjects').select(
            'id,subject_name,subject_code,qualification_type_id,specification_url'
        ).eq('exam_board_id', exam_board_id).execute()
        
        if result.data:
            # Filter for International subjects
            international_subjects = [
                s for s in result.data 
                if s['qualification_type_id'] in qual_map
            ]
            
            if international_subjects:
                print(f"\n✓ Found {len(international_subjects)} International subjects:")
                
                # Group by qualification
                ig_subjects = [s for s in international_subjects if qual_map.get(s['qualification_type_id']) == 'International GCSE']
                ial_subjects = [s for s in international_subjects if qual_map.get(s['qualification_type_id']) == 'International A Level']
                
                if ig_subjects:
                    print(f"\nInternational GCSE ({len(ig_subjects)} subjects):")
                    for s in ig_subjects[:5]:  # Show first 5
                        print(f"  - {s['subject_name']} (code: {s['subject_code']})")
                    if len(ig_subjects) > 5:
                        print(f"  ... and {len(ig_subjects) - 5} more")
                
                if ial_subjects:
                    print(f"\nInternational A Level ({len(ial_subjects)} subjects):")
                    for s in ial_subjects[:5]:  # Show first 5
                        print(f"  - {s['subject_name']} (code: {s['subject_code']})")
                    if len(ial_subjects) > 5:
                        print(f"  ... and {len(ial_subjects) - 5} more")
            else:
                print("✗ No International subjects found")
                
            # Show all Edexcel subjects for comparison
            print(f"\nTotal Edexcel subjects in database: {len(result.data)}")
        else:
            print("✗ No Edexcel subjects found")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()

def check_staging_subjects():
    """Check subjects in staging_aqa_subjects table."""
    print("\n" + "="*60)
    print("STAGING SUBJECTS (staging_aqa_subjects table)")
    print("="*60)
    
    try:
        result = supabase.table('staging_aqa_subjects').select('*').eq(
            'exam_board', 'Edexcel'
        ).execute()
        
        if result.data:
            # Filter for International subjects
            ig_subjects = [s for s in result.data if 'International GCSE' in s.get('qualification_type', '')]
            ial_subjects = [s for s in result.data if 'International A Level' in s.get('qualification_type', '')]
            
            total = len(ig_subjects) + len(ial_subjects)
            
            if total > 0:
                print(f"\n✓ Found {total} International subjects in staging:")
                print(f"  - International GCSE: {len(ig_subjects)}")
                print(f"  - International A Level: {len(ial_subjects)}")
                
                if ig_subjects:
                    print(f"\nSample International GCSE subjects:")
                    for s in ig_subjects[:3]:
                        print(f"  - {s['subject_name']}")
                
                if ial_subjects:
                    print(f"\nSample International A Level subjects:")
                    for s in ial_subjects[:3]:
                        print(f"  - {s['subject_name']}")
            else:
                print("✗ No International subjects found in staging")
        else:
            print("✗ No Edexcel subjects found in staging")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")

def check_topics():
    """Check if any topics were uploaded."""
    print("\n" + "="*60)
    print("TOPICS (staging_aqa_topics table)")
    print("="*60)
    
    try:
        # Get International GCSE Biology subject
        subject_result = supabase.table('staging_aqa_subjects').select('id,subject_name').eq(
            'exam_board', 'Edexcel'
        ).ilike('subject_name', '%Biology%International%').execute()
        
        if subject_result.data:
            for subject in subject_result.data:
                topics_result = supabase.table('staging_aqa_topics').select('id,topic_code,topic_name,topic_level').eq(
                    'subject_id', subject['id']
                ).limit(10).execute()
                
                if topics_result.data:
                    print(f"\n✓ {subject['subject_name']}: {len(topics_result.data)} topics (showing 10):")
                    for topic in topics_result.data[:5]:
                        print(f"  [{topic['topic_level']}] {topic['topic_code']}: {topic['topic_name'][:60]}")
                else:
                    print(f"\n✗ {subject['subject_name']}: No topics found")
        else:
            print("✗ No Biology subject found")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")

def main():
    print("\n" + "#"*60)
    print("# CHECKING INTERNATIONAL QUALIFICATIONS DATA")
    print("#"*60)
    
    # 1. Check qualification types
    qual_types = check_qualification_types()
    
    # 2. Check exam board
    exam_board_id = check_exam_board()
    
    # 3. Check subjects in main table
    check_subjects(exam_board_id)
    
    # 4. Check subjects in staging
    check_staging_subjects()
    
    # 5. Check topics
    check_topics()
    
    # Summary
    print("\n" + "="*60)
    print("WHERE TO FIND THE DATA")
    print("="*60)
    print("\nIn Supabase Data Viewer, look for:")
    print("\n1. Main Production Tables:")
    print("   - Table: exam_board_subjects")
    print("   - Filter: exam_board_id = (Edexcel's UUID)")
    print("   - Then filter by qualification_type_id for International GCSE/A Level")
    
    print("\n2. Staging Tables (where scraped topics are):")
    print("   - Table: staging_aqa_subjects")
    print("   - Filter: exam_board = 'Edexcel'")
    print("   - Filter: qualification_type contains 'International'")
    
    print("\n3. Topics Table:")
    print("   - Table: staging_aqa_topics")
    print("   - Join with staging_aqa_subjects on subject_id")
    print("   - Filter by subject from above")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    main()

