"""Chesterfield County Public Schools directory.

Builds public/schools.html from pipeline/schools_data.json: a clustered map of
every school (colored by level), a search box, level filters, and a card for
each school with address, phone, website, and links out to its GreatSchools
rating and Virginia School Quality Profile.

We do NOT republish GreatSchools' proprietary 1-10 score on the page; we link to
it instead. The on-page signal is the state accreditation context (Virginia
rates schools by accreditation, not A-F letter grades). All roster/contact data
is from oneccps.org, NCES, and the state.

Map markers reuse the same Leaflet + markercluster + CARTO theme-aware pattern
as the dining/business maps. Stdlib-only; reuses render._shell().
"""
from __future__ import annotations

import html
import json
import urllib.parse
from pathlib import Path

from . import render
from .render import PUBLIC

DATA = Path(__file__).resolve().parents[1] / "schools_data.json"

# Order + display for the level filter and map legend.
_LEVELS = ["Elementary", "Middle", "High", "Specialty"]
_LEVEL_COLOR = {
    "Elementary": "#2f7d8f",  # teal
    "Middle": "#c1820e",      # amber
    "High": "#9a3322",        # brick (matches the site accent)
    "Specialty": "#6b6b6b",   # gray
}


def _load() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def _gs_link(name: str, city: str = "") -> str:
    # GreatSchools' own search URL is unreliable and per-school pages need an
    # internal ID we don't have; a scoped search lands on the right GS page.
    q = urllib.parse.quote(f"{name} {city} VA site:greatschools.org")
    return f"https://www.google.com/search?q={q}"


def _maps_link(s: dict) -> str:
    parts = [s.get("address", ""), s.get("city", ""), "VA", s.get("zip", "")]
    q = urllib.parse.quote(" ".join(p for p in parts if p))
    return f"https://www.google.com/maps/search/?api=1&query={q}"


def _card(s: dict) -> str:
    name = html.escape(s["name"])
    level = s.get("level", "")
    color = _LEVEL_COLOR.get(level, "#6b6b6b")

    # Status line: opening-soon / specialty descriptor / nothing.
    badge2 = ""
    if s.get("status"):
        badge2 = f'<span class="sch-soon">{html.escape(s["status"])}</span>'
    elif s.get("note"):
        badge2 = f'<span class="sch-note">{html.escape(s["note"])}</span>'

    addr_parts = [s.get("address", ""), s.get("city", "")]
    addr = ", ".join(p for p in addr_parts if p)
    addr_html = (
        f'<a class="sch-addr" href="{_maps_link(s)}" target="_blank" '
        f'rel="noopener">{html.escape(addr)}</a>' if addr else ""
    )
    phone = s.get("phone", "")
    phone_html = (
        f'<a class="sch-phone" href="tel:{html.escape(phone.replace(" ", ""))}">'
        f'{html.escape(phone)}</a>' if phone else ""
    )

    facts = []
    if s.get("enrollment"):
        facts.append(f'{s["enrollment"]:,} students')
    if s.get("principal"):
        facts.append(html.escape(s["principal"]))
    facts_html = (
        f'<div class="sch-facts">{" · ".join(facts)}</div>' if facts else ""
    )

    links = []
    if s.get("website"):
        links.append(f'<a href="{html.escape(s["website"])}" target="_blank" '
                     'rel="noopener">Website ↗</a>')
    links.append(f'<a href="{_gs_link(s["name"], s.get("city", ""))}" target="_blank" '
                 'rel="noopener">GreatSchools ↗</a>')
    links_html = f'<div class="sch-links">{"".join(links)}</div>'

    search_key = html.escape(f'{s["name"]} {s.get("city","")} {level}'.lower(), quote=True)
    return (
        f'<article class="sch-card" data-level="{html.escape(level)}" '
        f'data-search="{search_key}">'
        f'<span class="sch-tag" style="background:{color}">{html.escape(level)}</span>'
        f'<h3 class="sch-name">{name}</h3>'
        f'{badge2}'
        f'{addr_html}{phone_html}{facts_html}{links_html}'
        '</article>'
    )


