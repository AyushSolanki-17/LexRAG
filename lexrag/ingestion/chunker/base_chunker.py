"""Shared base class for concrete chunker implementations.

This module provides the BaseChunker class which serves as a foundation
for all concrete chunker implementations in the LexRAG system. It composes
shared collaborators and provides common functionality to reduce code
duplication across different chunking strategies.
"""

from __future__ import annotations

from abc import ABC

from lexrag.ingestion.chunker.chunk_model_factory import ChunkModelFactory
from lexrag.ingestion.chunker.chunk_similarity_engine import SimilarityEngine
from lexrag.ingestion.chunker.chunker_base import Chunker
from lexrag.ingestion.chunker.tokenization_engine import TokenizationEngine


class BaseChunker(Chunker, ABC):
    """Base class that composes shared chunking collaborators.
    
    This class provides a foundation for concrete chunker implementations
    by composing common collaborators that are needed across different
    chunking strategies. It eliminates boilerplate code and ensures
    consistent behavior across all chunker implementations.
    
    The base class automatically initializes three key collaborators:
    - TokenizationEngine: For token counting and text normalization
    - ChunkModelFactory: For creating validated Chunk objects
    - SimilarityEngine: For vector similarity calculations
    
    Attributes:
        tokenization_engine: Engine for tokenizing and detokenizing text.
        chunk_model_factory: Factory for creating validated Chunk objects.
        similarity_engine: Engine for computing vector similarities.
    """

    def __init__(
        self,
        *,
        tokenization_engine: TokenizationEngine | None = None,
        chunk_model_factory: ChunkModelFactory | None = None,
        similarity_engine: SimilarityEngine | None = None,
    ) -> None:
        """Initializes the BaseChunker with shared collaborators.
        
        Args:
            tokenization_engine: Optional custom tokenization engine.
                If None, creates a default TokenizationEngine instance.
            chunk_model_factory: Optional custom chunk model factory.
                If None, creates a default ChunkModelFactory instance.
            similarity_engine: Optional custom similarity engine.
                If None, creates a default SimilarityEngine instance.
        """
        self.tokenization_engine = tokenization_engine or TokenizationEngine()
        self.chunk_model_factory = chunk_model_factory or ChunkModelFactory()
        self.similarity_engine = similarity_engine or SimilarityEngine()
