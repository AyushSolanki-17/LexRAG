"""Parser-side transition pipeline for loaded-file parse execution."""

from __future__ import annotations

from lexrag.ingestion.file_ingestion import FileLoadResult
from lexrag.ingestion.parser.document_parser import FallbackDocumentParser
from lexrag.ingestion.parser.manual_recovery_required_error import (
    ManualRecoveryRequiredError,
)
from lexrag.ingestion.parser.schemas.file_parse_result import FileParseResult


class FileParserPipeline:
    """Consume file-ingestion outputs and execute parser orchestration."""

    def __init__(
        self,
        *,
        parser: FallbackDocumentParser | None = None,
    ) -> None:
        self.parser = parser or FallbackDocumentParser()

    def parse_loaded_file(self, load_result: FileLoadResult) -> FileParseResult:
        """Parse one file that has already been approved by file ingestion."""
        return self._parse_loaded_file(load_result=load_result)

    def parse_loaded_files(
        self,
        load_results: list[FileLoadResult],
    ) -> list[FileParseResult]:
        """Parse a batch of file-ingestion outputs in order."""
        return [self._parse_loaded_file(load_result=item) for item in load_results]

    def _parse_loaded_file(self, *, load_result: FileLoadResult) -> FileParseResult:
        if not load_result.is_ready:
            return self._rejected_result(load_result=load_result)
        try:
            parse_result = self.parser.parse_loaded_file(load_result)
        except ManualRecoveryRequiredError as exc:
            return self._error_result(
                load_result=load_result,
                status="quarantined",
                error=exc,
            )
        except Exception as exc:
            return self._error_result(
                load_result=load_result,
                status="failed",
                error=exc,
            )
        return FileParseResult(
            load_result=load_result,
            parse_result=parse_result,
            status="parsed",
        )

    def _rejected_result(self, *, load_result: FileLoadResult) -> FileParseResult:
        return FileParseResult(
            load_result=load_result,
            parse_result=None,
            status="rejected",
            error_type=load_result.rejection_reason,
            error_message=load_result.failure_message,
        )

    def _error_result(
        self,
        *,
        load_result: FileLoadResult,
        status: str,
        error: Exception,
    ) -> FileParseResult:
        return FileParseResult(
            load_result=load_result,
            parse_result=None,
            status=status,
            error_type=error.__class__.__name__,
            error_message=str(error),
        )
