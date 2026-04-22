"""Semantic chunker with content-aware boundary detection.

This module provides the SemanticChunker class which implements intelligent
chunking based on content similarity, semantic boundaries, and block structure.
It preserves content coherence while optimizing for retrieval performance.
"""

from __future__ import annotations

from lexrag.indexing.schema import Chunk
from lexrag.ingestion.chunker import Chunker
from lexrag.ingestion.chunker.chunk_builder import ChunkBuilder
from lexrag.ingestion.chunker.chunk_model_factory import ChunkModelFactory
from lexrag.ingestion.chunker.block_aware_semantic_planner import (
    BlockAwareSemanticPlanner,
)
from lexrag.ingestion.parser import ParsedBlock


class SemanticChunker(Chunker):
    """Semantic chunker with content-aware boundary detection.
    
    This chunker implements intelligent content-aware chunking that preserves
    semantic coherence while respecting document structure. It uses a three-stage
    pipeline: planning, building, and factory conversion to create optimized
    retrieval chunks.
    
    The chunker analyzes content similarity, respects block boundaries,
    and preserves standalone elements like tables and code blocks. It provides
    superior retrieval quality compared to fixed-size chunking by maintaining
    content context and semantic boundaries.
    
    Pipeline stages:
        1. Planning: Analyzes ParsedBlock objects and decides chunking strategy
        2. Building: Creates raw chunks using similarity analysis and token limits
        3. Factory: Converts raw payloads into validated Chunk objects
    
    Attributes:
        planner: Analyzes ParsedBlock objects and creates chunking plans.
        builder: Constructs raw chunk payloads from planned units.
        factory: Creates validated Chunk objects from raw payloads.
    """

    def __init__(self) -> None:
        """Initializes the SemanticChunker with default components.
        
        Creates the three-stage pipeline with default configurations:
        - BlockAwareSemanticPlanner for content analysis
        - ChunkBuilder for similarity-based chunk construction
        - ChunkModelFactory for final Chunk object creation
        """
        self.planner = BlockAwareSemanticPlanner()
        self.builder = ChunkBuilder()
        self.factory = ChunkModelFactory()

    def chunk(
        self,
        pages: list[ParsedBlock],
    ) -> list[Chunk]:
        """Converts ParsedBlock objects into semantic Chunk objects.
        
        This method orchestrates the complete semantic chunking pipeline:
        1. Plans chunking strategy based on content analysis
        2. Builds raw chunks using similarity and boundary detection
        3. Creates validated Chunk objects with comprehensive metadata
        
        Args:
            pages: List of ParsedBlock objects representing parsed document
                content to be chunked semantically.
                
        Returns:
            List of Chunk objects with semantically coherent content
            and full metadata for retrieval operations.
            Returns empty list if input is empty or processing fails.
        """

        if not pages:
            return []

        planned_units = self.planner.plan(pages)

        if not planned_units:
            return []

        raw_chunks = self.builder.build(planned_units)

        return self.factory.build_chunks(
            raw_chunks,
            parsed_blocks=pages,
        )