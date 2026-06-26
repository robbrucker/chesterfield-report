"""Places of Worship: a faith-filtered map of congregations in and serving
Chesterfield County, across ALL faiths.

Builds public/places-of-worship.html from pipeline/worship_data.json, a merged
dataset of OpenStreetMap records (all tagged Christian) plus a hand-verified
supplement of non-Christian, LDS, Orthodox, and Unitarian Universalist
congregations. Markers are colored by faith with a legend and a clickable faith
filter; adjacent (in_county=false) sites are drawn hollow and labeled.

Leaflet + CARTO (theme-aware) map, same stack as safety.py. Vanilla filter JS,
no extra libraries. Stdlib only; reuses render._shell() / _inject_og.
"""
from __future__ import annotations

import html
import json
import json as _json
import os
from collections import Counter
from pathlib import Path

from . import render
from .render import PUBLIC

DATA = Path(__file__).resolve().parents[1] / "worship_data.json"

# The seven faith groups, in display order, each with a distinct, accessible
# color. These are deliberately separable hues, not a single accent ramp, so no
# faith is visually privileged over another.
FAITHS = [
    ("Christian", "#3b6fb0"),
    ("Muslim", "#1f9e6e"),
    ("Jewish", "#7c5cc4"),
    ("Hindu", "#e07b39"),
    ("Buddhist", "#d4a017"),
    ("Sikh", "#c0392b"),
    ("Other", "#6b7280"),
]
FAITH_COLOR = dict(FAITHS)


def _load() -> list:
    return json.loads(DATA.read_text(encoding="utf-8"))


_MAP_HEAD = (
    '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">'
    '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>'
)


def _legend() -> str:
    items = "".join(
        '<span class="wr-leg__item">'
        f'<span class="wr-leg__dot" style="background:{color}"></span>'
        f'{html.escape(name)}'
        '</span>'
        for name, color in FAITHS
    )
    return (
        '<div class="wr-legend">' + items
        + '<span class="wr-leg__item wr-leg__item--adj">'
          '<span class="wr-leg__dot wr-leg__dot--hollow"></span>'
          'Adjacent (serves the county, just over the line)'
          '</span>'
        + '</div>'
    )


def _filter_chips(counts: Counter, total: int) -> str:
    chips = [
        '<button type="button" class="wr-chip is-active" data-faith="All" '
        f'aria-pressed="true">All <span class="wr-chip__n">{total}</span></button>'
    ]
    for name, color in FAITHS:
        n = counts.get(name, 0)
        chips.append(
            f'<button type="button" class="wr-chip" data-faith="{html.escape(name)}" '
            f'aria-pressed="false">'
            f'<span class="wr-chip__sw" style="background:{color}"></span>'
            f'{html.escape(name)} <span class="wr-chip__n">{n}</span></button>'
        )
    return '<div class="wr-chips" role="group" aria-label="Filter by faith">' + "".join(chips) + '</div>'


