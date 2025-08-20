"""
Utility functions for the Map Scanner application.

Contains reusable helper functions following DRY principles.
"""

import os
import re
import random
import time
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Any, Dict

import numpy as np

from .logger_config import get_logger

logger = get_logger(__name__)


def extract_player_name_from_alliance_tag(text: str) -> str:
    """
    Extract player name from alliance-tagged text.

    Args:
        text: Text that may contain alliance tags

    Returns:
        Cleaned player name without alliance tags
    """
    patterns = [
        r'^\[.*?\]',      # [HxC], [iio], etc.
        r'^\(.*?\)',      # (TAG), etc.
        r'^\{.*?\}',      # {TAG}, etc.
        r'^\<.*?\>',      # <TAG>, etc.
        r'^.*?\|',        # TAG|, etc.
    ]

    cleaned_text = text
    for pattern in patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text).strip()

    return cleaned_text if cleaned_text else text


def create_test_directory(prefix: str = "test_screenshots") -> Optional[str]:
    """
    Create a timestamped test directory.

    Args:
        prefix: Directory name prefix

    Returns:
        Directory path if successful, None otherwise
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_dir = f"{prefix}_{timestamp}"

    try:
        os.makedirs(test_dir, exist_ok=True)
        logger.info(f"📁 Test directory created: {test_dir}")
        return test_dir
    except Exception as e:
        logger.warning(f"Could not create test directory: {e}")
        return None


def add_variance(value: float, variance_range: Tuple[float, float]) -> float:
    """
    Add random variance to a value for natural behavior.

    Args:
        value: Base value
        variance_range: Tuple of (min_multiplier, max_multiplier)

    Returns:
        Value with random variance applied
    """
    multiplier = random.uniform(*variance_range)
    return value * multiplier


def safe_clamp(value: int, min_val: int, max_val: int) -> int:
    """
    Safely clamp a value between min and max bounds.

    Args:
        value: Value to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Clamped value
    """
    return max(min_val, min(value, max_val))


def calculate_effective_area(
    client_rect: Tuple[int, int, int, int],
    ui_margins: Dict[str, float]
) -> Tuple[int, int, int, int]:
    """
    Calculate effective game area excluding UI margins.

    Args:
        client_rect: Client rectangle (x, y, right, bottom)
        ui_margins: UI margin percentages

    Returns:
        Effective area (x, y, width, height)
    """
    window_width = client_rect[2] - client_rect[0]
    window_height = client_rect[3] - client_rect[1]

    # Calculate margins in pixels
    left_margin = int(window_width * ui_margins['left'])
    right_margin = int(window_width * ui_margins['right'])
    top_margin = int(window_height * ui_margins['top'])
    bottom_margin = int(window_height * ui_margins['bottom'])

    # Calculate effective game area
    effective_x = client_rect[0] + left_margin
    effective_y = client_rect[1] + top_margin
    effective_width = window_width - left_margin - right_margin
    effective_height = window_height - top_margin - bottom_margin

    return effective_x, effective_y, effective_width, effective_height


def calculate_overlap_step(capture_size: int, overlap_percent: float) -> int:
    """
    Calculate step size to achieve target overlap percentage.

    Args:
        capture_size: Size of capture area
        overlap_percent: Desired overlap percentage

    Returns:
        Calculated step size
    """
    return int(capture_size * (1 - overlap_percent / 100))


def parse_target_names(targets_str: str) -> List[str]:
    """
    Parse comma-separated target names string.

    Args:
        targets_str: Comma-separated target names

    Returns:
        List of cleaned target names
    """
    if not targets_str:
        return []

    return [name.strip() for name in targets_str.split(",") if name.strip()]


def calculate_quality_score(
    confidence: float,
    height: float,
    text_count: int,
    readable_words: int,
    weights: Dict[str, float]
) -> float:
    """
    Calculate OCR quality score based on multiple factors.

    Args:
        confidence: Average OCR confidence
        height: Average text height
        text_count: Number of detected text elements
        readable_words: Number of readable words
        weights: Scoring weights for each factor

    Returns:
        Overall quality score (0-100)
    """
    # Confidence score
    confidence_score = min(confidence, 100)

    # Size score (optimal for game text)
    if 12 <= height <= 25:  # Optimal for game text
        size_score = 100
    elif 8 <= height < 12:
        size_score = 85
    elif 25 < height <= 35:
        size_score = 85
    elif height < 8:
        size_score = 50
    else:
        size_score = 70

    # Count score
    count_score = min(text_count * 15, 100)

    # Readability score
    readability_score = min(readable_words * 25, 100)

    # Calculate weighted score
    overall_quality = (
        confidence_score * weights['confidence'] +
        size_score * weights['size'] +
        count_score * weights['count'] +
        readability_score * weights['readability']
    )

    return overall_quality


def save_image_safely(image: np.ndarray, filepath: str) -> bool:
    """
    Safely save an image to disk.

    Args:
        image: Image array to save
        filepath: Target file path

    Returns:
        True if successful, False otherwise
    """
    try:
        from PIL import Image as PILImage

        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        # Convert and save
        pil_image = PILImage.fromarray(image)
        pil_image.save(filepath)

        logger.debug(f"Image saved: {filepath}")
        return True

    except Exception as e:
        logger.warning(f"Failed to save image {filepath}: {e}")
        return False


def format_scan_results(results: List[Dict[str, Any]]) -> str:
    """
    Format scan results for display.

    Args:
        results: List of scan result dictionaries

    Returns:
        Formatted results string
    """
    if not results:
        return "No targets found during scan"

    lines = [f"🎯 SUCCESS: {len(results)} targets found"]

    for i, target in enumerate(results, 1):
        confidence = target.get('confidence', 0)
        position = target.get('scan_position', 'Unknown')
        name = target.get('name', 'Unknown')

        lines.append(
            f"  {i}. {name} at {position} (confidence: {confidence:.1f})"
        )

    return "\n".join(lines)
