"""Docling-based parser implementation.

    This module provides a document parser implementation using the Docling library,
    which offers advanced document parsing capabilities for various formats including
    PDF, Word, HTML, and more. The parser converts documents to Markdown format
    and then splits them into normalized page objects.

    Features:
    - OCR support for scanned PDFs + images
    - Native PDF parsing + hybrid OCR fallback
    - Table extraction enabled
    - Image/document format support
    - Markdown + text fallback extraction
    - Metadata preservation
    - Safe exception handling
    - Observability-ready structure
    - Clean page normalization pipeline
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Set
from uuid import uuid4

from docling.document_converter import DocumentConverter
from pydantic_settings import BaseSettings

from lexrag.ingestion.parser import BaseDocumentParser, ParsedBlock
from lexrag.utils import get_logger

logger = get_logger(__name__)

class DoclingParser(BaseDocumentParser):
    """Primary parser backend that uses Docling for document parsing.

    This parser serves as the primary document parsing backend in the LexRAG
    system. It leverages the Docling library to convert various document formats
    into structured Markdown content, which is then processed into ParsedPage
    objects. The parser handles document conversion, Markdown extraction,
    and page segmentation automatically.

    Attributes:
        converter: The Docling DocumentConverter instance used for parsing.

    Raises:
        RuntimeError: If the Docling library is not installed or available.

    Supports:
        - PDF
        - DOCX
        - PPTX
        - XLSX
        - HTML
        - Markdown
        - TXT
        - PNG / JPG / TIFF (OCR)
        - scanned PDFs

    Strategy:
        1. Native extraction when possible
        2. OCR fallback when required
        3. Markdown export preferred
        4. Text fallback if Markdown unavailable
        5. Normalize output into ParsedPage objects
    """

    SUPPORTED_IMAGE_EXTENSIONS: Set[str] = {
        ".png",
        ".jpg",
        ".jpeg",
        ".tiff",
        ".tif",
        ".bmp",
        ".webp",
    }

    converter: DocumentConverter

    def __init__(self, settings: BaseSettings | None = None):
        """Initializes the DoclingParser with a DocumentConverter instance and settings.

            Raises:
                RuntimeError: If the Docling library is not installed or cannot be
                    imported. This ensures the parser fails fast if dependencies
                    are missing.
        """
        try:
            from docling.document_converter import DocumentConverter
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.datamodel.base_models import InputFormat
            from docling.document_converter import PdfFormatOption
        except Exception as exc:
            raise RuntimeError(
                "Docling is not installed. Install with required OCR extras."
            ) from exc

        self.settings = settings

        # Production PDF pipeline config
        pdf_options = PdfPipelineOptions()

        # Enable OCR for scanned PDFs + image-heavy docs
        pdf_options.do_ocr = True

        # Enable table extraction
        pdf_options.do_table_structure = True

        # Better structured parsing
        pdf_options.table_structure_options.do_cell_matching = True

        # Keep images referenced in output
        pdf_options.generate_page_images = False

        # Build converter with per-format config
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pdf_options
                )
            }
        )

    def parse(self, path: Path) -> list[ParsedBlock]:
        """Parses a document using the Docling parsing stack.

        This method orchestrates the complete parsing process by:
        1. Converting the document using Docling's DocumentConverter
        2. Extracting structured content from the Docling document object
        3. Falling back to Markdown/text extraction when required
        4. Normalizing output into ParsedBlock objects

        Args:
            path: The file system path to the document to be parsed.

        Returns:
            A list of ParsedBlock objects, each containing page number,
            section name, and extracted text content.

        Raises:
            RuntimeError: If Docling fails to parse the document or returns
                empty content.
        """
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        result = self._convert(path)

        return self._normalize_blocks(result, path)

    def _convert(self, path: Path):
        """Converts a document using Docling's DocumentConverter.

        Args:
            path: The file system path to the document to convert.

        Returns:
            The Docling conversion result object containing the parsed document.

        Raises:
            RuntimeError: If the Docling converter fails to process the document.
                This can happen due to unsupported formats, corrupted files,
                or internal Docling errors.
        """
        try:
            return self.converter.convert(str(path))
        except Exception as exc:
            raise RuntimeError(f"docling failed to parse {path}") from exc

    def _extract_content(self, result: Any, path: Path) -> str:
        """Extracts the best content from a Docling conversion result.
        This method attempts to extract text content from the Docling result using multiple fallback strategies:

            1. Try to export as Markdown if available
            2. Fall back to plain text extraction
            3. Validate that content was actually extracted

        Args:
            result: The Docling conversion result object.
            path: The original file path for error reporting.

        Returns: The extracted Markdown content as a string.
        Raises:
            RuntimeError: If no content can be extracted from the result, indicating either an empty document or extraction failure.
        """
        if not hasattr(result, "document"):
            raise RuntimeError(f"No parsed document returned by Docling for: {path}")
        document = result.document
        content = ""
        # Preferred: structured Markdown
        if hasattr(document, "export_to_markdown"):
            try:
                content = str(document.export_to_markdown()).strip()
            except Exception as exc:
                logger.warning("Failed to extract content from Docling Markdown for: %s", exc)
        # Fallback: plain text
        if not content and hasattr(document, "text"):
            try:
                content = str(document.text).strip()
            except Exception as exc:
                logger.warning("Failed to extract content from Docling plain text for: %s", exc)
        # Last fallback
        if not content:
            try:
                content = str(document).strip()
            except Exception as exc: logger.warning("Failed to extract content from Docling content for: %s", exc)
        if not content:
            raise RuntimeError(f"Empty output returned by Docling for: {path}")
        return content

    def _normalize_blocks(
            self,
            result: Any,
            path: Path,
    ) -> list[ParsedBlock]:
        """Converts parser output content into a list of ParsedBlock objects.

        This method prioritizes structured extraction directly from the
        Docling document object before falling back to Markdown and page-level
        normalization.

        Extraction priority:
        1. Structured Docling blocks
        2. Heading-aware Markdown sections
        3. Page-level fallback using form-feed delimiters

        Args:
            result: The Docling conversion result object.
            path: The file system path to the document to be parsed.

        Returns:
            A list of ParsedBlock objects with structural metadata,
            semantic section awareness, and page traceability.
        """
        if not hasattr(result, "document"):
            raise RuntimeError(
                f"No parsed document returned by Docling for: {path}"
            )

        document = result.document
        blocks: list[ParsedBlock] = []

        # Priority 1: Structured Docling extraction
        if hasattr(document, "iterate_items"):
            order = 0

            try:
                for item, level in document.iterate_items():
                    text = ""

                    if hasattr(item, "text"):
                        text = str(item.text).strip()

                    if not text:
                        continue

                    order += 1

                    block_type = self._detect_block_type(item)
                    section = self._resolve_section(item)
                    heading_level = self._resolve_heading_level(item)

                    blocks.append(
                        ParsedBlock(
                            block_id=str(uuid4()),
                            page=getattr(item, "page_no", 1),
                            section=section,
                            heading_level=heading_level,
                            block_type=block_type,
                            text=text,
                            markdown=text,
                            bbox=getattr(item, "bbox", None),
                            order_in_page=order,
                            is_ocr=False,
                            confidence=getattr(item, "confidence", None),
                            parent_section_path=[],
                            metadata={
                                "source_file": path.name,
                                "source_path": str(path),
                                "parser": "docling",
                                "extraction_mode": "structured",
                            },
                        )
                    )
            except Exception as exc:
                logger.warning(
                    "Structured Docling extraction failed for %s: %s",
                    path,
                    exc,
                )

        # Priority 2: Markdown fallback
        if not blocks:
            content = self._extract_content(result, path)

            markdown_chunks = [
                chunk.strip()
                for chunk in content.split("\n## ")
                if chunk.strip()
            ]

            if markdown_chunks:
                for idx, chunk in enumerate(markdown_chunks, start=1):
                    blocks.append(
                        ParsedBlock(
                            block_id=str(uuid4()),
                            page=idx,
                            section=f"Section {idx}",
                            heading_level=2,
                            block_type="section",
                            text=chunk,
                            markdown=chunk,
                            bbox=None,
                            order_in_page=idx,
                            is_ocr=False,
                            confidence=None,
                            parent_section_path=[],
                            metadata={
                                "source_file": path.name,
                                "source_path": str(path),
                                "parser": "docling",
                                "extraction_mode": "markdown_fallback",
                            },
                        )
                    )

        # Priority 3: Final page fallback
        if not blocks:
            content = self._extract_content(result, path)

            page_chunks = [
                chunk.strip()
                for chunk in content.split("\f")
                if chunk.strip()
            ]

            if not page_chunks:
                cleaned = content.strip()
                if cleaned:
                    page_chunks = [cleaned]

            for idx, text in enumerate(page_chunks, start=1):
                blocks.append(
                    ParsedBlock(
                        block_id=str(uuid4()),
                        page=idx,
                        section=f"Page {idx}",
                        heading_level=None,
                        block_type="page_content",
                        text=text,
                        markdown=text,
                        bbox=None,
                        order_in_page=1,
                        is_ocr=False,
                        confidence=None,
                        parent_section_path=[],
                        metadata={
                            "source_file": path.name,
                            "source_path": str(path),
                            "parser": "docling",
                            "page_number": idx,
                            "extraction_mode": "page_fallback",
                        },
                    )
                )

        return blocks

    def _detect_block_type(self, item) -> str:
        cls = item.__class__.__name__.lower()

        if "table" in cls:
            return "table"

        if "heading" in cls or "title" in cls:
            return "heading"

        if "list" in cls:
            return "list"

        if "code" in cls:
            return "code"

        if "caption" in cls:
            return "image_caption"

        return "paragraph"

    def _resolve_section(self, item) -> str:
        if hasattr(item, "label") and item.label:
            return str(item.label)

        if hasattr(item, "text") and item.text:
            text = str(item.text).strip()
            if len(text) > 120:
                return text[:120]

            return text

        return "Untitled Section"

    def _resolve_heading_level(self, item) -> int | None:
        if hasattr(item, "level"):
            return item.level

        return None
