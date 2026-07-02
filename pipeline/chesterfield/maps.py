"""News / development map for Chesterfield County.

Builds public/map.html: an interactive Leaflet map (CDN, no API key) on keyless
CARTO dark-matter tiles, plotting every published story that has numeric
lat/lon. Markers are color-coded by primary focus area, with a legend that
doubles as an on/off filter — toggling everything but "Growth & Development"
gives the classic *development map* view.

Stdlib-only (json for safe data embedding); the interactivity is client-side
Leaflet loaded from a CDN, matching the site's cyberpunk shell.
"""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone

from . import render
from .render import (
    FOCUS_COLORS, PUBLIC, _focus_color, _pretty_date, _primary_focus,
    _published_records, slugify, story_url,
)
from .sources import FOCUS_AREAS

# Chesterfield County centroid.
CENTER_LAT, CENTER_LON, ZOOM = 37.38, -77.59, 11

# Chesterfield County bounding box (generous). Geocoding occasionally returns
# garbage — a wrong-state match or Nominatim's "center of the USA" fallback
# (39.78,-100.44) — which would drag the whole map out to North America. Any
# coordinate outside this box is a bad geocode and is dropped from the map.
_BBOX = (36.9, 37.8, -78.1, -77.2)  # (lat_min, lat_max, lon_min, lon_max)


def _in_chesterfield(lat: float, lon: float) -> bool:
    return _BBOX[0] <= lat <= _BBOX[1] and _BBOX[2] <= lon <= _BBOX[3]


def _markers() -> list[dict]:
    """Every published story with usable coordinates -> a marker dict."""
    out = []
    for meta, body, name in _published_records():
        lat, lon = (meta.get("lat", "") or "").strip(), (meta.get("lon", "") or "").strip()
        if not lat or not lon:
            continue
        try:
            flat, flon = float(lat), float(lon)
        except ValueError:
            continue
        if not _in_chesterfield(flat, flon):
            continue  # bad geocode (wrong state / Nominatim US-center fallback)
        slug, label = _primary_focus(meta)
        headline = meta.get("headline", "") or name
        out.append({
            "lat": flat,
            "lon": flon,
            "headline": meta.get("headline", "") or name,
            "source": meta.get("source", ""),
            "date": _pretty_date((meta.get("published", "") or "")[:10]),
            "image": (meta.get("image") or "").strip(),
            "url": (meta.get("source_url") or "").strip(),
            "anchor": story_url(headline),
            "focus": slug,
            "focusLabel": label,
            "color": _focus_color(slug),
        })
    return out


def _legend_rows() -> str:
    rows = []
    for slug, (label, _kw) in FOCUS_AREAS.items():
        color = FOCUS_COLORS.get(slug, "#27e6c6")
        rows.append(
            f'<label class="lg-row" data-focus="{slug}">'
            f'<input type="checkbox" checked data-focus="{slug}">'
            f'<span class="lg-dot" style="background:{color};box-shadow:0 0 8px {color}"></span>'
            f'<span class="lg-label">{html.escape(label)}</span></label>'
        )
    return "".join(rows)


