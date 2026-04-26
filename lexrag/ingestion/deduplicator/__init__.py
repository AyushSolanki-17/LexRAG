"""Public API for the block-level deduplication layer."""

from lexrag.ingestion.deduplicator.block_deduplicator import BlockDeduplicator
from lexrag.ingestion.deduplicator.deduplication_stats import DeduplicationStats
from lexrag.ingestion.deduplicator.deduplicator_base import Deduplicator
from lexrag.ingestion.deduplicator.min_hash_deduplicator import MinHashDeduplicator
from lexrag.ingestion.deduplicator.schemas import (
    BlockDeduplicationConfig,
    BlockDeduplicationDecision,
    DeduplicationRunReport,
)
from lexrag.ingestion.deduplicator.similarity_engine import SimilarityEngine

__all__ = [
    "BlockDeduplicationConfig",
    "BlockDeduplicationDecision",
    "BlockDeduplicator",
    "DeduplicationRunReport",
    "DeduplicationStats",
    "Deduplicator",
    "MinHashDeduplicator",
    "SimilarityEngine",
]
