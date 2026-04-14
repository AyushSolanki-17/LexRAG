"""Evaluation runner skeleton for LexRAG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LexRAG evaluation")
    parser.add_argument("--split", default="ci", choices=["ci", "full"])
    parser.add_argument("--output", default="eval/results")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_path = Path("eval/dataset/qa_pairs.json")

    if not dataset_path.exists():
        raise FileNotFoundError(f"Missing dataset: {dataset_path}")

    qa_pairs = json.loads(dataset_path.read_text(encoding="utf-8"))

    print(f"Loaded {len(qa_pairs)} QA pairs for split '{args.split}'.")
    print("Not implemented")

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
