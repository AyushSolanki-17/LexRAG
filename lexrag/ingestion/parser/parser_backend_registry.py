"""Backend registry for parser orchestration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from lexrag.ingestion.parser.base_document_parser import BaseDocumentParser
from lexrag.ingestion.parser.docling_parser import DoclingParser
from lexrag.ingestion.parser.manual_recovery_parser import ManualRecoveryParser
from lexrag.ingestion.parser.ocr_only_parser import OCROnlyParser
from lexrag.ingestion.parser.pymupdf_parser import PyMuPDFParser
from lexrag.ingestion.parser.unstructured_parser import UnstructuredParser


class ParserBackendRegistry:
    """Provide parser backends by stable routing name."""

    def __init__(
        self,
        *,
        primary_parser: BaseDocumentParser | Any | None = None,
        fallback_parser: BaseDocumentParser | Any | None = None,
        unstructured_parser: BaseDocumentParser | Any | None = None,
        ocr_parser: BaseDocumentParser | Any | None = None,
        manual_recovery_parser: BaseDocumentParser | Any | None = None,
    ) -> None:
        """Initialize the parser backend registry.

        Args:
            primary_parser: Optional override for the Docling backend.
            fallback_parser: Optional override for the PyMuPDF backend.
            unstructured_parser: Optional override for the unstructured backend.
            ocr_parser: Optional override for the OCR backend.
            manual_recovery_parser: Optional override for the manual recovery backend.
        """
        self._provided_parsers = {
            "docling": primary_parser,
            "pymupdf": fallback_parser,
            "unstructured": unstructured_parser,
            "ocr_only": ocr_parser,
            "manual_recovery": manual_recovery_parser,
        }
        self._parser_factories = self._build_factories()
        self._parsers: dict[str, BaseDocumentParser | Any] = {}

    def get(self, parser_name: str) -> BaseDocumentParser | Any:
        """Return the parser backend registered under ``parser_name``."""
        parser = self._parsers.get(parser_name)
        if parser is not None:
            return parser
        parser = self._build_parser(parser_name=parser_name)
        self._parsers[parser_name] = parser
        return parser

    def _build_factories(self) -> dict[str, Callable[[], BaseDocumentParser | Any]]:
        return {
            "docling": DoclingParser,
            "pymupdf": PyMuPDFParser,
            "unstructured": UnstructuredParser,
            "ocr_only": OCROnlyParser,
            "manual_recovery": ManualRecoveryParser,
        }

    def _build_parser(self, *, parser_name: str) -> BaseDocumentParser | Any:
        provided = self._provided_parsers.get(parser_name)
        if provided is not None:
            return provided
        factory = self._parser_factories[parser_name]
        return factory()
