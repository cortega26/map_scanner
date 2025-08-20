"""
Window management module for handling game window operations.

Handles window detection, preparation, and area calculation.
"""

import time
from typing import Tuple, Optional, Dict, Any
import win32con
import win32gui

from .map_scanner.config import WindowConfig
from .map_scanner.exceptions import WindowError
from .map_scanner.logger_config import get_logger
from .map_scanner.utils import calculate_effective_area

logger = get_logger(__name__)


class WindowManager:
    """Manages game window operations and calculations."""

    def __init__(self, window_title: str = WindowConfig.DEFAULT_WINDOW_TITLE):
        """
        Initialize window manager.

        Args:
            window_title: Title of the game window to find
        """
        self.window_title = window_title
        self.hwnd: Optional[int] = None
        self.client_rect: Optional[Tuple[int, int, int, int]] = None
        self.window_width = 0
        self.window_height = 0
        self.effective_game_area: Optional[Tuple[int, int, int, int]] = None
        self.center_x = 0
        self.center_y = 0

    def find_and_prepare_window(self) -> bool:
        """
        Find the game window and prepare it for scanning.

        Returns:
            True if window found and prepared successfully

        Raises:
            WindowError: If window cannot be found or prepared
        """
        if not self._find_window():
            raise WindowError(f"Could not find window: {self.window_title}")

        if not self._prepare_window():
            raise WindowError("Failed to prepare window")

        return True

    def _find_window(self) -> bool:
        """Find the game window by title."""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title.strip():
                    windows.append((hwnd, title))

        all_windows = []
        win32gui.EnumWindows(enum_windows_callback, all_windows)

        # Find matching windows
        matching_windows = [
            (hwnd, title) for hwnd, title in all_windows
            if self.window_title in title
        ]

        if not matching_windows:
            logger.error(
                f"Could not find window with title containing: '{self.window_title}'"
            )
            logger.info("Available windows:")
            for hwnd, title in all_windows[:10]:
                logger.info(f"  - {title}")
            return False

        self.hwnd = matching_windows[0][0]
        window_title = matching_windows[0][1]
        logger.info(f"🎯 Found window: {window_title}")
        return True

    def _prepare_window(self) -> bool:
        """Prepare the window for scanning."""
        try:
            if win32gui.IsIconic(self.hwnd):
                logger.info("Window is minimized, restoring...")
                win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
                time.sleep(1.5)

            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
            win32gui.SetForegroundWindow(self.hwnd)
            time.sleep(2.0)

            # Get and validate client area
            rect = win32gui.GetClientRect(self.hwnd)
            client_pos = win32gui.ClientToScreen(self.hwnd, (0, 0))

            self.client_rect = (
                client_pos[0],
                client_pos[1],
                client_pos[0] + rect[2],
                client_pos[1] + rect[3]
            )

            self.window_width = self.client_rect[2] - self.client_rect[0]
            self.window_height = self.client_rect[3] - self.client_rect[1]

            if (self.window_width < WindowConfig.MIN_WINDOW_WIDTH or
                    self.window_height < WindowConfig.MIN_WINDOW_HEIGHT):
                raise WindowError(
                    f"Window too small: {self.window_width}x{self.window_height}"
                )

            logger.info(f"✓ Client area: {self.client_rect}")
            logger.info(
                f"✓ Window size: {self.window_width}x{self.window_height}")

            return True

        except Exception as e:
            logger.error(f"Failed to prepare window: {e}")
            return False

    def analyze_window_and_calculate_areas(self) -> bool:
        """Analyze window and calculate capture areas."""
        if not self.client_rect:
            logger.error("No client rect available for window analysis")
            return False

        # Calculate effective game area
        self.effective_game_area = calculate_effective_area(
            self.client_rect, WindowConfig.UI_MARGINS
        )

        effective_x, effective_y, effective_width, effective_height = self.effective_game_area

        # Update center point to be within effective game area
        self.center_x = effective_x + effective_width // 2
        self.center_y = effective_y + effective_height // 2

        self._log_analysis_results()
        return True

    def _log_analysis_results(self):
        """Log the window analysis results."""
        if not self.effective_game_area:
            return

        effective_x, effective_y, effective_width, effective_height = self.effective_game_area

        # Calculate margins in pixels for logging
        left_margin = int(self.window_width * WindowConfig.UI_MARGINS['left'])
        right_margin = int(self.window_width *
                           WindowConfig.UI_MARGINS['right'])
        top_margin = int(self.window_height * WindowConfig.UI_MARGINS['top'])
        bottom_margin = int(self.window_height *
                            WindowConfig.UI_MARGINS['bottom'])

        logger.info("📐 WINDOW ANALYSIS RESULTS:")
        logger.info(
            f"  Full window size: {self.window_width}x{self.window_height}")
        logger.info(
            f"  UI margins: L={left_margin}px, R={right_margin}px, "
            f"T={top_margin}px, B={bottom_margin}px"
        )
        logger.info(
            f"  Effective game area: {effective_width}x{effective_height}")
        logger.info(f"  New center point: ({self.center_x}, {self.center_y})")

    def calculate_optimal_capture_size(self) -> Tuple[int, int]:
        """
        Calculate optimal capture size based on effective area.

        Returns:
            Optimal capture size (width, height)
        """
        if not self.effective_game_area:
            return WindowConfig.DEFAULT_CAPTURE_SIZE

        _, _, effective_width, effective_height = self.effective_game_area

        # Maximize capture area within the effective scanning region
        capture_width = max(int(effective_width * 0.85), 600)
        capture_height = max(int(effective_height * 0.80), 500)

        capture_size = (capture_width, capture_height)

        logger.info(
            f"  Optimal capture size: {capture_size[0]}x{capture_size[1]}")
        logger.info(
            f"  Capture coverage: "
            f"{(capture_width/effective_width)*100:.1f}% x "
            f"{(capture_height/effective_height)*100:.1f}% of effective area"
        )

        return capture_size

    def is_window_valid(self) -> bool:
        """Check if the window is still valid."""
        try:
            return self.hwnd and win32gui.IsWindow(self.hwnd)
        except Exception:
            return False

    def get_window_info(self) -> Dict[str, Any]:
        """Get comprehensive window information."""
        return {
            'hwnd': self.hwnd,
            'window_title': self.window_title,
            'client_rect': self.client_rect,
            'window_size': (self.window_width, self.window_height),
            'effective_game_area': self.effective_game_area,
            'center_point': (self.center_x, self.center_y),
            'is_valid': self.is_window_valid()
        }
