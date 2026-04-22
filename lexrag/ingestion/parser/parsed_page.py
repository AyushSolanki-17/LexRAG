"""Parsed page model for ingestion parser outputs.

This module defines the ParsedPage dataclass which represents a single
parsed content block from a source document. It provides a standardized
structure for storing parsed content along with metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ParsedPage:
    """Represents one parsed content block from a source document.
    
    This dataclass encapsulates a single unit of parsed content from a document,
    typically representing a page or section. It includes the page number,
    section name, extracted text, and associated metadata.
    
    The class is immutable (frozen=True) to ensure data integrity throughout
    the ingestion pipeline. The slots=True optimization reduces memory usage
    for large document collections.
    
    Attributes:
        page: The page number (1-based indexing) of this content block.
        section: The section name or description (e.g., "Page 1", "Introduction").
        text: The extracted text content from this page/section.
        metadata: Additional metadata dictionary for storing extra information
            such as document type, source file, parsing timestamps, etc.
    """

    page: int
    section: str
    text: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Converts the parsed page object into the shared dictionary schema.
        
        This method provides a standardized dictionary representation of the
        ParsedPage object, useful for serialization, JSON encoding, or
        compatibility with other systems that expect dictionary-based data.
        
        Returns:
            A dictionary containing all ParsedPage fields with the same keys:
            'page', 'section', 'text', and 'metadata'.
        """
        return {"page": self.page, "section": self.section, "text": self.text, "metadata": self.metadata}
