"""Schema for parser input validation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FileValidationResult(BaseModel):
    """Describes whether a document passed pre-parse validation."""

    model_config = ConfigDict(frozen=True)

    extension: str = Field(description="Normalized file extension.")
    file_size_bytes: int = Field(ge=0, description="Document size in bytes.")
    encrypted: bool = Field(description="Whether the file appears encrypted.")
    supported_extension: bool = Field(description="Whether the extension is allowed.")
    is_valid: bool = Field(description="Whether parsing may continue.")
    failure_reason: str | None = Field(
        default=None,
        description="Stable failure reason when validation does not pass cleanly.",
    )
