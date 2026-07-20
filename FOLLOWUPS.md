# Follow-ups — long-running jobs

Ordered by value to RAG accuracy. Each is scoped to run as an independent
session / sub-agent job.

## 1. Season 5 transcripts (blocks "complete transcript" goal)

The wiki has no `Transcript of` pages for S5's 16 episodes. Known sources are
bot-challenged for plain HTTP (subslikescript.com → Cloudflare challenge;
transcripts.foreverdreaming.org → Anubis JS challenge). Options, best first:

1. **Own subtitles**: rip .srt from a personal copy / OpenSubtitles API (free
   key) → `scripts/` gains a `srt_to_transcript.py` (speaker-less, still
   fully searchable). Most reliable; least legally fuzzy.
2. **Browser-assisted fetch**: drive a real browser (Claude-in-Chrome /
   Playwright) through the 16 Forever Dreaming topic pages, save HTML,
   convert with the same cleaner.
3. Watch the wiki — transcripts get added over time; `fetch_transcripts.py`
   picks up new pages automatically on re-run.

## 2. Photo face tags

`data/photos/manifest.json` has 6,301 screencaps but only S5 filenames name
characters (31 provisional tags). Job: run local face detection + clustering
over `media/photos/` (fetch with `--download` first), label clusters once by
hand (9 core faces), emit real `photo_people` boxes. Until then the seed uses
full-frame placeholder boxes at confidence 0.3.

## 3. Per-character deep documents

`data/wiki/` covers 45 pages. Expand with per-character *timelines* distilled
from transcripts (every scene a character appears in, per episode) — a script
job over `corpus/transcripts.jsonl` keyed on `speakers`. Tobias and Lindsay
first (per product priorities).

## 4. Episode lore pages

`fetch_wiki.py --episodes` pulls all 84 per-episode wiki pages (recaps,
running-joke callouts). ~3 minutes; adds ~600 wiki chunks. Skipped from v1 to
keep the corpus review-able.

## 5. Eval set growth

25 gold questions now. Rule: every error the human tester catches becomes a
question. Target 200+ spanning all seasons, ≥20% trap questions (false
premises the system must correct).

## 6. On-this-day & newsletter fixtures

Hope Chest's feed/newsletter features want `feed_items` and
`newsletter_issues` rows. Generate from `life-events.json` anniversaries once
the seed uploads cleanly.
