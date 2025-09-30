#!/usr/bin/env python
"""Save OCR History page HTML to inspect structure."""

import requests

url = "https://www.ocr.org.uk/qualifications/as-and-a-level/history-a-h105-h505-from-2015/specification-at-a-glance/"

response = requests.get(url)
html = response.text

with open("data/ocr_history_spec_glance.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Saved HTML to: data/ocr_history_spec_glance.html")
print(f"HTML length: {len(html)} characters")
print(f"\nSearching for 'Unit group'...")
print(f"Found: {html.count('Unit group')} occurrences")
print(f"\nSearching for bullet points (li tags)...")  
print(f"Found: {html.count('<li>')} li tags")




