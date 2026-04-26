"""Backend registry for parser orchestration."""

from __future__ import annotations

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
        self._parsers = {
            "docling": primary_parser or DoclingParser(),
            "pymupdf": fallback_parser or PyMuPDFParser(),
            "unstructured": unstructured_parser or UnstructuredParser(),
            "ocr_only": ocr_parser or OCROnlyParser(),
            "manual_recovery": manual_recovery_parser or ManualRecoveryParser(),
        }

    def get(self, parser_name: str) -> BaseDocumentParser | Any:
        """Return the parser backend registered under ``parser_name``."""
        return self._parsers[parser_name]
