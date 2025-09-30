"""
Logging configuration for the UK Exam Board Topic List Scraper.
"""

import os
import logging
from datetime import datetime


def setup_logger(log_level='INFO', log_file=None):
    """
    Configure and return a logger with specified log level and optional file output.
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (str, optional): Path to log file. If None, logs to console only.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Ensure log directory exists if a log file is specified
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Set up basic logger
    logger = logging.getLogger('exam_scraper')
    
    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Handle both string and integer log levels
    if isinstance(log_level, str):
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {log_level}')
    else:
        # If it's already a numeric level, use it directly
        numeric_level = log_level
    
    logger.setLevel(numeric_level)
    
    # Create console handler with formatter
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    
    # Format: [TIMESTAMP] [LEVEL] message
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if log_file is provided
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger():
    """
    Get the existing logger or create a new one with default settings.
    
    Returns:
        logging.Logger: The logger instance
    """
    logger = logging.getLogger('exam_scraper')
    
    # If the logger doesn't have any handlers, set up a default one
    if not logger.hasHandlers():
        return setup_logger()
    
    return logger