def _map_section(points: list) -> str:
    """A Leaflet map of all places, colored by faith, with a filter and count.
    points = [[name, lat, lon, denomination, address, faith, in_county_bool], ...].
    Tiles follow the site theme (light by default, dark when data-theme=dark)."""
    if not points:
        return ""
    data = _json.dumps(points, ensure_ascii=False)
    colors = _json.dumps(FAITH_COLOR, ensure_ascii=False)
    return (
        _MAP_HEAD
        + '<div id="wr-map" class="wr-map"></div>'
        '<div class="wr-count" id="wr-count" aria-live="polite"></div>'
        '<script>(function(){if(!window.L)return;'
        'var pts=' + data + ';var COLORS=' + colors + ';'
        'function tileUrl(){var dark=document.documentElement.getAttribute("data-theme")==="dark";'
        'return dark?"https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"'
        ':"https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";}'
        'var map=L.map("wr-map",{scrollWheelZoom:false}).setView([37.40,-77.55],10);'
        'var layer=L.tileLayer(tileUrl(),{attribution:"\\u00a9 OpenStreetMap \\u00a9 CARTO",'
        'subdomains:"abcd",maxZoom:19}).addTo(map);'
        'function esc(s){var d=document.createElement("div");d.textContent=s==null?"":s;return d.innerHTML;}'
        'var groups={};var all=L.featureGroup().addTo(map);'
        'pts.forEach(function(p){'
        'var name=p[0],lat=p[1],lon=p[2],denom=p[3],addr=p[4],faith=p[5],inCounty=p[6];'
        'var col=COLORS[faith]||COLORS["Other"];'
        'var opts=inCounty'
        '?{radius:7,color:"#fff",weight:1.5,fillColor:col,fillOpacity:0.95}'
        ':{radius:7,color:col,weight:2.5,fillColor:"#fff",fillOpacity:0.25,dashArray:"2,2"};'
        'var m=L.circleMarker([lat,lon],opts);'
        'var h="<strong>"+esc(name)+"</strong>";'
        'if(denom){h+="<br><span class=\\"wr-pop-d\\">"+esc(denom)+"</span>";}'
        'if(addr){h+="<br>"+esc(addr);}'
        'if(!inCounty){h+="<br><em>Adjacent \\u2013 serves Chesterfield residents</em>";}'
        'm.bindPopup(h);(groups[faith]=groups[faith]||[]).push(m);m.addTo(all);});'
        'try{map.fitBounds(all.getBounds().pad(0.08));}catch(e){}'
        'var active="All";var countEl=document.getElementById("wr-count");'
        'function visible(){var n=0;Object.keys(groups).forEach(function(f){'
        'var show=(active==="All"||active===f);'
        'groups[f].forEach(function(m){'
        'if(show){if(!all.hasLayer(m)){all.addLayer(m);}n++;}'
        'else{if(all.hasLayer(m)){all.removeLayer(m);}}});});return n;}'
        'function update(){var n=visible();'
        'var label=active==="All"?"all faiths":active;'
        'countEl.textContent="Showing "+n+" place"+(n===1?"":"s")+" \\u2014 "+label;}'
        'var chips=document.querySelectorAll(".wr-chip");'
        'chips.forEach(function(c){c.addEventListener("click",function(){'
        'active=c.getAttribute("data-faith");'
        'chips.forEach(function(o){var on=o===c;o.classList.toggle("is-active",on);'
        'o.setAttribute("aria-pressed",on?"true":"false");});update();});});'
        'update();'
        'new MutationObserver(function(){layer.setUrl(tileUrl());})'
        '.observe(document.documentElement,{attributes:true,attributeFilter:["data-theme"]});'
        '})();</script>'
    )


def _form() -> str:
    key = os.environ.get("WEB3FORMS_KEY", "").strip()
    notice = "" if key else (
        '<div class="form-notice">⚠️ This form isn\'t active yet — add a '
        'free Web3Forms key (WEB3FORMS_KEY in scripts/.deploy.env, get one in 30s at '
        'web3forms.com) and rebuild.</div>')
    return (
        notice
        + '<form class="site-form" action="https://api.web3forms.com/submit" method="POST">'
        f'<input type="hidden" name="access_key" value="{html.escape(key or "MISSING_WEB3FORMS_KEY")}">'
        '<input type="hidden" name="subject" value="Add or correct a place of worship">'
        '<input type="hidden" name="from_name" value="Chesterfield Report Worship Map">'
        '<input type="hidden" name="redirect" value="https://chesterfieldreport.com/places-of-worship.html?ok=1">'
        '<input type="checkbox" name="botcheck" class="hp" tabindex="-1" autocomplete="off">'
        '<label>Congregation / place of worship name</label>'
        '<input type="text" name="Congregation" required autocomplete="organization" '
        'placeholder="e.g. First Baptist Church of Example">'
        '<label>Address</label>'
        '<input type="text" name="Address" required '
        'placeholder="Street, city, ZIP">'
        '<label>Faith / tradition</label>'
        '<input type="text" name="Faith" required '
        'placeholder="e.g. Christian (Methodist), Muslim, Jewish, Hindu, Buddhist, Sikh…">'
        '<label>What needs adding or correcting? <span class="opt">(optional)</span></label>'
        '<textarea name="Details" rows="4" placeholder="New listing, wrong location, '
        'closed, name change, a website to link…"></textarea>'
        '<label>Email <span class="opt">(optional, only if you want a reply; never published)</span></label>'
        '<input type="email" name="email" autocomplete="email">'
        '<label>Your name <span class="opt">(optional)</span></label>'
        '<input type="text" name="Name" autocomplete="name">'
        '<button type="submit" class="cr-btn cr-btn--primary" style="margin-top:1.3rem">'
        'Submit for review</button>'
        '</form>'
    )


