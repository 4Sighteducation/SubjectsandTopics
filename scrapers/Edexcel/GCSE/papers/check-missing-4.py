import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')
supabase = create_client(supabase_url, supabase_key)

subjects_to_check = [
    'GCSE-DesignTech',
    'GCSE-ComputerScience', 
    'GCSE-Psychology',
    'GCSE-Statistics'
]

print("Checking the 4 subjects with missing/few papers:")
print("=" * 70)

for subject_code in subjects_to_check:
    result = supabase.table('staging_aqa_subjects').select('id,subject_name,subject_code').eq('subject_code', subject_code).eq('exam_board', 'Edexcel').eq('qualification_type', 'GCSE').execute()
    
    if result.data:
        subject_id = result.data[0]['id']
        subject_name = result.data[0]['subject_name']
        actual_code = result.data[0]['subject_code']
        
        papers = supabase.table('staging_aqa_exam_papers').select('*').eq('subject_id', subject_id).execute()
        count = len(papers.data) if papers.data else 0
        
        print(f"\n{subject_name} ({actual_code}):")
        print(f"  Papers in DB: {count}")
        
        if count > 0 and papers.data:
            # Show years
            years = sorted(set([p['year'] for p in papers.data]))
            print(f"  Years: {years}")
            # Show sample
            sample_url = papers.data[0].get('question_paper_url', '')
            if sample_url:
                print(f"  Sample: {sample_url.split('/')[-1]}")
    else:
        print(f"\n{subject_code}: NOT FOUND in database")

