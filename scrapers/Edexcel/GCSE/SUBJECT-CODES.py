"""
STANDARDIZED GCSE EDEXCEL SUBJECT CODES
========================================

Use these codes in ALL scrapers to prevent duplicates!
"""

GCSE_SUBJECTS = {
    'Arabic': 'GCSE-Arabic',
    'Art and Design': 'GCSE-Art',
    'Astronomy': 'GCSE-Astronomy',
    'Biblical Hebrew': 'GCSE-BiblicalHebrew',
    'Business': 'GCSE-Business',
    'Chinese': 'GCSE-Chinese',
    'Citizenship Studies': 'GCSE-Citizenship',
    'Computer Science': 'GCSE-ComputerScience',
    'Design and Technology': 'GCSE-DesignTech',  # NOT GCSE-DT!
    'Drama': 'GCSE-Drama',
    'English Language': 'GCSE-EnglishLang',
    'English Literature': 'GCSE-EnglishLit',
    'French': 'GCSE-French',
    'Geography A': 'GCSE-GeoA',
    'Geography B': 'GCSE-GeoB',
    'German': 'GCSE-German',
    'Greek': 'GCSE-Greek',
    'Gujarati': 'GCSE-Gujarati',
    'History': 'GCSE-History',
    'Italian': 'GCSE-Italian',
    'Japanese': 'GCSE-Japanese',
    'Mathematics': 'GCSE-Maths',
    'Music': 'GCSE-Music',
    'Persian': 'GCSE-Persian',
    'Physical Education': 'GCSE-PE',
    'Portuguese': 'GCSE-Portuguese',
    'Psychology': 'GCSE-Psychology',
    'Religious Studies A': 'GCSE-RSA',
    'Religious Studies B': 'GCSE-RSB',
    'Russian': 'GCSE-Russian',
    'Science (Combined Science)': 'GCSE-Science',
    'Spanish': 'GCSE-Spanish',
    'Statistics': 'GCSE-Statistics',
    'Turkish': 'GCSE-Turkish',
    'Urdu': 'GCSE-Urdu'
}


def get_subject_code(subject_name):
    """Get standardized code for a subject name."""
    return GCSE_SUBJECTS.get(subject_name, f"GCSE-{subject_name.replace(' ', '')}")

