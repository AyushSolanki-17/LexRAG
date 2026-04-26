"""Canonical parser schemas and DTOs."""

from __future__ import annotations

from .document_parse_result import DocumentParseResult
from .file_type_detection import FileTypeDetection
from .file_validation_result import FileValidationResult
from .parse_attempt import ParseAttempt
from .parsed_block import ParsedBlock
from .parsed_page import ParsedPage
from .parser_config import ParserConfig
from .parser_selection import ParserSelection

__all__ = [
    "DocumentParseResult",
    "FileTypeDetection",
    "FileValidationResult",
    "ParseAttempt",
    "ParsedBlock",
    "ParsedPage",
    "ParserConfig",
    "ParserSelection",
]
