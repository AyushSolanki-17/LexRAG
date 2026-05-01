"""Production-grade document parsing package.

This package implements the parsing stages described in
``docs/architecture.md``:

1. File validation
2. File type detection
3. Parser selection
4. Deterministic fallback execution
5. Provenance annotation

The public surface stays small on purpose. Most callers only need
``FallbackDocumentParser`` and ``ParsedBlock``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base_document_parser import BaseDocumentParser
from .docling_parser import DoclingParser
from .document_parser import FallbackDocumentParser
from .document_parser_protocol import DocumentParserProtocol
from .manual_recovery_required_error import ManualRecoveryRequiredError
from .pymupdf_parser import PyMuPDFParser
from .schemas import (
    DocumentParseResult,
    ParseAttempt,
    ParsedBlock,
    ParsedPage,
    ParserConfig,
    ParserSelection,
)
from .unstructured_parser import UnstructuredParser


def parse_document(path: str | Path) -> list[dict[str, Any]]:
    """Parse a document and return the legacy dictionary payload shape.

    Args:
        path: Path to the document to parse.

    Returns:
        A list of dictionaries kept for legacy callers that have not yet
        migrated to ``ParsedBlock``.
    """
    parser = FallbackDocumentParser()
    blocks = parser.parse_document(path)
    return [_block_to_legacy_dict(block) for block in blocks]


def _block_to_legacy_dict(block: ParsedBlock) -> dict[str, Any]:
    """Convert a parsed block into the historic dictionary contract."""
    return {
        "page": block.page,
        "section": block.section,
        "text": block.text,
        "metadata": dict(block.metadata),
    }


__all__ = [
    "BaseDocumentParser",
    "DoclingParser",
    "DocumentParseResult",
    "DocumentParserProtocol",
    "FallbackDocumentParser",
    "ManualRecoveryRequiredError",
    "ParseAttempt",
    "ParsedBlock",
    "ParsedPage",
    "ParserConfig",
    "ParserSelection",
    "PyMuPDFParser",
    "UnstructuredParser",
    "parse_document",
]
