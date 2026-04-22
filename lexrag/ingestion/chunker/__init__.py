"""Chunker package public exports.

This package provides a comprehensive document chunking system for the LexRAG
project. It includes multiple chunking strategies, semantic analysis,
tokenization utilities, and metadata management to convert parsed documents
into optimized retrieval chunks.

Key components:
    - BaseChunker: Abstract base class for all chunker implementations
    - FixedSizeChunker: Deterministic fixed-token window chunking
    - SemanticChunker: Content-aware semantic chunking
    - ChunkModelFactory: Factory for creating validated Chunk objects
    - SimilarityEngine: Vector similarity calculations
    - TokenizationEngine: Token counting and text normalization
    - Chunk: Primary data model for retrieval units
    - ChunkMetadata: Comprehensive metadata for traceability

The package supports both deterministic and semantic chunking strategies,
with extensive metadata preservation for retrieval quality and observability.
"""

from .chunker import (
    BaseChunker,
    Chunker,
    ChunkModelFactory,
    SimilarityEngine,
    TokenizationEngine,
)
from .fixed_size_chunker import FixedSizeChunker
from .semantic_chunker import SemanticChunker
from .chunk import Chunk
from .chunk_metadata import ChunkMetadata

import re

SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")


__all__ = [
    "BaseChunker",
    "ChunkModelFactory",
    "Chunker",
    "FixedSizeChunker",
    "SemanticChunker",
    "SimilarityEngine",
    "TokenizationEngine",
    "Chunk",
    "ChunkMetadata",
]
