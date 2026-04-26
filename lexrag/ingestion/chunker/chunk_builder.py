"""Chunk builder that materializes raw payloads from planner output."""

from __future__ import annotations

from lexrag.ingestion.chunker.chunk_similarity_engine import SimilarityEngine
from lexrag.ingestion.chunker.schemas.chunking_config import ChunkingConfig
from lexrag.ingestion.chunker.schemas.planned_chunk import PlannedChunk
from lexrag.ingestion.chunker.schemas.raw_chunk_payload import RawChunkPayload
from lexrag.ingestion.chunker.tokenization_engine import TokenizationEngine
from lexrag.ingestion.parser.parsed_block import ParsedBlock


class ChunkBuilder:
    """Builds raw chunk payloads according to planner intent and token budgets."""

    def __init__(
        self,
        *,
        config: ChunkingConfig | None = None,
        tokenization_engine: TokenizationEngine | None = None,
        similarity_engine: SimilarityEngine | None = None,
    ) -> None:
        self.config = config or ChunkingConfig()
        self.tokenization_engine = tokenization_engine or TokenizationEngine()
        self.similarity_engine = similarity_engine or SimilarityEngine()

    def build(self, plans: list[PlannedChunk]) -> list[RawChunkPayload]:
        """Converts planner records into ordered raw chunk payloads."""
        raw_chunks: list[RawChunkPayload] = []
        buffer: list[PlannedChunk] = []
        current_anchor: str | None = None
        for plan in plans:
            current_anchor = self._apply_plan(
                plan=plan,
                buffer=buffer,
                raw_chunks=raw_chunks,
                current_anchor=current_anchor,
            )
        self._flush_buffer(
            buffer=buffer, raw_chunks=raw_chunks, heading_anchor=current_anchor
        )
        self._mark_adjacency(raw_chunks=raw_chunks)
        return raw_chunks

    def _apply_plan(
        self,
        *,
        plan: PlannedChunk,
        buffer: list[PlannedChunk],
        raw_chunks: list[RawChunkPayload],
        current_anchor: str | None,
    ) -> str | None:
        """Processes one planner record and returns the current heading anchor."""
        if plan.chunking_strategy == "heading_anchored":
            self._flush_buffer(
                buffer=buffer, raw_chunks=raw_chunks, heading_anchor=current_anchor
            )
            return plan.heading_anchor or plan.text
        if plan.chunking_strategy == "sliding_window":
            self._flush_buffer(
                buffer=buffer, raw_chunks=raw_chunks, heading_anchor=current_anchor
            )
            raw_chunks.extend(
                self._windowed_chunks(plan=plan, heading_anchor=current_anchor)
            )
            return current_anchor
        if plan.standalone:
            self._flush_buffer(
                buffer=buffer, raw_chunks=raw_chunks, heading_anchor=current_anchor
            )
            raw_chunks.append(
                self._standalone_chunk(plan=plan, heading_anchor=current_anchor)
            )
            return current_anchor
        if self._should_flush(buffer=buffer, incoming=plan):
            self._flush_buffer(
                buffer=buffer, raw_chunks=raw_chunks, heading_anchor=current_anchor
            )
        buffer.append(plan)
        return current_anchor or plan.heading_anchor

    def _should_flush(
        self, *, buffer: list[PlannedChunk], incoming: PlannedChunk
    ) -> bool:
        """Determines whether the incoming plan should start a new chunk."""
        if not buffer:
            return False
        if incoming.section_boundary:
            return True
        if (
            self._buffer_tokens(buffer=buffer) + incoming.token_count
            > self.config.max_chunk_tokens
        ):
            return True
        if self._buffer_tokens(buffer=buffer) < self.config.min_chunk_tokens:
            return False
        previous = buffer[-1]
        similarity = self.similarity_engine.score_text_pair(
            previous.text, incoming.text
        )
        return similarity < self.config.similarity_threshold

    def _flush_buffer(
        self,
        *,
        buffer: list[PlannedChunk],
        raw_chunks: list[RawChunkPayload],
        heading_anchor: str | None,
    ) -> None:
        """Materializes buffered plans into a merged semantic payload."""
        if not buffer:
            return
        raw_chunks.append(
            self._merged_chunk(plans=list(buffer), heading_anchor=heading_anchor)
        )
        buffer.clear()

    def _merged_chunk(
        self,
        *,
        plans: list[PlannedChunk],
        heading_anchor: str | None,
    ) -> RawChunkPayload:
        """Builds one semantic-merge payload from buffered plans."""
        blocks = [plan.block for plan in plans]
        text = self._compose_text(
            body_parts=[plan.text for plan in plans], heading_anchor=heading_anchor
        )
        return RawChunkPayload(
            text=text,
            source_blocks=blocks,
            chunking_strategy="semantic_merge",
            chunk_type=self._chunk_type(blocks=blocks),
            token_count=sum(plan.token_count for plan in plans),
            heading_anchor=heading_anchor,
        )

    def _standalone_chunk(
        self,
        *,
        plan: PlannedChunk,
        heading_anchor: str | None,
    ) -> RawChunkPayload:
        """Builds a standalone payload for tables, code, and protected blocks."""
        text = self._compose_text(body_parts=[plan.text], heading_anchor=heading_anchor)
        return RawChunkPayload(
            text=text,
            source_blocks=[plan.block],
            chunking_strategy=plan.chunking_strategy,
            chunk_type=plan.block.block_type,
            token_count=plan.token_count,
            heading_anchor=heading_anchor,
        )

    def _windowed_chunks(
        self,
        *,
        plan: PlannedChunk,
        heading_anchor: str | None,
    ) -> list[RawChunkPayload]:
        """Splits an oversized block into token windows with configured overlap."""
        tokens = self.tokenization_engine.tokenize(plan.text)
        windows = self.tokenization_engine.window_tokens(
            tokens=tokens,
            window_size=self.config.target_chunk_tokens,
            overlap=self.config.overlap_tokens,
        )
        return [
            RawChunkPayload(
                text=self._compose_text(
                    body_parts=[self.tokenization_engine.detokenize(window)],
                    heading_anchor=heading_anchor,
                ),
                source_blocks=[plan.block],
                chunking_strategy="sliding_window",
                chunk_type=plan.block.block_type,
                token_count=len(window),
                heading_anchor=heading_anchor,
            )
            for window in windows
        ]

    def _mark_adjacency(self, *, raw_chunks: list[RawChunkPayload]) -> None:
        """Marks boolean overlap adjacency for downstream compatibility."""
        for index, payload in enumerate(raw_chunks):
            payload.overlap_prev = index > 0
            payload.overlap_next = index < len(raw_chunks) - 1

    def _compose_text(
        self,
        *,
        body_parts: list[str],
        heading_anchor: str | None,
    ) -> str:
        """Prepends heading context once so chunks remain retrieval-safe."""
        parts = [part.strip() for part in body_parts if part.strip()]
        if heading_anchor and parts and parts[0] != heading_anchor:
            parts.insert(0, heading_anchor)
        return "\n\n".join(parts).strip()

    def _buffer_tokens(self, *, buffer: list[PlannedChunk]) -> int:
        """Returns the total token count for the buffered planner records."""
        return sum(plan.token_count for plan in buffer)

    def _chunk_type(self, *, blocks: list[ParsedBlock]) -> str:
        """Resolves a stable chunk type from source block composition."""
        types = {block.block_type for block in blocks if block.block_type}
        if "table" in types:
            return "table"
        if "code" in types:
            return "code"
        if "list" in types:
            return "list"
        return "paragraph"
