"""
Comprehensive subject lists for UK exam boards.

This module provides standardized lists of subjects for GCSE, A-Level, and other examination types.
These lists are used across the scraper modules for consistent subject identification and normalization.
"""

# GCSE Subjects
GCSE_SUBJECTS = [
    "Mathematics",
    "English Language",
    "English Literature",
    "Combined Science: Trilogy",
    "Biology",
    "Chemistry",
    "Physics",
    "Environmental Science",
    "Religious Studies",
    "History",
    "Ancient History",
    "Geography",
    "French",
    "Spanish",
    "German",
    "Arabic",
    "Chinese",
    "Italian",
    "Japanese",
    "Polish",
    "Russian",
    "Urdu",
    "Modern Greek",
    "Latin",
    "Classical Greek",
    "Classical Civilization",
    "Art and Design",
    "Design and Technology",
    "Textiles",
    "Food Preparation and Nutrition",
    "Hospitality and Catering",
    "Music",
    "Drama",
    "Dance",
    "Computer Science",
    "Information and Communications Technology (ICT)",
    "Business Studies",
    "Economics",
    "Sociology",
    "Psychology",
    "Media Studies",
    "Film Studies",
    "Physical Education",
    "Citizenship",
    "Health and Social Care",
    "Engineering",
    "Electronics",
    "Astronomy",
    "Geology",
    "Statistics"
]

# A-Level Subjects
A_LEVEL_SUBJECTS = [
    "Mathematics",
    "Further Mathematics",
    "Statistics",
    "English Language",
    "English Literature",
    "English Language and Literature",
    "Biology",
    "Chemistry",
    "Physics",
    "Environmental Science",
    "History",
    "Ancient History",
    "Geography",
    "Religious Studies",
    "Philosophy",
    "French",
    "Spanish",
    "German",
    "Arabic",
    "Chinese",
    "Italian",
    "Japanese",
    "Russian",
    "Urdu",
    "Latin",
    "Classical Greek",
    "Classical Civilization",
    "Psychology",
    "Sociology",
    "Economics",
    "Business Studies",
    "Accounting",
    "Government and Politics",
    "Law",
    "Computer Science",
    "Information Technology/ICT",
    "Design and Technology",
    "Textiles",
    "Art and Design",
    "History of Art",
    "Drama and Theatre",
    "Theatre Studies",
    "Media Studies",
    "Film Studies",
    "Music",
    "Music Technology",
    "Physical Education",
    "Dance",
    "Health and Social Care",
    "Electronics",
    "Geology",
    "Archaeology",
    "Criminology"
]

# Subject name variations for normalization
SUBJECT_SYNONYMS = {
    # Mathematics
    "math": "Mathematics",
    "maths": "Mathematics",
    "pure mathematics": "Mathematics",
    "further math": "Further Mathematics",
    "further maths": "Further Mathematics",
    "stats": "Statistics",
    
    # English
    "english lang": "English Language",
    "english lit": "English Literature",
    "lang and lit": "English Language and Literature",
    
    # Sciences
    "double science": "Combined Science: Trilogy",
    "combined science": "Combined Science: Trilogy",
    "trilogy science": "Combined Science: Trilogy",
    "biology, chemistry and physics": "Triple Science",
    "environmental studies": "Environmental Science",
    
    # Humanities
    "ancient history": "Ancient History",
    "classical civilisation": "Classical Civilization",
    "religious education": "Religious Studies",
    "re": "Religious Studies",
    "politics": "Government and Politics",
    
    # Languages
    "mandarin": "Chinese",
    "mandarin chinese": "Chinese",
    "greek": "Modern Greek",
    "classical greek": "Classical Greek",
    
    # Arts
    "art": "Art and Design",
    "fine art": "Art and Design",
    "graphic design": "Art and Design",
    "textiles design": "Textiles",
    "drama": "Drama and Theatre",
    "theatre": "Theatre Studies",
    
    # Technology
    "dt": "Design and Technology",
    "food tech": "Food Preparation and Nutrition",
    "food technology": "Food Preparation and Nutrition",
    "hospitality": "Hospitality and Catering",
    "computing": "Computer Science",
    "ict": "Information and Communications Technology (ICT)",
    "it": "Information Technology/ICT",
    
    # Social Sciences & Business
    "psych": "Psychology",
    "business": "Business Studies",
    "business studies": "Business Studies",
    "business and economics": "Business Studies",
    "government & politics": "Government and Politics",
    
    # Physical Education
    "pe": "Physical Education",
    "sports science": "Physical Education",
    "health & social care": "Health and Social Care"
}

def normalize_subject(subject_name):
    """
    Normalize a subject name by checking against known variations.
    
    Args:
        subject_name (str): The subject name to normalize
        
    Returns:
        str: The normalized subject name
    """
    if not subject_name:
        return ""
    
    # Convert to lowercase for matching
    subject_lower = subject_name.lower()
    
    # Check direct matches in SUBJECT_SYNONYMS
    if subject_lower in SUBJECT_SYNONYMS:
        return SUBJECT_SYNONYMS[subject_lower]
    
    # Check for partial matches
    for variant, canonical in SUBJECT_SYNONYMS.items():
        if subject_lower == variant or subject_lower.startswith(variant + " "):
            return canonical
    
    # Check if it's in our standard lists (but with different casing)
    for subject in GCSE_SUBJECTS + A_LEVEL_SUBJECTS:
        if subject.lower() == subject_lower:
            return subject
    
    # If no matches found, return the original with proper capitalization
    words = subject_name.split()
    # Capitalize all words except for common articles and prepositions
    small_words = {'and', 'of', 'the', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}
    capitalized = []
    for i, word in enumerate(words):
        if i == 0 or word.lower() not in small_words:
            capitalized.append(word.capitalize())
        else:
            capitalized.append(word.lower())
            
    return " ".join(capitalized)

def is_valid_subject(subject_name, exam_type=None):
    """
    Check if a subject name is valid for the given exam type.
    
    Args:
        subject_name (str): The subject name to check
        exam_type (str, optional): Exam type (e.g., 'gcse', 'a-level'). 
                                  If None, checks against all subjects.
        
    Returns:
        bool: True if the subject is valid, False otherwise
    """
    if not subject_name:
        return False
        
    # Normalize the subject name
    normalized = normalize_subject(subject_name)
    
    # Check against the appropriate subject list based on exam type
    if exam_type:
        exam_type = exam_type.lower()
        if exam_type in ['gcse', 'igcse']:
            return normalized in GCSE_SUBJECTS
        elif exam_type in ['a-level', 'alevel', 'gce', 'a level', 'a']:
            return normalized in A_LEVEL_SUBJECTS
    
    # If no exam type specified, check against all subjects
    return (normalized in GCSE_SUBJECTS or 
            normalized in A_LEVEL_SUBJECTS)

def get_subjects_for_exam_type(exam_type):
    """
    Get a list of valid subjects for the given exam type.
    
    Args:
        exam_type (str): Exam type (e.g., 'gcse', 'a-level')
        
    Returns:
        list: List of subject names valid for the given exam type
    """
    if not exam_type:
        return []
        
    exam_type = exam_type.lower()
    
    if exam_type in ['gcse', 'igcse']:
        return GCSE_SUBJECTS
    elif exam_type in ['a-level', 'alevel', 'gce', 'a level', 'a']:
        return A_LEVEL_SUBJECTS
    
    # Return empty list for unknown exam type
    return []
