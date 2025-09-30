"""
Exam Paper Processor module for UK Exam Board Topic List Scraper.

This module processes raw exam paper data scraped from exam board websites and
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


class ExamPaperProcessor:
    """
    Processor for exam paper data.
    
    This class handles the processing and standardization of exam paper data
    scraped from exam board websites.
    """
    
    def __init__(self, output_dir="data/processed/papers"):
        """
        Initialize the exam paper processor.
        
        Args:
            output_dir (str): Directory to save processed exam paper data
        """
        self.output_dir = output_dir
        ensure_directory(output_dir)
    
    def process(self, papers_data, exam_board):
        """
        Process raw exam paper data.
        
        Args:
            papers_data (list): List of paper data dictionaries
            exam_board (str): Name of the exam board
            
        Returns:
            list: Processed paper data ready for upload
        """
        if not papers_data:
            logger.warning(f"No paper data to process for {exam_board}")
            return []
        
        logger.info(f"Processing {len(papers_data)} papers for {exam_board}")
        
        # Standardize and clean data
        standardized_data = self._standardize_papers(papers_data, exam_board)
        
        # Group related papers (question papers, mark schemes, examiner reports)
        organized_data = self._organize_papers(standardized_data)
        
        # Save processed data
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = os.path.join(
            self.output_dir, 
            f"{exam_board.lower()}_processed_papers_{timestamp}.json"
        )
        save_json(organized_data, output_file)
        
        logger.info(f"Processed {len(organized_data)} papers for {exam_board}")
        return organized_data
    
    def _standardize_papers(self, papers_data, exam_board):
        """
        Standardize paper data format.
        
        Args:
            papers_data (list): List of paper data dictionaries
            exam_board (str): Name of the exam board
            
        Returns:
            list: Standardized paper data
        """
        standardized = []
        
        for paper in papers_data:
            # Skip incomplete entries
            if not paper.get("Subject") or not paper.get("Paper"):
                continue
            
            # Ensure exam board is correct
            paper["Exam Board"] = exam_board
            
            # Normalize fields
            if paper.get("Exam Type"):
                paper["Exam Type"] = paper["Exam Type"].upper()
            
            if paper.get("Document Type"):
                # Standardize document type names
                doc_type = paper["Document Type"].strip().lower()
                if "question" in doc_type or "paper" in doc_type:
                    paper["Document Type"] = "Question Paper"
                elif "mark" in doc_type or "scheme" in doc_type or "ms" in doc_type:
                    paper["Document Type"] = "Mark Scheme"
                elif "examiner" in doc_type or "report" in doc_type or "er" in doc_type:
                    paper["Document Type"] = "Examiner Report"
                else:
                    paper["Document Type"] = "Other"
            
            # Ensure Season is standardized
            if paper.get("Season"):
                season = paper["Season"].strip().lower()
                if "summer" in season or "may" in season or "june" in season:
                    paper["Season"] = "Summer"
                elif "winter" in season or "nov" in season or "jan" in season:
                    paper["Season"] = "Winter"
                else:
                    paper["Season"] = "Other"
            
            # Ensure Year is an integer
            if paper.get("Year") and not isinstance(paper["Year"], int):
                try:
                    paper["Year"] = int(paper["Year"])
                except (ValueError, TypeError):
                    # Try to extract year from string
                    year_match = re.search(r'(20\d\d)', str(paper["Year"]))
                    if year_match:
                        paper["Year"] = int(year_match.group(1))
                    else:
                        # Keep as is if we can't convert
                        pass
            
            # Ensure Paper Number is an integer
            if paper.get("Paper Number") and not isinstance(paper["Paper Number"], int):
                try:
                    paper["Paper Number"] = int(paper["Paper Number"])
                except (ValueError, TypeError):
                    # Try to extract paper number from string
                    num_match = re.search(r'(\d+)', str(paper["Paper Number"]))
                    if num_match:
                        paper["Paper Number"] = int(num_match.group(1))
                    else:
                        # Default to 1 if we can't convert
                        paper["Paper Number"] = 1
            
            # Clean text fields
            for field in ["Subject", "Title", "Specification Code"]:
                if paper.get(field):
                    paper[field] = sanitize_text(paper[field])
            
            # Add to standardized list
            standardized.append(paper)
        
        return standardized
    
    def _organize_papers(self, papers_data):
        """
        Organize papers to group related documents together.
        
        Args:
            papers_data (list): List of standardized paper data dictionaries
            
        Returns:
            list: Organized paper data
        """
        # We're not changing the structure, just ensuring uniqueness and completeness
        organized = []
        seen_papers = set()
        
        for paper in papers_data:
            # Create a unique key based on metadata
            key_parts = [
                paper.get("Exam Board", "Unknown"),
                paper.get("Exam Type", "Unknown"),
                paper.get("Subject", "Unknown"),
                str(paper.get("Year", "")),
                paper.get("Season", "Unknown"),
                str(paper.get("Paper Number", "")),
                paper.get("Document Type", "Unknown")
            ]
            
            paper_key = "|".join(key_parts)
            
            if paper_key not in seen_papers:
                organized.append(paper)
                seen_papers.add(paper_key)
            else:
                logger.debug(f"Skipping duplicate paper: {paper_key}")
        
        return organized
    
    def merge_papers(self, papers_list):
        """
        Merge multiple paper lists into a single consistent list.
        
        Args:
            papers_list (list): List of paper data lists to merge
            
        Returns:
            list: Merged paper data
        """
        if not papers_list:
            return []
        
        # Flatten the list of lists
        all_papers = []
        for papers in papers_list:
            all_papers.extend(papers)
        
        # Process the combined data for uniqueness
        organized = []
        seen_papers = set()
        
        for paper in all_papers:
            # Create a unique key based on metadata
            key_parts = [
                paper.get("Exam Board", "Unknown"),
                paper.get("Exam Type", "Unknown"),
                paper.get("Subject", "Unknown"),
                str(paper.get("Year", "")),
                paper.get("Season", "Unknown"),
                str(paper.get("Paper Number", "")),
                paper.get("Document Type", "Unknown")
            ]
            
            paper_key = "|".join(key_parts)
            
            if paper_key not in seen_papers:
                organized.append(paper)
                seen_papers.add(paper_key)
        
        # Save the merged data
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = os.path.join(
            self.output_dir, 
            f"merged_papers_{timestamp}.json"
        )
        save_json(organized, output_file)
        
        logger.info(f"Merged {len(all_papers)} papers into {len(organized)} unique entries")
        return organized
