"""Production-grade file ingestion boundary for pre-parse document checks.

This package implements the architecture-defined file ingestion layers:

1. File validation
2. File type detection

The package is intentionally independent from parsing so callers can validate
and classify uploads before any expensive parser dependency is invoked.
"""

from __future__ import annotations

from .build_antivirus_scanner import build_antivirus_scanner
from .clamav_antivirus_scanner import ClamAVAntivirusScanner
from .file_ingestion_gateway import FileIngestionGateway
from .file_loader_pipeline import FileLoaderPipeline
from .file_path_resolver import FilePathResolver
from .file_type_detector import FileTypeDetector
from .file_validation_service import FileValidationService
from .no_op_antivirus_scanner import NoOpAntivirusScanner
from .schemas import (
    AntivirusScanResult,
    FileIngestionConfig,
    FileIngestionReport,
    FileLoadResult,
    FileTypeDetection,
    FileValidationIssue,
    FileValidationResult,
)

__all__ = [
    "AntivirusScanResult",
    "ClamAVAntivirusScanner",
    "FileIngestionConfig",
    "FileIngestionGateway",
    "FileIngestionReport",
    "FileLoadResult",
    "FileLoaderPipeline",
    "FilePathResolver",
    "FileTypeDetection",
    "FileTypeDetector",
    "FileValidationIssue",
    "FileValidationResult",
    "FileValidationService",
    "NoOpAntivirusScanner",
    "build_antivirus_scanner",
]
