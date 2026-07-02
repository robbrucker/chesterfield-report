"""Parks & Recreation page for The Chesterfield Report.

Builds public/parks.html from pipeline/parks.json: an overview of the county
Parks & Recreation system, headline stats, a Leaflet map of every mappable park
(typed by who runs it), a table of the major parks with addresses and amenities,
a programs-and-registration section, and a sources footer. State- and
federal-run sites (Pocahontas State Park, Presquile, Richmond Battlefield) are
flagged as NOT county-run.

Reuses render._shell() / _inject_og. Leaflet map follows the safety.py pattern
(theme-aware CARTO tiles, circleMarkers, fitBounds). Stdlib only.
"""
from __future__ import annotations

import html
import json
import json as _json
from pathlib import Path

from . import render
from .render import PUBLIC

DATA = Path(__file__).resolve().parents[1] / "parks.json"

# Sites that are NOT run by Chesterfield County Parks & Recreation.
_NON_COUNTY = {
    "Pocahontas State Park": "Virginia DCR (state park)",
    "Presquile National Wildlife Refuge": "U.S. Fish & Wildlife (federal)",
    "Richmond National Battlefield Park": "National Park Service (federal)",
}

# Marker colors by type (county green, conservation teal, athletic blue,
# state/federal amber, everything else a neutral green).
_TYPE_COLOR = {
    "county_park": "#2e7d32",
    "conservation": "#00897b",
    "athletic": "#1565c0",
    "state": "#e08a00",
    "unknown": "#5b8c3a",
}
_TYPE_LABEL = {
    "county_park": "County park",
    "conservation": "Conservation area",
    "athletic": "Athletic complex",
    "state": "State / federal (not county-run)",
    "unknown": "Neighborhood / other park",
}


def _load() -> list:
    return json.loads(DATA.read_text(encoding="utf-8"))


def _stat_band(stats: list) -> str:
    cells = "".join(
        '<div class="ps-stat">'
        f'<div class="ps-stat__v">{html.escape(v)}</div>'
        f'<div class="ps-stat__l">{html.escape(l)}</div>'
        '</div>'
        for v, l in stats
    )
    return f'<div class="ps-stats">{cells}</div>'


# Leaflet + CARTO (theme-aware), same stack as safety.py.
_MAP_HEAD = (
    '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">'
    '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>'
)


def _legend() -> str:
    items = "".join(
        f'<span class="pk-leg"><i style="background:{_TYPE_COLOR[t]}"></i>'
        f'{html.escape(_TYPE_LABEL[t])}</span>'
        for t in ("county_park", "conservation", "athletic", "unknown", "state")
    )
    return f'<div class="pk-legend">{items}</div>'


def _map_section(points: list) -> str:
    """A Leaflet map of every park. points = [[name, lat, lon, popupHtml, color], ...].
    Tiles follow the site theme (light by default, dark when data-theme=dark)."""
    if not points:
        return ""
    data = _json.dumps(points)
    return (
        _MAP_HEAD
        + '<div id="pk-map" class="ps-map"></div>'
        + _legend()
        + '<script>(function(){if(!window.L)return;var pts=' + data + ';'
        'function tileUrl(){var dark=document.documentElement.getAttribute("data-theme")==="dark";'
        'return dark?"https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"'
        ':"https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";}'
        'var map=L.map("pk-map",{scrollWheelZoom:false}).setView([37.40,-77.55],10);'
        'var layer=L.tileLayer(tileUrl(),{attribution:"\\u00a9 OpenStreetMap \\u00a9 CARTO",'
        'subdomains:"abcd",maxZoom:19}).addTo(map);'
        'var grp=L.featureGroup();'
        'pts.forEach(function(p){'
        'L.circleMarker([p[1],p[2]],{radius:6,color:"#fff",weight:1.2,'
        'fillColor:p[4],fillOpacity:0.95}).bindPopup(p[3]).addTo(grp);});'
        'grp.addTo(map);'
        'try{if(pts.length>1){map.fitBounds(grp.getBounds().pad(0.08));}'
        'else{map.setView([pts[0][1],pts[0][2]],13);}}catch(e){}'
        'new MutationObserver(function(){layer.setUrl(tileUrl());})'
        '.observe(document.documentElement,{attributes:true,attributeFilter:["data-theme"]});'
        '})();</script>'
    )


