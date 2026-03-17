# app/utils/logger.py

import logging
import sys
from pathlib import Path

def setup_logging():
    """Simple logging setup"""
    
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console.setFormatter(console_format)
    logger.addHandler(console)
    
    # File handler
    file_handler = logging.FileHandler('logs/application.log', encoding='utf8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    return logging.getLogger(__name__)