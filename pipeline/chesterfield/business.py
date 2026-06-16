"""Chesterfield business hub.

Builds /business.html: the county's largest employers (public VEC/economic-dev
data, by size band) plus a directory of locally-owned INDEPENDENT businesses
(discovered via OpenStreetMap, chains filtered out), with a map, and a link to
business news. Independent businesses are sorted by type; precise employee-size
tiers for small businesses are not publicly available (see the note on the page).

Data: pipeline/business_employers.json (large tier) and
pipeline/business_independent.json (independents, from the OSM search).
"""
from __future__ import annotations

import json
from pathlib import Path

from . import render
from .render import PUBLIC

EMP = Path(__file__).resolve().parents[1] / "business_employers.json"
IND = Path(__file__).resolve().parents[1] / "business_independent.json"

_BAND_ORDER = ["1000+", "500-999", "250-499", ""]
_BAND_LABEL = {"1000+": "1,000+ employees", "500-999": "500 to 999 employees",
               "250-499": "250 to 499 employees", "": "Among the 50 largest (size band not published)"}


def _load(path: Path, key: str) -> list[dict]:
    try:
        return json.loads(path.read_text()).get(key, [])
    except (OSError, json.JSONDecodeError):
        return []


def _maps_link(b: dict) -> str:
    q = b["name"] + (" " + b["street"] if b.get("street") else "") + " Chesterfield VA"
    return "https://www.google.com/maps/search/?api=1&query=" + q.replace(" ", "+")


_CSS = """<style>
.biz-wrap{max-width:880px;margin:0 auto;}
.biz-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:62ch;}
.biz-sec{margin:2.2rem 0 0;}
.biz-sec h2{font-size:1.3rem;border-bottom:1px solid var(--border-hair);padding-bottom:7px;}
.biz-sub{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);
  text-transform:uppercase;color:var(--text-secondary);margin:1.3rem 0 .5rem;}
.biz-emp{list-style:none;padding:0;margin:.4rem 0 0;display:grid;
  grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:2px 18px;}
.biz-emp li{padding:7px 0;border-bottom:1px solid var(--border-hair);font-size:.93rem;}
.biz-emp .sector{display:block;font-size:.76rem;color:var(--text-secondary);}
#biz-map{height:420px;width:100%;border:1px solid var(--border-hair);border-radius:var(--radius-sm);margin:1.1rem 0;z-index:0;background:var(--surface-card);}
.leaflet-popup-content{font-family:var(--font-sans);}
.leaflet-popup-content .biz-pop-cat{font-size:.78rem;color:#5c6d75;}
.biz-controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:1.1rem 0;}
.biz-search{flex:1 1 240px;background:var(--surface-raised);border:1px solid var(--border-hair);
  border-radius:var(--radius-xs);padding:10px 13px;color:var(--text-default);font:var(--text-body-r);}
.biz-search:focus{outline:none;border-color:var(--accent);}
.biz-jump{display:flex;flex-wrap:wrap;gap:6px;}
.biz-jump a{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:.04em;text-transform:uppercase;
  color:var(--accent);border:1px solid var(--border-hair);border-radius:var(--radius-pill);padding:6px 11px;text-decoration:none;}
.biz-jump a:hover{border-color:var(--accent);}
.biz-cat{margin:1.6rem 0 0;}
.biz-cat h3{font-size:1.05rem;display:flex;justify-content:space-between;align-items:baseline;
  border-bottom:1px solid var(--border-hair);padding-bottom:5px;}
.biz-cat h3 span{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);color:var(--text-secondary);}
.biz-list{list-style:none;padding:0;margin:.5rem 0 0;display:grid;
  grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:2px 18px;}
.biz-list li{padding:5px 0;font-size:.92rem;border-bottom:1px solid var(--border-hair);}
.biz-list a{color:var(--text-default);text-decoration:none;font-weight:500;}
.biz-list a:hover{color:var(--accent);}
.biz-list .where{display:block;font-size:.75rem;color:var(--text-secondary);}
.biz-note{font-size:.84rem;color:var(--text-secondary);margin:1.6rem 0;}
@media(max-width:560px){#biz-map{height:300px;}}
</style>"""

_MAP_JS_TMPL = """
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
<div id="biz-map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
(function(){
  if (!window.L || !document.getElementById('biz-map')) return;
  var pts = __DATA__;
  function tileUrl(){
    var light = document.documentElement.getAttribute('data-theme') === 'light';
    return light ? 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
                 : 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
  }
  var map = L.map('biz-map', {scrollWheelZoom:false}).setView([37.40,-77.58], 10);
  var layer = L.tileLayer(tileUrl(), {
    attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains:'abcd', maxZoom:19 }).addTo(map);
  var cluster = L.markerClusterGroup({maxClusterRadius:45, showCoverageOnHover:false});
  pts.forEach(function(p){
    var q = encodeURIComponent(p[0] + ' Chesterfield VA');
    L.marker([p[1], p[2]]).bindPopup('<strong>' + p[0] + '</strong><br><span class="biz-pop-cat">' + p[3]
      + '</span><br><a href="https://www.google.com/maps/search/?api=1&query=' + q + '" target="_blank" rel="noopener">Open in Maps</a>')
      .addTo(cluster);
  });
  map.addLayer(cluster);
  new MutationObserver(function(){ layer.setUrl(tileUrl()); })
    .observe(document.documentElement, {attributes:true, attributeFilter:['data-theme']});
})();
</script>"""


