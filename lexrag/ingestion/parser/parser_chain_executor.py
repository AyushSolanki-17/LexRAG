"""Execute the configured parser chain deterministically."""

from __future__ import annotations

from pathlib import Path

from lexrag.ingestion.parser.error_classification import classify_parse_error
from lexrag.ingestion.parser.parsed_block_factory import ParsedBlockFactory
from lexrag.ingestion.parser.parser_backend_registry import ParserBackendRegistry
from lexrag.ingestion.parser.schemas.document_parse_result import DocumentParseResult
from lexrag.ingestion.parser.schemas.parse_attempt import ParseAttempt
from lexrag.ingestion.parser.schemas.parser_selection import ParserSelection


class ParserChainExecutor:
    """Run parser backends in the selected order until one succeeds."""

    def __init__(
        self,
        *,
        registry: ParserBackendRegistry,
        block_factory: ParsedBlockFactory | None = None,
    ) -> None:
        """Initialize the chain executor.

        Args:
            registry: Parser backend registry.
            block_factory: Optional parsed block factory.
        """
        self.registry = registry
        self.block_factory = block_factory or ParsedBlockFactory()

    def execute(
        self,
        *,
        path: Path,
        selection: ParserSelection,
    ) -> DocumentParseResult:
        """Execute the parser chain and return a structured parse result.

        Args:
            path: Document path to parse.
            selection: Parser selection plan for the document.

        Returns:
            Structured parse result containing attempts and parsed blocks.
        """
        attempts: list[ParseAttempt] = []
        for order, parser_name in enumerate(selection.parser_order, start=1):
            parser = self.registry.get(parser_name)
            parsed, attempt = self._attempt_parse(
                path=path,
                parser_name=parser_name,
                parser=parser,
                fallback_step=order,
            )
            attempts.append(attempt)
            if parsed is None:
                continue
            return self._build_success_result(
                selection=selection,
                attempts=attempts,
                parser_name=parser_name,
                parsed=parsed,
            )
        return self._build_failure_result(selection=selection, attempts=attempts)

    def _attempt_parse(
        self,
        *,
        path: Path,
        parser_name: str,
        parser,
        fallback_step: int,
    ) -> tuple[list | None, ParseAttempt]:
        """Attempt one parser backend and capture the outcome."""
        try:
            parsed = parser.parse(path)
        except Exception as exc:
            return None, self._failed_attempt(
                parser_name=parser_name,
                fallback_step=fallback_step,
                reason=classify_parse_error(exc),
                error_type=exc.__class__.__name__,
                error_message=str(exc),
            )
        if not parsed:
            return None, self._empty_attempt(
                parser_name=parser_name,
                fallback_step=fallback_step,
            )
        blocks = self.block_factory.build_blocks(
            path=path,
            parser_name=parser_name,
            parsed_items=list(parsed),
        )
        return blocks, self._successful_attempt(
            parser_name=parser_name,
            fallback_step=fallback_step,
            produced_blocks=len(blocks),
        )

    def _failed_attempt(
        self,
        *,
        parser_name: str,
        fallback_step: int,
        reason: str,
        error_type: str,
        error_message: str,
    ) -> ParseAttempt:
        """Build the failed-attempt record for parser execution."""
        return ParseAttempt(
            parser_name=parser_name,
            succeeded=False,
            fallback_step=fallback_step,
            produced_blocks=0,
            failure_reason=reason,
            error_type=error_type,
            error_message=error_message,
        )

    def _empty_attempt(
        self,
        *,
        parser_name: str,
        fallback_step: int,
    ) -> ParseAttempt:
        """Build the failed-attempt record for empty parser output."""
        return self._failed_attempt(
            parser_name=parser_name,
            fallback_step=fallback_step,
            reason="primary_empty_output",
            error_type="RuntimeError",
            error_message=f"{parser_name} returned no parsed blocks",
        )

    def _successful_attempt(
        self,
        *,
        parser_name: str,
        fallback_step: int,
        produced_blocks: int,
    ) -> ParseAttempt:
        """Build the successful-attempt record for parser execution."""
        return ParseAttempt(
            parser_name=parser_name,
            succeeded=True,
            fallback_step=fallback_step,
            produced_blocks=produced_blocks,
        )

    def _build_success_result(
        self,
        *,
        selection: ParserSelection,
        attempts: list[ParseAttempt],
        parser_name: str,
        parsed: list,
    ) -> DocumentParseResult:
        """Build the success result returned to the orchestrator."""
        fallback_used = None
        if parser_name != selection.primary_parser_name:
            fallback_used = parser_name
        ocr_used = parser_name if parser_name == "ocr_only" else None
        return DocumentParseResult(
            blocks=parsed,
            attempts=attempts,
            selection=selection,
            parser_used=parser_name,
            fallback_used=fallback_used,
            ocr_used=ocr_used,
            scanned_pdf=selection.scanned_pdf,
            encrypted=selection.encrypted,
            image_heavy=selection.image_heavy,
            partial_extraction=False,
            manual_recovery_required=False,
        )

    def _build_failure_result(
        self,
        *,
        selection: ParserSelection,
        attempts: list[ParseAttempt],
    ) -> DocumentParseResult:
        """Build a failure result when no parser backend succeeds."""
        return DocumentParseResult(
            blocks=[],
            attempts=attempts,
            selection=selection,
            parser_used="manual_recovery",
            fallback_used="manual_recovery",
            ocr_used=None,
            scanned_pdf=selection.scanned_pdf,
            encrypted=selection.encrypted,
            image_heavy=selection.image_heavy,
            partial_extraction=False,
            manual_recovery_required=True,
        )
