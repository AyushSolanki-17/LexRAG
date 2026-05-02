"""Schema for canonical file loader outcomes."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .file_ingestion_report import FileIngestionReport


class FileLoadResult(BaseModel):
    """Describe whether a resolved file is safe and ready for parsing."""

    model_config = ConfigDict(frozen=True)

    requested_path: str = Field(
        description="Original user- or caller-provided path string."
    )
    resolved_path: str = Field(
        description="Canonical absolute file path after safety checks."
    )
    ingestion_report: FileIngestionReport = Field(
        description="Validation and detection report for the resolved file."
    )
    is_ready: bool = Field(
        description="Whether the file is permitted to proceed into parsing."
    )
    rejection_reason: str | None = Field(
        default=None,
        description="Stable blocking reason when the file cannot proceed.",
    )
