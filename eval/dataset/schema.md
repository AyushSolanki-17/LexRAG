# QAPair Dataset Schema

Each item in `qa_pairs.json` follows this shape:

```json
{
  "question_id": "q_001",
  "question": "What is the liability cap under Section 12.3?",
  "gold_answer": "The liability cap is limited to fees paid in the prior 12 months.",
  "gold_chunk_ids": ["doc_abc123_14"],
  "difficulty": "factoid",
  "notes": "Optional annotation"
}
```

Allowed `difficulty` values:
- `factoid`
- `multi_hop`
- `unanswerable`
- `temporal`
