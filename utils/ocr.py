"""OCR utilities exposed under the utils package."""

from ocr import (
    extract_text,
    extract_text_from_image,
    extract_text_from_pdf,
    get_ocr_status,
)

__all__ = [
    "extract_text",
    "extract_text_from_image",
    "extract_text_from_pdf",
    "get_ocr_status",
]
