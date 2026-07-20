# bluth-files

Reliable, succinct, thoroughly documented **test data for
[Hope Chest](https://github.com/whitmanschorn/hopechest-demo-2026)** — a
family-memory RAG product. The test family is the Bluths of *Arrested
Development* (the show is ostensibly a documentary about them, which makes it
ideal ground truth: every "family memory" is independently verifiable against
the episodes).

## What's here

```
data/family/       hand-authored canon: people, relationships, locations,
                   life events, all-84-episode index (Hope Chest schema shapes)
data/wiki/         character/location/concept lore docs (CC-BY-SA, attributed)
data/photos/       screencap manifest (image binaries live in gitignored media/)
rag/eval/          gold Q&A set for accuracy testing
scripts/           stdlib-only Python fetch/build pipeline

# generated locally by the pipeline — gitignored, never distributed:
data/transcripts/  full episode transcripts, seasons 1–4 (68 episodes)
corpus/            RAG-ready JSONL chunks with retrieval metadata
out/seed/          JSON rows matching the Hope Chest Prisma tables
media/             screencap binaries
```

Verbatim show dialogue (© 20th Television / Netflix) is deliberately **not in
this repository** — the fetch scripts rebuild it on your machine in ~5
minutes, from the same community-transcript sources, byte-for-byte
reproducibly.

## Quick start

```bash
python3 scripts/fetch_transcripts.py   # transcripts S1–S4 -> data/transcripts/ (~2 min)
python3 scripts/fetch_wiki.py          # refresh lore docs (committed)
python3 scripts/fetch_photos.py        # refresh screencap manifest; --download for binaries
python3 scripts/build_corpus.py        # data/ -> corpus/*.jsonl
python3 scripts/export_seed.py         # -> out/seed/*.json (Hope Chest tables)
```

No dependencies — Python 3.10+ stdlib only. All fetchers are rate-limited and
idempotent.

## Provenance & licensing

See [DATA_SOURCES.md](DATA_SOURCES.md). Wiki-derived text is CC-BY-SA from
arresteddevelopment.fandom.com (attributed per file); transcripts and
screencap binaries are copyrighted show content, so they are fetched locally
by script and never committed or redistributed.

## Notes for the RAG feature builder

Read this before wiring the corpus into Hope Chest. It encodes what we learned
assembling the data.

1. **Trust order on conflicts:** `corpus/family.jsonl` (hand-curated ground
   truth) > `corpus/transcripts.jsonl` (primary evidence — what was actually
   said on screen) > `corpus/wiki.jsonl` (helpful but fan-written; occasionally
   speculative). If a wiki chunk contradicts a transcript, the transcript wins.
2. **Always cite.** Every answer should surface chunk ids, and transcript
   chunks carry `season`/`episode`/`episode_title` — the human tester grades
   against episode-level citations (`rag/eval/questions.jsonl`). An uncited
   answer is a failed answer even when factually right.
3. **Use the metadata as filters, not just payload.** `speakers` on transcript
   chunks makes "what did Tobias say about X" a filtered search, not a hope.
   Person-scoped questions should pre-filter or boost on `speakers` /
   `tags` before semantic ranking.
4. **The narrator is load-bearing.** Narrator lines state the show's actual
   facts and punchline-corrections ("He isn't."). They're excluded from
   `speakers` deliberately — never exclude them from the retrievable text.
5. **Season 5 is out of canon** (product-owner ruling). The transcript corpus
   (S1–S4) is therefore *complete*, not partial. S5 still leaks in at low
   resolution via wiki and family chunks (Cinco de Cuatro, Lucille 2's
   disappearance) — answers drawing on it should flag it as
   "post-documentary material" rather than improvise details.
6. **Expect trap questions.** The eval set embeds false premises
   (`tags: ["trap"]`); the grading rule is that the premise must be corrected.
   Don't tune retrieval to sycophancy — tune it to evidence.
7. **Fuzzy dates are a feature.** In-show chronology ≈ airdates and is
   sometimes deliberately contradictory. `life-events.json` uses
   `precision: circa|year|day` — carry that uncertainty into answers ("around
   2005") instead of inventing exact dates.
8. **Isolation:** seed rows in `out/seed/` are self-contained slug-id tables
   for one chest account; nothing references ids outside this dataset, so a
   test account can be created and torn down atomically.

## Roadmap

[PLAN.md](PLAN.md) for the full plan, [FOLLOWUPS.md](FOLLOWUPS.md) for open
long-running jobs (season 5 transcripts, face tags, deep character documents).
