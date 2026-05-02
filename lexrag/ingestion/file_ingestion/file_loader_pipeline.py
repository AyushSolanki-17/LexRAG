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
        candidates = self._collect_candidates(path=resolved, recursive=recursive)
        return self._load_candidates(requested_path=requested, candidates=candidates)

    def _collect_candidates(self, *, path: Path, recursive: bool) -> list[Path]:
        iterator = path.rglob("*") if recursive else path.iterdir()
        candidates = sorted(
            item for item in iterator if item.is_file() or item.is_symlink()
        )
        if not candidates:
            raise FileNotFoundError(f"No files were found under path: {path}")
        if len(candidates) > self.config.max_batch_files:
            raise ValueError("batch_limit_exceeded")
        return candidates

    def _load_candidates(
        self,
        *,
        requested_path: str,
        candidates: list[Path],
    ) -> list[FileLoadResult]:
        resolved_specs, failed = self._resolve_candidates(
            requested_path=requested_path,
            candidates=candidates,
        )
        resolved_files = [path for _index, path in resolved_specs]
        if not resolved_files:
            return [failed[index] for index in sorted(failed)]
        reports = self.gateway.inspect_batch(resolved_files)
        loaded = self._build_batch_results(
            requested_path=requested_path,
            files=resolved_files,
            reports=reports,
        )
        loaded_by_index = {
            index: result
            for (index, _path), result in zip(resolved_specs, loaded, strict=True)
        }
        return [
            loaded_by_index.get(index) or failed[index]
            for index in range(len(candidates))
            if index in loaded_by_index or index in failed
        ]

    def _resolve_candidates(
        self,
        *,
        requested_path: str,
        candidates: list[Path],
    ) -> tuple[list[tuple[int, Path]], dict[int, FileLoadResult]]:
        resolved_files: list[tuple[int, Path]] = []
        failed: dict[int, FileLoadResult] = {}
        for index, candidate in enumerate(candidates):
            try:
                resolved_files.append((index, self.resolver.resolve(candidate)))
            except (FileNotFoundError, PermissionError, OSError, ValueError) as exc:
                failed[index] = self._build_failed_result(
                    requested_path=requested_path,
                    candidate_path=candidate,
                    reason=self._failure_reason(exc),
                    message=str(exc),
                )
        return resolved_files, failed

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

    def _build_failed_result(
        self,
        *,
        requested_path: str,
        candidate_path: Path,
        reason: str,
        message: str,
    ) -> FileLoadResult:
        return FileLoadResult(
            requested_path=requested_path,
            resolved_path=str(candidate_path),
            ingestion_report=None,
            is_ready=False,
            rejection_reason=reason,
            failure_message=message,
        )

    def _assert_file(self, path: Path) -> None:
        if path.is_file():
            return
        raise FileNotFoundError(f"Document is not a file: {path}")

    def _failure_reason(self, exc: Exception) -> str:
        message = str(exc).lower()
        if "symlinked" in message:
            return "symlink_not_allowed"
        if "outside the configured roots" in message:
            return "outside_allowed_roots"
        if "does not exist" in message:
            return "file_not_found"
        if "not a file" in message:
            return "not_a_file"
        return exc.__class__.__name__
