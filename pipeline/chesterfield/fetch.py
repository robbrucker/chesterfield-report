"""Fetchers. Stdlib-only so the pipeline runs with no `pip install`.

For production you'd likely swap to `feedparser` + `httpx` + `trafilatura`
(more robust RSS/Atom handling, full-text extraction). The interface here —
each fetcher returns a list[Item] — stays the same, so that's a drop-in later.
"""
from __future__ import annotations

import html
import json
import re
import ssl
import urllib.request
from email.utils import parsedate_to_datetime

from .models import Item

USER_AGENT = "ChesterfieldLocalBlog/0.1 (contact: brucker.rob@gmail.com)"
TIMEOUT = 20


def _get(url: str) -> bytes:
    """HTTP GET with a normal verified TLS context, falling back to an
    unverified one only if the host's cert can't be verified (some county /
    newspaper hosts have misconfigured chains). We never send credentials,
    so the fallback is acceptable for public read-only feeds."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.read()
    except urllib.error.URLError as e:
        if isinstance(getattr(e, "reason", None), ssl.SSLCertVerificationError):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
                return r.read()
        raise


def _iso(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        return parsedate_to_datetime(date_str).isoformat()
    except (TypeError, ValueError):
        return date_str.strip()


_ITEM_RE = re.compile(r"<item\b[^>]*>(.*?)</item>", re.DOTALL | re.IGNORECASE)


def _tag(block: str, tag: str) -> str:
    """Extract a single tag's text from an RSS <item> block, handling CDATA
    and HTML entities. Regex-based so we don't depend on a working pyexpat /
    libexpat — robust for the well-formed CivicEngage and NWS Atom feeds.
    Production would use feedparser; this keeps the slice dependency-free."""
    m = re.search(rf"<{tag}\b[^>]*>(.*?)</{tag}>", block, re.DOTALL | re.IGNORECASE)
    if not m:
        return ""
    val = m.group(1).strip()
    cdata = re.match(r"<!\[CDATA\[(.*?)\]\]>", val, re.DOTALL)
    if cdata:
        val = cdata.group(1).strip()
    return html.unescape(val).strip()


def _img_from(block: str, desc: str) -> str:
    """Best-effort image URL from an RSS item: media tags, enclosure, or an
    <img> embedded in the description."""
    for pat in (r'<media:content[^>]+url="([^"]+)"[^>]*>',
                r'<media:thumbnail[^>]+url="([^"]+)"',
                r'<enclosure[^>]+url="([^"]+)"[^>]*type="image'):
        m = re.search(pat, block, re.IGNORECASE)
        if m:
            return html.unescape(m.group(1))
    m = re.search(r'<img[^>]+src="([^"]+)"', desc, re.IGNORECASE)
    return html.unescape(m.group(1)) if m else ""


def fetch_rss(source: dict) -> list[Item]:
    """Parse an RSS 2.0 feed. (CivicEngage feeds are RSS 2.0.)"""
    data = _get(source["url"]).decode("utf-8", errors="replace")
    items: list[Item] = []
    for block in _ITEM_RE.findall(data):
        title = _tag(block, "title")
        link = _tag(block, "link")
        desc = _tag(block, "description")
        pub = _tag(block, "pubDate")
        if not title and not link:
            continue
        image = _img_from(block, desc)
        items.append(
            Item(
                source_id=source["id"],
                source_name=source["name"],
                title=title,
                url=link,
                raw_summary=desc,
                published=_iso(pub),
                focus=list(source.get("default_focus", [])),
                license=source.get("license", "press"),
                image=image,
            )
        )
    return items


_ENTRY_RE = re.compile(r"<entry>(.*?)</entry>", re.DOTALL)


def fetch_youtube(source: dict) -> list[Item]:
    """Parse a YouTube channel Atom feed (keyless):
    https://www.youtube.com/feeds/videos.xml?channel_id=UC...
    Each video -> an Item with its thumbnail as the hero image."""
    data = _get(source["url"]).decode("utf-8", errors="replace")
    items: list[Item] = []
    for e in _ENTRY_RE.findall(data):
        title = _tag(e, "title")
        pub = _tag(e, "published")
        lm = re.search(r'<link[^>]+rel="alternate"[^>]+href="([^"]+)"', e)
        watch = html.unescape(lm.group(1)) if lm else ""
        tm = re.search(r'<media:thumbnail[^>]+url="([^"]+)"', e)
        thumb = html.unescape(tm.group(1)) if tm else ""
        desc = _tag(e, "media:description")
        if not title or not watch:
            continue
        items.append(
            Item(
                source_id=source["id"],
                source_name=source["name"],
                title=title,
                url=watch,
                raw_summary=desc,
                published=_iso(pub) if not pub else pub,
                focus=list(source.get("default_focus", [])),
                license=source.get("license", "press"),
                image=thumb,
                video_url=watch,
                media_kind="video",
            )
        )
    return items


_ENTRY_RE2 = re.compile(r"<entry\b[^>]*>(.*?)</entry>", re.DOTALL)
_ALT_LINK_RE = re.compile(r'<link[^>]+rel="alternate"[^>]+href="([^"]+)"', re.IGNORECASE)
_ANY_LINK_RE = re.compile(r'<link[^>]*\bhref="([^"]+)"', re.IGNORECASE)


def fetch_atom(source: dict) -> list[Item]:
    """Generic Atom feed (<entry>) parser for non-YouTube Atom sources such as
    Reddit's `/.rss`. Pulls title, the alternate (or first) link, published or
    updated time, and the content/summary. Reddit emits ISO timestamps already."""
    data = _get(source["url"]).decode("utf-8", errors="replace")
    items: list[Item] = []
    for e in _ENTRY_RE2.findall(data):
        title = _tag(e, "title")
        lm = _ALT_LINK_RE.search(e) or _ANY_LINK_RE.search(e)
        link = html.unescape(lm.group(1)) if lm else ""
        if not title or not link:
            continue
        desc = _tag(e, "content") or _tag(e, "summary")
        pub = _tag(e, "published") or _tag(e, "updated")
        items.append(
            Item(
                source_id=source["id"],
                source_name=source["name"],
                title=title,
                url=link,
                raw_summary=desc,
                published=pub,
                focus=list(source.get("default_focus", [])),
                license=source.get("license", "press"),
                image=_img_from(e, desc),
            )
        )
    return items


def fetch_nws(source: dict) -> list[Item]:
    """National Weather Service active alerts (GeoJSON)."""
    data = json.loads(_get(source["url"]))
    items: list[Item] = []
    for feat in data.get("features", []):
        p = feat.get("properties", {})
        headline = p.get("headline") or p.get("event", "Weather Alert")
        items.append(
            Item(
                source_id=source["id"],
                source_name=source["name"],
                title=headline,
                url=p.get("@id", source["url"]),
                raw_summary=p.get("description", ""),
                published=p.get("sent", ""),
                focus=list(source.get("default_focus", [])),
                license="government",
            )
        )
    return items


FETCHERS = {"rss": fetch_rss, "nws": fetch_nws, "youtube": fetch_youtube,
            "atom": fetch_atom}


def fetch(source: dict) -> list[Item]:
    fn = FETCHERS.get(source["kind"])
    if fn is None:
        raise ValueError(f"Unknown source kind: {source['kind']}")
    return fn(source)
