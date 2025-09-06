"""Common utilities for the trading bot system"""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

def setup_logging(service_name: str, log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration for a service
    
    Args:
        service_name (str): Name of the service
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    from .env_loader import get_log_path
    
    # Create logger
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    log_file = get_log_path(f"{service_name}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def save_json_data(data: Dict[Any, Any], filepath: str) -> bool:
    """Save data to JSON file
    
    Args:
        data (dict): Data to save
        filepath (str): Path to save file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        logging.error(f"Error saving JSON data to {filepath}: {e}")
        return False

def load_json_data(filepath: str) -> Optional[Dict[Any, Any]]:
    """Load data from JSON file
    
    Args:
        filepath (str): Path to JSON file
        
    Returns:
        dict: Loaded data or None if error
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON data from {filepath}: {e}")
        return None

def format_timestamp(dt: datetime = None) -> str:
    """Format timestamp for consistent display
    
    Args:
        dt (datetime, optional): Datetime object, defaults to now
        
    Returns:
        str: Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def validate_env_vars(required_vars: list, service_name: str) -> bool:
    """Validate that required environment variables are set
    
    Args:
        required_vars (list): List of required environment variable names
        service_name (str): Name of the service for logging
        
    Returns:
        bool: True if all variables are set, False otherwise
    """
    import os
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logging.error(f"{service_name}: Missing required environment variables: {missing_vars}")
        return False
    
    return True