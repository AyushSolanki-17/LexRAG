"""PyMuPDF and plain-text fallback parser implementation.

This module provides the PyMuPDFParser class which serves as a fallback
document parser using PyMuPDF (fitz) for PDF processing and basic HTML
parsing. It includes multiple fallback strategies to ensure maximum
document parsing coverage.
"""

from __future__ import annotations

from pathlib import Path

from lexrag.ingestion.parser.base_document_parser import BaseDocumentParser
from lexrag.ingestion.parser.html_text_extractor import TextExtractor
from lexrag.ingestion.parser.parsed_page import ParsedPage


class PyMuPDFParser(BaseDocumentParser):
    """Fallback parser using PyMuPDF with a text-based safety net.
    
    This parser serves as a reliable fallback option for document parsing,
    specializing in PDF and HTML files. It uses PyMuPDF (fitz) for PDF
    processing when available, with multiple fallback strategies including
    plain text extraction and HTML parsing.
    
    The parser is designed to handle edge cases and provide robust parsing
    even when specialized libraries are unavailable or documents have
    formatting issues.
    
    Supported formats:
        - PDF files (.pdf) using PyMuPDF or plain text fallback
        - HTML files (.html, .htm) using built-in HTML text extraction
    """

    def parse(self, path: Path) -> list[ParsedPage]:
        """Parses PDF/HTML files using fallback logic.
        
        This method determines the appropriate parsing strategy based on the
        file extension and delegates to specialized parsing methods.
        
        Args:
            path: The file system path to the document to parse.
                
        Returns:
            A list of ParsedPage objects representing the parsed document.
            
        Raises:
            RuntimeError: If the file format is not supported by this parser.
                Supported formats are PDF (.pdf) and HTML (.html, .htm).
        """
        suffix = path.suffix.lower()
        if suffix in {".html", ".htm"}:
            return self._parse_html(path)
        if suffix == ".pdf":
            return self._parse_pdf(path)
        raise RuntimeError(f"Unsupported document type for fallback parser: {path}")

    def _parse_html(self, path: Path) -> list[ParsedPage]:
        """Parses HTML files using the built-in TextExtractor.
        
        This method reads HTML content and extracts plain text using the
        lightweight TextExtractor class, which avoids external dependencies.
        
        Args:
            path: The file system path to the HTML file.
            
        Returns:
            A list containing a single ParsedPage with the extracted text.
            
        Raises:
            RuntimeError: If the HTML file is empty or no text can be extracted.
        """
        raw = path.read_text(encoding="utf-8", errors="ignore")
        extractor = TextExtractor()
        extractor.feed(raw)
        text = extractor.text()
        if not text:
            raise RuntimeError(f"Empty HTML content parsed for {path}")
        return [ParsedPage(page=1, section="HTML", text=text)]

    def _parse_pdf(self, path: Path) -> list[ParsedPage]:
        """Parses PDF files using PyMuPDF or text fallback.
        
        This method attempts to use PyMuPDF (fitz) for PDF parsing if available.
        If PyMuPDF is not installed, it falls back to plain text extraction.
        
        Args:
            path: The file system path to the PDF file.
            
        Returns:
            A list of ParsedPage objects representing the PDF content.
        """
        try:
            import fitz
        except Exception:
            return self._parse_pdf_text_fallback(path)
        return self._extract_pdf_pages(path, fitz)

    def _extract_pdf_pages(self, path: Path, fitz) -> list[ParsedPage]:
        """Extracts text content from PDF pages using PyMuPDF.
        
        This method opens the PDF using PyMuPDF and extracts text from each
        page. Pages with no extractable text are skipped.
        
        Args:
            path: The file system path to the PDF file.
            fitz: The PyMuPDF module (passed to avoid repeated imports).
            
        Returns:
            A list of ParsedPage objects, each containing text from one PDF page.
            
        Raises:
            RuntimeError: If no text can be extracted from any page in the PDF.
        """
        doc = fitz.open(path)  # pragma: no cover - requires fitz runtime
        pages: list[ParsedPage] = []
        for idx, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if text:
                pages.append(ParsedPage(page=idx, section=f"Page {idx}", text=text))
        if not pages:
            raise RuntimeError(f"No extractable text found in PDF {path}")
        return pages

    def _parse_pdf_text_fallback(self, path: Path) -> list[ParsedPage]:
        """Parses PDF files using plain text extraction as a last resort.
        
        This method reads the PDF file as plain text and attempts to extract
        content. It splits on form feed characters (\f) to identify page
        boundaries. This is a fallback method used when PyMuPDF is not
        available or fails to parse the PDF.
        
        Args:
            path: The file system path to the PDF file.
            
        Returns:
            A list of ParsedPage objects created from the extracted text.
            
        Raises:
            RuntimeError: If the PDF file is empty or no text can be extracted.
        """
        raw = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not raw:
            raise RuntimeError(f"Unable to parse empty PDF fallback text for {path}")
        parts = [part.strip() for part in raw.split("\f") if part.strip()]
        if not parts:
            parts = [raw]
        return [
            ParsedPage(page=idx, section=f"Page {idx}", text=text)
            for idx, text in enumerate(parts, start=1)
        ]
