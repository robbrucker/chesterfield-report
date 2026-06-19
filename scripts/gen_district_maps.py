#!/usr/bin/env python3
"""Generate the Chesterfield congressional-district SVG maps for the voter guide.

One-shot tool (not part of the per-build pipeline): it fetches authoritative
boundaries from the U.S. Census TIGERweb service, simplifies and projects them,
and writes three themed SVGs into public/assets/:

  * elections-districts.svg  county outline + both districts shaded (the split)
  * elections-va01.svg        county outline, VA-01's portion highlighted
  * elections-va04.svg        county outline, VA-04's portion highlighted

Re-run only when district lines change (e.g. after redistricting). Stdlib only.

    /usr/bin/python3 scripts/gen_district_maps.py
"""
import json
import math
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "public" / "assets"

# TIGERweb: Legislative/MapServer layer 0 = 119th Congressional Districts;
# State_County/MapServer layer 1 = Counties. GEOIDs: VA CD 1 = 5101, CD 4 = 5104,
# Chesterfield County = 51041.
LEG = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/0/query"
CNTY = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query"

BRICK = "#9a3322"     # VA-04 fill (matches site accent)
SLATE = "#3f6f86"     # VA-01 fill
OUTLINE = "#3a342c"   # county outline
MUTED = "#d9d2c5"     # inactive district fill on single maps
W = 520               # SVG width in px
PAD = 10
EPS = 0.00035         # ~35m simplification tolerance, in degrees


def fetch(base, where):
    q = urllib.parse.urlencode({
        "where": where, "outFields": "GEOID,NAME",
        "returnGeometry": "true", "outSR": "4326", "f": "geojson",
    })
    with urllib.request.urlopen(f"{base}?{q}", timeout=60) as r:
        return json.load(r)["features"][0]["geometry"]


def rings(geom):
    cs = geom["coordinates"]
    polys = [cs] if geom["type"] == "Polygon" else cs
    for poly in polys:
        for ring in poly:
            yield ring


def _perp(pt, a, b):
    (x, y), (x1, y1), (x2, y2) = pt, a, b
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(x - x1, y - y1)
    t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy))


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    dmax, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        d = _perp(pts[i], pts[0], pts[-1])
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]


print("Fetching boundaries from Census TIGERweb...")
county = fetch(CNTY, "GEOID='51041'")
cd01 = fetch(LEG, "GEOID='5101'")
cd04 = fetch(LEG, "GEOID='5104'")

xs, ys = [], []
for ring in rings(county):
    for x, y in ring:
        xs.append(x)
        ys.append(y)
lon_min, lon_max, lat_min, lat_max = min(xs), max(xs), min(ys), max(ys)
kx = math.cos(math.radians((lat_min + lat_max) / 2))
scale = (W - 2 * PAD) / ((lon_max - lon_min) * kx)
H = round((lat_max - lat_min) * scale + 2 * PAD)


def path_d(geom):
    parts = []
    for ring in rings(geom):
        simp = rdp(ring, EPS)
        if len(simp) < 3:
            simp = ring
        pts = [(PAD + (lon - lon_min) * kx * scale, PAD + (lat_max - lat) * scale)
               for lon, lat in simp]
        parts.append("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    return "".join(parts)


d_county, d01, d04 = path_d(county), path_d(cd01), path_d(cd04)


def svg(body, title):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" aria-label="{title}"><title>{title}</title>'
        f'<defs><clipPath id="cf"><path d="{d_county}"/></clipPath></defs>{body}'
        f'<path d="{d_county}" fill="none" stroke="{OUTLINE}" stroke-width="1.5" stroke-linejoin="round"/></svg>'
    )


maps = {
    "elections-districts.svg": (
        svg(f'<g clip-path="url(#cf)"><path d="{d04}" fill="{BRICK}" fill-opacity="0.55"/>'
            f'<path d="{d01}" fill="{SLATE}" fill-opacity="0.55"/></g>',
            "Map of Chesterfield County split between congressional districts VA-01 and VA-04")),
    "elections-va01.svg": (
        svg(f'<g clip-path="url(#cf)"><rect x="0" y="0" width="{W}" height="{H}" fill="{MUTED}"/>'
            f'<path d="{d01}" fill="{SLATE}" fill-opacity="0.75"/></g>',
            "Map of Chesterfield County highlighting the area in congressional district VA-01")),
    "elections-va04.svg": (
        svg(f'<g clip-path="url(#cf)"><rect x="0" y="0" width="{W}" height="{H}" fill="{MUTED}"/>'
            f'<path d="{d04}" fill="{BRICK}" fill-opacity="0.75"/></g>',
            "Map of Chesterfield County highlighting the area in congressional district VA-04")),
}
for name, doc in maps.items():
    (OUT / name).write_text(doc, encoding="utf-8")
    print(f"wrote {name}: {len(doc)} bytes ({W}x{H})")
