"""
Topic Extractor module for AI-assisted extraction of curriculum topics.

This module contains functions to extract structured topic data from
educational content using the Gemini API.
"""

import os
import json
import time
import re
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Union

from utils.logger import get_logger

# Initialize logger
logger = get_logger()

# Load environment variables
load_dotenv()

# Check if API keys are available
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI2.5_API_KEY")

if not GEMINI_API_KEY:
    logger.warning("GEMINI2.5_API_KEY not found in environment variables")
    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not found in environment variables - AI extraction will not work")


def create_topic_extraction_prompt(content: str, subject: str, exam_type: str, exam_board: str) -> str:
    """
    Create a prompt for topic extraction.
    
    Args:
        content (str): Raw text content from specification or website
        subject (str): Subject name
        exam_type (str): Exam type (e.g., GCSE, A-Level)
        exam_board (str): Exam board name
        
    Returns:
        str: Formatted prompt for the AI
    """
    # Truncate content if it's too long
    max_content_length = 50000  # Approximate limit for safe processing
    if len(content) > max_content_length:
        content_excerpt = content[:max_content_length] + "... [content truncated]"
        logger.warning(f"Content for {subject} ({exam_type}) was truncated from {len(content)} to {len(content_excerpt)} characters")
        content = content_excerpt
    
    prompt = f"""
    You are an expert in UK educational curricula and exam specifications.

    Please extract the COMPLETE three-level topic hierarchy for {subject} ({exam_type}) from the {exam_board} exam board from the following content.
    
    The output MUST be structured as a JSON array where each object has these three fields:
    - "Module": The main topic area (e.g., "Number" for Mathematics, "Cell Biology" for Biology)
    - "Topic": The specific topic under the module (e.g., "Fractions", "Cell Structure")
    - "Sub Topic": A more specific subtopic under the topic
    
    It is CRITICAL that you include detailed subtopics. For example:
    
    For Mathematics:
    - Module: "Number"
    - Topic: "Fractions"
    - Sub Topic: "Addition and subtraction of fractions"
    
    For Biology:
    - Module: "Cell Biology"
    - Topic: "Cell Structure"
    - Sub Topic: "Eukaryotic vs prokaryotic cells"
    
    Be extremely thorough and extract EVERY subtopic mentioned in the specification. Ensure you break down each topic into its detailed components. Look for bullet points, numbered lists, and paragraph descriptions that explain the specific content that students need to learn.
    
    Format the output as a valid JSON array of objects with those three fields.
    Ensure the response can be parsed with json.loads().
    
    CONTENT:
    {content}
    """
    
    return prompt


