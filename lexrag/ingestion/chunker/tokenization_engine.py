"""Tokenizer adapter used by ingestion chunkers.

This module provides the TokenizationEngine class which serves as an
adapter for Hugging Face tokenizers, providing token counting and
text normalization capabilities for chunking operations.
"""

from __future__ import annotations

from functools import lru_cache

from transformers import AutoTokenizer

from lexrag.config import get_settings


@lru_cache(maxsize=4)
def _get_tokenizer_cached(model_name: str):
    """Retrieves and caches a fast tokenizer for the specified model.
    
    This function loads a Hugging Face tokenizer and validates that it's
    a fast tokenizer (Rust-based) for optimal performance. The result is
    cached to avoid repeated loading operations.
    
    Args:
        model_name: Name or path of the Hugging Face model to load
            tokenizer for.
            
    Returns:
        Cached fast tokenizer instance.
        
    Raises:
        RuntimeError: If the tokenizer is not a fast tokenizer.
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    if tokenizer.is_fast is not True:
        raise RuntimeError(f"Tokenizer for model '{model_name}' is not a fast tokenizer")
    return tokenizer


class TokenizationEngine:
    """Tokenization adapter backed by Hugging Face fast tokenizers.
    
    This class provides a high-performance tokenization interface for
    chunking operations. It uses Hugging Face fast tokenizers (Rust-based)
    for optimal performance and caches tokenizer instances to avoid
    repeated loading overhead.
    
    The engine is configured to use the same model as the embedding
    system to ensure consistent tokenization across the pipeline.
    
    Key features:
        - Fast tokenization using Rust-based tokenizers
        - Automatic tokenizer caching for performance
        - Consistent tokenization with embedding model
        - Safe detokenization with proper text reconstruction
    """

    def _resolve_model_name(self) -> str:
        """Resolves the model name for tokenization.
        
        Returns:
            Model name configured for embeddings, ensuring consistent
            tokenization across the pipeline.
        """
        return get_settings().EMBED_MODEL

    def tokenize(self, text: str) -> list[str]:
        """Tokenizes text using the configured model tokenizer.
        
        This method converts text into a list of tokens using the same
        tokenizer as the embedding model, ensuring consistency across
        the pipeline.
        
        Args:
            text: Text to tokenize. Empty or whitespace-only text
                returns an empty list.
                
        Returns:
            List of token strings representing the tokenized text.
            Returns empty list for empty input.
        """
        if not text.strip():
            return []
        tokenizer = _get_tokenizer_cached(self._resolve_model_name())
        return tokenizer.tokenize(text)

    def detokenize(self, tokens: list[str]) -> str:
        """Converts model tokens back into readable text.
        
        This method reconstructs text from a list of tokens using the
        same tokenizer that was used for tokenization, ensuring accurate
        text reconstruction.
        
        Args:
            tokens: List of token strings to convert back to text.
                Empty list returns empty string.
                
        Returns:
            Reconstructed text with leading/trailing whitespace stripped.
            Returns empty string for empty input.
        """
        if not tokens:
            return ""
        tokenizer = _get_tokenizer_cached(self._resolve_model_name())
        return tokenizer.convert_tokens_to_string(tokens).strip()
