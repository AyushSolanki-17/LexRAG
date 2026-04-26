"""Shared base class for chunkers that materialize canonical chunk models."""

from __future__ import annotations

from abc import abstractmethod

from lexrag.ingestion.chunker.chunk_model_factory import ChunkModelFactory
from lexrag.ingestion.chunker.chunk_post_processor import ChunkPostProcessor
from lexrag.ingestion.chunker.chunk_similarity_engine import SimilarityEngine
from lexrag.ingestion.chunker.chunker import Chunker
from lexrag.ingestion.chunker.schemas.chunk import Chunk
from lexrag.ingestion.chunker.schemas.chunking_config import ChunkingConfig
from lexrag.ingestion.chunker.tokenization_engine import TokenizationEngine
from lexrag.ingestion.parser.parsed_block import ParsedBlock


class BaseChunker(Chunker):
    """Provides shared collaborators used by concrete chunker strategies."""

    def __init__(
        self,
        *,
        config: ChunkingConfig | None = None,
        tokenization_engine: TokenizationEngine | None = None,
        chunk_model_factory: ChunkModelFactory | None = None,
        similarity_engine: SimilarityEngine | None = None,
        chunk_post_processor: ChunkPostProcessor | None = None,
    ) -> None:
        self.config = config or ChunkingConfig()
        self.tokenization_engine = tokenization_engine or TokenizationEngine()
        self.chunk_model_factory = chunk_model_factory or ChunkModelFactory()
        self.similarity_engine = similarity_engine or SimilarityEngine()
        self.chunk_post_processor = chunk_post_processor or ChunkPostProcessor(
            config=self.config
        )

    @abstractmethod
    def chunk(self, blocks: list[ParsedBlock]) -> list[Chunk]:
        """Builds canonical chunks from normalized parsed blocks."""
