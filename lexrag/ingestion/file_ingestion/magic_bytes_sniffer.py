"""Content-type sniffing helpers for upload classification.

The architecture prefers byte-level MIME detection rather than trusting file
extensions. This module first attempts `python-magic` when available and then
falls back to conservative signature-based heuristics.
"""

from __future__ import annotations

from pathlib import Path

from lexrag.ingestion.file_ingestion.schemas.file_ingestion_config import FileIngestionConfig

HTML_MARKERS = (b"<html", b"<!doctype html", b"<body", b"<head")
XML_MARKERS = (b"<?xml",)
EML_MARKERS = (b"from:", b"subject:", b"mime-version:", b"content-type:")


class MagicBytesSniffer:
    """Infer MIME-like media types from file bytes."""

    def __init__(self, config: FileIngestionConfig | None = None) -> None:
        """Initialize sniffer configuration.

        Args:
            config: Optional ingestion configuration.
        """
        self.config = config or FileIngestionConfig()

    def sniff(self, path: Path) -> tuple[str, str]:
        """Return the best-effort media type and its detection source.

        Args:
            path: File path to inspect.

        Returns:
            A pair of `(media_type, detection_method)`.
        """
        sample = path.read_bytes()[: self.config.magic_byte_window]
        magic_result = self._sniff_with_python_magic(sample=sample)
        if magic_result is not None:
            return magic_result, "python-magic"
        return self._sniff_with_signatures(
            sample=sample,
            extension=path.suffix.lower(),
        )

    def _sniff_with_python_magic(self, *, sample: bytes) -> str | None:
        """Use libmagic when present because it is the highest-fidelity option."""
        try:
            import magic
        except Exception:
            return None
        try:
            detected = magic.from_buffer(sample, mime=True)
        except Exception:
            return None
        if not detected or detected == "application/octet-stream":
            return None
        return str(detected)

    def _sniff_with_signatures(
        self,
        *,
        sample: bytes,
        extension: str,
    ) -> tuple[str, str]:
        """Apply conservative fallback signatures when libmagic is unavailable."""
        lowered = sample.lower()
        if sample.startswith(b"%PDF"):
            return "application/pdf", "signature"
        if sample.startswith(b"PK\x03\x04"):
            return self._office_media_type(extension=extension), "signature"
        if sample.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png", "signature"
        if sample.startswith((b"\xff\xd8\xff",)):
            return "image/jpeg", "signature"
        if sample.startswith((b"II*\x00", b"MM\x00*")):
            return "image/tiff", "signature"
        if any(marker in lowered for marker in HTML_MARKERS):
            return "text/html", "heuristic"
        if any(marker in lowered for marker in XML_MARKERS):
            return "application/xml", "heuristic"
        if any(marker in lowered for marker in EML_MARKERS):
            return "message/rfc822", "heuristic"
        if self._is_likely_text(sample=sample):
            return "text/plain", "heuristic"
        return "application/octet-stream", "unknown"

    def _office_media_type(self, *, extension: str) -> str:
        """Map OOXML extensions onto their canonical media types."""
        if extension == ".docx":
            return (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            )
        if extension == ".xlsx":
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if extension == ".pptx":
            return (
                "application/vnd.openxmlformats-officedocument."
                "presentationml.presentation"
            )
        return "application/zip"

    def _is_likely_text(self, *, sample: bytes) -> bool:
        """Identify UTF-safe text payloads without being overly optimistic."""
        if not sample or b"\x00" in sample:
            return False
        try:
            sample.decode("utf-8")
        except UnicodeDecodeError:
            return False
        return True
