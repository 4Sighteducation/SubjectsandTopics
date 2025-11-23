"""
Extract exact qualification filter names from OCR GCSE dropdown.
"""

from pathlib import Path
from bs4 import BeautifulSoup

# Read any of the debug HTML files (they all have the same dropdown options)
html_file = Path(__file__).parent / "debug-output" / "ocr-gcse-J247-after-filters.html"

with open(html_file, 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find the qualification select dropdown
qual_select = soup.find('select', id='pp-qual')

if qual_select:
    print("=" * 80)
    print("OCR GCSE QUALIFICATION FILTER NAMES")
    print("=" * 80)
    print()
    
    options = qual_select.find_all('option')
    
    # Map subject codes to qualification names
    code_to_qual = {}
    
    for option in options:
        value = option.get('value')
        text = option.get_text(strip=True)
        
        if value and value != '0' and text:
            # Extract subject code from text (e.g., "J247" from "Gateway Science Suite - Biology A (9-1) - J247 (from 2016)")
            import re
            code_match = re.search(r'J\d{3}', text)
            if code_match:
                code = code_match.group(0)
                code_to_qual[code] = text
    
    # Print in order matching batch script
    subjects_order = [
        ("J051", "Ancient History"),
        ("J170", "Art and Design"),
        ("J247", "Biology A"),
        ("J257", "Biology B"),
        ("J204", "Business"),
        ("J248", "Chemistry A"),
        ("J258", "Chemistry B"),
        ("J270", "Citizenship Studies"),
        ("J199", "Classical Civilisation"),
        ("J250", "Combined Science A"),
        ("J260", "Combined Science B"),
        ("J277", "Computer Science"),
        ("J814", "Dance"),
        ("J310", "Design and Technology"),
        ("J316", "Drama"),
        ("J205", "Economics"),
        ("J351", "English Language"),
        ("J352", "English Literature"),
        ("J309", "Food Preparation and Nutrition"),
        ("J730", "French"),
        ("J382", "Geography A"),
        ("J384", "Geography B"),
        ("J731", "German"),
        ("J410", "History A"),
        ("J411", "History B"),
        ("J282", "Latin"),
        ("J560", "Mathematics"),
        ("J200", "Media Studies"),
        ("J536", "Music"),
        ("J587", "Physical Education"),
        ("J249", "Physics A"),
        ("J259", "Physics B"),
        ("J625", "Religious Studies"),
        ("J203", "Sociology"),
        ("J732", "Spanish")
    ]
    
    print("CORRECT QUALIFICATION FILTERS:")
    print("-" * 80)
    
    found = {}
    not_found = []
    
    for code, name in subjects_order:
        if code in code_to_qual:
            qual_name = code_to_qual[code]
            found[code] = qual_name
            print(f'{code:6} - {name:30} | "{qual_name}"')
        else:
            # Try to find by name
            matched = False
            for opt_code, opt_text in code_to_qual.items():
                if name.lower() in opt_text.lower():
                    found[code] = opt_text
                    print(f'{code:6} - {name:30} | "{opt_text}" (found as {opt_code})')
                    matched = True
                    break
            if not matched:
                not_found.append((code, name))
                print(f'{code:6} - {name:30} | NOT FOUND')
    
    print()
    print("=" * 80)
    print("ALL QUALIFICATIONS IN DROPDOWN:")
    print("-" * 80)
    for code, qual in sorted(code_to_qual.items()):
        print(f'{code:6} - {qual}')
    
    if not_found:
        print()
        print("=" * 80)
        print("SUBJECTS NOT FOUND IN DROPDOWN:")
        print("-" * 80)
        for code, name in not_found:
            print(f'{code:6} - {name}')

