"""
Represents one semantically meaningful parsed block.

Designed for:
- semantic chunking
- layout-aware ingestion
- precise citations
- OCR diagnostics
- table-aware retrieval
- enterprise-grade traceability
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import Any


class ParsedBlock(BaseModel):
    """Represents one semantically meaningful parsed block.

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

    A block may be:
    - paragraph
    - heading
    - table
    - list
    - image caption
    - OCR region
    - code block
    - footnote
    - appendix content

    This is significantly better than page-only parsing.
    """

    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    # Identity (document)
    doc_id: str | None = None
    source_path: str | None = None
    doc_type: str | None = None

    # Identity (block)
    block_id: str
    page: int = Field(ge=1, description="Page number (1-based indexing)")

    # Structural
    section: str
    heading_level: int | None = None
    block_type: str = "paragraph"
    # examples:
    # paragraph / heading / table / list / image_caption /
    # code / footnote / appendix / ocr_text

    # Content
    text: str = ""
    markdown: str | None = None

    # Layout
    # x1, y1, x2, y2 if available
    bbox: tuple[float, float, float, float] | None = None
    order_in_page: int | None = None

    # Quality
    is_ocr: bool = False
    confidence: float | None = Field(default=None,ge=0.0, le=1.0, description="Confidence")

    # Relationships
    parent_section_path: list[str] = Field(default_factory=list, description="Parent section path")

    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
