"""
Edexcel English Literature (9ET0) - Manual Topic Upload
3 Components with LOTS of prescribed texts organized by theme/genre
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT = {
    'code': '9ET0',
    'name': 'English Literature',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/English%20Literature/2015/Specification%20and%20sample%20assessments/Pearson_Edexcel_Level_3_Advanced_GCE_in_English_Literature_Specification_issue11.pdf'
}

def create_topics():
    """Create English Literature topics with all prescribed texts."""
    topics = []
    
    # Level 0: Components (skip NEA)
    topics.extend([
        {'code': 'Component1', 'title': 'Component 1: Drama', 'level': 0, 'parent': None},
        {'code': 'Component2', 'title': 'Component 2: Prose', 'level': 0, 'parent': None},
        {'code': 'Component3', 'title': 'Component 3: Poetry', 'level': 0, 'parent': None},
    ])
    
    # =========================================================================
    # COMPONENT 1: DRAMA
    # =========================================================================
    
    topics.extend([
        {'code': 'C1-Shakespeare', 'title': 'Shakespeare', 'level': 1, 'parent': 'Component1'},
        {'code': 'C1-OtherDrama', 'title': 'Other Drama', 'level': 1, 'parent': 'Component1'},
    ])
    
    # Shakespeare - Tragedy or Comedy (Level 2)
    topics.extend([
        {'code': 'C1-S-Tragedy', 'title': 'Tragedy', 'level': 2, 'parent': 'C1-Shakespeare'},
        {'code': 'C1-S-Comedy', 'title': 'Comedy', 'level': 2, 'parent': 'C1-Shakespeare'},
    ])
    
    # Shakespeare Tragedy Texts (Level 3)
    tragedy_texts = [
        'Antony and Cleopatra',
        'Hamlet',
        'King Lear',
        'Othello'
    ]
    for text in tragedy_texts:
        topics.append({
            'code': f'C1-S-T-{text.replace(" ", "")}',
            'title': text,
            'level': 3,
            'parent': 'C1-S-Tragedy'
        })
    
    # Shakespeare Comedy Texts (Level 3)
    comedy_texts = [
        'A Midsummer Night\'s Dream',
        'Measure for Measure',
        'The Taming of the Shrew',
        'Twelfth Night'
    ]
    for text in comedy_texts:
        topics.append({
            'code': f'C1-S-C-{text.replace(" ", "").replace("\'", "")}',
            'title': text,
            'level': 3,
            'parent': 'C1-S-Comedy'
        })
    
    # Other Drama (Level 2)
    topics.extend([
        {'code': 'C1-OD-Pre1900', 'title': 'Pre-1900 Drama', 'level': 2, 'parent': 'C1-OtherDrama'},
        {'code': 'C1-OD-Post1900', 'title': 'Post-1900 Drama', 'level': 2, 'parent': 'C1-OtherDrama'},
    ])
    
    # Pre-1900 Drama Texts (Level 3)
    pre1900_drama = [
        'Doctor Faustus by Christopher Marlowe',
        'The Duchess of Malfi by John Webster',
        'The Importance of Being Earnest by Oscar Wilde',
        'The Rover by Aphra Behn'
    ]
    for text in pre1900_drama:
        topics.append({
            'code': f'C1-OD-Pre-{len(topics)}',
            'title': text,
            'level': 3,
            'parent': 'C1-OD-Pre1900'
        })
    
    # Post-1900 Drama Texts (Level 3)
    post1900_drama = [
        'Les Blancs by Lorraine Hansberry',
        'A Streetcar Named Desire by Tennessee Williams',
        'Sweat by Lynn Nottage',
        'Waiting for Godot by Samuel Beckett'
    ]
    for text in post1900_drama:
        topics.append({
            'code': f'C1-OD-Post-{len(topics)}',
            'title': text,
            'level': 3,
            'parent': 'C1-OD-Post1900'
        })
    
    # =========================================================================
    # COMPONENT 2: PROSE (Thematic)
    # =========================================================================
    
    topics.append({
        'code': 'C2-Themes',
        'title': 'Thematic Prose Study (select 2 texts, at least 1 pre-1900)',
        'level': 1,
        'parent': 'Component2'
    })
    
    # Themes (Level 2)
    prose_themes = [
        ('Childhood', [
            'Hard Times by Charles Dickens (pre-1900)',
            'What Maisie Knew by Henry James (pre-1900)',
            'Atonement by Ian McEwan (post-1900)',
            'The Color Purple by Alice Walker (post-1900)'
        ]),
        ('Colonisation and its Aftermath', [
            'The Adventures of Huckleberry Finn by Mark Twain (pre-1900)',
            'Heart of Darkness by Joseph Conrad (pre-1900)',
            'Home Fire by Kamila Shamsie (post-1900)',
            'The Lonely Londoners by Sam Selvon (post-1900)'
        ]),
        ('Crime and Detection', [
            "Lady Audley's Secret by Mary Elizabeth Braddon (pre-1900)",
            'The Moonstone by Wilkie Collins (pre-1900)',
            'The Cutting Season by Attica Locke (post-1900)',
            'In Cold Blood by Truman Capote (post-1900)'
        ]),
        ('Science and Society', [
            'Frankenstein by Mary Shelley (pre-1900)',
            'The War of the Worlds by H G Wells (pre-1900)',
            'The Handmaid\'s Tale by Margaret Atwood (post-1900)',
            'Never Let Me Go by Kazuo Ishiguro (post-1900)'
        ]),
        ('The Supernatural', [
            'Dracula by Bram Stoker (pre-1900)',
            'The Picture of Dorian Gray by Oscar Wilde (pre-1900)',
            'Beloved by Toni Morrison (post-1900)',
            'The Little Stranger by Sarah Waters (post-1900)'
        ]),
        ('Women and Society', [
            'Tess of the D\'Urbervilles by Thomas Hardy (pre-1900)',
            'Wuthering Heights by Emily Brontë (pre-1900)',
            'Mrs Dalloway by Virginia Woolf (post-1900)',
            'A Thousand Splendid Suns by Khaled Hosseini (post-1900)'
        ])
    ]
    
    for theme_name, texts in prose_themes:
        theme_code = f'C2-{theme_name.replace(" ", "").replace("\'", "")}'
        topics.append({
            'code': theme_code,
            'title': f'{theme_name}',
            'level': 2,
            'parent': 'C2-Themes'
        })
        
        # Texts under theme (Level 3)
        for i, text in enumerate(texts, 1):
            topics.append({
                'code': f'{theme_code}-{i}',
                'title': text,
                'level': 3,
                'parent': theme_code
            })
    
    # =========================================================================
    # COMPONENT 3: POETRY
    # =========================================================================
    
    topics.extend([
        {'code': 'C3-Modern', 'title': 'Post-2000 Poetry: Poems of the Decade', 'level': 1, 'parent': 'Component3'},
        {'code': 'C3-Historical', 'title': 'Pre- or Post-1900 Poetry Collections', 'level': 1, 'parent': 'Component3'},
    ])
    
    # Historical Poetry - Pre-1900 (Level 2)
    topics.extend([
        {'code': 'C3-Pre1900', 'title': 'Pre-1900 Poetry Anthologies', 'level': 2, 'parent': 'C3-Historical'},
        {'code': 'C3-Post1900', 'title': 'Post-1900 Poetry Anthologies', 'level': 2, 'parent': 'C3-Historical'},
    ])
    
    # Pre-1900 Poetry Collections (Level 3)
    pre1900_poetry = [
        ('Medieval', [
            'Everyman and Medieval Miracle Plays',
            "Geoffrey Chaucer: The Wife of Bath's Prologue and Tale"
        ]),
        ('Metaphysical', [
            'Metaphysical Poetry anthology',
            'John Donne Selected Poems'
        ]),
        ('Romantic', [
            'English Romantic Verse',
            'John Keats Selected Poems'
        ]),
        ('Victorian', [
            'The New Oxford Book of Victorian Verse',
            'Christina Rossetti Selected Poems'
        ])
    ]
    
    for period, collections in pre1900_poetry:
        period_code = f'C3-P-{period}'
        topics.append({
            'code': period_code,
            'title': f'The {period} Period',
            'level': 3,
            'parent': 'C3-Pre1900'
        })
        
        for i, collection in enumerate(collections, 1):
            topics.append({
                'code': f'{period_code}-{i}',
                'title': collection,
                'level': 4,
                'parent': period_code
            })
    
    # Post-1900 Poetry Collections (Level 3)
    post1900_poetry = [
        ('Modernism', [
            'The Great Modern Poets',
            'T S Eliot Selected Poems'
        ]),
        ('Movement', [
            'The Oxford Book of Twentieth Century English Verse',
            'Philip Larkin: The Less Deceived'
        ])
    ]
    
    for period, collections in post1900_poetry:
        period_code = f'C3-Post-{period}'
        topics.append({
            'code': period_code,
            'title': f'The {period} Period',
            'level': 3,
            'parent': 'C3-Post1900'
        })
        
        for i, collection in enumerate(collections, 1):
            topics.append({
                'code': f'{period_code}-{i}',
                'title': collection,
                'level': 4,
                'parent': period_code
            })
    
    return topics

def upload_topics(topics):
    """Upload to Supabase."""
    print("\n[INFO] Uploading to database...")
    
    # Get/create subject
    subject_result = supabase.table('staging_aqa_subjects').upsert({
        'subject_name': f"{SUBJECT['name']} (A-Level)",
        'subject_code': SUBJECT['code'],
        'qualification_type': 'A-Level',
        'specification_url': SUBJECT['pdf_url'],
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

def main():
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 80)
    print("EDEXCEL ENGLISH LITERATURE (9ET0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print("\nNote: NEA excluded, includes all prescribed texts organized by theme/genre")
    
    try:
        topics = create_topics()
        
        # Show distribution
        levels = {}
        for t in topics:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print(f"\n[INFO] Created {len(topics)} topics")
        print("\n   Level distribution:")
        for l in sorted(levels.keys()):
            print(f"   Level {l}: {levels[l]} topics")
        
        upload_topics(topics)
        
        print("\n" + "=" * 80)
        print("[OK] ENGLISH LITERATURE COMPLETE!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()