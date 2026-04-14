.PHONY: lint test eval ingest serve precommit

lint:
	uv run --extra dev ruff check .
	uv run --extra dev python -m mypy ingestion/ retrieval/ generation/ serving/

test:
	uv run --extra dev pytest tests/

eval:
	python eval/run_eval.py --split ci

ingest:
	python ingestion/pipeline.py --input data/raw/ --limit 10

serve:
	uvicorn serving.app:app --host 0.0.0.0 --port 8000 --reload

precommit:
	uv run --extra dev pre-commit run --all-files
