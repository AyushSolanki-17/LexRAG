"""Optional unstructured parser backend."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lexrag.ingestion.parser.base_document_parser import BaseDocumentParser
from lexrag.ingestion.parser.schemas.parsed_block import ParsedBlock


class UnstructuredParser(BaseDocumentParser):
    """Broad-coverage parser used after higher-fidelity backends fail."""

    def parse(self, path: Path) -> list[ParsedBlock]:
        """Parse a document with the optional ``unstructured`` dependency.

        Args:
            path: Document path to parse.

        Returns:
            Canonical parsed blocks extracted from the document.
        """
        partition = self._load_partition_function()
        elements = partition(filename=str(path))
        return self._build_blocks(path=path, elements=elements)

    def _load_partition_function(self):
        """Load the ``unstructured`` auto-partition entry point."""
        try:
            from unstructured.partition.auto import partition
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "Unstructured is not installed. Add the dependency to enable this fallback."
            ) from exc
        return partition

    def _build_blocks(self, *, path: Path, elements: list[Any]) -> list[ParsedBlock]:
        """Convert unstructured elements into canonical blocks."""
        blocks = []
        for index, element in enumerate(elements, start=1):
            text = str(element).strip()
            if not text:
                continue
            blocks.append(
                ParsedBlock(
                    doc_id=path.stem,
                    source_path=str(path),
                    source_name=path.name,
                    doc_type=path.suffix.lower().lstrip(".") or None,
                    block_id=f"{path.stem}_p1_b{index}_unstructured",
                    page=1,
                    section=f"Element {index}",
                    block_type="paragraph",
                    text=text,
                    markdown=text,
                    order_in_page=index,
                    parser_used=self.parser_name,
                    metadata={
                        "parser": self.parser_name,
                        "extraction_mode": "partition",
                    },
                )
            )
        if blocks:
            return blocks
        raise RuntimeError(f"Unstructured returned no parsed blocks for {path}")
