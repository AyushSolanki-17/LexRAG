"""Tokenizer adapter for deterministic chunk sizing and fixed-window slicing."""

from __future__ import annotations

from lexrag.config import get_settings
from lexrag.ingestion.embeddings.shared_model_registry import SharedModelRegistry


class TokenizationEngine:
    """Provides token-aware helpers shared by all chunker implementations."""

    def __init__(self, *, registry: SharedModelRegistry | None = None) -> None:
        self.registry = registry or SharedModelRegistry()

    def tokenize(self, text: str) -> list[str]:
        """Tokenizes text into deterministic model-compatible tokens."""
        if not text.strip():
            return []
        tokenizer = self._tokenizer()
        return tokenizer.tokenize(text)

    def detokenize(self, tokens: list[str]) -> str:
        """Reconstructs readable text from model tokens."""
        if not tokens:
            return ""
        tokenizer = self._tokenizer()
        return tokenizer.convert_tokens_to_string(tokens).strip()

    def count_tokens(self, text: str) -> int:
        """Returns the token count for text using the configured tokenizer."""
        return len(self.tokenize(text))

    def window_tokens(
        self,
        *,
        tokens: list[str],
        window_size: int,
        overlap: int,
    ) -> list[list[str]]:
        """Splits tokens into overlapping windows for long-block fallback."""
        if not tokens:
            return []
        stride = max(window_size - overlap, 1)
        windows: list[list[str]] = []
        for start in range(0, len(tokens), stride):
            window = tokens[start : start + window_size]
            if not window:
                continue
            windows.append(window)
            if start + window_size >= len(tokens):
                break
        return windows

    def _resolve_model_name(self) -> str:
        """Resolves the tokenizer model name from shared runtime settings."""
        return get_settings().EMBED_MODEL

    def _tokenizer(self):
        """Resolve the tokenizer from the shared model registry."""
        return self.registry.get_tokenizer(
            model_name=self._resolve_model_name(),
            local_files_only=True,
        )
