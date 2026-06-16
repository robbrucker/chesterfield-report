"""Affordable / income-restricted housing finder -> public/affordable-housing.html.

Renders the verified income-restricted apartment communities in Chesterfield
County (data in pipeline/affordable_housing.json) as a filterable, mapped
directory. Data is sourced from the county's official Housing Assistance list,
the Better Housing Coalition, and HUD LIHTC/subsidized records; this page lists
income-restricted housing only (market-rate properties that merely accept
vouchers are excluded). Each listing links to the property and the county
resource; eligibility and waitlists must be confirmed with each property.

Stdlib only. Reuses render._shell(). A later phase adds the market-rate
community directory (build_directory).
"""
from __future__ import annotations

import html
import json
import urllib.parse
from pathlib import Path

from . import render
from .render import PUBLIC

DATA = Path(__file__).resolve().parents[1] / "affordable_housing.json"
APTS = Path(__file__).resolve().parents[1] / "apartments_data.json"
COUNTY_VOUCHERS = "https://www.chesterfield.gov/5778/Housing-Assistance"


def _load() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def _pop_bucket(pop: str) -> str:
    p = (pop or "").lower()
    has_s, has_f = "senior" in p, "family" in p
    if has_s and has_f:
        return "family senior"
    return "senior" if has_s else "family"


def _maps_link(x: dict) -> str:
    q = urllib.parse.quote(f"{x['address']} {x['city']} VA {x['zip']}")
    return f"https://www.google.com/maps/search/?api=1&query={q}"


def _card(x: dict) -> str:
    pop = x.get("population", "")
    badges = "".join(f'<span class="ah-prog">{html.escape(p)}</span>' for p in x.get("programs", []))
    facts = []
    if x.get("units"):
        facts.append(f'{x["units"]} units')
    if (x.get("ami") or "").strip():
        facts.append(html.escape(x["ami"]))
    facts_html = f'<div class="ah-facts">{" &middot; ".join(facts)}</div>' if facts else ""
    links = [f'<a href="{_maps_link(x)}" target="_blank" rel="noopener">Map ↗</a>']
    if x.get("website"):
        links.append(f'<a href="{html.escape(x["website"])}" target="_blank" rel="noopener">Website ↗</a>')
    if x.get("phone"):
        links.append(f'<a href="tel:{x["phone"].replace("-", "")}">{html.escape(x["phone"])}</a>')
    search = html.escape(f'{x["name"]} {x.get("area","")} {pop}'.lower(), quote=True)
    pop_label = f'<span class="ah-pop">{html.escape(pop)}</span>' if pop else ""
    return (
        f'<article class="ah-card" data-pop="{_pop_bucket(pop)}" data-search="{search}">'
        f'<div class="ah-head"><span class="ah-area">{html.escape(x.get("area",""))}</span>{pop_label}</div>'
        f'<h3 class="ah-name">{html.escape(x["name"])}</h3>'
        f'<div class="ah-addr">{html.escape(x["address"]) }, {html.escape(x["city"])}</div>'
        f'<div class="ah-progs">{badges}</div>'
        f'{facts_html}'
        f'<div class="ah-links">{" &middot; ".join(links)}</div>'
        '</article>'
    )


