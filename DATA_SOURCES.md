# Data sources, provenance, licensing

| Dataset | Source | License / basis |
|---|---|---|
| `data/transcripts/` (gitignored) | [arresteddevelopment.fandom.com](https://arresteddevelopment.fandom.com) `Transcript of <episode>` pages via the MediaWiki API | Hosted on Fandom under [CC-BY-SA 3.0](https://www.fandom.com/licensing), but the underlying dialogue is © 20th Television / Netflix — so this repo **does not redistribute it**. `scripts/fetch_transcripts.py` rebuilds the files locally for research & product-test use. |
| `data/wiki/` | Fandom character / episode / location pages via the MediaWiki API | CC-BY-SA 3.0, attribution in each file's frontmatter (`source_url`, `retrieved`) |
| `data/family/` | Hand-authored structured facts about the fictional Bluth family | Facts about a fictional work; original expression in this repo is MIT |
| `data/photos/manifest.json` | Fandom image file listings (episode galleries) | Metadata only. Image binaries are show screencaps (© 20th Television / Netflix) — downloaded locally by `scripts/fetch_photos.py`, **never committed** (`media/` is gitignored). |
| `corpus/`, `out/seed/` (gitignored) | Derived from the above, generated locally | Inherits upstream terms; not redistributed because they embed transcript text |

**Season 5 transcripts** are absent: no CC-BY-SA source exists; the usual
transcript sites are bot-challenged. See FOLLOWUPS.md for the sourcing plan.

**Attribution:** every fetched file carries frontmatter with `source_url`,
`retrieved` date, and `license`. If you redistribute wiki-derived text, keep
the attribution and share alike.

**Not affiliated** with Netflix, 20th Television, or Fandom, Inc. This repo is
test data for the Hope Chest product; the Bluths are fictional.

Code (everything in `scripts/`) is MIT — see LICENSE.
