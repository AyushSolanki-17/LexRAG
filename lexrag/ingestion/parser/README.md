# `lexrag.ingestion.parser`

This package owns parsing layer responsibilities from
[docs/architecture.md](/Users/ayushsolanki/Desktop/Projects/LexRAG/docs/architecture.md):

1. Accept a caller path only after the file-ingestion boundary approves it
2. Choose the parser route deterministically from validated file metadata
3. Execute the fallback parser chain without silently dropping documents
4. Annotate every parsed block with parser provenance and confidence signals

## Responsibilities

- Consume outputs from `lexrag.ingestion.file_ingestion` rather than duplicating
  its path resolution, MIME checks, extension policy, antivirus hooks, or
  encrypted/corrupt file rejection logic
- Route files into `docling`, `pymupdf`, `unstructured`, OCR-only, or manual
  recovery based on file family and lightweight PDF heuristics
- Emit canonical `ParsedBlock` and `DocumentParseResult` models for downstream
  normalization and chunking
- Preserve auditability through `ParseAttempt`, fallback metadata, and
  parse-confidence annotation

## Main objects

- `FallbackDocumentParser`: main orchestration entrypoint for one file
- `FileParserPipeline`: transition adapter from `FileLoadResult` into parser
  execution
- `ParserSelectionStrategy`: deterministic route planner
- `ParserChainExecutor`: backend execution with structured attempts
- `ParserProvenanceAnnotator`: parser metadata and confidence attachment

## Expected flow

```text
caller path
  -> FileLoaderPipeline
  -> FileLoadResult
  -> FileParserPipeline | FallbackDocumentParser.parse_loaded_file(...)
  -> ParserSelectionStrategy
  -> ParserChainExecutor
      -> docling | pymupdf | unstructured | ocr_only | manual_recovery
  -> ParserProvenanceAnnotator
  -> DocumentParseResult
```

## Usage

```python
from pathlib import Path

from lexrag.ingestion.file_ingestion import FileLoaderPipeline
from lexrag.ingestion.parser import FileParserPipeline

loader = FileLoaderPipeline()
parser_pipeline = FileParserPipeline()
load_result = loader.load_file(Path("/data/contracts/master-service-agreement.pdf"))
result = parser_pipeline.parse_loaded_file(load_result)

if result.status == "parsed":
    print(result.parse_result.parser_used)
else:
    print(result.load_result.rejection_reason or result.error_message)
```

For directory-style parsing:

```python
load_results = loader.load_path("/data/uploads", recursive=True)
results = parser_pipeline.parse_loaded_files(load_results)
parsed = [item for item in results if item.status == "parsed"]
rejected = [item for item in results if item.status == "rejected"]
quarantined = [item for item in results if item.status == "quarantined"]
```
