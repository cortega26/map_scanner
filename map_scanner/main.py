"""
Main entry point for the Map Scanner application.

Handles command line arguments and orchestrates the scanning process.
"""

import argparse
import logging
import sys
from typing import List, Optional

from .config import WindowConfig, ScanConfig
from .exceptions import SafetyExit, MapScannerError
from .logger_config import setup_logging, get_logger
from . import MapScanner
from .utils import parse_target_names

# Initialize logger
logger = get_logger(__name__)


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Enhanced Professional Map Scanner with Improved Game Text OCR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test the enhanced OCR on your game
  python -m map_scanner --test yes
  
  # Normal scanning with enhanced OCR
  python -m map_scanner --targets "AnnoyingCat,PlayerName123"
  python -m map_scanner --targets "[MoL]ZKeubnmasdfngh"
  
  # Scan with custom parameters
  python -m map_scanner --targets "Player1,Player2" --max-rows 30 --window "Game Window"
        """
    )

    parser.add_argument(
        "--targets",
        required=False,
        help="Comma-separated target names to search for"
    )

    parser.add_argument(
        "--window",
        default=WindowConfig.DEFAULT_WINDOW_TITLE,
        help="Game window title to search for"
    )

    parser.add_argument(
        "--max-rows",
        type=int,
        default=ScanConfig.DEFAULT_MAX_ROWS,
        help="Maximum rows to scan (default: %(default)s)"
    )

    parser.add_argument(
        "--test",
        choices=["yes", "no"],
        default="no",
        help="Enable test mode for OCR analysis (default: %(default)s)"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    parser.add_argument(
        "--log-file",
        default=None,
        help="Custom log file path (optional)"
    )

    return parser


def validate_arguments(args: argparse.Namespace) -> tuple[bool, Optional[str]]:
    """
    Validate command line arguments.

    Args:
        args: Parsed command line arguments

    Returns:
        Tuple of (is_valid, error_message)
    """
    test_mode = args.test == "yes"

    # Validate targets for non-test mode
    if not test_mode and not args.targets:
        return False, "--targets is required when not in test mode"

    if not test_mode:
        target_names = parse_target_names(args.targets)
        if not target_names:
            return False, "No valid target names provided"

    # Validate max_rows
    if args.max_rows <= 0:
        return False, "max-rows must be greater than 0"

    if args.max_rows > 100:
        return False, "max-rows should not exceed 100 for safety"

    return True, None


def setup_application_logging(debug: bool = False, log_file: Optional[str] = None):
    """
    Setup application logging configuration.

    Args:
        debug: Enable debug logging
        log_file: Custom log file path
    """
    log_level = logging.DEBUG if debug else logging.INFO
    setup_logging(level=log_level, log_file=log_file)


def print_application_header():
    """Print the application header with feature information."""
    logger.info("=" * 80)
    logger.info("ENHANCED PROFESSIONAL MAP SCANNER v3.0")
    logger.info("Improved Game Text Recognition & OCR")
    logger.info("=" * 80)
    logger.info("🚀 ENHANCED FEATURES:")
    logger.info("   • Advanced game text preprocessing")
    logger.info("   • White text + black outline detection")
    logger.info("   • Legacy OCR engine support")
    logger.info("   • Improved PSM modes for isolated text")
    logger.info("   • Enhanced quality scoring")
    logger.info("   • Better alliance tag handling")
    logger.info("=" * 80)


def main() -> int:
    """
    Main application entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Parse command line arguments
        parser = create_argument_parser()
        args = parser.parse_args()

        # Setup logging
        setup_application_logging(args.debug, args.log_file)

        # Validate arguments
        is_valid, error_message = validate_arguments(args)
        if not is_valid:
            logger.error(f"Invalid arguments: {error_message}")
            parser.print_help()
            return 1

        # Print application header
        print_application_header()

        # Prepare execution parameters
        test_mode = args.test == "yes"
        target_names = parse_target_names(args.targets) if args.targets else []

        if test_mode and target_names:
            logger.info(f"Test mode enabled with targets: {target_names}")
        elif not test_mode:
            logger.info(f"Scanning for targets: {target_names}")
        else:
            logger.info("Test mode enabled - analyzing OCR performance")

        # Create and execute scanner
        scanner = MapScanner(args.window)

        results = scanner.execute_scan(
            target_names=target_names,
            max_rows=args.max_rows,
            test_mode=test_mode
        )

        # Determine exit code based on results
        if test_mode:
            # In test mode, success is having any results
            return 0 if results else 1
        else:
            # In scan mode, success is finding targets
            return 0 if results else 1

    except KeyboardInterrupt:
        logger.info("Scanner interrupted by user")
        return 0

    except SafetyExit as e:
        logger.info(f"Scanner stopped safely: {e}")
        return 0

    except MapScannerError as e:
        logger.error(f"Scanner error: {e}")
        return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if logger.isEnabledFor(logging.DEBUG):
            import traceback
            logger.debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
