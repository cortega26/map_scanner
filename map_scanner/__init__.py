"""
Map Scanner Package - Professional Map Scanning Application

A modular, professional-grade map scanner for game automation with
advanced OCR capabilities and robust error handling.

This package follows SOLID principles and clean architecture patterns
to provide a maintainable and extensible solution.
"""

from .map_scanner import MapScanner
from .exceptions import (
    MapScannerError,
    SafetyExit,
    WindowError,
    OCRError,
    CaptureError,
    MovementError,
    CalibrationError
)
from .config import (
    WindowConfig,
    CaptureConfig,
    OCRConfig,
    ScanConfig,
    LoggingConfig,
    PyAutoGUIConfig
)

__version__ = "3.0.0"
__author__ = "Professional Development Team"
__description__ = "Enhanced Professional Map Scanner with Advanced OCR"

# Public API exports
__all__ = [
    # Main classes
    'MapScanner',

    # Exceptions
    'MapScannerError',
    'SafetyExit',
    'WindowError',
    'OCRError',
    'CaptureError',
    'MovementError',
    'CalibrationError',

    # Configuration classes
    'WindowConfig',
    'CaptureConfig',
    'OCRConfig',
    'ScanConfig',
    'LoggingConfig',
    'PyAutoGUIConfig',

    # Package metadata
    '__version__',
    '__author__',
    '__description__',
]


# Package-level convenience functions
def create_scanner(window_title: str = None) -> 'MapScanner':
    """
    Create a MapScanner instance with optional window title.

    Args:
        window_title: Game window title (uses default if None)

    Returns:
        Configured MapScanner instance
    """
    if window_title is None:
        window_title = WindowConfig.DEFAULT_WINDOW_TITLE

    return MapScanner(window_title)


def get_version() -> str:
    """
    Get the package version.

    Returns:
        Version string
    """
    return __version__
