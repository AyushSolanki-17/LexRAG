"""Primary chunk schema shared across LexRAG stages.

This module defines the Chunk dataclass which serves as the primary retrieval
unit throughout the LexRAG pipeline. It encapsulates chunked content with
metadata, embeddings, and traceability information for vector search and
citation operations.
"""

from __future__ import annotations

from lexrag.ingestion.chunker.chunk_metadata import ChunkMetadata

from pydantic import BaseModel, ConfigDict


class Chunk(BaseModel):
    """Primary retrieval unit used for embeddings and vector search.
    
    This dataclass represents the fundamental unit of content that is
    indexed, embedded, and retrieved in the LexRAG system. Each chunk
    contains the text content, optional cleaned embedding text, metadata
    for traceability, and the computed embedding vector.
    
    The model is configured to be immutable (frozen=True) to ensure
    data integrity throughout the ingestion and retrieval pipeline.
    
    Attributes:
        chunk_id: Unique identifier for this chunk within the document.
        text: The raw text content of the chunk as extracted from the source.
        embedding_text: Optional cleaned text used specifically for embedding
            generation. If None, the main text field is used.
        metadata: Comprehensive metadata including document information,
            source traceability, and chunking strategy details.
        embedding: Computed embedding vector for this chunk. Populated
            after the embedding pipeline processes the chunk.
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

    chunk_id: str
    text: str

    # optional cleaned text for embedding only
    embedding_text: str | None = None

    metadata: ChunkMetadata

    # generated after embedding pipeline
    embedding: list[float] | None = None