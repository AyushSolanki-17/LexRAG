"""Chunker abstraction.

This module defines the abstract Chunker interface that all chunking
implementations must follow. It provides a contract for converting parsed
document blocks into standardized chunk objects suitable for retrieval.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from lexrag.indexing.schema import Chunk
from lexrag.ingestion.parser import ParsedBlock


class Chunker(ABC):
    """Abstract chunker interface.
    
    This abstract base class defines the contract that all chunker
    implementations must follow. It ensures consistent behavior across
    different chunking strategies and provides a standardized interface
    for converting parsed document blocks into retrieval-ready chunks.
    
    All concrete chunker implementations should inherit from this class
    and implement the chunk method according to their specific strategy.
    """

    @abstractmethod
    def chunk(self, pages: list[ParsedBlock]) -> list[Chunk]:
        """Converts parsed blocks into normalized Chunk objects.
        
        This method must be implemented by concrete chunker classes to
        convert a list of ParsedBlock objects into a list of validated
        Chunk objects suitable for retrieval operations.
        
        Args:
            pages: A list of ParsedBlock objects representing parsed
                document content that needs to be chunked.
                
        Returns:
            A list of Chunk objects containing the chunked content with
            appropriate metadata for retrieval operations.
            
        Raises:
            NotImplementedError: If the method is not implemented by a
                concrete subclass.
        """
