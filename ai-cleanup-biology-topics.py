"""
AI Topic Name Cleanup Script
Summarizes verbose Biology topic names using OpenAI GPT-4

Example:
  Before: "Understand how the structures of blood vessels (capillaries, arteries and veins) relate to their functions."
  After:  "Blood vessel structures and functions"
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
import openai
import time

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

# Initialize
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
openai.api_key = os.getenv('OPENAI_API_KEY')  # Add this to your .env if not there


def summarize_topic_name(original_name, topic_code):
    """
    Use GPT-4 to summarize a verbose topic name.
    
    Args:
        original_name: The verbose topic name
        topic_code: The topic code (for context)
    
    Returns:
        Summarized name (5-15 words)
    """
    
    # Skip if already concise
    if len(original_name) < 50:
        return original_name
    
    prompt = f"""Summarize this biology curriculum topic into a concise name (5-15 words max).

Original: "{original_name}"

Rules:
- Keep key scientific terms (e.g., "cardiac cycle", "blood vessels")
- Remove verbs like "Understand", "Know", "Be able to"
- Remove explanatory details in parentheses
- Make it student-friendly

Return ONLY the summarized name, nothing else."""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=50
        )
        
        summary = response.choices[0].message.content.strip()
        
        # Remove quotes if GPT added them
        summary = summary.strip('"').strip("'")
        
        return summary
        
    except Exception as e:
        print(f"   ⚠️  Error summarizing: {e}")
        return original_name


def cleanup_biology_topics(subject_code='9BN0', dry_run=True):
    """
    Clean up Biology topic names.
    
    Args:
        subject_code: Subject code to clean
        dry_run: If True, shows changes but doesn't apply them
    """
    
    print("=" * 60)
    print("AI TOPIC CLEANUP - BIOLOGY A")
    print("=" * 60)
    print(f"\nSubject Code: {subject_code}")
    print(f"Mode: {'DRY RUN (preview only)' if dry_run else 'LIVE (will update database)'}")
    print("")
    
    # Get Biology subject
    subject = supabase.table('staging_aqa_subjects')\
        .select('id, subject_name')\
        .eq('subject_code', subject_code)\
        .eq('exam_board', 'Edexcel')\
        .execute()
    
    if not subject.data:
        print("❌ Subject not found!")
        return
    
    subject_id = subject.data[0]['id']
    subject_name = subject.data[0]['subject_name']
    
    print(f"✅ Found: {subject_name}\n")
    
    # Get all topics at Level 2 and 3 (these have verbose names)
    topics = supabase.table('staging_aqa_topics')\
        .select('id, topic_code, topic_name, topic_level')\
        .eq('subject_id', subject_id)\
        .in_('topic_level', [2, 3])\
        .order('topic_code')\
        .execute()
    
    print(f"📋 Processing {len(topics.data)} topics (Level 2 & 3 only)...\n")
    
    changes = []
    total_cost = 0
    
    for idx, topic in enumerate(topics.data):
        # Show progress
        if (idx + 1) % 10 == 0:
            print(f"   Progress: {idx + 1}/{len(topics.data)} topics processed...")
        
        original = topic['topic_name']
        
        # Summarize with GPT
        summarized = summarize_topic_name(original, topic['topic_code'])
        
        if summarized != original:
            changes.append({
                'id': topic['id'],
                'code': topic['topic_code'],
                'level': topic['topic_level'],
                'original': original,
                'summarized': summarized
            })
            
            # Rough cost estimate ($0.01 per topic)
            total_cost += 0.01
        
        # Rate limit (10 requests per second)
        time.sleep(0.15)
    
    # Show results
    print(f"\n✅ Processing complete!")
    print(f"\n📊 Results:")
    print(f"   Total topics: {len(topics.data)}")
    print(f"   Changes suggested: {len(changes)}")
    print(f"   Estimated cost: ${total_cost:.2f}")
    
    if len(changes) > 0:
        print(f"\n📝 Sample changes (first 10):")
        for change in changes[:10]:
            print(f"\n   {change['code']} (L{change['level']}):")
            print(f"   Before: {change['original'][:80]}...")
            print(f"   After:  {change['summarized']}")
    
    # Apply changes if not dry run
    if not dry_run and len(changes) > 0:
        print(f"\n💾 Applying {len(changes)} changes to database...")
        
        confirm = input("\n⚠️  Are you sure? Type 'YES' to confirm: ")
        
        if confirm == 'YES':
            for change in changes:
                supabase.table('staging_aqa_topics')\
                    .update({'topic_name': change['summarized']})\
                    .eq('id', change['id'])\
                    .execute()
            
            print(f"\n✅ Updated {len(changes)} topic names!")
        else:
            print("\n❌ Cancelled - no changes applied")
    elif len(changes) > 0:
        print(f"\n💡 To apply these changes, run:")
        print(f"   python ai-cleanup-biology-topics.py --live")
    
    return len(changes)


if __name__ == '__main__':
    # Check for --live flag
    dry_run = '--live' not in sys.argv
    
    cleanup_biology_topics(dry_run=dry_run)

