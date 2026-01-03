"""
GCSE Music - Manual Structure Upload
=====================================

Simple structure for Music:
- Level 0: Component 3 - Appraising
- Level 1: Musical Elements, Musical Contexts, Musical Language, Areas of Study
- Level 2: Individual items under each category

Usage:
    python upload-music-structure.py
"""

import os
import sys
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

SUBJECT = {
    'code': 'GCSE-Music',
    'name': 'Music',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Music/2016/specification/Pearson_Edexcel_GCSE_9_to_1_in_Music_Specification_issue4.pdf'
}

TOPICS = [
    # Level 0: Component
    {'code': 'Component3', 'title': 'Component 3: Appraising', 'level': 0, 'parent': None},
    
    # Level 1: Main categories
    {'code': 'Component3_Elements', 'title': 'Musical Elements', 'level': 1, 'parent': 'Component3'},
    {'code': 'Component3_Contexts', 'title': 'Musical Contexts', 'level': 1, 'parent': 'Component3'},
    {'code': 'Component3_Language', 'title': 'Musical Language', 'level': 1, 'parent': 'Component3'},
    {'code': 'Component3_AreasOfStudy', 'title': 'Areas of Study', 'level': 1, 'parent': 'Component3'},
    
    # ===== MUSICAL ELEMENTS =====
    # Level 2: Musical Elements categories
    {'code': 'Component3_Elements_Pitch', 'title': 'Organisation of pitch (melodically and harmonically)', 'level': 2, 'parent': 'Component3_Elements'},
    {'code': 'Component3_Elements_Tonality', 'title': 'Tonality', 'level': 2, 'parent': 'Component3_Elements'},
    {'code': 'Component3_Elements_Structure', 'title': 'Structure', 'level': 2, 'parent': 'Component3_Elements'},
    {'code': 'Component3_Elements_Sonority', 'title': 'Sonority', 'level': 2, 'parent': 'Component3_Elements'},
    {'code': 'Component3_Elements_Texture', 'title': 'Texture', 'level': 2, 'parent': 'Component3_Elements'},
    {'code': 'Component3_Elements_Tempo', 'title': 'Tempo, metre, and rhythm', 'level': 2, 'parent': 'Component3_Elements'},
    {'code': 'Component3_Elements_Dynamics', 'title': 'Dynamics', 'level': 2, 'parent': 'Component3_Elements'},
    
    # Level 3: Pitch details
    {'code': 'Component3_Elements_Pitch_Chords', 'title': 'Simple chord progressions (e.g., perfect and imperfect cadences)', 'level': 3, 'parent': 'Component3_Elements_Pitch'},
    {'code': 'Component3_Elements_Pitch_Melodic', 'title': 'Basic melodic devices', 'level': 3, 'parent': 'Component3_Elements_Pitch'},
    
    # Level 3: Tonality details
    {'code': 'Component3_Elements_Tonality_Major', 'title': 'Major', 'level': 3, 'parent': 'Component3_Elements_Tonality'},
    {'code': 'Component3_Elements_Tonality_Minor', 'title': 'Minor', 'level': 3, 'parent': 'Component3_Elements_Tonality'},
    {'code': 'Component3_Elements_Tonality_Modulations', 'title': 'Basic modulations (e.g., tonic, dominant)', 'level': 3, 'parent': 'Component3_Elements_Tonality'},
    
    # Level 3: Structure details
    {'code': 'Component3_Elements_Structure_Organisation', 'title': 'Organisation of musical material', 'level': 3, 'parent': 'Component3_Elements_Structure'},
    {'code': 'Component3_Elements_Structure_Simple', 'title': 'Simple structures (e.g., verse and chorus, call and response, binary, theme and variations)', 'level': 3, 'parent': 'Component3_Elements_Structure'},
    
    # Level 3: Sonority details
    {'code': 'Component3_Elements_Sonority_Timbres', 'title': 'Recognition of a range of instrumental and vocal timbres', 'level': 3, 'parent': 'Component3_Elements_Sonority'},
    {'code': 'Component3_Elements_Sonority_Articulation', 'title': 'Articulation (e.g., legato, staccato)', 'level': 3, 'parent': 'Component3_Elements_Sonority'},
    
    # Level 3: Texture details
    {'code': 'Component3_Elements_Texture_Parts', 'title': 'How musical lines (parts) fit together', 'level': 3, 'parent': 'Component3_Elements_Texture'},
    {'code': 'Component3_Elements_Texture_Combinations', 'title': 'Simple textural combinations (e.g., unison, chordal, solo)', 'level': 3, 'parent': 'Component3_Elements_Texture'},
    
    # Level 3: Tempo details
    {'code': 'Component3_Elements_Tempo_Pulse', 'title': 'Pulse', 'level': 3, 'parent': 'Component3_Elements_Tempo'},
    {'code': 'Component3_Elements_Tempo_Simple', 'title': 'Simple time', 'level': 3, 'parent': 'Component3_Elements_Tempo'},
    {'code': 'Component3_Elements_Tempo_Compound', 'title': 'Compound time', 'level': 3, 'parent': 'Component3_Elements_Tempo'},
    {'code': 'Component3_Elements_Tempo_Rhythmic', 'title': 'Basic rhythmic devices (e.g., dotted rhythms)', 'level': 3, 'parent': 'Component3_Elements_Tempo'},
    
    # Level 3: Dynamics details
    {'code': 'Component3_Elements_Dynamics_Devices', 'title': 'Basic dynamic devices (e.g., crescendo, diminuendo)', 'level': 3, 'parent': 'Component3_Elements_Dynamics'},
    
    # ===== MUSICAL CONTEXTS =====
    # Level 2: Musical Contexts categories
    {'code': 'Component3_Contexts_Purpose', 'title': 'Effect of purpose and intention', 'level': 2, 'parent': 'Component3_Contexts'},
    {'code': 'Component3_Contexts_Audience', 'title': 'Effect of audience, time, and place', 'level': 2, 'parent': 'Component3_Contexts'},
    
    # Level 3: Purpose details
    {'code': 'Component3_Contexts_Purpose_Role', 'title': "Composer's, performer's, or commissioner's role in music creation, development, and performance", 'level': 3, 'parent': 'Component3_Contexts_Purpose'},
    
    # Level 3: Audience details
    {'code': 'Component3_Contexts_Audience_Venue', 'title': 'Venue', 'level': 3, 'parent': 'Component3_Contexts_Audience'},
    {'code': 'Component3_Contexts_Audience_Occasion', 'title': 'Occasion', 'level': 3, 'parent': 'Component3_Contexts_Audience'},
    
    # ===== MUSICAL LANGUAGE =====
    # Level 2: Musical Language categories
    {'code': 'Component3_Language_Notation', 'title': 'Reading and writing of staff notation', 'level': 2, 'parent': 'Component3_Language'},
    {'code': 'Component3_Language_Chords', 'title': 'Major and minor chords', 'level': 2, 'parent': 'Component3_Language'},
    {'code': 'Component3_Language_Vocabulary', 'title': 'Recognising and using appropriate musical vocabulary and terminology', 'level': 2, 'parent': 'Component3_Language'},
    {'code': 'Component3_Language_Scores', 'title': 'Recognising and using appropriate terminology related to scores', 'level': 2, 'parent': 'Component3_Language'},
    
    # Level 3: Notation details
    {'code': 'Component3_Language_Notation_Clefs', 'title': 'Treble-clef and bass-clef note names', 'level': 3, 'parent': 'Component3_Language_Notation'},
    {'code': 'Component3_Language_Notation_Rhythmic', 'title': 'Rhythmic notation in simple time', 'level': 3, 'parent': 'Component3_Language_Notation'},
    {'code': 'Component3_Language_Notation_Keys', 'title': 'Key signatures up to four sharps and four flats', 'level': 3, 'parent': 'Component3_Language_Notation'},
    
    # Level 3: Chords details
    {'code': 'Component3_Language_Chords_Symbols', 'title': 'Associated chord symbols', 'level': 3, 'parent': 'Component3_Language_Chords'},
    {'code': 'Component3_Language_Chords_Traditional', 'title': 'Traditional and contemporary notation (e.g., IV or G7)', 'level': 3, 'parent': 'Component3_Language_Chords'},
    
    # Level 3: Vocabulary details
    {'code': 'Component3_Language_Vocabulary_Examples', 'title': 'Examples: slide, repeats, stepwise', 'level': 3, 'parent': 'Component3_Language_Vocabulary'},
    
    # Level 3: Scores details
    {'code': 'Component3_Language_Scores_Examples', 'title': 'Examples: continuo', 'level': 3, 'parent': 'Component3_Language_Scores'},
    
    # ===== AREAS OF STUDY =====
    # Level 2: Areas of Study (4 main areas)
    {'code': 'Component3_AreasOfStudy_Instrumental', 'title': 'Instrumental Music 1700–1820', 'level': 2, 'parent': 'Component3_AreasOfStudy'},
    {'code': 'Component3_AreasOfStudy_Vocal', 'title': 'Vocal Music', 'level': 2, 'parent': 'Component3_AreasOfStudy'},
    {'code': 'Component3_AreasOfStudy_StageScreen', 'title': 'Music for Stage and Screen', 'level': 2, 'parent': 'Component3_AreasOfStudy'},
    {'code': 'Component3_AreasOfStudy_Fusions', 'title': 'Fusions', 'level': 2, 'parent': 'Component3_AreasOfStudy'},
    
    # Level 3: Set Works - Instrumental Music
    {'code': 'Component3_AreasOfStudy_Instrumental_Bach', 'title': 'J.S. Bach: 3rd Movement from Brandenburg Concerto no. 5 in D major', 'level': 3, 'parent': 'Component3_AreasOfStudy_Instrumental'},
    {'code': 'Component3_AreasOfStudy_Instrumental_Beethoven', 'title': "L. van Beethoven: 1st Movement from Piano Sonata no. 8 in C minor 'Pathétique'", 'level': 3, 'parent': 'Component3_AreasOfStudy_Instrumental'},
    
    # Level 4: Bach details
    {'code': 'Component3_AreasOfStudy_Instrumental_Bach_Fugue', 'title': 'Study of fugue in a Gigue dance movement', 'level': 4, 'parent': 'Component3_AreasOfStudy_Instrumental_Bach'},
    {'code': 'Component3_AreasOfStudy_Instrumental_Bach_Baroque', 'title': 'General features of Baroque music', 'level': 4, 'parent': 'Component3_AreasOfStudy_Instrumental_Bach'},
    
    # Level 4: Beethoven details
    {'code': 'Component3_AreasOfStudy_Instrumental_Beethoven_Dramatic', 'title': 'Dramatic Romantic work', 'level': 4, 'parent': 'Component3_AreasOfStudy_Instrumental_Beethoven'},
    {'code': 'Component3_AreasOfStudy_Instrumental_Beethoven_Sonata', 'title': 'Sonata form', 'level': 4, 'parent': 'Component3_AreasOfStudy_Instrumental_Beethoven'},
    
    # Level 4: Instrumental Suggested Wider Listening
    {'code': 'Component3_AreasOfStudy_Instrumental_WL_Handel', 'title': 'G.F. Handel: Concerto Grosso op 6 no. 5, second movement', 'level': 4, 'parent': 'Component3_AreasOfStudy_Instrumental'},
    {'code': 'Component3_AreasOfStudy_Instrumental_WL_Vivaldi', 'title': "A. Vivaldi: 'Winter' from the Four Seasons concerti", 'level': 4, 'parent': 'Component3_AreasOfStudy_Instrumental'},
    {'code': 'Component3_AreasOfStudy_Instrumental_WL_Mozart', 'title': 'W.A. Mozart: Piano Sonata in C major K.545, first movement', 'level': 4, 'parent': 'Component3_AreasOfStudy_Instrumental'},
    {'code': 'Component3_AreasOfStudy_Instrumental_WL_Haydn', 'title': "F.J. Haydn: Piano Sonata in C major 'English Sonata' Hob 50, third movement", 'level': 4, 'parent': 'Component3_AreasOfStudy_Instrumental'},
    
    # Level 3: Set Works - Vocal Music
    {'code': 'Component3_AreasOfStudy_Vocal_Purcell', 'title': 'H. Purcell: Music for a While', 'level': 3, 'parent': 'Component3_AreasOfStudy_Vocal'},
    {'code': 'Component3_AreasOfStudy_Vocal_Queen', 'title': "Queen: Killer Queen (from the album 'Sheer Heart Attack')", 'level': 3, 'parent': 'Component3_AreasOfStudy_Vocal'},
    
    # Level 4: Purcell details
    {'code': 'Component3_AreasOfStudy_Vocal_Purcell_Baroque', 'title': 'Baroque setting for solo voice with accompaniment', 'level': 4, 'parent': 'Component3_AreasOfStudy_Vocal_Purcell'},
    
    # Level 4: Queen details
    {'code': 'Component3_AreasOfStudy_Vocal_Queen_20thCentury', 'title': 'Twentieth-century song for solo voice with accompaniment', 'level': 4, 'parent': 'Component3_AreasOfStudy_Vocal_Queen'},
    
    # Level 4: Vocal Suggested Wider Listening
    {'code': 'Component3_AreasOfStudy_Vocal_WL_Handel1', 'title': "G.F. Handel: 'The Trumpet Shall Sound' (bass) from Messiah", 'level': 4, 'parent': 'Component3_AreasOfStudy_Vocal'},
    {'code': 'Component3_AreasOfStudy_Vocal_WL_Handel2', 'title': "G.F. Handel: 'Rejoice Greatly' (soprano) from Messiah", 'level': 4, 'parent': 'Component3_AreasOfStudy_Vocal'},
    {'code': 'Component3_AreasOfStudy_Vocal_WL_Handel3', 'title': "G.F. Handel: 'Every Valley' (tenor) from Messiah", 'level': 4, 'parent': 'Component3_AreasOfStudy_Vocal'},
    {'code': 'Component3_AreasOfStudy_Vocal_WL_Bach1', 'title': "J.S. Bach: 'Weichet nur, betrubte Schatten' from wedding Cantata", 'level': 4, 'parent': 'Component3_AreasOfStudy_Vocal'},
    {'code': 'Component3_AreasOfStudy_Vocal_WL_Bach2', 'title': "J.S. Bach: 'Sehet in Zufriedenheit' from wedding Cantata", 'level': 4, 'parent': 'Component3_AreasOfStudy_Vocal'},
    {'code': 'Component3_AreasOfStudy_Vocal_WL_BeachBoys', 'title': "Beach Boys: 'God Only Knows' from Pet Sounds", 'level': 4, 'parent': 'Component3_AreasOfStudy_Vocal'},
    {'code': 'Component3_AreasOfStudy_Vocal_WL_Keys1', 'title': "Alicia Keys: 'If I Ain't Got You' from The Diary of Alicia Keys", 'level': 4, 'parent': 'Component3_AreasOfStudy_Vocal'},
    {'code': 'Component3_AreasOfStudy_Vocal_WL_Keys2', 'title': "Alicia Keys: 'Dragon Days' from The Diary of Alicia Keys", 'level': 4, 'parent': 'Component3_AreasOfStudy_Vocal'},
    
    # Level 3: Set Works - Stage and Screen
    {'code': 'Component3_AreasOfStudy_StageScreen_Schwartz', 'title': 'S. Schwartz: Defying Gravity (from the album of the cast recording of Wicked)', 'level': 3, 'parent': 'Component3_AreasOfStudy_StageScreen'},
    {'code': 'Component3_AreasOfStudy_StageScreen_Williams', 'title': 'J. Williams: Main title/rebel blockade runner (from the soundtrack to Star Wars Episode IV: A New Hope)', 'level': 3, 'parent': 'Component3_AreasOfStudy_StageScreen'},
    
    # Level 4: Schwartz details
    {'code': 'Component3_AreasOfStudy_StageScreen_Schwartz_Musical', 'title': 'Popular piece of West End musical theatre', 'level': 4, 'parent': 'Component3_AreasOfStudy_StageScreen_Schwartz'},
    
    # Level 4: Williams details
    {'code': 'Component3_AreasOfStudy_StageScreen_Williams_Film', 'title': 'Film music composed as sound to picture', 'level': 4, 'parent': 'Component3_AreasOfStudy_StageScreen_Williams'},
    
    # Level 4: Stage and Screen Suggested Wider Listening
    {'code': 'Component3_AreasOfStudy_StageScreen_WL_Minchin', 'title': "Tim Minchin: 'Naughty' from Matilda", 'level': 4, 'parent': 'Component3_AreasOfStudy_StageScreen'},
    {'code': 'Component3_AreasOfStudy_StageScreen_WL_Shaiman', 'title': "Marc Shaiman: 'Mama, I'm a Big Girl Now' from Hairspray", 'level': 4, 'parent': 'Component3_AreasOfStudy_StageScreen'},
    {'code': 'Component3_AreasOfStudy_StageScreen_WL_Lurie1', 'title': "Deborah Lurie: 'The Pier' from Dear John", 'level': 4, 'parent': 'Component3_AreasOfStudy_StageScreen'},
    {'code': 'Component3_AreasOfStudy_StageScreen_WL_Lurie2', 'title': "Deborah Lurie: 'Walk on the Beach' from Dear John", 'level': 4, 'parent': 'Component3_AreasOfStudy_StageScreen'},
    {'code': 'Component3_AreasOfStudy_StageScreen_WL_Lurie3', 'title': "Deborah Lurie: 'Dear John Letter' from Dear John", 'level': 4, 'parent': 'Component3_AreasOfStudy_StageScreen'},
    {'code': 'Component3_AreasOfStudy_StageScreen_WL_Shore1', 'title': "Howard Shore: 'The Prophecy' from The Lord of the Rings: The Fellowship of the Ring", 'level': 4, 'parent': 'Component3_AreasOfStudy_StageScreen'},
    {'code': 'Component3_AreasOfStudy_StageScreen_WL_Shore2', 'title': "Howard Shore: 'Concerning Hobbits' from The Lord of the Rings: The Fellowship of the Ring", 'level': 4, 'parent': 'Component3_AreasOfStudy_StageScreen'},
    {'code': 'Component3_AreasOfStudy_StageScreen_WL_Shore3', 'title': "Howard Shore: 'The Bridge of Khazad-dum' from The Lord of the Rings: The Fellowship of the Ring", 'level': 4, 'parent': 'Component3_AreasOfStudy_StageScreen'},
    {'code': 'Component3_AreasOfStudy_StageScreen_WL_Shore4', 'title': "Howard Shore: 'The Breaking of the Fellowship' from The Lord of the Rings: The Fellowship of the Ring", 'level': 4, 'parent': 'Component3_AreasOfStudy_StageScreen'},
    
    # Level 3: Set Works - Fusions
    {'code': 'Component3_AreasOfStudy_Fusions_AfroCelt', 'title': 'Afro Celt Sound System: Release (from the album Volume 2: Release)', 'level': 3, 'parent': 'Component3_AreasOfStudy_Fusions'},
    {'code': 'Component3_AreasOfStudy_Fusions_Spalding', 'title': 'Esperanza Spalding: Samba Em Preludio (from the album Esperanza)', 'level': 3, 'parent': 'Component3_AreasOfStudy_Fusions'},
    
    # Level 4: Afro Celt details
    {'code': 'Component3_AreasOfStudy_Fusions_AfroCelt_Elements', 'title': 'Combines African and Celtic musical elements', 'level': 4, 'parent': 'Component3_AreasOfStudy_Fusions_AfroCelt'},
    
    # Level 4: Spalding details
    {'code': 'Component3_AreasOfStudy_Fusions_Spalding_Styles', 'title': 'Combines Afro-Cuban Jazz and Latin American styles', 'level': 4, 'parent': 'Component3_AreasOfStudy_Fusions_Spalding'},
    
    # Level 4: Fusions Suggested Wider Listening
    {'code': 'Component3_AreasOfStudy_Fusions_WL_Capercaillie', 'title': 'Capercaillie: Beautiful Wasteland', 'level': 4, 'parent': 'Component3_AreasOfStudy_Fusions'},
    {'code': 'Component3_AreasOfStudy_Fusions_WL_Akalin1', 'title': "Demet Akalin: 'Pirlanta' from Pirlanta", 'level': 4, 'parent': 'Component3_AreasOfStudy_Fusions'},
    {'code': 'Component3_AreasOfStudy_Fusions_WL_Akalin2', 'title': "Demet Akalin: 'Ders Olsun' from Pirlanta", 'level': 4, 'parent': 'Component3_AreasOfStudy_Fusions'},
    {'code': 'Component3_AreasOfStudy_Fusions_WL_BuenaVista', 'title': 'Buena Vista Social Club: Buena Vista Social Club', 'level': 4, 'parent': 'Component3_AreasOfStudy_Fusions'},
    {'code': 'Component3_AreasOfStudy_Fusions_WL_Gillespie', 'title': 'Dizzy Gillespie y Machito: Afro-Cuban Jazz Moods', 'level': 4, 'parent': 'Component3_AreasOfStudy_Fusions'},
]