def _sources(srcs: list) -> str:
    links = " &middot; ".join(
        f'<a href="{html.escape(u)}" target="_blank" rel="noopener">{html.escape(l)}</a>'
        for l, u in srcs
    )
    return (
        '<div class="ps-source">Figures on this page come from the county Parks &amp; '
        f'Recreation department and related official sources: {links}. The map points are '
        'derived from OpenStreetMap data (© OpenStreetMap contributors, ODbL), clipped to '
        'the Chesterfield County, Virginia boundary; they are the most complete mappable set '
        'available but do not map one-to-one onto the county’s official "67 parks" count. '
        'Check the links to verify or for the most current figures.</div>'
    )


_CSS = """<style>
.ps-wrap{max-width:820px;margin:0 auto;}
.ps-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:64ch;margin:.4rem 0 1rem;}
.ps-meta{font:var(--fw-medium) var(--fs-2xs)/1.4 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);margin-bottom:1.6rem;}
.ps-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:0 0 2.2rem;}
.ps-stat{border:1px solid var(--border);border-radius:var(--radius-xs);padding:.9rem 1rem;background:var(--surface-card);}
.ps-stat__v{font:var(--fw-bold) var(--fs-2xl)/1 var(--font-display);color:var(--accent);}
.ps-stat__l{font:var(--fs-3xs)/1.3 var(--font-sans);color:var(--text-secondary);margin-top:.35rem;}
.ps-sec{margin:2.4rem 0;}
.ps-sec h2{font:var(--fw-bold) var(--fs-xl)/1.15 var(--font-display);margin:0 0 .3rem;}
.ps-sec__dek{font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);margin:0 0 1.2rem;max-width:64ch;}
.ps-note{font:var(--fs-2xs)/1.55 var(--font-sans);color:var(--text-tertiary);margin:.4rem 0 0;max-width:64ch;}
.ps-map{height:440px;border:1px solid var(--border);border-radius:var(--radius-sm);margin:0 0 .6rem;background:var(--surface-sunken,#eee);z-index:0;}
.ps-map .leaflet-popup-content{font:var(--fs-2xs)/1.45 var(--font-sans);}
.pk-legend{display:flex;flex-wrap:wrap;gap:.4rem 1.1rem;margin:0 0 1rem;}
.pk-leg{display:inline-flex;align-items:center;gap:.4rem;font:var(--fs-3xs)/1.2 var(--font-sans);color:var(--text-secondary);}
.pk-leg i{width:11px;height:11px;border-radius:50%;border:1px solid #fff;box-shadow:0 0 0 1px var(--border);display:inline-block;}
.pk-flag{display:inline-block;font:var(--fw-bold) var(--fs-4xs,9px)/1 var(--font-mono);letter-spacing:.04em;text-transform:uppercase;color:#fff;background:#e08a00;border-radius:3px;padding:.2rem .35rem;margin-left:.4rem;vertical-align:middle;}
.ps-table{width:100%;border-collapse:collapse;margin:.4rem 0 0;}
.ps-table th{text-align:left;font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);padding:0 .6rem .5rem 0;border-bottom:1px solid var(--border);}
.ps-table td{padding:.6rem .6rem;border-bottom:1px solid var(--border);font:var(--fs-sm)/1.45 var(--font-sans);color:var(--text-secondary);vertical-align:top;}
.ps-table .pk-name{font-weight:var(--fw-semibold);color:var(--text-primary);}
.ps-table .pk-addr{font:var(--fs-2xs)/1.4 var(--font-sans);color:var(--text-tertiary);}
.pk-prog{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin:0 0 1rem;}
.pk-card{border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface-card);padding:1rem 1.1rem;}
.pk-card h3{font:var(--fw-bold) var(--fs-md)/1.2 var(--font-display);color:var(--text-primary);margin:0 0 .35rem;}
.pk-card p{font:var(--fs-sm)/1.55 var(--font-sans);color:var(--text-secondary);margin:0;}
.pk-reg{border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:var(--radius-sm);background:var(--surface-card);padding:1.1rem 1.25rem;margin:1.2rem 0 0;}
.pk-reg ul{margin:.4rem 0 0;padding-left:1.1rem;}
.pk-reg li{font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);margin:.2rem 0;}
.pk-reg a{color:var(--accent);font-weight:600;}
.ps-source{margin:2.4rem 0 0;padding:1rem 1.1rem;border-left:3px solid var(--accent);background:var(--surface-card);border-radius:var(--radius-xs);font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);}
.ps-source a{color:var(--accent);font-weight:600;}
.ps-xlinks{margin:1.6rem 0 0;font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);}
.ps-xlinks a{color:var(--accent);font-weight:600;}
@media(max-width:620px){
  .ps-stats{grid-template-columns:repeat(2,1fr);}
  .pk-prog{grid-template-columns:1fr;}
}
</style>"""