def build_business() -> Path:
    employers = _load(EMP, "employers")
    indep = _load(IND, "businesses")

    # ---- largest employers, grouped by size band ----
    emp_html = ['<div class="biz-sec"><h2>Largest employers</h2>'
                '<p class="biz-note" style="margin:.5rem 0 0">Chesterfield County’s biggest '
                'employers, from Virginia Employment Commission and county economic-development data. '
                'The state publishes size bands, not exact head counts.</p>']
    by_band: dict[str, list[dict]] = {}
    for e in employers:
        by_band.setdefault(e.get("band", ""), []).append(e)
    for band in _BAND_ORDER:
        items = by_band.get(band)
        if not items:
            continue
        emp_html.append(f'<div class="biz-sub">{_BAND_LABEL[band]}</div><ul class="biz-emp">')
        for e in items:
            sec = f'<span class="sector">{e["sector"]}</span>' if e.get("sector") else ""
            emp_html.append(f'<li>{e["name"]}{sec}</li>')
        emp_html.append('</ul>')
    emp_html.append('</div>')

    # ---- independent businesses: map + categorized directory ----
    cats: dict[str, list[dict]] = {}
    for b in indep:
        cats.setdefault(b["category"], []).append(b)
    cat_order = sorted(cats, key=lambda c: -len(cats[c]))
    pts = [[b["name"], b["lat"], b["lon"], b["category"]]
           for b in indep if b.get("lat") is not None and b.get("lon") is not None]
    map_html = _MAP_JS_TMPL.replace("__DATA__", json.dumps(pts, separators=(",", ":"))) if pts else ""

    jump = '<div class="biz-jump">' + "".join(
        f'<a href="#{render.slugify(c)}">{c}</a>' for c in cat_order) + '</div>'
    sections = []
    for c in cat_order:
        lis = []
        for b in sorted(cats[c], key=lambda x: x["name"].lower()):
            where = b.get("street") or b.get("city") or ""
            wl = f'<span class="where">{where}</span>' if where else ""
            lis.append(f'<li data-name="{b["name"].lower()}">'
                       f'<a href="{_maps_link(b)}" target="_blank" rel="noopener">{b["name"]}</a>{wl}</li>')
        sections.append(f'<section class="biz-cat" id="{render.slugify(c)}">'
                        f'<h3>{c} <span>{len(cats[c])}</span></h3>'
                        f'<ul class="biz-list" data-cat>{"".join(lis)}</ul></section>')

    indep_html = (
        '<div class="biz-sec"><h2>Local &amp; independent businesses</h2>'
        f'<p class="biz-note" style="margin:.5rem 0 0">{len(indep):,} independently owned Chesterfield '
        'businesses, with national chains filtered out. Tap the map or search by name; browse by type below.</p>'
        + map_html
        + '<div class="biz-controls"><input class="biz-search" id="biz-q" type="search" '
          'placeholder="Search a business by name...">' + jump + '</div>'
        + "".join(sections)
        + '</div>'
        + """<script>
(function(){
  var q=document.getElementById('biz-q');
  if(!q) return;
  var items=[].slice.call(document.querySelectorAll('.biz-list li'));
  q.addEventListener('input',function(){
    var t=(q.value||'').trim().toLowerCase();
    items.forEach(function(li){ li.style.display=(!t||li.getAttribute('data-name').indexOf(t)>-1)?'':'none'; });
  });
})();
</script>""")

    news_html = (
        '<div class="biz-sec"><h2>Business news</h2>'
        '<p>The latest on openings, closures, development and local employers across Chesterfield.</p>'
        '<p><a class="cr-btn cr-btn--primary" href="/topics/business.html">See Chesterfield business news →</a></p>'
        '</div>')

    note = (
        '<p class="biz-note">Largest-employer data is from the Virginia Employment Commission and '
        'Chesterfield Economic Development. Independent businesses are discovered from '
        '<a href="https://www.openstreetmap.org" target="_blank" rel="noopener">OpenStreetMap</a> with '
        'chains removed, so the list is broad but may be incomplete. We do not show exact employee-size '
        'tiers for small businesses because that data is not public. Own a Chesterfield business or see one '
        'we are missing? <a href="/tip.html">Let us know.</a> Listing a business is not an endorsement.</p>')

    body = (_CSS + '<div class="biz-wrap">'
            + '<h1 class="page-title">Chesterfield business</h1>'
            + f'<p class="biz-lead">The county’s largest employers, a directory of {len(indep):,} '
              'local and independent businesses, and the latest business news.</p>'
            + "".join(emp_html) + indep_html + news_html + note
            + '</div>')
    page = render._shell(body)
    page = render._inject_og(page, "Chesterfield business",
        f"Chesterfield’s largest employers and {len(indep):,} local independent businesses.",
        "https://chesterfieldreport.com/business.html")
    out = PUBLIC / "business.html"
    out.write_text(page, encoding="utf-8")
    return out