_MAP_CSS = """
  .map-page {{ margin-bottom:1.5rem; }}
  .map-shell {{ display:grid; grid-template-columns:240px 1fr; gap:1.1rem;
    align-items:start; }}
  #map {{ height:72vh; min-height:460px; border:1px solid var(--line);
    border-radius:14px; background:#0a1f28;
    box-shadow:0 0 36px rgba(39,230,198,.10), inset 0 0 60px rgba(0,0,0,.5); }}
  .map-legend {{ background:var(--surface); border:1px solid var(--line);
    border-radius:14px; padding:1.1rem 1.15rem; position:sticky; top:1rem;
    box-shadow:0 0 24px rgba(39,230,198,.06); }}
  .map-legend h2 {{ font-family:var(--mono); font-size:.74rem; font-weight:700;
    text-transform:uppercase; letter-spacing:.1em; color:var(--neon);
    margin:0 0 .85rem; text-shadow:0 0 10px rgba(39,230,198,.4); }}
  .lg-row {{ display:flex; align-items:center; gap:.55rem; padding:.32rem 0;
    cursor:pointer; font-family:var(--mono); font-size:.78rem; color:var(--ink); }}
  .lg-row input {{ accent-color:var(--neon); width:15px; height:15px; cursor:pointer; }}
  .lg-row.is-off {{ opacity:.4; }}
  .lg-dot {{ width:12px; height:12px; border-radius:50%; flex:0 0 auto; }}
  .lg-actions {{ display:flex; gap:.4rem; margin-top:.9rem;
    padding-top:.85rem; border-top:1px solid var(--line); flex-wrap:wrap; }}
  .lg-btn {{ font-family:var(--mono); font-size:.66rem; font-weight:700;
    text-transform:uppercase; letter-spacing:.05em; cursor:pointer;
    background:rgba(39,230,198,.1); color:var(--neon);
    border:1px solid rgba(39,230,198,.35); border-radius:6px; padding:.32rem .5rem; }}
  .lg-btn:hover {{ box-shadow:0 0 12px rgba(39,230,198,.35); }}
  .lg-btn.dev {{ color:var(--gold); border-color:rgba(255,201,74,.4);
    background:rgba(255,201,74,.08); }}
  .lg-btn.dev:hover {{ box-shadow:0 0 12px rgba(255,201,74,.4); }}
  /* Leaflet popups, restyled for the dark theme */
  .leaflet-popup-content-wrapper {{ background:var(--surface); color:var(--ink);
    border:1px solid var(--line); border-radius:12px;
    box-shadow:0 0 26px rgba(39,230,198,.2); }}
  .leaflet-popup-tip {{ background:var(--surface);
    border:1px solid var(--line); box-shadow:none; }}
  .leaflet-popup-content {{ margin:.85rem 1rem; font-family:var(--sans);
    font-size:.9rem; line-height:1.45; }}
  .leaflet-popup-content a.pop-h {{ font-family:var(--sans); font-weight:700;
    font-size:1.04rem; color:var(--text-strong,var(--ink)); text-decoration:none; display:block;
    margin-bottom:.35rem; line-height:1.3; letter-spacing:0; }}
  .leaflet-popup-content a.pop-h:hover {{ color:var(--neon); }}
  .leaflet-popup-content .pop-meta {{ font-family:var(--mono); font-size:.7rem;
    text-transform:uppercase; letter-spacing:.05em; color:var(--muted);
    margin-bottom:.45rem; }}
  .leaflet-popup-content img.pop-img {{ width:100%; border-radius:8px;
    display:block; margin:.2rem 0 .5rem; border:1px solid var(--line); }}
  .leaflet-popup-content .pop-focus {{ font-family:var(--mono); font-size:.64rem;
    font-weight:700; text-transform:uppercase; letter-spacing:.05em;
    padding:.12rem .5rem; border-radius:5px; display:inline-block; }}
  .leaflet-popup-close-button {{ color:var(--muted) !important; }}
  .leaflet-container a.leaflet-popup-close-button:hover {{ color:var(--neon) !important; }}
  .leaflet-control-attribution {{ background:rgba(6,20,26,.8) !important;
    color:var(--muted) !important; }}
  .leaflet-control-attribution a {{ color:var(--neon) !important; }}
  .leaflet-bar a {{ background:var(--surface) !important; color:var(--neon) !important;
    border-color:var(--line) !important; }}
  .leaflet-bar a:hover {{ background:var(--bg2) !important; }}
  .map-empty {{ padding:2rem; text-align:center; color:var(--muted);
    font-family:var(--serif); }}
  @media (max-width:720px) {{
    .map-shell {{ grid-template-columns:1fr; }}
    .map-legend {{ position:static; }}
    #map {{ height:60vh; }}
  }}
"""

