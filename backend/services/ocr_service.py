"""
OCR Service
-----------
Provides OCR (Optical Character Recognition) fallback for scanned or
image-only PDF pages, i.e. pages where pypdf's text-layer extraction
returns nothing usable.

Two system-level dependencies are required (these are NOT pip packages,
they must be installed on the machine / container separately):

1. Tesseract OCR engine
   - Windows: https://github.com/UB-Mannheim/tesseract/wiki
   - macOS:   brew install tesseract
   - Ubuntu:  sudo apt-get install tesseract-ocr

2. Poppler (needed by pdf2image to rasterize PDF pages)
   - Windows: https://github.com/oschwartz10612/poppler-windows/releases
     (add the extracted "bin" folder to PATH)
   - macOS:   brew install poppler
   - Ubuntu:  sudo apt-get install poppler-utils

See backend/OCR_SETUP.md for full setup instructions.
"""

import io
import logging
from typing import List, Dict, Optional

from PIL import Image, ImageOps
import pytesseract
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)


class OCRService:
    """
    Handles OCR extraction for PDF pages that have no (or very little)
    extractable text layer.
    """

    # If pypdf's extracted text for a page is shorter than this,
    # we treat the page as "image-only" and OCR it instead.
    MIN_TEXT_LENGTH = 20

    # DPI used when rasterizing PDF pages to images before OCR.
    # Higher = more accurate but slower. 300 is a good default for
    # financial documents with small print / tables.
    RENDER_DPI = 300

    # Tesseract language(s). Add more with '+', e.g. "eng+fra".
    OCR_LANGUAGES = "eng"

    @classmethod
    def needs_ocr(cls, extracted_text: str) -> bool:
        """
        Decide whether a page's pypdf-extracted text is usable, or
        whether the page should be sent through OCR instead.
        """
        if not extracted_text:
            return True

        return len(extracted_text.strip()) < cls.MIN_TEXT_LENGTH

    @classmethod
    def _preprocess_image(cls, image: Image.Image) -> Image.Image:
        """
        Lightweight preprocessing to improve OCR accuracy:
        - convert to grayscale
        - auto-contrast
        No heavy CV dependencies (opencv, numpy pipelines) are used,
        to keep this in line with the project's existing footprint.
        """
        gray = image.convert("L")
        return ImageOps.autocontrast(gray)

    @classmethod
    def ocr_page_image(cls, image: Image.Image) -> str:
        """
        Run Tesseract OCR on a single PIL image and return cleaned text.
        """
        processed = cls._preprocess_image(image)

        text = pytesseract.image_to_string(
            processed,
            lang=cls.OCR_LANGUAGES,
        )

        return text.strip()

    @classmethod
    def extract_pages(
        cls,
        file_path: str,
        page_numbers: List[int],
    ) -> Dict[int, str]:
        """
        OCR only the given 1-indexed page numbers of a PDF.

        Rendering is restricted to the required page range for
        efficiency (a scanned 100-page annual report shouldn't force
        us to rasterize every page if only a handful actually need OCR).

        Returns:
            { page_number: ocr_text }
        """
        if not page_numbers:
            return {}

        results: Dict[int, str] = {}

        first_page = min(page_numbers)
        last_page = max(page_numbers)

        try:
            images = convert_from_path(
                file_path,
                dpi=cls.RENDER_DPI,
                first_page=first_page,
                last_page=last_page,
            )
        except Exception as exc:
            logger.error("OCR rendering failed for %s: %s", file_path, exc)
            raise RuntimeError(
                f"Could not rasterize PDF pages for OCR: {exc}"
            )

        wanted = set(page_numbers)

        for offset, image in enumerate(images):
            current_page = first_page + offset

            if current_page not in wanted:
                continue

            try:
                text = cls.ocr_page_image(image)
            except Exception as exc:
                logger.error(
                    "OCR failed on page %s of %s: %s",
                    current_page, file_path, exc
                )
                text = ""

            results[current_page] = text

        return results

    @classmethod
    def extract_full_document(cls, file_path: str, page_count: int) -> Dict[int, str]:
        """
        OCR every page of a document. Used when the PDF has no text
        layer at all (fully scanned document).
        """
        all_pages = list(range(1, page_count + 1))
        return cls.extract_pages(file_path, all_pages)