_CSS = """<style>
.ah-wrap{max-width:1000px;margin:0 auto;}
.ah-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:64ch;margin:.4rem 0 1.1rem;}
#ah-map{height:380px;border-radius:var(--radius-sm);overflow:hidden;border:1px solid var(--border);margin:0 0 1.2rem;}
.ah-filter{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 1.2rem;}
.ah-filter button{padding:.5rem .85rem;border:1px solid var(--border);background:var(--surface-card);color:var(--text-secondary);
  border-radius:999px;font:var(--fw-semibold) var(--fs-2xs) var(--font-sans);cursor:pointer;}
.ah-filter button.is-on{background:var(--accent);color:#fff;border-color:var(--accent);}
.ah-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;}
.ah-card{border:1px solid var(--border);border-radius:var(--radius-sm);padding:1rem 1.1rem;background:var(--surface-card);}
.ah-head{display:flex;justify-content:space-between;gap:8px;align-items:center;}
.ah-area{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);}
.ah-pop{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);text-transform:uppercase;letter-spacing:var(--ls-wide);
  color:#fff;background:var(--accent);border-radius:4px;padding:.22rem .5rem;}
.ah-name{font:var(--fw-bold) var(--fs-md)/1.2 var(--font-display);margin:.45rem 0 .15rem;}
.ah-addr{font:var(--fs-2xs)/1.4 var(--font-sans);color:var(--text-tertiary);margin-bottom:.5rem;}
.ah-progs{display:flex;flex-wrap:wrap;gap:5px;margin:.3rem 0;}
.ah-prog{font:var(--fw-semibold) var(--fs-3xs)/1.3 var(--font-sans);color:var(--text-secondary);
  border:1px solid var(--border);border-radius:4px;padding:.2rem .45rem;}
.ah-facts{font:var(--fs-2xs)/1.4 var(--font-sans);color:var(--text-secondary);margin:.4rem 0 .2rem;}
.ah-links{display:flex;flex-wrap:wrap;gap:12px;margin-top:.5rem;font:var(--fw-semibold) var(--fs-2xs) var(--font-sans);}
.ah-links a{color:var(--accent);}
.ah-summary{font:var(--fs-2xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);margin:0 0 1rem;}
.ah-src{margin-top:2rem;padding:1rem 1.1rem;border-left:3px solid var(--accent);background:var(--surface-card);
  border-radius:var(--radius-xs);font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);}
.ah-src a{color:var(--accent);font-weight:600;}
@media(max-width:560px){#ah-map{height:300px;}}
</style>"""

_MAP_JS = """
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
<div id="ah-map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
(function(){
  if(!window.L) return;
  var pts=__DATA__;
  function tile(){var l=document.documentElement.getAttribute('data-theme')==='light';
    return l?'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png':'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';}
  var map=L.map('ah-map',{scrollWheelZoom:false}).setView([37.41,-77.54],11);
  var layer=L.tileLayer(tile(),{attribution:'&copy; OpenStreetMap &copy; CARTO',subdomains:'abcd',maxZoom:19}).addTo(map);
  var cl=L.markerClusterGroup({maxClusterRadius:35,showCoverageOnHover:false});
  pts.forEach(function(p){
    L.circleMarker([p[1],p[2]],{radius:8,color:'#fff',weight:1.5,fillColor:'#9a3322',fillOpacity:.9})
      .bindPopup('<strong>'+p[0]+'</strong><br>'+p[3]).addTo(cl);
  });
  map.addLayer(cl);
  new MutationObserver(function(){layer.setUrl(tile());}).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
})();
</script>
"""

_FILTER_JS = """
<script>
(function(){
  var btns=[].slice.call(document.querySelectorAll('.ah-filter button')),
      cards=[].slice.call(document.querySelectorAll('.ah-card')),pop='all';
  function apply(){var n=0;cards.forEach(function(c){
    var on=pop==='all'||c.getAttribute('data-pop').indexOf(pop)!==-1;c.style.display=on?'':'none';if(on)n++;});
    document.getElementById('ah-count').textContent=n;}
  btns.forEach(function(b){b.addEventListener('click',function(){btns.forEach(function(x){x.classList.remove('is-on');});
    b.classList.add('is-on');pop=b.getAttribute('data-pop');apply();});});
})();
</script>
"""


