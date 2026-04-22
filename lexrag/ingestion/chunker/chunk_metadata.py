"""Metadata schema for extracted document chunks.

This module defines the ChunkMetadata dataclass which provides comprehensive
metadata for document chunks, including traceability information, chunking
strategy details, and quality indicators for retrieval operations.
"""

from __future__ import annotations

from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from typing import Any

class ChunkMetadata(BaseModel):
    """Metadata for a retrieval-ready chunk.
    
    This dataclass preserves comprehensive traceability back to the original
    ParsedBlock objects and supports ranking, citations, filtering, and
    observability throughout the LexRAG pipeline. It includes document
    identity, chunk positioning, source traceability, chunking strategy,
    and quality metrics.
    
    The model is configured to be immutable (frozen=True) to ensure
    metadata integrity throughout the ingestion and retrieval process.
    
    Attributes:
        doc_id: Unique identifier for the source document.
        source_path: File system path to the source document.
        doc_type: Type of document (e.g., 'pdf', 'html', 'docx').
        doc_date: Publication or creation date of the document.
        chunk_index: Zero-based index of this chunk within the document.
        total_chunks: Total number of chunks in the document.
        source_block_ids: List of ParsedBlock IDs that contributed to this chunk.
        page_start: Starting page number of this chunk's content.
        page_end: Ending page number of this chunk's content.
        section_title: Title of the section containing this chunk.
        parent_section_path: Hierarchical path to parent sections.
        chunking_strategy: Strategy used to create this chunk.
        token_count: Number of tokens in the chunk text.
        char_count: Number of characters in the chunk text.
        overlap_prev: Whether this chunk overlaps with previous chunk.
        overlap_next: Whether this chunk overlaps with next chunk.
        contains_table: Whether chunk content includes table data.
        contains_code: Whether chunk content includes code snippets.
        contains_ocr: Whether chunk content includes OCR-extracted text.
        avg_confidence: Average OCR confidence score (0.0-1.0).
        metadata: Additional custom metadata as key-value pairs.
    """

    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )
    
    # Pydantic configuration:
    #   frozen=True: Makes the model immutable for data integrity
    #   populate_by_name=True: Allows field population by name or alias
    #   str_strip_whitespace=True: Automatically strips whitespace from string fields

    # Document Identity

    doc_id: str | None = None
    source_path: str | None = None
    doc_type: str | None = None
    doc_date: date | None = None

    # Chunk Identity
    chunk_index: int
    total_chunks: int

    # Source Traceability
    source_block_ids: list[str] = Field(default_factory=list)
    # Example:
    # ["blk_001", "blk_002", "blk_003"]

    page_start: int
    page_end: int

    section_title: str | None = None
    parent_section_path: list[str] = Field(default_factory=list)

    # Chunking Metadata

    chunking_strategy: str
    # examples:
    # semantic_merge
    # heading_based
    # table_preserved
    # recursive_splitter
    # fixed_token_window

    token_count: int | None = None
    char_count: int | None = None

    overlap_prev: bool = False
    overlap_next: bool = False

    # Retrieval Quality
    contains_table: bool = False
    contains_code: bool = False
    contains_ocr: bool = False

    avg_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    # Extra
    metadata: dict[str, Any] = Field(default_factory=dict)

