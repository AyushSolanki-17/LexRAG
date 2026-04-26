"""Lightweight ingestion package exports.

This module intentionally avoids eager imports so parser-only paths do not
require chunking/tokenizer dependencies at import time.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "BGEEmbedder",
    "BlockDeduplicator",
    "BlockQualityValidator",
    "Chunker",
    "Deduplicator",
    "EmbeddingMode",
    "FallbackDocumentParser",
    "FixedSizeChunker",
    "MinHashDeduplicator",
    "SemanticChunker",
    "build_embedder",
]


def __getattr__(name: str) -> Any:
    """Resolve ingestion exports lazily to avoid hard dependency coupling."""
    if name in {"Chunker", "FixedSizeChunker", "SemanticChunker"}:
        from lexrag.ingestion.chunker import Chunker, FixedSizeChunker, SemanticChunker

        return {
            "Chunker": Chunker,
            "FixedSizeChunker": FixedSizeChunker,
            "SemanticChunker": SemanticChunker,
        }[name]
    if name in {
        "BlockDeduplicator",
        "Deduplicator",
        "MinHashDeduplicator",
    }:
        from lexrag.ingestion.deduplicator import (
            BlockDeduplicator,
            Deduplicator,
            MinHashDeduplicator,
        )

        return {
            "BlockDeduplicator": BlockDeduplicator,
            "Deduplicator": Deduplicator,
            "MinHashDeduplicator": MinHashDeduplicator,
        }[name]
    if name == "BlockQualityValidator":
        from lexrag.ingestion.block_quality import BlockQualityValidator

        return BlockQualityValidator
    if name in {"BGEEmbedder", "EmbeddingMode", "build_embedder"}:
        from lexrag.ingestion.embedder import BGEEmbedder, EmbeddingMode, build_embedder

        return {
            "BGEEmbedder": BGEEmbedder,
            "EmbeddingMode": EmbeddingMode,
            "build_embedder": build_embedder,
        }[name]
    if name == "FallbackDocumentParser":
        from lexrag.ingestion.parser import FallbackDocumentParser

        return FallbackDocumentParser
    raise AttributeError(f"module 'lexrag.ingestion' has no attribute {name!r}")
