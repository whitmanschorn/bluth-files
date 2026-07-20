# Plan — bluth-files

Test data for **Hope Chest** (family-memory RAG product,
[hopechest-demo-2026](https://github.com/whitmanschorn/hopechest-demo-2026)).
The Bluth family of *Arrested Development* is the test family: the show is
framed as a documentary, so its transcripts, wiki lore, and screencaps map
naturally onto Hope Chest's people / photos / documents / life-events model.

## Goals

1. **Bulk upload** — produce data shaped for the Hope Chest Prisma schema so a
   new isolated "Bluth" chest account can be seeded in one pass
   (`out/seed/*.json`, one file per table).
2. **RAG accuracy testing** — produce a chunked, metadata-rich corpus
   (`corpus/*.jsonl`) plus a gold Q&A eval set (`rag/eval/questions.jsonl`)
   so answers can be scored against fanatical ground-truth knowledge.

## Data layers

| Layer | Source | Committed? | Status |
|---|---|---|---|
| Transcripts S1–S4 (68 eps) | arresteddevelopment.fandom.com `Transcript of *` pages, MediaWiki API | no — fetched locally into gitignored `data/transcripts/` (verbatim dialogue is not redistributed) | scripted |
| Transcripts S5 (16 eps) | not on fandom; bot-challenged transcript sites → follow-up job | no (gap) | see FOLLOWUPS.md |
| Wiki lore docs | fandom character/episode/location pages (CC-BY-SA) | yes (`data/wiki/`) | scripted |
| Family core data | hand-authored from show canon | yes (`data/family/`) | authored |
| Episode index | scripted from wiki season templates, all 84 eps S1–S5 | yes (`data/family/episodes.json`) | scripted |
| Photos (screencaps) | fandom image files per episode/character | manifest only (`data/photos/manifest.json`); binaries in gitignored `media/` | scripted |
| RAG corpus chunks | derived from the above by `scripts/build_corpus.py` | no — generated (`corpus/`, gitignored: contains transcript text) | scripted |
| Seed export | derived by `scripts/export_seed.py` | no — generated (`out/seed/`, gitignored) | scripted |

## Pipeline

```
fetch_transcripts.py ─┐
fetch_wiki.py ────────┼─> data/ ──> build_corpus.py ──> corpus/*.jsonl ──> RAG index
fetch_photos.py ──────┘      └────> export_seed.py ──> out/seed/*.json ──> Hope Chest DB
   (hand-authored data/family/*.json feeds both)
```

All scripts are Python 3 stdlib-only (no venv, no deps), idempotent, and
rate-limited. Re-running refreshes in place.

## Hope Chest schema mapping

From `hopechest-demo-2026/prisma/schema.prisma`:

- `data/family/people.json` → `people` (slug ids, nicknames, lifespans)
- `data/family/relationships.json` → `relationships` (`parent` / `spouse` edges)
- `data/family/locations.json` → `locations` (model home, banana stand, …)
- `data/family/life-events.json` → `life_events` (FuzzyDate JSON, kind enum)
- `data/photos/manifest.json` → `photos` + `photo_people` (face tags = TODO)
- transcripts & wiki docs → `documents` (kind `record`) *and* the RAG corpus;
  the corpus is the primary retrieval surface, documents are the in-app view

## RAG testing loop

1. Embed `corpus/*.jsonl` (each chunk carries `source`, `season`, `episode`,
   `speakers`, `license`).
2. Chat about family history; every answer must cite chunk ids.
3. Score against `rag/eval/questions.jsonl` (question, gold answer, gold
   episode citation). Add questions whenever the human tester catches an error
   — the eval set is append-only and grows from real failures.

## Version 1 definition of done

- [x] Transcripts S1–S4 (scripted fetch; local-only by design)
- [ ] Transcripts S5 (blocked on source — FOLLOWUPS.md)
- [x] Core family data + episode index
- [x] Wiki lore docs for the 9 core Bluths + key recurring characters
- [x] Photo manifest + fetch script (100s of screencaps, local)
- [x] Corpus build + seed export
- [x] Eval question set (starter)

## Long-running / sub-agent jobs (post-v1)

See `FOLLOWUPS.md`: S5 transcript sourcing, per-character deep documents
(Tobias, Lindsay, …), photo face-tagging boxes, per-photo FuzzyDate + episode
event linking, expansion of the eval set to 200+ questions.
