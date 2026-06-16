"""Chesterfield neighborhoods directory.

Builds /neighborhoods.html (an index of residential neighborhoods with home
counts and HOA flags) plus a per-neighborhood page at /neighborhoods/<slug>.html.
This is a standalone reference section; neighborhood content does NOT appear in
the main news feed.

Data: pipeline/neighborhoods_data.json — home counts from the county's public
ArcGIS parcel layer, HOA flags matched to the VA DPOR Common Interest Community
registry. Home counts can be refreshed weekly from the county GIS (refresh()).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from . import render
from .render import PUBLIC

DATA = Path(__file__).resolve().parents[1] / "neighborhoods_data.json"
THRESHOLD = 50   # only list neighborhoods with at least this many homes
OUT_DIR = PUBLIC / "neighborhoods"

# County GIS parcel layer (public, no key) for the weekly home-count refresh.
_PARCELS = ("https://services3.arcgis.com/TsynfzBSE6sXfoLq/arcgis/rest/services/"
            "Cadastral_ProdA/FeatureServer/3/query")

BOUNDARIES = PUBLIC / "assets" / "neighborhood-boundaries.geojson"
WIKI = Path(__file__).resolve().parents[1] / "neighborhoods_wiki.json"


def _load_boundaries() -> dict:
    """slug -> the neighborhood's GeoJSON feature (for the per-page location map)."""
    try:
        gj = json.loads(BOUNDARIES.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return {f["properties"]["slug"]: f for f in gj.get("features", [])
            if f.get("properties", {}).get("slug")}


def _load_wiki() -> dict:
    """UPPERCASE name -> {title, extract, url} for neighborhoods with a verified
    Wikipedia article (most have none)."""
    try:
        return json.loads(WIKI.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


# Per-page location map: a single neighborhood's boundary on a small Leaflet map.
# Plain string (not .format'd); __FEAT__ is replaced with the feature JSON.
_LOC_MAP = """
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<div id="loc-map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
(function(){
  if (!window.L || !document.getElementById('loc-map')) return;
  var feat = __FEAT__;
  function tileUrl(){
    var light = document.documentElement.getAttribute('data-theme') === 'light';
    return light ? 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
                 : 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
  }
  var map = L.map('loc-map', {scrollWheelZoom:false});
  var layer = L.tileLayer(tileUrl(), {
    attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains:'abcd', maxZoom:18 }).addTo(map);
  var gl = L.geoJSON(feat, {style:{color:'#0a8f7e', weight:2, fillColor:'#12b39c', fillOpacity:.22}}).addTo(map);
  try { map.fitBounds(gl.getBounds(), {padding:[24,24]}); } catch(e){ map.setView([37.40,-77.58], 11); }
  new MutationObserver(function(){ layer.setUrl(tileUrl()); })
    .observe(document.documentElement, {attributes:true, attributeFilter:['data-theme']});
})();
</script>"""


def _load() -> list[dict]:
    try:
        return json.loads(DATA.read_text()).get("neighborhoods", [])
    except (OSError, json.JSONDecodeError):
        return []


def _slug(name: str) -> str:
    return render.slugify(name)


def refresh(apply: bool = True) -> int:
    """Re-pull residential home counts per subdivision from the county GIS and
    update DATA in place (HOA flags are preserved). Returns the count updated."""
    import urllib.parse, urllib.request
    counts: dict[str, int] = {}
    offset = 0
    ua = {"User-Agent": "ChesterfieldReport/1.0 (brucker.rob@gmail.com)"}
    while True:
        params = urllib.parse.urlencode({
            "where": "UseCode IN ('SD','TH','CD','DU') AND ParcelType NOT IN ('CommonArea','OpenSpace')",
            "groupByFieldsForStatistics": "SubdivisionName",
            "outStatistics": json.dumps([{"statisticType": "count",
                "onStatisticField": "SubdivisionName", "outStatisticFieldName": "n"}]),
            "resultOffset": offset, "resultRecordCount": 1000, "f": "json"})
        try:
            req = urllib.request.Request(f"{_PARCELS}?{params}", headers=ua)
            with urllib.request.urlopen(req, timeout=40) as r:
                feats = json.loads(r.read()).get("features", [])
        except Exception as e:
            print(f"  ! neighborhoods refresh failed at offset {offset}: {e}")
            return 0
        if not feats:
            break
        for f in feats:
            a = f.get("attributes", {})
            nm = (a.get("SubdivisionName") or "").strip()
            if nm and nm != "ACREAGE PARCEL":
                counts[nm] = a.get("n", 0)
        offset += 1000
    if not counts or not apply:
        return len(counts)
    blob = json.loads(DATA.read_text())
    seen = {n["name"] for n in blob["neighborhoods"]}
    for n in blob["neighborhoods"]:
        if n["name"] in counts:
            n["homes"] = counts[n["name"]]
    # add any newly-appeared subdivisions (>=10 homes), no HOA flag yet
    for nm, c in counts.items():
        if nm not in seen and c >= 10:
            blob["neighborhoods"].append({"name": nm, "homes": c, "hoa": False, "hoa_name": None})
    blob["neighborhoods"].sort(key=lambda x: -x["homes"])
    DATA.write_text(json.dumps(blob, indent=0))
    return len(counts)


_CSS = """<style>
.nb-wrap{max-width:860px;margin:0 auto;}
.nb-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:62ch;}
.nb-controls{display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin:1.3rem 0;}
.nb-search{flex:1 1 240px;background:var(--surface-raised);border:1px solid var(--border-hair);
  border-radius:var(--radius-xs);padding:10px 13px;color:var(--text-default);font:var(--text-body-r);}
.nb-search:focus{outline:none;border-color:var(--accent);}
.nb-toggle{display:inline-flex;align-items:center;gap:7px;font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);
  letter-spacing:.04em;text-transform:uppercase;color:var(--text-secondary);cursor:pointer;
  border:1px solid var(--border-hair);border-radius:var(--radius-pill);padding:8px 13px;background:none;}
.nb-toggle.on{color:var(--accent);border-color:var(--accent);}
.nb-count{font:var(--fs-3xs)/1 var(--font-mono);color:var(--text-secondary);}
.nb-list{list-style:none;padding:0;margin:1rem 0 0;
  display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:2px 18px;}
.nb-list li{padding:8px 0;border-bottom:1px solid var(--border-hair);display:flex;
  align-items:baseline;justify-content:space-between;gap:10px;}
.nb-list a{color:var(--text-default);text-decoration:none;font-weight:500;}
.nb-list a:hover{color:var(--accent);}
.nb-homes{font:var(--fs-3xs)/1 var(--font-mono);color:var(--text-secondary);white-space:nowrap;}
.nb-hoa{display:inline-block;font:var(--fw-bold) 9px/1 var(--font-mono);letter-spacing:.06em;
  color:var(--text-on-neon);background:var(--accent);border-radius:3px;padding:3px 5px;margin-left:7px;vertical-align:middle;}
.nb-comm{display:inline-block;font:var(--fw-bold) 9px/1 var(--font-mono);letter-spacing:.06em;
  color:var(--text-on-neon);background:var(--civic);border-radius:3px;padding:3px 5px;margin-left:6px;vertical-align:middle;}
.nb-kick{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wider);
  text-transform:uppercase;color:var(--civic);margin-bottom:6px;}
#loc-map{height:320px;width:100%;border:1px solid var(--border-hair);border-radius:var(--radius-sm);
  margin:1.3rem 0;z-index:0;background:var(--surface-card);}
.nb-wiki{border-left:3px solid var(--accent);background:var(--surface-card);padding:.9rem 1.15rem;
  border-radius:var(--radius-xs);margin:1.3rem 0;}
.nb-wiki p{margin:0;color:var(--text-default);font-size:.96rem;line-height:1.55;}
.nb-wiki .nb-wiki-src{font:var(--fs-3xs)/1 var(--font-mono);color:var(--text-secondary);margin-top:8px;text-transform:uppercase;letter-spacing:.05em;}
.nb-note{font-size:.83rem;color:var(--text-secondary);margin:1.6rem 0;}
/* per-neighborhood page */
.nb-stat{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:1.4rem 0;}
.nb-stat div{background:var(--surface-card);border:1px solid var(--border-hair);border-radius:var(--radius-sm);padding:1rem 1.1rem;}
.nb-stat b{display:block;font:var(--fw-bold) var(--fs-2xl)/1 var(--font-display);color:var(--accent);margin-bottom:6px;}
.nb-stat span{font-size:.82rem;color:var(--text-secondary);}
.nb-back{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);text-transform:uppercase;letter-spacing:.06em;color:var(--accent);text-decoration:none;}
#nb-map{height:460px;width:100%;border:1px solid var(--border-hair);border-radius:var(--radius-sm);margin:1.3rem 0;z-index:0;background:var(--surface-card);}
#nb-map .leaflet-interactive{cursor:pointer;}
.nb-maphint{font:var(--fs-3xs)/1.4 var(--font-mono);color:var(--text-secondary);text-transform:uppercase;letter-spacing:.05em;margin:-.6rem 0 0;}
@media(max-width:560px){#nb-map{height:320px;}}
.leaflet-popup-content{font-family:var(--font-sans);margin:.7rem .95rem;}
.leaflet-popup-content .nb-pop-sub{font-size:.8rem;color:#5c6d75;}
.leaflet-popup-content .nb-pop-link{display:inline-block;margin-top:6px;font-weight:600;color:#0a8f7e;text-decoration:none;}
.leaflet-popup-content .nb-pop-link:hover{text-decoration:underline;}
</style>"""


# Interactive boundary map (Leaflet). Plain string (not .format'd); _shell inserts
# the body verbatim, so raw JS braces are fine. Loads the prebaked GeoJSON and
# makes each neighborhood polygon clickable -> its page.
_MAP_JS = """
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<div id="nb-map"></div>
<p class="nb-maphint">Tap a neighborhood on the map to open its page. Shaded = registered HOA.</p>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
(function(){
  if (!window.L || !document.getElementById('nb-map')) return;
  function tileUrl(){
    var light = document.documentElement.getAttribute('data-theme') === 'light';
    return light ? 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
                 : 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
  }
  function titleCase(s){ return s.toLowerCase().replace(/\\b\\w/g, function(c){ return c.toUpperCase(); }); }
  var map = L.map('nb-map', {scrollWheelZoom:false}).setView([37.40,-77.58], 10);
  var layer = L.tileLayer(tileUrl(), {
    attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains:'abcd', maxZoom:18 }).addTo(map);
  function baseStyle(f){ var h=f.properties.hoa;
    return { color: h?'#0a8f7e':'#6f8aa0', weight:1, opacity:.8,
             fillColor: h?'#12b39c':'#7f9bb3', fillOpacity: h?0.30:0.10 }; }
  var selected = null;
  fetch('/assets/neighborhood-boundaries.geojson').then(function(r){ return r.json(); }).then(function(gj){
    var gl = L.geoJSON(gj, {
      style: baseStyle,
      onEachFeature: function(f, lyr){
        var p = f.properties, nm = titleCase(p.name);
        lyr.bindTooltip(nm, {sticky:true});
        // Click SELECTS the neighborhood: keeps it highlighted and shows a popup
        // with a link, until another section is clicked.
        lyr.bindPopup(
          '<strong>' + nm + '</strong><br>'
          + '<span class="nb-pop-sub">' + (p.homes||0).toLocaleString() + ' homes'
          + (p.hoa ? ' &middot; Registered HOA' : '') + '</span><br>'
          + '<a class="nb-pop-link" href="/neighborhoods/' + p.slug + '.html">View ' + nm + ' &rarr;</a>',
          {autoPan: true, closeButton: true});
        lyr.on('mouseover', function(){ if (this !== selected) this.setStyle({fillOpacity:.45, weight:2}); });
        lyr.on('mouseout', function(){ if (this !== selected) gl.resetStyle(this); });
        lyr.on('click', function(){
          if (selected && selected !== this) gl.resetStyle(selected);
          selected = this;
          this.setStyle({color:'#0a8f7e', weight:3, fillColor:'#12b39c', fillOpacity:.55});
        });
      }
    }).addTo(map);
    map.on('popupclose', function(){ if (selected){ gl.resetStyle(selected); selected = null; } });
    try { map.fitBounds(gl.getBounds(), {padding:[12,12]}); } catch(e){}
  }).catch(function(){});
  new MutationObserver(function(){ layer.setUrl(tileUrl()); })
    .observe(document.documentElement, {attributes:true, attributeFilter:['data-theme']});
})();
</script>"""


def _title(name: str) -> str:
    # county data is uppercase; title-case for display, keep small joiner words lower
    small = {"at", "of", "the", "on", "by"}
    out = []
    for i, w in enumerate(name.lower().split()):
        out.append(w if (w in small and i) else (w[:1].upper() + w[1:]))
    return " ".join(out)


def build_neighborhoods() -> Path:
    rows = sorted((n for n in _load() if n.get("homes", 0) >= THRESHOLD),
                  key=lambda x: x["name"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    n_hoa = sum(1 for r in rows if r.get("hoa"))

    # ---- index ----
    items = []
    for r in rows:
        nm = _title(r["name"])
        slug = _slug(r["name"])
        hoa = ' <span class="nb-hoa">HOA</span>' if r.get("hoa") else ""
        comm = ' <span class="nb-comm">COMMUNITY</span>' if r.get("type") == "community" else ""
        items.append(
            f'<li data-hoa="{1 if r.get("hoa") else 0}" data-name="{nm.lower()}">'
            f'<span><a href="/neighborhoods/{slug}.html">{nm}</a>{comm}{hoa}</span>'
            f'<span class="nb-homes">{r["homes"]:,} homes</span></li>')
    body = (
        _CSS
        + '<div class="nb-wrap">'
        + '<h1 class="page-title">Chesterfield neighborhoods</h1>'
        + f'<p class="nb-lead">{len(rows):,} residential neighborhoods across Chesterfield County '
          f'with 50 or more homes. {n_hoa} have a state-registered homeowners association. '
          'Home counts come from county parcel records.</p>'
        + _MAP_JS
        + '<div class="nb-controls">'
          '<input class="nb-search" id="nb-q" type="search" placeholder="Search a neighborhood...">'
          '<button class="nb-toggle" id="nb-hoa-only" type="button">HOA only</button>'
          f'<span class="nb-count" id="nb-count">{len(rows):,} shown</span>'
          '</div>'
        + f'<ul class="nb-list" id="nb-list">{"".join(items)}</ul>'
        + '<p class="nb-note">Home counts are residential parcels from '
          '<a href="https://opengisdata.chesterfield.gov/" target="_blank" rel="noopener">Chesterfield County GIS</a>, '
          'refreshed weekly. The HOA tag means a homeowners association registered with the '
          'Virginia DPOR Common Interest Community Board was matched to the neighborhood; no tag '
          'does not guarantee there is no HOA. Spotted something off? <a href="/tip.html">Tell us.</a></p>'
        + '</div>'
        + """<script>
(function(){
  var q=document.getElementById('nb-q'),btn=document.getElementById('nb-hoa-only'),
      cnt=document.getElementById('nb-count'),
      items=[].slice.call(document.querySelectorAll('#nb-list li'));
  var hoaOnly=false;
  function apply(){
    var t=(q.value||'').trim().toLowerCase(),shown=0;
    items.forEach(function(li){
      var ok=(!t||li.getAttribute('data-name').indexOf(t)>-1)&&(!hoaOnly||li.getAttribute('data-hoa')==='1');
      li.style.display=ok?'':'none'; if(ok)shown++;
    });
    cnt.textContent=shown.toLocaleString()+' shown';
  }
  q.addEventListener('input',apply);
  btn.addEventListener('click',function(){hoaOnly=!hoaOnly;btn.classList.toggle('on',hoaOnly);apply();});
})();
</script>""")
    page = render._shell(body)
    page = render._inject_og(page, "Chesterfield neighborhoods directory",
        f"{len(rows):,} Chesterfield County neighborhoods with home counts and HOA info.",
        "https://chesterfieldreport.com/neighborhoods.html")
    out = PUBLIC / "neighborhoods.html"
    out.write_text(page, encoding="utf-8")

    # ---- per-neighborhood pages ----
    bounds = _load_boundaries()
    wiki = _load_wiki()
    for r in rows:
        nm = _title(r["name"])
        slug = _slug(r["name"])
        hoa_block = (
            f'<div><b>Yes</b><span>Registered HOA<br>{r["hoa_name"]}</span></div>'
            if r.get("hoa") else
            '<div><b>—</b><span>No registered HOA matched<br>(not a guarantee there is none)</span></div>')
        feat = bounds.get(slug)
        loc_map = _LOC_MAP.replace("__FEAT__", json.dumps(feat, separators=(",", ":"))) if feat else ""
        w = wiki.get(r["name"])
        blurb = (f'<div class="nb-wiki"><p>{w["extract"]}</p>'
                 f'<p class="nb-wiki-src">From <a href="{w["url"]}" target="_blank" rel="noopener">'
                 f'Wikipedia</a></p></div>') if w and w.get("extract") else ""
        nbody = (
            _CSS
            + '<div class="nb-wrap">'
            + '<a class="nb-back" href="/neighborhoods.html">&larr; All neighborhoods</a>'
            + ('<div class="nb-kick" style="margin-top:.7rem">Master-planned community</div>'
               if r.get("type") == "community" else "")
            + f'<h1 class="page-title" style="margin-top:.3rem">{nm}</h1>'
            + '<div class="nb-stat">'
            + f'<div><b>{r["homes"]:,}</b><span>homes</span></div>'
            + hoa_block
            + '</div>'
            + blurb
            + loc_map
            + '<p class="nb-note">Home count is residential parcels from Chesterfield County GIS, '
              'refreshed weekly. Coming soon: HOA meeting notices and homes for sale. '
              'Are you on this neighborhood’s HOA board? '
              '<a href="/tip.html">Send us your meeting info and updates.</a></p>'
            + '</div>')
        npage = render._shell(nbody)
        npage = render._inject_og(npage, f"{nm} — Chesterfield neighborhood",
            f"{nm}: {r['homes']:,} homes" + (", registered HOA" if r.get("hoa") else "") + ".",
            f"https://chesterfieldreport.com/neighborhoods/{slug}.html")
        (OUT_DIR / f"{slug}.html").write_text(npage, encoding="utf-8")

    return out
