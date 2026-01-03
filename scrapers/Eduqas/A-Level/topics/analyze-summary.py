"""Analyze the summary report to see which subjects were processed."""
import json
from pathlib import Path

summary_file = Path(__file__).parent / "reports" / "summary-20251123-205739.json"

with open(summary_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total subjects in report: {data['total_subjects']}")
print(f"Success: {data['success_count']}, Failed: {data['fail_count']}\n")

processed_subjects = [r['subject_name'] for r in data['reports']]
print("Processed subjects:")
for i, name in enumerate(sorted(processed_subjects), 1):
    report = next(r for r in data['reports'] if r['subject_name'] == name)
    status = "✓" if report['success'] else "✗"
    topics = report.get('topics_extracted', 0)
    print(f"{i:2d}. {status} {name:35s} - {topics:4d} topics")

# Expected from file
expected = [
    "Art and Design", "Biology", "Business", "Chemistry", "Computer Science",
    "Design and Technology", "Drama", "Economics", "Electronics", "English Language",
    "English Language and Literature", "English Literature", "Film Studies", "French",
    "Geography", "Geology", "German", "Law", "Media Studies", "Music",
    "Physical Education", "Physics", "Psychology", "Religious Studies", "Sociology", "Spanish"
]

print(f"\n\nExpected: {len(expected)} subjects")
print("Missing from processed list:")
for exp in expected:
    if exp not in processed_subjects:
        print(f"  - {exp}")

print("\nSubjects with 0 topics (won't upload to DB):")
for r in data['reports']:
    if r.get('topics_extracted', 0) == 0:
        print(f"  - {r['subject_name']} ({'failed' if not r['success'] else 'succeeded but 0 topics'})")

print("\nSubjects with topics > 0 (should be in DB):")
successful_with_topics = [r for r in data['reports'] if r.get('topics_extracted', 0) > 0]
print(f"Total: {len(successful_with_topics)}")
for r in successful_with_topics:
    print(f"  - {r['subject_name']}: {r.get('topics_extracted', 0)} topics")





















