#!/usr/bin/env python
"""
AQA Database Proof of Concept
Test complete workflow: Scrape Law → Upload to AQA database → Verify
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

from database.uploaders.aqa_uploader import AQAUploader
from scrapers.uk.aqa_recursive_web_scraper import AQARecursiveWebScraper
from organize_topics_by_numbers import organize_topics_by_numbers


def main():
    print("=" * 80)
    print("AQA DATABASE PROOF OF CONCEPT - Law A-Level")
    print("=" * 80)
    print("\nThis will:")
    print("1. Scrape Law from AQA website (tables + hierarchy)")
    print("2. Organize topics into 3 levels")
    print("3. Upload to AQA-specific database tables")
    print("4. Verify data integrity")
    print("\n" + "=" * 80)
    
    input("Press Enter to continue...")
    
    # Initialize
    scraper = AQARecursiveWebScraper(headless=True)
    uploader = AQAUploader()
    
    try:
        # Step 1: Scrape Law
        print("\nStep 1: Scraping Law from AQA website...")
        print("-" * 80)
        
        result = scraper.scrape_subject_complete_deep(
            subject="Law",
            qualification="A-Level",
            subject_code="7162"
        )
        
        # Flatten all topics
        all_topics = []
        for item in result.get('content_items', []):
            # Add main section (Level 0)
            all_topics.append({
                'code': item.get('code'),
                'title': item.get('title'),
                'level': 0,
                'parent_code': None
            })
            
            # Add table rows
            all_topics.extend(item.get('table_rows', []))
        
        print(f"✓ Scraped {len(all_topics)} raw topics")
        
        # Step 2: Organize by numbers
        print("\nStep 2: Organizing topics into hierarchy...")
        print("-" * 80)
        
        organized_topics = organize_topics_by_numbers(all_topics)
        
        from collections import Counter
        by_level = Counter(t['level'] for t in organized_topics)
        
        print(f"✓ Organized into levels:")
        for level in sorted(by_level.keys()):
            print(f"  Level {level}: {by_level[level]} topics")
        
        # Step 3: Upload to AQA database
        print("\nStep 3: Uploading to AQA database...")
        print("-" * 80)
        
        subject_data = {
            'subject_name': 'Law',
            'subject_code': '7162',
            'qualification_type': 'A-Level',
            'specification_url': 'https://www.aqa.org.uk/subjects/law/a-level/law-7162/specification',
            'specification_pdf_url': 'https://cdn.sanity.io/files/p28bar15/green/543e9f2bd397a5e918290f9ae265a559285cbbca.pdf',
            'topics': organized_topics,
            'components': [
                {'code': 'P1', 'name': 'Paper 1', 'selection_type': 'required_all', 'weight': '33%'},
                {'code': 'P2', 'name': 'Paper 2', 'selection_type': 'required_all', 'weight': '33%'},
                {'code': 'P3', 'name': 'Paper 3', 'selection_type': 'choose_one', 'count_required': 1, 'total_available': 2, 'weight': '33%'}
            ],
            'constraints': [
                {
                    'type': 'general',
                    'description': 'Paper 3: Choose either Contract or Tort option',
                    'rule_details': {'options': ['Contract', 'Tort']}
                }
            ]
        }
        
        upload_result = uploader.upload_subject_complete(subject_data)
        
        print(f"✓ Uploaded to AQA database:")
        print(f"  Subject ID: {upload_result['subject_id']}")
        print(f"  Topics: {upload_result['topics_uploaded']}")
        print(f"  Components: {upload_result['components_uploaded']}")
        print(f"  Constraints: {upload_result['constraints_uploaded']}")
        
        # Step 4: Verify
        print("\nStep 4: Verifying data in Supabase...")
        print("-" * 80)
        
        # Check hierarchy
        topics_with_parents = uploader.client.table('aqa_topics').select('id', count='exact').eq(
            'subject_id', upload_result['subject_id']
        ).not_.is_('parent_topic_id', 'null').execute().count
        
        total_topics = uploader.client.table('aqa_topics').select('id', count='exact').eq(
            'subject_id', upload_result['subject_id']
        ).execute().count
        
        print(f"✓ Verification:")
        print(f"  Total topics in aqa_topics: {total_topics}")
        print(f"  Topics with parents: {topics_with_parents}")
        print(f"  Hierarchy: {'✓ Working!' if topics_with_parents > 0 else '✗ Issue'}")
        
        # Sample topics
        samples = uploader.client.table('aqa_topics').select(
            'topic_code, topic_name, topic_level, parent_topic_id'
        ).eq('subject_id', upload_result['subject_id']).order('topic_level').limit(10).execute().data
        
        print(f"\nSample topics:")
        for t in samples:
            indent = "  " * (t['topic_level'] + 1)
            parent_str = f"→ {t['parent_topic_id'][:8]}..." if t.get('parent_topic_id') else "✗ None"
            print(f"{indent}L{t['topic_level']}: {t['topic_code']} {t['topic_name'][:40]} {parent_str}")
        
        print("\n" + "=" * 80)
        print("PROOF OF CONCEPT COMPLETE!")
        print("=" * 80)
        print("\nAQA Database Tables Created and Populated:")
        print("✓ aqa_subjects: 1 subject (Law)")
        print(f"✓ aqa_topics: {total_topics} topics with hierarchy")
        print(f"✓ aqa_components: {upload_result['components_uploaded']} components")
        print(f"✓ aqa_constraints: {upload_result['constraints_uploaded']} constraints")
        
        print("\nNext Steps:")
        print("1. Check Supabase to verify data quality")
        print("2. If happy, document this approach")
        print("3. Return to FLASH app development")
        print("4. Come back to build OCR/Edexcel databases when ready")
        
        print("\nSQL to check:")
        print(f"SELECT * FROM aqa_subject_stats WHERE subject_name = 'Law';")
        print(f"SELECT * FROM get_aqa_topic_hierarchy('7162');")
        
        return 0
        
    finally:
        scraper.close()


if __name__ == '__main__':
    sys.exit(main())

















