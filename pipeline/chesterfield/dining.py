"""Chesterfield dining directory + food-safety lookup.

Builds /dining.html: a browsable list of Chesterfield County restaurants grouped
by type of food, plus a prominent link to the official health-inspection portal.

Restaurant data comes from OpenStreetMap via the keyless Overpass API (no API
key, no cost). OSM is community-maintained, so coverage is good but not
exhaustive; the page says so and invites corrections. The result is cached on
disk (dining_cache.json) so normal builds don't re-query Overpass; it refreshes
when the cache is missing or older than CACHE_TTL_DAYS.

Fails soft: if Overpass is unreachable and there's no cache, the page still
builds with just the inspection-lookup section.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from . import render
from .render import PUBLIC

CACHE = Path(__file__).resolve().parents[1] / "dining_cache.json"
CACHE_TTL_DAYS = 14
OVERPASS = "https://overpass-api.de/api/interpreter"
INSPECTIONS_URL = "https://inspections.myhealthdepartment.com/va-chesterfield"

_QUERY = """[out:json][timeout:90];
area["name"="Chesterfield County"]["admin_level"="6"]->.a;
(
  node["amenity"~"^(restaurant|fast_food|cafe)$"](area.a);
  way["amenity"~"^(restaurant|fast_food|cafe)$"](area.a);
);
out center tags;
"""

# Ordered display categories -> the raw OSM cuisine tokens that map to each.
# First matching category (in this order) wins for a multi-cuisine place.
_CATEGORIES: list[tuple[str, set[str]]] = [
    ("Pizza", {"pizza"}),
    ("Burgers", {"burger", "burgers"}),
    ("Sandwiches & Subs", {"sandwich", "sub", "subs", "deli"}),
    ("Mexican & Tex-Mex", {"mexican", "tex-mex", "latin_american", "burrito", "taco", "tacos"}),
    ("Chicken & Wings", {"chicken", "fried_chicken", "wings", "wing"}),
    ("BBQ", {"barbecue", "bbq"}),
    ("Seafood", {"seafood", "fish", "fish_and_chips"}),
    ("Italian", {"italian", "pasta"}),
    ("Chinese", {"chinese"}),
    ("Japanese & Sushi", {"japanese", "sushi", "ramen"}),
    ("Thai & Vietnamese", {"thai", "vietnamese"}),
    ("Korean", {"korean"}),
    ("Asian (other)", {"asian", "indonesian", "filipino", "noodle", "dumpling", "malaysian"}),
    ("Indian & South Asian", {"indian", "pakistani", "nepalese", "bangladeshi"}),
    ("Mediterranean & Middle Eastern",
     {"mediterranean", "greek", "middle_eastern", "lebanese", "turkish", "falafel", "kebab", "persian"}),
    ("Breakfast & Brunch", {"breakfast", "brunch", "pancake", "pancakes", "waffle"}),
    ("Coffee & Cafés", {"coffee_shop", "coffee", "cafe", "tea", "tea_house"}),
    ("Bakery, Donuts & Desserts",
     {"donut", "doughnut", "bakery", "dessert", "desserts", "pastry", "ice_cream", "frozen_yogurt", "cake"}),
    ("Juice & Smoothies", {"juice", "smoothie", "bubble_tea"}),
    ("Burgers & American", {"american", "steak_house", "steak", "diner", "comfort_food", "cajun", "soul_food"}),
]
_OTHER = "Other & uncategorized"


def _cache_fresh() -> bool:
    if not CACHE.exists():
        return False
    try:
        age_days = (time.time() - CACHE.stat().st_mtime) / 86400
        return age_days < CACHE_TTL_DAYS and bool(json.loads(CACHE.read_text()))
    except (OSError, json.JSONDecodeError):
        return False


def _fetch_overpass() -> list[dict]:
    """Query Overpass via curl (robust TLS), return the raw element list."""
    proc = subprocess.run(
        ["curl", "-s", "--max-time", "100",
         "-A", "ChesterfieldReport/1.0 (brucker.rob@gmail.com)",
         "--data-urlencode", f"data={_QUERY}", OVERPASS],
        capture_output=True, text=True, timeout=110,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError(f"overpass failed: {proc.stderr[:200]}")
    return json.loads(proc.stdout).get("elements", [])


def _load_places() -> list[dict]:
    """Return normalized restaurant records, from cache when fresh."""
    if _cache_fresh():
        try:
            return json.loads(CACHE.read_text())
        except json.JSONDecodeError:
            pass
    try:
        elements = _fetch_overpass()
    except Exception as e:                       # offline/error: fall back to any stale cache
        print(f"  ! dining: overpass fetch failed ({e}); using cache if present")
        if CACHE.exists():
            try:
                return json.loads(CACHE.read_text())
            except json.JSONDecodeError:
                return []
        return []
    places = [_normalize(e) for e in elements if e.get("tags", {}).get("name")]
    places = [p for p in places if p]
    places.sort(key=lambda p: p["name"].lower())
    CACHE.write_text(json.dumps(places, indent=0), encoding="utf-8")
    return places


def _category_for(cuisine_raw: str) -> str:
    tokens = {t.strip().lower() for t in cuisine_raw.split(";") if t.strip()}
    if not tokens:
        return _OTHER
    for label, toks in _CATEGORIES:
        if tokens & toks:
            return label
    return _OTHER


def _normalize(el: dict) -> dict | None:
    t = el.get("tags", {})
    name = (t.get("name") or "").strip()
    if not name:
        return None
    # Coordinates: nodes carry lat/lon directly; ways carry a 'center'.
    lat = el.get("lat", (el.get("center") or {}).get("lat"))
    lon = el.get("lon", (el.get("center") or {}).get("lon"))
    street = (t.get("addr:street") or "").strip()
    city = (t.get("addr:city") or t.get("addr:suburb") or "").strip()
    return {
        "name": name,
        "amenity": t.get("amenity", "restaurant"),
        "category": _category_for(t.get("cuisine", "")),
        "street": street,
        "city": city,
        "lat": round(lat, 6) if isinstance(lat, (int, float)) else None,
        "lon": round(lon, 6) if isinstance(lon, (int, float)) else None,
    }


def _maps_link(p: dict) -> str:
    q = p["name"]
    if p["street"]:
        q += " " + p["street"]
    q += " Chesterfield VA"
    return "https://www.google.com/maps/search/?api=1&query=" + q.replace(" ", "+")


_CSS = """<style>
.din-wrap{max-width:820px;margin:0 auto;}
.din-look{border:1px solid var(--border-strong);background:var(--surface-card);
  border-radius:var(--radius-sm);padding:1.1rem 1.2rem;margin:1.3rem 0;}
