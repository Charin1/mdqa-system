import logging
import pdfplumber
from typing import List, Dict, Any

from ..core.settings import settings
from .base import BaseParser, ParseResult

# --- Lazy-loading OCR Engine ---
_PADDLE_OCR_ENGINE = None

def _get_paddleocr():
    """Initializes and returns a memoized instance of the PaddleOCR engine."""
    global _PADDLE_OCR_ENGINE
    if _PADDLE_OCR_ENGINE is not None:
        return _PADDLE_OCR_ENGINE

    try:
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

# --- The PDF Parser (Final Version) ---
class PDFParser(BaseParser):
    def parse(self, file_path: str) -> ParseResult:
        full_text_parts = []
        doc_metadata = {}
        pages_metadata_list = [] # A list to hold metadata for each page

        with pdfplumber.open(file_path) as pdf:
            doc_metadata = {
                "title": pdf.metadata.get("Title"),
                "author": pdf.metadata.get("Author"),
                "page_count": len(pdf.pages),
            }

            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                text = page.extract_text() or ""
                
                if not text.strip() and settings.OCR_ENABLED:
                    logging.info(f"Page {page_num} of '{file_path}' contains no text. Attempting OCR...")
                    ocr_engine = _get_paddleocr()
                    if ocr_engine:
                        try:
                            img = page.to_image(resolution=300).original
                            result = ocr_engine.ocr(img, cls=True)
                            if result and result[0] is not None:
                                line_texts = [line[1][0] for line in result[0]]
                                text = "\n".join(line_texts)
                                logging.info(f"Successfully extracted {len(line_texts)} lines of text via OCR from page {page_num}.")
                            else:
                                logging.warning(f"OCR run on page {page_num} but returned no results.")
                        except Exception as e:
                            logging.error(f"Error during OCR on page {page_num}: {e}")
                
                full_text_parts.append(text)
                # Store this page's specific metadata
                pages_metadata_list.append({
                    "text": text,
                    "page_number": page_num
                })

        final_text = "\n\n".join(full_text_parts).strip()
        doc_metadata["pages"] = pages_metadata_list

        return ParseResult(text=final_text, metadata=doc_metadata)