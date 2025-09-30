from bs4 import BeautifulSoup
import re

soup = BeautifulSoup(open('data/ocr_history_spec_glance.html', encoding='utf-8').read(), 'lxml')

# Find Unit group 1
h4s = soup.find_all('h4', string=re.compile(r'Unit group 1', re.I))
print(f"Found {len(h4s)} h4 tags with 'Unit group 1'")

for i, h4 in enumerate(h4s):
    print(f"\n=== h4 #{i+1}: {h4.get_text().strip()} ===")
    
    # Check next siblings
    print("Next 5 siblings:")
    current = h4
    for j in range(5):
        current = current.find_next_sibling()
        if current:
            print(f"  {j+1}. {current.name}: {current.get_text().strip()[:80]}")
            
            if current.name == 'ul':
                lis = current.find_all('li', recursive=False)
                print(f"     -> Found {len(lis)} topics in this ul!")
                for li in lis[:3]:
                    print(f"        - {li.get_text().strip()}")
                break