.din-look h2{margin:0 0 .4rem;font-size:1.05rem;}
.din-look .cr-btn{margin-top:.7rem;}
.din-note{font-size:.85rem;color:var(--text-secondary);margin:1rem 0 1.4rem;}
.din-jump{display:flex;flex-wrap:wrap;gap:6px;margin:1.2rem 0;}
.din-jump a{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:.04em;
  text-transform:uppercase;color:var(--accent);border:1px solid var(--border-hair);
  border-radius:var(--radius-pill);padding:6px 11px;text-decoration:none;}
.din-jump a:hover{border-color:var(--accent);}
.din-cat{margin:1.8rem 0 0;}
.din-cat h2{font-size:1.15rem;border-bottom:1px solid var(--border-hair);
  padding-bottom:6px;display:flex;justify-content:space-between;align-items:baseline;}
.din-cat h2 span{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);color:var(--text-secondary);}
.din-list{list-style:none;padding:0;margin:.6rem 0 0;
  display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:2px 18px;}
.din-list li{padding:5px 0;font-size:.93rem;border-bottom:1px solid var(--border-hair);}
.din-list a{color:var(--text-default);text-decoration:none;font-weight:500;}
.din-list a:hover{color:var(--accent);}
.din-list .where{display:block;font-size:.76rem;color:var(--text-secondary);}
.din-fast{font:var(--fs-3xs)/1 var(--font-mono);color:var(--text-secondary);}
#din-map{height:430px;width:100%;border:1px solid var(--border-hair);
  border-radius:var(--radius-sm);margin:1.3rem 0;z-index:0;}
