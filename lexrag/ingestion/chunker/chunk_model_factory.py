"""Factory that materializes canonical chunk models from builder payloads."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from datetime import date
from typing import Any

from lexrag.ingestion.chunker.schemas.chunk import Chunk
from lexrag.ingestion.chunker.schemas.chunk_metadata import ChunkMetadata
from lexrag.ingestion.chunker.schemas.raw_chunk_payload import RawChunkPayload
from lexrag.ingestion.chunker.tokenization_engine import TokenizationEngine
from lexrag.ingestion.parser.parsed_block import ParsedBlock
from lexrag.utils import get_logger

logger = get_logger(__name__)


class ChunkModelFactory:
    """Builds stable `Chunk` models with deterministic IDs and lineage metadata."""

    def __init__(
        self,
        *,
        tokenization_engine: TokenizationEngine | None = None,
    ) -> None:
        self.tokenization_engine = tokenization_engine or TokenizationEngine()

    def build_chunks(
        self,
        raw_chunks: Sequence[RawChunkPayload | dict[str, Any]],
        *,
        parsed_blocks: list[ParsedBlock],
    ) -> list[Chunk]:
        """Converts raw chunk payloads into canonical chunk models."""
        if not raw_chunks:
            return []
        metadata_base = self._metadata_base(parsed_blocks=parsed_blocks)
        built_chunks: list[Chunk] = []
        for index, payload in enumerate(raw_chunks):
            raw_payload = self._coerce_payload(payload=payload)
            chunk = self._build_chunk(
                payload=raw_payload,
                index=index,
                total_chunks=len(raw_chunks),
                metadata_base=metadata_base,
            )
            if chunk is not None:
                built_chunks.append(chunk)
        return built_chunks

    def _coerce_payload(
        self,
        *,
        payload: RawChunkPayload | dict[str, Any],
    ) -> RawChunkPayload:
        """Normalizes caller input to the typed raw payload schema."""
        if isinstance(payload, RawChunkPayload):
            return payload
        return RawChunkPayload.model_validate(payload)

    def _build_chunk(
        self,
        *,
        payload: RawChunkPayload,
        index: int,
        total_chunks: int,
        metadata_base: dict[str, Any],
    ) -> Chunk | None:
        """Builds one canonical chunk or returns `None` for invalid payloads."""
        text = payload.text.strip()
        if not text or not payload.source_blocks:
            return None
        chunk_id = payload.chunk_id or self._chunk_id(
            payload=payload, doc_id=metadata_base["doc_id"], text=text
        )
        metadata = self._metadata(
            payload=payload,
            index=index,
            total_chunks=total_chunks,
            metadata_base=metadata_base,
            text=text,
        )
        self._warn_on_boundary_artifact(text=text, chunk_id=chunk_id)
        return Chunk(
            chunk_id=chunk_id,
            text=text,
            embedding_text=text,
            metadata=metadata,
            embedding=None,
        )

    def _metadata(
        self,
        *,
        payload: RawChunkPayload,
        index: int,
        total_chunks: int,
        metadata_base: dict[str, Any],
        text: str,
    ) -> ChunkMetadata:
        """Builds canonical metadata for one chunk payload."""
        source_blocks = payload.source_blocks
        first_block = source_blocks[0]
        return ChunkMetadata(
            doc_id=metadata_base["doc_id"],
            source_path=metadata_base["source_path"],
            doc_type=metadata_base["doc_type"],
            doc_date=metadata_base["doc_date"],
            chunk_index=index,
            total_chunks=max(total_chunks, 1),
            source_block_ids=[block.block_id for block in source_blocks],
            page_start=min(block.page for block in source_blocks),
            page_end=max(block.page for block in source_blocks),
            section_title=first_block.section,
            section_path=self._section_path(first_block=first_block),
            heading_anchor=payload.heading_anchor,
            chunk_type=payload.chunk_type,
            chunking_strategy=payload.chunking_strategy,
            token_count=payload.token_count
            or self.tokenization_engine.count_tokens(text),
            char_count=len(text),
            overlap_prev=payload.overlap_prev,
            overlap_next=payload.overlap_next,
            previous_chunk_id=payload.previous_chunk_id,
            next_chunk_id=payload.next_chunk_id,
            contains_table=any(block.block_type == "table" for block in source_blocks),
            contains_code=any(block.block_type == "code" for block in source_blocks),
            contains_ocr=any(block.is_ocr for block in source_blocks),
            avg_confidence=self._average_confidence(blocks=source_blocks),
            parser_used=self._parser_names(blocks=source_blocks),
            fallback_used=any(block.is_fallback_used for block in source_blocks),
            ocr_used=any(bool(block.ocr_used) for block in source_blocks),
            parse_confidence=self._parse_confidence(blocks=source_blocks),
            metadata=self._extension_metadata(payload=payload, text=text),
        )

    def _metadata_base(self, *, parsed_blocks: list[ParsedBlock]) -> dict[str, Any]:
        """Resolves stable document-level defaults shared by all built chunks."""
        if not parsed_blocks:
            return {
                "doc_id": "unknown_doc",
                "source_path": "unknown_source",
                "doc_type": None,
                "doc_date": None,
            }
        first = parsed_blocks[0]
        return {
            "doc_id": first.doc_id or "unknown_doc",
            "source_path": first.source_path or "unknown_source",
            "doc_type": first.doc_type,
            "doc_date": self._normalize_doc_date(first.metadata.get("doc_date")),
        }

    def _chunk_id(self, *, payload: RawChunkPayload, doc_id: str, text: str) -> str:
        """Generates a deterministic chunk ID from source block lineage and text."""
        source = "|".join(block.block_id for block in payload.source_blocks)
        digest = hashlib.sha1(f"{source}|{text[:500]}".encode()).hexdigest()[:12]
        page = min(block.page for block in payload.source_blocks)
        return f"{doc_id}_p{page}_{digest}"

    def _section_path(self, *, first_block: ParsedBlock) -> list[str]:
        """Builds a safe section path for retrieval and citation lineage."""
        if first_block.parent_section_path:
            return [*first_block.parent_section_path, first_block.section]
        if first_block.section:
            return [first_block.section]
        return []

    def _parser_names(self, *, blocks: list[ParsedBlock]) -> list[str]:
        """Returns parser names in deterministic order for observability."""
        return sorted({block.parser_used for block in blocks if block.parser_used})

    def _parse_confidence(self, *, blocks: list[ParsedBlock]) -> float | None:
        """Averages parse confidence when the parser emitted explicit scores."""
        values = [
            block.parse_confidence
            for block in blocks
            if block.parse_confidence is not None
        ]
        if not values:
            return None
        return round(sum(values) / len(values), 4)

    def _average_confidence(self, *, blocks: list[ParsedBlock]) -> float | None:
        """Averages OCR confidence across source blocks when present."""
        values = [block.confidence for block in blocks if block.confidence is not None]
        if not values:
            return None
        return round(sum(values) / len(values), 4)

    def _extension_metadata(
        self,
        *,
        payload: RawChunkPayload,
        text: str,
    ) -> dict[str, Any]:
        """Builds extension metadata that supports audit and debugging tooling."""
        return {
            "heading_anchor": payload.heading_anchor,
            "is_fallback_used": any(
                block.is_fallback_used for block in payload.source_blocks
            ),
            "source_spans": self._source_spans(
                text=text, source_blocks=payload.source_blocks
            ),
            **self._fallback_provenance(source_blocks=payload.source_blocks),
        }

    def _fallback_provenance(
        self,
        *,
        source_blocks: list[ParsedBlock],
    ) -> dict[str, Any]:
        """Extracts fallback parser provenance from source block metadata."""
        keys = {
            "fallback_event",
            "fallback_reason_code",
            "primary_parser",
            "fallback_parser",
            "primary_error_type",
            "primary_error_message",
        }
        for block in source_blocks:
            selected = {
                key: block.metadata[key] for key in keys if key in block.metadata
            }
            if selected:
                return selected
        return {}

    def _source_spans(
        self,
        *,
        text: str,
        source_blocks: list[ParsedBlock],
    ) -> list[dict[str, Any]]:
        """Locates approximate source spans for every contributing block."""
        spans: list[dict[str, Any]] = []
        cursor = 0
        for block in source_blocks:
            source_text = block.text.strip()
            if not source_text:
                continue
            start, end, match_type = self._locate_span(
                text=text, source_text=source_text, cursor=cursor
            )
            spans.append(
                self._span_payload(
                    block=block, start=start, end=end, match_type=match_type
                )
            )
            if end is not None:
                cursor = end
        return spans

    def _span_payload(
        self,
        *,
        block: ParsedBlock,
        start: int | None,
        end: int | None,
        match_type: str,
    ) -> dict[str, Any]:
        """Builds one source-span metadata record."""
        return {
            "block_id": block.block_id,
            "page": block.page,
            "start_char": start,
            "end_char": end,
            "matched": start is not None,
            "match_type": match_type,
        }

    def _locate_span(
        self,
        *,
        text: str,
        source_text: str,
        cursor: int,
    ) -> tuple[int | None, int | None, str]:
        """Matches by exact text first and token anchor second."""
        exact_match = self._exact_span(
            text=text, source_text=source_text, cursor=cursor
        )
        if exact_match is not None:
            return (exact_match[0], exact_match[1], "exact")
        anchor_match = self._token_anchor_span(text=text, source_text=source_text)
        if anchor_match is not None:
            return (anchor_match[0], anchor_match[1], "token_anchor")
        return (None, None, "unmatched")

    def _exact_span(
        self,
        *,
        text: str,
        source_text: str,
        cursor: int,
    ) -> tuple[int, int] | None:
        """Finds an exact character span with cursor-aware fallback search."""
        start = text.find(source_text, cursor)
        if start < 0:
            start = text.find(source_text)
        if start < 0:
            return None
        return (start, start + len(source_text))

    def _token_anchor_span(
        self,
        *,
        text: str,
        source_text: str,
    ) -> tuple[int, int] | None:
        """Falls back to a token anchor when the block text was reformatted."""
        source_tokens = self._token_positions(text=source_text)
        chunk_tokens = self._token_positions(text=text)
        if not source_tokens or not chunk_tokens:
            return None
        anchor_words = [token.lower() for token, _, _ in source_tokens[:4]]
        anchor_index = self._subsequence_index(
            haystack=[token.lower() for token, _, _ in chunk_tokens],
            needle=anchor_words,
        )
        if anchor_index is None:
            return None
        start = chunk_tokens[anchor_index][1]
        end = chunk_tokens[anchor_index + len(anchor_words) - 1][2]
        return (start, end)

    def _token_positions(self, *, text: str) -> list[tuple[str, int, int]]:
        """Extracts alphanumeric tokens with source character offsets."""
        return [
            (match.group(0), match.start(), match.end())
            for match in re.finditer(r"[A-Za-z0-9]+", text)
        ]

    def _subsequence_index(
        self,
        *,
        haystack: list[str],
        needle: list[str],
    ) -> int | None:
        """Returns the first position where a token sequence appears."""
        if not needle or len(needle) > len(haystack):
            return None
        limit = len(haystack) - len(needle)
        for start in range(limit + 1):
            if haystack[start : start + len(needle)] == needle:
                return start
        return None

    def _normalize_doc_date(self, value: Any) -> date | None:
        """Normalizes persisted document dates to a `date` object."""
        if value is None or isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                return None
        return None

    def _warn_on_boundary_artifact(self, *, text: str, chunk_id: str) -> None:
        """Logs likely boundary artifacts that deserve offline inspection."""
        stripped = text.lstrip()
        if stripped and stripped[0].islower():
            logger.warning(
                "Possible chunk boundary artifact detected for chunk_id=%s", chunk_id
            )
