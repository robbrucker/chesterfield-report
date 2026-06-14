"""Geocoding via OpenStreetMap Nominatim — free, no API key.

Results are cached on disk so repeated builds don't re-query, and we respect
Nominatim's usage policy (descriptive User-Agent, max ~1 request/second).
Everything fails soft: offline or no-match simply returns None and the site
renders without a map.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

CACHE = Path(__file__).resolve().parents[1] / "geocode_cache.json"
USER_AGENT = "ChesterfieldLocalBlog/0.1 (brucker.rob@gmail.com)"
ENDPOINT = "https://nominatim.openstreetmap.org/search"
_last_call = [0.0]


def _load() -> dict:
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _save(cache: dict) -> None:
    CACHE.write_text(json.dumps(cache, indent=0), encoding="utf-8")


def _variants(query: str) -> list[str]:
    """Query forms to try, best-first. Nominatim resolves
    '<place>, Chesterfield, VA, USA' well but fails on '&' intersections, so we
    also fall back to the primary street of an intersection."""
    q = query.strip().rstrip(",")
    low = q.lower()
    out = []

    def add(s):
        if s and s not in out:
            out.append(s)

    add(q if "usa" in low else (q + ", USA"))
    if "chesterfield" not in low:
        add(f"{q}, Chesterfield, VA, USA")
    else:
        add(f"{q}, VA, USA")
    # Intersection ("A and B" / "A at B" / "A & B") -> try the first street.
    first = re.split(r"\s+(?:and|at|&|/)\s+", q, maxsplit=1)[0].strip()
    if first and first.lower() != q.lower():
        add(f"{first}, Chesterfield, VA, USA")
    return out


def _query_nominatim(q: str):
    wait = 1.05 - (time.monotonic() - _last_call[0])
    if wait > 0:
        time.sleep(wait)
    params = urllib.parse.urlencode(
        {"q": q, "format": "json", "limit": 1, "countrycodes": "us"}
    )
    req = urllib.request.Request(f"{ENDPOINT}?{params}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as r:
        hits = json.loads(r.read())
    _last_call[0] = time.monotonic()
    if not hits:
        return None
    h = hits[0]
    return {"lat": float(h["lat"]), "lon": float(h["lon"]),
            "display_name": h.get("display_name", q)}


# Chesterfield County bounding box. A geocode outside it is a bad match (wrong
# state, or Nominatim's "center of the USA" 39.78,-100.44 fallback) — reject it
# so we never store/plot a pin in the wrong place.
_BBOX = (36.9, 37.8, -78.1, -77.2)  # lat_min, lat_max, lon_min, lon_max


def _in_bbox(lat, lon) -> bool:
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return False
    return _BBOX[0] <= lat <= _BBOX[1] and _BBOX[2] <= lon <= _BBOX[3]


def geocode(query: str):
    """Return {'lat': float, 'lon': float, 'display_name': str} or None.
    Tries several query forms; caches by the original query. Results outside
    Chesterfield County are rejected (bad geocodes)."""
    if not query or not query.strip():
        return None
    key = query.strip()
    cache = _load()
    if key in cache:               # cached hit (incl. cached misses as null)
        return cache[key]

    result = None
    try:
        for variant in _variants(key):
            result = _query_nominatim(variant)
            if result:
                break
    except Exception:
        return None                # offline/error: don't cache; retry next time

    if result and not _in_bbox(result.get("lat"), result.get("lon")):
        result = None              # outside Chesterfield -> bad geocode, treat as miss

    cache[key] = result            # cache the answer (including a null miss)
    _save(cache)
    return result