def build_affordable() -> Path:
    d = _load()
    props = d["properties"]
    pts = [[p["name"], p["lat"], p["lng"], html.escape(p.get("area", ""))]
           for p in props if p.get("lat") and p.get("lng")]
    map_html = _MAP_JS.replace("__DATA__", json.dumps(pts, separators=(",", ":"))) if pts else ""

    filters = ('<div class="ah-filter">'
               '<button class="is-on" data-pop="all">All</button>'
               '<button data-pop="family">Family</button>'
               '<button data-pop="senior">Senior</button>'
               '</div>')
    cards = "".join(_card(p) for p in props)

    body = (
        _CSS
        + '<div class="ah-wrap">'
        + '<h1 class="page-title">Affordable Housing</h1>'
        + '<p class="ah-lead">Income-restricted apartment communities in Chesterfield County, where '
          'rent is capped or based on income. Most use the federal Low-Income Housing Tax Credit (LIHTC) '
          'or HUD subsidies, and many serve families or seniors specifically. Income limits, eligibility, '
          'and waitlists vary by property, so confirm directly with each one.</p>'
        + map_html
        + filters
        + f'<p class="ah-summary"><span id="ah-count">{len(props)}</span> communities</p>'
        + f'<div class="ah-grid">{cards}</div>'
        + '<div class="ah-src">This list covers <strong>income-restricted</strong> housing, verified '
          'against the county’s '
          f'<a href="{COUNTY_VOUCHERS}" target="_blank" rel="noopener">Housing Assistance</a> resources, '
          'the Better Housing Coalition, and HUD records. It is not exhaustive, and eligibility, rents, and '
          'waitlists change, so always confirm with the property. Many market-rate communities also accept '
          'Housing Choice (Section 8) vouchers; the county keeps that list on the same page. '
          'Spotted something to add or fix? <a href="/tip.html">Let us know.</a></div>'
        + '</div>'
        + _FILTER_JS
    )
    page = render._shell(body)
    page = render._inject_og(
        page, "Affordable Housing in Chesterfield County",
        f"{len(props)} income-restricted apartment communities in Chesterfield County, mapped, with "
        "program, contact, and eligibility info.",
        "https://chesterfieldreport.com/affordable-housing.html")
    out = PUBLIC / "affordable-housing.html"
    out.write_text(page, encoding="utf-8")
    return out


# --------------------------------------------------------------------------- #
# Market-rate apartment community directory
# --------------------------------------------------------------------------- #

_DIR_CSS = """<style>
#hd-map{height:400px;border-radius:var(--radius-sm);overflow:hidden;border:1px solid var(--border);margin:0 0 1.2rem;}
.hd-controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:0 0 .7rem;}
#hd-search{flex:1;min-width:220px;padding:.6rem .8rem;border:1px solid var(--border);border-radius:var(--radius-xs);
  background:var(--surface-card);color:var(--text-primary);font:var(--fs-sm) var(--font-sans);}
.hd-filters{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 1.2rem;}
.hd-filters button{padding:.45rem .8rem;border:1px solid var(--border);background:var(--surface-card);color:var(--text-secondary);
  border-radius:999px;font:var(--fw-semibold) var(--fs-3xs) var(--font-sans);cursor:pointer;}
.hd-filters button.is-on{background:var(--accent);color:#fff;border-color:var(--accent);}
.hd-flabel{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);text-transform:uppercase;letter-spacing:var(--ls-wide);
  color:var(--text-tertiary);margin-right:4px;align-self:center;}
.ah-kind{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);text-transform:uppercase;letter-spacing:var(--ls-wide);
  color:#fff;border-radius:4px;padding:.22rem .5rem;}
.ah-kind.luxury{background:#9a3322;}.ah-kind.market{background:#2f7d8f;}
.ah-beds{font:var(--fw-semibold) var(--fs-2xs)/1.3 var(--font-sans);color:var(--text-secondary);margin:.4rem 0 .2rem;}
.ah-feats{display:flex;flex-wrap:wrap;gap:5px;margin:.35rem 0 .1rem;}
.ah-feat{font:var(--fw-semibold) var(--fs-3xs)/1.3 var(--font-sans);color:var(--text-secondary);
  border:1px solid var(--border);border-radius:4px;padding:.18rem .42rem;}
@media(max-width:560px){#hd-map{height:300px;}}
</style>"""


def _region(city: str) -> str:
    c = (city or "").strip()
    return c if c in ("Midlothian", "North Chesterfield", "Chester", "Moseley") else "Other"


_FEATURES = [("pet", "Pet-friendly"), ("pool", "Pool"), ("fitness", "Fitness center"),
             ("laundry", "In-unit W/D")]
_BEDS = ["Studio", "1 BR", "2 BR", "3 BR"]


def _bedkey(b: str) -> str:
    return b.lower().replace(" ", "")


