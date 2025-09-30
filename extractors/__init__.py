"""Extractors package for AI-powered specification extraction."""

from .specification_extractor import SpecificationExtractor
from .topic_extractor import (
    extract_topics_from_pdf,
    extract_topics_from_html,
    extract_topics_from_content
)

__all__ = [
    'SpecificationExtractor',
    'extract_topics_from_pdf',
    'extract_topics_from_html',
    'extract_topics_from_content'
]
