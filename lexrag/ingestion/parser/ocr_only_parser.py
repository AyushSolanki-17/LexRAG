"""OCR-only parser for scanned PDFs and standalone image documents."""

from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

from lexrag.ingestion.parser.base_document_parser import BaseDocumentParser
from lexrag.ingestion.parser.ocr_extractor import OCRExtractor
from lexrag.ingestion.parser.pdf_page_rasterizer import PdfPageRasterizer
from lexrag.ingestion.parser.schemas.ocr_text_block import OCRTextBlock
from lexrag.ingestion.parser.schemas.parsed_block import ParsedBlock
from lexrag.ingestion.parser.schemas.parser_config import ParserConfig
from lexrag.ingestion.parser.schemas.rasterized_page import RasterizedPage
from lexrag.ingestion.parser.tesseract_ocr_extractor import TesseractOCRExtractor


class OCROnlyParser(BaseDocumentParser):
    """Parse scanned PDFs and image documents with OCR."""

    def __init__(
        self,
        *,
        config: ParserConfig | None = None,
        ocr_extractor: OCRExtractor | None = None,
        pdf_rasterizer: PdfPageRasterizer | None = None,
    ) -> None:
        self.config = config or ParserConfig()
        self.ocr_extractor = ocr_extractor or TesseractOCRExtractor()
        self.pdf_rasterizer = pdf_rasterizer or PdfPageRasterizer(
            dpi=self.config.ocr_render_dpi
        )

    @property
    def parser_name(self) -> str:
        """Return the stable routing name used by orchestration."""
        return "ocr_only"

    def parse(self, path: Path) -> list[ParsedBlock]:
        """Parse one scanned document path into OCR-backed parsed blocks."""
        self._validate_path(path=path)
        if path.suffix.lower() == ".pdf":
            return self._parse_pdf(path=path)
        return self._parse_image(path=path)

    def _validate_path(self, *, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if path.suffix.lower() not in self.config.allowed_extensions:
            raise RuntimeError(f"OCR parser does not support extension: {path.suffix}")

    def _parse_pdf(self, *, path: Path) -> list[ParsedBlock]:
        with TemporaryDirectory(prefix="lexrag_ocr_") as temp_dir:
            pages = self.pdf_rasterizer.rasterize(
                path=path,
                output_dir=Path(temp_dir),
            )
            return self._blocks_from_pages(path=path, image_pages=pages)

    def _parse_image(self, *, path: Path) -> list[ParsedBlock]:
        ocr_blocks = self.ocr_extractor.extract(image_path=path, page_number=1)
        return self._parsed_blocks(path=path, ocr_blocks=ocr_blocks)

    def _blocks_from_pages(
        self,
        *,
        path: Path,
        image_pages: list[RasterizedPage],
    ) -> list[ParsedBlock]:
        blocks: list[ParsedBlock] = []
        for page in image_pages:
            ocr_blocks = self.ocr_extractor.extract(
                image_path=page.image_path,
                page_number=page.page_number,
            )
            blocks.extend(self._parsed_blocks(path=path, ocr_blocks=ocr_blocks))
        if not blocks:
            raise RuntimeError(f"OCR parser produced no text for {path}")
        return blocks

    def _parsed_blocks(
        self,
        *,
        path: Path,
        ocr_blocks: list[OCRTextBlock],
    ) -> list[ParsedBlock]:
        if not ocr_blocks:
            raise RuntimeError(f"OCR produced no usable text for {path}")
        return [self._build_block(path=path, block=block) for block in ocr_blocks]

    def _build_block(self, *, path: Path, block: OCRTextBlock) -> ParsedBlock:
        return ParsedBlock(
            doc_id=path.stem,
            source_path=str(path),
            source_name=path.name,
            doc_type=path.suffix.lower().lstrip(".") or None,
            block_id=self._block_id(path=path, block=block),
            page=block.page,
            section=f"OCR Page {block.page}",
            block_type="paragraph",
            text=block.text,
            markdown=block.text,
            bbox=block.bbox,
            order_in_page=block.order,
            is_ocr=True,
            confidence=block.confidence,
            parser_used=self.parser_name,
            ocr_used=self._ocr_backend_name(),
            parse_confidence=block.confidence,
            metadata={
                "parser": self.parser_name,
                "extraction_mode": "ocr",
            },
        )

    def _block_id(self, *, path: Path, block: OCRTextBlock) -> str:
        digest = hashlib.sha1(block.text[:500].encode("utf-8")).hexdigest()[:12]
        return f"{path.stem}_p{block.page}_b{block.order}_{digest}"

    def _ocr_backend_name(self) -> str:
        return self.ocr_extractor.__class__.__name__.removesuffix("Extractor").lower()
