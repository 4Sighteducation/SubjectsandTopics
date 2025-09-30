"""
AQA exam board scraper implementation.

This module provides the AQAScraper class that scrapes topic lists and exam materials
from the AQA (Assessment and Qualifications Alliance) exam board website.
"""

import os
import re
import json
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin

from scrapers.base_scraper import BaseScraper
from utils.logger import get_logger
from utils.helpers import (
    sanitize_text, normalize_subject_name, normalize_exam_type, 
    extract_tables_from_html, ensure_directory
)
from utils.subjects import normalize_subject

# AQA-specific subject lists derived from official website URLs
AQA_GCSE_SUBJECTS = [
    "Art and Design (Art, craft and design)",
    "Art and Design (Fine art)",
    "Art and Design (Graphic communication)",
    "Art and Design (Photography)",
    "Art and Design (Textile design)",
    "Art and Design (Three-dimensional design)",
    "Bengali",
    "Biology",
    "Business",
    "Chemistry",
    "Chinese (Mandarin)",
    "Citizenship Studies",
    "Computer Science",
    "Dance",
    "Design and Technology",
    "Drama",
    "Economics",
    "Engineering",
    "English Language",
    "English Literature",
    "Food preparation and nutrition",
    "French",
    "Geography",
    "German",
    "Hebrew (Modern)",
    "History",
    "Italian",
    "Mathematics",
    "Media Studies",
    "Music",
    "Panjabi",
    "Physical Education",
    "Physics",
    "Polish",
    "Psychology",
    "Religious Studies",
    "Science",
    "Sociology",
    "Spanish",
    "Statistics",
    "Urdu"
]

AQA_A_LEVEL_SUBJECTS = [
    "Accounting",
    "Art and Design (Art, craft and design)",
    "Art and Design (Fine art)",
    "Art and Design (Graphic communication)",
    "Art and Design (Photography)",
    "Art and Design (Textile design)",
    "Art and Design (Three-dimensional design)",
    "Bengali",
    "Biology",
    "Business",
    "Chemistry",
    "Computer Science",
    "Dance",
    "Design and Technology",
    "Drama",
    "Economics",
    "English Language",
    "English Language and Literature",
    "English Literature A",
    "English Literature B",
    "Environmental Science",
    "French",
    "Further Mathematics",
    "Geography",
    "German",
    "Hebrew (Biblical)",
    "Hebrew (Modern)",
    "History",
    "Law",
    "Mathematics",
    "Media Studies",
    "Music",
    "Panjabi",
    "Philosophy",
    "Physical Education",
    "Physics",
    "Polish",
    "Politics",
    "Psychology",
    "Religious Studies",
    "Sociology",
    "Spanish"
]

    # URLs for AQA subjects from the official website
    # These will be used in the _get_subject_urls method

# Import AI-assisted topic extraction functions
try:
    from ai_helpers.topic_extractor import (
        extract_topics_from_html, 
        extract_topics_from_pdf,
        extract_topics_from_content
    )
    AI_HELPERS_AVAILABLE = True
except ImportError:
    AI_HELPERS_AVAILABLE = False
    logger = get_logger()
    logger.warning("AI helpers not available. Some features will be limited.")

logger = get_logger()


