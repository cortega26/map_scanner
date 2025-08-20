"""
Screen capture module for handling screenshot operations.

Handles screen capture with proper error handling and area validation.
"""

from typing import Optional, Tuple
import numpy as np
import pyautogui
import cv2

from .config import CaptureConfig
from .exceptions import CaptureError, SafetyExit
from .logger_config import get_logger
from .utils import safe_clamp

logger = get_logger(__name__)


class ScreenCapture:
    """Handles screen capture operations with safety checks."""

    def __init__(self, center_x: int, center_y: int, capture_size: Tuple[int, int]):
        """
        Initialize screen capture with center point and capture size.

        Args:
            center_x: X coordinate of capture center
            center_y: Y coordinate of capture center
            capture_size: Capture area size (width, height)
        """
        self.center_x = center_x
        self.center_y = center_y
        self.capture_size = capture_size
        self.effective_game_area: Optional[Tuple[int, int, int, int]] = None

    def set_effective_area(self, effective_area: Tuple[int, int, int, int]):
        """
        Set the effective game area for capture validation.

        Args:
            effective_area: Effective area (x, y, width, height)
        """
        self.effective_game_area = effective_area

    def update_center(self, center_x: int, center_y: int):
        """
        Update the capture center point.

        Args:
            center_x: New X coordinate
            center_y: New Y coordinate
        """
        self.center_x = center_x
        self.center_y = center_y

    def capture_screen(self, running_flag: bool = True) -> Optional[np.ndarray]:
        """
        Capture screen with comprehensive error handling.

        Args:
            running_flag: Flag to check if operation should continue

        Returns:
            Screenshot as numpy array, or None if failed

        Raises:
            SafetyExit: If running flag is False
            CaptureError: If capture fails
        """
        try:
            if not running_flag:
                raise SafetyExit("Capture stopped")

            x, y = self._calculate_capture_coordinates()

            screenshot = pyautogui.screenshot(
                region=(x, y, self.capture_size[0], self.capture_size[1])
            )
            return np.array(screenshot)

        except SafetyExit:
            raise
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            raise CaptureError(f"Screen capture failed: {e}")

    def _calculate_capture_coordinates(self) -> Tuple[int, int]:
        """Calculate safe capture coordinates."""
        x = self.center_x - self.capture_size[0] // 2
        y = self.center_y - self.capture_size[1] // 2

        if self.effective_game_area:
            eff_x, eff_y, eff_width, eff_height = self.effective_game_area
            x = safe_clamp(x, eff_x, eff_x + eff_width - self.capture_size[0])
            y = safe_clamp(y, eff_y, eff_y + eff_height - self.capture_size[1])

        return x, y

    def detect_movement(
        self,
        before_image: np.ndarray,
        after_image: np.ndarray
    ) -> Tuple[bool, str]:
        """
        Detect movement between two images using correlation.

        Args:
            before_image: Image before movement
            after_image: Image after movement

        Returns:
            Tuple of (movement_detected, similarity_info)
        """
        try:
            if before_image is None or after_image is None:
                return False, "Invalid images provided"

            before_gray = cv2.cvtColor(before_image, cv2.COLOR_RGB2GRAY)
            after_gray = cv2.cvtColor(after_image, cv2.COLOR_RGB2GRAY)

            correlation = cv2.matchTemplate(
                before_gray, after_gray, cv2.TM_CCOEFF_NORMED
            )[0][0]
            similarity_percentage = correlation * 100

            movement_detected = similarity_percentage < CaptureConfig.SIMILARITY_THRESHOLD

            return movement_detected, f"{similarity_percentage:.1f}% similar"

        except Exception as e:
            logger.error(f"Movement detection failed: {e}")
            return False, str(e)

    def capture_and_detect_movement(
        self,
        mouse_controller,
        dx: int,
        dy: int,
        duration: float,
        running_flag: bool = True
    ) -> Tuple[bool, str]:
        """
        Capture before/after images and detect movement.

        Args:
            mouse_controller: Mouse controller instance for movement
            dx: X displacement for movement
            dy: Y displacement for movement
            duration: Movement duration
            running_flag: Flag to check if operation should continue

        Returns:
            Tuple of (movement_detected, info_string)
        """
        try:
            # Capture before image
            before_img = self.capture_screen(running_flag)
            if before_img is None:
                return False, "Could not capture before image"

            # Perform movement
            if not mouse_controller.safe_drag(dx, dy, duration):
                return False, "Drag operation failed"

            # Wait for movement to settle
            import time
            time.sleep(0.4)

            # Capture after image
            after_img = self.capture_screen(running_flag)
            if after_img is None:
                return False, "Could not capture after image"

            # Detect movement
            return self.detect_movement(before_img, after_img)

        except Exception as e:
            logger.error(f"Capture and movement detection failed: {e}")
            return False, str(e)
