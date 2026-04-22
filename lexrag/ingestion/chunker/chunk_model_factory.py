"""Factory for creating validated Chunk objects from raw payloads.

This module provides the ChunkModelFactory class which converts raw chunk
payloads into validated Chunk objects with comprehensive metadata,
traceability information, and quality indicators.
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4
from typing import Any

from lexrag.indexing.schema import Chunk, ChunkMetadata
from lexrag.ingestion.parser import ParsedBlock
from lexrag.utils import get_logger

logger = get_logger(__name__)


class ChunkModelFactory:
    """Factory for converting raw chunk payloads into validated Chunk objects.
    
    This factory is responsible for transforming raw chunk payloads from the
    chunking pipeline into fully validated Chunk objects with comprehensive
    metadata, traceability information, and quality indicators. It ensures
    data integrity and provides observability throughout the process.
    
    Key responsibilities:
        - Metadata normalization and validation
        - Source block traceability preservation
        - Unique chunk ID generation
        - Chunk content validation and filtering
        - Retrieval metadata enrichment
        - Boundary artifact detection and warnings
        - Document-level metadata resolution
    
    The factory creates chunks that are ready for indexing, embedding,
    and retrieval operations with full audit trails.
    """

    def build_chunks(
        self,
        raw_chunks: list[dict[str, Any]],
        *,
        parsed_blocks: list[ParsedBlock],
    ) -> list[Chunk]:
        """Converts raw chunk payloads into validated Chunk objects.
        
        This method processes raw chunk payloads and creates fully validated
        Chunk objects with comprehensive metadata, traceability information,
        and quality indicators. It handles metadata normalization, source
        block tracking, and boundary artifact detection.
        
        Args:
            raw_chunks: List of raw chunk payloads from the chunking pipeline,
                each containing text and source block references.
            parsed_blocks: Original ParsedBlock objects for metadata resolution
                and traceability.
                
        Returns:
            List of validated Chunk objects ready for indexing and retrieval.
            Chunks with empty text or missing source blocks are filtered out.
        """

        if not raw_chunks:
            return []

        metadata_base = self._resolve_metadata_base(parsed_blocks)
        total_chunks = len(raw_chunks)

        chunks: list[Chunk] = []

        for index, payload in enumerate(raw_chunks):
            text = str(payload.get("text", "")).strip()

            if not text:
                continue

            source_blocks = payload.get("source_blocks", [])

            if not source_blocks:
                logger.warning(
                    "Chunk skipped due to missing source_blocks"
                )
                continue

            first_block = source_blocks[0]

            chunk_id = str(
                payload.get("chunk_id")
                or f"{metadata_base['doc_id']}_{index}"
            )

            page_start = min(
                block.page for block in source_blocks
            )
            page_end = max(
                block.page for block in source_blocks
            )

            contains_table = any(
                block.block_type == "table"
                for block in source_blocks
            )

            contains_code = any(
                block.block_type == "code"
                for block in source_blocks
            )

            contains_ocr = any(
                block.is_ocr
                for block in source_blocks
            )

            avg_confidence = self._average_confidence(
                source_blocks
            )

            self._warn_boundary_artifact_if_needed(
                text,
                chunk_id=chunk_id,
            )

            metadata = ChunkMetadata(
                # ---------- Document ----------
                doc_id=metadata_base["doc_id"],
                source_path=metadata_base["source_path"],
                doc_type=metadata_base["doc_type"],
                doc_date=metadata_base["doc_date"],

                # ---------- Chunk ----------
                chunk_index=index,
                total_chunks=max(total_chunks, 1),

                # ---------- Source ----------
                source_block_ids=[
                    block.block_id
                    for block in source_blocks
                ],
                page_start=page_start,
                page_end=page_end,
                section_title=first_block.section,
                parent_section_path=first_block.parent_section_path,

                # ---------- Strategy ----------
                chunking_strategy="semantic_merge",
                token_count=len(text.split()),
                char_count=len(text),
                overlap_prev=False,
                overlap_next=False,

                # ---------- Quality ----------
                contains_table=contains_table,
                contains_code=contains_code,
                contains_ocr=contains_ocr,
                avg_confidence=avg_confidence,

                # ---------- Extra ----------
                metadata={
                    "parser": "docling",
                    "builder": "semantic_chunker",
                },
            )

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    text=text,
                    embedding_text=text,
                    metadata=metadata,
                    embedding=None,
                )
            )

        return chunks

    def _resolve_metadata_base(
        self,
        parsed_blocks: list[ParsedBlock],
    ) -> dict[str, Any]:
        """Resolves canonical document metadata from ParsedBlock objects.
        
        This method extracts document-level metadata from the first
        ParsedBlock to provide consistent defaults for all chunks.
        
        Args:
            parsed_blocks: List of ParsedBlock objects to extract
                document metadata from.
                
        Returns:
            Dictionary containing document-level metadata including
            doc_id, source_path, doc_type, and doc_date.
        """

        if not parsed_blocks:
            return {
                "doc_id": "unknown_doc",
                "source_path": "unknown_source",
                "doc_type": None,
                "doc_date": None,
            }

        first = parsed_blocks[0]

        return {
            "doc_id": first.doc_id or "unknown_doc",
            "source_path": first.source_path or "unknown_source",
            "doc_type": first.doc_type,
            "doc_date": self._normalize_doc_date(
                first.metadata.get("doc_date")
            ),
        }

    def _normalize_doc_date(
        self,
        value: Any,
    ) -> date | None:
        """Normalizes document date from various input formats.
        
        This method safely converts date values from different formats
        (date objects, ISO strings) into a standardized date object.
        
        Args:
            value: Date value to normalize. Can be a date object,
                ISO format string, or None.
                
        Returns:
            Normalized date object or None if conversion fails.
        """

        if value is None:
            return None

        if isinstance(value, date):
            return value

        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                return None

        return None

    def _average_confidence(
        self,
        blocks: list[ParsedBlock],
    ) -> float | None:
        """Calculates average OCR confidence across source blocks.
        
        This method computes the mean confidence score from all source
        blocks that have confidence values, providing an overall quality
        indicator for OCR-extracted content.
        
        Args:
            blocks: List of ParsedBlock objects to average confidence for.
                
        Returns:
            Average confidence score rounded to 4 decimal places,
            or None if no blocks have confidence values.
        """

        values = [
            block.confidence
            for block in blocks
            if block.confidence is not None
        ]

        if not values:
            return None

        return round(sum(values) / len(values), 4)

    def _warn_boundary_artifact_if_needed(
        self,
        text: str,
        *,
        chunk_id: str,
    ) -> None:
        """Detects and warns about potential chunk boundary artifacts.
        
        This method identifies chunks that may start with lowercase letters,
        which can indicate poor boundary detection during chunking. Such
        artifacts may affect retrieval quality and should be monitored.
        
        Args:
            text: Chunk text to analyze for boundary artifacts.
            chunk_id: Unique identifier for logging purposes.
        """

        stripped = text.lstrip()

        if stripped and stripped[0].islower():
            logger.warning(
                "Possible chunk boundary artifact detected "
                "for chunk_id=%s",
                chunk_id,
            )