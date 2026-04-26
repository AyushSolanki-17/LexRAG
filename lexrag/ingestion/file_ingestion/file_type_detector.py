"""File type detection for parser routing.

This is the architecture-defined 2.2 layer. It classifies the uploaded file
family using byte sniffing first and extension cross-validation second so the
parser layer can make routing decisions without duplicating file-inspection
logic.
"""

from __future__ import annotations

from pathlib import Path

from lexrag.ingestion.file_ingestion.magic_bytes_sniffer import MagicBytesSniffer
from lexrag.ingestion.file_ingestion.schemas.file_ingestion_config import FileIngestionConfig
from lexrag.ingestion.file_ingestion.schemas.file_type_detection import FileTypeDetection

HTML_MARKERS = (b"<html", b"<!doctype html", b"<body", b"<head")


class FileTypeDetector:
    """Classify files into document families used by parser selection."""

    def __init__(
        self,
        config: FileIngestionConfig | None = None,
        *,
        sniffer: MagicBytesSniffer | None = None,
    ) -> None:
        """Initialize the detector.

        Args:
            config: Optional ingestion configuration.
            sniffer: Optional byte sniffer override.
        """
        self.config = config or FileIngestionConfig()
        self.sniffer = sniffer or MagicBytesSniffer(config=self.config)

    def detect(self, path: Path) -> FileTypeDetection:
        """Detect the file family from content and extension.

        Args:
            path: File path to inspect.

        Returns:
            Structured file type detection result for parser routing.
        """
        sample = path.read_bytes()[: self.config.magic_byte_window]
        media_type, detection_method = self.sniffer.sniff(path)
        extension = path.suffix.lower()
        return FileTypeDetection(
            extension=extension,
            media_type=media_type,
            detection_method=detection_method,
            document_family=self._document_family(
                extension=extension,
                media_type=media_type,
            ),
            detected_type=self._document_family(
                extension=extension,
                media_type=media_type,
            ),
            has_pdf_header=sample.startswith(b"%PDF"),
            is_html=any(marker in sample.lower() for marker in HTML_MARKERS),
            is_text_like=self._is_likely_text(sample=sample),
            extension_matches_media_type=self._extension_matches_media_type(
                extension=extension,
                media_type=media_type,
            ),
            is_office_document=extension in self.config.office_extensions,
            is_email=extension in self.config.email_extensions
            or media_type == "message/rfc822",
        )

    def _document_family(self, *, extension: str, media_type: str) -> str:
        """Collapse low-level media types into parser-friendly families."""
        if media_type == "application/pdf":
            return "pdf"
        if media_type.startswith("image/"):
            return "image"
        if media_type == "text/html":
            return "html"
        if media_type == "application/xml":
            return "xml"
        if media_type == "message/rfc822" or extension in self.config.email_extensions:
            return "email"
        if extension in self.config.office_extensions:
            return "office"
        if media_type.startswith("text/"):
            return "text"
        return extension.lstrip(".") or "unknown"

    def _extension_matches_media_type(self, *, extension: str, media_type: str) -> bool:
        """Cross-validate extension and byte-level media detection."""
        allowed_media_types = self.config.extension_media_type_map.get(extension)
        if allowed_media_types is None:
            return False
        return media_type in allowed_media_types

    def _is_likely_text(self, *, sample: bytes) -> bool:
        """Heuristically identify text-like payloads for secondary routing."""
        if not sample or b"\x00" in sample:
            return False
        try:
            sample.decode("utf-8")
        except UnicodeDecodeError:
            return False
        return True
