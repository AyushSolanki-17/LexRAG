"""Compatibility shim for the canonical planned chunk schema."""

from __future__ import annotations

from lexrag.ingestion.chunker.schemas.planned_chunk import (
    PlannedChunk as PlannedChunkUnit,
)

__all__ = ["PlannedChunkUnit"]