_MAP_JS = """
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
  integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<script>
(function() {{
  var MARKERS = {markers_json};
  var el = document.getElementById('map');
  if (!el || !window.L) return;
  var map = L.map('map', {{ scrollWheelZoom:true }}).setView([{center_lat}, {center_lon}], {zoom});
  L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd', maxZoom: 19
  }}).addTo(map);

  function esc(s) {{ return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }}
  var byFocus = {{}};   // slug -> [marker,...]
  var bounds = [];
  MARKERS.forEach(function(m) {{
    var ring = L.circleMarker([m.lat, m.lon], {{
      radius: 9, color: m.color, weight: 2, fillColor: m.color,
      fillOpacity: 0.55, opacity: 0.95
    }});
    var link = m.anchor || m.url || '#';
    var img = m.image ? '<img class="pop-img" src="' + esc(m.image) + '" alt="" loading="lazy">' : '';
    ring.bindPopup(
      '<a class="pop-h" href="' + esc(link) + '">' + esc(m.headline) + '</a>' +
      '<div class="pop-meta">' + esc(m.source) + ' &middot; ' + esc(m.date) + '</div>' +
      img +
      '<span class="pop-focus" style="background:' + m.color + '22;color:' + m.color +
      ';border:1px solid ' + m.color + '55">' + esc(m.focusLabel) + '</span>'
    );
    ring.addTo(map);
    (byFocus[m.focus] = byFocus[m.focus] || []).push(ring);
    bounds.push([m.lat, m.lon]);
  }});
  if (bounds.length) {{ try {{ map.fitBounds(bounds, {{ padding:[40,40], maxZoom:13 }}); }} catch(e) {{}} }}

  function setFocus(slug, on) {{
    (byFocus[slug] || []).forEach(function(mk) {{
      if (on) {{ mk.addTo(map); }} else {{ map.removeLayer(mk); }}
    }});
    var row = document.querySelector('.lg-row[data-focus="' + slug + '"]');
    if (row) row.classList.toggle('is-off', !on);
  }}

  document.querySelectorAll('.lg-row input[data-focus]').forEach(function(cb) {{
    cb.addEventListener('change', function() {{ setFocus(cb.getAttribute('data-focus'), cb.checked); }});
  }});

  function applyAll(on) {{
    document.querySelectorAll('.lg-row input[data-focus]').forEach(function(cb) {{
      cb.checked = on; setFocus(cb.getAttribute('data-focus'), on);
    }});
  }}
  var bAll = document.getElementById('lg-all');
  var bNone = document.getElementById('lg-none');
  var bDev = document.getElementById('lg-dev');
  if (bAll) bAll.addEventListener('click', function() {{ applyAll(true); }});
  if (bNone) bNone.addEventListener('click', function() {{ applyAll(false); }});
  if (bDev) bDev.addEventListener('click', function() {{
    document.querySelectorAll('.lg-row input[data-focus]').forEach(function(cb) {{
      var dev = cb.getAttribute('data-focus') === 'growth';
      cb.checked = dev; setFocus(cb.getAttribute('data-focus'), dev);
    }});
  }});
}})();
</script>
"""


def build_map():
    """Render the interactive news/development map -> public/map.html."""
    PUBLIC.mkdir(parents=True, exist_ok=True)
    markers = _markers()

    legend = (
        '<aside class="map-legend">'
        '<h2>Focus areas</h2>'
        f'{_legend_rows()}'
        '<div class="lg-actions">'
        '<button class="lg-btn" id="lg-all" type="button">All</button>'
        '<button class="lg-btn" id="lg-none" type="button">None</button>'
        '<button class="lg-btn dev" id="lg-dev" type="button">Development only</button>'
        '</div></aside>'
    )

    map_or_empty = (
        '<div id="map" role="application" aria-label="Map of Chesterfield County news"></div>'
        if markers else
        '<div id="map"><p class="map-empty">No geolocated stories yet. '
        'Stories gain a map pin once they have a specific location.</p></div>'
    )

    body = (
        '<div class="map-page">'
        '<h1 class="page-title">News &amp; Development Map</h1>'
        '<p class="lead">Every Chesterfield County story we\'ve mapped, color-coded by '
        'focus area. Toggle a category in the legend to filter the map &mdash; switch to '
        '<strong>Development only</strong> for a clean view of growth and rezoning across '
        'the county.</p>'
        '<div class="map-shell">'
        f'{legend}'
        f'{map_or_empty}'
        '</div></div>'
        + "<style>" + _MAP_CSS.format() + "</style>"
        + _MAP_JS.format(
            markers_json=json.dumps(markers),
            center_lat=CENTER_LAT, center_lon=CENTER_LON, zoom=ZOOM,
        )
    )

    out = PUBLIC / "map.html"
    page = render._shell(body, len(markers))
    page = render._inject_og(
        page,
        "News & Development Map | The Chesterfield Report",
        "An interactive map of Chesterfield County news stories, color-coded by topic: "
        "growth and development, schools, public safety, government, and community.",
        f"{render.SITE_URL}/map.html",
        og_type="website",
        page_title="News & Development Map | The Chesterfield Report")
    out.write_text(page, encoding="utf-8")
    return out