def upload_topics():
    """Upload Music topics to Supabase."""
    print(f"\n[INFO] Uploading {len(TOPICS)} topics for Music...")
    
    try:
        # Create/update subject
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT['name']} ({SUBJECT['qualification']})",
            'subject_code': SUBJECT['code'],
            'qualification_type': SUBJECT['qualification'],
            'specification_url': SUBJECT['pdf_url'],
            'exam_board': SUBJECT['exam_board']
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
            'exam_board': SUBJECT['exam_board']
        } for t in TOPICS]
        
        inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted.data)} topics")
        
        # Link parent relationships
        code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
        linked = 0
        for topic in TOPICS:
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
        levels = defaultdict(int)
        for t in TOPICS:
            levels[t['level']] += 1
        
        print("\n" + "=" * 80)
        print(f"[SUCCESS] {SUBJECT['name'].upper()} - UPLOAD COMPLETE!")
        print("=" * 80)
        for level in sorted(levels.keys()):
            count = levels[level]
            level_names = {
                0: 'Components',
                1: 'Main Categories',
                2: 'Subtopics',
                3: 'Details / Set Works',
                4: 'Set Work Details / Wider Listening'
            }
            print(f"   Level {level} ({level_names.get(level, f'Level {level}')}): {count}")
        print(f"\n   Total: {len(TOPICS)} topics")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 80)
    print("GCSE MUSIC - STRUCTURE UPLOADER")
    print("=" * 80)
    
    success = upload_topics()
    
    if success:
        print("\n✅ COMPLETE!")
        print("\nFull Music GCSE structure uploaded with extended hierarchy:")
        print("  - Level 0: Component 3 - Appraising")
        print("  - Level 1: 4 main categories")
        print("  - Level 2: Categories and subtopics")
        print("  - Level 3: Detailed elements + 8 set works")
        print("  - Level 4: Set work details + Suggested Wider Listening pieces")
    else:
        print("\n❌ FAILED")


if __name__ == '__main__':
    main()