# Curated amenity blurbs for the major-parks table (research/parks-rec.md),
# keyed by the exact name as it appears in parks.json.
_AMENITIES = {
    "Harry G. Daniel Park at Iron Bridge":
        "~187 acres. 14 baseball/softball fields incl. the Diamonds at Iron Bridge "
        "complex; soccer & football fields; basketball, tennis & racquetball courts; "
        "~2.1 mi trails; playground; First Tee golf.",
    "Rockwood Park":
        "~171 acres. 5.5 mi fitness trails; 7 baseball fields; 9 tennis courts; archery "
        "range; orienteering course; Rockwood Nature Center; Ruff House Dog Park.",
    "Goyne Park":
        "18-hole disc golf; lighted baseball/softball, football & soccer fields; tennis & "
        "pickleball; playground; Chester Dog Park; recycling center.",
    "R. Garland Dodd Park at Point of Rocks":
        "~176 acres on the Appomattox River. Baseball, soccer & football fields; tennis & "
        "pickleball; ~2.7 mi trails; floating boardwalk through tidal marsh; 2 playgrounds.",
    "Matoaca Park":
        "~69 acres. Tennis courts; baseball, softball & football fields; basketball court; "
        "trail network; playground; outdoor gym equipment.",
    "Huguenot Park":
        "~53 wooded acres. Azalea garden; crushed-gravel fitness loop; tennis & basketball "
        "courts; soccer & football fields; inclusive Playground for Katie and Friends.",
    "Robious Landing Park":
        "James River access; non-motorized boat slide & floating dock; ~3.4 mi trails; "
        "fishing; river overlooks. On the VA Bird & Wildlife Trail.",
    "Mid-lothian Mines Park":
        "~1.6 mi paved/gravel trails (ADA loop); lake/pond access; historic coal-mining "
        "ruins; picnic areas.",
    "Bensley Park":
        "Co-located with Bensley Recreation Center; planned splash pad.",
    "Ettrick Park":
        "Athletic complex co-located with the Mayes-Colbert Ettrick Recreation Center.",
    "Chester Linear Park":
        "Linear greenway / trail park.",
    "Clarendon Park":
        "Neighborhood park.",
    "Fernbrook Park":
        "Neighborhood park.",
    "Gates Mill Park":
        "Historic / neighborhood park.",
    "Falling Creek Ironworks":
        "Historic ironworks site with creek/water access.",
    "Lake Chesdin Boat Landing":
        "Boat & canoe launch on ~3,000-acre Lake Chesdin (state-vs-county note: county-run "
        "launch).",
    "Appomattox River Canoe Launch":
        "Canoe/kayak launch on the Appomattox River (shares its site with the John J. "
        "Radcliffe Conservation Area).",
    "River City Sportsplex":
        "County tournament complex; 16 synthetic fields (9 lighted) for soccer/lacrosse/"
        "field hockey; 35+ tournaments a year; planned splash pad.",
    "Lowe's Athletic Complex":
        "County athletic fields.",
    "Warbro Road Athletic Complex":
        "County athletic fields.",
    "Irvin G. Horner Park":
        "County athletic complex in Moseley.",
    "Woodlake Athletic Complex":
        "Athletic complex (Woodlake).",
    "Pocahontas State Park":
        "Virginia’s largest state park (~7,900+ acres): 90+ mi trails, three lakes, "
        "camping/cabins, an amphitheater, and the seasonal Aquatic Recreation Center with "
        "water slides. State admission fee. Run by Virginia DCR, NOT the county.",
}


