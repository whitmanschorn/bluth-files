"""Fetch character / place / concept lore pages from the wiki into
data/wiki/<slug>.md (CC-BY-SA, attributed in frontmatter).

Page list is explicit and curated below — succinct beats exhaustive. Pass
--episodes to also pull all 84 per-episode pages (long-running; see
FOLLOWUPS.md).
"""

import json
import pathlib
import re
import sys
from datetime import date

from fandom import (WIKI_LICENSE, frontmatter, page_url, page_wikitext,
                    strip_markup)

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "wiki"

CHARACTERS = [
    "Michael Bluth", "George Michael Bluth", "G.O.B.", "Lindsay Bluth Fünke",
    "Tobias Fünke", "Maeby Fünke", "Buster Bluth", "Lucille Bluth", "George Bluth",
    "Oscar Bluth", "Tracey Bluth", "Steve Holt", "Annyong Bluth", "Lucille Austero",
    "Ann Veal", "Barry Zuckerkorn", "Kitty Sanchez", "Rita Leeds", "Stan Sitwell",
    "Sally Sitwell", "Bob Loblaw", "Wayne Jarvis", "Marta Estrella", "Tony Wonder",
    "Rebel Alley", "DeBrie Bardeaux", "Eve Holt", "Narrator",
]

PLACES_AND_CONCEPTS = [
    "Bluth Company", "Banana Stand", "Model Home", "Sudden Valley",
    "Balboa Towers", "Cornballer", "Stair car", "Alliance of Magicians",
    "Motherboy", "Cinco de Cuatro", "Fakeblock", "Wee Britain",
    "RMS Queen Mary", "Boyfights", "Bluth family", "Arrested Development",
]


def slugify(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def clean_wiki(wikitext):
    """Wikitext -> readable markdown: keep prose + headings, drop chrome."""
    text = re.sub(r"<gallery.*?</gallery>", "", wikitext, flags=re.S)
    text = re.sub(r"\[\[(?:File|Image):[^\]]*(?:\[\[[^\]]*\]\][^\]]*)*\]\]", "", text)
    # drop templates, tolerating one level of nesting
    for _ in range(3):
        text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = re.sub(r"^\s*\|.*$", "", text, flags=re.M)  # stray table/infobox rows
    text = re.sub(r"\{\||\|\}", "", text)
    text = strip_markup(text)
    text = re.sub(r"^(=+)\s*(.*?)\s*=+\s*$",
                  lambda m: "#" * min(len(m.group(1)), 4) + " " + m.group(2),
                  text, flags=re.M)
    text = re.sub(r"^\*", "-", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fetch(titles, kind):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    missing = []
    for title in titles:
        try:
            resolved, wikitext = page_wikitext(title)
        except KeyError:
            missing.append(title)
            continue
        meta = {
            "title": resolved,
            "kind": kind,
            "source_url": page_url(resolved),
            "retrieved": date.today().isoformat(),
            "license": WIKI_LICENSE,
        }
        path = OUT_DIR / f"{kind}-{slugify(resolved)}.md"
        path.write_text(frontmatter(meta) + clean_wiki(wikitext) + "\n")
        print(f"{kind:9s} {resolved}")
    return missing


def main():
    missing = fetch(CHARACTERS, "character")
    missing += fetch(PLACES_AND_CONCEPTS, "concept")
    if "--episodes" in sys.argv:
        episodes = json.loads(
            (ROOT / "data" / "family" / "episodes.json").read_text())
        missing += fetch([e["title"] for e in episodes], "episode")
    if missing:
        print("\nMISSING (fix titles):")
        for t in missing:
            print(" ", t)


if __name__ == "__main__":
    main()
