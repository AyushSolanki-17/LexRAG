"""Canonical parser schemas and DTOs."""

from __future__ import annotations

from .document_parse_result import DocumentParseResult
from .file_parse_result import FileParseResult
from .ocr_text_block import OCRTextBlock
from .parse_attempt import ParseAttempt
from .parsed_block import ParsedBlock
from .parsed_page import ParsedPage
from .parser_config import ParserConfig
from .parser_selection import ParserSelection
from .rasterized_page import RasterizedPage

__all__ = [
    "DocumentParseResult",
    "FileParseResult",
    "OCRTextBlock",
    "ParseAttempt",
    "ParsedBlock",
    "ParsedPage",
    "ParserConfig",
    "ParserSelection",
    "RasterizedPage",
]
