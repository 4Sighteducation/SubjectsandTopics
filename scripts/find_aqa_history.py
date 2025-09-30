import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.supabase_client import SupabaseUploader
from dotenv import load_dotenv

load_dotenv()

uploader = SupabaseUploader()

# Get exam boards
boards = uploader.client.table('exam_boards').select('*').execute()
print("\nExam Boards:")
for b in boards.data:
    print(f"  {b['code']}: {b['id']}")
    if b['code'] == 'AQA':
        aqa_id = b['id']
        print(f"\n  ^^^ AQA ID: {aqa_id}")

# Get qualification types
quals = uploader.client.table('qualification_types').select('*').execute()
print("\nQualification Types:")
for q in quals.data:
    print(f"  {q['code']}: {q['id']}")
    if 'a-level' in q['code'].lower():
        alevel_id = q['id']
        print(f"  ^^^ A-Level ID: {alevel_id}")

# Now find AQA History A-Level
print("\nSearching for AQA History A-Level...")
history = uploader.client.table('exam_board_subjects').select('*').eq(
    'subject_name', 'History'
).execute()

for h in history.data:
    print(f"\nHistory record: {h['id']}")
    print(f"  exam_board_id: {h['exam_board_id']}")
    print(f"  qualification_type_id: {h['qualification_type_id']}")
    
print("\n✅ Use this ID for AQA History A-Level uploads!")
