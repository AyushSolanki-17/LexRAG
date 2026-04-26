"""OCR-only parser placeholder.

The architecture requires an OCR route, but this repository does not yet ship
an OCR provider. We keep the route explicit so the orchestration layer is ready
for the future implementation instead of hiding the gap.
"""

from __future__ import annotations

from pathlib import Path

from lexrag.ingestion.parser.base_document_parser import BaseDocumentParser
from lexrag.ingestion.parser.schemas.parsed_block import ParsedBlock


class OCROnlyParser(BaseDocumentParser):
    """Explicit OCR-only backend placeholder."""

    def parse(self, path: Path) -> list[ParsedBlock]:
        """Raise an explicit error until an OCR provider is configured.

        Args:
            path: Document path requested for OCR parsing.

        Returns:
            This method never returns because OCR is not configured yet.
        """
        raise RuntimeError(
            f"OCR-only parser is not configured for this deployment: {path}"
        )