def _dir_card(x: dict) -> str:
    kind = "luxury" if x.get("kind") == "luxury" else "market"
    klabel = "Luxury" if kind == "luxury" else "Market-rate"
    facts = []
    if x.get("units"):
        facts.append(f'{x["units"]} units')
    if x.get("year"):
        facts.append(f'built {x["year"]}')
    if (x.get("manager") or "").strip():
        facts.append(html.escape(x["manager"]))
    facts_html = f'<div class="ah-facts">{" &middot; ".join(facts)}</div>' if facts else ""

    beds = [b for b in (x.get("beds") or []) if b in _BEDS]
    beds_html = (f'<div class="ah-beds">{html.escape(" · ".join(beds))}</div>' if beds else "")
    feats = [lab for key, lab in _FEATURES if x.get(key)]
    am = (x.get("amenities") or [])[:5]
    chips = feats + [a for a in am if a not in feats]
    amen_html = ('<div class="ah-feats">' + "".join(f'<span class="ah-feat">{html.escape(c)}</span>'
                 for c in chips[:6]) + '</div>') if chips else ""

    links = [f'<a href="{_maps_link(x)}" target="_blank" rel="noopener">Map ↗</a>']
    if x.get("website"):
        links.append(f'<a href="{html.escape(x["website"])}" target="_blank" rel="noopener">Website ↗</a>')
    if x.get("phone"):
        links.append(f'<a href="tel:{x["phone"].replace("(","").replace(")","").replace(" ","").replace("-","")}">{html.escape(x["phone"])}</a>')
    search = html.escape(f'{x["name"]} {x.get("area","")} {x.get("manager","")}'.lower(), quote=True)
    dattr = (f'data-region="{html.escape(_region(x["city"]))}" data-kind="{kind}" '
             f'data-pet="{int(bool(x.get("pet")))}" data-pool="{int(bool(x.get("pool")))}" '
             f'data-fitness="{int(bool(x.get("fitness")))}" data-laundry="{int(bool(x.get("laundry")))}" '
             f'data-beds="{html.escape(" ".join(_bedkey(b) for b in beds))}" data-search="{search}"')
    return (
        f'<article class="ah-card" {dattr}>'
        f'<div class="ah-head"><span class="ah-area">{html.escape(x.get("area",""))}</span>'
        f'<span class="ah-kind {kind}">{klabel}</span></div>'
        f'<h3 class="ah-name">{html.escape(x["name"])}</h3>'
        f'<div class="ah-addr">{html.escape(x["address"])}, {html.escape(x["city"])}</div>'
        f'{beds_html}{facts_html}{amen_html}'
        f'<div class="ah-links">{" &middot; ".join(links)}</div>'
        '</article>'
    )


_DIR_JS = """
<script>
(function(){
  var s=document.getElementById('hd-search'),
      cards=[].slice.call(document.querySelectorAll('.ah-card')),
      region='all',kind='all',bed='all',feats={};
  function single(sel,set){[].slice.call(document.querySelectorAll(sel+' button')).forEach(function(b){
    b.addEventListener('click',function(){
      [].slice.call(document.querySelectorAll(sel+' button')).forEach(function(x){x.classList.remove('is-on');});
      b.classList.add('is-on');set(b);apply();});});}
  single('.hd-region',function(b){region=b.getAttribute('data-region');});
  single('.hd-kind',function(b){kind=b.getAttribute('data-kind');});
  single('.hd-bed',function(b){bed=b.getAttribute('data-bed');});
  [].slice.call(document.querySelectorAll('.hd-feat button')).forEach(function(b){
    b.addEventListener('click',function(){var f=b.getAttribute('data-feat');
      if(feats[f]){delete feats[f];b.classList.remove('is-on');}else{feats[f]=1;b.classList.add('is-on');}apply();});});
  if(s) s.addEventListener('input',apply);
  function apply(){var q=(s&&s.value||'').trim().toLowerCase(),n=0;
    cards.forEach(function(c){
      var on = (region==='all'||c.getAttribute('data-region')===region)
            && (kind==='all'||c.getAttribute('data-kind')===kind)
            && (bed==='all'||(' '+c.getAttribute('data-beds')+' ').indexOf(' '+bed+' ')!==-1)
            && (!q||c.getAttribute('data-search').indexOf(q)!==-1);
      for(var f in feats){ if(c.getAttribute('data-'+f)!=='1'){on=false;break;} }
      c.style.display=on?'':'none';if(on)n++;});
    document.getElementById('hd-count').textContent=n;}
})();
</script>
"""


