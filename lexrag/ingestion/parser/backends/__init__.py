"""Parser backend implementations."""

from __future__ import annotations

from .docling_backend import DoclingParser
from .ocr_only_backend import OCROnlyParser

__all__ = ["DoclingParser", "OCROnlyParser"]
