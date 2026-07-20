"""Build data/family/episodes.json from the wiki's Season N Episodes templates.

Each template is a sequence of {{EpisodeList |ep= |overall= |airdate= |title=
|summary= ...}} blocks in broadcast order — the authoritative index for all 84
episodes (S1–S5) that every other script keys on.
"""

import json
import pathlib
import re
from datetime import date, datetime

from fandom import api, page_url, strip_markup

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "family" / "episodes.json"

FIELD_RE = re.compile(r"^\|\s*(\w+)\s*=\s*(.*)$")


def parse_blocks(wikitext):
    """Yield {field: value} for each {{EpisodeList ...}} block, in order."""
    for chunk in wikitext.split("{{EpisodeList")[1:]:
        chunk = chunk.split("\n}}")[0]
        fields, last = {}, None
        for line in chunk.splitlines():
            m = FIELD_RE.match(line)
            if m:
                last = m.group(1).lower()
                fields[last] = m.group(2).strip()
            elif last and line.strip() and not line.startswith("}}"):
                fields[last] += " " + line.strip()
        yield fields


def norm_date(raw):
    raw = strip_markup(raw).strip().rstrip(".").replace("Nov.", "November")
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return date.strftime(datetime.strptime(raw, fmt), "%Y-%m-%d")
        except ValueError:
            continue
    return raw  # leave unparseable dates visible rather than guessing


def slugify(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower().replace("ñ", "n"))
    return slug.strip("-")


def main():
    episodes = []
    for season in range(1, 6):
        _, wikitext = api_template(season)
        for fields in parse_blocks(wikitext):
            title = strip_markup(fields["title"]).strip()
            ep = int(fields["ep"])
            episodes.append(
                {
                    "code": f"s{season:02d}e{ep:02d}",
                    "season": season,
                    "episode": ep,
                    "overall": int(fields["overall"]),
                    "title": title,
                    "slug": slugify(title),
                    "airdate": norm_date(fields.get("airdate", "")),
                    "summary": strip_markup(fields.get("summary", "")).strip(),
                    "source_url": page_url(title),
                }
            )
        print(f"season {season}: {sum(e['season'] == season for e in episodes)} episodes")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(episodes, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(episodes)} episodes -> {OUT.relative_to(ROOT)}")


def api_template(season):
    data = api(
        action="query", prop="revisions", rvprop="content", rvslots="main",
        titles=f"Template:Season {season} Episodes", redirects="1",
    )
    page = next(iter(data["query"]["pages"].values()))
    return page["title"], page["revisions"][0]["slots"]["main"]["*"]


if __name__ == "__main__":
    main()
