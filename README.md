# LexRAG

LexRAG is a legal-domain retrieval-augmented generation system built in
phases with strict evaluation gates.

## Quick Start

1. Start local services:

```bash
docker compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up -d
```

2. Install deps and git hooks:

```bash
uv sync --extra dev
uv run --extra dev pre-commit install
```

3. Run checks:

```bash
make lint
make test
make precommit
```

4. Run eval skeleton:

```bash
python eval/run_eval.py --split ci
```
