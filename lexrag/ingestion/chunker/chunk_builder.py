"""Chunk builder for semantic chunking with similarity-based merging.

This module provides the ChunkBuilder class which handles the construction
of retrieval-ready chunks from planned units using semantic similarity
analysis and token limit enforcement.
"""

from __future__ import annotations

from typing import Any

from lexrag.ingestion.embedder import EmbeddingMode, build_embedder


class ChunkBuilder:
    """Builder for creating retrieval-safe raw chunks from planner units.
    
    This class is responsible for converting planned units into raw chunk
    payloads using semantic similarity analysis and token limit enforcement.
    It implements intelligent chunking strategies that preserve content
    coherence while respecting size constraints.
    
    Key responsibilities:
        - Semantic merging based on embedding similarity
        - Token limit enforcement with configurable bounds
        - Intelligent buffer flushing for optimal chunk boundaries
        - Standalone block preservation (tables, code, headings)
        - Source block lineage tracking for traceability
    
    Attributes:
        similarity_threshold: Minimum cosine similarity for merging blocks.
        min_tokens: Minimum tokens required for a valid chunk.
        max_tokens: Maximum tokens allowed per chunk.
        embedder: Embedding engine for similarity calculations.
    """

    def __init__(
        self,
        *,
        similarity_threshold: float = 0.78,
        min_tokens: int = 150,
        max_tokens: int = 600,
        embedding_mode: EmbeddingMode = "production",
    ) -> None:
        """Initializes the ChunkBuilder with configuration parameters.
        
        Args:
            similarity_threshold: Minimum cosine similarity (0.0-1.0) required
                for merging consecutive blocks. Lower values create more chunks.
            min_tokens: Minimum number of tokens required for a valid chunk.
                Chunks below this threshold will be merged if possible.
            max_tokens: Maximum number of tokens allowed per chunk. Chunks
                exceeding this limit will be split.
            embedding_mode: Embedding mode for the underlying embedder.
                Controls model selection and performance characteristics.
        """
        self.similarity_threshold = similarity_threshold
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.embedder = build_embedder(mode=embedding_mode)

    def build(
        self,
        units: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Builds raw chunk payloads from planned units.
        
        This method processes planned units and creates raw chunk payloads
        using semantic similarity analysis and token limit enforcement.
        It handles standalone blocks, manages buffer accumulation, and
        ensures optimal chunk boundaries.
        
        Args:
            units: List of planned units from the semantic planner,
                each containing text, embeddings, and metadata.
                
        Returns:
            List of raw chunk payloads containing text and source block
            references ready for final Chunk object creation.
        """

        if not units:
            return []

        self._attach_embeddings(units)

        raw_chunks: list[dict[str, Any]] = []
        buffer: list[dict[str, Any]] = []

        previous_embedding = None

        for unit in units:
            if unit["force_standalone"] or unit["is_boundary"]:
                if buffer:
                    raw_chunks.append(self._flush(buffer))
                    buffer = []

                raw_chunks.append(self._single_block_chunk(unit))
                previous_embedding = None
                continue

            should_split = self._should_split(
                unit=unit,
                buffer=buffer,
                previous_embedding=previous_embedding,
            )

            if should_split and buffer:
                raw_chunks.append(self._flush(buffer))
                buffer = []

            buffer.append(unit)
            previous_embedding = unit["embedding"]

            if self._token_count(buffer) >= self.max_tokens:
                raw_chunks.append(self._flush(buffer))
                buffer = []
                previous_embedding = None

        if buffer:
            raw_chunks.append(self._flush(buffer))

        return raw_chunks

    def _attach_embeddings(
        self,
        units: list[dict[str, Any]],
    ) -> None:
        """Attaches embedding vectors to all units in-place.
        
        Args:
            units: List of planned units to attach embeddings to.
                Each unit must have a 'text' field.
        """
        texts = [u["text"] for u in units]
        embeddings = self.embedder.embed_texts(texts)

        for unit, emb in zip(units, embeddings, strict=True):
            unit["embedding"] = list(map(float, emb))

    def _should_split(
        self,
        *,
        unit: dict[str, Any],
        buffer: list[dict[str, Any]],
        previous_embedding: list[float] | None,
    ) -> bool:
        """Determines whether a new chunk should start before the current unit.
        
        This method evaluates multiple criteria to decide if the current
        unit should start a new chunk, including token limits, minimum
        size requirements, and semantic similarity.
        
        Args:
            unit: Current unit being evaluated for chunk boundary.
            buffer: Current accumulated units in the chunk buffer.
            previous_embedding: Embedding of the previous unit for
                similarity comparison.
                
        Returns:
            True if a new chunk should start before this unit,
            False if it should be merged with the current buffer.
        """
        if not buffer:
            return False

        if self._token_count(buffer) + unit["tokens"] > self.max_tokens:
            return True

        if previous_embedding is None:
            return False

        if self._token_count(buffer) < self.min_tokens:
            return False

        similarity = self._cosine_similarity(
            previous_embedding,
            unit["embedding"],
        )

        return similarity < self.similarity_threshold

    def _flush(
        self,
        buffer: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Creates a raw chunk payload from the accumulated buffer.
        
        Args:
            buffer: List of accumulated units to be merged into a single chunk.
                
        Returns:
            Dictionary containing the merged text and source block references.
        """
        blocks = [item["block"] for item in buffer]

        return {
            "text": "\n\n".join(
                item["text"] for item in buffer
            ).strip(),
            "source_blocks": blocks,
        }

    def _single_block_chunk(
        self,
        unit: dict[str, Any],
    ) -> dict[str, Any]:
        """Creates a raw chunk payload for a standalone unit.
        
        Args:
            unit: Unit that should be preserved as a standalone chunk.
                
        Returns:
            Dictionary containing the unit text and source block reference.
        """
        return {
            "text": unit["text"],
            "source_blocks": [unit["block"]],
        }

    def _token_count(
        self,
        buffer: list[dict[str, Any]],
    ) -> int:
        """Calculates total token count for all units in the buffer.
        
        Args:
            buffer: List of units to count tokens for.
            
        Returns:
            Total number of tokens across all units in the buffer.
        """
        return sum(item["tokens"] for item in buffer)

    def _cosine_similarity(
        self,
        a: list[float],
        b: list[float],
    ) -> float:
        """Computes cosine similarity between two embedding vectors.
        
        Args:
            a: First embedding vector.
            b: Second embedding vector.
            
        Returns:
            Cosine similarity score between 0.0 and 1.0.
            Returns 0.0 if either vector is zero-length.
        """
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(y * y for y in b) ** 0.5

        if not norm_a or not norm_b:
            return 0.0

        return dot / (norm_a * norm_b)