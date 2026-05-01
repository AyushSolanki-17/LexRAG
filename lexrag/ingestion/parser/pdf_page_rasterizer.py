"""Rasterize PDF pages into temporary images for OCR."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lexrag.ingestion.parser.schemas.rasterized_page import RasterizedPage


class PdfPageRasterizer:
    """Render PDF pages to PNG images before OCR execution."""

    def __init__(self, *, dpi: int = 300) -> None:
        self.dpi = dpi

    def rasterize(self, *, path: Path, output_dir: Path) -> list[RasterizedPage]:
        """Rasterize all pages of ``path`` into ``output_dir``."""
        fitz_module = self._load_fitz()
        with fitz_module.open(path) as document:  # pragma: no cover
            return self._render_pages(
                document=document,
                output_dir=output_dir,
                fitz_module=fitz_module,
            )

    def _load_fitz(self):
        try:
            import fitz
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "PyMuPDF is required for OCR rasterization of scanned PDFs."
            ) from exc
        return fitz

    def _render_pages(
        self,
        *,
        document: Any,
        output_dir: Path,
        fitz_module: Any,
    ) -> list[RasterizedPage]:
        pages: list[RasterizedPage] = []
        matrix = fitz_module.Matrix(self.dpi / 72.0, self.dpi / 72.0)
        for index, page in enumerate(document, start=1):
            pages.append(
                self._render_page(
                    page=page,
                    page_number=index,
                    output_dir=output_dir,
                    matrix=matrix,
                )
            )
        return pages

    def _render_page(
        self,
        *,
        page: Any,
        page_number: int,
        output_dir: Path,
        matrix: Any,
    ) -> RasterizedPage:
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        image_path = output_dir / f"page_{page_number:04d}.png"
        pixmap.save(image_path)
        return RasterizedPage(page_number=page_number, image_path=image_path)
