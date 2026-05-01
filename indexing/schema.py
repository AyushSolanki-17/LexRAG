"""Compatibility shim for legacy `indexing.schema` imports."""

from __future__ import annotations

from lexrag.indexing.schemas import Chunk, ChunkMetadata, QAPair

__all__ = ["Chunk", "ChunkMetadata", "QAPair"]
