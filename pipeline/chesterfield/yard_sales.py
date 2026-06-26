"""Yard Sales: a submit-your-own map of garage, yard, estate, and moving sales
in Chesterfield County, with a date filter (today / tomorrow / this week /
this month / all upcoming).

Builds public/yard-sales.html. Two layers on one Leaflet map:

  1. LIVE SALES  - reader-submitted, moderated entries from pipeline/yard_sales.json.
                   Filtered by date client-side; past sales auto-expire (the build
                   never needs cleaning, the browser hides anything past its end
                   date). Markers are solid.
  2. COMMUNITY   - the curated, recurring neighborhood/HOA community-wide sales
                   (Woodland Pond, Charter Colony, Harpers Mill, ...). These are
                   annual events whose exact date moves year to year, so they are
                   NOT date-filtered: they always show as hollow markers and as a
                   reference calendar below the map. Source-linked, dates flagged
                   "confirm with the neighborhood."

Why submission-first: every high-volume listing source (Craigslist, the gsalr
network, the estate-sale directories, Facebook, Nextdoor) prohibits automated or
manual copying in its terms of service, so we cannot ingest them. We link out to
them instead and let residents post their own sale here. See research/yard-sales.md.

Leaflet + CARTO (theme-aware) map, same stack as worship.py / safety.py. Vanilla
filter JS, no extra libraries. Stdlib only; reuses render._shell() / _inject_og.
"""
from __future__ import annotations

import html
import json
import json as _json
import os
from datetime import datetime
from pathlib import Path

from . import render
from .render import PUBLIC

# Reader-submitted, moderated sales. Starts empty; the moderation workflow adds
# geocoded entries here (see _example_shape below) and a rebuild publishes them.
DATA = Path(__file__).resolve().parents[1] / "yard_sales.json"

# Shape of one LIVE sale entry in yard_sales.json (all dates ISO YYYY-MM-DD,
# times 24h "HH:MM", lat/lon geocoded at moderation time):
#   {"title","type","start_date","end_date","start_time","end_time",
#    "address","city","zip","lat","lon","description","rain_date"(opt)}

# Curated recurring community-wide sales. Coordinates are the neighborhood center
# (approximate by nature: these are area-wide events, not a single address).
# Timing is the OBSERVED pattern, not a promise; we confirm each year's date from
# the neighborhood's own channel. Sourced in research/yard-sales.md.
COMMUNITY_SALES = [
    {
        "name": "Woodland Pond Community Yard Sale",
        "neighborhood": "Woodland Pond", "city": "Chesterfield",
        "timing": "Annual, a Saturday in mid-May (8am to 1pm). Run by the Woodland Pond Swim & Racquet Club.",
        "lat": 37.37009, "lon": -77.51235,
        "source": "https://www.facebook.com/WPSRC/",
    },
    {
        "name": "Charter Colony Spring Community Yard Sale",
        "neighborhood": "Villages of Charter Colony", "city": "Midlothian",
        "timing": "Spring, an early-May Saturday (7am to 1pm), at the Charter House.",
        "lat": 37.47917, "lon": -77.66774,
        "source": "https://www.hhhuntcommunities.com/new-communities/charter-colony/community-overview.html",
    },
    {
        "name": "Harpers Mill Community Yard Sale",
        "neighborhood": "Harpers Mill", "city": "Chesterfield",
        "timing": "Twice a year, a spring and a fall Saturday (about 8am to noon), at the clubhouse.",
        "lat": 37.37997, "lon": -77.68765,
        "source": "https://harpersmill.com/events/",
    },
    {
        "name": "Hallsley Community Yard Sale",
        "neighborhood": "Hallsley", "city": "Midlothian",
        "timing": "Recurring, primarily a late-April Saturday (8am to noon), some years a fall edition too.",
        "lat": 37.46503, "lon": -77.68794,
        "source": "https://www.hallsley.com/tag/garage-sale/",
    },
    {
        "name": "The Highlands Neighborhood Yard Sale",
        "neighborhood": "The Highlands", "city": "Chesterfield",
        "timing": "Annual, spring, at the pool parking lot (about 8am to noon).",
        "lat": 37.33397, "lon": -77.53002,
        "source": "https://www.thehighlandsonline.com/",
    },
    {
        "name": "Brandermill Neighborhood Yard Sales",
        "neighborhood": "Brandermill", "city": "Midlothian",
        "timing": "Annual community sale; date set each year by the Brandermill Community Association.",
        "lat": 37.47037, "lon": -77.66721,
        "source": "https://brandermill.com/",
    },
    {
        "name": "Woodlake Community Yard Sale",
        "neighborhood": "Woodlake", "city": "Midlothian",
        "timing": "More than once a year (a spring and a fall sale); register with the WCA at least 48 hours ahead.",
        "lat": 37.42169, "lon": -77.6766,
        "source": "https://woodlakeva.org/events/",
    },
    {
        "name": "FoxCreek Community Yard Sale",
        "neighborhood": "FoxCreek", "city": "Moseley",
        "timing": "A large spring sale (a Saturday in April, 90+ homes across the community).",
        "lat": 37.413, "lon": -77.756,
        "source": "https://www.facebook.com/foxcreekrva/",
    },
    {
        "name": "Ashbrook Community Yard Sale",
        "neighborhood": "Ashbrook", "city": "Chesterfield",
        "timing": "Recurring (at least a fall sale), organized through the community association.",
        "lat": 37.39451, "lon": -77.689,
        "source": "https://ashbrookonline.com/ashbrook-community-yard-sale/",
    },
]