def _popup(rec: dict) -> str:
    name = html.escape(rec["name"])
    flag = ""
    if rec["name"] in _NON_COUNTY:
        flag = (f'<br><strong style="color:#b36b00">Not county-run — '
                f'{html.escape(_NON_COUNTY[rec["name"]])}</strong>')
    tlabel = html.escape(_TYPE_LABEL.get(rec.get("type", "unknown"), "Park"))
    addr = html.escape(rec["address"]) if rec.get("address") else ""
    addr_html = f'<br>{addr}' if addr else ""
    return f'<strong>{name}</strong>{flag}<br><em>{tlabel}</em>{addr_html}'


def _major_table(records: list) -> str:
    """Major parks that have both an address and a curated amenity blurb,
    plus any non-county sites with an address (so they appear flagged)."""
    rows = []
    seen = set()
    # Stable order: the curated major-parks list first (where present in data).
    by_name = {r["name"]: r for r in records}
    order = list(_AMENITIES.keys())
    for name in order:
        rec = by_name.get(name)
        if not rec or not rec.get("address"):
            continue
        seen.add(name)
        is_state = name in _NON_COUNTY
        flag = (f'<span class="pk-flag">Not county-run</span>' if is_state else "")
        rows.append(
            '<tr>'
            f'<td><span class="pk-name">{html.escape(name)}</span>{flag}'
            f'<div class="pk-addr">{html.escape(rec["address"])}</div></td>'
            f'<td>{html.escape(_AMENITIES[name])}</td>'
            '</tr>'
        )
    return (
        '<table class="ps-table"><thead><tr>'
        '<th>Park &amp; address</th><th>Amenities</th>'
        '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
    )


def _programs() -> str:
    cards = [
        ("Youth sports & camps",
         "Little League, soccer, basketball, football, cheer, wrestling, lacrosse, tennis "
         "and more, plus summer camps and tot/preschool programs. Many leagues run through "
         "co-sponsored community sports groups."),
        ("Active Lifestyles (50+)",
         "Fitness, Tai Chi, line dancing, luncheons, social groups and seminars for older "
         "adults, centered at the Beulah and Stonebridge recreation centers."),
        ("Therapeutic recreation",
         "Educational and recreational programs designed for residents with disabilities, "
         "offered across the county’s recreation centers."),
        ("Outdoors, arts & community",
         "Canoeing, backpacking and climbing trips; arts & crafts; nature programs at "
         "Rockwood; community gardens; and a farmers market. Over 700 programs each season."),
    ]
    grid = "".join(
        f'<div class="pk-card"><h3>{html.escape(t)}</h3><p>{html.escape(b)}</p></div>'
        for t, b in cards
    )
    reg = (
        '<div class="pk-reg"><strong>How to register</strong>'
        '<ul>'
        '<li><strong>Online:</strong> ActiveNet at '
        '<a href="https://anc.apm.activecommunities.com/chesterfieldparksrec" '
        'target="_blank" rel="noopener">anc.apm.activecommunities.com/chesterfieldparksrec</a> '
        '— create an account, register and pay by card.</li>'
        '<li><strong>By phone:</strong> 804-748-1623, Monday–Friday 8:30 a.m.–5 p.m.</li>'
        '<li><strong>In person:</strong> the administrative office at Beulah Recreation Center, '
        '6901 Hopkins Road, North Chesterfield.</li>'
        '<li><strong>Scholarships</strong> are available for Chesterfield youth under 18; '
        'refunds are issued for canceled courses or with a week’s notice.</li>'
        '</ul></div>'
    )
    return f'<div class="pk-prog">{grid}</div>{reg}'


