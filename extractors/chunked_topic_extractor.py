"""
Chunked Topic Extractor
Extracts topics section-by-section to overcome token limits
"""

import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv
import anthropic
import PyPDF2

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from utils.logger import get_logger

logger = get_logger()


class ChunkedTopicExtractor:
    """Extract topics by processing each section separately."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def extract_topics_complete(self, pdf_path: str, subject: str,
                                exam_board: str, qualification: str) -> list:
        """Extract ALL topics by processing sections individually."""
        
        logger.info(f"Extracting topics for {subject} using chunked method...")
        
        # Extract PDF text
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
        
        logger.info(f"Extracted {len(full_text)} characters from PDF")
        
        # Find all section markers (3.1, 3.2, 3.3, etc.)
        section_pattern = r'(3\.\d+)\s+([^\n]+)'
        sections = re.findall(section_pattern, full_text)
        
        logger.info(f"Found {len(sections)} sections to extract")
        
        all_topics = []
        
        # Extract each section separately
        for section_code, section_title in sections:
            logger.info(f"  Extracting {section_code}: {section_title[:50]}...")
            
            # Find the text for THIS section (from 3.1 to 3.2, or 3.2 to 3.3, etc.)
            section_text = self._extract_section_text(full_text, section_code)
            
            if not section_text:
                logger.warning(f"    No content found for {section_code}")
                continue
            
            # Extract topics for this section
            topics = self._extract_section_topics(
                section_code, section_title, section_text, subject
            )
            
            logger.info(f"    Found {len(topics)} sub-topics")
            all_topics.extend(topics)
        
        logger.info(f"Total extracted: {len(all_topics)} topics")
        
        return all_topics
    
    def _extract_section_text(self, full_text: str, section_code: str) -> str:
        """Extract text for one section."""
        
        # Find start of this section
        pattern = rf'{section_code}\s+[^\n]+'
        match = re.search(pattern, full_text)
        
        if not match:
            return ""
        
        start_pos = match.start()
        
        # Find start of NEXT section (3.2 after 3.1, or 4.0 after 3.5)
        next_section_num = section_code.split('.')[0]
        next_minor = int(section_code.split('.')[1]) + 1
        next_pattern = rf'({next_section_num}\.{next_minor}|{int(next_section_num)+1}\.0)\s+'
        
        next_match = re.search(next_pattern, full_text[start_pos + 10:])
        
        if next_match:
            end_pos = start_pos + next_match.start() + 10
            return full_text[start_pos:end_pos]
        else:
            # Last section - take rest of document
            return full_text[start_pos:start_pos + 15000]
    
    def _extract_section_topics(self, section_code: str, section_title: str,
                                section_text: str, subject: str) -> list:
        """Extract all sub-topics for one section using AI."""
        
        prompt = f"""Analyze this section from a {subject} specification.

Section: {section_code} {section_title}

Extract EVERY row from the content table. Each row is a topic students must learn.

For EACH row/topic, provide:
1. Topic name (from left column of table)
2. Brief description (from right column bullet points)

Return as JSON array:
[
  {{
    "code": "{section_code}.1",
    "title": "Nature of law",
    "parent_code": "{section_code}",
    "level": 1,
    "description": "Distinction between legal rules and other rules"
  }},
  {{
    "code": "{section_code}.2", 
    "title": "Law and society",
    "parent_code": "{section_code}",
    "level": 1,
    "description": "Role law plays in society"
  }}
]

Section text:
{section_text[:20000]}"""
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result_text = response.content[0].text.strip()
            
            if '[' in result_text:
                start = result_text.find('[')
                end = result_text.rfind(']') + 1
                result_text = result_text[start:end]
            
            import json
            topics = json.loads(result_text)
            
            # Add main section as Level 0
            all_topics = [{
                'code': section_code,
                'title': section_title,
                'level': 0,
                'parent_code': None,
                'component': 'All papers',
                'content_points': [t['title'] for t in topics]  # For compatibility
            }]
            
            # Add extracted sub-topics
            all_topics.extend(topics)
            
            return all_topics
            
        except Exception as e:
            logger.error(f"Error extracting {section_code}: {e}")
            return []


if __name__ == '__main__':
    extractor = ChunkedTopicExtractor()
    
    pdf_path = "data/raw/AQA/specifications/Law_A-Level_7162.pdf"
    
    if Path(pdf_path).exists():
        topics = extractor.extract_topics_complete(
            pdf_path, "Law", "AQA", "A-Level"
        )
        
        print(f"\nExtracted {len(topics)} topics")
        
        # Group by level
        from collections import Counter
        by_level = Counter(t['level'] for t in topics)
        print(f"\nBy level: {dict(by_level)}")
        
        # Show samples
        print(f"\nLevel 0 topics:")
        for t in [x for x in topics if x['level'] == 0]:
            print(f"  {t['code']}: {t['title']}")
        
        print(f"\nLevel 1 samples (first 15):")
        for t in [x for x in topics if x['level'] == 1][:15]:
            print(f"  {t['code']}: {t['title']} (parent: {t.get('parent_code')})")
    else:
        print(f"PDF not found: {pdf_path}")




















