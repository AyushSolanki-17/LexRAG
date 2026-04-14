"""Core shared schemas for chunks and evaluation QA pairs."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata for a single chunk extracted from a source document."""

    doc_id: str
    source_path: str
    doc_type: Literal["sec_filing", "court_opinion", "regulation", "contract"]
    jurisdiction: str | None = None
    doc_date: date | None = None
    page_num: int
    section_title: str | None = None
    chunk_index: int
    total_chunks: int


class Chunk(BaseModel):
    """Primary chunk object used across ingestion, retrieval and generation."""

    chunk_id: str = Field(pattern=r"^[A-Za-z0-9_-]+_\d+$")
    text: str
    metadata: ChunkMetadata
    embedding: list[float] | None = None


class QAPair(BaseModel):
    """Evaluation QA pair with retrieval ground truth and difficulty label."""

    question_id: str
    question: str
    gold_answer: str
    gold_chunk_ids: list[str]
    difficulty: Literal["factoid", "multi_hop", "unanswerable", "temporal"]
    notes: str | None = None
