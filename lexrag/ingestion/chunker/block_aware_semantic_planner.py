"""Planning pass that annotates blocks before chunk construction."""

from __future__ import annotations

from lexrag.ingestion.chunker.schemas.chunking_config import ChunkingConfig
from lexrag.ingestion.chunker.schemas.planned_chunk import PlannedChunk
from lexrag.ingestion.chunker.tokenization_engine import TokenizationEngine
from lexrag.ingestion.parser.schemas.parsed_block import ParsedBlock


class BlockAwareSemanticPlanner:
    """Assigns chunking strategy and boundary signals per normalized block.

    This class implements the architecture's planning layer. It does not merge
    text or create chunks; it only decides how each block should be treated so
    the builder can remain predictable and free of parsing heuristics.

    Attributes:
        config: Shared token and quality thresholds.
        tokenization_engine: Token counter used only for plan sizing signals.
    """

    def __init__(
        self,
        *,
        config: ChunkingConfig | None = None,
        tokenization_engine: TokenizationEngine | None = None,
    ) -> None:
        self.config = config or ChunkingConfig()
        self.tokenization_engine = tokenization_engine or TokenizationEngine()

    def plan(self, blocks: list[ParsedBlock]) -> list[PlannedChunk]:
        """Build planner records while dropping blank, non-indexable blocks.

        Args:
            blocks: Normalized parser blocks from the upstream ingestion stages.

        Returns:
            Ordered planner directives consumed by the chunk builder.
        """
        plans: list[PlannedChunk] = []
        for block in blocks:
            text = block.text.strip()
            if not text:
                continue
            plans.append(self._plan_block(block=block, text=text))
        return plans

    def _plan_block(self, *, block: ParsedBlock, text: str) -> PlannedChunk:
        """Builds one planning record from one parsed block."""
        token_count = self.tokenization_engine.count_tokens(text)
        strategy = self._strategy_for(block=block, token_count=token_count)
        return PlannedChunk(
            block=block,
            text=text,
            token_count=token_count,
            chunking_strategy=strategy,
            standalone=strategy in {"standalone", "table_aware"},
            merge_with_next=strategy not in {"standalone", "table_aware"},
            overlap_candidate=strategy in {"semantic_merge", "sliding_window"},
            section_boundary=self._is_section_boundary(block=block, strategy=strategy),
            heading_anchor=self._heading_anchor(block=block),
        )

    def _strategy_for(self, *, block: ParsedBlock, token_count: int) -> str:
        """Choose the chunking strategy that best fits the block shape.

        The planner intentionally keeps this policy explicit because retrieval
        quality issues are often traced back to silent chunking heuristics. A
        visible strategy assignment makes those decisions auditable.
        """
        if block.block_type == "heading":
            return "heading_anchored"
        if block.block_type == "table":
            return "table_aware"
        if block.block_type in {"code", "code_block", "definition", "caption"}:
            return "standalone"
        if block.block_type == "list":
            return "heading_anchored"
        if token_count > self.config.max_chunk_tokens:
            return "sliding_window"
        return "semantic_merge"

    def _is_section_boundary(self, *, block: ParsedBlock, strategy: str) -> bool:
        """Detects boundaries that should flush the current semantic buffer."""
        if strategy == "heading_anchored":
            return True
        if block.heading_level is not None:
            return True
        return bool(block.is_ocr and (block.confidence or 1.0) < 0.50)

    def _heading_anchor(self, *, block: ParsedBlock) -> str | None:
        """Resolve stable heading context for downstream chunk lineage.

        Returns:
            A normalized anchor value when a block can provide heading context.
        """
        anchor = block.metadata.get("heading_anchor")
        if isinstance(anchor, str) and anchor.strip():
            return anchor.strip()
        if block.block_type == "heading" and block.text.strip():
            return block.text.strip()
        if block.section.strip():
            return block.section.strip()
        return None
