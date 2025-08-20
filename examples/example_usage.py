"""
Example usage scripts for the Map Scanner application.

Demonstrates various ways to use the refactored map scanner with
different configurations and use cases.
"""

import logging
from typing import List, Dict, Any

# Import the refactored components
from map_scanner import (
    MapScanner,
    create_scanner,
    WindowConfig,
    ScanConfig,
    OCRConfig
)
from map_scanner.exceptions import SafetyExit, MapScannerError
from map_scanner.logger_config import setup_logging


def basic_usage_example():
    """
    Basic usage example - simplest way to use the scanner.
    """
    print("=" * 60)
    print("BASIC USAGE EXAMPLE")
    print("=" * 60)

    # Setup logging
    setup_logging(level=logging.INFO)

    try:
        # Create scanner using convenience function
        scanner = create_scanner()

        # Define targets to search for
        target_names = ["PlayerName1", "PlayerName2", "[ABC]SomePlayer"]

        # Execute scan
        results = scanner.execute_scan(
            target_names=target_names,
            max_rows=15,
            test_mode=False
        )

        # Process results
        if results:
            print(f"\n✅ Found {len(results)} targets:")
            for i, target in enumerate(results, 1):
                print(f"  {i}. {target['name']} at {target['scan_position']}")
        else:
            print("\n❌ No targets found")

    except SafetyExit:
        print("\n🛑 Scanner stopped safely by user")
    except MapScannerError as e:
        print(f"\n❌ Scanner error: {e}")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")


def advanced_usage_example():
    """
    Advanced usage example with custom configuration.
    """
    print("=" * 60)
    print("ADVANCED USAGE EXAMPLE")
    print("=" * 60)

    # Setup debug logging
    setup_logging(level=logging.DEBUG, log_file="advanced_scan.log")

    try:
        # Create scanner with custom window title
        scanner = MapScanner("My Custom Game Window")

        # Initialize manually for more control
        if not scanner.initialize():
            raise MapScannerError("Failed to initialize scanner")

        # Custom calibration
        print("🔍 Performing zoom calibration...")
        if not scanner.calibrate_zoom():
            print("⚠️ Zoom calibration had issues, but continuing...")

        # Define multiple target sets
        priority_targets = ["HighValueTarget1", "HighValueTarget2"]
        secondary_targets = ["[ALLY]Friend1", "[ALLY]Friend2"]

        # Scan for priority targets first
        print("🎯 Scanning for priority targets...")
        priority_results = scanner.perform_scan(
            target_names=priority_targets,
            max_rows=20
        )

        if priority_results:
            print(f"✅ Found {len(priority_results)} priority targets!")
        else:
            print("🔍 No priority targets found, scanning for secondary targets...")
            secondary_results = scanner.perform_scan(
                target_names=secondary_targets,
                max_rows=25
            )

            if secondary_results:
                print(f"✅ Found {len(secondary_results)} secondary targets!")
            else:
                print("❌ No targets found in either scan")

    except Exception as e:
        print(f"❌ Advanced scan failed: {e}")


def test_mode_example():
    """
    Test mode example for OCR analysis and debugging.
    """
    print("=" * 60)
    print("TEST MODE EXAMPLE")
    print("=" * 60)

    # Setup detailed logging for testing
    setup_logging(level=logging.DEBUG, log_file="test_mode.log")

    try:
        # Create scanner
        scanner = create_scanner()

        print("🧪 Running OCR test mode...")

        # Run test mode to analyze OCR performance
        test_results = scanner.execute_scan(
            target_names=[],  # Empty for test mode
            test_mode=True
        )

        # Analyze test results
        if test_results:
            total_detections = sum(r['word_count'] for r in test_results)
            total_readable = sum(r['readable_words'] for r in test_results)
            avg_quality = sum(r['quality_score']
                              for r in test_results) / len(test_results)

            print(f"\n📊 TEST RESULTS SUMMARY:")
            print(f"  Screenshots analyzed: {len(test_results)}")
            print(f"  Total text detections: {total_detections}")
            print(f"  Readable words: {total_readable}")
            print(f"  Average quality score: {avg_quality:.1f}")

            if avg_quality >= 50:
                print("  ✅ OCR quality: EXCELLENT")
            elif avg_quality >= 35:
                print("  ✅ OCR quality: GOOD")
            elif avg_quality >= 25:
                print("  ⚠️ OCR quality: MARGINAL")
            else:
                print("  ❌ OCR quality: POOR")
        else:
            print("❌ Test mode failed to generate results")

    except Exception as e:
        print(f"❌ Test mode failed: {e}")


