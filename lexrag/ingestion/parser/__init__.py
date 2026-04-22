"""Parser package public exports.

This package provides a comprehensive document parsing system for the LexRAG
project. It includes multiple parser implementations with fallback strategies
to handle various document formats including PDF, HTML, and more.

Key components:
    - BaseDocumentParser: Abstract base class for all parsers
    - DoclingParser: Primary parser using the Docling library
    - PyMuPDFParser: Fallback parser for PDF and HTML files
    - FallbackDocumentParser: Orchestrator with primary/fallback logic
    - ParsedPage: Data model for parsed content
    - parse_document: Convenience function for common use cases

The package is designed to be robust, with multiple fallback strategies to
ensure maximum document parsing coverage while maintaining high quality
results.
"""

from .parsed_block import ParsedBlock
from .base_document_parser import BaseDocumentParser
from .docling_parser import DoclingParser
from .pymupdf_parser import PyMuPDFParser
from .fallback_document_parser import FallbackDocumentParser


__all__ = [
    "BaseDocumentParser",
    "DoclingParser",
    "FallbackDocumentParser",
    "PyMuPDFParser",
    "ParsedBlock",
]
