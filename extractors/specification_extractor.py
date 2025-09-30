"""
Enhanced Specification Extractor
Extracts complete specification context including structure, constraints, and metadata.
"""

import os
import json
import yaml
from typing import Dict, List, Optional
from pathlib import Path
import PyPDF2
import anthropic

from utils.logger import get_logger

logger = get_logger()


class SpecificationExtractor:
    """
    Extracts comprehensive specification data using AI.
    Goes beyond just topics - captures structure, rules, and context.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize with AI client.
        
        Args:
            api_key: Anthropic API key (from env if not provided)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # Load prompts from config
        prompts_file = Path(__file__).parent.parent / 'config' / 'extraction_prompts.yaml'
        if prompts_file.exists():
            with open(prompts_file) as f:
                self.prompts = yaml.safe_load(f)
        else:
            logger.warning("Prompts file not found, using defaults")
            self.prompts = {}
    
    def extract_complete_specification(self, pdf_path: str, subject: str,
                                      exam_board: str, qualification: str) -> Dict:
        """
        Extract everything from a specification PDF.
        
        Returns:
            {
                "metadata": {...},
                "components": [...],
                "constraints": [...],
                "options": [...],
                "vocabulary": [...]
            }
        """
        logger.info(f"Extracting complete specification for {subject} ({exam_board}, {qualification})")
        
        # Extract full text from PDF
        full_text = self._extract_pdf_text(pdf_path)
        
        if not full_text:
            logger.error(f"Failed to extract text from {pdf_path}")
            return {}
        
        logger.info(f"Extracted {len(full_text)} characters from PDF")
        
        # Extract each component
        results = {}
        
        # 1. Metadata
        logger.info("Extracting specification metadata...")
        results['metadata'] = self._extract_metadata(full_text, subject, exam_board, qualification)
        
        # 2. Components
        logger.info("Extracting component structure...")
        results['components'] = self._extract_components(full_text, subject)
        
        # 3. Constraints
        logger.info("Extracting selection constraints...")
        results['constraints'] = self._extract_constraints(full_text, subject, results['components'])
        
        # 4. Topic Options
        logger.info("Extracting topic options...")
        results['options'] = self._extract_topic_options(full_text, subject, results['components'], exam_board, qualification)
        
        # Add context to each option (for uploader)
        for option in results.get('options', []):
            option['exam_board'] = exam_board
            option['subject'] = subject  
            option['qualification'] = qualification
        
        # 5. Vocabulary
        logger.info("Extracting subject vocabulary...")
        results['vocabulary'] = self._extract_vocabulary(full_text, subject)
        
        return results
    
    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract all text from PDF."""
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""
    
    def _extract_metadata(self, text: str, subject: str, exam_board: str, qualification: str) -> Dict:
        """Extract specification overview metadata."""
        
        prompt = f"""You are analyzing a UK exam specification for {subject} ({qualification}) from {exam_board}.

Extract the high-level specification metadata:

1. **Subject Code** (e.g., "7042", "8300") - usually found near title
2. **Subject Description** - What is this qualification about? (2-3 sentences)
3. **Guided Learning Hours** - Total hours if mentioned
4. **Assessment Overview** - How is it assessed overall?
5. **Specification Version** - Version number if mentioned

Return ONLY valid JSON (no markdown, no explanation):
{{
  "subject_code": "...",
  "description": "...",
  "guided_learning_hours": 360,
  "assessment_overview": "...",
  "spec_version": "..."
}}

SPECIFICATION TEXT (first 10000 chars):
{text[:10000]}"""
        
        return self._call_ai(prompt, "metadata")
    
    def _extract_components(self, text: str, subject: str) -> List[Dict]:
        """Extract component structure."""
        
        prompt = f"""Analyze this {subject} specification and extract the COMPONENT STRUCTURE.

Components are major parts of the course (e.g., "Component 1", "Paper 1", "Unit 1").

For EACH component found:
- Component name
- Component code (C1, C2, etc. or extract from name)
- How students select: "choose_one", "choose_multiple", "required_all", or "custom"
- How many must choose
- Total options available
- Assessment weight (%)
- Assessment format

Look for sections like "Assessment", "Structure", "Components", "Papers".

Return ONLY valid JSON array (no markdown):
[
  {{
    "name": "Component 1: Breadth Study",
    "code": "C1",
    "selection_type": "choose_one",
    "count_required": 1,
    "total_available": 11,
    "weight": "40%",
    "assessment": "2.5 hour written exam",
    "description": "Study of historical developments over ~100 years"
  }}
]

SPECIFICATION TEXT (first 15000 chars):
{text[:15000]}"""
        
        return self._call_ai(prompt, "components")
    
    def _extract_constraints(self, text: str, subject: str, components: List[Dict]) -> List[Dict]:
        """Extract selection constraints and rules."""
        
        prompt = f"""Analyze this {subject} specification for SELECTION RULES and CONSTRAINTS.

Find ALL rules about how students choose topics, such as:

1. **Geographic/thematic diversity** - "must choose British AND non-British"
2. **Prohibited combinations** - "may not be combined with"
3. **Required pairings** - "must study both"
4. **Chronological requirements** - "must cover X years"

For EACH constraint:
- Type: geographic_diversity, prohibited_combination, required_pair, chronological_requirement
- Description in plain English
- Specific option codes affected
- Which components it applies to

Return ONLY valid JSON array (no markdown):
[
  {{
    "type": "geographic_diversity",
    "description": "Must choose 1 British and 1 non-British option",
    "rule_details": {{
      "british_codes": ["1C", "1D", ...],
      "non_british_codes": ["1A", "1B", ...]
    }},
    "applies_to_components": ["C1", "C2"]
  }}
]

SPECIFICATION TEXT (first 15000 chars):
{text[:15000]}"""
        
        return self._call_ai(prompt, "constraints")
    
    def _extract_topic_options(self, text: str, subject: str, components: List[Dict],
                               exam_board: str, qualification: str) -> List[Dict]:
        """Extract all topic options with metadata."""
        
        # Get option codes from components
        all_codes = []
        for comp in components:
            all_codes.extend(comp.get('option_codes', []))
        
        prompt = f"""Analyze this {subject} specification and extract ALL TOPIC OPTIONS.

These are the choosable topics students can select (codes like 1A, 1B, 2A, etc.).

For EACH option, extract:
1. Option code (e.g., "1C")
2. Full title
3. Time period if applicable (extract years)
4. Geographic region (British, European, American, Asian, etc.)
5. Component it belongs to
6. Type (breadth_study, depth_study, etc.)
7. Page reference if given
8. Key themes/sections listed under it

Be comprehensive - find ALL options in the specification.

Return ONLY valid JSON array (no markdown):
[
  {{
    "code": "1C",
    "title": "The Tudors: England, 1485–1603",
    "period": "1485-1603",
    "period_start": 1485,
    "period_end": 1603,
    "period_length": 118,
    "region": "British",
    "component": "Component 1",
    "component_code": "C1",
    "type": "breadth_study",
    "page_reference": "page 18",
    "key_themes": ["Consolidation of Dynasty", "Mid-Tudor Crisis", ...],
    "exam_board": "{exam_board}",
    "qualification": "{qualification}",
    "subject": "{subject}"
  }}
]

SPECIFICATION TEXT:
{text[:30000]}"""
        
        return self._call_ai(prompt, "options")
    
    def _extract_vocabulary(self, text: str, subject: str) -> List[Dict]:
        """Extract key subject-specific vocabulary."""
        
        prompt = f"""Analyze this {subject} specification and extract KEY VOCABULARY terms.

Focus on:
- Assessment-specific terms (e.g., "source analysis", "interpretation")
- Subject-specific concepts (e.g., "causation", "continuity")
- Technical terminology

For each term:
- The term itself
- Brief definition
- Category: "concept", "skill", "assessment", or "technique"

Return top 20-30 most important terms as JSON:
[
  {{
    "term": "Historical interpretation",
    "definition": "Analysis of how historians view past events",
    "category": "skill"
  }}
]

SPECIFICATION TEXT (sample):
{text[:8000]}"""
        
        return self._call_ai(prompt, "vocabulary")
    
    def _call_ai(self, prompt: str, extraction_type: str) -> any:
        """Call Claude AI and parse JSON response."""
        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8000,
                temperature=0.1,  # Low temperature for factual extraction
                system="You are an expert at analyzing UK exam specifications. Always return ONLY valid JSON with no markdown formatting, no code blocks, no explanations - just the raw JSON.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # Clean response (remove markdown if present)
            response_text = response_text.strip()
            if response_text.startswith('```'):
                # Remove code blocks
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])
            
            # Parse JSON
            result = json.loads(response_text)
            logger.info(f"Successfully extracted {extraction_type}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response for {extraction_type}: {e}")
            logger.debug(f"Response was: {response_text[:500]}")
            return {} if extraction_type in ['metadata'] else []
            
        except Exception as e:
            logger.error(f"Error calling AI for {extraction_type}: {e}")
            return {} if extraction_type in ['metadata'] else []
