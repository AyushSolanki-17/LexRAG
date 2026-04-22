"""Block-aware semantic planner for intelligent chunking.

This module provides the BlockAwareSemanticPlanner class which analyzes
ParsedBlock objects and creates chunking plans that respect document
structure and content boundaries.
"""

from __future__ import annotations

from typing import Any

from lexrag.ingestion.parser import ParsedBlock


class BlockAwareSemanticPlanner:
    """Planner for block-aware semantic chunking strategies.
    
    This class analyzes ParsedBlock objects and creates chunking plans
    that respect document structure, content boundaries, and quality
    indicators. It determines which blocks should be preserved as
    standalone chunks and which can be merged based on content type
    and structural boundaries.
    
    Key responsibilities:
        - Preserve standalone blocks (tables, code, headings, captions)
        - Allow mergeable blocks (paragraphs, lists) for semantic grouping
        - Detect section boundaries for intelligent splitting
        - Handle heading anchoring for content hierarchy
        - Apply OCR-sensitive boundaries for quality control
    
    Attributes:
        FORCE_STANDALONE_BLOCKS: Set of block types that must be preserved
            as standalone chunks regardless of similarity analysis.
    """

    FORCE_STANDALONE_BLOCKS = {
        "table",
        "code",
        "heading",
        "image_caption",
    }
    
    # Block types that should never be merged with other content:
    # - table: Tabular data loses meaning when split
    # - code: Code snippets require context preservation
    # - heading: Structural elements define hierarchy
    # - image_caption: Captions must stay with their images

    def plan(
        self,
        blocks: list[ParsedBlock],
    ) -> list[dict[str, Any]]:
        """Converts ParsedBlock objects into planned chunking units.
        
        This method processes ParsedBlock objects and creates planning units
        that contain metadata for the chunking pipeline. Each unit includes
        information about whether it should be standalone, boundary detection,
        and content analysis.
        
        Args:
            blocks: List of ParsedBlock objects to analyze and plan.
                
        Returns:
            List of planning unit dictionaries containing:
            - block: Original ParsedBlock object
            - text: Cleaned text content
            - page: Page number where content originates
            - section: Section title or description
            - block_type: Type of content (table, code, paragraph, etc.)
            - tokens: Estimated token count
            - force_standalone: Whether block must be standalone
            - is_boundary: Whether block represents a hard boundary
            
            Empty blocks are filtered out automatically.
        """

        planned_units: list[dict[str, Any]] = []

        for block in blocks:
            if not block.text.strip():
                continue

            planned_units.append(
                {
                    "block": block,
                    "text": block.text.strip(),
                    "page": block.page,
                    "section": block.section,
                    "block_type": block.block_type,
                    "tokens": len(block.text.split()),
                    "force_standalone": (
                        block.block_type in self.FORCE_STANDALONE_BLOCKS
                    ),
                    "is_boundary": self._is_boundary(block),
                }
            )

        return planned_units

    def _is_boundary(self, block: ParsedBlock) -> bool:
        """Determines if a block represents a hard splitting boundary.
        
        This method identifies blocks that should trigger chunk boundaries
        regardless of semantic similarity. These boundaries help maintain
        content coherence and structural integrity.
        
        Args:
            block: ParsedBlock to analyze for boundary characteristics.
            
        Returns:
            True if the block should trigger a hard boundary,
            False if content can be merged across this block.
            
        Boundary criteria:
            - Heading blocks always create boundaries
            - Blocks with explicit heading levels create boundaries
            - Low-confidence OCR blocks create boundaries for quality control
        """

        if block.block_type == "heading":
            return True

        if block.heading_level is not None:
            return True

        if block.is_ocr and (block.confidence or 1.0) < 0.50:
            return True

        return False