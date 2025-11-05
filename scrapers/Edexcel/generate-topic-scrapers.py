"""
Generate individual topic scraper files for each subject
Based on working Biology A template
"""

import json
from pathlib import Path

# Load subjects
config_path = Path(__file__).parent / 'edexcel-alevel-subjects-complete.json'
with open(config_path) as f:
    subjects = json.load(f)

# Load Biology template
template_path = Path(__file__).parent / 'A-Level' / 'topics' / 'scrape-biology-a-python.py'
template = template_path.read_text(encoding='utf-8')

output_dir = Path(__file__).parent / 'A-Level' / 'topics'

print("Generating topic scrapers...")

for subject in subjects:
    if subject['status'] == 'complete':
        print(f"  Skip {subject['name']} (already complete)")
        continue
    
    # Replace Biology config with this subject's config
    modified = template.replace(
        "'name': 'Biology A (Salters-Nuffield)',",
        f"'name': '{subject['name']}',"
    )
    modified = modified.replace(
        "'code': '9BN0',",
        f"'code': '{subject['code']}',"
    )
    
    # Replace PDF URL (find the Biology URL and replace it)
    bio_url = "https://qualifications.pearson.com/content/dam/pdf/A%20Level/biology-a/2015/specification-and-sample-assessment-materials/9781446930885-gce2015-a-bioa-spec.pdf"
    modified = modified.replace(bio_url, subject['pdf_url'])
    
    # Write individual scraper file
    output_file = output_dir / f"scrape-{subject['code'].lower()}.py"
    output_file.write_text(modified, encoding='utf-8')
    
    print(f"  Created: scrape-{subject['code'].lower()}.py for {subject['name']}")

print(f"\nDone! Created {len([s for s in subjects if s['status'] != 'complete'])} topic scrapers")
print("\nTo run all:")
print("  cd A-Level/topics")
print("  python scrape-9ch0.py    # Chemistry")
print("  python scrape-9ph0.py    # Physics")
print("  etc.")

