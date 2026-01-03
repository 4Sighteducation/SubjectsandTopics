"""
OCR A-Level Latin Manual Structure Builder
===========================================

Manually builds the Latin H443 subject structure with:
- Prose Literature (Groups 1 & 2)
- Verse Literature (Groups 3 & 4)
- Accidence and Syntax

Requirements:
    pip install python-dotenv supabase

Usage:
    python ocr-latin-manual.py
"""

import os
import sys
from pathlib import Path
from typing import List, Dict
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

PDF_URL = 'https://www.ocr.org.uk/Images/260757-specification-accredited-a-level-gce-latin-h443.pdf'


# ================================================================
# MANUAL TOPIC STRUCTURE
# ================================================================

TOPICS = [
    # PROSE LITERATURE
    {'code': 'H443_1', 'title': 'Prose Literature', 'level': 0, 'parent': None},
    
    # Group 1
    {'code': 'H443_1_1', 'title': 'Group 1', 'level': 1, 'parent': 'H443_1'},
    {'code': 'H443_1_1_1', 'title': 'Cicero, Pro Cluentio (2023-2024)', 'level': 2, 'parent': 'H443_1_1'},
    {'code': 'H443_1_1_2', 'title': 'Cicero, Pro Caelio (2025-2026)', 'level': 2, 'parent': 'H443_1_1'},
    {'code': 'H443_1_1_3', 'title': 'Cicero, pro Roscio Amerino (2027-2028)', 'level': 2, 'parent': 'H443_1_1'},
    
    # Group 2
    {'code': 'H443_1_2', 'title': 'Group 2', 'level': 1, 'parent': 'H443_1'},
    {'code': 'H443_1_2_1', 'title': 'Tacitus, Annals IV (2023-2024)', 'level': 2, 'parent': 'H443_1_2'},
    {'code': 'H443_1_2_2', 'title': 'Livy, Book 1 (2023-2024)', 'level': 2, 'parent': 'H443_1_2'},
    {'code': 'H443_1_2_3', 'title': 'Tacitus, Annals XII & XIV (2025-2026)', 'level': 2, 'parent': 'H443_1_2'},
    {'code': 'H443_1_2_4', 'title': 'Pliny, Letters (2025-2026)', 'level': 2, 'parent': 'H443_1_2'},
    {'code': 'H443_1_2_5', 'title': 'Nepos, Life of Hannibal (2027-2028)', 'level': 2, 'parent': 'H443_1_2'},
    {'code': 'H443_1_2_6', 'title': 'Tacitus, Annals XIV (2027-2028)', 'level': 2, 'parent': 'H443_1_2'},
    {'code': 'H443_1_2_7', 'title': 'Apuleius, Metamorphoses Book VI (2027-2028)', 'level': 2, 'parent': 'H443_1_2'},
    
    # VERSE LITERATURE
    {'code': 'H443_2', 'title': 'Verse Literature', 'level': 0, 'parent': None},
    
    # Group 3
    {'code': 'H443_2_1', 'title': 'Group 3', 'level': 1, 'parent': 'H443_2'},
    {'code': 'H443_2_1_1', 'title': 'Virgil, Aeneid Book XII (2023-2024)', 'level': 2, 'parent': 'H443_2_1'},
    {'code': 'H443_2_1_2', 'title': 'Catullus, poems (2023-2024)', 'level': 2, 'parent': 'H443_2_1'},
    {'code': 'H443_2_1_3', 'title': 'Ovid, Heroides I & VII (2023-2024)', 'level': 2, 'parent': 'H443_2_1'},
    {'code': 'H443_2_1_4', 'title': 'Virgil, Aeneid Book 2 (2025-2026)', 'level': 2, 'parent': 'H443_2_1'},
    {'code': 'H443_2_1_5', 'title': 'Juvenal, Satire 6 (2025-2026)', 'level': 2, 'parent': 'H443_2_1'},
    {'code': 'H443_2_1_6', 'title': 'Ovid, Fasti Book 2 (2025-2026)', 'level': 2, 'parent': 'H443_2_1'},
    {'code': 'H443_2_1_7', 'title': 'Virgil, Aeneid Book 4 (2027-2028)', 'level': 2, 'parent': 'H443_2_1'},
    {'code': 'H443_2_1_8', 'title': 'Tibullus 1.2, 1.5, 2.4 (2027-2028)', 'level': 2, 'parent': 'H443_2_1'},
    {'code': 'H443_2_1_9', 'title': 'Ovid, Metamorphoses Book 7 (2027-2028)', 'level': 2, 'parent': 'H443_2_1'},
    
    # Group 4
    {'code': 'H443_2_2', 'title': 'Group 4', 'level': 1, 'parent': 'H443_2'},
    {'code': 'H443_2_2_1', 'title': 'Virgil, Aeneid Book XII (2023-2024)', 'level': 2, 'parent': 'H443_2_2'},
    {'code': 'H443_2_2_2', 'title': 'Catullus, poems (2023-2024)', 'level': 2, 'parent': 'H443_2_2'},
    {'code': 'H443_2_2_3', 'title': 'Virgil, Aeneid Book 2 (2025-2026)', 'level': 2, 'parent': 'H443_2_2'},
    {'code': 'H443_2_2_4', 'title': 'Juvenal, Satires 14 & 15 (2025-2026)', 'level': 2, 'parent': 'H443_2_2'},
    {'code': 'H443_2_2_5', 'title': 'Virgil, Aeneid Book 4 (2027-2028)', 'level': 2, 'parent': 'H443_2_2'},
    {'code': 'H443_2_2_6', 'title': 'Lucretius, De Rerum Natura Book 1 (2027-2028)', 'level': 2, 'parent': 'H443_2_2'},
    
    # ACCIDENCE AND SYNTAX
    {'code': 'H443_3', 'title': 'Accidence and Syntax', 'level': 0, 'parent': None},
    
    # Accidence
    {'code': 'H443_3_1', 'title': 'Accidence', 'level': 1, 'parent': 'H443_3'},
    {'code': 'H443_3_1_1', 'title': 'Nouns of all standard types', 'level': 2, 'parent': 'H443_3_1'},
    {'code': 'H443_3_1_2', 'title': 'Adjectives from all three declensions', 'level': 2, 'parent': 'H443_3_1'},
    {'code': 'H443_3_1_3', 'title': 'Adverbs', 'level': 2, 'parent': 'H443_3_1'},
    {'code': 'H443_3_1_4', 'title': 'Comparison of adjectives and adverbs', 'level': 2, 'parent': 'H443_3_1'},
    {'code': 'H443_3_1_5', 'title': 'Pronouns and pronominal adjectives', 'level': 2, 'parent': 'H443_3_1'},
    {'code': 'H443_3_1_6', 'title': 'Verbs of all standard types from all conjugations', 'level': 2, 'parent': 'H443_3_1'},
    {'code': 'H443_3_1_7', 'title': 'Compound verbs of regular formation', 'level': 2, 'parent': 'H443_3_1'},
    {'code': 'H443_3_1_8', 'title': 'Cardinal numbers 1-1000 and ordinal numbers 1st-10th', 'level': 2, 'parent': 'H443_3_1'},
    {'code': 'H443_3_1_9', 'title': 'Uses of prepositions', 'level': 2, 'parent': 'H443_3_1'},
    
    # Syntax
    {'code': 'H443_3_2', 'title': 'Syntax', 'level': 1, 'parent': 'H443_3'},
    {'code': 'H443_3_2_1', 'title': 'Standard patterns of case usage', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_2', 'title': 'Negation', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_3', 'title': 'Direct statement, question and command', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_4', 'title': 'Prohibitions, exhortations and wishes', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_5', 'title': 'Uses of the infinitive', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_6', 'title': 'Uses of the participle (including ablative absolute)', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_7', 'title': 'Uses of the subjunctive', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_8', 'title': 'Comparison (including ablative of comparison)', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_9', 'title': 'Uses of the gerund and gerundive', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_10', 'title': 'Constructions using quominus and quin', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_11', 'title': 'Use of dum and dummodo to mean "provided that"', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_12', 'title': 'Subordinate clauses', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_13', 'title': 'Indirect statement, question, command and prohibition', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_14', 'title': 'Description (relative clauses)', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_15', 'title': 'Purpose clauses', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_16', 'title': 'Result clauses', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_17', 'title': 'Conditional clauses', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_18', 'title': 'Causal clauses', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_19', 'title': 'Temporal clauses', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_20', 'title': 'Subordinate clauses within indirect speech', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_21', 'title': 'Fearing, prevention and precaution', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_22', 'title': 'Concessive clauses', 'level': 2, 'parent': 'H443_3_2'},
    {'code': 'H443_3_2_23', 'title': 'Comparative clauses', 'level': 2, 'parent': 'H443_3_2'}
]


class LatinBuilder:
    """Manual builder for OCR A-Level Latin."""
    
    def build_and_upload(self):
        """Build and upload Latin structure."""
        print("\n" + "📖 "*40)
        print("OCR LATIN MANUAL BUILDER")
        print("📖 "*40)
        
        print(f"\n[INFO] Building Latin structure with {len(TOPICS)} topics...")
        
        # Count by level
        level_counts = {}
        for t in TOPICS:
            level_counts[t['level']] = level_counts.get(t['level'], 0) + 1
        level_str = ", ".join([f"L{k}:{v}" for k, v in sorted(level_counts.items())])
        print(f"[OK] Structure: {len(TOPICS)} topics ({level_str})")
        
        # Upload
        return self._upload_subject(TOPICS)
    
    def _upload_subject(self, topics: List[Dict]) -> bool:
        """Upload to Supabase."""
        
        try:
            # Upsert subject
            subject_result = supabase.table('staging_aqa_subjects').upsert({
                'subject_name': "Latin (A-Level)",
                'subject_code': 'H443',
                'qualification_type': 'A-Level',
                'specification_url': PDF_URL,
                'exam_board': 'OCR'
            }, on_conflict='subject_code,qualification_type,exam_board').execute()
            
            subject_id = subject_result.data[0]['id']
            print(f"[OK] Subject ID: {subject_id}")
            
            # Clear old topics
            supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
            
            # Insert topics
            to_insert = [{
                'subject_id': subject_id,
                'topic_code': t['code'],
                'topic_name': t['title'],
                'topic_level': t['level'],
                'exam_board': 'OCR'
            } for t in topics]
            
            inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
            print(f"[OK] Uploaded {len(inserted.data)} topics")
            
            # Link hierarchy
            code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
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
            print(f"[ERROR] Upload failed: {e}")
            return False


def main():
    builder = LatinBuilder()
    success = builder.build_and_upload()
    
    print("\n" + "="*80)
    if success:
        print("✅ Latin structure built successfully!")
    else:
        print("❌ Latin build failed")
    print("="*80)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

