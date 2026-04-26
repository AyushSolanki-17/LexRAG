"""Docling-backed parser implementation.

Docling remains the preferred backend for native PDFs because it preserves
more document structure than text-only parsers.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings

from lexrag.ingestion.parser.base_document_parser import BaseDocumentParser
from lexrag.ingestion.parser.schemas.parsed_block import ParsedBlock
from lexrag.utils.logging import get_logger

logger = get_logger(__name__)


class DoclingParser(BaseDocumentParser):
    """Parse rich documents with Docling.

    The implementation favors stable, canonical block output over trying to
    mirror every detail exposed by the underlying library.
    """

    def __init__(self, settings: BaseSettings | None = None) -> None:
        """Store parser settings and build the converter lazily.

        Args:
            settings: Optional application settings object.
        """
        self.settings = settings
        self.converter = self._build_converter()

    def parse(self, path: Path) -> list[ParsedBlock]:
        """Parse a document path into canonical parsed blocks.

        Args:
            path: Document path to parse.

        Returns:
            Canonical parsed blocks extracted from the document.
        """
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        result = self._convert(path)
        return self._normalize_blocks(result=result, path=path)

    def _build_converter(self) -> Any:
        """Build the Docling converter with OCR and table support enabled."""
        try:
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.document_converter import DocumentConverter, PdfFormatOption
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "Docling is not installed. Install Docling OCR extras for parsing."
            ) from exc
        pdf_options = PdfPipelineOptions()
        pdf_options.do_ocr = True
        pdf_options.do_table_structure = True
        table_options = getattr(pdf_options, "table_structure_options", None)
        if table_options is not None and hasattr(table_options, "do_cell_matching"):
            table_options.do_cell_matching = True
        pdf_options.generate_page_images = False
        return DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options)
            }
        )

    def _convert(self, path: Path) -> Any:
        """Run Docling conversion and normalize parser-level failures."""
        try:
            return self.converter.convert(str(path))
        except Exception as exc:
            raise RuntimeError(f"Docling failed to parse {path}") from exc

    def _normalize_blocks(self, *, result: Any, path: Path) -> list[ParsedBlock]:
        """Choose the highest-fidelity output representation available."""
        document = self._resolve_document(result=result, path=path)
        defaults = self._build_defaults(path=path)
        blocks = self._extract_structured(
            document=document, path=path, defaults=defaults
        )
        if blocks:
            return blocks
        content = self._extract_content(document=document, path=path)
        blocks = self._extract_markdown_sections(
            content=content, path=path, defaults=defaults
        )
        if blocks:
            return blocks
        return self._extract_page_fallback(
            content=content, path=path, defaults=defaults
        )

    def _resolve_document(self, *, result: Any, path: Path) -> Any:
        """Resolve the document object from a Docling conversion result."""
        if hasattr(result, "document"):
            return result.document
        raise RuntimeError(f"No parsed document returned by Docling for {path}")

    def _build_defaults(self, *, path: Path) -> dict[str, Any]:
        """Build shared parsed block fields."""
        return {
            "doc_id": path.stem,
            "source_path": str(path),
            "source_name": path.name,
            "doc_type": path.suffix.lower().lstrip(".") or None,
            "parser_used": self.parser_name,
            "ocr_used": "docling_ocr",
        }

    def _extract_structured(
        self,
        *,
        document: Any,
        path: Path,
        defaults: dict[str, Any],
    ) -> list[ParsedBlock]:
        """Extract item-level blocks from Docling's structured output."""
        if not hasattr(document, "iterate_items"):
            return []
        blocks: list[ParsedBlock] = []
        order = 0
        try:
            for item, _level in document.iterate_items():
                text = str(getattr(item, "text", "")).strip()
                if not text:
                    continue
                order += 1
                blocks.append(
                    self._build_structured_block(
                        path=path,
                        defaults=defaults,
                        item=item,
                        order=order,
                        text=text,
                    )
                )
        except Exception as exc:
            logger.warning("Structured Docling extraction failed for %s: %s", path, exc)
            return []
        return blocks

    def _build_structured_block(
        self,
        *,
        path: Path,
        defaults: dict[str, Any],
        item: Any,
        order: int,
        text: str,
    ) -> ParsedBlock:
        """Build one parsed block from one Docling item."""
        page = self._resolve_page_number(value=getattr(item, "page_no", 1))
        confidence = self._resolve_confidence(value=getattr(item, "confidence", None))
        return ParsedBlock(
            **defaults,
            block_id=self._build_block_id(path=path, page=page, order=order, text=text),
            page=page,
            section=self._resolve_section(item=item, text=text),
            heading_level=self._resolve_heading_level(item=item),
            block_type=self._detect_block_type(item=item),
            text=text,
            markdown=text,
            bbox=self._normalize_bbox(value=getattr(item, "bbox", None)),
            order_in_page=order,
            is_ocr=self._resolve_item_bool(
                item=item,
                names=("is_ocr", "ocr_used", "used_ocr"),
            ),
            confidence=confidence,
            parse_confidence=confidence,
            metadata={"parser": self.parser_name, "extraction_mode": "structured"},
        )

    def _extract_content(self, *, document: Any, path: Path) -> str:
        """Extract best-effort content when structured items are unavailable."""
        content = self._try_markdown(document=document)
        if content:
            return content
        content = self._try_plain_text(document=document)
        if content:
            return content
        content = self._try_generic_repr(document=document)
        if content:
            return content
        raise RuntimeError(f"Docling returned empty content for {path}")

    def _try_markdown(self, *, document: Any) -> str:
        """Export markdown when Docling makes it available."""
        if not hasattr(document, "export_to_markdown"):
            return ""
        try:
            return str(document.export_to_markdown()).strip()
        except Exception as exc:
            logger.warning("Docling markdown export failed: %s", exc)
            return ""

    def _try_plain_text(self, *, document: Any) -> str:
        """Export plain text when markdown export is unavailable."""
        if not hasattr(document, "text"):
            return ""
        try:
            return str(document.text).strip()
        except Exception as exc:
            logger.warning("Docling text export failed: %s", exc)
            return ""

    def _try_generic_repr(self, *, document: Any) -> str:
        """Use the generic string representation as a last resort."""
        try:
            return str(document).strip()
        except Exception as exc:
            logger.warning("Docling generic export failed: %s", exc)
            return ""

    def _extract_markdown_sections(
        self,
        *,
        content: str,
        path: Path,
        defaults: dict[str, Any],
    ) -> list[ParsedBlock]:
        """Split markdown content into coarse section blocks."""
        sections = [part.strip() for part in content.split("\n## ") if part.strip()]
        return [
            ParsedBlock(
                **defaults,
                block_id=self._build_block_id(
                    path=path, page=index, order=1, text=section
                ),
                page=index,
                section=f"Section {index}",
                heading_level=2,
                block_type="section",
                text=section,
                markdown=section,
                order_in_page=1,
                metadata={
                    "parser": self.parser_name,
                    "extraction_mode": "markdown_fallback",
                },
            )
            for index, section in enumerate(sections, start=1)
        ]

    def _extract_page_fallback(
        self,
        *,
        content: str,
        path: Path,
        defaults: dict[str, Any],
    ) -> list[ParsedBlock]:
        """Split plain text into page-like blocks using form-feed markers."""
        chunks = [part.strip() for part in content.split("\f") if part.strip()]
        page_chunks = chunks or [content.strip()]
        return [
            ParsedBlock(
                **defaults,
                block_id=self._build_block_id(
                    path=path, page=index, order=1, text=text
                ),
                page=index,
                section=f"Page {index}",
                block_type="page_content",
                text=text,
                markdown=text,
                order_in_page=1,
                metadata={
                    "parser": self.parser_name,
                    "extraction_mode": "page_fallback",
                },
            )
            for index, text in enumerate(page_chunks, start=1)
            if text
        ]

    def _build_block_id(self, *, path: Path, page: int, order: int, text: str) -> str:
        """Build deterministic block identifiers for re-index safety."""
        digest = hashlib.sha1(text[:500].encode("utf-8")).hexdigest()[:12]
        return f"{path.stem}_p{page}_b{order}_{digest}"

    def _resolve_page_number(self, *, value: Any) -> int:
        """Coerce page numbers into safe 1-based integers."""
        if isinstance(value, int) and value >= 1:
            return value
        try:
            page = int(value)
        except (TypeError, ValueError):
            return 1
        return page if page >= 1 else 1

    def _resolve_item_bool(self, *, item: Any, names: tuple[str, ...]) -> bool:
        """Resolve parser booleans from a list of candidate attributes."""
        for name in names:
            if hasattr(item, name):
                return bool(getattr(item, name))
        return False

    def _resolve_confidence(self, *, value: Any) -> float | None:
        """Normalize confidence values into the closed interval [0, 1]."""
        if value is None:
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if 0.0 <= number <= 1.0 else None

    def _detect_block_type(self, *, item: Any) -> str:
        """Map Docling item types into LexRAG block types."""
        class_name = item.__class__.__name__.lower()
        if "table" in class_name:
            return "table"
        if "heading" in class_name or "title" in class_name:
            return "heading"
        if "list" in class_name:
            return "list"
        if "code" in class_name:
            return "code"
        if "caption" in class_name:
            return "image_caption"
        return "paragraph"

    def _resolve_section(self, *, item: Any, text: str) -> str:
        """Resolve a stable, human-readable section label."""
        label = getattr(item, "label", None)
        if label:
            return str(label).strip()
        return text[:120].strip() or "Untitled Section"

    def _resolve_heading_level(self, *, item: Any) -> int | None:
        """Return the heading level when Docling provides one."""
        level = getattr(item, "level", None)
        if not isinstance(level, int):
            return None
        return level if 1 <= level <= 6 else None

    def _normalize_bbox(
        self, *, value: Any
    ) -> tuple[float, float, float, float] | None:
        """Normalize bounding boxes into float tuples."""
        if not isinstance(value, (tuple, list)) or len(value) != 4:
            return None
        try:
            x1, y1, x2, y2 = (float(part) for part in value)
        except (TypeError, ValueError):
            return None
        return (x1, y1, x2, y2)
