"""
Mouse controller module for handling mouse movements and interactions.

Handles all mouse-related operations with natural movement patterns.
"""

import time
import random
from typing import Tuple, Optional
import pyautogui

from .map_scanner.config import CaptureConfig, PyAutoGUIConfig
from .map_scanner.exceptions import MovementError, SafetyExit
from .map_scanner.logger_config import get_logger
from .map_scanner.utils import add_variance, safe_clamp

logger = get_logger(__name__)


class MouseController:
    """Handles mouse movements and interactions with natural behavior patterns."""

    def __init__(self, center_x: int, center_y: int):
        """
        Initialize mouse controller with center coordinates.

        Args:
            center_x: X coordinate of center point
            center_y: Y coordinate of center point
        """
        self.center_x = center_x
        self.center_y = center_y
        self.effective_game_area: Optional[Tuple[int, int, int, int]] = None
        self.client_rect: Optional[Tuple[int, int, int, int]] = None

        # Configure PyAutoGUI
        pyautogui.FAILSAFE = PyAutoGUIConfig.FAILSAFE
        pyautogui.PAUSE = PyAutoGUIConfig.PAUSE

        if PyAutoGUIConfig.FAILSAFE:
            logger.info(
                "PyAutoGUI fail-safe ENABLED - move mouse to corner to emergency stop"
            )

    def set_areas(
        self,
        effective_area: Optional[Tuple[int, int, int, int]] = None,
        client_rect: Optional[Tuple[int, int, int, int]] = None
    ):
        """
        Set effective game area and client rect for boundary calculations.

        Args:
            effective_area: Effective game area (x, y, width, height)
            client_rect: Client rectangle (x, y, right, bottom)
        """
        self.effective_game_area = effective_area
        self.client_rect = client_rect

    def update_center(self, center_x: int, center_y: int):
        """
        Update the center coordinates.

        Args:
            center_x: New X coordinate
            center_y: New Y coordinate
        """
        self.center_x = center_x
        self.center_y = center_y

    def safe_move_mouse(
        self,
        x: int,
        y: int,
        duration: float = 0.3,
        running_flag: bool = True
    ) -> bool:
        """
        Safely move mouse to coordinates with boundary checking.

        Args:
            x: Target X coordinate
            y: Target Y coordinate
            duration: Movement duration
            running_flag: Flag to check if operation should continue

        Returns:
            True if movement successful

        Raises:
            SafetyExit: If running flag is False
        """
        try:
            if not running_flag:
                raise SafetyExit("Mouse movement stopped")

            safe_x, safe_y = self._calculate_safe_coordinates(x, y)

            pyautogui.moveTo(safe_x, safe_y, duration=duration)
            time.sleep(0.1)
            return True

        except SafetyExit:
            raise
        except Exception as e:
            logger.error(f"Failed to move mouse: {e}")
            return False

    def safe_drag(
        self,
        dx: int,
        dy: int,
        duration: float = 0.3,
        running_flag: bool = True
    ) -> bool:
        """
        Perform drag operation with automatic recentering and natural behavior.

        Args:
            dx: X displacement
            dy: Y displacement
            duration: Drag duration
            running_flag: Flag to check if operation should continue

        Returns:
            True if drag successful

        Raises:
            SafetyExit: If running flag is False
        """
        try:
            if not running_flag:
                raise SafetyExit("Drag operation stopped")

            # Add natural variance to duration and movement
            final_duration = add_variance(
                duration, CaptureConfig.DURATION_VARIANCE_RANGE)
            actual_dx = int(
                dx * add_variance(1.0, CaptureConfig.POSITION_VARIANCE_RANGE))
            actual_dy = int(
                dy * add_variance(1.0, CaptureConfig.POSITION_VARIANCE_RANGE))

            # Ensure we start from center
            self._ensure_centered_start()

            # Calculate safe target coordinates
            target_x = self.center_x + actual_dx
            target_y = self.center_y + actual_dy
            safe_target_x, safe_target_y = self._calculate_safe_coordinates(
                target_x, target_y, margin=100
            )

            # Calculate actual displacement to safe target
            final_dx = safe_target_x - self.center_x
            final_dy = safe_target_y - self.center_y

            # Perform drag
            pyautogui.drag(final_dx, final_dy,
                           duration=final_duration, button='left')

            # Add natural pause after drag
            post_drag_pause = add_variance(
                0.2, CaptureConfig.POST_DRAG_PAUSE_RANGE
            )
            time.sleep(post_drag_pause)

            # Recenter mouse
            self._recenter_mouse()

            # Settlement delay
            settle_time = add_variance(CaptureConfig.SETTLE_DELAY, (0.8, 1.2))
            time.sleep(max(settle_time, 0.3))

            if not running_flag:
                raise SafetyExit("Drag operation stopped during settlement")

            return True

        except SafetyExit:
            raise
        except Exception as e:
            logger.error(f"Failed to perform drag: {e}")
            return False

    def zoom_control(self, clicks: int, running_flag: bool = True) -> bool:
        """
        Control zoom with mouse scroll.

        Args:
            clicks: Number of scroll clicks (positive = zoom in, negative = zoom out)
            running_flag: Flag to check if operation should continue

        Returns:
            True if zoom successful

        Raises:
            SafetyExit: If running flag is False
        """
        try:
            if not running_flag:
                raise SafetyExit("Zoom operation stopped")

            pyautogui.scroll(clicks)
            time.sleep(CaptureConfig.ZOOM_DELAY)
            return True

        except SafetyExit:
            raise
        except Exception as e:
            logger.error(f"Zoom control failed: {e}")
            return False

    def _ensure_centered_start(self):
        """Ensure mouse starts from center position."""
        current_x, current_y = pyautogui.position()

        if (abs(current_x - self.center_x) > 10 or
                abs(current_y - self.center_y) > 10):

            center_duration = add_variance(0.2, (0.75, 1.25))
            pyautogui.moveTo(self.center_x, self.center_y,
                             duration=center_duration)
            time.sleep(add_variance(0.1, (0.5, 1.5)))

    def _recenter_mouse(self):
        """Recenter mouse to center position."""
        recenter_duration = add_variance(0.2, (0.75, 1.25))
        pyautogui.moveTo(self.center_x, self.center_y,
                         duration=recenter_duration)

    def _calculate_safe_coordinates(
        self,
        x: int,
        y: int,
        margin: int = 50
    ) -> Tuple[int, int]:
        """
        Calculate safe coordinates within boundaries.

        Args:
            x: Target X coordinate
            y: Target Y coordinate
            margin: Safety margin from boundaries

        Returns:
            Safe coordinates (x, y)
        """
        if self.effective_game_area:
            eff_x, eff_y, eff_width, eff_height = self.effective_game_area
            safe_x = safe_clamp(x, eff_x + margin, eff_x + eff_width - margin)
            safe_y = safe_clamp(y, eff_y + margin, eff_y + eff_height - margin)
        elif self.client_rect:
            safe_x = safe_clamp(x, self.client_rect[0] + margin,
                                self.client_rect[2] - margin)
            safe_y = safe_clamp(y, self.client_rect[1] + margin,
                                self.client_rect[3] - margin)
        else:
            # Fallback to screen boundaries
            screen_width, screen_height = pyautogui.size()
            safe_x = safe_clamp(x, margin, screen_width - margin)
            safe_y = safe_clamp(y, margin, screen_height - margin)

        return safe_x, safe_y
