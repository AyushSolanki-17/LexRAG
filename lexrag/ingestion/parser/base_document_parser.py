"""Abstract document parser interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from lexrag.ingestion.parser.parsed_block import ParsedBlock


class BaseDocumentParser(ABC):
    """Abstract base class for document parser implementations.
    
    This class defines the common interface that all document parsers must implement.
    It provides a contract for parsing various document formats (PDF, HTML, etc.)
    into a standardized list of ParsedPage objects.
    
    Subclasses must implement the parse method to handle specific document types
    and parsing strategies.
    """

    @abstractmethod
    def parse(self, path: Path) -> list[ParsedBlock]:
        """Parses a document file into a list of normalized page objects.
        
        Args:
            path: The file system path to the document to be parsed.
                
        Returns:
            A list of ParsedBlock objects, each representing a parsed section
            or page from the document.
            
        Raises:
            FileNotFoundError: If the specified file does not exist.
            RuntimeError: If the document cannot be parsed due to format issues
                or parsing failures.
            NotImplementedError: If the document format is not supported by
                the concrete implementation.
        """