.leaflet-popup-content{font-family:var(--font-sans);}
.leaflet-popup-content .pop-cat{font-size:.78rem;color:#5c6d75;}
@media(max-width:560px){#din-map{height:300px;}}
</style>"""


# Embedded Leaflet map of every restaurant (clustered, theme-aware tiles).
# Plain string (NOT .format'd) so the braces in the JS are safe; __DATA__ is
# replaced with the points array. _shell inserts this as the body verbatim.
_MAP_JS = """
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
<div id="din-map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
(function(){
  if (!window.L) return;
  var pts = __DATA__;
  function tileUrl(){
    var light = document.documentElement.getAttribute('data-theme') === 'light';
    return light
      ? 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
      : 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
  }
  var map = L.map('din-map', {scrollWheelZoom:false}).setView([37.378,-77.572], 11);
  var layer = L.tileLayer(tileUrl(), {
    attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains:'abcd', maxZoom:19
  }).addTo(map);
  var cluster = L.markerClusterGroup({maxClusterRadius:45, showCoverageOnHover:false});
  pts.forEach(function(p){
    var q = encodeURIComponent(p[0] + ' Chesterfield VA');
    var html = '<strong>' + p[0] + '</strong><br>'
      + '<span class="pop-cat">' + p[3] + '</span><br>'
      + '<a href="https://www.google.com/maps/search/?api=1&query=' + q + '" target="_blank" rel="noopener">Open in Maps</a>';
    L.marker([p[1], p[2]]).bindPopup(html).addTo(cluster);
  });
  map.addLayer(cluster);
  new MutationObserver(function(){ layer.setUrl(tileUrl()); })
    .observe(document.documentElement, {attributes:true, attributeFilter:['data-theme']});
})();
</script>
"""


def _map_html(places: list[dict]) -> str:
    pts = [[p["name"], p["lat"], p["lon"], p["category"]]
           for p in places if p.get("lat") is not None and p.get("lon") is not None]
    if not pts:
        return ""
    return _MAP_JS.replace("__DATA__", json.dumps(pts, separators=(",", ":")))


def build_dining() -> Path:
    """Build /dining.html: inspection lookup + restaurants grouped by food type."""
    places = _load_places()

    # group by category, preserving the _CATEGORIES order, "Other" last
    order = [label for label, _ in _CATEGORIES] + [_OTHER]
    groups: dict[str, list[dict]] = {k: [] for k in order}
    for p in places:
        groups.setdefault(p["category"], []).append(p)
    groups = {k: v for k, v in groups.items() if v}

    look = (
        '<div class="din-look">'
        '<h2>Check a restaurant’s health inspection</h2>'
        '<p>Health inspections for Chesterfield restaurants are run by the Virginia '
        'Department of Health. You can look up any establishment’s inspection '
        'history, scores and violations on the county health department’s official '
        'portal.</p>'
        f'<a class="cr-btn cr-btn--primary" href="{INSPECTIONS_URL}" '
        'target="_blank" rel="noopener">Look up an inspection →</a>'
        '</div>')

    if not places:
        body = (_CSS + '<div class="din-wrap">'
                '<h1 class="page-title">Chesterfield dining</h1>'
                '<p class="lead">A guide to eating in Chesterfield County.</p>'
                + look +
                '<p class="din-note">Our restaurant directory is being rebuilt and will '
                'be back shortly.</p></div>')
        out = PUBLIC / "dining.html"
        out.write_text(render._shell(body), encoding="utf-8")
        return out

    total = len(places)
    jump = '<div class="din-jump">' + "".join(
        f'<a href="#{render.slugify(label)}">{label}</a>' for label in groups) + '</div>'

    sections = []
    for label, items in groups.items():
        lis = []
        for p in items:
            where = p["street"] or p["city"]
            fast = ' <span class="din-fast">· fast food</span>' if p["amenity"] == "fast_food" else ""
            wl = f'<span class="where">{where}</span>' if where else ""
            lis.append(
                f'<li><a href="{_maps_link(p)}" target="_blank" rel="noopener">'
                f'{p["name"]}</a>{fast}{wl}</li>')
        sections.append(
            f'<section class="din-cat" id="{render.slugify(label)}">'
            f'<h2>{label} <span>{len(items)}</span></h2>'
            f'<ul class="din-list">{"".join(lis)}</ul></section>')

    body = (
        _CSS
        + '<div class="din-wrap">'
        + '<h1 class="page-title">Chesterfield dining</h1>'
        + f'<p class="lead">A guide to {total} places to eat across Chesterfield County, '
          'grouped by type of food, plus how to check any restaurant’s health inspection.</p>'
        + _map_html(places)
        + look
        + jump
        + "".join(sections)
        + '<p class="din-note" style="margin-top:2rem">Restaurant data is from '
          '<a href="https://www.openstreetmap.org" target="_blank" rel="noopener">OpenStreetMap</a>, '
          'a community-maintained map, so it is broad but may be incomplete or out of date. '
          'Spotted a place we are missing or got wrong? <a href="/tip.html">Let us know.</a> '
          'Listing a restaurant is not an endorsement.</p>'
        + '</div>')

    page = render._shell(body)
    page = render._inject_og(
        page, "Chesterfield dining guide",
        f"{total} places to eat in Chesterfield County by type of food, plus health-inspection lookup.",
        "https://chesterfieldreport.com/dining.html",
        page_title="Dining Guide | The Chesterfield Report")
    out = PUBLIC / "dining.html"
    out.write_text(page, encoding="utf-8")
    return out
