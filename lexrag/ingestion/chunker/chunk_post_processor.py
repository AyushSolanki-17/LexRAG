"""Post-processing for canonical chunks before they leave the chunking layer."""

from __future__ import annotations

from lexrag.ingestion.chunker.schemas.chunk import Chunk
from lexrag.ingestion.chunker.schemas.chunk_metadata import ChunkMetadata
from lexrag.ingestion.chunker.schemas.chunking_config import ChunkingConfig


class ChunkPostProcessor:
    """Validates adjacency metadata and computes chunk quality signals.

    This is the final step in the chunking package before embedding
    preparation. It centralizes cross-chunk enrichments so builders can focus
    on segmentation logic rather than mutating finalized models.
    """

    def __init__(self, *, config: ChunkingConfig) -> None:
        self.config = config

    def process(self, chunks: list[Chunk]) -> list[Chunk]:
        """Enriches chunk metadata with adjacency links and quality scores."""
        processed: list[Chunk] = []
        for index, chunk in enumerate(chunks):
            previous_chunk = chunks[index - 1] if index > 0 else None
            next_chunk = chunks[index + 1] if index < len(chunks) - 1 else None
            metadata = self._build_metadata(
                chunk=chunk,
                previous_chunk=previous_chunk,
                next_chunk=next_chunk,
            )
            processed.append(chunk.model_copy(update={"metadata": metadata}))
        return processed

    def _build_metadata(
        self,
        *,
        chunk: Chunk,
        previous_chunk: Chunk | None,
        next_chunk: Chunk | None,
    ) -> ChunkMetadata:
        """Copies metadata while wiring adjacency and computed quality fields."""
        payload = chunk.metadata.model_dump()
        payload["previous_chunk_id"] = (
            previous_chunk.chunk_id if previous_chunk else None
        )
        payload["next_chunk_id"] = next_chunk.chunk_id if next_chunk else None
        payload["overlap_prev"] = previous_chunk is not None
        payload["overlap_next"] = next_chunk is not None
        payload["chunk_quality_score"] = self._quality_score(metadata=chunk.metadata)
        return ChunkMetadata.model_validate(payload)

    def _quality_score(self, *, metadata: ChunkMetadata) -> float:
        """Computes a bounded chunk quality score from architecture signals."""
        parse_score = metadata.parse_confidence or metadata.avg_confidence or 0.7
        heading_score = 1.0 if metadata.heading_anchor else 0.0
        token_score = self._token_budget_score(metadata=metadata)
        section_score = 1.0 if metadata.section_path else 0.0
        ocr_score = 0.0 if metadata.contains_ocr else 1.0
        score = (
            (0.30 * parse_score)
            + (0.20 * heading_score)
            + (0.20 * token_score)
            + (0.15 * section_score)
            + (0.15 * ocr_score)
        )
        return round(min(max(score, 0.0), 1.0), 4)

    def _token_budget_score(self, *, metadata: ChunkMetadata) -> float:
        """Rewards chunks that land within the configured size envelope."""
        count = metadata.token_count or 0
        if self.config.min_chunk_tokens <= count <= self.config.max_chunk_tokens:
            return 1.0
        if 0 < count < self.config.min_chunk_tokens:
            return round(count / self.config.min_chunk_tokens, 4)
        if count > self.config.max_chunk_tokens:
            return round(self.config.max_chunk_tokens / count, 4)
        return 0.0