def build_directory() -> Path:
    d = json.loads(APTS.read_text(encoding="utf-8"))
    comms = sorted(d["communities"], key=lambda c: (_region(c["city"]), c["name"]))
    pts = [[c["name"], c["lat"], c["lng"], html.escape(c.get("area", ""))]
           for c in comms if c.get("lat") and c.get("lng")]
    map_html = (_MAP_JS.replace("ah-map", "hd-map").replace("__DATA__", json.dumps(pts, separators=(",", ":")))
                if pts else "")

    regions = ["Midlothian", "North Chesterfield", "Chester", "Moseley", "Other"]
    present = [r for r in regions if any(_region(c["city"]) == r for c in comms)]
    region_btns = ('<div class="hd-filters hd-region"><span class="hd-flabel">Area</span>'
                   '<button class="is-on" data-region="all">All</button>'
                   + "".join(f'<button data-region="{r}">{html.escape(r)}</button>' for r in present)
                   + '</div>')
    kind_btns = ('<div class="hd-filters hd-kind"><span class="hd-flabel">Type</span>'
                 '<button class="is-on" data-kind="all">All</button>'
                 '<button data-kind="luxury">Luxury</button>'
                 '<button data-kind="market">Market-rate</button></div>')
    # Bed + feature filters only render for the values we actually have data on.
    have_beds = any(c.get("beds") for c in comms)
    bed_btns = ""
    if have_beds:
        bed_btns = ('<div class="hd-filters hd-bed"><span class="hd-flabel">Beds</span>'
                    '<button class="is-on" data-bed="all">Any</button>'
                    + "".join(f'<button data-bed="{_bedkey(b)}">{html.escape(b)}</button>' for b in _BEDS)
                    + '</div>')
    feat_present = [(k, lab) for k, lab in _FEATURES if any(c.get(k) for c in comms)]
    feat_btns = ""
    if feat_present:
        feat_btns = ('<div class="hd-filters hd-feat"><span class="hd-flabel">Features</span>'
                     + "".join(f'<button data-feat="{k}">{html.escape(lab)}</button>' for k, lab in feat_present)
                     + '</div>')
    cards = "".join(_dir_card(c) for c in comms)

    body = (
        _CSS + _DIR_CSS
        + '<div class="ah-wrap">'
        + '<h1 class="page-title">Apartment Communities</h1>'
        + f'<p class="ah-lead">A directory of {len(comms)} market-rate and luxury apartment communities '
          'across Chesterfield County, by area. Each links to the community’s own site for current floor '
          'plans, amenities, and pricing. Looking for income-restricted options? See '
          '<a href="/affordable-housing.html" style="color:var(--accent);font-weight:600;">affordable housing</a>.</p>'
        + map_html
        + '<div class="hd-controls"><input id="hd-search" type="search" '
          'placeholder="Search by name, area, or manager…" aria-label="Search apartments"></div>'
        + region_btns + kind_btns + bed_btns + feat_btns
        + f'<p class="ah-summary"><span id="hd-count">{len(comms)}</span> communities</p>'
        + f'<div class="ah-grid">{cards}</div>'
        + '<div class="ah-src">This directory lists market-rate communities in Chesterfield County '
          '(it excludes Richmond city and income-restricted housing, which has its own page). Rents, '
          'availability, and amenities change constantly and live on each community’s own site, so always '
          'check there. Run a community we missed or got wrong? <a href="/tip.html">Let us know.</a></div>'
        + '</div>'
        + _DIR_JS
    )
    page = render._shell(body)
    page = render._inject_og(
        page, "Chesterfield Apartment Communities",
        f"A directory of {len(comms)} market-rate apartment communities in Chesterfield County, by area, "
        "mapped, each linking to current pricing and floor plans.",
        "https://chesterfieldreport.com/apartments.html")
    out = PUBLIC / "apartments.html"
    out.write_text(page, encoding="utf-8")
    return out
