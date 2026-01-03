"""Quick script to check which subjects are loaded."""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from eduqas_alevel_universal_scraper import EduqasALevelUniversalScraper

scraper = EduqasALevelUniversalScraper()
subjects = scraper.load_alevel_subjects()

print(f"\nTotal subjects loaded: {len(subjects)}\n")
print("Subjects:")
for i, s in enumerate(subjects, 1):
    print(f"{i:2d}. {s['name']:30s} - PDF URL: {'Yes' if s.get('pdf_url') else 'No'}")

# Expected subjects from the file
expected = [
    "Art and Design", "Biology", "Business", "Chemistry", "Computer Science",
    "Design and Technology", "Drama", "Economics", "Electronics", "English Language",
    "English Language and Literature", "English Literature", "Film Studies", "French",
    "Geography", "Geology", "German", "Law", "Media Studies", "Music",
    "Physical Education", "Physics", "Psychology", "Religious Studies", "Sociology", "Spanish"
]

print(f"\n\nExpected: {len(expected)} subjects")
print("Missing subjects:")
loaded_names = {s['name'] for s in subjects}
for exp in expected:
    if exp not in loaded_names:
        print(f"  - {exp}")

print("\nExtra subjects (loaded but not expected):")
for s in subjects:
    if s['name'] not in expected:
        print(f"  - {s['name']}")





