_MAP_JS = """
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
<div id="sch-map"></div>
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
  var map = L.map('sch-map', {scrollWheelZoom:false}).setView([37.378,-77.572], 11);
  var layer = L.tileLayer(tileUrl(), {
    attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains:'abcd', maxZoom:19
  }).addTo(map);
  var cluster = L.markerClusterGroup({maxClusterRadius:40, showCoverageOnHover:false});
  pts.forEach(function(p){
    var html = '<strong>' + p[0] + '</strong><br><span class="pop-cat">' + p[3] + '</span>'
      + (p[4] ? '<br><a href="' + p[4] + '" target="_blank" rel="noopener">School website</a>' : '');
    L.circleMarker([p[1], p[2]], {
      radius:7, color:'#fff', weight:1.5, fillColor:p[5], fillOpacity:0.9
    }).bindPopup(html).addTo(cluster);
  });
  map.addLayer(cluster);
  new MutationObserver(function(){ layer.setUrl(tileUrl()); })
    .observe(document.documentElement, {attributes:true, attributeFilter:['data-theme']});
})();
</script>
"""


_FILTER_JS = """
<script>
(function(){
  var search = document.getElementById('sch-search');
  var btns = Array.prototype.slice.call(document.querySelectorAll('.sch-filter button'));
  var cards = Array.prototype.slice.call(document.querySelectorAll('.sch-card'));
  var level = 'all';
  function apply(){
    var q = (search.value || '').trim().toLowerCase();
    var shown = 0;
    cards.forEach(function(c){
      var okL = level === 'all' || c.getAttribute('data-level') === level;
      var okQ = !q || c.getAttribute('data-search').indexOf(q) !== -1;
      var on = okL && okQ;
      c.style.display = on ? '' : 'none';
      if (on) shown++;
    });
    document.getElementById('sch-count').textContent = shown;
  }
  btns.forEach(function(b){
    b.addEventListener('click', function(){
      btns.forEach(function(x){ x.classList.remove('is-on'); });
      b.classList.add('is-on');
      level = b.getAttribute('data-level');
      apply();
    });
  });
  search.addEventListener('input', apply);
})();
</script>
"""


_CSS = """<style>
.sch-wrap{max-width:1000px;margin:0 auto;}
.sch-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);
  max-width:64ch;margin:.4rem 0 1.2rem;}
#sch-map{height:420px;border-radius:var(--radius-sm);overflow:hidden;margin:0 0 .8rem;
  border:1px solid var(--border);}
.sch-legend{display:flex;flex-wrap:wrap;gap:14px;margin:0 0 1.4rem;
  font:var(--fs-2xs)/1 var(--font-sans);color:var(--text-secondary);}
.sch-legend span{display:inline-flex;align-items:center;gap:6px;}
.sch-legend i{width:11px;height:11px;border-radius:50%;display:inline-block;border:1px solid #fff;}
.sch-controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:0 0 1.2rem;}
#sch-search{flex:1;min-width:220px;padding:.6rem .8rem;border:1px solid var(--border);
  border-radius:var(--radius-xs);background:var(--surface-card);color:var(--text-primary);
  font:var(--fs-sm) var(--font-sans);}
.sch-filter{display:flex;flex-wrap:wrap;gap:6px;}
.sch-filter button{padding:.5rem .85rem;border:1px solid var(--border);
  background:var(--surface-card);color:var(--text-secondary);border-radius:999px;
  font:var(--fw-semibold) var(--fs-2xs) var(--font-sans);cursor:pointer;}
.sch-filter button.is-on{background:var(--accent);color:#fff;border-color:var(--accent);}
.sch-summary{font:var(--fs-2xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);
  text-transform:uppercase;color:var(--text-tertiary);margin:0 0 1rem;}
.sch-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;}
.sch-card{border:1px solid var(--border);border-radius:var(--radius-sm);padding:1rem 1.1rem;
  background:var(--surface-card);}
.sch-tag{display:inline-block;color:#fff;font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);
  letter-spacing:var(--ls-wide);text-transform:uppercase;padding:.28rem .5rem;border-radius:4px;}
.sch-name{font:var(--fw-bold) var(--fs-md)/1.2 var(--font-display);margin:.5rem 0 .35rem;}
.sch-soon{display:inline-block;font:var(--fw-bold) var(--fs-3xs) var(--font-mono);
  color:var(--accent);text-transform:uppercase;letter-spacing:var(--ls-wide);margin-bottom:.35rem;}
.sch-note{display:block;font:var(--fs-2xs)/1.4 var(--font-sans);color:var(--text-tertiary);margin-bottom:.35rem;}
.sch-addr,.sch-phone{display:block;font:var(--fs-sm)/1.45 var(--font-sans);color:var(--text-secondary);}
.sch-addr{color:var(--accent);}
.sch-facts{font:var(--fs-2xs)/1.5 var(--font-sans);color:var(--text-tertiary);margin:.4rem 0 .2rem;}
.sch-links{display:flex;flex-wrap:wrap;gap:12px;margin-top:.55rem;
  font:var(--fw-semibold) var(--fs-2xs) var(--font-sans);}
.sch-links a{color:var(--accent);}
.sch-source{margin:2rem 0 0;padding:1rem 1.1rem;border-left:3px solid var(--accent);
  background:var(--surface-card);border-radius:var(--radius-xs);
  font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);}
.sch-source a{color:var(--accent);font-weight:600;}
.leaflet-popup-content .pop-cat{font-size:.78rem;color:#5c6d75;}
@media(max-width:560px){#sch-map{height:320px;}}
</style>"""


