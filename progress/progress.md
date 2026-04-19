# Progress Snapshot (LexRAG)

Last updated: 2026-04-19 (Asia/Kolkata)

This file is a lightweight handoff note so you can switch chat windows without losing context.

**Current Status**
- Build plan source of truth: `AGENTS.md` + `SKILLS.md`
- Repo state: Phase 0 scaffold + tooling hardened, Phase 1.1 corpus script scaffolded
- Quality gates: `pre-commit` configured and passing (Ruff, Ruff format, mypy, unit tests)
- Eval harness: skeleton exists and runs (`python eval/run_eval.py --split ci` prints "Not implemented")

**Last File Updates (Working Tree)**
- Modified: `pyproject.toml`, `uv.lock`
- Added / untracked (not committed yet): `AGENTS.md`, `SKILLS.md`, `SKILL.md`, `.env.example`, `.pre-commit-config.yaml`, `.github/`, `Makefile`, `docs/`, `eval/`, `scripts/`, `tests/`, and scaffold dirs (`ingestion/`, `indexing/`, `retrieval/`, `generation/`, `serving/`, `infra/`, `observability/`, `frontend/`, `data/`)
- Added (staged): `lexrag/__init__.py`

**Folder Progress**
- `docs/`: created `decisions.md` (ADR-000 + ADR-001), `ablation.md` placeholder table, `failures.md` placeholder
- `eval/`: `metrics.py` stubs + `run_eval.py` CLI skeleton + `dataset/qa_pairs.json` (10 seed pairs) + schema doc
- `scripts/`: `download_corpus.sh` (downloads to `data/raw/`, logs summary; does not commit data), `benchmark_chunking.py` placeholder
- `tests/`: unit tests for schema, metric stubs, and eval CLI smoke test
- `ingestion/`, `indexing/`, `retrieval/`, `generation/`, `serving/`, `observability/`: present but mostly placeholders (search keyword "placeholder" lists these files)
- `infra/`: docker compose dev stack files added (`qdrant`, `elasticsearch`, `redis`, `langfuse`), plus placeholder `modal_deploy.py`
- `lexrag/`: package scaffold exists; `lexrag/config/config.py` currently references `pydantic_settings` + `yaml` but those deps are not pinned/added yet (avoid using this module until we decide whether to keep it)

**Tooling / Commands (Known Good)**
- Install + hooks: `uv sync --extra dev && uv run --extra dev pre-commit install`
- Run checks: `make lint && make test && make precommit`
- Run eval skeleton: `python eval/run_eval.py --split ci`

**Notes / Decisions**
- Dependency policy: direct deps pinned exactly in `pyproject.toml` (no broad `>=`), with deterministic `uv.lock`
- Ruff policy: stronger lint rule set enabled; `print` allowed only in `eval/run_eval.py` and tests
- Mypy policy: run via `python -m mypy ...` (more reliable with the current toolchain)

**Next Steps (Suggested)**
- Phase 0 commit splitting (per `AGENTS.md`): break current working tree into commits 0.1–0.6 (no "and" commits)
- Phase 1.2: implement `ingestion/parser.py` (+ fixtures + unit tests), then continue in-order

