"""
Religious Studies B - Structure Uploader
========================================

Separate uploader for Religious Studies B.
Different format from RSA - has "Area of Study 1:" (with colon), then "1A", "2A", etc.

Usage:
    python upload-religious-studies-b.py
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

SUBJECT_INFO = {
    'code': 'GCSE-RSB',
    'name': 'Religious Studies B',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Religious%20Studies/2016/Specification%20and%20sample%20assessments/specification-gcse-l1-l2-religious-studies-b.pdf'
}

# Paste your Religious Studies B hierarchy here
HIERARCHY_TEXT = """
Area of Study 1: Religion and Ethics
1A Catholic Christianity
Section 1: Catholic Beliefs

1.1 The Trinity
1.2 Biblical understandings of God as a Trinity of Persons
1.3 Creation
1.4 The significance of the Creation account in understanding the nature of humanity
1.5 The Incarnation
1.6 The events in the Paschal Mystery
1.7 The significance of the life, death, resurrection, and ascension of Jesus
1.8 Catholic beliefs about eschatology
Section 2: Marriage and the Family

2.1 The importance and purpose of marriage for Catholics
2.2 Catholic teaching about the importance of sexual relationships
2.3 Catholic teaching about the purpose and importance of the family
2.4 Support for the family in the local Catholic parish
2.5 Catholic teaching on family planning and the regulation of births
2.6 Catholic teaching about divorce, annulment, and remarriage
2.7 Catholic teaching about the equality of men and women in the family
2.8 Catholic teachings about gender prejudice and discrimination
Section 3: Living the Catholic Life

3.1 The sacramental nature of reality
3.2 Liturgical worship within Catholic Christianity
3.3 The funeral rite as a liturgical celebration of the Church
3.4 Prayer as the 'raising of hearts and minds to God'
3.5 The role and importance of forms of popular piety
3.6 Pilgrimage
3.7 Catholic Social Teaching
3.8 Catholic mission and evangelism
Section 4: Matters of Life and Death

4.1 Catholic teachings about the origins and value of the universe
4.2 Catholic teachings about the sanctity of life
4.3 Catholic responses to scientific and non-religious explanations about the origins and value of human life
4.4 Implications of Catholic teachings about the value and sanctity of life for the issue of abortion
4.5 Catholic teachings and beliefs about life after death
4.6 Catholic responses to non-religious arguments against life after death
4.7 Implications of Catholic teachings about the value and sanctity of life for the issue of euthanasia
4.8 Catholic responses to issues in the natural world
"""


def parse_rsb_hierarchy(text):
    """Parse Religious Studies B hierarchy."""
    lines = [line.rstrip() for line in text.strip().split('\n') if line.strip()]
    
    topics = []
    current_area = None  # Level 0
    current_subarea = None  # Level 1
    current_section = None  # Level 2
    
    for line in lines:
        # Detect "Area of Study X:" (Level 0)
        if re.match(r'^Area of Study\s+\d+:', line, re.IGNORECASE):
            area_match = re.match(r'^Area of Study\s+(\d+):\s*(.+)$', line, re.IGNORECASE)
            if area_match:
                area_num = area_match.group(1)
                area_name = area_match.group(2).strip()
                area_code = f"AreaofStudy{area_num}"
                
                topics.append({
                    'code': area_code,
                    'title': line.strip(),
                    'level': 0,
                    'parent': None
                })
                
                current_area = area_code
                current_subarea = None
                current_section = None
                print(f"[L0] {line.strip()}")
                continue
        
        # Detect "1A Name" (Level 1 sub-areas)
        if re.match(r'^(\d+)([A-Z])\s+', line) and current_area:
            subarea_match = re.match(r'^(\d+)([A-Z])\s+(.+)$', line)
            if subarea_match:
                num = subarea_match.group(1)
                letter = subarea_match.group(2)
                name = subarea_match.group(3).strip()
                subarea_code = f"{current_area}_{num}{letter}"
                
                topics.append({
                    'code': subarea_code,
                    'title': f"{num}{letter} {name}",
                    'level': 1,
                    'parent': current_area
                })
                
                current_subarea = subarea_code
                current_section = None
                print(f"  [L1] {num}{letter} {name}")
                continue
        
        # Detect "Section X:" (Level 2)
        if re.match(r'^Section\s+\d+:', line, re.IGNORECASE) and current_subarea:
            section_match = re.match(r'^Section\s+(\d+):\s*(.+)$', line, re.IGNORECASE)
            if section_match:
                sect_num = section_match.group(1)
                sect_name = section_match.group(2).strip()
                section_code = f"{current_subarea}_Section{sect_num}"
                
                topics.append({
                    'code': section_code,
                    'title': f"Section {sect_num}: {sect_name}",
                    'level': 2,
                    'parent': current_subarea
                })
                
                current_section = section_code
                print(f"    [L2] Section {sect_num}: {sect_name}")
                continue
        
        # Detect "1.1 Name" (Level 3)
        if re.match(r'^\d+\.\d+\s+', line) and current_section:
            topic_match = re.match(r'^(\d+\.\d+)\s+(.+)$', line)
            if topic_match:
                topic_num = topic_match.group(1)
                topic_name = topic_match.group(2).strip()
                topic_code = f"{current_section}_T{topic_num.replace('.', '_')}"
                
                topics.append({
                    'code': topic_code,
                    'title': f"{topic_num} {topic_name}",
                    'level': 3,
                    'parent': current_section
                })
                
                print(f"      [L3] {topic_num} {topic_name}")
                continue
    
    return topics


def upload_topics(topics):
    """Upload to Supabase."""
    print(f"\n[INFO] Uploading {len(topics)} topics...")
    
    try:
        # Create/update subject
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT_INFO['name']} ({SUBJECT_INFO['qualification']})",
            'subject_code': SUBJECT_INFO['code'],
            'qualification_type': SUBJECT_INFO['qualification'],
            'specification_url': SUBJECT_INFO['pdf_url'],
            'exam_board': SUBJECT_INFO['exam_board']
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
            'exam_board': SUBJECT_INFO['exam_board']
        } for t in topics]
        
        inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted.data)} topics")
        
        # Link parent relationships level by level
        code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
        
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
        print("[SUCCESS] RELIGIOUS STUDIES B - UPLOAD COMPLETE!")
        print("=" * 80)
        for level in sorted(levels.keys()):
            count = levels[level]
            level_names = {
                0: 'Main Areas',
                1: 'Sub-Areas',
                2: 'Sections',
                3: 'Topics'
            }
            print(f"   Level {level} ({level_names.get(level, f'Level {level}')}): {count}")
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
    print("RELIGIOUS STUDIES B - STRUCTURE UPLOADER")
    print("=" * 80)
    
    topics = parse_rsb_hierarchy(HIERARCHY_TEXT)
    
    if not topics:
        print("[ERROR] No topics found!")
        return
    
    print(f"\n[OK] Parsed {len(topics)} topics")
    
    success = upload_topics(topics)
    
    if success:
        print("\n✅ COMPLETE!")
    else:
        print("\n❌ FAILED")


if __name__ == '__main__':
    main()

