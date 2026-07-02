"""Geocoding via OpenStreetMap Nominatim with a US Census fallback — free, no
API keys.

Results are cached on disk so repeated builds don't re-query. Successful hits
are cached forever; misses are cached with a timestamp and retried after
MISS_TTL_DAYS (the geocoders improve, and our query normalization does too).
We respect Nominatim's usage policy (descriptive User-Agent, max ~1 request
per second) and apply a similar modest throttle to the Census endpoint.
Everything fails soft: offline or no-match simply returns None and the site
renders without a map pin for that story.
"""
from __future__ import annotations

import datetime as _dt
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

CACHE = Path(__file__).resolve().parents[1] / "geocode_cache.json"
USER_AGENT = "ChesterfieldLocalBlog/0.1 (brucker.rob@gmail.com)"
ENDPOINT = "https://nominatim.openstreetmap.org/search"
CENSUS_ENDPOINT = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
MISS_TTL_DAYS = 14
_last_call = [0.0]          # Nominatim politeness throttle
_last_census_call = [0.0]   # Census politeness throttle


def _load() -> dict:
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _save(cache: dict) -> None:
    CACHE.write_text(json.dumps(cache, indent=0), encoding="utf-8")


# Communities/post towns inside Chesterfield County. Used both to recognize a
# trailing town in a location string and as a last-resort geocode target.
_TOWNS = (
    "north chesterfield", "south chesterfield", "midlothian", "chester",
    "matoaca", "moseley", "bon air", "ettrick", "enon", "chesterfield",
)

# Street-ish suffixes that suggest a token is a road, not a venue name.
_ROAD_RE = re.compile(
    r"\b(?:road|rd|street|st|avenue|ave|boulevard|blvd|drive|dr|lane|ln|"
    r"parkway|pkwy|highway|hwy|court|ct|circle|cir|place|pl|way|turnpike|"
    r"pike|trail|route|rte)\b\.?", re.IGNORECASE)


def _find_town(text: str) -> str | None:
    low = text.lower()
    for t in _TOWNS:  # multi-word towns first so "Chesterfield" can't shadow
        if re.search(rf"\b{re.escape(t)}\b", low):
            return t.title()
    return None


def _variants(query: str) -> list[str]:
    """Query forms to try, best-first.

    Normalizations, in rough order of specificity:
      - '"NNNN block of X Road"' -> 'X Road' (crime-blotter style addresses)
      - the full string as given (suffixed with VA/USA context)
      - venue prefixes stripped progressively: 'Venue, 123 Main St, Town, VA'
        -> '123 Main St, Town, VA' -> '123 Main St, Chesterfield County, VA'
      - a bare road name + 'Chesterfield County, VA'
      - the first street of an intersection ('A and B' / 'A at B' / 'A & B')
      - the community/town alone ('Midlothian, VA') as a last resort
    """
    q = query.strip().rstrip(",").rstrip(".")
    # "2800 block of E. Hundred Road" -> "E. Hundred Road"
    q = re.sub(r"\b\d+\s+block\s+of\s+", "", q, flags=re.IGNORECASE)
    low = q.lower()
    out: list[str] = []

    def add(s):
        s = (s or "").strip().strip(",")
        if s and s not in out:
            out.append(s)

    # 1) Full string with geographic context.
    if "usa" in low:
        add(q)
    elif "virginia" in low or re.search(r"\bva\b", low):
        add(f"{q}, USA")
    elif "chesterfield" in low:
        add(f"{q}, VA, USA")
    else:
        add(f"{q}, Chesterfield County, VA, USA")

    parts = [p.strip() for p in q.split(",") if p.strip()]
    town = _find_town(q)

    # 2) Progressively drop leading venue names: keep any comma parts after the
    #    first that still carry an address (digits or a road suffix or a town).
    for i in range(1, len(parts)):
        tail = ", ".join(parts[i:])
        tl = tail.lower()
        if re.search(r"\d", tail) or _ROAD_RE.search(tail):
            if "virginia" in tl or re.search(r"\bva\b", tl):
                add(f"{tail}, USA")
            elif "chesterfield" in tl or _find_town(tail):
                add(f"{tail}, VA, USA")
            else:
                add(f"{tail}, Chesterfield County, VA, USA")

    # 3) A bare road mentioned anywhere in the string (first road-looking chunk).
    for part in parts:
        m = _ROAD_RE.search(part)
        if m:
            # keep the words leading up to and including the road suffix
            road = part[: m.end()].strip()
            # drop leading venue-ish words before a house number if present
            mnum = re.search(r"\d[\w.\- ]*$", road)
            if mnum and not road[0].isdigit():
                road = road[mnum.start():].strip()
            if road:
                add(f"{road}, Chesterfield County, VA, USA")
            break

    # 4) Intersection ("A and B" / "A at B" / "A & B") -> try the first street.
    first = re.split(r"\s+(?:and|at|&|/)\s+", q, maxsplit=1)[0].strip()
    if first and first.lower() != q.lower():
        add(f"{first}, Chesterfield County, VA, USA")

    # 5) Last resort: the community/town centroid.
    if town:
        add(f"{town}, VA, USA")
    return out


