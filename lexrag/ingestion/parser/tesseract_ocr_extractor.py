"""Tesseract-backed OCR extractor."""

from __future__ import annotations

import csv
import subprocess
from collections import defaultdict
from io import StringIO
from pathlib import Path

from lexrag.ingestion.parser.ocr_extractor import OCRExtractor
from lexrag.ingestion.parser.schemas.ocr_text_block import OCRTextBlock


class TesseractOCRExtractor(OCRExtractor):
    """Use the Tesseract CLI to OCR rasterized document pages."""

    def extract(self, *, image_path: Path, page_number: int) -> list[OCRTextBlock]:
        """Return grouped OCR text blocks for one page image."""
        rows = self._tsv_rows(image_path=image_path)
        blocks = self._group_rows(rows=rows, page_number=page_number)
        if not blocks:
            raise RuntimeError(f"OCR produced no usable text for {image_path}")
        return blocks

    def _tsv_rows(self, *, image_path: Path) -> list[dict[str, str]]:
        command = ["tesseract", str(image_path), "stdout", "--psm", "6", "tsv"]
        try:
            completed = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("Tesseract CLI is required for OCR parsing.") from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip() if exc.stderr else "unknown_tesseract_error"
            raise RuntimeError(
                f"Tesseract OCR failed for {image_path}: {stderr}"
            ) from exc
        reader = csv.DictReader(StringIO(completed.stdout), delimiter="\t")
        return [row for row in reader if self._is_text_row(row=row)]

    def _is_text_row(self, *, row: dict[str, str]) -> bool:
        text = row.get("text", "").strip()
        confidence = self._confidence_value(raw=row.get("conf"))
        return bool(text) and confidence is not None and confidence >= 0.0

    def _group_rows(
        self,
        *,
        rows: list[dict[str, str]],
        page_number: int,
    ) -> list[OCRTextBlock]:
        grouped: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(
            list
        )
        for row in rows:
            key = (
                row.get("page_num", "1"),
                row.get("block_num", "0"),
                row.get("par_num", "0"),
                row.get("line_num", "0"),
            )
            grouped[key].append(row)
        blocks: list[OCRTextBlock] = []
        for order, key in enumerate(sorted(grouped), start=1):
            block = self._build_block(
                rows=grouped[key],
                page_number=page_number,
                order=order,
            )
            if block is not None:
                blocks.append(block)
        return blocks

    def _build_block(
        self,
        *,
        rows: list[dict[str, str]],
        page_number: int,
        order: int,
    ) -> OCRTextBlock | None:
        text = " ".join(row.get("text", "").strip() for row in rows).strip()
        if not text:
            return None
        return OCRTextBlock(
            page=page_number,
            order=order,
            text=text,
            confidence=self._average_confidence(rows=rows),
            bbox=self._bounding_box(rows=rows),
        )

    def _average_confidence(self, *, rows: list[dict[str, str]]) -> float | None:
        values = [
            value
            for value in (self._confidence_value(raw=row.get("conf")) for row in rows)
            if value is not None and value >= 0.0
        ]
        if not values:
            return None
        return sum(values) / len(values)

    def _bounding_box(
        self,
        *,
        rows: list[dict[str, str]],
    ) -> tuple[float, float, float, float] | None:
        boxes = [self._row_box(row=row) for row in rows]
        realized = [box for box in boxes if box is not None]
        if not realized:
            return None
        left = min(box[0] for box in realized)
        top = min(box[1] for box in realized)
        right = max(box[2] for box in realized)
        bottom = max(box[3] for box in realized)
        return (left, top, right, bottom)

    def _row_box(
        self,
        *,
        row: dict[str, str],
    ) -> tuple[float, float, float, float] | None:
        try:
            left = float(row.get("left", ""))
            top = float(row.get("top", ""))
            width = float(row.get("width", ""))
            height = float(row.get("height", ""))
        except ValueError:
            return None
        return (left, top, left + width, top + height)

    def _confidence_value(self, *, raw: str | None) -> float | None:
        if raw is None:
            return None
        try:
            value = float(raw)
        except ValueError:
            return None
        if value < 0.0:
            return None
        return min(value / 100.0, 1.0)
