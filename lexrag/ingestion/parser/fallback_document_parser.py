"""Primary/fallback parser orchestrator.

This module provides the FallbackDocumentParser class which implements a
robust parsing strategy by attempting to use a primary parser first and
falling back to a secondary parser if the primary fails. This ensures
maximum document parsing reliability while maintaining quality.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lexrag.ingestion.parser.base_document_parser import BaseDocumentParser
from lexrag.ingestion.parser.docling_parser import DoclingParser
from lexrag.ingestion.parser.parsed_block import ParsedBlock
from lexrag.ingestion.parser.pymupdf_parser import PyMuPDFParser
from lexrag.utils.logging import get_logger

logger = get_logger(__name__)


class FallbackDocumentParser:
    """Parser orchestrator that implements primary/fallback parsing strategy.
    
    This class provides a robust document parsing mechanism by attempting
    to parse documents using a primary parser first (typically DoclingParser)
    and falling back to a secondary parser (typically PyMuPDFParser) if the
    primary parser fails. This approach ensures maximum parsing coverage
    while maintaining high quality results.
    
    The parser logs the parsing attempts and outcomes, providing visibility
    into which parser was successful for each document.
    
    Attributes:
        primary_parser: The primary parser to attempt first. Defaults to
            DoclingParser if not provided.
        fallback_parser: The secondary parser to use if primary fails.
            Defaults to PyMuPDFParser if not provided.
    """

    def __init__(
        self,
        primary_parser: BaseDocumentParser | Any | None = None,
        fallback_parser: BaseDocumentParser | Any | None = None,
    ) -> None:
        """Initializes the FallbackDocumentParser with primary and fallback parsers.
        
        Args:
            primary_parser: The primary parser to attempt first. If None,
                defaults to DoclingParser. Must implement a parse() method.
            fallback_parser: The fallback parser to use if primary fails.
                If None, defaults to PyMuPDFParser. Must implement a parse() method.
        """
        self.primary_parser = primary_parser or DoclingParser()
        self.fallback_parser = fallback_parser or PyMuPDFParser()

    def parse_document(self, path: str | Path) -> list[ParsedBlock]:
        """Parses a document using the fallback strategy.
        
        This method validates the file path exists and then attempts to parse
        the document using the primary parser first, falling back to the
        secondary parser if needed.
        
        Args:
            path: The file system path to the document to parse. Can be a
                string or Path object.
                
        Returns:
            A list of ParsedPage objects representing the parsed document.
            
        Raises:
            FileNotFoundError: If the specified document file does not exist.
            RuntimeError: If both primary and fallback parsers fail to parse
                the document.
        """
        resolved_path = Path(path)
        if not resolved_path.exists():
            raise FileNotFoundError(f"Document does not exist: {resolved_path}")
        pages = self._parse_with_fallback(resolved_path)
        return pages

    def _parse_with_fallback(self, path: Path) -> list[ParsedBlock]:
        """Attempts to parse a document with fallback logic.
        
        This method first tries to parse the document using the primary parser.
        If the primary parser fails for any reason, it logs the failure and
        attempts to parse using the fallback parser.
        
        Args:
            path: The file system path to the document to parse.
            
        Returns:
            A list of ParsedPage objects from either the primary or fallback
            parser, whichever succeeded.
            
        Raises:
            RuntimeError: If both the primary and fallback parsers fail to parse
                the document.
        """
        try:
            pages = self.primary_parser.parse(path)
            logger.info("Parsed %s with primary parser", path)
            return pages
        except Exception as primary_exc:
            logger.warning("Primary parser failed for %s: %s. Falling back.", path, primary_exc)
            pages = self.fallback_parser.parse(path)
            logger.info("Parsed %s with fallback parser", path)
            return pages