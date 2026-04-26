"""File type detection for parser routing."""

from __future__ import annotations

from pathlib import Path

from lexrag.ingestion.parser.schemas.file_type_detection import FileTypeDetection
from lexrag.ingestion.parser.schemas.parser_config import ParserConfig

HTML_MARKERS = (b"<html", b"<!doctype html", b"<body", b"<head")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


class FileTypeDetector:
    """Detect the most likely document family for parser routing."""

    def __init__(self, config: ParserConfig | None = None) -> None:
        """Initialize detection heuristics.

        Args:
            config: Optional parser configuration.
        """
        self.config = config or ParserConfig()

    def detect(self, path: Path) -> FileTypeDetection:
        """Detect the file type from content and extension.

        Args:
            path: Document path to inspect.

        Returns:
            Structured file type detection result.
        """
        sample = path.read_bytes()[: self.config.magic_byte_window]
        lowered = sample.lower()
        extension = path.suffix.lower()
        detected_type = self._detect_type(extension=extension, lowered=lowered)
        return FileTypeDetection(
            extension=extension,
            detected_type=detected_type,
            has_pdf_header=sample.startswith(b"%PDF"),
            is_html=any(marker in lowered for marker in HTML_MARKERS),
            is_text_like=self._is_likely_text(sample=sample),
        )

    def _detect_type(self, *, extension: str, lowered: bytes) -> str:
        """Resolve the dominant document family for routing."""
        if lowered.startswith(b"%pdf"):
            return "pdf"
        if any(marker in lowered for marker in HTML_MARKERS):
            return "html"
        if extension in IMAGE_EXTENSIONS:
            return "image"
        if self._is_likely_text(sample=lowered):
            return "text"
        return extension.lstrip(".") or "unknown"

    def _is_likely_text(self, *, sample: bytes) -> bool:
        """Heuristically identify text-like payloads."""
        if not sample:
            return False
        try:
            sample.decode("utf-8")
        except UnicodeDecodeError:
            return False
        return b"\x00" not in sample
