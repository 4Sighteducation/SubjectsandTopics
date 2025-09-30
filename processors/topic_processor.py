"""
Topic Processor module for UK Exam Board Topic List Scraper.

This module processes raw topic data scraped from exam board websites and
standardizes it for uploading to Knack.
"""

import os
import json
import re
from datetime import datetime
from collections import defaultdict

from utils.logger import get_logger
from utils.helpers import (
    sanitize_text, normalize_subject_name, normalize_exam_type,
    save_json, ensure_directory
)

logger = get_logger()


class TopicProcessor:
    """
    Processor for topic list data.
    
    This class handles the processing and standardization of topic data
    scraped from exam board websites.
    """
    
    def __init__(self, output_dir="data/processed/topics"):
        """
        Initialize the topic processor.
        
        Args:
            output_dir (str): Directory to save processed topic data
        """
        self.output_dir = output_dir
        ensure_directory(output_dir)
    
    def process(self, topics_data, exam_board):
        """
        Process raw topic data.
        
        Args:
            topics_data (list): List of topic data dictionaries
            exam_board (str): Name of the exam board
            
        Returns:
            list: Processed topic data ready for upload
        """
        if not topics_data:
            logger.warning(f"No topic data to process for {exam_board}")
            return []
        
        logger.info(f"Processing {len(topics_data)} topics for {exam_board}")
        
        # Standardize and clean data
        standardized_data = self._standardize_topics(topics_data, exam_board)
        
        # Organize topics into hierarchical structure
        organized_data = self._organize_topics(standardized_data)
        
        # Save processed data
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = os.path.join(
            self.output_dir, 
            f"{exam_board.lower()}_processed_topics_{timestamp}.json"
        )
        save_json(organized_data, output_file)
        
        logger.info(f"Processed {len(organized_data)} topics for {exam_board}")
        return organized_data
    
    def _standardize_topics(self, topics_data, exam_board):
        """
        Standardize topic data format.
        
        Args:
            topics_data (list): List of topic data dictionaries
            exam_board (str): Name of the exam board
            
        Returns:
            list: Standardized topic data
        """
        standardized = []
        
        for topic in topics_data:
            # Skip incomplete entries
            if not topic.get("Subject") or not topic.get("Topic"):
                continue
            
            # Ensure exam board is correct
            topic["Exam Board"] = exam_board
            
            # Normalize exam type
            if topic.get("Exam Type"):
                topic["Exam Type"] = topic["Exam Type"].upper()
            
            # Ensure all fields exist
            if not topic.get("Module"):
                topic["Module"] = "General"
            
            # Clean text fields
            for field in ["Subject", "Module", "Topic"]:
                if topic.get(field):
                    topic[field] = sanitize_text(topic[field])
            
            # Special handling for Sub Topic field which can be a string or a list
            if topic.get("Sub Topic"):
                if isinstance(topic["Sub Topic"], list):
                    # If it's a list, sanitize each item in the list
                    topic["Sub Topic"] = [sanitize_text(item) for item in topic["Sub Topic"] if item]
                else:
                    # If it's a string, sanitize it normally
                    topic["Sub Topic"] = sanitize_text(topic["Sub Topic"])
            
            # Add to standardized list
            standardized.append(topic)
        
        return standardized
    
    def _organize_topics(self, topics_data):
        """
        Organize topics into a proper hierarchical structure.
        
        Args:
            topics_data (list): List of standardized topic data dictionaries
            
        Returns:
            list: Organized topic data
        """
        # Group by exam type, subject, module
        organized = []
        seen_topics = set()
        
        # Create a hierarchy: exam_type -> subject -> module -> topic -> sub_topic
        hierarchy = defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(
                    lambda: defaultdict(list)
                )
            )
        )
        
        # Fill the hierarchy
        for topic in topics_data:
            exam_type = topic.get("Exam Type", "Unknown")
            subject = topic.get("Subject", "Unknown")
            module = topic.get("Module", "General")
            topic_name = topic.get("Topic", "")
            sub_topic = topic.get("Sub Topic", "")
            
            # Add to hierarchy
            if sub_topic:
                if isinstance(sub_topic, list):
                    # Handle list of subtopics (from AI extraction)
                    for st in sub_topic:
                        if st:  # Only add non-empty strings
                            topic_key = f"{exam_type}|{subject}|{module}|{topic_name}|{st}"
                            if topic_key not in seen_topics:
                                hierarchy[exam_type][subject][module][topic_name].append(st)
                                seen_topics.add(topic_key)
                else:
                    # Handle single string subtopic
                    topic_key = f"{exam_type}|{subject}|{module}|{topic_name}|{sub_topic}"
                    if topic_key not in seen_topics:
                        hierarchy[exam_type][subject][module][topic_name].append(sub_topic)
                        seen_topics.add(topic_key)
            else:
                # If no sub-topic, add the topic if it's not there already
                topic_key = f"{exam_type}|{subject}|{module}|{topic_name}"
                if topic_key not in seen_topics and topic_name:
                    hierarchy[exam_type][subject][module][topic_name] = []
                    seen_topics.add(topic_key)
        
        # Convert hierarchy to list of topic objects
        for exam_type, subjects in hierarchy.items():
            for subject, modules in subjects.items():
                for module, topics in modules.items():
                    for topic_name, sub_topics in topics.items():
                        if sub_topics:
                            # Add sub-topics
                            for sub_topic in sub_topics:
                                organized.append({
                                    "Exam Board": topic.get("Exam Board"),
                                    "Exam Type": exam_type,
                                    "Subject": subject,
                                    "Module": module,
                                    "Topic": topic_name,
                                    "Sub Topic": sub_topic
                                })
                        else:
                            # Just add the topic if no sub-topics
                            organized.append({
                                "Exam Board": topic.get("Exam Board"),
                                "Exam Type": exam_type,
                                "Subject": subject,
                                "Module": module,
                                "Topic": topic_name
                            })
        
        return organized
    
    def merge_topics(self, topics_list):
        """
        Merge multiple topic lists into a single consistent list.
        
        Args:
            topics_list (list): List of topic data lists to merge
            
        Returns:
            list: Merged topic data
        """
        if not topics_list:
            return []
        
        # Flatten the list of lists
        all_topics = []
        for topics in topics_list:
            all_topics.extend(topics)
        
        # Process the combined data
        # Group by exam type, subject, module
        organized = []
        seen_topics = set()
        
        # Create a hierarchy: exam_board -> exam_type -> subject -> module -> topic -> sub_topic
        hierarchy = defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(
                    lambda: defaultdict(
                        lambda: defaultdict(list)
                    )
                )
            )
        )
        
        # Fill the hierarchy
        for topic in all_topics:
            exam_board = topic.get("Exam Board", "Unknown")
            exam_type = topic.get("Exam Type", "Unknown")
            subject = topic.get("Subject", "Unknown")
            module = topic.get("Module", "General")
            topic_name = topic.get("Topic", "")
            sub_topic = topic.get("Sub Topic", "")
            
            # Add to hierarchy
            if sub_topic:
                if isinstance(sub_topic, list):
                    # Handle list of subtopics (from AI extraction)
                    for st in sub_topic:
                        if st:  # Only add non-empty strings
                            topic_key = f"{exam_board}|{exam_type}|{subject}|{module}|{topic_name}|{st}"
                            if topic_key not in seen_topics:
                                hierarchy[exam_board][exam_type][subject][module][topic_name].append(st)
                                seen_topics.add(topic_key)
                else:
                    # Handle single string subtopic
                    topic_key = f"{exam_board}|{exam_type}|{subject}|{module}|{topic_name}|{sub_topic}"
                    if topic_key not in seen_topics:
                        hierarchy[exam_board][exam_type][subject][module][topic_name].append(sub_topic)
                        seen_topics.add(topic_key)
            else:
                # If no sub-topic, add the topic if it's not there already
                topic_key = f"{exam_board}|{exam_type}|{subject}|{module}|{topic_name}"
                if topic_key not in seen_topics and topic_name:
                    hierarchy[exam_board][exam_type][subject][module][topic_name] = []
                    seen_topics.add(topic_key)
        
        # Convert hierarchy to list of topic objects
        for exam_board, exam_types in hierarchy.items():
            for exam_type, subjects in exam_types.items():
                for subject, modules in subjects.items():
                    for module, topics in modules.items():
                        for topic_name, sub_topics in topics.items():
                            if sub_topics:
                                # Add sub-topics
                                for sub_topic in sub_topics:
                                    organized.append({
                                        "Exam Board": exam_board,
                                        "Exam Type": exam_type,
                                        "Subject": subject,
                                        "Module": module,
                                        "Topic": topic_name,
                                        "Sub Topic": sub_topic
                                    })
                            else:
                                # Just add the topic if no sub-topics
                                organized.append({
                                    "Exam Board": exam_board,
                                    "Exam Type": exam_type,
                                    "Subject": subject,
                                    "Module": module,
                                    "Topic": topic_name
                                })
        
        # Save the merged data
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = os.path.join(
            self.output_dir, 
            f"merged_topics_{timestamp}.json"
        )
        save_json(organized, output_file)
        
        logger.info(f"Merged {len(all_topics)} topics into {len(organized)} unique entries")
        return organized
