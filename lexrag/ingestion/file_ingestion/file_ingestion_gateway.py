"""Gateway combining validation and type detection.

This object gives the parser layer a single architecture-aligned entrypoint for
the full pre-parse file ingestion phase, keeping validation and classification
decisions together for auditability.
"""

from __future__ import annotations

from pathlib import Path

from lexrag.ingestion.file_ingestion.file_type_detector import FileTypeDetector
from lexrag.ingestion.file_ingestion.file_validation_service import FileValidationService
from lexrag.ingestion.file_ingestion.schemas.file_ingestion_config import FileIngestionConfig
from lexrag.ingestion.file_ingestion.schemas.file_ingestion_report import FileIngestionReport


class FileIngestionGateway:
    """Run file validation and type detection as one cohesive operation."""

    def __init__(
        self,
        config: FileIngestionConfig | None = None,
        *,
        validator: FileValidationService | None = None,
        detector: FileTypeDetector | None = None,
    ) -> None:
        """Initialize gateway collaborators.

        Args:
            config: Optional ingestion configuration.
            validator: Optional validation service override.
            detector: Optional type detector override.
        """
        self.config = config or FileIngestionConfig()
        self.validator = validator or FileValidationService(config=self.config)
        self.detector = detector or FileTypeDetector(config=self.config)

    def inspect(self, path: Path) -> FileIngestionReport:
        """Inspect a single file and return both validation and detection data.

        Args:
            path: File path to inspect.

        Returns:
            Canonical file ingestion report.
        """
        validation = self.validator.validate(path)
        detection = self.detector.detect(path)
        return FileIngestionReport(validation=validation, detection=detection)

    def inspect_batch(self, paths: list[Path]) -> list[FileIngestionReport]:
        """Inspect a batch while enabling duplicate detection within the batch.

        Args:
            paths: Files to inspect together.

        Returns:
            Canonical inspection reports in input order.
        """
        validations = self.validator.validate_many(paths)
        detections = [self.detector.detect(path) for path in paths]
        return [
            FileIngestionReport(validation=validation, detection=detection)
            for validation, detection in zip(validations, detections, strict=True)
        ]
