"""
OCR Engine module for text extraction and image preprocessing.

Handles all OCR-related operations following Single Responsibility Principle.
"""

from typing import Dict, Any, List
import numpy as np
import cv2
import pytesseract
from PIL import Image, ImageEnhance

from .config import OCRConfig
from .exceptions import OCRError
from .logger_config import get_logger
from .utils import calculate_quality_score

logger = get_logger(__name__)


class ImagePreprocessor:
    """Handles image preprocessing for optimal OCR results."""

    @staticmethod
    def preprocess_for_game_text(image: np.ndarray) -> Image.Image:
        """Specialized preprocessing for game text with white text and black outlines."""
        try:
            # Convert numpy array to PIL Image
            if len(image.shape) == 3:
                pil_img = Image.fromarray(
                    cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            else:
                pil_img = Image.fromarray(image)

            # Convert to OpenCV format for advanced processing
            cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

            # Convert to LAB color space for better text separation
            lab = cv2.cvtColor(cv_img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)

            # Enhance the L channel (lightness) for better text contrast
            clahe = cv2.createCLAHE(
                clipLimit=OCRConfig.CLAHE_CLIP_LIMIT,
                tileGridSize=OCRConfig.CLAHE_TILE_GRID_SIZE
            )
            l = clahe.apply(l)

            # Merge back and convert to BGR
            enhanced_lab = cv2.merge([l, a, b])
            cv_img = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

            # Convert to grayscale
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

            # Apply morphological operations to enhance text
            kernel = np.ones(OCRConfig.MORPHOLOGY_KERNEL_SIZE, np.uint8)
            gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

            # Bilateral filter to reduce noise while preserving edges
            gray = cv2.bilateralFilter(
                gray, *OCRConfig.BILATERAL_FILTER_PARAMS)

            # Adaptive threshold for better text separation
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 15, 3
            )

            # Clean up with morphological operations
            kernel_clean = np.ones((1, 1), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_clean)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_clean)

            return Image.fromarray(binary)

        except Exception as e:
            logger.error(f"Error in game text preprocessing: {e}")
            return Image.fromarray(image) if isinstance(image, np.ndarray) else image

    @staticmethod
    def preprocess_white_text_black_outline(image: np.ndarray) -> Image.Image:
        """Specialized preprocessing for white text with black outlines."""
        try:
            # Convert numpy array to PIL Image
            if len(image.shape) == 3:
                pil_img = Image.fromarray(
                    cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            else:
                pil_img = Image.fromarray(image)

            # Convert to OpenCV format
            cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

            # Convert to HSV for better color separation
            hsv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)

            # Enhance contrast in the value channel
            v = cv2.equalizeHist(v)

            # Merge back
            hsv_enhanced = cv2.merge([h, s, v])
            cv_img = cv2.cvtColor(hsv_enhanced, cv2.COLOR_HSV2BGR)

            # Convert to grayscale
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

            # Apply Gaussian blur to smooth out the black outlines
            gray_blurred = cv2.GaussianBlur(
                gray, OCRConfig.GAUSSIAN_BLUR_KERNEL, 0)

            # Use Otsu's threshold to separate text from background
            _, binary = cv2.threshold(
                gray_blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

            # Morphological operations to clean up
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            return Image.fromarray(binary)

        except Exception as e:
            logger.error(f"Error in white text preprocessing: {e}")
            return Image.fromarray(image) if isinstance(image, np.ndarray) else image

    @classmethod
    def preprocess_image(cls, image: np.ndarray, strategy: str = 'default') -> Image.Image:
        """Apply image preprocessing based on strategy."""
        try:
            # Convert numpy array to PIL Image
            if len(image.shape) == 3:
                pil_img = Image.fromarray(
                    cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            else:
                pil_img = Image.fromarray(image)

            if strategy == 'game_text':
                return cls.preprocess_for_game_text(image)
            elif strategy == 'white_text_outline':
                return cls.preprocess_white_text_black_outline(image)
            elif strategy == 'enhanced_contrast':
                pil_img = pil_img.convert('L')
                enhancer = ImageEnhance.Contrast(pil_img)
                pil_img = enhancer.enhance(1.8)
            elif strategy == 'high_contrast':
                pil_img = pil_img.convert('L')
                enhancer = ImageEnhance.Contrast(pil_img)
                pil_img = enhancer.enhance(2.0)
                pil_img = pil_img.point(lambda x: 0 if x < 128 else 255, '1')
            elif strategy == 'sharp_text':
                enhancer = ImageEnhance.Sharpness(pil_img)
                pil_img = enhancer.enhance(2.0)
                enhancer = ImageEnhance.Contrast(pil_img)
                pil_img = enhancer.enhance(1.5)
            elif strategy == 'denoise':
                cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                cv_img = cv2.bilateralFilter(
                    cv_img, *OCRConfig.BILATERAL_FILTER_PARAMS)
                pil_img = Image.fromarray(
                    cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
            elif strategy == 'upscale':
                width, height = pil_img.size
                pil_img = pil_img.resize(
                    (width * 3, height * 3), Image.Resampling.LANCZOS
                )
            elif strategy == 'upscale_sharp':
                width, height = pil_img.size
                pil_img = pil_img.resize(
                    (width * 4, height * 4), Image.Resampling.LANCZOS
                )
                enhancer = ImageEnhance.Sharpness(pil_img)
                pil_img = enhancer.enhance(2.5)

            return pil_img

        except Exception as e:
            logger.error(f"Error in image preprocessing: {e}")
            return Image.fromarray(image) if isinstance(image, np.ndarray) else image


class OCREngine:
    """Main OCR engine for text extraction and recognition."""

    def __init__(self):
        """Initialize OCR engine with verification."""
        self.preprocessor = ImagePreprocessor()
        self._verify_tesseract()

    def _verify_tesseract(self) -> bool:
        """Verify Tesseract OCR is properly installed."""
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract OCR version: {version}")
            return True
        except Exception as e:
            error_msg = f"Tesseract OCR not properly installed: {e}"
            logger.error(error_msg)
            logger.error(
                "Please install Tesseract OCR: "
                "https://github.com/UB-Mannheim/tesseract/wiki"
            )
            raise OCRError(error_msg)

    def extract_text_comprehensive(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract text using multiple OCR strategies optimized for game text."""
        results = {
            'texts': [],
            'confidences': [],
            'best_text': '',
            'best_confidence': 0,
            'all_detections': []
        }

        try:
            for preprocess_strategy, ocr_config in OCRConfig.OCR_STRATEGIES:
                try:
                    # Preprocess image
                    processed_img = self.preprocessor.preprocess_image(
                        image, preprocess_strategy
                    )

                    # Extract text with confidence
                    config = OCRConfig.TESSERACT_CONFIGS[ocr_config]
                    ocr_data = pytesseract.image_to_data(
                        processed_img,
                        config=config,
                        output_type=pytesseract.Output.DICT
                    )

                    # Process OCR results
                    strategy_texts, strategy_confidences = self._process_ocr_data(
                        ocr_data, preprocess_strategy, ocr_config, results
                    )

                    # Combine all text from this strategy
                    if strategy_texts:
                        combined_text = ' '.join(strategy_texts)
                        avg_confidence = np.mean(strategy_confidences)

                        results['texts'].append(combined_text)
                        results['confidences'].append(avg_confidence)

                        if avg_confidence > results['best_confidence']:
                            results['best_confidence'] = avg_confidence
                            results['best_text'] = combined_text

                        logger.debug(
                            f"OCR Strategy '{preprocess_strategy}' + '{ocr_config}' "
                            f"found: '{combined_text}' (conf: {avg_confidence:.1f})"
                        )

                except Exception as e:
                    logger.debug(
                        f"OCR strategy '{preprocess_strategy}' + '{ocr_config}' "
                        f"failed: {e}"
                    )
                    continue

            # Final cleanup of best text
            if results['best_text']:
                results['best_text'] = ' '.join(results['best_text'].split())

            return results

        except Exception as e:
            logger.error(f"Comprehensive OCR extraction failed: {e}")
            return results

    def _process_ocr_data(
        self,
        ocr_data: Dict,
        preprocess_strategy: str,
        ocr_config: str,
        results: Dict[str, Any]
    ) -> tuple[List[str], List[float]]:
        """Process OCR data and extract valid text."""
        strategy_texts = []
        strategy_confidences = []

        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()
            confidence = int(ocr_data['conf'][i])

            # Lower confidence threshold for game text
            if (len(text) >= OCRConfig.MIN_TEXT_LENGTH and
                    confidence > OCRConfig.MIN_CONFIDENCE_THRESHOLD):

                strategy_texts.append(text)
                strategy_confidences.append(confidence)

                results['all_detections'].append({
                    'text': text,
                    'confidence': confidence,
                    'strategy': preprocess_strategy,
                    'config': ocr_config,
                    'height': ocr_data['height'][i],
                    'width': ocr_data['width'][i]
                })

        return strategy_texts, strategy_confidences

    def evaluate_quality(self, image: np.ndarray) -> tuple[float, Dict[str, Any]]:
        """Evaluate OCR quality with enhanced game text focus."""
        try:
            if image is None:
                return 0.0, {'error': 'No image provided'}

            ocr_results = self.extract_text_comprehensive(image)

            if not ocr_results['all_detections']:
                return 0.0, {'error': 'No text detected', 'ocr_results': ocr_results}

            # Calculate quality metrics
            confidences = [det['confidence']
                           for det in ocr_results['all_detections']]
            heights = [det['height'] for det in ocr_results['all_detections']]

            avg_confidence = np.mean(confidences)
            avg_height = np.mean(heights)
            text_count = len(ocr_results['all_detections'])

            # Look for actual readable words (game names/alliance tags)
            readable_words = sum(
                1 for det in ocr_results['all_detections']
                if len(det['text'].strip()) >= 3 and
                any(c.isalpha() for c in det['text'])
            )

            # Calculate quality score
            from .config import ScanConfig
            overall_quality = calculate_quality_score(
                avg_confidence, avg_height, text_count, readable_words,
                ScanConfig.QUALITY_WEIGHTS
            )

            quality_info = {
                'overall_quality': overall_quality,
                'avg_confidence': avg_confidence,
                'avg_height': avg_height,
                'text_count': text_count,
                'readable_words': readable_words,
                'detected_texts': [
                    det['text'] for det in ocr_results['all_detections'][:5]
                ],
                'ocr_results': ocr_results
            }

            return overall_quality, quality_info

        except Exception as e:
            logger.error(f"OCR quality evaluation failed: {e}")
            return 0.0, {'error': str(e)}
