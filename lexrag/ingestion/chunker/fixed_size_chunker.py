"""Deterministic fixed-window chunker used for baselines and controlled tests."""

from __future__ import annotations

from lexrag.ingestion.chunker.base_chunker import BaseChunker
from lexrag.ingestion.chunker.schemas.chunk import Chunk
from lexrag.ingestion.chunker.schemas.chunking_config import ChunkingConfig
from lexrag.ingestion.chunker.schemas.raw_chunk_payload import RawChunkPayload
from lexrag.ingestion.chunker.schemas.token_context import TokenContext
from lexrag.ingestion.parser.parsed_block import ParsedBlock


class FixedSizeChunker(BaseChunker):
    """Slices parsed content into overlapping token windows with full lineage."""

    def __init__(self, *, chunk_size: int = 512, overlap: int = 64) -> None:
        config = ChunkingConfig(
            min_chunk_tokens=min(chunk_size, 64),
            target_chunk_tokens=chunk_size,
            max_chunk_tokens=chunk_size,
            overlap_tokens=overlap,
        )
        super().__init__(config=config)

    def chunk(self, blocks: list[ParsedBlock]) -> list[Chunk]:
        """Builds fixed-window chunks from parsed blocks."""
        token_stream = self._token_stream(blocks=blocks)
        if not token_stream:
            return []
        raw_chunks = self._raw_chunks(token_stream=token_stream)
        built = self.chunk_model_factory.build_chunks(raw_chunks, parsed_blocks=blocks)
        return self.chunk_post_processor.process(built)

    def _token_stream(self, *, blocks: list[ParsedBlock]) -> list[TokenContext]:
        """Flattens blocks into tokens while preserving source lineage."""
        stream: list[TokenContext] = []
        for block in blocks:
            for token in self.tokenization_engine.tokenize(block.text.strip()):
                stream.append(TokenContext(token=token, block=block))
        return stream

    def _raw_chunks(self, *, token_stream: list[TokenContext]) -> list[RawChunkPayload]:
        """Creates raw overlapping windows from the token stream."""
        windows = self.tokenization_engine.window_tokens(
            tokens=[context.token for context in token_stream],
            window_size=self.config.max_chunk_tokens,
            overlap=self.config.overlap_tokens,
        )
        raw_chunks: list[RawChunkPayload] = []
        cursor = 0
        stride = max(self.config.max_chunk_tokens - self.config.overlap_tokens, 1)
        for window in windows:
            source_blocks = self._source_blocks(
                token_stream=token_stream,
                start=cursor,
                size=len(window),
            )
            raw_chunks.append(
                RawChunkPayload(
                    text=self.tokenization_engine.detokenize(window).strip(),
                    source_blocks=source_blocks,
                    chunking_strategy="fixed_token_window",
                    chunk_type=self._chunk_type(source_blocks=source_blocks),
                    token_count=len(window),
                )
            )
            cursor += stride
        return raw_chunks

    def _source_blocks(
        self,
        *,
        token_stream: list[TokenContext],
        start: int,
        size: int,
    ) -> list[ParsedBlock]:
        """Collects unique source blocks covered by one token window."""
        selected = token_stream[start : start + size]
        blocks_by_id: dict[str, ParsedBlock] = {}
        for context in selected:
            blocks_by_id[context.block.block_id] = context.block
        return list(blocks_by_id.values())

    def _chunk_type(self, *, source_blocks: list[ParsedBlock]) -> str:
        """Resolves dominant chunk type for fixed-window output."""
        types = {block.block_type for block in source_blocks if block.block_type}
        if "table" in types:
            return "table"
        if "code" in types:
            return "code"
        return "paragraph"
