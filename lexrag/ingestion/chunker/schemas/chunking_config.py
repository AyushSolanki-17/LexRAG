"""Configuration contract for chunk planning and construction."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ChunkingConfig(BaseModel):
    """Chunking thresholds shared by planner, builder, and post-processor.

    The architecture document defines chunking as a multi-stage pipeline rather
    than a monolithic algorithm. Centralizing size and similarity thresholds in
    one schema keeps those stages aligned and prevents silent drift between
    planning and building rules.
    """

    model_config = ConfigDict(frozen=True)

    min_chunk_tokens: int = Field(default=64, ge=1)
    target_chunk_tokens: int = Field(default=512, ge=1)
    max_chunk_tokens: int = Field(default=1024, ge=1)
    overlap_tokens: int = Field(default=96, ge=0)
    similarity_threshold: float = Field(default=0.72, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_token_budget(self) -> ChunkingConfig:
        """Ensures chunk size thresholds define a coherent budget."""
        if self.min_chunk_tokens > self.target_chunk_tokens:
            raise ValueError("min_chunk_tokens must be <= target_chunk_tokens")
        if self.target_chunk_tokens > self.max_chunk_tokens:
            raise ValueError("target_chunk_tokens must be <= max_chunk_tokens")
        if self.overlap_tokens >= self.max_chunk_tokens:
            raise ValueError("overlap_tokens must be < max_chunk_tokens")
        return self
