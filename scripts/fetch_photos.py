"""Build data/photos/manifest.json — an index of show screencaps hosted on the
wiki — and optionally download the binaries into gitignored media/photos/.

The wiki names episode screencaps by episode code ("1x01 Pilot (23).png",
"5x03 - Lindsay Bluth Fünke 01.jpg"), so `list=allimages&aiprefix=<code>`
enumerates them per episode. Character names appearing in an image's filename
become provisional person tags (real face boxes are a follow-up job).

Usage:
    python3 scripts/fetch_photos.py             # manifest only (committed)
    python3 scripts/fetch_photos.py --download  # + binaries into media/ (local)
"""

import json
import pathlib
import re
import sys
import time
import urllib.request

from fandom import UA, api

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "photos" / "manifest.json"
MEDIA = ROOT / "media" / "photos"
EPISODES = json.loads((ROOT / "data" / "family" / "episodes.json").read_text())

# person-id -> filename patterns for provisional tagging
NAME_PATTERNS = {
    "michael": r"\bMichael\b(?! Bluth Jr)",
    "george-michael": r"George.Michael",
    "gob": r"\bG\.?O\.?B\b|\bGob\b",
    "lindsay": r"\bLindsay\b",
    "tobias": r"\bTobias\b",
    "maeby": r"\bMaeby\b",
    "buster": r"\bBuster\b",
    "lucille": r"\bLucille\b(?! Austero| 2)",
    "george-sr": r"\bGeorge Bluth\b|\bGeorge Sr\b",
    "oscar": r"\bOscar\b",
    "steve-holt": r"\bSteve Holt\b",
    "annyong": r"\bAnnyong\b",
    "lucille-austero": r"\bLucille Austero\b|\bLucille 2\b",
    "tracey": r"\bTracey\b",
}


def images_for_prefix(prefix):
    """Yield image dicts from list=allimages for a filename prefix."""
    cont = {}
    while True:
        data = api(action="query", list="allimages", aiprefix=prefix,
                   ailimit="500", aiprop="url|size", **cont)
        yield from data["query"]["allimages"]
        if "continue" not in data:
            return
        cont = {"aicontinue": data["continue"]["aicontinue"]}


def provisional_tags(name):
    # "George Michael" also matches the Michael pattern's absence-guard, so
    # resolve the overlap explicitly.
    tags = [pid for pid, pat in NAME_PATTERNS.items()
            if re.search(pat, name, flags=re.I)]
    if "george-michael" in tags and "michael" in tags:
        tags.remove("michael")
    return tags


def main():
    download = "--download" in sys.argv
    manifest = []
    for ep in EPISODES:
        prefix = f"{ep['season']}x{ep['episode']:02d}"
        rows = []
        for img in images_for_prefix(prefix):
            rows.append({
                "file": img["name"],
                "url": img["url"],
                "width": img.get("width"),
                "height": img.get("height"),
                "episode": ep["code"],
                "title": ep["title"],
                "people": provisional_tags(img["name"]),
            })
        manifest.extend(rows)
        print(f"{ep['code']} {len(rows):4d} images")

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(f"\n{len(manifest)} images -> {MANIFEST.relative_to(ROOT)}")

    if download:
        for row in manifest:
            dest = MEDIA / row["episode"] / row["file"]
            if dest.exists():
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            req = urllib.request.Request(row["url"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as resp:
                dest.write_bytes(resp.read())
            time.sleep(0.5)
        print(f"binaries -> {MEDIA.relative_to(ROOT)}/ (gitignored)")


if __name__ == "__main__":
    main()
