"""Production-facing file loader pipeline for pre-parse ingestion."""

from __future__ import annotations

from pathlib import Path

from lexrag.ingestion.file_ingestion.file_ingestion_gateway import FileIngestionGateway
from lexrag.ingestion.file_ingestion.file_path_resolver import FilePathResolver
from lexrag.ingestion.file_ingestion.schemas.file_ingestion_config import (
    FileIngestionConfig,
)
from lexrag.ingestion.file_ingestion.schemas.file_ingestion_report import (
    FileIngestionReport,
)
from lexrag.ingestion.file_ingestion.schemas.file_load_result import FileLoadResult


class FileLoaderPipeline:
    """Resolve, inspect, and approve files before parser execution."""

    def __init__(
        self,
        config: FileIngestionConfig | None = None,
        *,
        gateway: FileIngestionGateway | None = None,
        resolver: FilePathResolver | None = None,
    ) -> None:
        self.config = config or FileIngestionConfig()
        self.gateway = gateway or FileIngestionGateway(config=self.config)
        self.resolver = resolver or FilePathResolver(config=self.config)

    def load_file(self, path: str | Path) -> FileLoadResult:
        """Load one file path into a parser-ready inspection result."""
        requested = str(path)
        resolved = self.resolver.resolve(path)
        self._assert_file(resolved)
        report = self.gateway.inspect(resolved)
        return self._build_result(
            requested_path=requested,
            resolved_path=resolved,
            report=report,
        )

    def load_path(
        self,
        path: str | Path,
        *,
        recursive: bool = False,
    ) -> list[FileLoadResult]:
        """Expand a file or directory path into deterministic load results."""
        requested = str(path)
        resolved = self.resolver.resolve(path)
        if resolved.is_file():
            return [self.load_file(resolved)]
        files = self._collect_files(path=resolved, recursive=recursive)
        reports = self.gateway.inspect_batch(files)
        return self._build_batch_results(
            requested_path=requested,
            files=files,
            reports=reports,
        )

    def _collect_files(self, *, path: Path, recursive: bool) -> list[Path]:
        iterator = path.rglob("*") if recursive else path.iterdir()
        files = [self.resolver.resolve(item) for item in iterator if item.is_file()]
        files.sort()
        if not files:
            raise FileNotFoundError(f"No files were found under path: {path}")
        if len(files) > self.config.max_batch_files:
            raise ValueError("batch_limit_exceeded")
        return files

    def _build_batch_results(
        self,
        *,
        requested_path: str,
        files: list[Path],
        reports: list[FileIngestionReport],
    ) -> list[FileLoadResult]:
        return [
            self._build_result(
                requested_path=requested_path,
                resolved_path=path,
                report=report,
            )
            for path, report in zip(files, reports, strict=True)
        ]

    def _build_result(
        self,
        *,
        requested_path: str,
        resolved_path: Path,
        report: FileIngestionReport,
    ) -> FileLoadResult:
        validation = report.validation
        return FileLoadResult(
            requested_path=requested_path,
            resolved_path=str(resolved_path),
            ingestion_report=report,
            is_ready=validation.is_valid,
            rejection_reason=validation.failure_reason,
        )

    def _assert_file(self, path: Path) -> None:
        if path.is_file():
            return
        raise FileNotFoundError(f"Document is not a file: {path}")
