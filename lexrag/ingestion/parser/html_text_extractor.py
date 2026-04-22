"""Minimal HTML text extractor used by parser fallbacks.

This module provides a lightweight HTML text extraction utility that avoids
external dependencies like BeautifulSoup. It uses Python's built-in HTMLParser
to extract plain text content from HTML documents while preserving the
readable text flow.
"""

from __future__ import annotations

from html.parser import HTMLParser


class TextExtractor(HTMLParser):
    """Minimal HTML-to-text extractor that avoids extra dependencies.
    
    This class extends Python's built-in HTMLParser to provide simple
    text extraction from HTML documents. It collects text content from
    HTML nodes while ignoring tags, attributes, and script content.
    The extracted text is normalized with proper spacing.
    
    This is a lightweight alternative to heavier libraries like BeautifulSoup
    or lxml, suitable for basic text extraction needs in the parsing pipeline.
    
    Attributes:
        _parts: Internal list that accumulates extracted text fragments.
    """

    def __init__(self) -> None:
        """Initializes the TextExtractor with an empty text parts list."""
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        """Processes text data encountered during HTML parsing.
        
        This method is called automatically by HTMLParser when text data
        is encountered between HTML tags. The method strips whitespace
        and stores non-empty text fragments for later assembly.
        
        Args:
            data: The raw text data encountered during HTML parsing.
        """
        data = data.strip()
        if data:
            self._parts.append(data)

    def text(self) -> str:
        """Returns normalized plain text assembled from collected HTML nodes.
        
        This method assembles all collected text fragments into a single
        string with proper spacing between fragments. The result is stripped
        of leading and trailing whitespace.
        
        Returns:
            The extracted plain text content from the HTML document,
            normalized with single spaces between text fragments.
        """
        return " ".join(self._parts).strip()
