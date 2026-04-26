"""Similarity utilities used only inside the chunking layer."""

from __future__ import annotations

from collections import Counter


class SimilarityEngine:
    """Computes lexical coherence between adjacent block texts.

    Chunking happens before embeddings are generated, so this engine avoids any
    dependency on the embedding layer. A weighted Jaccard score is accurate
    enough for boundary detection while keeping the layer architecture pure.
    """

    def score_text_pair(self, left_text: str, right_text: str) -> float:
        """Returns a weighted token-overlap score between two text spans."""
        left_counts = self._token_counts(text=left_text)
        right_counts = self._token_counts(text=right_text)
        if not left_counts or not right_counts:
            return 0.0
        shared = sum((left_counts & right_counts).values())
        total = sum((left_counts | right_counts).values())
        if total == 0:
            return 0.0
        return shared / total

    def _token_counts(self, *, text: str) -> Counter[str]:
        """Builds normalized token counts for lexical similarity scoring."""
        tokens = [token.lower() for token in text.split() if token.strip()]
        return Counter(tokens)
