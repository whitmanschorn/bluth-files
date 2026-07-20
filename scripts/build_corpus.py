"""Build the RAG corpus: data/ -> corpus/*.jsonl.

One JSON object per chunk:
  id        stable chunk id ("s01e01-pilot#004", "wiki-character-michael-bluth#002")
  text      the retrievable passage
  source    "transcript" | "wiki" | "family"
  season/episode/episode_title   (transcript chunks)
  speakers  list of speaker names appearing in the chunk (transcript chunks)
  title/kind                     (wiki chunks)
  source_url, license, retrieved

Transcript chunking: scene-ish windows of ~TARGET_CHARS, split only on blank
lines, with one line of overlap context. Wiki chunking: by section heading.
Family JSON records are emitted whole (they are already succinct).
"""

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
TARGET_CHARS = 1400

SPEAKER_RE = re.compile(r"^([A-Z][A-Za-z.'’ \-]{0,30}):\s", re.M)


def read_frontmatter(path):
    text = path.read_text()
    meta = {}
    if text.startswith("---"):
        head, _, body = text[3:].partition("\n---")
        for line in head.strip().splitlines():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip('"')
    else:
        body = text
    return meta, body.strip()


def windows(paragraphs):
    """Greedy ~TARGET_CHARS windows over paragraphs, 1-paragraph overlap."""
    buf, size, start = [], 0, 0
    i = 0
    while i < len(paragraphs):
        buf.append(paragraphs[i])
        size += len(paragraphs[i])
        if size >= TARGET_CHARS or i == len(paragraphs) - 1:
            yield "\n\n".join(buf)
            buf, size = [paragraphs[i]], len(paragraphs[i])  # overlap
            if i == len(paragraphs) - 1:
                return
        i += 1


def transcript_chunks():
    for path in sorted((ROOT / "data" / "transcripts").glob("s*.md")):
        meta, body = read_frontmatter(path)
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        for n, text in enumerate(windows(paragraphs)):
            yield {
                "id": f"{path.stem}#{n:03d}",
                "text": text,
                "source": "transcript",
                "season": int(meta["season"]),
                "episode": int(meta["episode"]),
                "episode_title": meta["title"],
                "airdate": meta.get("airdate"),
                "speakers": sorted(set(SPEAKER_RE.findall(text)) - {"Narrator"}),
                "source_url": meta.get("source_url"),
                "license": meta.get("license"),
                "retrieved": meta.get("retrieved"),
            }


def wiki_chunks():
    for path in sorted((ROOT / "data" / "wiki").glob("*.md")):
        meta, body = read_frontmatter(path)
        sections = re.split(r"\n(?=#{1,4} )", body)
        for n, text in enumerate(s for s in sections if len(s.strip()) > 80):
            yield {
                "id": f"wiki-{path.stem}#{n:03d}",
                "text": text.strip()[:6000],
                "source": "wiki",
                "title": meta["title"],
                "kind": meta.get("kind"),
                "source_url": meta.get("source_url"),
                "license": meta.get("license"),
                "retrieved": meta.get("retrieved"),
            }


def family_chunks():
    fam = ROOT / "data" / "family"
    for name in ("people", "relationships", "locations", "life-events", "episodes"):
        records = json.loads((fam / f"{name}.json").read_text())
        for n, record in enumerate(records):
            yield {
                "id": f"family-{name}#{n:03d}",
                "text": json.dumps(record, ensure_ascii=False),
                "source": "family",
                "table": name,
            }


def write(name, chunks):
    path = CORPUS / f"{name}.jsonl"
    count = 0
    with path.open("w") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
            count += 1
    print(f"{count:5d} chunks -> {path.relative_to(ROOT)}")


def main():
    CORPUS.mkdir(exist_ok=True)
    write("transcripts", transcript_chunks())
    write("wiki", wiki_chunks())
    write("family", family_chunks())


if __name__ == "__main__":
    main()
