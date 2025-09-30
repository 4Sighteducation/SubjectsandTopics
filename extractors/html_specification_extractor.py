"""
HTML Specification Extractor
Extracts metadata from HTML pages instead of PDFs - faster and cheaper!
"""

import os
import re
import anthropic
from typing import Dict, List
from utils.logger import get_logger

logger = get_logger()


class HTMLSpecificationExtractor:
    """Extract specification metadata from HTML using AI."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def extract_from_html(self, html_text: str, subject: str, 
                         exam_board: str, qualification: str) -> Dict:
        """
        Extract specification metadata from HTML.
        
        Args:
            html_text: HTML content from specification page
            subject: Subject name (e.g., "History")
            exam_board: Exam board (e.g., "AQA")
            qualification: Qualification type (e.g., "A-Level")
        
        Returns:
            {
                "metadata": {...},
                "components": [...],
                "constraints": [...]
            }
        """
        logger.info(f"Extracting metadata from HTML for {subject}")
        
        # Truncate HTML to reasonable size (Claude can handle it but let's be efficient)
        clean_html = self._clean_html(html_text)
        
        # Extract in one AI call to save costs
        prompt = f"""You are analyzing a UK exam specification webpage for {subject} ({qualification}) from {exam_board}.

This is the HTML from the specification page. Extract the following:

1. **METADATA:**
   - Subject code (usually 4 digits like "7042")
   - Guided learning hours (total hours if mentioned)
   - Assessment overview (how the course is assessed)

2. **COMPONENTS** (major parts of the course):
   - Component code (e.g., "Component 1", "C1", "Paper 1")
   - Component name (e.g., "Breadth Study")
   - Selection type: Is it "choose_one", "choose_multiple", or "required_all"?
   - If choice: How many to choose? (count_required)
   - If choice: How many available? (total_available)
   - Assessment weight (e.g., "40%")
   
   NOTE: Most subjects have ALL topics required. Only subjects like History/English have choices.

3. **CONSTRAINTS** (selection rules):
   - Geographic diversity (e.g., "must study British AND non-British")
   - Prohibited combinations (e.g., "cannot choose 1C with 2C")
   - Chronological requirements (e.g., "must cover 200 years")
   - Genre requirements (for English - must study prose, poetry, drama)
   
   NOTE: Most subjects have NO constraints. Only extract if explicitly stated.

4. **TOPIC OPTIONS** (if there are chooseable options like History 1A, 1B, 2A, 2B):
   - Option code (e.g., "1B", "2S")
   - Option title
   - Chronological period if mentioned (e.g., "1469-1598")
   - Geographic region if clear (e.g., "British", "European", "American")
   
   NOTE: Only extract this for subjects with option codes. Most subjects just have numbered topics (3.1, 3.2).

CRITICAL: Return ONLY the raw JSON object with NO explanation, NO markdown, NO commentary.
Start your response with {{ and end with }}

{{
  "metadata": {{
    "subject_code": "...",
    "guided_learning_hours": 360,
    "assessment_overview": "..."
  }},
  "components": [
    {{
      "code": "Component 1",
      "name": "Breadth Study",
      "selection_type": "choose_one",
      "count_required": 1,
      "total_available": 11,
      "weight": "40%"
    }}
  ],
  "constraints": [
    {{
      "type": "geographic_diversity",
      "description": "Students must study one British and one non-British option",
      "rule_details": {{"must_include": ["British", "non-British"]}}
    }}
  ],
  "options": [
    {{
      "code": "1B",
      "title": "Spain in the Age of Discovery",
      "period": "1469-1598",
      "region": "European"
    }}
  ]
}}

If the subject has NO components/constraints/options (like most simple subjects), return empty arrays.

HTML CONTENT:
{clean_html[:15000]}"""
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse JSON response
            result_text = response.content[0].text.strip()
            
            # Debug: log what we got
            logger.info(f"[DEBUG] AI response length: {len(result_text)}")
            logger.info(f"[DEBUG] First 100 chars: {result_text[:100]}")
            
            # Clean markdown if present
            if '```' in result_text:
                # Extract JSON from markdown code block
                parts = result_text.split('```')
                for part in parts:
                    part = part.strip()
                    if part.startswith('json'):
                        result_text = part[4:].strip()
                        break
                    elif part.startswith('{'):
                        result_text = part
                        break
            
            # If still has explanation text, find the JSON
            if not result_text.strip().startswith('{'):
                # Find first { and last }
                start = result_text.find('{')
                end = result_text.rfind('}')
                if start != -1 and end != -1:
                    result_text = result_text[start:end+1]
            
            # Remove any leading/trailing whitespace
            result_text = result_text.strip()
            
            if not result_text or not result_text.startswith('{'):
                raise ValueError(f"AI returned invalid JSON format. Got: {result_text[:200]}")
            
            import json
            data = json.loads(result_text)
            
            logger.info(f"[OK] Extracted from HTML")
            logger.info(f"  - Components: {len(data.get('components', []))}")
            logger.info(f"  - Constraints: {len(data.get('constraints', []))}")
            logger.info(f"  - Options: {len(data.get('options', []))}")
            
            return data
            
        except Exception as e:
            logger.error(f"AI extraction from HTML failed: {e}")
            return {}
    
    def _clean_html(self, html: str) -> str:
        """Remove unnecessary HTML to reduce token usage."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove script, style, nav, footer
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        
        # Get main content if exists
        main = soup.find('main') or soup.find('article') or soup.find(class_=re.compile(r'content|main'))
        
        if main:
            return main.get_text(separator='\n', strip=True)
        
        return soup.get_text(separator='\n', strip=True)


if __name__ == '__main__':
    # Quick test
    import requests
    
    url = "https://www.aqa.org.uk/subjects/history/a-level/history-7042/specification"
    response = requests.get(url)
    
    extractor = HTMLSpecificationExtractor()
    result = extractor.extract_from_html(response.text, "History", "AQA", "A-Level")
    
    import json
    print(json.dumps(result, indent=2))
