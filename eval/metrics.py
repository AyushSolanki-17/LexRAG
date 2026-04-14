"""Evaluation metric stubs for retrieval and generation quality."""

from __future__ import annotations


def mrr_at_k(retrieved_ids: list[str], gold_ids: list[str], k: int = 5) -> float:
    """Compute mean reciprocal rank@k for one query."""
    raise NotImplementedError("mrr_at_k is implemented in Phase 1")


def ndcg_at_k(retrieved_ids: list[str], gold_ids: list[str], k: int = 5) -> float:
    """Compute normalized discounted cumulative gain@k for one query."""
    raise NotImplementedError("ndcg_at_k is implemented in Phase 1")


def recall_at_k(retrieved_ids: list[str], gold_ids: list[str], k: int = 10) -> float:
    """Compute recall@k for one query."""
    raise NotImplementedError("recall_at_k is implemented in Phase 1")


def faithfulness_score(answer: str, chunks: list[object]) -> float:
    """Compute groundedness/faithfulness score for a generated answer."""
    return 0.0


def bertscore_f1(generated: str, gold: str) -> float:
    """Compute BERTScore F1 for generated answer against gold answer."""
    return 0.0


def citation_accuracy(citations: list[dict], chunks: list[object]) -> float:
    """Compute citation validity accuracy against retrieved chunks."""
    return 0.0
