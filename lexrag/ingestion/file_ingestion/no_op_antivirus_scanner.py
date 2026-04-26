"""Default antivirus implementation used when no scanner is wired.

Production deployments can replace this class with a real scanner backed by
ClamAV, an internal malware gateway, or a SaaS provider. Keeping the default
behavior explicit avoids pretending that a scan happened when it did not.
"""

from __future__ import annotations

from pathlib import Path

from lexrag.ingestion.file_ingestion.antivirus_scanner import AntivirusScanner
from lexrag.ingestion.file_ingestion.schemas.antivirus_scan_result import AntivirusScanResult


class NoOpAntivirusScanner(AntivirusScanner):
    """Return a structured "skipped" scan result when no scanner is configured."""

    def scan(self, path: Path) -> AntivirusScanResult:
        """Return a non-blocking placeholder result.

        Args:
            path: File path to inspect.

        Returns:
            Scan result explaining that malware scanning was skipped.
        """
        return AntivirusScanResult(
            engine_name="noop",
            status="skipped",
            details=f"No antivirus scanner configured for {path.name}.",
            signature_name=None,
            blocking=False,
        )