def _sources() -> str:
    srcs = [
        ("OpenStreetMap (© contributors, ODbL)", "https://www.openstreetmap.org/copyright"),
        ("Overpass API", "https://overpass-api.de/api/interpreter"),
        ("US Census geocoder", "https://geocoding.geo.census.gov/"),
    ]
    links = " &middot; ".join(
        f'<a href="{html.escape(u)}" target="_blank" rel="noopener">{html.escape(l)}</a>'
        for l, u in srcs
    )
    return (
        '<div class="wr-source">The base map of Christian churches is drawn from '
        f'OpenStreetMap, scoped to the Chesterfield County boundary: {links}. '
        'Because OpenStreetMap under-tags minority faiths here, we supplement it with '
        'a hand-verified list of Muslim, Jewish, Hindu, Buddhist, Sikh, Latter-day '
        'Saint, Orthodox, and Unitarian Universalist congregations, each cross-checked '
        'against the congregation’s own website and geocoded with the US Census '
        'geocoder. A few sites just over the county line are included as adjacent '
        'because they are the nearest option for that faith and serve county residents.'
        '</div>'
    )


_CSS = """<style>
.wr-wrap{max-width:820px;margin:0 auto;}
.wr-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:64ch;margin:.4rem 0 1.4rem;}
.wr-chips{display:flex;flex-wrap:wrap;gap:.5rem;margin:0 0 1rem;}
.wr-chip{display:inline-flex;align-items:center;gap:.4rem;cursor:pointer;
 font:var(--fw-semibold) var(--fs-2xs)/1 var(--font-sans);color:var(--text-secondary);
 background:var(--surface-card);border:1px solid var(--border);border-radius:999px;
 padding:.5rem .85rem;}
.wr-chip:hover{border-color:var(--accent);color:var(--text-primary);}
.wr-chip.is-active{background:var(--accent);border-color:var(--accent);color:#fff;}
.wr-chip__sw{width:.7rem;height:.7rem;border-radius:50%;border:1px solid rgba(255,255,255,.6);}
.wr-chip__n{font:var(--fw-bold) var(--fs-3xs) var(--font-mono);opacity:.85;}
.wr-map{height:440px;border:1px solid var(--border);border-radius:var(--radius-sm);margin:0 0 .5rem;background:var(--surface-sunken,#eee);z-index:0;}
.wr-map .leaflet-popup-content{font:var(--fs-2xs)/1.4 var(--font-sans);}
.wr-map .leaflet-popup-content .wr-pop-d{color:var(--text-tertiary);}
.wr-count{font:var(--fw-semibold) var(--fs-2xs)/1.4 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);margin:0 0 1rem;}
.wr-legend{display:flex;flex-wrap:wrap;gap:.5rem 1.1rem;margin:0 0 1.4rem;padding:.85rem 1rem;border:1px solid var(--border);border-radius:var(--radius-xs);background:var(--surface-card);}
.wr-leg__item{display:inline-flex;align-items:center;gap:.45rem;font:var(--fs-3xs)/1.3 var(--font-sans);color:var(--text-secondary);}
.wr-leg__dot{width:.8rem;height:.8rem;border-radius:50%;border:1.5px solid #fff;box-shadow:0 0 0 1px var(--border);}
.wr-leg__dot--hollow{background:transparent !important;border:2px dashed var(--text-tertiary);box-shadow:none;}
.wr-leg__item--adj{color:var(--text-tertiary);}
.wr-sec{margin:2.4rem 0;}
.wr-sec h2{font:var(--fw-bold) var(--fs-xl)/1.15 var(--font-display);margin:0 0 .3rem;}
.wr-sec__dek{font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);margin:0 0 1.2rem;max-width:64ch;}
.wr-fair{border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:var(--radius-sm);background:var(--surface-card);padding:1.1rem 1.25rem;margin:0 0 1.6rem;}
.wr-fair p{font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);margin:0 0 .6rem;}
.wr-fair p:last-child{margin-bottom:0;}
.wr-formwrap{max-width:640px;}
.form-notice{background:rgba(255,210,63,.12);border:1px solid var(--accent);border-radius:8px;padding:.85rem 1.1rem;margin:0 0 1.3rem;color:var(--text-secondary);font:var(--fs-sm)/1.5 var(--font-sans);}
.site-form label{display:block;font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);text-transform:uppercase;letter-spacing:var(--ls-wide);color:var(--accent);margin:1.1rem 0 .35rem;}
.site-form .opt{color:var(--text-tertiary);font-weight:400;text-transform:none;letter-spacing:0;}
.site-form input[type=text],.site-form input[type=email],.site-form textarea{width:100%;font:inherit;padding:.65rem .75rem;background:var(--surface-card);color:var(--text-primary);border:1px solid var(--border);border-radius:6px;}
.site-form input:focus,.site-form textarea:focus{outline:none;border-color:var(--accent);}
.site-form textarea{resize:vertical;min-height:6rem;}
.site-form .hp{position:absolute;left:-9999px;}
.wr-thanks{border:1px solid var(--accent);border-radius:10px;padding:1.1rem 1.3rem;background:var(--surface-card);}
.wr-thanks h2{font:var(--fw-bold) var(--fs-xl) var(--font-display);color:var(--accent);margin:.2rem 0 .5rem;}
.wr-source{margin:2.4rem 0 0;padding:1rem 1.1rem;border-left:3px solid var(--accent);background:var(--surface-card);border-radius:var(--radius-xs);font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);}
.wr-source a{color:var(--accent);font-weight:600;}
@media(max-width:620px){
  .wr-map{height:360px;}
}
</style>"""


