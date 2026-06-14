"""Best-effort hero images for article pages via Open Graph (`og:image`).

Used at render time for published stories that don't already have an image
(YouTube items bring their own thumbnails). Cached on disk, fails soft.
We skip Google News redirect URLs (they don't carry a useful og:image).
"""
from __future__ import annotations

import json
import re
import ssl
import urllib.request
from pathlib import Path

CACHE = Path(__file__).resolve().parents[1] / "ogimage_cache.json"
UA = "ChesterfieldLocalBlog/0.1 (brucker.rob@gmail.com)"
_OG = re.compile(
    r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def _load() -> dict:
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def og_image(url: str) -> str:
    """Return a hero image URL for a page, or '' (cached)."""
    if not url or "news.google.com" in url or "youtube.com" in url:
        return ""
    cache = _load()
    if url in cache:
        return cache[url] or ""
    img = ""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=12) as r:
                head = r.read(120_000).decode("utf-8", errors="replace")
        except urllib.error.URLError as e:
            if isinstance(getattr(e, "reason", None), ssl.SSLCertVerificationError):
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                with urllib.request.urlopen(req, timeout=12, context=ctx) as r:
                    head = r.read(120_000).decode("utf-8", errors="replace")
            else:
                raise
        m = _OG.search(head)
        if m:
            img = m.group(1).strip()
    except Exception:
        return ""                       # don't cache transient errors
    cache[url] = img
    CACHE.write_text(json.dumps(cache, indent=0), encoding="utf-8")
    return img
