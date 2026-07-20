"""Render data/transcripts/*.md as typed-manuscript PDFs in out/pdf/ — the
form a real family archive would hold ("the documentary people sent us the
transcripts; they're in a box in the garage").

Pure stdlib: text-only PDFs using the built-in core fonts (Courier for the
typescript body, Helvetica for the cover header), WinAnsi-encoded, Flate-
compressed. Speaker names are bold, stage directions italic, acts are
headings; each page carries an archive footer.

Run after fetch_transcripts.py. export_seed.py links each PDF via scanSrc.
"""

import pathlib
import re
import zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "transcripts"
OUT = ROOT / "out" / "pdf"

PAGE_W, PAGE_H = 612, 792  # US Letter
MARGIN = 72
LEADING = 13
BODY_SIZE = 10
CHARS_PER_LINE = 74  # Courier 10pt = 6pt/char inside the margins
FOOT_Y = 40

F_BODY, F_BOLD, F_ITAL, F_HEAD, F_SANS = "F1", "F2", "F3", "F4", "F5"
FONTS = {
    F_BODY: "Courier",
    F_BOLD: "Courier-Bold",
    F_ITAL: "Courier-Oblique",
    F_HEAD: "Helvetica-Bold",
    F_SANS: "Helvetica",
}

SPEAKER_RE = re.compile(r"^([A-Z][A-Za-z.'’ \-]{0,30}):\s+(.*)$")
ACT_RE = re.compile(r"^==+\s*(.*?)\s*=*=$")


def pdf_str(text):
    """Encode text as a WinAnsi PDF literal string (bytes)."""
    data = text.encode("cp1252", errors="replace")
    return b"(" + data.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)") + b")"


def wrap(text, width, indent=0):
    lines, line = [], ""
    for word in text.split():
        candidate = (line + " " + word).strip()
        if len(candidate) > width and line:
            lines.append(line)
            line = " " * indent + word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines or [""]


class Page:
    def __init__(self, meta, number):
        self.ops = []
        self.y = PAGE_H - MARGIN
        title = f"{meta['title']} — transcript, p. {number}"
        self.text(FOOT_Y, [(F_SANS, 7, "Bluth family archive · documentary transcripts · " + title)])

    def text(self, y, runs, x=MARGIN):
        parts = [b"BT", f"{x} {y} Td".encode()]
        for font, size, s in runs:
            parts.append(f"/{font} {size} Tf".encode())
            parts.append(pdf_str(s) + b" Tj")
        parts.append(b"ET")
        self.ops.append(b" ".join(parts))

    def line(self, runs, extra_leading=0):
        self.y -= LEADING + extra_leading
        self.text(self.y, runs)

    @property
    def full(self):
        return self.y < MARGIN + LEADING

    def stream(self):
        return b"\n".join(self.ops)


def render_lines(body):
    """Yield (kind, payload) rows: kind in {act, speaker, stage, plain, gap}."""
    for paragraph in body.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        for raw in paragraph.splitlines():
            raw = raw.strip()
            m = ACT_RE.match(raw)
            if m:
                yield "act", m.group(1)
                continue
            m = SPEAKER_RE.match(raw)
            if m:
                yield "speaker", (m.group(1), m.group(2))
            elif raw.startswith("[") and raw.endswith("]"):
                yield "stage", raw
            else:
                yield "plain", raw
        yield "gap", None


def build_pdf(meta, body, dest):
    pages = []

    def page():
        pages.append(Page(meta, len(pages) + 1))
        return pages[-1]

    p = page()
    # cover header
    p.line([(F_HEAD, 18, meta["title"])], extra_leading=6)
    p.line([(F_SANS, 10, f"Documentary transcript · episode {meta['code']} · first aired {meta['airdate']}")])
    p.line([(F_SANS, 8, f"From the family archive. Source: {meta['source_url']} (retrieved {meta['retrieved']})")])
    p.line([(F_SANS, 8, "License: " + meta["license"])], extra_leading=2)
    p.y -= LEADING

    for kind, payload in render_lines(body):
        if p.full:
            p = page()
        if kind == "gap":
            p.y -= LEADING // 2
        elif kind == "act":
            p.y -= LEADING // 2
            p.line([(F_HEAD, 12, payload)], extra_leading=2)
        elif kind == "speaker":
            name, speech = payload
            first, *rest = wrap(speech, CHARS_PER_LINE - len(name) - 2)
            p.line([(F_BOLD, BODY_SIZE, name + ": "), (F_BODY, BODY_SIZE, first)])
            for cont in wrap(" ".join(rest), CHARS_PER_LINE - 4) if rest else []:
                if p.full:
                    p = page()
                p.line([(F_BODY, BODY_SIZE, "    " + cont)])
        else:
            font = F_ITAL if kind == "stage" else F_BODY
            for row in wrap(payload, CHARS_PER_LINE):
                if p.full:
                    p = page()
                p.line([(font, BODY_SIZE, row)])

    write_pdf(dest, pages, meta)


def write_pdf(dest, pages, meta):
    objects = []  # list of bytes bodies; object number = index + 1

    def add(body):
        objects.append(body)
        return len(objects)

    font_ids = {key: add(f"<< /Type /Font /Subtype /Type1 /BaseFont /{name} "
                         f"/Encoding /WinAnsiEncoding >>".encode())
                for key, name in FONTS.items()}
    font_res = " ".join(f"/{k} {n} 0 R" for k, n in font_ids.items())

    page_ids = []
    pages_id_placeholder = len(objects) + 2 * len(pages) + 1
    for pg in pages:
        data = zlib.compress(pg.stream())
        content = add(b"<< /Length %d /Filter /FlateDecode >>\nstream\n%s\nendstream"
                      % (len(data), data))
        page_ids.append(add(
            f"<< /Type /Page /Parent {pages_id_placeholder} 0 R "
            f"/MediaBox [0 0 {PAGE_W} {PAGE_H}] "
            f"/Resources << /Font << {font_res} >> >> "
            f"/Contents {content} 0 R >>".encode()))

    kids = " ".join(f"{n} 0 R" for n in page_ids)
    pages_id = add(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode())
    assert pages_id == pages_id_placeholder
    catalog = add(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode())
    info = add(b"<< /Title " + pdf_str(meta["title"] + " - documentary transcript")
               + b" /Author (Bluth family archive) >>")

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref_at = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += (b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\n"
            b"startxref\n%d\n%%%%EOF\n" % (len(objects) + 1, catalog, info, xref_at))
    dest.write_bytes(bytes(out))


def read_frontmatter(path):
    text = path.read_text()
    head, _, body = text[3:].partition("\n---")
    meta = {}
    for line in head.strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"')
    return meta, body.strip()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for path in sorted(SRC.glob("s*.md")):
        meta, body = read_frontmatter(path)
        dest = OUT / (path.stem + ".pdf")
        build_pdf(meta, body, dest)
        print(f"{dest.relative_to(ROOT)}  ({dest.stat().st_size // 1024} KB)")
    print(f"\n{len(list(OUT.glob('*.pdf')))} transcript PDFs -> {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
