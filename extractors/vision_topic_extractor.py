"""
Vision-Based Topic Extractor
Uses Claude's vision API to extract topics from PDF pages as images
This properly handles tables, diagrams, and complex layouts
"""

import os
import sys
import base64
import anthropic
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

from pdf2image import convert_from_path
from utils.logger import get_logger

logger = get_logger()


class VisionTopicExtractor:
    """Extract topics from PDFs using Claude Vision API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def extract_topics_from_pdf(self, pdf_path: str, subject: str, 
                                exam_board: str, qualification: str) -> list:
        """
        Extract ALL topics from PDF using vision.
        
        Returns:
            List of topics with full hierarchy
        """
        logger.info(f"Converting PDF to images for vision extraction...")
        
        # Path to local poppler installation
        poppler_path = Path(__file__).parent.parent / 'poppler' / 'poppler-24.08.0' / 'Library' / 'bin'
        
        # Convert PDF pages to images
        images = convert_from_path(pdf_path, dpi=200, poppler_path=str(poppler_path))
        logger.info(f"Converted {len(images)} pages to images")
        
        all_topics = []
        
        # Process specification content pages (usually pages 8-20)
        # Skip intro/assessment pages
        spec_pages = images[7:25] if len(images) > 25 else images[5:]
        
        logger.info(f"Processing {len(spec_pages)} specification pages with Vision API...")
        
        for page_num, image in enumerate(spec_pages, start=1):
            logger.info(f"  Analyzing page {page_num}/{len(spec_pages)}...")
            
            # Convert image to base64
            import io
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            img_base64 = base64.standard_b64encode(img_byte_arr).decode('utf-8')
            
            # Send to Claude Vision
            topics_from_page = self._extract_from_image(
                img_base64, subject, page_num
            )
            
            all_topics.extend(topics_from_page)
        
        logger.info(f"Extracted {len(all_topics)} total topics from {len(spec_pages)} pages")
        
        return all_topics
    
    def _extract_from_image(self, img_base64: str, subject: str, page_num: int) -> list:
        """Extract topics from one PDF page image."""
        
        prompt = f"""You are analyzing page {page_num} of an exam specification for {subject}.

This page shows curriculum content in a table format.

Extract EVERY row from the content table(s). For EACH row:

1. **Topic name** (left column - "Nature of law: law and society")
2. **Description/Content** (right column - the bullet points)
3. **Level**: Estimate based on indentation/formatting:
   - Level 1 = Main section headers
   - Level 2 = Sub-topics (like "Nature of law: law and society")
   - Level 3 = Detailed content points
4. **Parent**: Which topic is this under?

Return as JSON array:
[
  {{
    "title": "Nature of law: law and society",
    "level": 2,
    "parent": "Nature of law",
    "content": "The role law plays in society. The effect of law..."
  }}
]

Return EVERY row you see in the table, no matter how many. Return empty array [] if no content table on this page."""
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            )
            
            result_text = response.content[0].text.strip()
            
            # Parse JSON
            if '[' in result_text:
                start = result_text.find('[')
                end = result_text.rfind(']') + 1
                result_text = result_text[start:end]
            
            import json
            topics = json.loads(result_text)
            
            logger.info(f"    Page {page_num}: Found {len(topics)} topics")
            return topics
            
        except Exception as e:
            logger.error(f"Error extracting from page {page_num}: {e}")
            return []


if __name__ == '__main__':
    # Quick test
    extractor = VisionTopicExtractor()
    
    pdf_path = "data/raw/AQA/specifications/Law_A-Level_7162.pdf"
    
    if Path(pdf_path).exists():
        topics = extractor.extract_topics_from_pdf(
            pdf_path, "Law", "AQA", "A-Level"
        )
        
        print(f"\nExtracted {len(topics)} topics")
        print("\nFirst 10:")
        for t in topics[:10]:
            print(f"  L{t.get('level')}: {t.get('title')}")
    else:
        print(f"PDF not found: {pdf_path}")
