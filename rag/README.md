# RAG testing

The corpus lives in `../corpus/*.jsonl` (built by `scripts/build_corpus.py`).
Each chunk carries retrieval metadata (`source`, `season`, `episode`,
`speakers`, `source_url`) so answers can cite chunk ids and be traced to an
exact episode.

## Eval protocol

`eval/questions.jsonl` — one gold Q&A per line:

```json
{"id": "q003", "question": "...", "answer": "...", "citations": ["s02e11"],
 "difficulty": "easy|medium|hard", "tags": ["buster", "events"]}
```

- **Grading:** an answer passes if it (a) matches the gold answer's facts and
  (b) cites at least one chunk from a gold-cited episode. `trap`-tagged
  questions embed a false premise; passing requires *correcting* it.
- **Growth rule:** the set is append-only. Every time the human tester (a
  show fanatic) catches the system in an error, that error becomes a new
  question. Target: 200+ questions before trusting accuracy claims.
- Season 5 questions are deliberately thin until S5 transcripts land
  (FOLLOWUPS.md) — wiki chunks cover S5 events at low resolution only.
