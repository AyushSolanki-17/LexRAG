"""File validation layer for document parsing."""

from __future__ import annotations

from pathlib import Path

from lexrag.ingestion.parser.schemas.file_validation_result import FileValidationResult
from lexrag.ingestion.parser.schemas.parser_config import ParserConfig


class FileValidationService:
    """Validate files before parser selection begins."""

    def __init__(self, config: ParserConfig | None = None) -> None:
        """Initialize validation rules.

        Args:
            config: Optional parser configuration. Defaults are production-safe.
        """
        self.config = config or ParserConfig()

    def validate(self, path: Path) -> FileValidationResult:
        """Validate the document path against parsing preconditions.

        Args:
            path: Document path to validate.

        Returns:
            Structured validation result describing whether parsing may proceed.
        """
        if not path.exists():
            raise FileNotFoundError(f"Document does not exist: {path}")
        if not path.is_file():
            raise FileNotFoundError(f"Document is not a file: {path}")
        size_bytes = path.stat().st_size
        extension = path.suffix.lower()
        supported = extension in self.config.allowed_extensions
        encrypted = self._is_encrypted_pdf(path=path, extension=extension)
        failure_reason = self._failure_reason(
            size_bytes=size_bytes,
            supported=supported,
            encrypted=encrypted,
        )
        return FileValidationResult(
            extension=extension,
            file_size_bytes=size_bytes,
            encrypted=encrypted,
            supported_extension=supported,
            is_valid=failure_reason is None or encrypted,
            failure_reason=failure_reason,
        )

    def _failure_reason(
        self,
        *,
        size_bytes: int,
        supported: bool,
        encrypted: bool,
    ) -> str | None:
        """Resolve a single validation failure reason."""
        if size_bytes < self.config.min_file_size_bytes:
            return "file_empty"
        if size_bytes > self.config.max_file_size_bytes:
            return "file_too_large"
        if not supported:
            return "unsupported_extension"
        if encrypted:
            return "encrypted_pdf"
        return None

    def _is_encrypted_pdf(self, *, path: Path, extension: str) -> bool:
        """Detect encrypted PDFs before the parser stack is invoked."""
        if extension != ".pdf":
            return False
        header = path.read_bytes()[: self.config.magic_byte_window]
        if not header.startswith(b"%PDF"):
            return False
        if b"/Encrypt" in header:
            return True
        return self._is_encrypted_via_fitz(path=path)

    def _is_encrypted_via_fitz(self, *, path: Path) -> bool:
        """Use PyMuPDF when available to detect encrypted PDFs accurately."""
        try:
            import fitz
        except Exception:  # pragma: no cover
            return False
        try:
            with fitz.open(path) as document:  # pragma: no cover
                return bool(getattr(document, "needs_pass", False))
        except Exception:
            return False
