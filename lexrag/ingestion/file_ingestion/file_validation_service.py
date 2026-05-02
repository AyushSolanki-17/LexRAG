"""File validation service for architecture layer 2.1.

The validator exists to reject unsafe or obviously malformed uploads before
parsers run. It also emits structured validation issues so callers can explain
why a document was blocked instead of failing with parser-specific errors.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from lexrag.ingestion.file_ingestion.antivirus_scanner import AntivirusScanner
from lexrag.ingestion.file_ingestion.build_antivirus_scanner import (
    build_antivirus_scanner,
)
from lexrag.ingestion.file_ingestion.file_hash_calculator import FileHashCalculator
from lexrag.ingestion.file_ingestion.magic_bytes_sniffer import MagicBytesSniffer
from lexrag.ingestion.file_ingestion.schemas.antivirus_scan_result import (
    AntivirusScanResult,
)
from lexrag.ingestion.file_ingestion.schemas.file_ingestion_config import (
    FileIngestionConfig,
)
from lexrag.ingestion.file_ingestion.schemas.file_validation_issue import (
    FileValidationIssue,
)
from lexrag.ingestion.file_ingestion.schemas.file_validation_result import (
    FileValidationResult,
)


class FileValidationService:
    """Validate file safety, integrity, and batch-level uniqueness."""

    def __init__(
        self,
        config: FileIngestionConfig | None = None,
        *,
        antivirus_scanner: AntivirusScanner | None = None,
        hash_calculator: FileHashCalculator | None = None,
        sniffer: MagicBytesSniffer | None = None,
    ) -> None:
        """Initialize validation collaborators.

        Args:
            config: Optional ingestion configuration.
            antivirus_scanner: Optional malware scanner implementation.
            hash_calculator: Optional file hash implementation.
            sniffer: Optional byte-level content sniffer.
        """
        self.config = config or FileIngestionConfig()
        self.antivirus_scanner = antivirus_scanner or build_antivirus_scanner(
            config=self.config
        )
        self.hash_calculator = hash_calculator or FileHashCalculator()
        self.sniffer = sniffer or MagicBytesSniffer(config=self.config)

    def validate(
        self,
        path: Path,
        *,
        known_hashes: set[str] | None = None,
    ) -> FileValidationResult:
        """Validate a single file before parser selection begins.

        Args:
            path: File path to validate.
            known_hashes: Optional in-memory batch hash set for duplicate checks.

        Returns:
            Structured validation result with blocking and non-blocking issues.
        """
        self._assert_path(path)
        media_type, _method = self.sniffer.sniff(path)
        sha256 = self.hash_calculator.sha256(path)
        issues = self._build_issues(path=path, media_type=media_type, sha256=sha256)
        duplicate_in_batch = self._track_batch_duplicate(
            sha256=sha256,
            known_hashes=known_hashes,
        )
        if duplicate_in_batch:
            issues.append(self._issue("duplicate_file_in_batch", blocking=True))
        antivirus = self.antivirus_scanner.scan(path)
        if antivirus.blocking:
            issues.append(self._issue("antivirus_infected", blocking=True))
        return self._build_result(
            path=path,
            media_type=media_type,
            sha256=sha256,
            antivirus=antivirus,
            duplicate_in_batch=duplicate_in_batch,
            issues=issues,
        )

    def validate_many(self, paths: list[Path]) -> list[FileValidationResult]:
        """Validate a batch and detect duplicate uploads within that batch.

        Args:
            paths: File paths to validate together.

        Returns:
            Validation results in the same order as the input paths.
        """
        known_hashes: set[str] = set()
        return [self.validate(path, known_hashes=known_hashes) for path in paths]

    def _build_issues(
        self,
        *,
        path: Path,
        media_type: str,
        sha256: str,
    ) -> list[FileValidationIssue]:
        """Collect deterministic validation issues for a file."""
        issues: list[FileValidationIssue] = []
        self._append_size_issues(path=path, issues=issues)
        self._append_extension_issues(path=path, media_type=media_type, issues=issues)
        self._append_corruption_issue(path=path, media_type=media_type, issues=issues)
        self._append_encryption_issue(path=path, media_type=media_type, issues=issues)
        self._append_hash_presence_issue(sha256=sha256, issues=issues)
        return issues

    def _append_size_issues(
        self,
        *,
        path: Path,
        issues: list[FileValidationIssue],
    ) -> None:
        """Enforce minimum and maximum document size thresholds."""
        size_bytes = path.stat().st_size
        if size_bytes < self.config.min_file_size_bytes:
            issues.append(self._issue("file_empty", blocking=True))
        if size_bytes > self.config.max_file_size_bytes:
            issues.append(self._issue("file_too_large", blocking=True))

    def _append_extension_issues(
        self,
        *,
        path: Path,
        media_type: str,
        issues: list[FileValidationIssue],
    ) -> None:
        """Validate allowlisted extensions and content-type consistency."""
        extension = path.suffix.lower()
        if extension not in self.config.allowed_extensions:
            issues.append(self._issue("unsupported_extension", blocking=True))
            return
        if not self._extension_matches_media_type(
            extension=extension, media_type=media_type
        ):
            issues.append(self._issue("extension_media_mismatch", blocking=False))

    def _append_corruption_issue(
        self,
        *,
        path: Path,
        media_type: str,
        issues: list[FileValidationIssue],
    ) -> None:
        """Block obviously malformed PDFs and OOXML archives early."""
        if self._is_corrupted(path=path, media_type=media_type):
            issues.append(self._issue("corrupt_file", blocking=True))

    def _append_encryption_issue(
        self,
        *,
        path: Path,
        media_type: str,
        issues: list[FileValidationIssue],
    ) -> None:
        """Detect password-protected PDFs before parser execution."""
        if media_type != "application/pdf":
            return
        if self._is_encrypted_pdf(path=path):
            issues.append(self._issue("encrypted_pdf", blocking=True))

    def _append_hash_presence_issue(
        self,
        *,
        sha256: str,
        issues: list[FileValidationIssue],
    ) -> None:
        """Guard against impossible hashing failures and empty digests."""
        if sha256:
            return
        issues.append(self._issue("hash_unavailable", blocking=True))

    def _build_result(
        self,
        *,
        path: Path,
        media_type: str,
        sha256: str,
        antivirus: AntivirusScanResult,
        duplicate_in_batch: bool,
        issues: list[FileValidationIssue],
    ) -> FileValidationResult:
        """Materialize the canonical validation DTO."""
        extension = path.suffix.lower()
        blocking_issues = [issue for issue in issues if issue.blocking]
        return FileValidationResult(
            path=str(path),
            extension=extension,
            file_size_bytes=path.stat().st_size,
            media_type=media_type,
            sha256=sha256,
            encrypted=self._has_issue("encrypted_pdf", issues=issues),
            corrupted=self._has_issue("corrupt_file", issues=issues),
            supported_extension=extension in self.config.allowed_extensions,
            extension_matches_media_type=self._extension_matches_media_type(
                extension=extension,
                media_type=media_type,
            ),
            duplicate_in_batch=duplicate_in_batch,
            antivirus=antivirus,
            issues=issues,
            is_valid=not blocking_issues,
            failure_reason=blocking_issues[0].code if blocking_issues else None,
        )

    def _track_batch_duplicate(
        self,
        *,
        sha256: str,
        known_hashes: set[str] | None,
    ) -> bool:
        """Track duplicate files within a single batch validation call."""
        if known_hashes is None:
            return False
        already_seen = sha256 in known_hashes
        known_hashes.add(sha256)
        return already_seen

    def _assert_path(self, path: Path) -> None:
        """Validate basic path preconditions before deeper inspection."""
        if not path.exists():
            raise FileNotFoundError(f"Document does not exist: {path}")
        if not path.is_file():
            raise FileNotFoundError(f"Document is not a file: {path}")

    def _extension_matches_media_type(self, *, extension: str, media_type: str) -> bool:
        """Cross-check extension and media type using configured allowlists."""
        allowed_media_types = self.config.extension_media_type_map.get(extension)
        if allowed_media_types is None:
            return False
        return media_type in allowed_media_types

    def _is_corrupted(self, *, path: Path, media_type: str) -> bool:
        """Detect common malformed container types without full parsing."""
        extension = path.suffix.lower()
        if media_type == "application/pdf":
            return not path.read_bytes()[: self.config.magic_byte_window].startswith(
                b"%PDF"
            )
        if extension not in self.config.office_extensions:
            return False
        return self._is_corrupted_zip_archive(path=path)

    def _is_corrupted_zip_archive(self, *, path: Path) -> bool:
        """Validate OOXML archives with lightweight ZIP integrity checks."""
        try:
            with zipfile.ZipFile(path) as archive:
                if "[Content_Types].xml" not in archive.namelist():
                    return True
                return archive.testzip() is not None
        except zipfile.BadZipFile:
            return True

    def _is_encrypted_pdf(self, *, path: Path) -> bool:
        """Detect encrypted PDFs using cheap header checks and PyMuPDF fallback."""
        header = path.read_bytes()[: self.config.magic_byte_window]
        if b"/Encrypt" in header:
            return True
        return self._is_encrypted_via_fitz(path=path)

    def _is_encrypted_via_fitz(self, *, path: Path) -> bool:
        """Use PyMuPDF when present because encrypted metadata can be subtle."""
        try:
            import fitz
        except Exception:
            return False
        try:
            with fitz.open(path) as document:  # pragma: no cover
                return bool(getattr(document, "needs_pass", False))
        except Exception:
            return False

    def _issue(self, code: str, *, blocking: bool) -> FileValidationIssue:
        """Create a stable issue object for a validation failure or warning."""
        return FileValidationIssue(
            code=code,
            message=self.config.validation_messages[code],
            severity="error" if blocking else "warning",
            blocking=blocking,
        )

    def _has_issue(
        self,
        code: str,
        *,
        issues: list[FileValidationIssue],
    ) -> bool:
        """Check whether a structured issue list contains a specific code."""
        return any(issue.code == code for issue in issues)
