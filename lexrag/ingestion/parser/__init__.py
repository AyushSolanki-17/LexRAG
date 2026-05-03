"""Production-grade document parsing package."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .backends.docling_backend import DoclingParser
from .backends.ocr_only_backend import OCROnlyParser
from .base_document_parser import BaseDocumentParser
from .builders import ParsedBlockBuilder
from .docling import (
    DoclingConverterFactory,
    DoclingPipelineOptionsFactory,
    DoclingResultNormalizer,
    DoclingRuntime,
)
from .document_parser_protocol import DocumentParserProtocol
from .loaded_document_parser_pipeline import LoadedDocumentParserPipeline
from .manual_recovery_required_error import ManualRecoveryRequiredError
from .ocr import (
    OCRExtractor,
    OcrRuntimeValidator,
    PdfPageRasterizer,
    TesseractOCRExtractor,
)
from .orchestration import (
    DocumentParser,
    ParserBackendRegistry,
    ParserChainExecutor,
)
from .pymupdf_parser import PyMuPDFParser
from .schemas import (
    DoclingAcceleratorConfig,
    DoclingAcceleratorDevice,
    DoclingConfig,
    DoclingOcrConfig,
    DoclingOcrEngine,
    DoclingTableMode,
    DocumentParseResult,
    LoadedDocumentParseResult,
    LoadedDocumentParseStatus,
    OCRTextBlock,
    ParseAttempt,
    ParsedBlock,
    ParsedPage,
    ParserBackend,
    ParserConfig,
    ParserOcrConfig,
    ParserOcrEngine,
    ParserPdfRoutingConfig,
    ParserSelection,
    RasterizedPage,
)
from .unstructured_parser import UnstructuredParser


def parse_document(path: str | Path) -> list[dict[str, Any]]:
    """Parse a document and return the legacy dictionary payload shape."""
    parser = DocumentParser()
    blocks = parser.parse_document(path)
    return [_block_to_legacy_dict(block) for block in blocks]


def _block_to_legacy_dict(block: ParsedBlock) -> dict[str, Any]:
    return {
        "page": block.page,
        "section": block.section,
        "text": block.text,
        "metadata": dict(block.metadata),
    }


__all__ = [
    "BaseDocumentParser",
    "DoclingAcceleratorConfig",
    "DoclingAcceleratorDevice",
    "DoclingConfig",
    "DoclingConverterFactory",
    "DoclingOcrConfig",
    "DoclingOcrEngine",
    "DoclingParser",
    "DoclingPipelineOptionsFactory",
    "DoclingResultNormalizer",
    "DoclingRuntime",
    "DoclingTableMode",
    "DocumentParseResult",
    "DocumentParser",
    "DocumentParserProtocol",
    "LoadedDocumentParserPipeline",
    "LoadedDocumentParseResult",
    "LoadedDocumentParseStatus",
    "ManualRecoveryRequiredError",
    "OCRExtractor",
    "OCROnlyParser",
    "OCRTextBlock",
    "OcrRuntimeValidator",
    "ParseAttempt",
    "ParsedBlock",
    "ParsedBlockBuilder",
    "ParsedPage",
    "ParserBackend",
    "ParserBackendRegistry",
    "ParserChainExecutor",
    "ParserConfig",
    "ParserOcrConfig",
    "ParserOcrEngine",
    "ParserPdfRoutingConfig",
    "ParserSelection",
    "PdfPageRasterizer",
    "PyMuPDFParser",
    "RasterizedPage",
    "TesseractOCRExtractor",
    "UnstructuredParser",
    "parse_document",
]
