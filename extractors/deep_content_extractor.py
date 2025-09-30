"""
Deep Content Extractor - Extract complete hierarchical content for each topic option.
Gets Level 1 (study areas) and Level 2 (content points) for maximum detail.
"""

import json
import re
from typing import Dict, List, Optional
from utils.logger import get_logger
import anthropic
import os

logger = get_logger()


class DeepContentExtractor:
    """
    Extracts complete hierarchical content for topic options.
    
    For History example "1B Spain 1469-1598":
    - Extracts key questions
    - Extracts Part one, Part two (Level 1)
    - Extracts all bullet points within each part (Level 2)
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def extract_option_complete(self, pdf_text: str, option_code: str, 
                               option_title: str, subject: str) -> Dict:
        """
        Extract COMPLETE content for a single option.
        
        Returns:
        {
          "option_code": "1B",
          "option_title": "Spain in the Age of Discovery, 1469-1598",
          "key_questions": [...],
          "study_areas": [
            {
              "area_title": "Part one: the establishment of a 'New Monarchy', 1469-1556",
              "period": "1469-1556",
              "sections": [
                {
                  "section_title": "The forging of a new state, 1469-1516",
                  "content_points": [...]
                }
              ]
            }
          ]
        }
        """
        logger.info(f"Deep extracting content for {option_code}: {option_title}")
        
        # Find the section for this option in the PDF text
        section_text = self._extract_option_section(pdf_text, option_code, option_title)
        
        if not section_text:
            logger.warning(f"Could not find section for {option_code} in PDF")
            return {}
        
        logger.info(f"Found section text: {len(section_text)} characters")
        
        # Extract complete hierarchical structure
        result = self._extract_hierarchical_content(
            section_text, option_code, option_title, subject
        )
        
        return result
    
    def _extract_option_section(self, full_text: str, option_code: str, option_title: str) -> str:
        """
        Extract just the section of the PDF that covers this option.
        Looks for the DETAILED content section, not just the table of contents.
        """
        # For History, the detailed sections come AFTER "Subject content" heading
        # and usually have longer content with key questions and bullet points
        
        # Find all occurrences of this option code
        pattern = rf"\b{option_code}\b"
        matches = list(re.finditer(pattern, full_text))
        
        if not matches:
            logger.warning(f"No matches found for {option_code}")
            return ""
        
        logger.info(f"Found {len(matches)} occurrences of {option_code}")
        
        # For each match, check if it has detailed content nearby
        best_match = None
        best_score = 0
        
        for match in matches:
            start_pos = match.start()
            # Check next 5000 chars for indicators of detailed content
            sample = full_text[start_pos:start_pos + 5000]
            
            # Score this section based on detailed content indicators
            score = 0
            if "key questions" in sample.lower() or "this option allows" in sample.lower():
                score += 10
            if "part one" in sample.lower() or "part two" in sample.lower():
                score += 10
            # Count bullet points (often indicates detailed content)
            score += sample.count('•') + sample.count('–')
            
            if score > best_score:
                best_score = score
                best_match = match
        
        if not best_match:
            # Fallback to first match
            best_match = matches[0]
            logger.warning(f"Using first match (no detailed content indicators found)")
        else:
            logger.info(f"Using match with score {best_score} (has detailed content)")
        
        start_pos = best_match.start()
        
        # Find where next option starts (or end of document)
        # Next option would be like "1C" or "2A" etc
        next_codes = self._get_next_option_codes(option_code)
        
        end_pos = len(full_text)
        for next_code in next_codes:
            next_pattern = rf"\n{next_code}\s+"
            next_match = re.search(next_pattern, full_text[start_pos + 100:])  # Start searching after current option
            if next_match:
                end_pos = start_pos + 100 + next_match.start()
                break
        
        section = full_text[start_pos:end_pos]
        return section
    
    def _get_next_option_codes(self, current_code: str) -> List[str]:
        """Get possible next option codes to find section boundaries."""
        # If current is "1B", next could be "1C", "1D", etc. or "2A" if Component 1 ends
        
        if current_code[0].isdigit():
            component = current_code[0]
            letter = current_code[1]
            
            # Generate next letters in same component
            next_codes = []
            for next_letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                if next_letter > letter:
                    next_codes.append(f"{component}{next_letter}")
                    if len(next_codes) >= 5:  # Check a few
                        break
            
            # Also check next component
            next_component = str(int(component) + 1)
            next_codes.extend([f"{next_component}A", f"{next_component}B", f"{next_component}C"])
            
            return next_codes
        
        return []
    
    def _extract_hierarchical_content(self, section_text: str, option_code: str,
                                     option_title: str, subject: str) -> Dict:
        """
        Use AI to extract complete hierarchical structure.
        """
        prompt = f"""You are analyzing a {subject} exam specification section.

Extract the COMPLETE HIERARCHICAL CONTENT for this option:

Option Code: {option_code}
Option Title: {option_title}

Extract:

1. **Key Questions** - Usually 4-6 questions starting with "What", "How", "To what extent"
   
2. **Study Areas** (Parts/Sections) - Major divisions like "Part one:", "Part two:"
   For each study area extract:
   - Title (e.g., "Part one: the establishment of a 'New Monarchy', 1469-1556")
   - Time period if mentioned
   - Sections within it
   
3. **Sections** - Within each study area
   For each section extract:
   - Section title (e.g., "The forging of a new state, 1469-1516")
   - All bullet point content points listed under it
   
Be COMPREHENSIVE - extract EVERY bullet point, EVERY section, EVERY study area.

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "option_code": "{option_code}",
  "option_title": "{option_title}",
  "key_questions": [
    "What were the political issues and how well did rulers handle them?",
    "Where did opposition come from and how was it dealt with?"
  ],
  "study_areas": [
    {{
      "area_title": "Part one: the establishment of a 'New Monarchy', 1469-1556",
      "period": "1469-1556",
      "sections": [
        {{
          "section_title": "The forging of a new state, 1469-1516",
          "period": "1469-1516",
          "content_points": [
            "The political, economic, social and religious condition of the Iberian Peninsula in 1469",
            "The restoration of royal authority; royal government; unity and confederation",
            "Muslims/Moriscos; the Reconquista; Jews/conversos and anti-Semitism"
          ]
        }},
        {{
          "section_title": "The drive to 'Great Power' status, 1516-1556",
          "period": "1516-1556",
          "content_points": [
            "Charles' inheritance; opposition and consolidation; revolts",
            "The workings of Empire: ideas and image; conciliar government"
          ]
        }}
      ]
    }},
    {{
      "area_title": "Part two: Philip II's Spain, 1556-1598",
      "period": "1556-1598",
      "sections": [...]
    }}
  ]
}}

SPECIFICATION SECTION:
{section_text}"""
        
        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8192,  # Maximum for Claude 3.5 Sonnet
                temperature=0.1,
                system="You are an expert at extracting detailed curriculum content. Return ONLY valid JSON with no markdown.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            
            # Debug: save raw response
            logger.info(f"Raw AI response length: {len(response_text)}")
            logger.debug(f"First 500 chars: {response_text[:500]}")
            
            # Clean markdown if present
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])
            
            if not response_text:
                logger.error("AI returned empty response")
                return {}
            
            result = json.loads(response_text)
            logger.info(f"Successfully extracted deep content for {option_code}")
            logger.info(f"  - Key questions: {len(result.get('key_questions', []))}")
            logger.info(f"  - Study areas: {len(result.get('study_areas', []))}")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response text: {response_text[:1000]}")
            return {}
        except Exception as e:
            logger.error(f"Failed to extract deep content: {e}")
            return {}
