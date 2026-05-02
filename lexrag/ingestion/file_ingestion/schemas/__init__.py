"""Schemas for the file ingestion package."""

from __future__ import annotations

from .antivirus_scan_result import AntivirusScanResult
from .file_ingestion_config import FileIngestionConfig
from .file_ingestion_report import FileIngestionReport
from .file_load_result import FileLoadResult
from .file_type_detection import FileTypeDetection
from .file_validation_issue import FileValidationIssue
from .file_validation_result import FileValidationResult

__all__ = [
    "AntivirusScanResult",
    "FileIngestionConfig",
    "FileIngestionReport",
    "FileLoadResult",
    "FileTypeDetection",
    "FileValidationIssue",
    "FileValidationResult",
]