def custom_configuration_example():
    """
    Example showing how to customize scanner configuration.
    """
    print("=" * 60)
    print("CUSTOM CONFIGURATION EXAMPLE")
    print("=" * 60)

    # Create scanner with custom window title
    scanner = MapScanner("Last War: Survival Game - Custom")

    # Access configuration (read-only examples)
    print("📋 Current Configuration:")
    print(f"  Default window title: {WindowConfig.DEFAULT_WINDOW_TITLE}")
    print(f"  Max rows limit: {ScanConfig.DEFAULT_MAX_ROWS}")
    print(f"  OCR strategies available: {len(OCRConfig.OCR_STRATEGIES)}")
    print(f"  UI margins: {WindowConfig.UI_MARGINS}")

    # For actual customization, you would modify the config classes
    # or create custom subclasses (following Open/Closed Principle)

    print("\n💡 To customize configuration:")
    print("  1. Modify values in config.py classes")
    print("  2. Create custom config subclasses")
    print("  3. Pass custom parameters to scanner methods")


def batch_scanning_example():
    """
    Example of scanning for multiple target sets in batch.
    """
    print("=" * 60)
    print("BATCH SCANNING EXAMPLE")
    print("=" * 60)

    # Setup logging
    setup_logging(level=logging.INFO)

    # Define multiple target groups
    target_groups = {
        "Enemies": ["EnemyPlayer1", "EnemyPlayer2", "[EVIL]BadGuy"],
        "Allies": ["[ALLY]Friend1", "[ALLY]Friend2", "TrustedPlayer"],
        "Neutrals": ["NeutralPlayer1", "NeutralPlayer2"]
    }

    all_results = {}

    try:
        scanner = create_scanner()

        for group_name, targets in target_groups.items():
            print(f"\n🔍 Scanning for {group_name}...")

            results = scanner.execute_scan(
                target_names=targets,
                max_rows=15,
                test_mode=False
            )

            all_results[group_name] = results

            if results:
                print(f"  ✅ Found {len(results)} {group_name.lower()}")
                for target in results:
                    print(
                        f"    - {target['name']} at {target['scan_position']}")
            else:
                print(f"  ❌ No {group_name.lower()} found")

        # Summary
        total_found = sum(len(results) for results in all_results.values())
        print(f"\n📊 BATCH SCAN SUMMARY:")
        print(f"  Total targets found: {total_found}")
        for group_name, results in all_results.items():
            print(f"  {group_name}: {len(results)} found")

    except Exception as e:
        print(f"❌ Batch scanning failed: {e}")


def error_handling_example():
    """
    Example demonstrating proper error handling.
    """
    print("=" * 60)
    print("ERROR HANDLING EXAMPLE")
    print("=" * 60)

    from map_scanner.exceptions import (
        WindowError, OCRError, CaptureError,
        MovementError, CalibrationError
    )

    try:
        # Attempt to create scanner with invalid window
        scanner = MapScanner("NonExistentGameWindow")

        # This will likely fail, demonstrating error handling
        results = scanner.execute_scan(
            target_names=["TestTarget"],
            max_rows=5
        )

    except WindowError as e:
        print(f"🪟 Window Error: {e}")
        print("  💡 Suggestion: Check if the game is running and window title is correct")

    except OCRError as e:
        print(f"👁️ OCR Error: {e}")
        print("  💡 Suggestion: Ensure Tesseract is installed and properly configured")

    except CaptureError as e:
        print(f"📸 Capture Error: {e}")
        print("  💡 Suggestion: Check screen permissions and window visibility")

    except MovementError as e:
        print(f"🖱️ Movement Error: {e}")
        print("  💡 Suggestion: Ensure the game window is active and accessible")

    except CalibrationError as e:
        print(f"🔧 Calibration Error: {e}")
        print("  💡 Suggestion: Try running test mode to analyze OCR performance")

    except SafetyExit as e:
        print(f"🛑 Safety Exit: {e}")
        print("  ℹ️ This is normal when stopping the scanner safely")

    except MapScannerError as e:
        print(f"⚠️ General Scanner Error: {e}")
        print("  💡 Suggestion: Check logs for more detailed error information")

    except Exception as e:
        print(f"💥 Unexpected Error: {e}")
        print("  🐛 This might be a bug - please report with logs")


def main():
    """
    Run all examples in sequence.
    """
    examples = [
        ("Basic Usage", basic_usage_example),
        ("Test Mode", test_mode_example),
        ("Custom Configuration", custom_configuration_example),
        ("Error Handling", error_handling_example),
        # Advanced examples commented out to avoid long execution
        # ("Advanced Usage", advanced_usage_example),
        # ("Batch Scanning", batch_scanning_example),
    ]

    print("🚀 MAP SCANNER USAGE EXAMPLES")
    print("=" * 80)

    for name, example_func in examples:
        print(f"\n▶️ Running {name} Example...")
        try:
            example_func()
        except KeyboardInterrupt:
            print(f"\n⏹️ {name} example interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ {name} example failed: {e}")

        print("\n" + "─" * 60)

    print("\n✅ Examples completed!")
    print("\n💡 Tips:")
    print("  • Run individual examples by calling their functions directly")
    print("  • Check the logs for detailed information")
    print("  • Use test mode first to verify OCR performance")
    print("  • Customize configuration in config.py for your specific needs")


if __name__ == "__main__":
    main()
