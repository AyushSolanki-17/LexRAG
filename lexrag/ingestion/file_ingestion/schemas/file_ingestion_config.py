"""Configuration schema for file ingestion layers 2.1 and 2.2."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FileIngestionConfig(BaseModel):
    """Configuration knobs for validation and type detection."""

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
        description="Extensions accepted by the file ingestion boundary.",
    )
    office_extensions: tuple[str, ...] = Field(
        default=(".docx", ".xlsx", ".pptx"),
        description="OOXML container formats requiring ZIP integrity validation.",
    )
    image_extensions: tuple[str, ...] = Field(
        default=(".png", ".jpg", ".jpeg", ".tif", ".tiff"),
        description="Image formats routed toward OCR-capable parsing paths.",
    )
    email_extensions: tuple[str, ...] = Field(
        default=(".eml", ".msg"),
        description="Email container formats handled specially by detection.",
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
        description="Leading byte window used for MIME sniffing and header checks.",
    )
    follow_symlinks: bool = Field(
        default=False,
        description="Whether file loading may traverse symlinked paths.",
    )
    max_batch_files: int = Field(
        default=1000,
        ge=1,
        description="Maximum number of concrete files a single load request may expand to.",
    )
    allowed_root_paths: tuple[str, ...] = Field(
        default=(),
        description="Optional absolute roots that loaded files must remain inside.",
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
        description="Override for whether missing antivirus should block ingestion.",
    )
    block_on_antivirus_error: bool = Field(
        default=True,
        description="Whether antivirus runtime errors should block ingestion.",
    )
    extension_media_type_map: dict[str, tuple[str, ...]] = Field(
        default={
            ".pdf": ("application/pdf",),
            ".html": ("text/html",),
            ".htm": ("text/html",),
            ".txt": ("text/plain",),
            ".md": ("text/plain",),
            ".xml": ("application/xml", "text/plain"),
            ".docx": (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
            ".xlsx": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
            ".pptx": (
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ),
            ".png": ("image/png",),
            ".jpg": ("image/jpeg",),
            ".jpeg": ("image/jpeg",),
            ".tif": ("image/tiff",),
            ".tiff": ("image/tiff",),
            ".eml": ("message/rfc822", "text/plain"),
            ".msg": ("application/octet-stream",),
        },
        description="Allowed MIME-like media types for each allowlisted extension.",
    )
    validation_messages: dict[str, str] = Field(
        default={
            "antivirus_infected": "The file was blocked by antivirus scanning.",
            "antivirus_error": "The antivirus scan could not be completed safely.",
            "corrupt_file": "The file appears malformed or truncated.",
            "duplicate_file_in_batch": "The same file content was uploaded twice in one batch.",
            "encrypted_pdf": "Encrypted PDFs must be decrypted before ingestion.",
            "extension_media_mismatch": "The file extension does not match the detected content type.",
            "file_empty": "The file is empty.",
            "file_too_large": "The file exceeds the configured size limit.",
            "hash_unavailable": "The file could not be hashed safely.",
            "unsupported_extension": "The file extension is not supported.",
        },
        description="Stable user-facing messages for structured validation issues.",
    )
