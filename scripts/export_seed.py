"""Export data/family/* into out/seed/*.json — one file per Hope Chest table,
field names matching hopechest-demo-2026/prisma/schema.prisma — so a fresh,
isolated "Bluth" chest account seeds in one pass.

Emitted tables: people, relationships, locations, life_events, documents
(one per transcript, kind "record"), photos + photo_people (from the screencap
manifest, capped at PHOTOS_PER_EPISODE to keep the seed sane; face boxes are
full-frame placeholders until the tagging job runs — see FOLLOWUPS.md).
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
FAM = ROOT / "data" / "family"
OUT = ROOT / "out" / "seed"
PHOTOS_PER_EPISODE = 6
SEEDER = "michael"  # contributedBy/uploadedBy for imported artifacts


def load(name):
    return json.loads((FAM / f"{name}.json").read_text())


def people_rows(people):
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "shortName": p["shortName"],
            "fullName": p["fullName"],
            "maidenName": p.get("maidenName"),
            "nicknames": p.get("nicknames", []),
            "alternateNames": p.get("alternateNames", []),
            "relation": p["relation"],
            "gender": p["gender"],
            "lifespan": p.get("lifespan"),
            "avatarSrc": None,
            "photoCount": 0,
        }
        for p in people
    ]


def relationship_rows(rels):
    return [{"fromId": r["fromId"], "toId": r["toId"], "type": r["type"]}
            for r in rels]


def location_rows(locs):
    return [{k: loc.get(k) for k in
             ("id", "label", "street", "city", "state", "country", "lat", "lng")}
            for loc in locs]


def life_event_rows(events):
    return [
        {
            "id": e["id"],
            "personId": e["personId"],
            "kind": e["kind"],
            "title": e["title"],
            "date": e["date"],
            "locationId": e.get("locationId"),
            "description": e.get("description"),
            "createdById": SEEDER,
            "createdAt": "2026-07-20T00:00:00Z",
        }
        for e in events
    ]


def document_rows():
    rows = []
    for path in sorted((ROOT / "data" / "transcripts").glob("s*.md")):
        text = path.read_text()
        body = text.partition("\n---")[2].strip()
        title = next(l.split(": ", 1)[1] for l in text.splitlines()
                     if l.startswith("title:")).strip('"')
        airdate = next((l.split(": ", 1)[1] for l in text.splitlines()
                        if l.startswith("airdate:")), "")
        rows.append({
            "id": f"doc-{path.stem}",
            "title": f"Documentary transcript — {title}",
            "kind": "record",
            "scanSrc": f"pdf/{path.stem}.pdf",  # rendered by make_pdfs.py
            "excerpt": body[:280].rsplit(" ", 1)[0] + "…",
            "year": airdate[:4] or None,
            "uploadedById": SEEDER,
            "locationId": None,
        })
    return rows


def photo_rows(episodes):
    manifest_path = ROOT / "data" / "photos" / "manifest.json"
    if not manifest_path.exists():
        return [], []
    by_code = {e["code"]: e for e in episodes}
    photos, tags, per_ep = [], [], {}
    for img in json.loads(manifest_path.read_text()):
        code = img["episode"]
        if per_ep.get(code, 0) >= PHOTOS_PER_EPISODE:
            continue
        per_ep[code] = per_ep.get(code, 0) + 1
        ep = by_code[code]
        pid = f"photo-{code}-{per_ep[code]:02d}"
        photos.append({
            "id": pid,
            "title": f"{ep['title']} — scene {per_ep[code]}",
            "src": img["url"],
            "width": img.get("width") or 1280,
            "height": img.get("height") or 720,
            "description": f"Documentary still from “{ep['title']}” ({code}).",
            "contributedById": SEEDER,
            "contributedWhen": ep["airdate"],
            "photographer": {"value": "Documentary crew"},
            "takenWhere": None,
            "locationId": None,
            "dateIso": ep["airdate"],
            "dateYear": int(ep["airdate"][:4]) if ep["airdate"][:4].isdigit() else None,
            "dateMonth": int(ep["airdate"][5:7]) if len(ep["airdate"]) == 10 else None,
            "dateDay": int(ep["airdate"][8:10]) if len(ep["airdate"]) == 10 else None,
            "datePrecision": "day" if len(ep["airdate"]) == 10 else "year",
            "dateDisplay": ep["airdate"],
            "dateDeduced": True,
            "dateClue": f"air date of {code}",
        })
        for person in img.get("people", []):
            tags.append({
                "photoId": pid,
                "personId": person,
                "box": {"x": 0, "y": 0, "w": 1, "h": 1},  # placeholder
                "confidence": 0.3,
            })
    return photos, tags


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    people = load("people")
    episodes = load("episodes")
    known = {p["id"] for p in people}
    photos, tags = photo_rows(episodes)
    tables = {
        "people": people_rows(people),
        "relationships": relationship_rows(load("relationships")),
        "locations": location_rows(load("locations")),
        "life_events": life_event_rows(load("life-events")),
        "documents": document_rows(),
        "photos": photos,
        "photo_people": [t for t in tags if t["personId"] in known],
    }
    for name, rows in tables.items():
        path = OUT / f"{name}.json"
        path.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
        print(f"{len(rows):5d} rows -> {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
