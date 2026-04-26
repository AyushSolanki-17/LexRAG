"""Public chunker package exports with lazy loading.

The chunker package now has explicit internal boundaries:

- `schemas/` holds Pydantic contracts shared across layers.
- planners/builders/factories implement the chunking workflow.
- compatibility shims preserve older import paths during migration.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "BaseChunker",
    "Chunk",
    "ChunkMetadata",
    "ChunkModelFactory",
    "Chunker",
    "ChunkingConfig",
    "FixedSizeChunker",
    "PlannedChunkUnit",
    "RawChunkPayload",
    "SemanticChunker",
    "SimilarityEngine",
    "TokenContext",
    "TokenizationEngine",
]

_EXPORTS: dict[str, tuple[str, str]] = {
    "BaseChunker": (".base_chunker", "BaseChunker"),
    "Chunk": (".chunk", "Chunk"),
    "ChunkMetadata": (".chunk_metadata", "ChunkMetadata"),
    "ChunkingConfig": (".schemas.chunking_config", "ChunkingConfig"),
    "Chunker": (".chunker", "Chunker"),
    "ChunkModelFactory": (".chunk_model_factory", "ChunkModelFactory"),
    "FixedSizeChunker": (".fixed_size_chunker", "FixedSizeChunker"),
    "PlannedChunkUnit": (".planned_chunk_unit", "PlannedChunkUnit"),
    "RawChunkPayload": (".raw_chunk_payload", "RawChunkPayload"),
    "SemanticChunker": (".semantic_chunker", "SemanticChunker"),
    "SimilarityEngine": (".chunk_similarity_engine", "SimilarityEngine"),
    "TokenContext": (".token_context", "TokenContext"),
    "TokenizationEngine": (".tokenization_engine", "TokenizationEngine"),
}


def _load_export(*, module_path: str, symbol: str) -> Any:
    """Import one symbol lazily from its module path."""
    module = import_module(module_path, package=__name__)
    return getattr(module, symbol)


def __getattr__(name: str) -> Any:
    """Resolve chunker exports lazily to break circular import chains."""
    export = _EXPORTS.get(name)
    if export is not None:
        module_path, symbol = export
        return _load_export(module_path=module_path, symbol=symbol)
    raise AttributeError(f"module 'lexrag.ingestion.chunker' has no attribute {name!r}")
