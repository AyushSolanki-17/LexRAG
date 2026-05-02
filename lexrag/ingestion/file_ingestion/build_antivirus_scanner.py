"""Build the configured antivirus scanner for file ingestion."""

from __future__ import annotations

from lexrag.ingestion.file_ingestion.antivirus_scanner import AntivirusScanner
from lexrag.ingestion.file_ingestion.clamav_antivirus_scanner import (
    ClamAVAntivirusScanner,
)
from lexrag.ingestion.file_ingestion.no_op_antivirus_scanner import NoOpAntivirusScanner
from lexrag.ingestion.file_ingestion.schemas.file_ingestion_config import (
    FileIngestionConfig,
)


def build_antivirus_scanner(
    config: FileIngestionConfig | None = None,
) -> AntivirusScanner:
    """Return the best available antivirus scanner for the current config."""
    resolved = config or FileIngestionConfig()
    if resolved.clamav_socket_path or resolved.clamav_host:
        return ClamAVAntivirusScanner(config=resolved)
    return NoOpAntivirusScanner(config=resolved)
