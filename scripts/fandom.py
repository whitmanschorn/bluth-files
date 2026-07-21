"""Shared helpers for the arresteddevelopment.fandom.com MediaWiki API.

Stdlib only. Every fetcher in this repo goes through `api()` so rate limiting
and the identifying User-Agent live in one place.
"""

import json
import re
import time
import urllib.parse
import urllib.request

API = "https://arresteddevelopment.fandom.com/api.php"
UA = "bluth-files/0.1 (hopechest test data; me@wschorn.com)"
WIKI_LICENSE = "CC-BY-SA 3.0 (https://www.fandom.com/licensing)"
DELAY_S = 1.0

_last_call = 0.0


def api(**params):
    """GET the MediaWiki API, rate-limited to one call per DELAY_S seconds."""
    global _last_call
    wait = _last_call + DELAY_S - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    params.setdefault("format", "json")
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    _last_call = time.monotonic()
    return data


def page_wikitext(title):
    """Return (resolved_title, wikitext) for a page, following redirects."""
    data = api(
        action="query", prop="revisions", rvprop="content", rvslots="main",
        titles=title, redirects="1",
    )
    page = next(iter(data["query"]["pages"].values()))
    if "missing" in page:
        raise KeyError(f"page not found: {title}")
    return page["title"], page["revisions"][0]["slots"]["main"]["*"]


def page_revision(title=None, revid=None):
    """Return (resolved_title, revid, wikitext) — for the latest revision of
    `title`, or the exact pinned revision when `revid` is given."""
    params = dict(action="query", prop="revisions",
                  rvprop="content|ids", rvslots="main")
    if revid:
        params["revids"] = str(revid)
    else:
        params.update(titles=title, redirects="1")
    data = api(**params)
    page = next(iter(data["query"]["pages"].values()))
    if "missing" in page or "revisions" not in page:
        raise KeyError(f"revision not found: {title or revid}")
    rev = page["revisions"][0]
    return page["title"], rev["revid"], rev["slots"]["main"]["*"]


def page_url(title):
    return "https://arresteddevelopment.fandom.com/wiki/" + urllib.parse.quote(
        title.replace(" ", "_")
    )


def strip_links(text):
    """[[a|b]] -> b, [[a]] -> a, [ext label] -> label."""
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"\[https?://\S+ ([^\]]*)\]", r"\1", text)
    return text


def strip_markup(text):
    """Clean inline wikitext markup, keeping the prose."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", "", text, flags=re.S)
    text = re.sub(r"</?[a-zA-Z][^>]*>", "", text)
    text = strip_links(text)
    text = text.replace("'''", "").replace("''", "")
    text = text.replace("&nbsp;", " ")
    return text


def drop_leading_template(text):
    """Remove one balanced {{...}} template at the start of the page."""
    text = text.lstrip()
    if not text.startswith("{{"):
        return text
    depth, i = 0, 0
    while i < len(text) - 1:
        pair = text[i : i + 2]
        if pair == "{{":
            depth, i = depth + 1, i + 2
        elif pair == "}}":
            depth, i = depth - 1, i + 2
            if depth == 0:
                return text[i:].lstrip()
        else:
            i += 1
    return text


def frontmatter(fields):
    """Render an ordered dict of scalars as a YAML frontmatter block."""
    lines = ["---"]
    for key, value in fields.items():
        value = str(value)
        if re.search(r"[:#\"']", value):
            value = '"' + value.replace('"', '\\"') + '"'
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"