def _throttle(slot: list, min_gap: float) -> None:
    wait = min_gap - (time.monotonic() - slot[0])
    if wait > 0:
        time.sleep(wait)


def _query_nominatim(q: str):
    _throttle(_last_call, 1.05)
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


def _query_census(q: str):
    """US Census geocoder — free, no key, strong on street addresses.
    Returns the same shape as _query_nominatim or None."""
    _throttle(_last_census_call, 0.55)
    params = urllib.parse.urlencode(
        {"address": q, "benchmark": "Public_AR_Current", "format": "json"}
    )
    req = urllib.request.Request(f"{CENSUS_ENDPOINT}?{params}",
                                 headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    _last_census_call[0] = time.monotonic()
    matches = (data.get("result") or {}).get("addressMatches") or []
    if not matches:
        return None
    m = matches[0]
    coords = m.get("coordinates") or {}
    try:
        return {"lat": float(coords["y"]), "lon": float(coords["x"]),
                "display_name": m.get("matchedAddress", q)}
    except (KeyError, TypeError, ValueError):
        return None


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


def _is_hit(entry) -> bool:
    return isinstance(entry, dict) and "lat" in entry and "lon" in entry


def _miss_is_fresh(entry) -> bool:
    """A cached miss counts (i.e. we skip re-querying) only while it's fresh.
    Legacy plain-null misses have no timestamp -> always retry them."""
    if not isinstance(entry, dict) or "miss_at" not in entry:
        return False
    try:
        when = _dt.datetime.fromisoformat(entry["miss_at"])
    except (TypeError, ValueError):
        return False
    age = _dt.datetime.now(_dt.timezone.utc) - when
    return age < _dt.timedelta(days=MISS_TTL_DAYS)


def geocode(query: str):
    """Return {'lat': float, 'lon': float, 'display_name': str} or None.

    Tries several query forms against Nominatim, then the US Census geocoder.
    Caches by the original query: hits forever, misses for MISS_TTL_DAYS.
    Results outside Chesterfield County are rejected (bad geocodes)."""
    if not query or not query.strip():
        return None
    key = query.strip()
    cache = _load()
    if key in cache:
        entry = cache[key]
        if _is_hit(entry):
            if _in_bbox(entry.get("lat"), entry.get("lon")):
                return entry
            # legacy cached bad geocode (e.g. center-of-USA): retry below
        if _miss_is_fresh(entry):
            return None
        # legacy null or stale miss marker: fall through and retry

    result = None
    variants = _variants(key)
    try:
        for variant in variants:
            r = _query_nominatim(variant)
            if r and _in_bbox(r.get("lat"), r.get("lon")):
                result = r
                break
        if result is None:
            for variant in variants:
                r = _query_census(variant)
                if r and _in_bbox(r.get("lat"), r.get("lon")):
                    result = r
                    break
    except Exception:
        return None                # offline/error: don't cache; retry next time

    if result is None:
        cache[key] = {"miss_at": _dt.datetime.now(_dt.timezone.utc).isoformat()}
    else:
        cache[key] = result
    _save(cache)
    return result
