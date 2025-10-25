"""
Timezone utilities for logging with Singapore timezone
"""
import logging


def setup_singapore_logging(logger_name, level=logging.INFO, log_format=None, datefmt=None, console=True):
    """
    Setup logger with Singapore timezone formatting

    Args:
        logger_name: Name of the logger
        level: Logging level (default: INFO)
        log_format: Log message format
        datefmt: Date format string
        console: Whether to add console handler

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Set default format if not provided
    if not log_format:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    formatter = logging.Formatter(log_format, datefmt=datefmt)

    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
