"""Mutable sentence buffer used by semantic chunker.

This module defines the SemanticChunkBuffer dataclass which provides
a mutable container for accumulating sentences during semantic chunking.
It tracks the current state of in-progress chunk construction.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SemanticChunkBuffer:
    """In-progress semantic chunk accumulation state.
    
    This dataclass represents the mutable state of a chunk being
    constructed during semantic chunking. It accumulates sentences,
    tracks token count, and maintains context information for
    intelligent boundary detection.
    
    The buffer is used by the semantic chunker to temporarily
    accumulate content until a chunk boundary is detected based
    on semantic similarity or size constraints.
    
    Attributes:
        sentences: List of accumulated sentences for the current chunk.
        token_count: Total number of tokens in the accumulated sentences.
        page_num: Page number where the chunk content originates.
        section_title: Title of the section containing the chunk content.
    """

    sentences: list[str]
    token_count: int
    page_num: int
    section_title: str | None