def call_gemini_api(prompt: str, retries: int = 3, model: str = "gemini-1.5-pro-latest") -> Optional[str]:
    """
    Call Google Gemini API with the given prompt.
    
    Args:
        prompt (str): The formatted prompt to send to the API
        retries (int): Number of retries on failure
        model (str): Gemini model to use
        
    Returns:
        str or None: API response content or None if failed
    """
    try:
        import google.generativeai as genai
    except ImportError:
        logger.error("Google GenerativeAI library not installed. Run: pip install google-generativeai")
        return None
    
    # Configure the Gemini API
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Customize generation config
    generation_config = {
        "temperature": 0.2,  # Lower temperature for more factual, consistent outputs
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,  # Use more tokens for comprehensive topic extraction
    }
    
    # Safety settings - set to the least restrictive to prevent filtering of educational content
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
    ]
    
    # System instruction for Gemini
    system_instruction = (
        "You are an expert in educational curricula and exam specifications. "
        "Extract detailed topic hierarchies from educational content. "
        "Always format your responses as valid JSON arrays of objects with 'Module', 'Topic', and 'Sub Topic' fields. "
        "Your output must be parseable with json.loads()."
    )
    
    for attempt in range(retries):
        try:
            # Initialize the model
            model = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
                safety_settings=safety_settings,
                system_instruction=system_instruction
            )
            
            # Generate the response
            response = model.generate_content(prompt)
            
            # Extract the text from the response
            response_text = response.text if hasattr(response, 'text') else None
            
            # Validate and clean up JSON
            if response_text:
                # Extract JSON array from response if not already a clean JSON
                json_match = re.search(r'\[\s*{.+}\s*\]', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
                
                # Try to parse as JSON to verify it's valid
                try:
                    json.loads(response_text)
                    return response_text
                except json.JSONDecodeError:
                    logger.warning("Gemini response was not valid JSON. Retrying...")
            
            time.sleep(2)  # Add delay between retries
            
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
    
    logger.error("Failed to get valid JSON response from Gemini API")
    return None

def call_anthropic_api(prompt: str, retries: int = 3, model: str = "claude-3-haiku-20240307") -> Optional[str]:
    """
    Call Anthropic API with the given prompt (fallback method).
    
    Args:
        prompt (str): The formatted prompt to send to the API
        retries (int): Number of retries on failure
        model (str): Anthropic model to use
        
    Returns:
        str or None: API response content or None if failed
    """
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set, cannot use fallback")
        return None
        
    try:
        import anthropic
    except ImportError:
        logger.error("Anthropic library not installed. Run: pip install anthropic")
        return None
    
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    for attempt in range(retries):
        try:
            message = client.messages.create(
                model=model,
                max_tokens=4000,
                system="You are an expert in educational curricula and exam specifications. "
                       "Always format your responses as valid JSON that can be parsed with json.loads().",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract content from response
            response_content = message.content[0].text if hasattr(message, 'content') and message.content else None
            
            # Validate and clean up JSON
            if response_content:
                # Extract JSON array from response if not already a clean JSON
                json_match = re.search(r'\[\s*{.+}\s*\]', response_content, re.DOTALL)
                if json_match:
                    response_content = json_match.group(0)
                
                # Try to parse as JSON to verify it's valid
                try:
                    json.loads(response_content)
                    return response_content
                except json.JSONDecodeError:
                    logger.warning("AI response was not valid JSON. Retrying...")
            
            time.sleep(2)  # Add delay between retries
            
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
    
    logger.error("Failed to get valid JSON response from Anthropic API")
    return None


def parse_ai_response(response: Optional[str], subject: str, 
                     exam_type: str, exam_board: str) -> List[Dict[str, str]]:
    """
    Parse the AI response into structured topic data.
    
    Args:
        response (str): JSON string from AI
        subject (str): Subject name
        exam_type (str): Exam type
        exam_board (str): Exam board name
        
    Returns:
        list: List of topic data dictionaries
    """
    if not response:
        logger.error("No AI response to parse")
        return []
    
    try:
        # Parse JSON response
        topic_data = json.loads(response)
        
        # Ensure it's a list
        if not isinstance(topic_data, list):
            logger.error("AI response is not a list")
            return []
        
        # Standardize and enrich data
        standardized_data = []
        for item in topic_data:
            # Ensure all required fields are present
            if "Module" not in item or "Topic" not in item:
                logger.warning(f"Skipping item without required fields: {item}")
                continue
            
            standardized_item = {
                "Exam Board": exam_board,
                "Exam Type": exam_type,
                "Subject": subject,
                "Module": item["Module"],
                "Topic": item["Topic"]
            }
            
            # Add Sub Topic if present
            if "Sub Topic" in item and item["Sub Topic"]:
                standardized_item["Sub Topic"] = item["Sub Topic"]
            
            standardized_data.append(standardized_item)
        
        logger.info(f"Parsed {len(standardized_data)} topics from AI response")
        return standardized_data
        
    except json.JSONDecodeError:
        logger.error("Failed to parse AI response as JSON")
        return []
    except Exception as e:
        logger.error(f"Error parsing AI response: {e}")
        return []


def extract_topics_from_content(content: str, subject: str, 
                               exam_type: str, exam_board: str) -> List[Dict[str, str]]:
    """
    Use AI to extract and structure topics from content.
    
    Args:
        content (str): Raw text content from specification or website
        subject (str): Subject name
        exam_type (str): Exam type (e.g., GCSE, A-Level)
        exam_board (str): Exam board name
        
    Returns:
        list: Structured topic data
    """
    # Create the prompt
    prompt = create_topic_extraction_prompt(content, subject, exam_type, exam_board)
    
    # Check for Gemini API key first
    response = None
    if GEMINI_API_KEY:
        logger.info(f"Using Gemini API for extracting topics from {subject} ({exam_type})")
        response = call_gemini_api(prompt)
    
    # Fall back to Anthropic API if Gemini fails or is not available
    if not response and ANTHROPIC_API_KEY:
        logger.info(f"Falling back to Anthropic API for extracting topics from {subject} ({exam_type})")
        response = call_anthropic_api(prompt)
    
    # Check if we have a valid response from either API
    if not response:
        if not GEMINI_API_KEY and not ANTHROPIC_API_KEY:
            logger.error("Cannot extract topics: No API keys available (GEMINI2.5_API_KEY or ANTHROPIC_API_KEY)")
        else:
            logger.error("Failed to extract topics: Both APIs returned no valid response")
        return []
    
    # Parse the AI response
    return parse_ai_response(response, subject, exam_type, exam_board)


def extract_topics_from_pdf(pdf_path: str, subject: str, 
                           exam_type: str, exam_board: str) -> List[Dict[str, str]]:
    """
    Extract topics from a PDF specification document.
    
    Args:
        pdf_path (str): Path to the PDF file
        subject (str): Subject name
        exam_type (str): Exam type (e.g., GCSE, A-Level)
        exam_board (str): Exam board name
        
    Returns:
        list: Structured topic data
    """
    try:
        import PyPDF2
    except ImportError:
        logger.error("PyPDF2 library not installed. Run: pip install PyPDF2")
        return []
    
    try:
        # Extract text from PDF
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                text += reader.pages[page_num].extract_text() + "\n"
        
        # Extract topics using the AI
        return extract_topics_from_content(text, subject, exam_type, exam_board)
        
    except Exception as e:
        logger.error(f"Error extracting topics from PDF: {e}")
        return []


def extract_topics_from_html(html: str, subject: str, 
                            exam_type: str, exam_board: str) -> List[Dict[str, str]]:
    """
    Extract topics from HTML content.
    
    Args:
        html (str): HTML content
        subject (str): Subject name
        exam_type (str): Exam type (e.g., GCSE, A-Level)
        exam_board (str): Exam board name
        
    Returns:
        list: Structured topic data
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("BeautifulSoup library not installed. Run: pip install beautifulsoup4")
        return []
    
    try:
        # Parse HTML and extract text
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get text
        text = soup.get_text(separator="\n")
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Extract topics using the AI
        return extract_topics_from_content(text, subject, exam_type, exam_board)
        
    except Exception as e:
        logger.error(f"Error extracting topics from HTML: {e}")
        return []