def build_worship() -> Path:
    places = _load()
    counts = Counter(p["religion"] for p in places)
    total = len(places)
    in_county = sum(1 for p in places if p.get("in_county"))
    adjacent = total - in_county

    points = [
        [
            p["name"], p["lat"], p["lon"],
            p.get("denomination", ""), p.get("address", ""),
            p["religion"], bool(p.get("in_county")),
        ]
        for p in places
    ]

    lead = (
        f'A directory of {total} places of worship in and serving Chesterfield '
        'County, across all faiths. The data comes from OpenStreetMap plus our own '
        'additions, and it is never finished: congregations can ask to be added or '
        'corrected using the form below.'
    )

    thanks_js = (
        "<script>if(location.search.indexOf('ok=1')>-1){"
        "var f=document.querySelector('.site-form');"
        "if(f){f.outerHTML='<div class=\\\"wr-thanks\\\"><h2>Thank you.</h2>'"
        "+'<p>Your submission is in. We review every one before it goes on the map. "
        "<a href=\\\"/places-of-worship.html\\\">\\u2190 Back to the map</a></p></div>';}}</script>")

    body = (
        _CSS
        + '<div class="wr-wrap">'
        + '<h1 class="page-title">Places of Worship</h1>'
        + f'<p class="wr-lead">{html.escape(lead)}</p>'
        + _filter_chips(counts, total)
        + _map_section(points)
        + _legend()
        + '<div class="wr-sec"><h2>How this list is kept</h2>'
        + '<div class="wr-fair">'
        + '<p>This map exists to represent every faith community in Chesterfield '
          'fairly. Most of the markers are Christian churches pulled from '
          'OpenStreetMap, which has strong coverage of churches here but under-tags '
          'minority faiths. So we hand-add and verify Muslim, Jewish, Hindu, '
          'Buddhist, Sikh, Latter-day Saint, Orthodox, and Unitarian Universalist '
          'congregations, including a few just over the county line that are the '
          'nearest option for that faith.</p>'
        + f'<p>Right now the map shows {in_county} places inside the county and '
          f'{adjacent} adjacent. Some OpenStreetMap entries are unnamed or may be '
          'historic church buildings rather than active congregations, and a small '
          'number of coordinates (such as one of the gurdwaras) are approximate and '
          'being verified. If something is wrong, missing, or out of date, please '
          'tell us. Any community can get added or fixed.</p>'
        + '</div></div>'
        + '<div class="wr-sec"><h2>Add or correct a place of worship</h2>'
        + '<p class="wr-sec__dek">Is your congregation missing, in the wrong spot, '
          'or listed incorrectly? Send it here and we will review and update the map.</p>'
        + '<div class="wr-formwrap">' + _form() + '</div>'
        + '</div>'
        + _sources()
        + thanks_js
        + '</div>'
    )

    page = render._shell(body)
    page = render._inject_og(
        page,
        "Places of Worship in Chesterfield County: a map of every faith",
        "A faith-filtered map of churches, mosques, synagogues, temples, and "
        "gurdwaras in and serving Chesterfield County, Virginia, from OpenStreetMap "
        "plus our own verified additions. Congregations can ask to be added or corrected.",
        f"{render.SITE_URL}/places-of-worship.html", og_type="website")
    out = PUBLIC / "places-of-worship.html"
    out.write_text(page, encoding="utf-8")
    return out
