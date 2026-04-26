"""Schema for file type detection results."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FileTypeDetection(BaseModel):
    """Describes the detected document family used for parser routing."""

    model_config = ConfigDict(frozen=True)

    extension: str = Field(description="Normalized file extension.")
    detected_type: str = Field(description="Detected document family.")
    has_pdf_header: bool = Field(description="Whether the file starts with ``%PDF``.")
    is_html: bool = Field(description="Whether HTML markers were detected.")
    is_text_like: bool = Field(
        description="Whether the payload appears UTF-8 text-like."
    )
