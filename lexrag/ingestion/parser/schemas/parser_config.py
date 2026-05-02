"""Configuration schema for parser orchestration."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ParserConfig(BaseModel):
    """Configuration knobs for the parsing package."""

    model_config = ConfigDict(frozen=True)

    allowed_extensions: tuple[str, ...] = Field(
        default=(
            ".pdf",
            ".html",
            ".htm",
            ".txt",
            ".md",
            ".xml",
            ".docx",
            ".xlsx",
            ".pptx",
            ".png",
            ".jpg",
            ".jpeg",
            ".tif",
            ".tiff",
            ".eml",
            ".msg",
        ),
        description="Extensions accepted by the parsing layer.",
    )
    min_file_size_bytes: int = Field(
        default=1,
        ge=0,
        description="Minimum accepted file size in bytes.",
    )
    max_file_size_bytes: int = Field(
        default=100_000_000,
        ge=1,
        description="Maximum accepted file size in bytes.",
    )
    magic_byte_window: int = Field(
        default=4096,
        ge=64,
        description="Number of leading bytes used for file sniffing.",
    )
    follow_symlinks: bool = Field(
        default=False,
        description="Whether the parsing boundary may traverse symlinked paths.",
    )
    allowed_root_paths: tuple[str, ...] = Field(
        default=(),
        description="Optional root directories that parse requests must stay inside.",
    )
    max_batch_files: int = Field(
        default=1000,
        ge=1,
        description="Maximum number of files a single path expansion may include.",
    )
    clamav_socket_path: str | None = Field(
        default=None,
        description="Optional UNIX socket path for a local ClamAV daemon.",
    )
    clamav_host: str | None = Field(
        default=None,
        description="Optional hostname for a network-accessible ClamAV daemon.",
    )
    clamav_port: int | None = Field(
        default=None,
        ge=1,
        le=65535,
        description="Optional port for a network-accessible ClamAV daemon.",
    )
    block_on_missing_antivirus: bool | None = Field(
        default=None,
        description="Override for whether missing antivirus blocks parsing.",
    )
    block_on_antivirus_error: bool = Field(
        default=True,
        description="Whether antivirus runtime errors should block parsing.",
    )
    scanned_pdf_min_chars_per_page: int = Field(
        default=50,
        ge=0,
        description="Average character threshold below which a PDF is treated as scanned.",
    )
    image_heavy_page_ratio: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Fraction of pages with images required to mark a PDF image-heavy.",
    )
    image_heavy_max_chars_per_page: int = Field(
        default=200,
        ge=0,
        description="Maximum average characters per page for image-heavy routing.",
    )
    ocr_render_dpi: int = Field(
        default=300,
        ge=72,
        le=600,
        description="Rasterization DPI used before OCRing scanned PDFs.",
    )