class AQAScraper(BaseScraper):
    """
    Scraper for the AQA exam board website.
    """
    
    # Direct specification URLs for GCSE subjects
    AQA_GCSE_SPEC_URLS = {
    "Art and Design (Art, craft and design)": "https://www.aqa.org.uk/subjects/art-and-design/gcse/art-and-design-8201",
    "Art and Design (Fine art)": "https://www.aqa.org.uk/subjects/art-and-design/gcse/art-and-design-8202",
    "Art and Design (Graphic communication)": "https://www.aqa.org.uk/subjects/art-and-design/gcse/art-and-design-8203",
    "Art and Design (Photography)": "https://www.aqa.org.uk/subjects/art-and-design/gcse/art-and-design-8206",
    "Art and Design (Textile design)": "https://www.aqa.org.uk/subjects/art-and-design/gcse/art-and-design-8204",
    "Art and Design (Three-dimensional design)": "https://www.aqa.org.uk/subjects/art-and-design/gcse/art-and-design-8205",
    "Bengali": "https://www.aqa.org.uk/subjects/bengali/gcse/bengali-8638",
    "Biology": "https://www.aqa.org.uk/subjects/biology/gcse/biology-8461",
    "Business": "https://www.aqa.org.uk/subjects/business/gcse/business-8132",
    "Chemistry": "https://www.aqa.org.uk/subjects/chemistry/gcse/chemistry-8462",
    "Chinese": "https://www.aqa.org.uk/subjects/chinese-mandarin/gcse/chinese-mandarin-8673",
    "Citizenship Studies": "https://www.aqa.org.uk/subjects/citizenship-studies/gcse/citizenship-studies-8100",
    "Computer Science": "https://www.aqa.org.uk/subjects/computer-science/gcse/computer-science-8525",
    "Dance": "https://www.aqa.org.uk/subjects/dance/gcse/dance-8236",
    "Design and Technology": "https://www.aqa.org.uk/subjects/design-and-technology/gcse/design-and-technology-8552",
    "Drama": "https://www.aqa.org.uk/subjects/drama/gcse/drama-8261",
    "Economics": "https://www.aqa.org.uk/subjects/economics/gcse/economics-8136",
    "Engineering": "https://www.aqa.org.uk/subjects/engineering/gcse/engineering-8852",
    "English Language": "https://www.aqa.org.uk/subjects/english/gcse/english-8700",
    "English Literature": "https://www.aqa.org.uk/subjects/english/gcse/english-8702",
    "Food preparation and nutrition": "https://www.aqa.org.uk/subjects/food-preparation-and-nutrition/gcse/food-preparation-and-nutrition-8585",
    "French": "https://www.aqa.org.uk/subjects/french/gcse/french-8652",
    "Geography": "https://www.aqa.org.uk/subjects/geography/gcse/geography-8035",
    "German": "https://www.aqa.org.uk/subjects/german/gcse/german-8662",
    "Hebrew (Modern)": "https://www.aqa.org.uk/subjects/hebrew-modern/gcse/hebrew-modern-8678",
    "History": "https://www.aqa.org.uk/subjects/history/gcse/history-8145",
    "Italian": "https://www.aqa.org.uk/subjects/italian/gcse/italian-8633",
    "Mathematics": "https://www.aqa.org.uk/subjects/mathematics/gcse/mathematics-8300",
    "Media Studies": "https://www.aqa.org.uk/subjects/media-studies/gcse/media-studies-8572",
    "Music": "https://www.aqa.org.uk/subjects/music/gcse/music-8271",
    "Panjabi": "https://www.aqa.org.uk/subjects/panjabi/gcse/panjabi-8683",
    "Physical Education": "https://www.aqa.org.uk/subjects/physical-education/gcse/physical-education-8582",
    "Physics": "https://www.aqa.org.uk/subjects/physics/gcse/physics-8463",
    "Polish": "https://www.aqa.org.uk/subjects/polish/gcse/polish-8688",
    "Psychology": "https://www.aqa.org.uk/subjects/psychology/a-level/psychology-7182/specification",
    "Religious Studies": "https://www.aqa.org.uk/subjects/religious-studies/gcse/religious-studies-8061",
    "Combined Science": "https://www.aqa.org.uk/subjects/science/gcse/science-8464/specification/specification-at-a-glance",
    "Sociology": "https://www.aqa.org.uk/subjects/sociology/gcse/sociology-8192",
    "Spanish": "https://www.aqa.org.uk/subjects/spanish/gcse/spanish-8692",
    "Statistics": "https://www.aqa.org.uk/subjects/mathematics/gcse/mathematics-8382",
    "Urdu": "https://www.aqa.org.uk/subjects/urdu/gcse/urdu-8648"
}

    
    # Direct specification URLs for A-Level subjects
    AQA_A_LEVEL_SPEC_URLS = {
    "Accounting": "https://www.aqa.org.uk/subjects/accounting/a-level/accounting-7127",
    "Art and Design (Art, craft and design)": "https://www.aqa.org.uk/subjects/art-and-design/a-level/art-and-design-7201",
    "Art and Design (Fine art)": "https://www.aqa.org.uk/subjects/art-and-design/a-level/art-and-design-7202",
    "Art and Design (Graphic communication)": "https://www.aqa.org.uk/subjects/art-and-design/a-level/art-and-design-7203",
    "Art and Design (Photography)": "https://www.aqa.org.uk/subjects/art-and-design/a-level/art-and-design-7206",
    "Art and Design (Textile design)": "https://www.aqa.org.uk/subjects/art-and-design/a-level/art-and-design-7204",
    "Art and Design (Three-dimensional design)": "https://www.aqa.org.uk/subjects/art-and-design/a-level/art-and-design-7205",
    "Bengali": "https://www.aqa.org.uk/subjects/bengali/a-level/bengali-7637",
    "Biology": "https://www.aqa.org.uk/subjects/biology/a-level/biology-7402",
    "Business": "https://www.aqa.org.uk/subjects/business/a-level/business-7132",
    "Chemistry": "https://www.aqa.org.uk/subjects/chemistry/a-level/chemistry-7405",
    "Computer Science": "https://www.aqa.org.uk/subjects/computer-science/a-level/computer-science-7517",
    "Dance": "https://www.aqa.org.uk/subjects/dance/a-level/dance-7237",
    "Design and Technology": "https://www.aqa.org.uk/subjects/design-and-technology/a-level/design-and-technology-7552",
    "Drama": "https://www.aqa.org.uk/subjects/drama/a-level/drama-7262",
    "Economics": "https://www.aqa.org.uk/subjects/economics/a-level/economics-7136",
    "Engineering": "https://www.aqa.org.uk/subjects/engineering/a-level/engineering-8852",
    "English": "https://www.aqa.org.uk/subjects/english/a-level/english-7700",
    "English Language and Literature": "https://www.aqa.org.uk/subjects/english/a-level/english-7707",
    "English Language": "https://www.aqa.org.uk/subjects/english/a-level/english-7702",
    "English Language and Literature": "https://www.aqa.org.uk/subjects/english/a-level/english-7707",
    "English Literature A": "https://www.aqa.org.uk/subjects/english/a-level/english-7712",
    "English Literature B": "https://www.aqa.org.uk/subjects/english/a-level/english-7717",
    "Environmental Science": "https://www.aqa.org.uk/subjects/environmental-science/a-level/environmental-science-7447",
    "Food Preparation and Nutrition": "https://www.aqa.org.uk/subjects/food-preparation-and-nutrition/a-level/food-preparation-and-nutrition-8585",
    "French": "https://www.aqa.org.uk/subjects/french/a-level/french-7652",
    "Further Mathematics": "https://www.aqa.org.uk/subjects/mathematics/a-level/mathematics-7367",
    "Geography": "https://www.aqa.org.uk/subjects/geography/a-level/geography-7037",
    "German": "https://www.aqa.org.uk/subjects/german/a-level/german-7662",
    "Hebrew (Biblical)": "https://www.aqa.org.uk/subjects/hebrew-(biblical)/a-level/hebrew-(biblical)-7671",
    "Hebrew (Modern)": "https://www.aqa.org.uk/subjects/hebrew-modern/a-level/hebrew-modern-7672",
    "History": "https://www.aqa.org.uk/subjects/history/a-level/history-7042",
    "Law": "https://www.aqa.org.uk/subjects/law/a-level/law-7162",
    "Mathematics": "https://www.aqa.org.uk/subjects/mathematics/a-level/mathematics-7357",
    "Media Studies": "https://www.aqa.org.uk/subjects/media-studies/a-level/media-studies-7572",
    "Music": "https://www.aqa.org.uk/subjects/music/a-level/music-7272",
    "Panjabi": "https://www.aqa.org.uk/subjects/panjabi/a-level/panjabi-7682",
    "Philosophy": "https://www.aqa.org.uk/subjects/philosophy/a-level/philosophy-7172",
    "Physical Education": "https://www.aqa.org.uk/subjects/physical-education/a-level/physical-education-7582",
    "Physics": "https://www.aqa.org.uk/subjects/physics/a-level/physics-7408",
    "Polish": "https://www.aqa.org.uk/subjects/polish/a-level/polish-7687",
    "Politics": "https://www.aqa.org.uk/subjects/politics/a-level/politics-7152",
    "Projects": "https://www.aqa.org.uk/subjects/projects/a-level/projects-8552",
    "Psychology": "https://www.aqa.org.uk/subjects/psychology/a-level/psychology-7182/specification/specification-at-a-glance",
    "Religious Studies": "https://www.aqa.org.uk/subjects/religion/a-level/religion-7142",
    "Russian": "https://www.aqa.org.uk/subjects/russian/a-level/russian-7697",
    "Sociology": "https://www.aqa.org.uk/subjects/sociology/a-level/sociology-7192",
    "Spanish": "https://www.aqa.org.uk/subjects/spanish/a-level/spanish-7692"
}
    
    def __init__(self, headless=True, delay=1.5):
        """
        Initialize the AQA scraper.
        
        Args:
            headless (bool): Whether to run the browser in headless mode
            delay (float): Delay between requests in seconds
        """
        super().__init__(
            name="AQA",
            base_url="https://www.aqa.org.uk",
            headless=headless,
            delay=delay
        )
        
        # AQA-specific URLs
        self.qualifications_url = urljoin(self.base_url, "/subjects")
        self.past_papers_url = urljoin(self.base_url, "/find-past-papers-and-mark-schemes")
        
        # Map of normalized subject names to AQA subject codes
        self.subject_code_map = {}
    
    def _get_subject_urls(self, exam_type=None):
        """
        Get URLs for all subjects based on exam type.
        
        Args:
            exam_type (str, optional): Type of exam to filter by
            
        Returns:
            dict: Dictionary mapping subject names to their URLs
        """
        logger.info(f"Getting subject URLs for AQA" + (f" ({exam_type})" if exam_type else ""))
        
        # Normalize exam_type for consistent matching
        norm_exam_type = normalize_exam_type(exam_type) if exam_type else None
        
        # Hard-coded subject URLs for AQA subjects
        subject_urls = {}
        
        # GCSE Subjects
        if not norm_exam_type or norm_exam_type.lower() == 'gcse':
            # Use AQA-specific GCSE subjects list
            for subject in AQA_GCSE_SUBJECTS:
                subject_lower = subject.lower()
                
                # Add specific URLs for GCSE subjects
                if subject_lower == "mathematics":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/mathematics/gcse/mathematics-8300"
                elif subject_lower == "english language":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/english/gcse/english-language-8700"
                elif subject_lower == "english literature":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/english/gcse/english-literature-8702"
                elif subject_lower == "biology":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/science/gcse/biology-8461"
                elif subject_lower == "chemistry":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/science/gcse/chemistry-8462"
                elif subject_lower == "physics":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/science/gcse/physics-8463"
                elif subject_lower == "science":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/science/gcse/combined-science-trilogy-8464"
                elif subject_lower == "food preparation and nutrition":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/food/gcse/food-preparation-and-nutrition-8585"
                elif subject_lower == "statistics":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/mathematics/gcse/statistics-8382"
                elif subject_lower == "french":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/languages/gcse/french-8658"
                elif subject_lower == "spanish":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/languages/gcse/spanish-8698"
                elif subject_lower == "german":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/languages/gcse/german-8668"
                elif subject_lower == "italian":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/languages/gcse/italian-8633"
                elif subject_lower == "urdu":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/languages/gcse/urdu-8648"
                elif subject_lower == "chinese (mandarin)":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/languages/gcse/chinese-spoken-mandarin-8673"
                elif subject_lower == "citizenship studies":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/citizenship/gcse/citizenship-studies-8100"
                elif subject_lower == "religious studies":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/religious-studies/gcse/religious-studies-a-8062"
                elif subject_lower == "computer science":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/computer-science-and-it/gcse/computer-science-8525"
                elif subject_lower == "design and technology":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/design-and-technology/gcse/design-and-technology-8552"
                elif subject_lower == "geography":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/geography/gcse/geography-8035"
                elif subject_lower == "history":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/history/gcse/history-8145"
                elif subject_lower == "psychology":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/psychology/gcse/psychology-8182"
                elif subject_lower == "sociology":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/sociology/gcse/sociology-8192"
                elif subject_lower == "business":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/business/gcse/business-8132"
                elif subject_lower == "economics":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/economics/gcse/economics-8136"
                elif subject_lower == "media studies":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/media-studies/gcse/media-studies-8572"
                elif subject_lower == "music":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/music/gcse/music-8271"
                elif subject_lower == "physical education":
                    subject_urls[subject] = "https://www.aqa.org.uk/subjects/physical-education/gcse/physical-education-8582"
                elif subject_lower.startswith("art and design"):
                    # Special handling for Art and Design variants
                    if "(art, craft and design)" in subject_lower:
                        subject_urls[subject] = "https://www.aqa.org.uk/subjects/art-and-design/gcse/art-and-design-8201-8206/subject-content/art,-craft-and-design"
                    elif "(fine art)" in subject_lower:
                        subject_urls[subject] = "https://www.aqa.org.uk/subjects/art-and-design/gcse/art-and-design-8201-8206/subject-content/fine-art"
                    elif "(graphic communication)" in subject_lower:
                        subject_urls[subject] = "https://www.aqa.org.uk/subjects/art-and-design/gcse/art-and-design-8201-8206/subject-content/graphic-communication"
                    elif "(textile design)" in subject_lower:
                        subject_urls[subject] = "https://www.aqa.org.uk/subjects/art-and-design/gcse/art-and-design-8201-8206/subject-content/textile-design"
                    elif "(three-dimensional design)" in subject_lower:
                        subject_urls[subject] = "https://www.aqa.org.uk/subjects/art-and-design/gcse/art-and-design-8201-8206/subject-content/three-dimensional-design"
                    elif "(photography)" in subject_lower:
                        subject_urls[subject] = "https://www.aqa.org.uk/subjects/art-and-design/gcse/art-and-design-8201-8206/subject-content/photography"
                    else:
                        subject_urls[subject] = "https://www.aqa.org.uk/subjects/art-and-design/gcse/art-and-design-8201-8206"
                else:
                    # Generate URL for other subjects based on common patterns
                    # Remove special characters and format for URL
                    url_part = subject_lower.replace("(", "").replace(")", "").replace(" and ", "-").replace(" ", "-").replace(":", "")
                    
                    # Standard GCSE URL pattern - use a generic pattern as fallback
                    subject_urls[subject] = f"https://www.aqa.org.uk/subjects/{url_part}/gcse/{url_part}"
        
        # A-Level Subjects
        if not norm_exam_type or norm_exam_type.lower() in ['a-level', 'as-level']:
            # Use AQA-specific A-Level subjects list
            for subject in AQA_A_LEVEL_SUBJECTS:
                subject_lower = subject.lower()
                # A-level subjects are referenced with (A-Level) suffix
                subject_with_level = f"{subject} (A-Level)"
                
                # Add specific URLs for A-Level subjects
                if subject_lower == "mathematics":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/mathematics/as-and-a-level/mathematics-7357"
                elif subject_lower == "further mathematics":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/mathematics/as-and-a-level/further-mathematics-7367"
                elif subject_lower == "statistics":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/mathematics/as-and-a-level/statistics-7366"
                elif subject_lower == "english language":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/english/as-and-a-level/english-language-7701-7702"
                elif subject_lower == "english language and literature":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/english/as-and-a-level/english-language-and-literature-7706-7707"
                elif subject_lower == "english literature a":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/english/as-and-a-level/english-literature-a-7711-7712"
                elif subject_lower == "english literature b":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/english/as-and-a-level/english-literature-b-7716-7717"
                elif subject_lower == "biology":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/science/as-and-a-level/biology-7401-7402"
                elif subject_lower == "chemistry":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/science/as-and-a-level/chemistry-7404-7405"
                elif subject_lower == "physics":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/science/as-and-a-level/physics-7407-7408"
                elif subject_lower == "computer science":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/computer-science-and-it/as-and-a-level/computer-science-7516-7517"
                elif subject_lower == "environmental science":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/science/as-and-a-level/environmental-science-7447"
                elif subject_lower == "psychology":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/psychology/as-and-a-level/psychology-7181-7182"
                elif subject_lower == "sociology":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/sociology/as-and-a-level/sociology-7191-7192"
                elif subject_lower == "politics":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/government-and-politics/as-and-a-level/politics-7151-7152"
                elif subject_lower == "business":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/business/as-and-a-level/business-7131-7132"
                elif subject_lower == "economics":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/economics/as-and-a-level/economics-7135-7136"
                elif subject_lower == "law":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/law/as-and-a-level/law-7161-7162"
                elif subject_lower == "religious studies":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/religious-studies/as-and-a-level/religious-studies-7061-7062"
                elif subject_lower == "geography":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/geography/as-and-a-level/geography-7036-7037"
                elif subject_lower == "history":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/history/as-and-a-level/history-7041-7042"
                elif subject_lower == "accounting":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/accounting/as-and-a-level/accounting-7126-7127"
                elif subject_lower == "design and technology":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/design-and-technology/as-and-a-level/design-and-technology-product-design-7551-7552"
                elif subject_lower == "media studies":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/media-studies/as-and-a-level/media-studies-7571-7572"
                elif subject_lower == "music":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/music/as-and-a-level/music-7271-7272"
                elif subject_lower == "physical education":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/physical-education/as-and-a-level/physical-education-7581-7582"
                elif subject_lower == "dance":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/dance/as-and-a-level/dance-7236-7237"
                elif subject_lower == "drama":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/drama/as-and-a-level/drama-and-theatre-7261-7262"
                elif subject_lower == "french":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/languages/as-and-a-level/french-7651-7652"
                elif subject_lower == "spanish":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/languages/as-and-a-level/spanish-7691-7692"
                elif subject_lower == "german":
                    subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/languages/as-and-a-level/german-7661-7662"
                elif subject_lower.startswith("art and design"):
                    # Special handling for Art and Design variants
                    if "(art, craft and design)" in subject_lower:
                        subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/art-and-design/as-and-a-level/art-and-design-7201-7206/subject-content/art,-craft-and-design"
                    elif "(fine art)" in subject_lower:
                        subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/art-and-design/as-and-a-level/art-and-design-7201-7206/subject-content/fine-art"
                    elif "(graphic communication)" in subject_lower:
                        subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/art-and-design/as-and-a-level/art-and-design-7201-7206/subject-content/graphic-communication"
                    elif "(textile design)" in subject_lower:
                        subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/art-and-design/as-and-a-level/art-and-design-7201-7206/subject-content/textile-design"
                    elif "(three-dimensional design)" in subject_lower:
                        subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/art-and-design/as-and-a-level/art-and-design-7201-7206/subject-content/three-dimensional-design"
                    elif "(photography)" in subject_lower:
                        subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/art-and-design/as-and-a-level/art-and-design-7201-7206/subject-content/photography"
                    else:
                        subject_urls[subject_with_level] = "https://www.aqa.org.uk/subjects/art-and-design/as-and-a-level/art-and-design-7201-7206"
                else:
                    # Generate URL for other subjects based on common patterns
                    # Remove special characters and format for URL
                    url_part = subject_lower.replace("(", "").replace(")", "").replace(" and ", "-").replace(" ", "-").replace(":", "")
                    
                    # Standard A-level URL pattern
                    subject_urls[subject_with_level] = f"https://www.aqa.org.uk/subjects/{url_part}/as-and-a-level/{url_part}"
        
        # Notes on using hard-coded URLs temporarily:
        # The approach above is a temporary solution to bypass the website scraping issues.
        # In a production environment, you'd want to implement a more robust solution
        # that actually scrapes the AQA website. For this demo, this will allow us to
        # continue with testing the rest of the functionality.
        
        # Original code is commented below:
        # try:
        #    # Get the qualifications page
        #    html = self._get_page(self.qualifications_url, use_selenium=True)
        #    if not html:
        #        logger.error("Failed to get AQA qualifications page")
        #        return {}
        #    
        #    soup = BeautifulSoup(html, 'lxml')
        #    
        #    # More flexible approach to find links
        #    # Look for any links that might contain subject information
        #    for link in soup.find_all('a', href=True):
        #        href = link.get('href', '')
        #        text = sanitize_text(link.text)
        #        
        #        # Skip empty or very short text links
        #        if not text or len(text) < 3:
        #            continue
        #            
        #        # Look for subject-related links
        #        if ('subjects/' in href or 'qualification' in href):
        #            # Filter by exam type if specified
        #            if norm_exam_type:
        #                if norm_exam_type.lower() == 'gcse' and 'gcse' in href.lower():
        #                    subject_urls[text] = urljoin(self.base_url, href)
        #                elif norm_exam_type.lower() in ['a-level', 'as-level'] and ('a-level' in href.lower() or 'a-level' in href.lower()):
        #                    subject_urls[text] = urljoin(self.base_url, href)
        #            else:
        #                # If no exam type specified, include all
        #                subject_urls[text] = urljoin(self.base_url, href)
        # except Exception as e:
        #    logger.error(f"Error while getting subject URLs: {e}", exc_info=True)
        
        logger.info(f"Found {len(subject_urls)} subject URLs")
        return subject_urls
    
    def _extract_specification_topics(self, specification_url, exam_type, subject):
        """
        Extract topics from a specification URL.
        
        Args:
            specification_url (str): URL of the specification
            exam_type (str): Type of exam
            subject (str): Subject name
            
        Returns:
            list: List of topic data dictionaries
        """
        logger.info(f"Extracting topics from specification: {specification_url}")
        
        html = self._get_page(specification_url, use_selenium=True)
        if not html:
            logger.error(f"Failed to get specification page: {specification_url}")
            return []
        
        # Try AI-assisted extraction first if available
        if AI_HELPERS_AVAILABLE:
            logger.info(f"Attempting AI-assisted topic extraction for {subject}")
            
            # If URL is a PDF, download it and use extract_topics_from_pdf
            if specification_url.lower().endswith('.pdf'):
                # Download the PDF
                pdf_filename = f"{normalize_subject_name(subject)}_{normalize_exam_type(exam_type)}_spec.pdf"
                pdf_subdir = os.path.join("specifications", self.name.lower())
                pdf_path = self._download_document(
                    specification_url, 
                    pdf_filename, 
                    pdf_subdir, 
                    "specification"
                )
                
                if pdf_path:
                    # Extract topics from the downloaded PDF
                    ai_topics = extract_topics_from_pdf(
                        pdf_path, subject, exam_type, self.name
                    )
                    
                    if ai_topics:
                        logger.info(f"AI successfully extracted {len(ai_topics)} topics from PDF")
                        return ai_topics
                    else:
                        logger.warning("AI extraction from PDF failed, falling back to conventional methods")
            else:
                # For HTML content, use extract_topics_from_html
                ai_topics = extract_topics_from_html(
                    html, subject, exam_type, self.name
                )
                
                if ai_topics:
                    logger.info(f"AI successfully extracted {len(ai_topics)} topics from HTML")
                    return ai_topics
                else:
                    logger.warning("AI extraction from HTML failed, falling back to conventional methods")
        
        # Fallback to conventional extraction methods
        soup = BeautifulSoup(html, 'lxml')
        topics_data = []
        
        # For problematic subjects, use predefined topic structures
        
        # For Mathematics GCSE, use predefined structure
        if subject.lower() == "mathematics" and exam_type.lower() == "gcse":
            # GCSE Mathematics main topics and subtopics based on AQA specification
            topic_structure = {
                "Number": [
                    "Structure and calculation",
                    "Fractions, decimals and percentages",
                    "Measures and accuracy"
                ],
                "Algebra": [
                    "Notation, vocabulary and manipulation",
                    "Graphs",
                    "Solving equations and inequalities",
                    "Sequences"
                ],
                "Ratio, proportion and rates of change": [
                    "Ratio",
                    "Proportion",
                    "Percentages",
                    "Compound growth and decay"
                ],
                "Geometry and measures": [
                    "Properties and constructions",
                    "Mensuration and calculation",
                    "Vectors"
                ],
                "Probability": [
                    "Probability",
                    "Set theory"
                ],
                "Statistics": [
                    "Sampling",
                    "Data representation",
                    "Measures of central tendency and spread"
                ]
            }
            
            for module, topics in topic_structure.items():
                for topic in topics:
                    topics_data.append(self._build_topic_data(
                        exam_board="AQA",
                        exam_type=exam_type,
                        subject=subject,
                        module=module,
                        topic=topic
                    ))
            
            logger.info(f"Generated {len(topics_data)} topics for Mathematics GCSE using predefined structure")
            return topics_data
            
        # For Further Mathematics A-Level, use predefined structure
        elif subject.lower() == "further mathematics" and exam_type.lower() in ["a-level", "as-level"]:
            # A-Level Further Mathematics topics based on AQA specification
            topic_structure = {
                "Compulsory content": [
                    "Complex numbers",
                    "Matrix algebra",
                    "Further algebra and functions",
                    "Further calculus",
                    "Further vectors",
                    "Polar coordinates",
                    "Hyperbolic functions",
                    "Differential equations"
                ],
                "Optional content": [
                    "Mechanics: Dimensional analysis",
                    "Mechanics: Momentum and collisions",
                    "Mechanics: Work, energy and power",
                    "Mechanics: Circular motion",
                    "Mechanics: Centre of mass and moments",
                    "Statistics: Discrete random variables",
                    "Statistics: Poisson distribution",
                    "Statistics: Continuous random variables",
                    "Statistics: Linear combinations of random variables",
                    "Statistics: Hypothesis testing and confidence intervals",
                    "Statistics: Chi-squared tests",
                    "Discrete: Logic and proof",
                    "Discrete: Graphs and networks",
                    "Discrete: Network flows",
                    "Discrete: Linear programming",
                    "Discrete: Binary operations and group theory",
                ]
            }
            
            for module, topics in topic_structure.items():
                for topic in topics:
                    topics_data.append(self._build_topic_data(
                        exam_board="AQA",
                        exam_type=exam_type,
                        subject=subject,
                        module=module,
                        topic=topic
                    ))
            
            logger.info(f"Generated {len(topics_data)} topics for Further Mathematics A-Level using predefined structure")
            return topics_data
            
        # For Environmental Science A-Level, use predefined structure
        elif subject.lower() == "environmental science" and exam_type.lower() in ["a-level", "as-level"]:
            # A-Level Environmental Science topics based on AQA specification
            topic_structure = {
                "The physical environment": [
                    "The atmosphere",
                    "The hydrosphere",
                    "Mineral resources",
                    "Biogeochemical cycles",
                    "Soils"
                ],
                "The living environment": [
                    "Biodiversity",
                    "Conservation of biodiversity",
                    "Life process in the biosphere",
                    "Dynamic equilibria",
                    "Succession",
                    "Agriculture, aquaculture and forestry"
                ],
                "Sustainability": [
                    "The concept of sustainability",
                    "Waste management",
                    "Energy resources",
                    "Pollution",
                    "Environmental monitoring",
                    "Environmental management"
                ],
                "Research methods and skills": [
                    "Scientific methodologies",
                    "Statistical analysis",
                    "Data interpretation",
                    "Case studies and research techniques",
                    "Ethics and environmental decision-making"
                ]
            }
            
            for module, topics in topic_structure.items():
                for topic in topics:
                    topics_data.append(self._build_topic_data(
                        exam_board="AQA",
                        exam_type=exam_type,
                        subject=subject,
                        module=module,
                        topic=topic
                    ))
            
            logger.info(f"Generated {len(topics_data)} topics for Environmental Science A-Level using predefined structure")
            return topics_data
        
        # Look for headings that might indicate topic sections
        topic_headings = soup.find_all(['h2', 'h3', 'h4', 'h5'])
        current_module = "General"
        current_topic = None
        
        for heading in topic_headings:
            heading_text = sanitize_text(heading.text)
            
            # Skip headings that are not related to content
            if not heading_text or any(ignore in heading_text.lower() for ignore in 
                                      ['assessment', 'introduction', 'appendix']):
                continue
                
            # Based on heading level, decide if it's a module or topic
            if heading.name in ['h2', 'h3']:
                # Likely a module/main section
                current_module = heading_text
                current_topic = None
            else:
                # Likely a topic
                if current_module:
                    current_topic = heading_text
                    topics_data.append(self._build_topic_data(
                        exam_board="AQA",
                        exam_type=exam_type,
                        subject=subject,
                        module=current_module,
                        topic=current_topic
                    ))
        
        # Look for lists that might contain topics
        for ul in soup.find_all('ul'):
            # Skip navigation and utility lists
            if 'nav' in ul.get('class', []) or ul.parent.name == 'nav':
                continue
                
            module_candidate = None
            for parent in ul.parents:
                if parent.name in ['h2', 'h3', 'h4', 'h5']:
                    module_candidate = sanitize_text(parent.text)
                    break
            
            current_module = module_candidate or current_module
            
            for li in ul.find_all('li', recursive=False):
                item_text = sanitize_text(li.text)
                if len(item_text) > 3 and len(item_text) < 200:
                    # This is likely a topic or subtopic
                    if item_text.startswith(('•', '○', '·')):
                        # Probably a bullet point list, treat as subtopic
                        if current_topic:
                            topics_data.append(self._build_topic_data(
                                exam_board="AQA",
                                exam_type=exam_type,
                                subject=subject,
                                module=current_module,
                                topic=current_topic,
                                sub_topic=item_text
                            ))
                    else:
                        # Treat as a topic
                        current_topic = item_text
                        topics_data.append(self._build_topic_data(
                            exam_board="AQA",
                            exam_type=exam_type,
                            subject=subject,
                            module=current_module,
                            topic=current_topic
                        ))
        
        # If we still haven't found topics, try strong tags and paragraphs
        if not topics_data:
            # Look for strong tags that might be topics
            for tag in soup.find_all(['strong', 'b']):
                topic_text = sanitize_text(tag.text)
                if len(topic_text) > 3 and len(topic_text) < 100:
                    topics_data.append(self._build_topic_data(
                        exam_board="AQA",
                        exam_type=exam_type,
                        subject=subject,
                        module=current_module,
                        topic=topic_text
                    ))
            
            # Look for paragraphs that might contain topic indicators
            for p in soup.find_all('p'):
                p_text = sanitize_text(p.text)
                if len(p_text) > 10 and len(p_text) < 150 and p_text[0].isupper():
                    if any(keyword in p_text.lower() for keyword in 
                          ['study', 'learn', 'understand', 'know', 'content']):
                        topics_data.append(self._build_topic_data(
                            exam_board="AQA",
                            exam_type=exam_type,
                            subject=subject,
                            module=current_module,
                            topic=p_text
                        ))
        
        logger.info(f"Extracted {len(topics_data)} topics from specification")
        return topics_data
    
    def _get_spec_url_from_subject_page(self, subject_url):
        """
        Get specification URL from a subject page.
        
        Args:
            subject_url (str): URL of the subject page
            
        Returns:
            str or None: URL of the specification
        """
        # First, determine if it's a GCSE or A-Level URL and find the matching subject
        subject_name = None
        is_gcse = False
        is_alevel = False
        
        # Check if it's a GCSE URL
        if "gcse" in subject_url.lower():
            is_gcse = True
            # Try to find the matching subject from the URL
            for subject in AQA_GCSE_SUBJECTS:
                subject_lower = subject.lower()
                # Create URL-friendly version of subject for comparison
                url_subject = subject_lower.replace(" ", "-").replace("(", "").replace(")", "").replace(":", "")
                if url_subject in subject_url.lower():
                    subject_name = subject
                    break
        
        # Check if it's an A-Level URL
        elif "a-level" in subject_url.lower() or "as-and-a-level" in subject_url.lower():
            is_alevel = True
            # Try to find the matching subject from the URL
            for subject in AQA_A_LEVEL_SUBJECTS:
                subject_lower = subject.lower()
                # Create URL-friendly version of subject for comparison
                url_subject = subject_lower.replace(" ", "-").replace("(", "").replace(")", "").replace(":", "")
                if url_subject in subject_url.lower():
                    subject_name = subject
                    break
        
        # If we identified the subject and level, check our direct specification URL dictionaries
        if subject_name:
            if is_gcse and subject_name in self.AQA_GCSE_SPEC_URLS:
                logger.info(f"Using direct specification URL for GCSE {subject_name}")
                return self.AQA_GCSE_SPEC_URLS[subject_name]
            elif is_alevel and subject_name in self.AQA_A_LEVEL_SPEC_URLS:
                logger.info(f"Using direct specification URL for A-Level {subject_name}")
                return self.AQA_A_LEVEL_SPEC_URLS[subject_name]
        
        # If we couldn't find a direct URL, fall back to the original method
        logger.info(f"No direct specification URL found, falling back to page scraping for {subject_url}")
        
        html = self._get_page(subject_url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Look for links containing "specification"
        spec_links = soup.find_all('a', href=True, string=re.compile('specification', re.IGNORECASE))
        if spec_links:
            spec_link = spec_links[0]
            return urljoin(self.base_url, spec_link['href'])
        
        # If not found, try looking for PDF links
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$'))
        for link in pdf_links:
            if 'specification' in link.text.lower() or 'specification' in link['href'].lower():
                return urljoin(self.base_url, link['href'])
        
        return None
    
    def _get_subject_code(self, subject_url):
        """
        Extract subject code from the subject URL or page.
        
        Args:
            subject_url (str): URL of the subject page
            
        Returns:
            str or None: Subject code
        """
        # Try to extract code from URL
        match = re.search(r'/subjects/([a-z0-9-]+)/', subject_url)
        if match:
            return match.group(1)
        
        # If not in URL, try to extract from page content
        html = self._get_page(subject_url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Look for specification code in text
        code_pattern = re.compile(r'\b([A-Z0-9]{4})\b')
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5']):
            match = code_pattern.search(element.text)
            if match:
                return match.group(1)
        
        return None
    
    def _find_past_papers(self, subject, exam_type, year_from=2021):
        """
        Find past papers for a subject.
        
        Args:
            subject (str): Subject name
            exam_type (str): Type of exam
            year_from (int): Year to start from
            
        Returns:
            list: List of paper data dictionaries
        """
        logger.info(f"Finding past papers for {subject} ({exam_type})")
        
        # Normalize inputs
        norm_subject = normalize_subject_name(subject)
        norm_exam_type = normalize_exam_type(exam_type)
        
        # Use both subject and qualification parameters for more precise filtering
        # Format the qualification parameter based on exam_type and subject
        if norm_exam_type.lower() == 'gcse':
            qualification = f"GCSE+{subject}"
        else:  # A-level or AS-level
            # For A-level Mathematics specifically, use a direct approach
            if "mathematics" in norm_subject.lower():
                qualification = "A-level+Mathematics"
            else:
                # For other A-level subjects, use just "A-level"
                qualification = "A-level"
            
        papers_url = f"https://www.aqa.org.uk/find-past-papers-and-mark-schemes?subject={subject}&qualification={qualification}"
        
        logger.info(f"Using URL with both subject and qualification: {papers_url}")
        
        # Initialize driver
        self._init_driver()
        
        try:
            logger.info(f"Navigating to past papers URL")
            self.driver.get(papers_url)
            
            # Wait for results to load - looking for PDF icons or results count
            try:
                WebDriverWait(self.driver, 60).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='results'], svg[class*='pdf']"))
                )
                html = self.driver.page_source
            except Exception as e:
                logger.warning(f"Timed out waiting for results to load: {e}")
                
                # Check if we have any content despite the timeout
                html = self.driver.page_source
                
                # If we have content but no results, log it but continue
                if len(html) > 1000:
                    logger.info("Page content received but no results found. Attempting to parse anyway.")
                else:
                    logger.error(f"Failed to get meaningful page content")
                    return []
        except Exception as e:
            logger.error(f"Error loading past papers page: {e}")
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        papers_data = []
        
        # Find results count to verify we have papers
        results_count_text = None
        results_count_el = soup.find(string=re.compile(r'Showing .* results'))
        if results_count_el:
            results_count_text = results_count_el.strip()
            match = re.search(r'(\d+,?\d*)', results_count_text)
            if match:
                count = int(match.group(1).replace(',', ''))
                logger.info(f"Found {count} results on the page")
        
        # Look for paper items - each paper is shown as a card with PDF icon
        # Based on the screenshot, each paper has:
        # 1. A PDF icon
        # 2. A title like "Mathematics - Question paper (Higher) : Paper 1 Non-calculator"
        # 3. Publication date and file size
        # 4. A PDF link
        
        paper_items = []
        
        # Try several selectors that might match the paper items
        selectors = [
            "div[class*='result']", 
            "div:has(svg[class*='pdf'])",
            "div:has(a[href*='.pdf'])"
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            if items:
                logger.info(f"Found {len(items)} paper items using selector: {selector}")
                paper_items = items
                break
        
        # If no items found with selectors, look for any divs containing PDF links
        if not paper_items:
            for pdf_link in soup.select("a[href$='.pdf']"):
                # Find parent div that contains the paper details
                parent = pdf_link.find_parent("div")
                if parent and parent not in paper_items:
                    paper_items.append(parent)
            
            if paper_items:
                logger.info(f"Found {len(paper_items)} paper items by finding PDF link parents")
        
        if not paper_items:
            # Last attempt - try to find any elements with file info
            file_info_elements = soup.find_all(string=re.compile(r'\d+\.\d+ (KB|MB)'))
            for element in file_info_elements:
                parent = element.find_parent("div")
                if parent and parent not in paper_items:
                    paper_items.append(parent)
            
            if paper_items:
                logger.info(f"Found {len(paper_items)} paper items by finding file size elements")
        
        if not paper_items:
            logger.warning(f"Could not find any paper items at {papers_url}")
            return []
            
        logger.info(f"Processing {len(paper_items)} paper items for {subject} ({exam_type})")
        
        # Extract papers
        for item in paper_items:
            try:
                # Extract title
                title_element = item.find(["h2", "h3", "h4", "strong", "div", "span"], string=re.compile(r'paper', re.IGNORECASE))
                if not title_element:
                    title_elements = item.select("div > *:not(a):not(svg):not(img):not(button)")
                    title_element = title_elements[0] if title_elements else None
                
                if not title_element:
                    continue
                    
                paper_title = sanitize_text(title_element.text)
                
                # Extract publication date and file info
                pub_date = None
                file_size = None
                
                date_element = item.find(string=re.compile(r'Published.*\d{4}'))
                if date_element:
                    date_text = date_element.strip()
                    date_match = re.search(r'(\d{2}\s+\w+\s+\d{4})', date_text)
                    if date_match:
                        pub_date = date_match.group(1)
                
                # Extract file size
                file_info = item.find(string=re.compile(r'\d+\.\d+ (KB|MB)'))
                if file_info:
                    file_size = file_info.strip()
                
                # Find PDF link
                pdf_link = item.select_one("a[href$='.pdf']")
                if not pdf_link:
                    # Try to find any link that might be the PDF
                    links = item.select("a")
                    for link in links:
                        href = link.get("href", "")
                        if ".pdf" in href or "download" in href:
                            pdf_link = link
                            break
                
                if not pdf_link:
                    logger.warning(f"No PDF link found for paper: {paper_title}")
                    continue
                
                # Extract data from paper title and date
                # Filter by subject and exam type first
                # Log paper title for debugging
                logger.debug(f"Checking paper title: {paper_title}")
                
                # Log the paper title for debugging
                logger.debug(f"Checking paper: {paper_title}")
                
                # For papers filtered by URL, we'll be very lenient with matching
                paper_matches_subject = True
                paper_matches_exam_type = True
                
                # Only reject papers that are obviously for a different subject
                wrong_subject_keywords = ['physics', 'chemistry', 'biology', 'history', 'geography', 'english', 
                                         'psychology', 'sociology', 'business', 'economics', 'french', 'spanish', 'german']
                
                # For A-level Mathematics, also accept papers with "pure", "mechanics", "statistics" in the title
                if norm_exam_type.lower() in ['a-level', 'as-level'] and "mathematics" in norm_subject.lower():
                    if (not any(kw in paper_title.lower() for kw in ['math', 'pure', 'mechanics', 'statistics', 'further']) and
                        any(kw in paper_title.lower() for kw in wrong_subject_keywords)):
                        paper_matches_subject = False
                        logger.debug(f"Rejecting paper: wrong subject for A-level Mathematics")
                # For other subjects, do basic subject checking
                elif subject.lower() not in paper_title.lower() and any(kw in paper_title.lower() for kw in wrong_subject_keywords):
                    paper_matches_subject = False
                    logger.debug(f"Rejecting paper: wrong subject")
                
                # For GCSE, be stricter with exam type checks
                if norm_exam_type.lower() == 'gcse' and not any(term in paper_title.lower() for term in 
                                                              ['gcse', 'foundation', 'higher']):
                    paper_matches_exam_type = False
                    logger.debug(f"Rejecting paper: not a GCSE paper")
                
                # Skip if this paper doesn't match our filter criteria
                if not (paper_matches_subject and paper_matches_exam_type):
                    continue
                
                logger.debug(f"Found matching paper: {paper_title}")
                
                # Extract year from publication date or title
                year = None
                if pub_date:
                    year_match = re.search(r'(20\d\d)', pub_date)
                    if year_match:
                        year = int(year_match.group(1))
                
                if not year:
                    year_match = re.search(r'(20\d\d)', paper_title)
                    if year_match:
                        year = int(year_match.group(1))
                
                # If still no year, use current year
                if not year:
                    year = datetime.now().year
                
                # Skip if it's older than year_from
                if year < year_from:
                    continue
                
                # Determine season based on date or title
                season = 'Summer'  # Default
                if pub_date and any(month in pub_date.lower() for month in ['jan', 'november', 'dec']):
                    season = 'Winter'
                elif any(term in paper_title.lower() for term in ['january', 'november', 'winter']):
                    season = 'Winter'
                
                # Extract paper number
                paper_num_match = re.search(r'paper\s*(\d+)', paper_title.lower())
                paper_number = int(paper_num_match.group(1)) if paper_num_match else 1
                
                # Determine document type
                doc_type = "Question Paper"  # Default
                if "mark scheme" in paper_title.lower():
                    doc_type = "Mark Scheme"
                elif "examiner" in paper_title.lower() or "report" in paper_title.lower():
                    doc_type = "Examiner Report"
                
                # Extract specification code if present
                spec_code_match = re.search(r'([A-Z0-9]{4})', paper_title)
                spec_code = spec_code_match.group(1) if spec_code_match else ""
                
                # If no spec code found, use normalized subject as identifier
                if not spec_code:
                    spec_code = norm_subject.replace(" ", "")[:4].upper()
                
                # Download the paper
                if pdf_link and pdf_link.has_attr('href'):
                    pdf_url = urljoin(self.base_url, pdf_link['href'])
                    
                    # Create a unique filename based on the information we have
                    filename = f"AQA_{norm_subject}_{year}_{season}_Paper{paper_number}"
                    
                    if doc_type == "Mark Scheme":
                        filename += "_MS"
                    elif doc_type == "Examiner Report":
                        filename += "_ER"
                    
                    filename += ".pdf"
                    
                    # Create subdirectory path
                    subdir = os.path.join(
                        norm_exam_type,
                        norm_subject.replace(" ", "_"),
                        str(year),
                        season
                    )
                    
                    # Determine document type for directory structure
                    document_type_dir = doc_type.lower().replace(" ", "_")
                    
                    # Download the paper
                    logger.info(f"Downloading {doc_type} from {pdf_url}")
                    file_path = self._download_document(
                        pdf_url,
                        filename,
                        subdir,
                        document_type_dir
                    )
                    
                    if file_path:
                        # Create paper data dictionary
                        papers_data.append(self._build_paper_data(
                            exam_board="AQA",
                            exam_type=exam_type,
                            subject=subject,
                            year=year,
                            season=season,
                            title=paper_title,
                            paper_number=paper_number,
                            document_type=doc_type,
                            specification_code=spec_code,
                            file_path=file_path
                        ))
                        
                        logger.info(f"Successfully downloaded: {paper_title}")
                    else:
                        logger.warning(f"Failed to download paper: {paper_title}")
                
            except Exception as e:
                logger.error(f"Error processing paper item: {e}", exc_info=True)
        
        logger.info(f"Found {len(papers_data)} papers for {subject} ({exam_type})")
        return papers_data
    
    def scrape_topics(self, subject=None, exam_type=None):
        """
        Scrape topic lists from the AQA website.
        
        Args:
            subject (str, optional): Subject to scrape topics for
            exam_type (str, optional): Exam type to scrape topics for
            
        Returns:
            list: List of topic data dictionaries
        """
        logger.info(f"Scraping AQA topics" + 
                   (f" for {subject}" if subject else "") + 
                   (f" ({exam_type})" if exam_type else ""))
        
        # Get subject URLs
        subject_urls = self._get_subject_urls(exam_type)
        
        # If a specific subject is requested, filter the URLs
        if subject:
            norm_subject = normalize_subject_name(subject)
            filtered_urls = {}
            for subj_name, subj_url in subject_urls.items():
                if norm_subject in normalize_subject_name(subj_name):
                    filtered_urls[subj_name] = subj_url
            subject_urls = filtered_urls
        
        # Get topics for each subject
        all_topics = []
        
        for subj_name, subj_url in subject_urls.items():
            try:
                # Get the specification URL
                spec_url = self._get_spec_url_from_subject_page(subj_url)
                if not spec_url:
                    logger.warning(f"Could not find specification URL for {subj_name}")
                    continue
                
                # Extract topics from specification
                topics = self._extract_specification_topics(
                    spec_url, 
                    exam_type or "GCSE" if "gcse" in subj_url else "A-Level",
                    subj_name
                )
                
                all_topics.extend(topics)
                
                # Save the raw topics data
                if topics:
                    subdir = normalize_exam_type(exam_type) if exam_type else "all"
                    self._save_raw_data(
                        topics,
                        f"{sanitize_text(subj_name)}_topics.json",
                        subdir
                    )
            
            except Exception as e:
                logger.error(f"Error scraping topics for {subj_name}: {e}", exc_info=True)
        
        logger.info(f"Scraped {len(all_topics)} topics from AQA")
        return all_topics
    
    def scrape_papers(self, subject=None, exam_type=None, year_from=2021):
        """
        Scrape exam papers from the AQA website.
        
        Args:
            subject (str, optional): Subject to scrape papers for
            exam_type (str, optional): Exam type to scrape papers for
            year_from (int): Year to start scraping papers from
            
        Returns:
            list: List of paper data dictionaries
        """
        logger.info(f"Scraping AQA papers" + 
                   (f" for {subject}" if subject else "") + 
                   (f" ({exam_type})" if exam_type else "") +
                   f" from {year_from}")
        
        # If no specific subject/exam type is provided, get all subjects
        if not subject or not exam_type:
            # Get subject URLs
            subject_urls = self._get_subject_urls(exam_type)
            
            # Filter by subject if provided
            if subject:
                norm_subject = normalize_subject_name(subject)
                filtered_urls = {}
                for subj_name, subj_url in subject_urls.items():
                    if norm_subject in normalize_subject_name(subj_name):
                        filtered_urls[subj_name] = subj_url
                subject_urls = filtered_urls
            
            # Determine exam type for each subject if not specified
            if not exam_type:
                all_papers = []
                for subj_name, subj_url in subject_urls.items():
                    # Determine exam type from URL
                    current_exam_type = "GCSE" if "gcse" in subj_url else "A-Level"
                    papers = self._find_past_papers(subj_name, current_exam_type, year_from)
                    all_papers.extend(papers)
                
                # Save the raw papers data
                if all_papers:
                    self._save_raw_data(
                        all_papers,
                        f"all_papers_{year_from}_onwards.json",
                        "all"
                    )
                
                return all_papers
        
        # If both subject and exam type are provided, just get papers for that combination
        papers = self._find_past_papers(subject, exam_type, year_from)
        
        # Save the raw papers data
        if papers:
            subdir = normalize_exam_type(exam_type)
            self._save_raw_data(
                papers,
                f"{normalize_subject_name(subject)}_papers_{year_from}_onwards.json",
                subdir
            )
        
        return papers
