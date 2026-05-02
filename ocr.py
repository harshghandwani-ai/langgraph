"""
ocr.py — Helper module for extracting text from images using PaddleOCR.

Provides a module-level singleton so the model is loaded exactly once per
server process, avoiding multi-second cold-start delays on every upload.
"""
from __future__ import annotations
import logging
from paddleocr import PaddleOCR

logger = logging.getLogger(__name__)

# ── Singleton ─────────────────────────────────────────────────────────────────
_engine: "ExpenseExtractor | None" = None


def get_engine() -> "ExpenseExtractor":
    """Return the shared OCR engine, creating it on first call."""
    global _engine
    if _engine is None:
        logger.info("[OCR] Initialising PaddleOCR engine (first call)...")
        _engine = ExpenseExtractor()
        logger.info("[OCR] Engine ready.")
    return _engine


# ── Engine class ──────────────────────────────────────────────────────────────
class ExpenseExtractor:
    def __init__(self):
        # Initialize the PaddleOCR engine once to avoid reloading it on every request.
        # use_angle_cls=True enables text-orientation correction (replaces deprecated use_textline_orientation).
        # use_gpu=False keeps this compatible with CPU-only environments.
        self.ocr_engine = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)

    def extract_raw_text(self, image_path: str) -> str:
        """
        Runs OCR on the provided image and combines all detected text into a single string.
        Returns an empty string if no text is found or an error occurs.
        Raises RuntimeError on OCR engine failure so the caller can distinguish
        between "no text" and "engine crashed".
        """
        try:
            # cls=True detects and corrects text orientation (upside-down / rotated)
            results = self.ocr_engine.ocr(image_path, cls=True)

            extracted_lines: list[str] = []

            # PaddleOCR returns a list of pages; for a single image it's results[0]
            if results and results[0]:
                for line in results[0]:
                    # Each entry: [[box_points], (text_string, confidence_score)]
                    text: str = line[1][0]
                    confidence: float = line[1][1]
                    # Skip tokens with very low confidence (likely noise)
                    if confidence >= 0.5:
                        extracted_lines.append(text)

            return "\n".join(extracted_lines)

        except Exception as exc:
            logger.error("[OCR] Engine error on %s: %s", image_path, exc)
            raise RuntimeError(f"OCR engine failed: {exc}") from exc

