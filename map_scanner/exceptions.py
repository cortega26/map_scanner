"""
Custom exceptions for the Map Scanner application.

Following the Zen of Python: "Errors should never pass silently."
"""


class MapScannerError(Exception):
    """Base exception for all map scanner related errors."""
    pass


class SafetyExit(MapScannerError):
    """Exception for safe exit scenarios."""
    pass


class WindowError(MapScannerError):
    """Exception for window-related operations."""
    pass


class OCRError(MapScannerError):
    """Exception for OCR-related operations."""
    pass


class CaptureError(MapScannerError):
    """Exception for screen capture operations."""
    pass


class MovementError(MapScannerError):
    """Exception for mouse movement operations."""
    pass


class CalibrationError(MapScannerError):
    """Exception for zoom calibration operations."""
    pass
