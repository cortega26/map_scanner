"""
Main map scanner module that coordinates all scanning operations.

This is the main orchestrator that brings together all components.
"""

import signal
import time
from typing import List, Dict, Any, Tuple, Optional
import pyautogui
import numpy as np

from map_scanner.config import WindowConfig, CaptureConfig, ScanConfig
from map_scanner.exceptions import SafetyExit, CalibrationError
from map_scanner.logger_config import get_logger
from map_scanner.utils import (
    extract_player_name_from_alliance_tag,
    create_test_directory,
    save_image_safely,
    format_scan_results,
    calculate_overlap_step
)
from map_scanner.window_manager import WindowManager
from map_scanner.screen_capture import ScreenCapture
from map_scanner.mouse_controller import MouseController
from map_scanner.ocr_engine import OCREngine
from map_scanner.ocr_engine import OCRConfig

logger = get_logger(__name__)


class MapScanner:
    """
    Main map scanner class that coordinates all scanning operations.

    Follows the Single Responsibility Principle by orchestrating
    specialized components rather than handling everything directly.
    """

    def __init__(self, window_title: str = WindowConfig.DEFAULT_WINDOW_TITLE):
        """
        Initialize the map scanner with all necessary components.

        Args:
            window_title: Title of the game window to scan
        """
        self.window_title = window_title
        self.running = True

        # Initialize components
        self.window_manager = WindowManager(window_title)
        self.ocr_engine = OCREngine()

        # These will be initialized after window setup
        self.screen_capture: Optional[ScreenCapture] = None
        self.mouse_controller: Optional[MouseController] = None

        # Scanning configuration
        self.capture_size = CaptureConfig.DEFAULT_CAPTURE_SIZE
        self.step_size = CaptureConfig.BASE_STEP_SIZE
        self.vertical_step_size = 0
        self.optimal_zoom_level = 0

        # Safety limits
        self.max_columns_per_row = CaptureConfig.MAX_COLUMNS_PER_ROW
        self.max_rows_total = CaptureConfig.MAX_ROWS_TOTAL

        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(
                "Received interrupt signal - initiating graceful shutdown...")
            self.running = False
            raise SafetyExit("Scanner stopped by user interrupt")

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _check_safety_exit(self):
        """Check if scanner should exit safely."""
        if not self.running:
            raise SafetyExit("Scanner stopped")

        if not self.window_manager.is_window_valid():
            raise SafetyExit("Game window closed")

    def initialize(self) -> bool:
        """
        Initialize all scanner components.

        Returns:
            True if initialization successful
        """
        try:
            # Find and prepare window
            if not self.window_manager.find_and_prepare_window():
                return False

            # Analyze window and calculate areas
            if not self.window_manager.analyze_window_and_calculate_areas():
                return False

            # Calculate optimal capture size
            self.capture_size = self.window_manager.calculate_optimal_capture_size()

            # Initialize screen capture
            self.screen_capture = ScreenCapture(
                self.window_manager.center_x,
                self.window_manager.center_y,
                self.capture_size
            )
            self.screen_capture.set_effective_area(
                self.window_manager.effective_game_area
            )

            # Initialize mouse controller
            self.mouse_controller = MouseController(
                self.window_manager.center_x,
                self.window_manager.center_y
            )
            self.mouse_controller.set_areas(
                self.window_manager.effective_game_area,
                self.window_manager.client_rect
            )

            # Optimize settings based on screen size
            self._optimize_for_screen_size()

            return True

        except Exception as e:
            logger.error(f"Failed to initialize scanner: {e}")
            return False

    def _optimize_for_screen_size(self):
        """Optimize scanner settings based on detected screen and window size."""
        if not self.window_manager.effective_game_area:
            return

        _, _, effective_width, effective_height = self.window_manager.effective_game_area
        screen_width, screen_height = pyautogui.size()

        logger.info("🔧 SCREEN OPTIMIZATION:")
        logger.info(f"  Screen resolution: {screen_width}x{screen_height}")
        logger.info(
            f"  Effective game area: {effective_width}x{effective_height}")

        # Adjust step size based on effective game area width
        if effective_width >= 1600:
            recommended_step = int(effective_width * 0.35)
            self.max_columns_per_row = 150
        elif effective_width >= 1200:
            recommended_step = int(effective_width * 0.30)
            self.max_columns_per_row = 100
        else:
            recommended_step = int(effective_width * 0.25)
            self.max_columns_per_row = 75

        old_step = self.step_size
        self.step_size = max(recommended_step, 400)  # Minimum 400px
        logger.info(
            f"  Auto-optimized step size: {old_step}px → {self.step_size}px")

        # Calculate optimal vertical step
        self.vertical_step_size = calculate_overlap_step(
            self.capture_size[1], CaptureConfig.TARGET_OVERLAP_PERCENT
        )
        self.vertical_step_size = max(self.vertical_step_size, 150)

    def calibrate_zoom(self) -> bool:
        """
        Calibrate zoom level for optimal OCR results.

        Returns:
            True if calibration successful
        """
        logger.info("🔍 ENHANCED ZOOM CALIBRATION FOR GAME TEXT")
        logger.info("Testing zoom levels with game-optimized OCR analysis...")

        try:
            if not self.mouse_controller.safe_move_mouse(
                self.window_manager.center_x,
                self.window_manager.center_y,
                running_flag=self.running
            ):
                return False

            # Test current zoom level
            current_image = self.screen_capture.capture_screen(self.running)
            current_quality, current_info = self.ocr_engine.evaluate_quality(
                current_image)

            logger.info(f"Current zoom quality: {current_quality:.1f}")
            if current_info.get('detected_texts'):
                logger.info(
                    f"Current detected texts: {current_info['detected_texts']}")

            zoom_results = [(0, current_quality, current_info)]
            best_quality = current_quality
            best_zoom_level = 0

            # Test zoom levels
            for zoom_level, clicks_per_level in ScanConfig.ZOOM_LEVELS_TO_TEST:
                self._check_safety_exit()

                direction = "IN" if zoom_level > 0 else "OUT"
                logger.info(
                    f"Testing zoom {direction} level {abs(zoom_level)}...")

                zoom_clicks = clicks_per_level if zoom_level > 0 else -clicks_per_level
                if not self.mouse_controller.zoom_control(zoom_clicks, self.running):
                    continue

                test_image = self.screen_capture.capture_screen(self.running)
                quality, info = self.ocr_engine.evaluate_quality(test_image)

                zoom_results.append((zoom_level, quality, info))

                logger.info(
                    f"  Zoom {zoom_level:+d}: Quality {quality:.1f} "
                    f"(Conf: {info.get('avg_confidence', 0):.1f}, "
                    f"Readable: {info.get('readable_words', 0)}, "
                    f"Height: {info.get('avg_height', 0):.1f}px)"
                )

                if info.get('detected_texts'):
                    logger.info(
                        f"  Sample texts: {info['detected_texts'][:3]}")

                if quality > best_quality:
                    best_quality = quality
                    best_zoom_level = zoom_level
                    logger.info(f"  ✓ NEW BEST ZOOM LEVEL: {zoom_level:+d}")

            # Reset and apply optimal zoom
            self._reset_and_apply_optimal_zoom(zoom_results, best_zoom_level)

            # Final verification
            final_image = self.screen_capture.capture_screen(self.running)
            final_quality, final_info = self.ocr_engine.evaluate_quality(
                final_image)

            self._log_calibration_results(final_quality, final_info)

            return final_quality >= OCRConfig.MIN_QUALITY_THRESHOLD

        except Exception as e:
            logger.error(f"Zoom calibration failed: {e}")
            raise CalibrationError(f"Zoom calibration failed: {e}")

    def _reset_and_apply_optimal_zoom(self, zoom_results: List, best_zoom_level: int):
        """Reset zoom and apply optimal level."""
        logger.info("Resetting to original zoom level...")
        total_applied_zoom = sum(
            abs(level) * 2 for level, _, _ in zoom_results[1:])

        if total_applied_zoom > 0:
            reset_clicks = sum(-level * 2 for level, _, _ in zoom_results[1:])
            if reset_clicks != 0:
                self.mouse_controller.zoom_control(reset_clicks, self.running)

        logger.info(f"🎯 OPTIMAL ZOOM LEVEL: {best_zoom_level:+d}")

        if best_zoom_level != 0:
            optimal_clicks = best_zoom_level * 2
            logger.info(f"Applying optimal zoom: {optimal_clicks:+d} clicks")
            self.mouse_controller.zoom_control(optimal_clicks, self.running)
            self.optimal_zoom_level = best_zoom_level

    def _log_calibration_results(self, final_quality: float, final_info: Dict):
        """Log the final calibration results."""
        logger.info(f"✓ FINAL OCR QUALITY: {final_quality:.1f}")
        logger.info(f"  Confidence: {final_info.get('avg_confidence', 0):.1f}")
        logger.info(f"  Readable Words: {final_info.get('readable_words', 0)}")
        logger.info(f"  Text Height: {final_info.get('avg_height', 0):.1f}px")

        if final_info.get('detected_texts'):
            logger.info(f"  Readable texts: {final_info['detected_texts']}")

        if final_quality >= 60:
            logger.info("🎯 EXCELLENT zoom calibration for game text")
        elif final_quality >= 40:
            logger.info("✓ GOOD zoom calibration for game text")
        elif final_quality >= 25:
            logger.warning("⚠️ MARGINAL zoom calibration")
        else:
            logger.warning("❌ POOR zoom calibration")

    def find_top_left_corner(self) -> bool:
        """Find the top-left corner of the map."""
        logger.info("🎯 FINDING TOP-LEFT CORNER")

        if not self.mouse_controller.safe_move_mouse(
            self.window_manager.center_x,
            self.window_manager.center_y,
            running_flag=self.running
        ):
            return False

        drag_distance = 450
        logger.info("Moving toward top-left corner...")

        for attempt in range(CaptureConfig.MAX_CORNER_SEARCH_ATTEMPTS):
            self._check_safety_exit()

            moved, info = self.screen_capture.capture_and_detect_movement(
                self.mouse_controller, drag_distance, drag_distance,
                duration=0.4, running_flag=self.running
            )

            if attempt % 10 == 0 or not moved:
                logger.info(
                    f"  Attempt {attempt+1}: {'MOVED' if moved else 'CORNER HIT'}")

            if not moved:
                # Confirm we're at corner
                moved_confirm, _ = self.screen_capture.capture_and_detect_movement(
                    self.mouse_controller, 200, 200,
                    duration=0.3, running_flag=self.running
                )
                if not moved_confirm:
                    logger.info("✓ TOP-LEFT CORNER REACHED")
                    return True

        logger.info("✓ Corner search completed")
        return True

    def search_for_targets(
        self,
        image: np.ndarray,
        target_names: List[str]
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Search for target names in the provided image.

        Args:
            image: Image to search in
            target_names: List of target names to find

        Returns:
            Tuple of (found, target_info)
        """
        try:
            if image is None:
                return False, None

            ocr_results = self.ocr_engine.extract_text_comprehensive(image)

            if not ocr_results['best_text']:
                return False, None

            detected_text = ocr_results['best_text'].lower()
            found_targets = []

            for target_name in target_names:
                target_lower = target_name.lower()
                target_without_tags = extract_player_name_from_alliance_tag(
                    target_name
                ).lower()

                # Check full text first
                if target_lower in detected_text:
                    found_targets.append({
                        'name': target_name,
                        'detected_text': ocr_results['best_text'],
                        'match_type': 'exact_full',
                        'confidence': ocr_results['best_confidence'],
                        'ocr_strategy': 'comprehensive'
                    })
                    logger.info(
                        f"🎯 TARGET FOUND (EXACT): '{target_name}' "
                        f"in '{ocr_results['best_text']}'"
                    )
                    continue

                # Check individual words
                words = detected_text.split()
                for word in words:
                    word_without_tags = extract_player_name_from_alliance_tag(
                        word
                    ).lower()

                    if (target_lower == word.lower() or
                        target_lower == word_without_tags or
                        target_without_tags == word.lower() or
                            target_without_tags == word_without_tags):

                        found_targets.append({
                            'name': target_name,
                            'detected_text': ocr_results['best_text'],
                            'matched_word': word,
                            'match_type': 'exact_word',
                            'confidence': ocr_results['best_confidence'],
                            'ocr_strategy': 'comprehensive'
                        })
                        logger.info(
                            f"🎯 TARGET FOUND (WORD): '{target_name}' = '{word}'"
                        )
                        break

            if found_targets:
                best_match = max(
                    found_targets, key=lambda x: x.get('confidence', 0))
                return True, best_match

            return False, None

        except Exception as e:
            logger.error(f"Target search failed: {e}")
            return False, None

    def perform_scan(
        self,
        target_names: List[str],
        max_rows: int = ScanConfig.DEFAULT_MAX_ROWS
    ) -> List[Dict[str, Any]]:
        """
        Perform the main scanning operation.

        Args:
            target_names: List of target names to search for
            max_rows: Maximum number of rows to scan

        Returns:
            List of found targets with their information
        """
        logger.info("🔍 PROFESSIONAL SCAN WITH ENHANCED OCR")
        logger.info(f"Targets: {target_names}")

        targets_found = []
        scan_count = 0

        try:
            if not self.find_top_left_corner():
                logger.error("Failed to find top-left corner")
                return targets_found

            if not self.mouse_controller.safe_move_mouse(
                self.window_manager.center_x,
                self.window_manager.center_y,
                running_flag=self.running
            ):
                return targets_found

            logger.info("🔍 Beginning enhanced scan...")

            for row in range(min(max_rows, self.max_rows_total)):
                self._check_safety_exit()
                logger.info(f"Scanning row {row + 1}...")

                targets_found.extend(
                    self._scan_row(row, target_names, scan_count)
                )

                # Move to next row
                if row < max_rows - 1:
                    moved_down, _ = self.screen_capture.capture_and_detect_movement(
                        self.mouse_controller, 0, -self.vertical_step_size,
                        duration=CaptureConfig.MOVEMENT_DELAY, running_flag=self.running
                    )
                    if not moved_down:
                        logger.info(
                            "✓ Reached BOTTOM boundary - scan complete")
                        break

            scan_count = sum(1 for _ in range(
                min(max_rows, self.max_rows_total)))
            logger.info(
                f"✓ SCAN COMPLETED - {scan_count} positions scanned, "
                f"{len(targets_found)} targets found"
            )
            return targets_found

        except Exception as e:
            logger.error(f"Scan failed: {e}")
            return targets_found

    def _scan_row(
        self,
        row: int,
        target_names: List[str],
        scan_count: int
    ) -> List[Dict[str, Any]]:
        """Scan a single row for targets."""
        targets_found = []
        going_right = (row % 2 == 0)
        direction = '→' if going_right else '←'
        step_dx = self.step_size if going_right else -self.step_size

        col = 1
        while True:
            self._check_safety_exit()
            scan_count += 1

            logger.info(
                f"  Scan {scan_count}: Row {row+1}, Col {col} ({direction})")

            # Capture and search for targets
            image = self.screen_capture.capture_screen(self.running)
            if image is not None:
                found, target_info = self.search_for_targets(
                    image, target_names)
                if found and target_info:
                    target_info['scan_position'] = f"Row {row+1}, Col {col}"
                    target_info['scan_count'] = scan_count
                    targets_found.append(target_info)
                    logger.info(f"🎯 TARGET FOUND: {target_info}")

            # Move to next column
            moved, _ = self.screen_capture.capture_and_detect_movement(
                self.mouse_controller, -step_dx, 0,
                duration=CaptureConfig.MOVEMENT_DELAY, running_flag=self.running
            )

            if not moved:
                boundary = 'RIGHT' if going_right else 'LEFT'
                logger.info(f"  ✓ Reached {boundary} boundary")
                break
            else:
                col += 1
                if col > self.max_columns_per_row:
                    logger.warning(
                        f"Reached safety limit ({self.max_columns_per_row} columns)"
                    )
                    break

        return targets_found

    def perform_test_mode(self, num_screenshots: int = 10) -> List[Dict[str, Any]]:
        """
        Perform test mode to analyze OCR performance.

        Args:
            num_screenshots: Number of test screenshots to take

        Returns:
            List of test results
        """
        logger.info(
            f"🧪 ENHANCED TEST MODE: Analyzing OCR with {num_screenshots} screenshots"
        )

        all_detections = []
        test_dir = create_test_directory()

        try:
            if not self.find_top_left_corner():
                logger.error("Failed to find top-left corner for test mode")
                return all_detections

            if not self.mouse_controller.safe_move_mouse(
                self.window_manager.center_x,
                self.window_manager.center_y,
                running_flag=self.running
            ):
                return all_detections

            logger.info("🔍 Beginning enhanced test mode...")

            for screenshot_num in range(num_screenshots):
                self._check_safety_exit()

                logger.info(
                    f"📸 Test screenshot {screenshot_num + 1}/{num_screenshots}")

                image = self.screen_capture.capture_screen(self.running)
                if image is None:
                    logger.warning(
                        f"Failed to capture screenshot {screenshot_num + 1}")
                    continue

                # Save screenshot if directory available
                if test_dir:
                    screenshot_filename = f"test_{screenshot_num + 1:02d}.png"
                    screenshot_path = f"{test_dir}/{screenshot_filename}"
                    if save_image_safely(image, screenshot_path):
                        logger.info(f"  💾 Saved: {screenshot_filename}")

                # Analyze with OCR
                screenshot_data = self._analyze_test_screenshot(
                    image, screenshot_num + 1, test_dir
                )
                all_detections.append(screenshot_data)

                # Move for next screenshot
                if screenshot_num < num_screenshots - 1:
                    step_size = self.step_size // 3
                    self.screen_capture.capture_and_detect_movement(
                        self.mouse_controller, -step_size, 0,
                        duration=0.3, running_flag=self.running
                    )

            self._generate_test_report(all_detections, test_dir)
            return all_detections

        except Exception as e:
            logger.error(f"Test mode failed: {e}")
            return all_detections

    def _analyze_test_screenshot(
        self,
        image: np.ndarray,
        screenshot_num: int,
        test_dir: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze a single test screenshot."""
        ocr_results = self.ocr_engine.extract_text_comprehensive(image)

        screenshot_data = {
            'screenshot_number': screenshot_num,
            'screenshot_file': f"test_{screenshot_num:02d}.png" if test_dir else None,
            'all_detected_text': ocr_results['best_text'],
            'confidence': ocr_results['best_confidence'],
            'individual_detections': [],
            'word_count': 0,
            'quality_score': 0,
            'readable_words': 0
        }

        if ocr_results['all_detections']:
            readable_count = 0
            for detection in ocr_results['all_detections']:
                if len(detection['text'].strip()) >= 2:
                    screenshot_data['individual_detections'].append({
                        'text': detection['text'].strip(),
                        'confidence': detection['confidence'],
                        'strategy': detection['strategy'],
                        'config': detection['config'],
                        'height': detection['height'],
                        'width': detection['width']
                    })

                    if any(c.isalpha() for c in detection['text'].strip()):
                        readable_count += 1

            screenshot_data['word_count'] = len(
                screenshot_data['individual_detections'])
            screenshot_data['readable_words'] = readable_count

            if screenshot_data['individual_detections']:
                avg_conf = sum(
                    d['confidence'] for d in screenshot_data['individual_detections']
                ) / len(screenshot_data['individual_detections'])
                screenshot_data['quality_score'] = avg_conf

        # Log results
        logger.info(f"  📊 Screenshot {screenshot_num} results:")
        logger.info(
            f"    • Best text: '{screenshot_data['all_detected_text'][:100]}'"
            f"{'...' if len(screenshot_data['all_detected_text']) > 100 else ''}"
        )
        logger.info(f"    • Total detections: {screenshot_data['word_count']}")
        logger.info(
            f"    • Readable words: {screenshot_data['readable_words']}")
        logger.info(
            f"    • Quality score: {screenshot_data['quality_score']:.1f}")

        return screenshot_data

    def _generate_test_report(
        self,
        test_data: List[Dict[str, Any]],
        test_dir: Optional[str]
    ):
        """Generate comprehensive test report."""
        if not test_data:
            logger.warning("No test data to analyze")
            return

        logger.info("=" * 80)
        logger.info("🧪 ENHANCED TEST MODE ANALYSIS REPORT")
        logger.info("=" * 80)

        total_screenshots = len(test_data)
        total_words = sum(data['word_count'] for data in test_data)
        total_readable = sum(data['readable_words'] for data in test_data)
        avg_quality = (
            sum(data['quality_score']
                for data in test_data) / total_screenshots
            if total_screenshots > 0 else 0
        )

        logger.info("📊 OVERALL STATISTICS:")
        logger.info(f"  • Screenshots analyzed: {total_screenshots}")
        logger.info(f"  • Total detections: {total_words}")
        logger.info(f"  • Readable words: {total_readable}")
        logger.info(f"  • Average quality: {avg_quality:.1f}")
        readability_rate = (total_readable/total_words *
                            100) if total_words > 0 else 0
        logger.info(f"  • Readability rate: {readability_rate:.1f}%")

        # Quality assessment
        logger.info("📈 QUALITY ASSESSMENT:")
        if avg_quality >= 50:
            logger.info(
                "  ✅ EXCELLENT: OCR performing very well for game text")
        elif avg_quality >= 35:
            logger.info("  ✅ GOOD: OCR performing well for game text")
        elif avg_quality >= 25:
            logger.info("  ⚠️ MARGINAL: OCR struggling with game text")
        else:
            logger.info("  ❌ POOR: OCR not working well for game text")

        logger.info("=" * 80)

    def execute_scan(
        self,
        target_names: List[str],
        max_rows: int = ScanConfig.DEFAULT_MAX_ROWS,
        test_mode: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Execute the complete scanning process.

        Args:
            target_names: List of target names to search for
            max_rows: Maximum number of rows to scan
            test_mode: Whether to run in test mode

        Returns:
            List of results (targets found or test data)
        """
        try:
            logger.info("=" * 80)
            logger.info("ENHANCED PROFESSIONAL MAP SCANNER")
            logger.info("=" * 80)

            if not self.initialize():
                raise Exception("Failed to initialize scanner")

            if not self.calibrate_zoom():
                logger.warning("Zoom calibration had issues - continuing")

            if test_mode:
                logger.info("ENHANCED TEST MODE - Analyzing OCR...")
                results = self.perform_test_mode(10)
                logger.info("=" * 80)
                logger.info("ENHANCED TEST MODE COMPLETED")
                logger.info("=" * 80)
            else:
                logger.info("ENHANCED PROFESSIONAL SCAN...")
                results = self.perform_scan(target_names, max_rows)

                logger.info("=" * 80)
                logger.info("ENHANCED SCAN COMPLETED")
                logger.info("=" * 80)

                logger.info(format_scan_results(results))

            return results

        except Exception as e:
            logger.error(f"Scanner execution failed: {e}")
            return []
