"""Canonical metadata schema for indexing-ready chunks."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class ChunkMetadata(BaseModel):
    """Audit-safe metadata attached to every chunk.

    The architecture requires chunks to preserve section lineage, parser
    provenance, and overlap context. This model is the contract that makes that
    information portable across indexing, retrieval, and evaluation layers.
    """

    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    doc_id: str | None = Field(default=None)
    source_path: str | None = Field(default=None)
    doc_type: str | None = Field(default=None)
    doc_date: date | None = Field(default=None)
    chunk_index: int = Field(ge=0)
    total_chunks: int = Field(ge=1)
    source_block_ids: list[str] = Field(default_factory=list)
    page_start: int = Field(
        default=1,
        ge=1,
        validation_alias=AliasChoices("page_start", "page_num"),
    )
    page_end: int = Field(
        default=1,
        ge=1,
        validation_alias=AliasChoices("page_end", "page_num"),
    )
    section_title: str | None = Field(default=None)
    section_path: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("section_path", "parent_section_path"),
    )
    heading_anchor: str | None = Field(default=None)
    chunk_type: str = Field(default="paragraph")
    chunking_strategy: str = Field(default="unspecified")
    token_count: int | None = Field(default=None, ge=0)
    char_count: int | None = Field(default=None, ge=0)
    overlap_prev: bool = Field(default=False)
    overlap_next: bool = Field(default=False)
    previous_chunk_id: str | None = Field(default=None)
    next_chunk_id: str | None = Field(default=None)
    contains_table: bool = Field(default=False)
    contains_code: bool = Field(default=False)
    contains_ocr: bool = Field(default=False)
    avg_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    parser_used: list[str] = Field(default_factory=list)
    fallback_used: bool = Field(default=False)
    ocr_used: bool = Field(default=False)
    parse_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    chunk_quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def page_num(self) -> int:
        """Returns the start page for legacy single-page callers."""
        return self.page_start

    @property
    def parent_section_path(self) -> list[str]:
        """Provides a backward-compatible alias for older metadata readers."""
        return self.section_path