def _page(records: list) -> str:
    points = [
        [rec["name"], rec["lat"], rec["lon"], _popup(rec),
         _TYPE_COLOR.get(rec.get("type", "unknown"), _TYPE_COLOR["unknown"])]
        for rec in records
        if isinstance(rec.get("lat"), (int, float)) and isinstance(rec.get("lon"), (int, float))
    ]
    headline = [
        ("67", "public parks"),
        ("~5,100", "acres of parkland"),
        ("44 mi", "of trails"),
        ("4", "recreation centers"),
    ]
    state_names = ", ".join(html.escape(n) for n in _NON_COUNTY)
    lead = (
        "Chesterfield County runs one of the larger park systems in the Richmond region: "
        "67 public parks, a dozen athletic complexes and about 44 miles of trails across "
        "roughly 5,100 acres, bounded by the James River to the north and the Appomattox to "
        "the south. Below is a map of every park we can plot, the major parks and their "
        "amenities, and how to sign up for programs."
    )
    sources = [
        ("Chesterfield Parks & Recreation", "https://www.chesterfield.gov/150/Parks-and-Recreation"),
        ("About / system overview", "https://www.chesterfield.gov/164/About"),
        ("Parks & Facilities", "https://www.chesterfield.gov/163/Parks-and-Facilities"),
        ("Programs", "https://www.chesterfield.gov/161/Programs"),
        ("Recreation Centers", "https://www.chesterfield.gov/861/Recreation-Centers"),
        ("Online registration (ActiveNet)", "https://anc.apm.activecommunities.com/chesterfieldparksrec"),
        ("Pocahontas State Park (VA DCR)", "https://www.dcr.virginia.gov/state-parks/pocahontas"),
    ]
    return (
        _CSS
        + '<div class="ps-wrap">'
        + '<h1 class="page-title">Parks &amp; Recreation</h1>'
        + '<div class="ps-meta">Chesterfield County, Virginia</div>'
        + f'<p class="ps-lead">{html.escape(lead)}</p>'
        + _stat_band(headline)
        + '<div class="ps-sec"><h2>Every park on the map</h2>'
        + f'<p class="ps-sec__dek">Markers are colored by who runs the site. A handful '
          f'of large parks inside or along the county line are state- or federally run '
          f'— {state_names} — and are flagged in amber; they are <strong>not</strong> '
          f'Chesterfield County Parks &amp; Recreation sites.</p>'
        + _map_section(points)
        + f'<p class="ps-note">{len(points)} mappable points from OpenStreetMap, typed by '
          'category. This is the most complete plottable set we have; it is not an exact '
          'one-to-one with the county’s official 67-park count.</p>'
        + '</div>'
        + '<div class="ps-sec"><h2>Major parks &amp; what’s there</h2>'
        + '<p class="ps-sec__dek">The larger regional and community parks, their addresses '
          'and headline amenities. State-run sites are labeled.</p>'
        + _major_table(records)
        + '</div>'
        + '<div class="ps-sec"><h2>Programs &amp; registration</h2>'
        + '<p class="ps-sec__dek">The department offers more than 700 programs a season, '
          'from youth leagues to 50-plus fitness to therapeutic recreation.</p>'
        + _programs()
        + '</div>'
        + _sources(sources)
        + '<div class="ps-xlinks">Related: <a href="/taxes.html">Where your taxes go</a> '
          '&middot; <a href="/board.html">Board of Supervisors</a></div>'
        + '</div>'
    )


def build_parks() -> Path:
    records = _load()
    body = _page(records)
    page = render._shell(body)
    page = render._inject_og(
        page,
        "Chesterfield Parks & Recreation: parks map, amenities, and programs",
        "A map of every Chesterfield County park, the major parks and their amenities, and "
        "how to register for youth sports, camps, Active Lifestyles 50+ and therapeutic "
        "recreation. State parks like Pocahontas are flagged as not county-run.",
        f"{render.SITE_URL}/parks.html", og_type="website",
        page_title="Parks & Recreation | The Chesterfield Report")
    out = PUBLIC / "parks.html"
    out.write_text(page, encoding="utf-8")
    return out
