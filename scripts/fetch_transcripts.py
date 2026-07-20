"""Fetch every "Transcript of <episode>" page from the wiki into
data/transcripts/<code>-<slug>.md with provenance frontmatter.

The wiki hosts community transcripts for all of S1–S4 (68 episodes); S5 has no
transcript pages there — see FOLLOWUPS.md. Dialogue format in the output:

    [stage direction]
    Speaker: line

Run after fetch_episodes.py (filenames key on the episode index).
"""

import json
import pathlib
import re
from datetime import date

from fandom import (WIKI_LICENSE, api, drop_leading_template, frontmatter,
                    page_url, page_wikitext, strip_links)

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "transcripts"
EPISODES = json.loads((ROOT / "data" / "family" / "episodes.json").read_text())

# transcript page title -> episode title, where the wiki disagrees with itself
ALIASES = {}


def clean_body(wikitext):
    text = drop_leading_template(wikitext)
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if re.fullmatch(r"\{\{[^{}]*\}\}", line):  # {{callout}} etc.
            continue
        line = re.sub(r"\{\{[^{}]*\}\}", "", line)
        line = re.sub(r"<!--.*?-->", "", line)
        line = re.sub(r"<br\s*/?>", " ", line)
        line = strip_links(line)
        line = line.lstrip(":").strip()
        if re.fullmatch(r"''[^']((?!'').)*''", line):  # whole-line italics
            line = "[" + line.strip("'").strip() + "]"
        line = line.replace("'''", "").replace("''", "")
        # normalize "Speaker:line" -> "Speaker: line"
        line = re.sub(r"^([A-Z][^:\n]{0,40}):(\S)", r"\1: \2", line)
        line = re.sub(r"</?[a-zA-Z][^>]*>", "", line)
        lines.append(line)
    body = "\n".join(lines)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    # drop the boilerplate lead ("The following is the transcript of ...")
    body = re.sub(r"^The following is the transcript of[^\n]*\n+", "", body)
    return body


def transcript_pages():
    data = api(action="query", list="allpages",
               apprefix="Transcript of", aplimit="500")
    return [p["title"] for p in data["query"]["allpages"]]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    by_title = {e["title"]: e for e in EPISODES}
    unmatched, written = [], 0

    for page_title in transcript_pages():
        ep_title = page_title.removeprefix("Transcript of ").strip()
        ep = by_title.get(ALIASES.get(ep_title, ep_title))
        if ep is None:
            unmatched.append(page_title)
            continue
        _, wikitext = page_wikitext(page_title)
        meta = {
            "title": ep["title"],
            "code": ep["code"],
            "season": ep["season"],
            "episode": ep["episode"],
            "airdate": ep["airdate"],
            "source_url": page_url(page_title),
            "retrieved": date.today().isoformat(),
            "license": WIKI_LICENSE,
        }
        path = OUT_DIR / f"{ep['code']}-{ep['slug']}.md"
        path.write_text(frontmatter(meta) + clean_body(wikitext) + "\n")
        written += 1
        print(f"{ep['code']}  {ep['title']}")

    print(f"\nwrote {written} transcripts -> {OUT_DIR.relative_to(ROOT)}/")
    if unmatched:
        print("UNMATCHED (add to ALIASES):")
        for t in unmatched:
            print(" ", t)
    have = {p.stem.split("-")[0][:3] for p in OUT_DIR.glob("s*.md")}
    missing = [e["code"] for e in EPISODES
               if not (OUT_DIR / f"{e['code']}-{e['slug']}.md").exists()]
    print(f"missing episodes ({len(missing)}): {', '.join(missing) or 'none'}")


if __name__ == "__main__":
    main()
