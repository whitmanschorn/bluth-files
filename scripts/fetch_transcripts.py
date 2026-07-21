"""Fetch every "Transcript of <episode>" page from the wiki into
data/transcripts/<code>-<slug>.md with provenance frontmatter.

The wiki hosts community transcripts for all of S1–S4 (68 episodes); S5 has no
transcript pages there — see FOLLOWUPS.md. Dialogue format in the output:

    [stage direction]
    Speaker: line

Run after fetch_episodes.py (filenames key on the episode index).

Reproducibility: data/transcripts.lock.json (committed) pins each transcript
to an exact wiki revision id + SHA-256 of the emitted file, so every clone
rebuilds byte-identical transcripts. Locked episodes are fetched by revid and
checksum-verified; new episodes get locked on first fetch. `--repin` refetches
latest revisions and rewrites the lock (bump the npm version after).
"""

import hashlib
import json
import pathlib
import re
import sys
from datetime import date

from fandom import (WIKI_LICENSE, api, drop_leading_template, frontmatter,
                    page_revision, page_url, strip_links)

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "transcripts"
LOCK = ROOT / "data" / "transcripts.lock.json"
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
    repin = "--repin" in sys.argv
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lock = json.loads(LOCK.read_text()) if LOCK.exists() and not repin else {}
    by_title = {e["title"]: e for e in EPISODES}
    unmatched, written, drift = [], 0, []

    for page_title in transcript_pages():
        ep_title = page_title.removeprefix("Transcript of ").strip()
        ep = by_title.get(ALIASES.get(ep_title, ep_title))
        if ep is None:
            unmatched.append(page_title)
            continue
        pin = lock.get(ep["code"])
        if pin:
            _, revid, wikitext = page_revision(revid=pin["revid"])
            retrieved = pin["retrieved"]
        else:
            _, revid, wikitext = page_revision(title=page_title)
            retrieved = date.today().isoformat()
        meta = {
            "title": ep["title"],
            "code": ep["code"],
            "season": ep["season"],
            "episode": ep["episode"],
            "airdate": ep["airdate"],
            "source_url": f"{page_url(page_title)}?oldid={revid}",
            "retrieved": retrieved,
            "license": WIKI_LICENSE,
        }
        content = frontmatter(meta) + clean_body(wikitext) + "\n"
        sha = hashlib.sha256(content.encode()).hexdigest()
        if pin and sha != pin["sha256"]:
            drift.append(ep["code"])
        lock[ep["code"]] = {"page": page_title, "revid": revid,
                            "retrieved": retrieved, "sha256": sha}
        (OUT_DIR / f"{ep['code']}-{ep['slug']}.md").write_text(content)
        written += 1
        print(f"{ep['code']}  rev {revid}  {ep['title']}")

    LOCK.write_text(json.dumps(dict(sorted(lock.items())), indent=1) + "\n")
    print(f"\nwrote {written} transcripts -> {OUT_DIR.relative_to(ROOT)}/")
    print(f"lock: {LOCK.relative_to(ROOT)} ({len(lock)} pins)")
    if drift:
        print(f"CHECKSUM DRIFT (pinned revid produced different bytes — "
              f"investigate before trusting): {', '.join(drift)}")
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
