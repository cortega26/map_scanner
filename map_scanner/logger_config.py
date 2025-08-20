"""
Logging configuration for the Map Scanner application.

Provides centralized logging setup following best practices.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from .config import LoggingConfig


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Set up logging configuration for the application.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_file: Optional log file path. If None, uses default from config
        console_output: Whether to output logs to console

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('map_scanner')
    logger.setLevel(level)

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(LoggingConfig.LOG_FORMAT)

    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Add file handler
    if log_file is None:
        log_file = LoggingConfig.LOG_FILENAME

    try:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(
            log_file,
            encoding=LoggingConfig.LOG_ENCODING
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    except (OSError, PermissionError) as e:
        # If file logging fails, just log to console
        logger.warning(f"Could not set up file logging: {e}")

    return logger


def get_logger(name: str = 'map_scanner') -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
