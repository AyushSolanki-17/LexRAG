"""Production semantic chunker aligned with the architecture's planning flow."""

from __future__ import annotations

from lexrag.ingestion.chunker.base_chunker import BaseChunker
from lexrag.ingestion.chunker.block_aware_semantic_planner import (
    BlockAwareSemanticPlanner,
)
from lexrag.ingestion.chunker.chunk_builder import ChunkBuilder
from lexrag.ingestion.chunker.schemas.chunk import Chunk
from lexrag.ingestion.chunker.schemas.chunking_config import ChunkingConfig
from lexrag.ingestion.parser.parsed_block import ParsedBlock


class SemanticChunker(BaseChunker):
    """Builds semantically coherent chunks without depending on embeddings."""

    def __init__(
        self,
        *,
        config: ChunkingConfig | None = None,
        embedding_mode: str | None = None,
    ) -> None:
        _ = embedding_mode
        super().__init__(config=config)
        self.planner = BlockAwareSemanticPlanner(
            config=self.config,
            tokenization_engine=self.tokenization_engine,
        )
        self.builder = ChunkBuilder(
            config=self.config,
            tokenization_engine=self.tokenization_engine,
            similarity_engine=self.similarity_engine,
        )

    def chunk(self, blocks: list[ParsedBlock]) -> list[Chunk]:
        """Runs planner -> builder -> factory -> post-processor."""
        plans = self.planner.plan(blocks)
        if not plans:
            return []
        raw_chunks = self.builder.build(plans)
        built = self.chunk_model_factory.build_chunks(raw_chunks, parsed_blocks=blocks)
        return self.chunk_post_processor.process(built)
