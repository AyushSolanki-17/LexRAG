"""Attach parser provenance to parsed blocks."""

from __future__ import annotations

from lexrag.ingestion.parser.error_classification import classify_parse_error
from lexrag.ingestion.parser.parse_confidence_scorer import ParseConfidenceScorer
from lexrag.ingestion.parser.schemas.document_parse_result import DocumentParseResult
from lexrag.ingestion.parser.schemas.parsed_block import ParsedBlock


class ParserProvenanceAnnotator:
    """Annotate blocks with parser flow metadata for downstream auditing."""

    def __init__(self, scorer: ParseConfidenceScorer | None = None) -> None:
        """Initialize provenance annotation dependencies.

        Args:
            scorer: Optional confidence scorer instance.
        """
        self.scorer = scorer or ParseConfidenceScorer()

    def annotate(self, result: DocumentParseResult) -> list[ParsedBlock]:
        """Return parsed blocks enriched with parse provenance metadata.

        Args:
            result: Document parse result to annotate.

        Returns:
            Annotated parsed blocks ready for downstream ingestion.
        """
        confidence = self.scorer.score(
            selection=result.selection,
            attempts=result.attempts,
            blocks=result.blocks,
        )
        return [
            self._annotate_block(block=block, result=result, confidence=confidence)
            for block in result.blocks
        ]

    def _annotate_block(
        self,
        *,
        block: ParsedBlock,
        result: DocumentParseResult,
        confidence: float,
    ) -> ParsedBlock:
        """Attach structured provenance to a single parsed block."""
        metadata = dict(block.metadata or {})
        metadata.update(self._build_metadata(result=result, confidence=confidence))
        return block.model_copy(
            update={
                "parser_used": result.parser_used,
                "fallback_used": result.fallback_used,
                "is_fallback_used": result.fallback_used is not None,
                "ocr_used": result.ocr_used,
                "parse_confidence": confidence,
                "metadata": metadata,
            }
        )

    def _build_metadata(
        self,
        *,
        result: DocumentParseResult,
        confidence: float,
    ) -> dict[str, object]:
        """Build stable metadata keys consumed by the pipeline and eval code."""
        failed_attempt = next(
            (attempt for attempt in result.attempts if not attempt.succeeded), None
        )
        return {
            "parser_used": result.parser_used,
            "primary_parser": result.selection.primary_parser_name,
            "fallback_event": self._fallback_event(result=result),
            "fallback_reason_code": self._fallback_reason_code(result=result),
            "fallback_parser": result.fallback_used,
            "parser_attempts": [attempt.model_dump() for attempt in result.attempts],
            "primary_error_type": None
            if failed_attempt is None
            else failed_attempt.error_type,
            "primary_error_message": None
            if failed_attempt is None
            else failed_attempt.error_message,
            "scanned_pdf": result.scanned_pdf,
            "image_heavy": result.image_heavy,
            "encrypted": result.encrypted,
            "partial_extraction": result.partial_extraction,
            "manual_recovery_required": result.manual_recovery_required,
            "parse_confidence": confidence,
        }

    def _fallback_event(self, *, result: DocumentParseResult) -> str:
        """Describe whether fallback was required for the successful parse."""
        if result.fallback_used is None:
            return "not_used"
        return "primary_failed_fallback_succeeded"

    def _fallback_reason_code(self, *, result: DocumentParseResult) -> str | None:
        """Report the first failure reason that forced fallback execution."""
        failed_attempt = next(
            (attempt for attempt in result.attempts if not attempt.succeeded), None
        )
        if failed_attempt is None:
            return None
        if failed_attempt.error_message is None:
            return "primary_parse_error"
        return classify_parse_error(RuntimeError(failed_attempt.error_message))
