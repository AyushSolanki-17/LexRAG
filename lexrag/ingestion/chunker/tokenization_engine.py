"""Tokenizer adapter for deterministic chunk sizing and fixed-window slicing."""

from __future__ import annotations

from functools import lru_cache

from lexrag.config import get_settings
from lexrag.ingestion.chunker.whitespace_tokenizer import WhitespaceTokenizer


@lru_cache(maxsize=4)
def _get_tokenizer_cached(model_name: str):
    """Loads and caches the tokenizer matching the configured embed model."""
    try:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            use_fast=True,
            local_files_only=True,
        )
    except Exception:
        return WhitespaceTokenizer()
    if tokenizer.is_fast is not True:
        raise RuntimeError(
            f"Tokenizer for model '{model_name}' is not a fast tokenizer"
        )
    return tokenizer


class TokenizationEngine:
    """Provides token-aware helpers shared by all chunker implementations."""

    def tokenize(self, text: str) -> list[str]:
        """Tokenizes text into deterministic model-compatible tokens."""
        if not text.strip():
            return []
        tokenizer = _get_tokenizer_cached(self._resolve_model_name())
        return tokenizer.tokenize(text)

    def detokenize(self, tokens: list[str]) -> str:
        """Reconstructs readable text from model tokens."""
        if not tokens:
            return ""
        tokenizer = _get_tokenizer_cached(self._resolve_model_name())
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
