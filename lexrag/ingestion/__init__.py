"""Ingestion package public exports."""

from lexrag.ingestion.chunker import Chunker, FixedSizeChunker, SemanticChunker
from lexrag.ingestion.deduplicator import Deduplicator, MinHashDeduplicator
from lexrag.ingestion.embedder import BGEEmbedder, EmbeddingMode, build_embedder
from lexrag.ingestion.parser import FallbackDocumentParser

__all__ = [
    "BGEEmbedder",
    "Chunker",
    "Deduplicator",
    "EmbeddingMode",
    "FallbackDocumentParser",
    "FixedSizeChunker",
    "MinHashDeduplicator",
    "SemanticChunker",
    "build_embedder",
]
