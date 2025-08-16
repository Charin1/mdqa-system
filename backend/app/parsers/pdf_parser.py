import logging
import pdfplumber
from typing import List, Dict, Any

# Import our project's settings and base classes
from ..core.settings import settings
from .base import BaseParser, ParseResult

# --- Lazy-loading OCR Engine ---
# This is a best practice. It means we only import and initialize the heavy OCR library
# if and when it's actually needed, which keeps application startup fast.
_PADDLE_OCR_ENGINE = None

def _get_paddleocr():
    """Initializes and returns a memoized instance of the PaddleOCR engine."""
    global _PADDLE_OCR_ENGINE
    if _PADDLE_OCR_ENGINE is not None:
        return _PADDLE_OCR_ENGINE

    try:
        # This import can be slow, so we do it on demand.
        from paddleocr import PaddleOCR
        print("--- [INFO] Initializing PaddleOCR engine for the first time... ---")
        _PADDLE_OCR_ENGINE = PaddleOCR(use_angle_cls=True, lang=settings.PADDLEOCR_LANG, use_gpu=settings.PADDLEOCR_USE_GPU)
        print("--- [INFO] PaddleOCR engine initialized successfully. ---")
        return _PADDLE_OCR_ENGINE
    except ImportError:
        logging.warning("PaddleOCR is enabled but not installed. Please run 'pip install paddleocr paddlepaddle'. Skipping OCR.")
        return None
    except Exception as e:
        logging.error(f"Failed to initialize PaddleOCR engine: {e}")
        return None

# --- The New, Robust PDF Parser ---

class PDFParser(BaseParser):
    def parse(self, file_path: str) -> ParseResult:
        """
        Parses a PDF document, attempting to extract text directly. If no text is found
        (indicating a scanned/image-based PDF), it will use OCR as a fallback.
        
        This parser will raise exceptions for corrupt or encrypted files.
        """
        full_text_parts = []
        doc_metadata = {}

        with pdfplumber.open(file_path) as pdf:
            doc_metadata = {
                "title": pdf.metadata.get("Title"),
                "author": pdf.metadata.get("Author"),
                "page_count": len(pdf.pages),
            }

            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                
                # 1. First, try the fast, direct text extraction
                text = page.extract_text() or ""
                
                # 2. If no text is found and OCR is enabled, use OCR as a fallback
                if not text.strip() and settings.OCR_ENABLED:
                    logging.info(f"Page {page_num} of '{file_path}' contains no text. Attempting OCR...")
                    ocr_engine = _get_paddleocr()
                    if ocr_engine:
                        try:
                            # Convert page to an image for OCR
                            img = page.to_image(resolution=300).original
                            
                            # Run OCR and extract text
                            result = ocr_engine.ocr(img, cls=True)
                            if result and result[0] is not None:
                                # The result is a list of lines, where each line has text and confidence.
                                # We extract just the text for each line.
                                line_texts = [line[1][0] for line in result[0]]
                                text = "\n".join(line_texts)
                                logging.info(f"Successfully extracted {len(line_texts)} lines of text via OCR from page {page_num}.")
                            else:
                                logging.warning(f"OCR run on page {page_num} but returned no results.")
                        except Exception as e:
                            logging.error(f"Error during OCR on page {page_num}: {e}")
                            # If OCR fails, we just fall back to the empty text
                
                full_text_parts.append(text)

        final_text = "\n\n".join(full_text_parts).strip()
        if not final_text:
            logging.warning(f"PDF '{file_path}' resulted in zero extractable text after parsing and OCR attempts.")

        return ParseResult(text=final_text, metadata=doc_metadata)