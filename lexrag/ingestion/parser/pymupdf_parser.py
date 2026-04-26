"""PyMuPDF-backed fallback parser.

This backend focuses on reliability. It can parse real PDFs, extract HTML text,
and recover plain-text fixture files that intentionally wear a ``.pdf``
extension in tests and guardrail pipelines.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from lexrag.ingestion.parser.base_document_parser import BaseDocumentParser
from lexrag.ingestion.parser.html_text_extractor import HtmlTextExtractor
from lexrag.ingestion.parser.schemas.parsed_block import ParsedBlock


class PyMuPDFParser(BaseDocumentParser):
    """Fallback parser for PDF, HTML, and text-like recovery paths."""

    def parse(self, path: Path) -> list[ParsedBlock]:
        """Parse a supported document into canonical parsed blocks.

        Args:
            path: Document path to parse.

        Returns:
            Canonical parsed blocks extracted from the document.
        """
        suffix = path.suffix.lower()
        if suffix in {".html", ".htm"}:
            return self._parse_html(path=path)
        if self._looks_like_pdf(path=path):
            return self._parse_pdf(path=path)
        return self._parse_text_recovery(path=path)

    def _parse_html(self, *, path: Path) -> list[ParsedBlock]:
        """Extract visible text from HTML content."""
        raw = path.read_text(encoding="utf-8", errors="ignore")
        extractor = HtmlTextExtractor()
        extractor.feed(raw)
        text = extractor.text()
        if not text:
            raise RuntimeError(f"Empty HTML content parsed for {path}")
        return [self._build_block(path=path, page=1, section="HTML", text=text)]

    def _looks_like_pdf(self, *, path: Path) -> bool:
        """Detect real PDFs by header instead of trusting the extension."""
        try:
            header = path.read_bytes()[:8]
        except OSError:
            return False
        return header.startswith(b"%PDF")

    def _parse_pdf(self, *, path: Path) -> list[ParsedBlock]:
        """Extract page text from a real PDF using PyMuPDF."""
        try:
            import fitz
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("PyMuPDF is required for PDF fallback parsing") from exc
        return self._extract_pdf_pages(path=path, fitz_module=fitz)

    def _extract_pdf_pages(self, *, path: Path, fitz_module: Any) -> list[ParsedBlock]:
        """Emit one parsed block per text-bearing page."""
        blocks: list[ParsedBlock] = []
        with fitz_module.open(path) as document:  # pragma: no cover
            for page_index, page in enumerate(document, start=1):
                text = page.get_text("text").strip()
                if not text:
                    continue
                blocks.append(
                    self._build_block(
                        path=path,
                        page=page_index,
                        section=f"Page {page_index}",
                        text=text,
                    )
                )
        if blocks:
            return blocks
        raise RuntimeError(f"No extractable text found in PDF {path}")

    def _parse_text_recovery(self, *, path: Path) -> list[ParsedBlock]:
        """Recover text-like files that could not be parsed as binary PDFs.

        This branch exists for robustness. Some upstream systems rename text
        exports to ``.pdf`` even when they are not real PDFs, and our tests
        intentionally cover that failure mode.
        """
        content = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not content:
            raise RuntimeError(
                f"No extractable text found in fallback recovery for {path}"
            )
        parts = [part.strip() for part in content.split("\f") if part.strip()]
        return [
            self._build_block(
                path=path,
                page=index,
                section=f"Page {index}",
                text=text,
            )
            for index, text in enumerate(parts or [content], start=1)
        ]

    def _build_block(
        self,
        *,
        path: Path,
        page: int,
        section: str,
        text: str,
    ) -> ParsedBlock:
        """Build a canonical parsed block for this backend."""
        return ParsedBlock(
            doc_id=path.stem,
            source_path=str(path),
            source_name=path.name,
            doc_type=path.suffix.lower().lstrip(".") or None,
            block_id=self._build_block_id(path=path, page=page, order=1, text=text),
            page=page,
            section=section,
            block_type="paragraph",
            text=text,
            markdown=text,
            order_in_page=1,
            parser_used=self.parser_name,
            metadata={"parser": self.parser_name, "extraction_mode": "text"},
        )

    def _build_block_id(self, *, path: Path, page: int, order: int, text: str) -> str:
        """Build deterministic block identifiers."""
        digest = hashlib.sha1(text[:500].encode("utf-8")).hexdigest()[:12]
        return f"{path.stem}_p{page}_b{order}_{digest}"
