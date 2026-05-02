"""Document parsing orchestrator.

This module implements the architecture-defined parser flow:
validation, detection, selection, fallback execution, and provenance
annotation.
"""

from __future__ import annotations

from pathlib import Path

from lexrag.ingestion.file_ingestion import FileIngestionConfig, FileLoaderPipeline
from lexrag.ingestion.parser.manual_recovery_required_error import (
    ManualRecoveryRequiredError,
)
from lexrag.ingestion.parser.parser_backend_registry import ParserBackendRegistry
from lexrag.ingestion.parser.parser_chain_executor import ParserChainExecutor
from lexrag.ingestion.parser.parser_provenance_annotator import (
    ParserProvenanceAnnotator,
)
from lexrag.ingestion.parser.parser_selection_strategy import ParserSelectionStrategy
from lexrag.ingestion.parser.schemas.document_parse_result import DocumentParseResult
from lexrag.ingestion.parser.schemas.parsed_block import ParsedBlock
from lexrag.ingestion.parser.schemas.parser_config import ParserConfig
from lexrag.observability.logging_runtime import get_logger

logger = get_logger(__name__)


class FallbackDocumentParser:
    """Architecture-compliant parser orchestrator.

    The public class name is kept for backward compatibility, but the
    implementation now covers the full documented parser flow rather than only
    a primary/fallback pair.
    """

    def __init__(
        self,
        *,
        config: ParserConfig | None = None,
        primary_parser: object | None = None,
        fallback_parser: object | None = None,
        unstructured_parser: object | None = None,
        ocr_parser: object | None = None,
        manual_recovery_parser: object | None = None,
        file_loader: FileLoaderPipeline | None = None,
    ) -> None:
        """Initialize parsing collaborators.

        Args:
            config: Optional parser configuration.
            primary_parser: Optional Docling override for tests or custom wiring.
            fallback_parser: Optional PyMuPDF override for tests or custom wiring.
            unstructured_parser: Optional unstructured parser override.
            ocr_parser: Optional OCR parser override.
            manual_recovery_parser: Optional manual recovery backend override.
            file_loader: Optional file-ingestion boundary override.
        """
        self.config = config or ParserConfig()
        self.file_loader = file_loader or FileLoaderPipeline(
            config=self._file_ingestion_config()
        )
        self.selector = ParserSelectionStrategy(config=self.config)
        self.registry = ParserBackendRegistry(
            primary_parser=primary_parser,
            fallback_parser=fallback_parser,
            unstructured_parser=unstructured_parser,
            ocr_parser=ocr_parser,
            manual_recovery_parser=manual_recovery_parser,
        )
        self.executor = ParserChainExecutor(registry=self.registry)
        self.annotator = ParserProvenanceAnnotator()
        self.last_result: DocumentParseResult | None = None

    def parse_document(self, path: str | Path) -> list[ParsedBlock]:
        """Parse a document and return canonical parsed blocks.

        Args:
            path: Path to the document to parse.

        Returns:
            Canonical parsed blocks with provenance metadata attached.
        """
        result = self.parse_with_report(path)
        return result.blocks

    def parse_with_report(self, path: str | Path) -> DocumentParseResult:
        """Parse a document and return the full structured parse report.

        Args:
            path: Path to the document to parse.

        Returns:
            Structured parse result containing blocks and execution metadata.

        Raises:
            ManualRecoveryRequiredError: If every parser strategy is exhausted.
        """
        load_result = self.file_loader.load_file(path)
        resolved_path = Path(load_result.resolved_path)
        validation = load_result.ingestion_report.validation
        if not validation.is_valid:
            raise ValueError(validation.failure_reason or "validation_failed")
        detection = load_result.ingestion_report.detection
        selection = self.selector.select(
            path=resolved_path,
            validation=validation,
            detection=detection,
        )
        result = self.executor.execute(path=resolved_path, selection=selection)
        if result.manual_recovery_required:
            self.last_result = result
            raise ManualRecoveryRequiredError(
                f"Manual recovery required for document: {resolved_path}",
                result=result,
            )
        annotated_blocks = self.annotator.annotate(result)
        final_result = result.model_copy(update={"blocks": annotated_blocks})
        self.last_result = final_result
        self._log_success(path=resolved_path, result=final_result)
        return final_result

    def _log_success(self, *, path: Path, result: DocumentParseResult) -> None:
        """Log a concise, structured summary of the parse flow."""
        confidence = result.blocks[0].parse_confidence if result.blocks else 0.0
        logger.info(
            "Parsed document path=%s parser=%s fallback=%s attempts=%d blocks=%d confidence=%.2f",
            path,
            result.parser_used,
            result.fallback_used,
            len(result.attempts),
            len(result.blocks),
            confidence or 0.0,
        )

    def _file_ingestion_config(self) -> FileIngestionConfig:
        return FileIngestionConfig(
            allowed_extensions=self.config.allowed_extensions,
            min_file_size_bytes=self.config.min_file_size_bytes,
            max_file_size_bytes=self.config.max_file_size_bytes,
            magic_byte_window=self.config.magic_byte_window,
        )