def _map_html(schools: list[dict]) -> str:
    pts = [[s["name"], s["lat"], s["lng"], s.get("level", ""), s.get("website", ""),
            _LEVEL_COLOR.get(s.get("level", ""), "#6b6b6b")]
           for s in schools if s.get("lat") and s.get("lng")]
    if not pts:
        return ""
    return _MAP_JS.replace("__DATA__", json.dumps(pts, separators=(",", ":")))


def build_schools() -> Path:
    """Build /schools.html: map + searchable, filterable CCPS directory."""
    d = _load()
    schools = d["schools"]

    # Sort: by level order, then name.
    schools = sorted(schools, key=lambda s: (_LEVELS.index(s["level"]) if s.get("level") in _LEVELS else 99,
                                             s["name"]))
    counts = {lv: sum(1 for s in schools if s.get("level") == lv) for lv in _LEVELS}

    legend = '<div class="sch-legend">' + "".join(
        f'<span><i style="background:{_LEVEL_COLOR[lv]}"></i>{lv} ({counts[lv]})</span>'
        for lv in _LEVELS if counts[lv]) + '</div>'

    filters = '<div class="sch-filter">' + \
        '<button class="is-on" data-level="all">All</button>' + \
        "".join(f'<button data-level="{lv}">{lv}</button>' for lv in _LEVELS if counts[lv]) + \
        '</div>'

    controls = (
        '<div class="sch-controls">'
        '<input id="sch-search" type="search" placeholder="Search by school or area…" '
        'aria-label="Search schools">'
        + filters +
        '</div>'
    )

    cards = '<div class="sch-grid">' + "".join(_card(s) for s in schools) + '</div>'

    body = (
        _CSS
        + '<div class="sch-wrap">'
        + '<h1 class="page-title">Chesterfield Schools</h1>'
        + f'<p class="sch-lead">Every Chesterfield County public school: {len(schools)} '
          'elementary, middle, high, and specialty schools, with location, contact info, '
          'and links to each school’s rating and report card.</p>'
        + _map_html(schools)
        + legend
        + controls
        + '<p class="sch-summary"><span id="sch-count">' + str(len(schools)) + '</span> schools</p>'
        + cards
        + '<div class="sch-source">'
          'Roster and contact info from '
          '<a href="https://www.oneccps.org/schools" target="_blank" rel="noopener">'
          'Chesterfield County Public Schools</a>. '
          'Virginia rates schools by <strong>accreditation</strong>, not A-F letter grades; '
          'CCPS reports all of its schools accredited for the 2025-26 year. For each school’s '
          'ratings and full report card, use the GreatSchools link on its card or the state '
          '<a href="https://schoolquality.virginia.gov/" target="_blank" rel="noopener">'
          'School Quality Profiles</a>. The GreatSchools rating is a third-party measure, '
          'not an official state score. '
          'Spotted something out of date? <a href="/tip.html">Let us know.</a>'
          '</div>'
        + '</div>'
        + _FILTER_JS
    )

    page = render._shell(body)
    page = render._inject_og(
        page, "Chesterfield Schools directory",
        f"Every Chesterfield County public school ({len(schools)}) with location, contact "
        "info, and links to ratings and report cards.",
        "https://chesterfieldreport.com/schools.html")
    out = PUBLIC / "schools.html"
    out.write_text(page, encoding="utf-8")
    return out
