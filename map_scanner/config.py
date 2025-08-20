"""
Configuration module for the Map Scanner application.

Contains all configuration constants, settings, and default values
following the Zen of Python principle: "Namespaces are one honking great idea".
"""

from typing import Dict, Tuple


class WindowConfig:
    """Window-related configuration constants."""
    
    DEFAULT_WINDOW_TITLE = "Last War-Survival Game"
    MIN_WINDOW_WIDTH = 500
    MIN_WINDOW_HEIGHT = 300
    
    # UI Margins (as percentages) - optimized based on actual game UI
    UI_MARGINS = {
        'left': 0.06,    # 6% for left toolbar
        'right': 0.12,   # 12% for right UI panels
        'top': 0.08,     # 8% for Windows title bar + resource bars
        'bottom': 0.12   # 12% for chat window + heroes panel
    }


class CaptureConfig:
    """Screen capture and movement configuration."""
    
    DEFAULT_CAPTURE_SIZE = (500, 400)
    BASE_STEP_SIZE = 900
    TARGET_OVERLAP_PERCENT = 15  # Target 15% overlap (10-20% range)
    
    # Timing configuration
    MOVEMENT_DELAY = 0.3
    SETTLE_DELAY = 0.5
    ZOOM_DELAY = 0.5
    POST_DRAG_PAUSE_RANGE = (0.1, 0.3)
    
    # Safety limits
    MAX_COLUMNS_PER_ROW = 100
    MAX_ROWS_TOTAL = 50
    MAX_CORNER_SEARCH_ATTEMPTS = 200
    
    # Movement variance for natural mouse behavior
    DURATION_VARIANCE_RANGE = (0.8, 1.2)
    POSITION_VARIANCE_RANGE = (0.98, 1.02)


class OCRConfig:
    """OCR engine configuration and strategies."""
    
    # Tesseract configurations optimized for game text
    TESSERACT_CONFIGS = {
        # Game-optimized configurations
        'game_names': (
            r'--oem 1 --psm 8 -c tessedit_char_whitelist='
            r'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            r'0123456789[](){}.-_!@#$%^&*+= '
        ),
        'single_word_game': r'--oem 1 --psm 8',
        'raw_line_game': r'--oem 1 --psm 13',
        'sparse_text_game': r'--oem 1 --psm 11',
        
        # Legacy configurations with better PSM modes
        'legacy_single': (
            r'--oem 1 --psm 8 -c tessedit_char_whitelist='
            r'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            r'0123456789[]().-_ '
        ),
        'legacy_raw': (
            r'--oem 1 --psm 13 -c tessedit_char_whitelist='
            r'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            r'0123456789[](){}|<>.-_!@#$%^&*+=~ '
        ),
        
        # Original configurations (kept as fallbacks)
        'default': r'--oem 3 --psm 6',
        'text_heavy': r'--oem 3 --psm 3',
        'single_word': r'--oem 3 --psm 8',
        'single_char': r'--oem 3 --psm 10',
        'base_names': (
            r'--oem 3 --psm 6 -c tessedit_char_whitelist='
            r'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            r'0123456789[]().-_ '
        ),
        'player_names': (
            r'--oem 3 --psm 6 -c tessedit_char_whitelist='
            r'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            r'0123456789[](){}.-_!@#$%^&*+= '
        ),
        'alliance_names': (
            r'--oem 3 --psm 6 -c tessedit_char_whitelist='
            r'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            r'0123456789[](){}|<>.-_!@#$%^&*+=~ '
        ),
    }
    
    # OCR processing strategies
    OCR_STRATEGIES = [
        # Game-specific strategies first
        ('game_text', 'game_names'),
        ('white_text_outline', 'single_word_game'),
        ('upscale_sharp', 'legacy_single'),
        ('enhanced_contrast', 'raw_line_game'),
        ('game_text', 'legacy_raw'),
        
        # Upscaling strategies for small text
        ('upscale', 'game_names'),
        ('upscale_sharp', 'sparse_text_game'),
        
        # Original strategies as fallbacks
        ('default', 'player_names'),
        ('sharp_text', 'alliance_names'),
        ('denoise', 'text_heavy'),
        ('high_contrast', 'single_word'),
    ]
    
    # Quality thresholds
    MIN_TEXT_LENGTH = 2
    MIN_CONFIDENCE_THRESHOLD = 20
    MIN_QUALITY_THRESHOLD = 25
    
    # Image processing parameters
    CLAHE_CLIP_LIMIT = 3.0
    CLAHE_TILE_GRID_SIZE = (8, 8)
    BILATERAL_FILTER_PARAMS = (9, 75, 75)
    GAUSSIAN_BLUR_KERNEL = (3, 3)
    MORPHOLOGY_KERNEL_SIZE = (2, 2)


class ScanConfig:
    """Scanning behavior configuration."""
    
    DEFAULT_MAX_ROWS = 20
    SIMILARITY_THRESHOLD = 98.0  # For movement detection
    
    # Quality scoring weights
    QUALITY_WEIGHTS = {
        'confidence': 0.3,
        'size': 0.2,
        'count': 0.2,
        'readability': 0.3,
    }
    
    # Zoom calibration
    ZOOM_LEVELS_TO_TEST = [
        (1, 2), (2, 2), (3, 2),   # Zoom in moderately
        (-1, 2), (-2, 2), (-3, 2)  # Zoom out moderately
    ]


class LoggingConfig:
    """Logging configuration constants."""
    
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    LOG_FILENAME = 'map_scanner.log'
    LOG_ENCODING = 'utf-8'


class PyAutoGUIConfig:
    """PyAutoGUI configuration."""
    
    FAILSAFE = True
    PAUSE = 0.1