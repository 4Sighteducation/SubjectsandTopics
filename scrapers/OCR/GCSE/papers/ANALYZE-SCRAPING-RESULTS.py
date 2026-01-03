"""
Analyze OCR GCSE scraping results to find subjects with no papers.
"""

import os
from pathlib import Path
from bs4 import BeautifulSoup
import json

debug_dir = Path(__file__).parent / "debug-output"

# Subject mapping from batch script
subjects = {
    "J051": "Ancient History",
    "J170": "Art and Design",
    "J247": "Biology A",
    "J257": "Biology B",
    "J204": "Business",
    "J248": "Chemistry A",
    "J258": "Chemistry B",
    "J270": "Citizenship Studies",
    "J199": "Classical Civilisation",
    "J250": "Combined Science A",
    "J260": "Combined Science B",
    "J277": "Computer Science",
    "J814": "Dance",
    "J310": "Design and Technology",
    "J316": "Drama",
    "J205": "Economics",
    "J351": "English Language",
    "J352": "English Literature",
    "J309": "Food Preparation and Nutrition",
    "J730": "French",
    "J382": "Geography A",
    "J384": "Geography B",
    "J731": "German",
    "J410": "History A",
    "J411": "History B",
    "J282": "Latin",
    "J560": "Mathematics",
    "J200": "Media Studies",
    "J536": "Music",
    "J587": "Physical Education",
    "J249": "Physics A",
    "J259": "Physics B",
    "J625": "Religious Studies",
    "J203": "Sociology",
    "J732": "Spanish"
}

results = {}
no_papers = []
has_papers = []

print("=" * 80)
print("ANALYZING OCR GCSE SCRAPING RESULTS")
print("=" * 80)
print()

for code, name in subjects.items():
    html_file = debug_dir / f"ocr-gcse-{code}-after-filters.html"
    
    if not html_file.exists():
        results[code] = {
            "name": name,
            "status": "NO_DEBUG_FILE",
            "papers_found": 0,
            "resource_lists": 0,
            "pdf_links": 0
        }
        no_papers.append((code, name, "No debug file"))
        continue
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check for finder-results div
        finder_results = soup.find('div', class_='finder-results')
        
        # Count resource lists
        resource_lists = soup.find_all('ul', class_='resource-list')
        
        # Count PDF links
        pdf_links = soup.find_all('a', href=lambda x: x and x.endswith('.pdf'))
        
        # Check for "no documents" message
        no_doc_message = soup.find(string=lambda x: x and 'no past paper materials' in x.lower())
        
        # Check for loading indicator still present
        loading = soup.find('span', class_='loading-documents')
        
        # Check if qualification was selected
        qual_select = soup.find('select', id='pp-qual')
        qual_selected = False
        if qual_select:
            selected_option = qual_select.find('option', selected=True)
            if selected_option and selected_option.get('value') != '0':
                qual_selected = True
        
        papers_found = len(resource_lists)
        
        status = "HAS_PAPERS" if papers_found > 0 else "NO_PAPERS"
        
        if papers_found == 0:
            reason = []
            if not qual_selected:
                reason.append("Qualification not selected")
            if loading:
                reason.append("Still loading")
            if no_doc_message:
                reason.append("No papers message found")
            if not finder_results:
                reason.append("No finder-results div")
            if len(pdf_links) == 0:
                reason.append("No PDF links found")
            
            reason_str = "; ".join(reason) if reason else "Unknown"
            no_papers.append((code, name, reason_str))
        else:
            has_papers.append((code, name, papers_found))
        
        results[code] = {
            "name": name,
            "status": status,
            "papers_found": papers_found,
            "resource_lists": len(resource_lists),
            "pdf_links": len(pdf_links),
            "qualification_selected": qual_selected,
            "has_loading": loading is not None,
            "has_no_doc_message": no_doc_message is not None,
            "has_finder_results": finder_results is not None
        }
        
    except Exception as e:
        results[code] = {
            "name": name,
            "status": "ERROR",
            "error": str(e),
            "papers_found": 0
        }
        no_papers.append((code, name, f"Error: {e}"))

print("SUBJECTS WITH NO PAPERS (12 expected):")
print("-" * 80)
for code, name, reason in no_papers:
    print(f"  {code:6} - {name:30} | Reason: {reason}")

print()
print("SUBJECTS WITH PAPERS:")
print("-" * 80)
for code, name, count in has_papers:
    print(f"  {code:6} - {name:30} | {count} resource lists")

print()
print("=" * 80)
print(f"SUMMARY:")
print(f"  Total subjects: {len(subjects)}")
print(f"  Subjects with papers: {len(has_papers)}")
print(f"  Subjects with no papers: {len(no_papers)}")
print("=" * 80)

# Save detailed results to JSON
output_file = debug_dir / "scraping-analysis-results.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n💾 Detailed results saved to: {output_file}")





