# Places people can also look for sales we do not host. We link out (the law and
# these sites' terms let us link, not copy).
LINKOUTS = [
    ("Craigslist Richmond: garage & moving sales", "https://richmond.craigslist.org/search/gms"),
    ("gsalr.com: Chesterfield garage sales", "https://gsalr.com/garage-sales-chesterfield-va.html"),
    ("EstateSales.net: Chesterfield estate sales", "https://www.estatesales.net/VA/Chesterfield"),
]

_MAP_HEAD = (
    '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">'
    '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>'
)

# Date filter buttons: data-bucket drives the client-side window. "week" and
# "month" are rolling windows (next 7 / next 30 days), which reads more naturally
# for a "what's coming up" board than a calendar week that empties out by Friday.
_BUCKETS = [
    ("week", "This week"),
    ("today", "Today"),
    ("tomorrow", "Tomorrow"),
    ("month", "This month"),
    ("all", "All upcoming"),
]
_DEFAULT_BUCKET = "week"


def _load() -> list:
    try:
        return json.loads(DATA.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return []


def _fmt_time(t: str) -> str:
    """'08:00' -> '8 AM'; '13:30' -> '1:30 PM'; '' -> ''."""
    if not t or ":" not in t:
        return ""
    try:
        h, m = (int(x) for x in t.split(":")[:2])
    except ValueError:
        return ""
    ap = "AM" if h < 12 else "PM"
    hr = h % 12 or 12
    return f"{hr}:{m:02d} {ap}".replace(":00 ", " ")


def _fmt_daterange(start: str, end: str) -> str:
    """ISO start/end -> 'Sat, Jul 11' or 'Fri to Sat, Jul 10 to 11'."""
    try:
        ds = datetime.strptime(start, "%Y-%m-%d")
    except (ValueError, TypeError):
        return ""
    de = ds
    if end and end != start:
        try:
            de = datetime.strptime(end, "%Y-%m-%d")
        except ValueError:
            de = ds
    if de == ds:
        return ds.strftime("%a, %b ") + str(ds.day)
    if de.month == ds.month:
        return f"{ds.strftime('%a, %b ')}{ds.day} to {de.day}"
    return f"{ds.strftime('%a, %b ')}{ds.day} to {de.strftime('%b ')}{de.day}"


def _fmt_times(s: dict) -> str:
    a, b = _fmt_time(s.get("start_time", "")), _fmt_time(s.get("end_time", ""))
    if a and b:
        return f"{a} to {b}"
    return a or b or ""


def _addr_line(s: dict) -> str:
    bits = [s.get("address", ""), s.get("city", ""), s.get("zip", "")]
    return ", ".join(b for b in bits if b).replace(", VA,", ",")


def _chips() -> str:
    chips = []
    for bucket, label in _BUCKETS:
        active = bucket == _DEFAULT_BUCKET
        chips.append(
            f'<button type="button" class="ys-chip{" is-active" if active else ""}" '
            f'data-bucket="{bucket}" aria-pressed="{"true" if active else "false"}">'
            f'{html.escape(label)} <span class="ys-chip__n" data-n="{bucket}"></span></button>'
        )
    return '<div class="ys-chips" role="group" aria-label="Filter sales by date">' + "".join(chips) + "</div>"


def _sale_cards(sales: list) -> str:
    """Server-rendered live-sale cards with ISO data-attrs; JS shows/hides them in
    sync with the map by date bucket. Empty at launch (no cards), which is fine:
    the empty-state note carries the page until residents post."""
    cards = []
    for i, s in enumerate(sales):
        date_lbl = _fmt_daterange(s.get("start_date", ""), s.get("end_date", "") or s.get("start_date", ""))
        time_lbl = _fmt_times(s)
        rain = s.get("rain_date", "")
        rain_lbl = ""
        if rain:
            rr = _fmt_daterange(rain, rain)
            rain_lbl = f'<span class="ys-card__rain">Rain date: {html.escape(rr)}</span>'
        meta = " &middot; ".join(x for x in [html.escape(date_lbl), html.escape(time_lbl)] if x)
        typ = s.get("type", "").strip()
        cards.append(
            f'<article class="ys-card" id="ys-card-{i}" '
            f'data-start="{html.escape(s.get("start_date",""))}" '
            f'data-end="{html.escape(s.get("end_date","") or s.get("start_date",""))}">'
            + (f'<span class="ys-card__type">{html.escape(typ)}</span>' if typ else "")
            + f'<h3 class="ys-card__title">{html.escape(s.get("title","Yard sale"))}</h3>'
            + f'<p class="ys-card__when">{meta}</p>'
            + f'<p class="ys-card__addr">{html.escape(_addr_line(s))}</p>'
            + (f'<p class="ys-card__desc">{html.escape(s.get("description",""))}</p>' if s.get("description") else "")
            + rain_lbl
            + '</article>'
        )
    empty = (
        '<div class="ys-empty" id="ys-empty">'
        '<p><strong>No sales posted for this window yet.</strong></p>'
        '<p>Got a sale coming up? <a href="#ys-post">Post it here</a> and it will show on '
        'the map after a quick review. It is free.</p>'
        '</div>'
    )
    return '<div class="ys-list" id="ys-list">' + "".join(cards) + "</div>" + empty


def _map_section(sales: list) -> str:
    # Live points: [i, title, lat, lon, type, dateLabel, timeLabel, addr, desc, startISO, endISO]
    live = []
    for i, s in enumerate(sales):
        if s.get("lat") is None or s.get("lon") is None:
            continue
        live.append([
            i, s.get("title", "Yard sale"), s["lat"], s["lon"], s.get("type", ""),
            _fmt_daterange(s.get("start_date", ""), s.get("end_date", "") or s.get("start_date", "")),
            _fmt_times(s), _addr_line(s), s.get("description", ""),
            s.get("start_date", ""), s.get("end_date", "") or s.get("start_date", ""),
        ])
    # Community points: [name, lat, lon, neighborhood, city, timing, source]
    comm = [
        [c["name"], c["lat"], c["lon"], c["neighborhood"], c["city"], c["timing"], c["source"]]
        for c in COMMUNITY_SALES
    ]
    live_j = _json.dumps(live, ensure_ascii=False)
    comm_j = _json.dumps(comm, ensure_ascii=False)
    default_b = _json.dumps(_DEFAULT_BUCKET)
    return (
        _MAP_HEAD
        + '<div id="ys-map" class="ys-map"></div>'
        '<div class="ys-count" id="ys-count" aria-live="polite"></div>'
        '<script>(function(){'
        'var LIVE=' + live_j + ';var COMM=' + comm_j + ';var bucket=' + default_b + ';'
        'function esc(s){var d=document.createElement("div");d.textContent=s==null?"":s;return d.innerHTML;}'
        # date math, all in local midnight ms
        'var n=new Date();n.setHours(0,0,0,0);var T=n.getTime();var DAY=86400000;'
        'var TOM=T+DAY,WK=T+7*DAY,MO=T+30*DAY;'
        'function pd(s){if(!s)return null;var p=s.split("-");return new Date(+p[0],(+p[1])-1,+p[2]).getTime();}'
        'function inBucket(s,e){if(e==null)e=s;if(e<T)return false;'  # past -> never
        'if(bucket==="all")return true;'
        'if(bucket==="today")return s<=T&&e>=T;'
        'if(bucket==="tomorrow")return s<=TOM&&e>=TOM;'
        'if(bucket==="week")return s<=WK&&e>=T;'
        'if(bucket==="month")return s<=MO&&e>=T;return true;}'
        'if(!window.L){return;}'
        'function tileUrl(){var dark=document.documentElement.getAttribute("data-theme")==="dark";'
        'return dark?"https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"'
        ':"https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";}'
        'var map=L.map("ys-map",{scrollWheelZoom:false}).setView([37.42,-77.55],10);'
        'var layer=L.tileLayer(tileUrl(),{attribution:"\\u00a9 OpenStreetMap \\u00a9 CARTO",'
        'subdomains:"abcd",maxZoom:19}).addTo(map);'
        'var ACCENT=getComputedStyle(document.documentElement).getPropertyValue("--accent").trim()||"#c0392b";'
        # community markers (always shown, hollow)
        'var commLayer=L.featureGroup().addTo(map);'
        'COMM.forEach(function(c){'
        'var m=L.circleMarker([c[1],c[2]],{radius:7,color:"#6b7280",weight:2,'
        'fillColor:"#6b7280",fillOpacity:0.25,dashArray:"2,2"});'
        'var h="<strong>"+esc(c[0])+"</strong><br><span class=\\"ys-pop-n\\">"+esc(c[3])+", "+esc(c[4])+"</span>";'
        'h+="<br>"+esc(c[5]);'
        'h+="<br><em>Annual event, date varies. Confirm with the neighborhood.</em>";'
        'if(c[6]){h+="<br><a href=\\""+esc(c[6])+"\\" target=\\"_blank\\" rel=\\"noopener\\">Neighborhood info</a>";}'
        'm.bindPopup(h);m.addTo(commLayer);});'
        # live markers (filtered)
        'var liveLayer=L.featureGroup().addTo(map);var liveMk={};'
        'LIVE.forEach(function(p){'
        'var m=L.circleMarker([p[2],p[3]],{radius:8,color:"#fff",weight:1.5,fillColor:ACCENT,fillOpacity:0.95});'
        'var h="<strong>"+esc(p[1])+"</strong>";'
        'if(p[4]){h+="<br><span class=\\"ys-pop-t\\">"+esc(p[4])+"</span>";}'
        'if(p[5]){h+="<br>"+esc(p[5]);}if(p[6]){h+=" \\u00b7 "+esc(p[6]);}'
        'if(p[7]){h+="<br>"+esc(p[7]);}if(p[8]){h+="<br><span class=\\"ys-pop-d\\">"+esc(p[8])+"</span>";}'
        'm.bindPopup(h);liveMk[p[0]]=m;});'
        'function fit(){var g=L.featureGroup([]);'
        'liveLayer.eachLayer(function(l){g.addLayer(l);});commLayer.eachLayer(function(l){g.addLayer(l);});'
        'try{var b=g.getBounds();if(b.isValid())map.fitBounds(b.pad(0.12));}catch(e){}}'
        'var countEl=document.getElementById("ys-count");var emptyEl=document.getElementById("ys-empty");'
        'function bucketCount(bk){var save=bucket;bucket=bk;var c=0;'
        'LIVE.forEach(function(p){if(inBucket(pd(p[9]),pd(p[10])))c++;});bucket=save;return c;}'
        'function update(){var shown=0;'
        'LIVE.forEach(function(p){var vis=inBucket(pd(p[9]),pd(p[10]));'
        'var card=document.getElementById("ys-card-"+p[0]);if(card)card.style.display=vis?"":"none";'
        'var m=liveMk[p[0]];if(m){if(vis){if(!liveLayer.hasLayer(m))liveLayer.addLayer(m);shown++;}'
        'else{if(liveLayer.hasLayer(m))liveLayer.removeLayer(m);}}});'
        'if(emptyEl)emptyEl.style.display=shown?"none":"";'
        'var lab=({week:"this week",today:"today",tomorrow:"tomorrow",month:"this month",all:"upcoming"})[bucket];'
        'countEl.textContent=shown+" sale"+(shown===1?"":"s")+" "+lab+" \\u00b7 "+COMM.length+" annual neighborhood sales";'
        'document.querySelectorAll(".ys-chip__n").forEach(function(el){'
        'var c=bucketCount(el.getAttribute("data-n"));el.textContent=c?("("+c+")"):"";});'
        'fit();}'
        'var chips=document.querySelectorAll(".ys-chip");'
        'chips.forEach(function(c){c.addEventListener("click",function(){'
        'bucket=c.getAttribute("data-bucket");'
        'chips.forEach(function(o){var on=o===c;o.classList.toggle("is-active",on);'
        'o.setAttribute("aria-pressed",on?"true":"false");});update();});});'
        'update();'
        'new MutationObserver(function(){layer.setUrl(tileUrl());})'
        '.observe(document.documentElement,{attributes:true,attributeFilter:["data-theme"]});'
        '})();</script>'
    )


def _community_section() -> str:
    cards = []
    for c in COMMUNITY_SALES:
        cards.append(
            '<article class="ys-comm">'
            f'<h3 class="ys-comm__title">{html.escape(c["name"])}</h3>'
            f'<p class="ys-comm__loc">{html.escape(c["neighborhood"])}, {html.escape(c["city"])}</p>'
            f'<p class="ys-comm__timing">{html.escape(c["timing"])}</p>'
            f'<a class="ys-comm__src" href="{html.escape(c["source"])}" target="_blank" rel="noopener">'
            'Neighborhood info &rarr;</a>'
            '</article>'
        )
    return (
        '<div class="ys-sec"><h2>Annual neighborhood sales</h2>'
        '<p class="ys-sec__dek">Many Chesterfield neighborhoods hold a big community-wide '
        'yard sale once or twice a year, often dozens of homes on the same morning. These are '
        'the ones we have confirmed. Exact dates move year to year, so check the neighborhood’s '
        'own page or Facebook before you go, and if you can confirm this year’s date, '
        '<a href="#ys-post">let us know</a> and we will put it on the map.</p>'
        '<div class="ys-comm-grid">' + "".join(cards) + '</div></div>'
    )


def _linkouts_section() -> str:
    links = "".join(
        f'<li><a href="{html.escape(u)}" target="_blank" rel="noopener">{html.escape(t)}</a></li>'
        for t, u in LINKOUTS
    )
    return (
        '<div class="ys-sec"><h2>Looking for more sales right now?</h2>'
        '<p class="ys-sec__dek">We only map sales people post to us, so the list above is not '
        'everything happening this weekend. These other boards carry Chesterfield sales too '
        '(they open in a new tab):</p>'
        f'<ul class="ys-links">{links}</ul></div>'
    )


def _form() -> str:
    key = os.environ.get("WEB3FORMS_KEY", "").strip()
    notice = "" if key else (
        '<div class="form-notice">⚠️ This form isn\'t active yet — add a '
        'free Web3Forms key (WEB3FORMS_KEY in scripts/.deploy.env) and rebuild.</div>')
    type_opts = "".join(
        f'<option>{t}</option>' for t in
        ["Yard / garage sale", "Estate sale", "Moving sale", "Multi-family / community", "Other"]
    )
    return (
        notice
        + '<form class="site-form" action="https://api.web3forms.com/submit" method="POST">'
        f'<input type="hidden" name="access_key" value="{html.escape(key or "MISSING_WEB3FORMS_KEY")}">'
        '<input type="hidden" name="subject" value="New yard sale submission">'
        '<input type="hidden" name="from_name" value="Chesterfield Report Yard Sales">'
        '<input type="hidden" name="redirect" value="https://chesterfieldreport.com/yard-sales.html?ok=1">'
        '<input type="checkbox" name="botcheck" class="hp" tabindex="-1" autocomplete="off">'
        '<label>Sale title</label>'
        '<input type="text" name="Title" required placeholder="e.g. Big multi-family garage sale">'
        '<label>Type of sale</label>'
        f'<select name="Type">{type_opts}</select>'
        '<div class="ys-row">'
        '<div><label>Start date</label><input type="date" name="Start date" required></div>'
        '<div><label>End date <span class="opt">(if more than one day)</span></label>'
        '<input type="date" name="End date"></div>'
        '</div>'
        '<div class="ys-row">'
        '<div><label>Start time</label><input type="time" name="Start time" required></div>'
        '<div><label>End time</label><input type="time" name="End time" required></div>'
        '</div>'
        '<label>Street address</label>'
        '<input type="text" name="Address" required placeholder="e.g. 1234 Genito Rd">'
        '<div class="ys-row">'
        '<div><label>City</label><input type="text" name="City" required value="" placeholder="Midlothian, Chester..."></div>'
        '<div><label>ZIP</label><input type="text" name="ZIP" required inputmode="numeric" placeholder="231.."></div>'
        '</div>'
        '<label>What are you selling? <span class="opt">(optional, but it helps)</span></label>'
        '<textarea name="Description" rows="3" placeholder="Furniture, baby gear, tools, household..."></textarea>'
        '<label>Rain date <span class="opt">(optional)</span></label>'
        '<input type="date" name="Rain date">'
        '<label>Your email <span class="opt">(so we can confirm; never published)</span></label>'
        '<input type="email" name="email" required autocomplete="email">'
        '<label>Your name <span class="opt">(optional)</span></label>'
        '<input type="text" name="Name" autocomplete="name">'
        '<button type="submit" class="cr-btn cr-btn--primary" style="margin-top:1.3rem">'
        'Submit your sale</button>'
        '<p class="ys-form-note">We review every submission before it goes on the map (it keeps out '
        'spam and bad addresses), so it may take a few hours to appear. Sales drop off the map '
        'automatically after they are over.</p>'
        '</form>'
    )


_CSS = """<style>
.ys-wrap{max-width:840px;margin:0 auto;}
.ys-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:64ch;margin:.4rem 0 1.3rem;}
.ys-cta{display:inline-flex;align-items:center;gap:.5rem;font:var(--fw-bold) var(--fs-sm) var(--font-sans);
 background:var(--accent);color:#fff;border-radius:999px;padding:.6rem 1.2rem;text-decoration:none;margin:0 0 1.6rem;}
.ys-cta:hover{filter:brightness(1.08);}
.ys-chips{display:flex;flex-wrap:wrap;gap:.5rem;margin:0 0 1rem;}
.ys-chip{display:inline-flex;align-items:center;gap:.4rem;cursor:pointer;
 font:var(--fw-semibold) var(--fs-2xs)/1 var(--font-sans);color:var(--text-secondary);
 background:var(--surface-card);border:1px solid var(--border);border-radius:999px;padding:.5rem .9rem;}
.ys-chip:hover{border-color:var(--accent);color:var(--text-primary);}
.ys-chip.is-active{background:var(--accent);border-color:var(--accent);color:#fff;}
.ys-chip__n{font:var(--fw-bold) var(--fs-3xs) var(--font-mono);opacity:.85;}
.ys-map{height:440px;border:1px solid var(--border);border-radius:var(--radius-sm);margin:0 0 .5rem;background:var(--surface-sunken,#eee);z-index:0;}
.ys-map .leaflet-popup-content{font:var(--fs-2xs)/1.4 var(--font-sans);}
.ys-map .leaflet-popup-content .ys-pop-t{color:var(--accent);font-weight:700;text-transform:uppercase;letter-spacing:.04em;font-size:var(--fs-3xs);}
.ys-map .leaflet-popup-content .ys-pop-n,.ys-map .leaflet-popup-content .ys-pop-d{color:var(--text-tertiary);}
.ys-count{font:var(--fw-semibold) var(--fs-2xs)/1.4 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);margin:0 0 1.2rem;}
.ys-list{display:grid;gap:.9rem;margin:0 0 1rem;}
.ys-card{border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface-card);padding:1rem 1.15rem;position:relative;}
.ys-card__type{display:inline-block;font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);text-transform:uppercase;letter-spacing:.06em;color:var(--accent);margin:0 0 .4rem;}
.ys-card__title{font:var(--fw-bold) var(--fs-md)/1.2 var(--font-display);margin:0 0 .3rem;}
.ys-card__when{font:var(--fw-semibold) var(--fs-sm)/1.4 var(--font-sans);color:var(--text-primary);margin:0 0 .2rem;}
.ys-card__addr{font:var(--fs-sm)/1.4 var(--font-sans);color:var(--text-secondary);margin:0 0 .35rem;}
.ys-card__desc{font:var(--fs-sm)/1.5 var(--font-sans);color:var(--text-secondary);margin:0;}
.ys-card__rain{display:block;font:var(--fs-3xs)/1.3 var(--font-mono);color:var(--text-tertiary);margin:.4rem 0 0;}
.ys-empty{border:1px dashed var(--border);border-radius:var(--radius-sm);padding:1.3rem 1.4rem;background:var(--surface-card);text-align:center;}
.ys-empty p{font:var(--fs-sm)/1.5 var(--font-sans);color:var(--text-secondary);margin:.2rem 0;}
.ys-empty a{color:var(--accent);font-weight:600;}
.ys-sec{margin:2.6rem 0;}
.ys-sec h2{font:var(--fw-bold) var(--fs-xl)/1.15 var(--font-display);margin:0 0 .3rem;}
.ys-sec__dek{font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);margin:0 0 1.2rem;max-width:66ch;}
.ys-sec__dek a{color:var(--accent);font-weight:600;}
.ys-comm-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:.9rem;}
.ys-comm{border:1px solid var(--border);border-left:3px solid #6b7280;border-radius:var(--radius-sm);background:var(--surface-card);padding:.95rem 1.1rem;}
.ys-comm__title{font:var(--fw-bold) var(--fs-sm)/1.25 var(--font-display);margin:0 0 .2rem;}
.ys-comm__loc{font:var(--fw-semibold) var(--fs-3xs)/1.3 var(--font-mono);text-transform:uppercase;letter-spacing:.05em;color:var(--text-tertiary);margin:0 0 .45rem;}
.ys-comm__timing{font:var(--fs-2xs)/1.5 var(--font-sans);color:var(--text-secondary);margin:0 0 .55rem;}
.ys-comm__src{font:var(--fw-semibold) var(--fs-3xs) var(--font-sans);color:var(--accent);text-decoration:none;}
.ys-links{margin:0;padding:0 0 0 1.1rem;}
.ys-links li{font:var(--fs-sm)/1.7 var(--font-sans);}
.ys-links a{color:var(--accent);font-weight:600;}
.ys-formwrap{max-width:640px;}
.ys-row{display:flex;gap:1rem;flex-wrap:wrap;}
.ys-row>div{flex:1 1 180px;}
.form-notice{background:rgba(255,210,63,.12);border:1px solid var(--accent);border-radius:8px;padding:.85rem 1.1rem;margin:0 0 1.3rem;color:var(--text-secondary);font:var(--fs-sm)/1.5 var(--font-sans);}
.site-form label{display:block;font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);text-transform:uppercase;letter-spacing:var(--ls-wide);color:var(--accent);margin:1.1rem 0 .35rem;}
.site-form .opt{color:var(--text-tertiary);font-weight:400;text-transform:none;letter-spacing:0;}
.site-form input[type=text],.site-form input[type=email],.site-form input[type=date],.site-form input[type=time],.site-form select,.site-form textarea{width:100%;font:inherit;padding:.65rem .75rem;background:var(--surface-card);color:var(--text-primary);border:1px solid var(--border);border-radius:6px;}
.site-form input:focus,.site-form select:focus,.site-form textarea:focus{outline:none;border-color:var(--accent);}
.site-form textarea{resize:vertical;min-height:4.5rem;}
.site-form .hp{position:absolute;left:-9999px;}
.ys-form-note{font:var(--fs-3xs)/1.5 var(--font-sans);color:var(--text-tertiary);margin:1rem 0 0;}
.ys-thanks{border:1px solid var(--accent);border-radius:10px;padding:1.1rem 1.3rem;background:var(--surface-card);}
.ys-thanks h2{font:var(--fw-bold) var(--fs-xl) var(--font-display);color:var(--accent);margin:.2rem 0 .5rem;}
@media(max-width:620px){.ys-map{height:360px;}}
</style>"""


def build_yard_sales() -> Path:
    sales = _load()
    lead = (
        'Find a yard sale near you, or post your own. Drag the map, then filter by when the '
        'sale is happening. Anyone in Chesterfield can add a sale for free, and listings drop '
        'off automatically once the sale is over.'
    )
    thanks_js = (
        "<script>if(location.search.indexOf('ok=1')>-1){"
        "var f=document.querySelector('.site-form');"
        "if(f){f.outerHTML='<div class=\\\"ys-thanks\\\"><h2>Got it, thank you.</h2>'"
        "+'<p>Your sale is in. We review every submission before it goes on the map, so give it "
        "a few hours. <a href=\\\"/yard-sales.html\\\">\\u2190 Back to the map</a></p></div>';}}</script>")

    body = (
        _CSS
        + '<div class="ys-wrap">'
        + '<h1 class="page-title">Chesterfield Yard Sales</h1>'
        + f'<p class="ys-lead">{html.escape(lead)}</p>'
        + '<a class="ys-cta" href="#ys-post">+ Post your yard sale</a>'
        + _chips()
        + _map_section(sales)
        + _sale_cards(sales)
        + _community_section()
        + _linkouts_section()
        + '<div class="ys-sec" id="ys-post"><h2>Post your yard sale</h2>'
        + '<p class="ys-sec__dek">Free to list. Fill this out and we will add your sale to the map '
          'after a quick review. The more detail you give, the more shoppers show up.</p>'
        + '<div class="ys-formwrap">' + _form() + '</div>'
        + '</div>'
        + thanks_js
        + '</div>'
    )

    page = render._shell(body)
    page = render._inject_og(
        page,
        "Chesterfield Yard Sales: a map you can post your own sale to",
        "A map of garage, yard, estate, and moving sales in Chesterfield County, Virginia. "
        "Filter by today, tomorrow, this week, or this month, see the annual neighborhood "
        "community sales, and post your own sale for free.",
        f"{render.SITE_URL}/yard-sales.html", og_type="website")
    out = PUBLIC / "yard-sales.html"
    out.write_text(page, encoding="utf-8")
    return out
