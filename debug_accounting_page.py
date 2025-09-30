"""Quick debug to see what's on the Accounting subject-content page"""

import requests
from bs4 import BeautifulSoup
import re

url = "https://www.aqa.org.uk/subjects/accounting/a-level/accounting-7127/specification/subject-content"

print(f"Fetching: {url}\n")

response = requests.get(url)
soup = BeautifulSoup(response.content, 'lxml')

# Find all links
all_links = soup.find_all('a', href=True)

print(f"Total links found: {len(all_links)}\n")

# Filter for subject-content links
content_links = [link for link in all_links if 'subject-content' in link.get('href', '')]

print(f"Subject-content links: {len(content_links)}\n")

# Show first 20
for i, link in enumerate(content_links[:20], 1):
    text = link.get_text().strip()
    href = link.get('href')
    print(f"{i}. Text: '{text}'")
    print(f"   Href: {href}\n")

# Also check for bullet points with numbers
print("\n" + "="*60)
print("Looking for numbered patterns in text...")
print("="*60 + "\n")

# Find all text that matches 3.X pattern
all_text = soup.get_text()
numbered_items = re.findall(r'(3\.\d+)\s+([^\n]{10,100})', all_text)

for code, title in numbered_items[:20]:
    print(f"{code}: {title}")
