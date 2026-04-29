"""Public schemas for the block-level deduplication package."""

from lexrag.ingestion.deduplicator.schemas.block_deduplication_config import (
    BlockDeduplicationConfig,
)
from lexrag.ingestion.deduplicator.schemas.block_deduplication_decision import (
    BlockDeduplicationDecision,
)
from lexrag.ingestion.deduplicator.schemas.deduplication_run_report import (
    DeduplicationRunReport,
)
from lexrag.ingestion.deduplicator.schemas.vector_deduplication_config import (
    VectorDeduplicationConfig,
)
from lexrag.ingestion.deduplicator.schemas.vector_deduplication_decision import (
    VectorDeduplicationDecision,
)
from lexrag.ingestion.deduplicator.schemas.vector_deduplication_report import (
    VectorDeduplicationReport,
)

__all__ = [
    "BlockDeduplicationConfig",
    "BlockDeduplicationDecision",
    "DeduplicationRunReport",
    "VectorDeduplicationConfig",
    "VectorDeduplicationDecision",
    "VectorDeduplicationReport",
]
