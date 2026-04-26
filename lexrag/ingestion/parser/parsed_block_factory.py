"""Factories for canonical parsed block creation."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from lexrag.ingestion.parser.schemas.parsed_block import ParsedBlock


class ParsedBlockFactory:
    """Coerce legacy and backend-specific payloads into ``ParsedBlock``."""

    def build_blocks(
        self,
        *,
        path: Path,
        parser_name: str,
        parsed_items: list[Any],
    ) -> list[ParsedBlock]:
        """Normalize backend outputs into canonical parsed blocks.

        Args:
            path: Source document path.
            parser_name: Stable parser name used for provenance.
            parsed_items: Backend output objects to normalize.

        Returns:
            Canonical parsed blocks with deterministic identity.
        """
        normalized: list[ParsedBlock] = []
        for index, item in enumerate(parsed_items, start=1):
            normalized.append(
                self._coerce_item(
                    path=path,
                    parser_name=parser_name,
                    item=item,
                    index=index,
                )
            )
        return normalized

    def _coerce_item(
        self,
        *,
        path: Path,
        parser_name: str,
        item: Any,
        index: int,
    ) -> ParsedBlock:
        """Convert a backend item into the shared block schema."""
        if isinstance(item, ParsedBlock):
            return self._enrich_parsed_block(
                path=path, parser_name=parser_name, item=item
            )
        payload = item if isinstance(item, dict) else self._object_to_payload(item=item)
        return self._build_block_from_payload(
            path=path,
            parser_name=parser_name,
            payload=payload,
            index=index,
        )

    def _enrich_parsed_block(
        self,
        *,
        path: Path,
        parser_name: str,
        item: ParsedBlock,
    ) -> ParsedBlock:
        """Backfill required provenance fields on existing parsed blocks."""
        updates = {
            "doc_id": item.doc_id or path.stem,
            "source_path": item.source_path or str(path),
            "source_name": item.source_name or path.name,
            "doc_type": item.doc_type or path.suffix.lower().lstrip(".") or None,
            "parser_used": item.parser_used or parser_name,
        }
        return item.model_copy(update=updates)

    def _build_block_from_payload(
        self,
        *,
        path: Path,
        parser_name: str,
        payload: dict[str, Any],
        index: int,
    ) -> ParsedBlock:
        """Build a parsed block from a generic payload."""
        text = str(payload.get("text", "")).strip()
        page = self._resolve_page(value=payload.get("page"), fallback=index)
        section = str(payload.get("section", f"Page {page}")).strip() or f"Page {page}"
        metadata = dict(payload.get("metadata", {}) or {})
        return ParsedBlock(
            doc_id=path.stem,
            source_path=str(path),
            source_name=path.name,
            doc_type=path.suffix.lower().lstrip(".") or None,
            block_id=self._build_block_id(path=path, page=page, order=index, text=text),
            page=page,
            section=section,
            block_type="paragraph",
            text=text,
            markdown=text,
            order_in_page=index,
            parser_used=parser_name,
            metadata=metadata,
        )

    def _object_to_payload(self, *, item: Any) -> dict[str, Any]:
        """Extract a generic payload from legacy parser DTOs."""
        return {
            "page": getattr(item, "page", None),
            "section": getattr(item, "section", None),
            "text": getattr(item, "text", None),
            "metadata": getattr(item, "metadata", {}) or {},
        }

    def _resolve_page(self, *, value: Any, fallback: int) -> int:
        """Normalize page values into safe 1-based integers."""
        try:
            page = int(value)
        except (TypeError, ValueError):
            return max(fallback, 1)
        return page if page >= 1 else max(fallback, 1)

    def _build_block_id(self, *, path: Path, page: int, order: int, text: str) -> str:
        """Build deterministic block identifiers."""
        digest = hashlib.sha1(text[:500].encode("utf-8")).hexdigest()[:12]
        return f"{path.stem}_p{page}_b{order}_{digest}"
