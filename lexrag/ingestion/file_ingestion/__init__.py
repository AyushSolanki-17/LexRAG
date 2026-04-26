"""Production-grade file ingestion boundary for pre-parse document checks.

This package implements the architecture-defined file ingestion layers:

1. File validation
2. File type detection

The package is intentionally independent from parsing so callers can validate
and classify uploads before any expensive parser dependency is invoked.
"""

from __future__ import annotations

from .file_ingestion_gateway import FileIngestionGateway
from .file_type_detector import FileTypeDetector
from .file_validation_service import FileValidationService
from .no_op_antivirus_scanner import NoOpAntivirusScanner
from .schemas import (
    AntivirusScanResult,
    FileIngestionConfig,
    FileIngestionReport,
    FileTypeDetection,
    FileValidationIssue,
    FileValidationResult,
)

__all__ = [
    "AntivirusScanResult",
    "FileIngestionConfig",
    "FileIngestionGateway",
    "FileIngestionReport",
    "FileTypeDetection",
    "FileTypeDetector",
    "FileValidationIssue",
    "FileValidationResult",
    "FileValidationService",
    "NoOpAntivirusScanner",
]
