"""Data Center Tracker for The Chesterfield Report.

Builds public/data-centers.html from pipeline/datacenters.json: a standing
tracker of every data-center project in Chesterfield County. A summary strip
(projects, approvals, acreage, headline investment), a Leaflet map of project
sites colored by status, a per-project card section (status badge, timeline of
key dates, related coverage, county case links), and a "Latest data-center
news" list auto-populated from published stories.

Facts in datacenters.json trace to the site's own published stories (slugs in
each entry's "stories" list) and research/data-centers.md. Statuses that are
not clearly documented stay "under review" with the sourcing story linked.

Reuses render._shell() / _inject_og / _article_cta. Leaflet map follows the
parks.py / safety.py pattern (theme-aware CARTO tiles, circleMarkers,
fitBounds). Stdlib only.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

from . import render
from .render import PUBLIC

DATA = Path(__file__).resolve().parents[1] / "datacenters.json"

# Marker + badge colors by status.
_STATUS_COLOR = {
    "approved": "#2e7d32",
    "under construction": "#1565c0",
    "under review": "#e08a00",
    "proposed": "#8e6bbf",
    "paused": "#946200",
    "denied": "#c62828",
    "withdrawn": "#757575",
}
_STATUS_ORDER = ["under construction", "approved", "under review", "proposed",
                 "paused", "denied", "withdrawn"]


def _load() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def _status_color(status: str) -> str:
    return _STATUS_COLOR.get((status or "").lower(), "#757575")


def _badge(status: str) -> str:
    return (f'<span class="dc-badge" style="background:{_status_color(status)}">'
            f'{html.escape(status)}</span>')


# --- published-story helpers -----------------------------------------------

_DC_TAGS = {"data centers", "data center"}
_DC_KEYWORDS = ("data center", "data-center", "datacenter")


def _is_dc_story(meta: dict) -> bool:
    tags = [t.strip().lower() for t in
            (meta.get("tags", "") or "").strip("[]").split(",")]
    if _DC_TAGS & set(tags):
        return True
    hay = (meta.get("headline", "") + " " + meta.get("location", "")).lower()
    return any(k in hay for k in _DC_KEYWORDS)


def _dc_stories() -> list:
    """[(md_filename_no_ext, headline, date_iso, url)] newest first."""
    out = []
    for meta, _body, name in render._published_records():
        if not _is_dc_story(meta):
            continue
        headline = meta.get("headline", "")
        out.append((name[:-3] if name.endswith(".md") else name,
                    headline,
                    (meta.get("published", "") or "")[:10],
                    render.story_url(headline)))
    out.sort(key=lambda r: r[2], reverse=True)
    return out


# --- sections ---------------------------------------------------------------

def _stat_band(stats: list) -> str:
    cells = "".join(
        '<div class="ps-stat">'
        f'<div class="ps-stat__v">{html.escape(v)}</div>'
        f'<div class="ps-stat__l">{html.escape(l)}</div>'
        '</div>'
        for v, l in stats
    )
    return f'<div class="ps-stats">{cells}</div>'


_MAP_HEAD = (
    '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">'
    '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>'
)


def _legend(statuses: list) -> str:
    items = "".join(
        f'<span class="pk-leg"><i style="background:{_status_color(s)}"></i>'
        f'{html.escape(s)}</span>'
        for s in _STATUS_ORDER if s in statuses
    )
    return f'<div class="pk-legend">{items}</div>'


def _popup(p: dict) -> str:
    name = html.escape(p["name"])
    status = html.escape(p.get("status", ""))
    loc = html.escape(p.get("location", ""))
    acr = p.get("acreage")
    acr_html = f"<br>~{acr:,.0f} acres" if isinstance(acr, (int, float)) else ""
    return (f'<strong>{name}</strong><br><em>{status}</em>{acr_html}'
            f'<br>{loc}<br><a href="#dc-{html.escape(p["id"])}">Details &darr;</a>')


def _map_section(projects: list) -> str:
    points = [
        [p["name"], p["lat"], p["lon"], _popup(p), _status_color(p.get("status", ""))]
        for p in projects
        if isinstance(p.get("lat"), (int, float)) and isinstance(p.get("lon"), (int, float))
    ]
    if not points:
        return ""
    statuses = sorted({(p.get("status") or "").lower() for p in projects})
    data = json.dumps(points)
    return (
        _MAP_HEAD
        + '<div id="dc-map" class="ps-map"></div>'
        + _legend(statuses)
        + '<script>(function(){if(!window.L)return;var pts=' + data + ';'
        'function tileUrl(){var dark=document.documentElement.getAttribute("data-theme")==="dark";'
        'return dark?"https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"'
        ':"https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";}'
        'var map=L.map("dc-map",{scrollWheelZoom:false}).setView([37.40,-77.55],10);'
        'var layer=L.tileLayer(tileUrl(),{attribution:"\\u00a9 OpenStreetMap \\u00a9 CARTO",'
        'subdomains:"abcd",maxZoom:19}).addTo(map);'
        'var grp=L.featureGroup();'
        'pts.forEach(function(p){'
        'L.circleMarker([p[1],p[2]],{radius:8,color:"#fff",weight:1.4,'
        'fillColor:p[4],fillOpacity:0.95}).bindPopup(p[3]).addTo(grp);});'
        'grp.addTo(map);'
        'try{if(pts.length>1){map.fitBounds(grp.getBounds().pad(0.12));}'
        'else{map.setView([pts[0][1],pts[0][2]],12);}}catch(e){}'
        'new MutationObserver(function(){layer.setUrl(tileUrl());})'
        '.observe(document.documentElement,{attributes:true,attributeFilter:["data-theme"]});'
        '})();</script>'
    )


def _timeline(key_dates: list) -> str:
    if not key_dates:
        return ""
    rows = []
    for kd in key_dates:
        date = html.escape(kd.get("date", ""))
        event = html.escape(kd.get("event", ""))
        src = (kd.get("source") or "").strip()
        if src.startswith("http"):
            event += (f' <a class="dc-src" href="{html.escape(src)}" target="_blank" '
                      'rel="noopener">[source]</a>')
        rows.append(f'<li><span class="dc-tl__d">{date}</span>'
                    f'<span class="dc-tl__e">{event}</span></li>')
    return '<ul class="dc-tl">' + "".join(rows) + '</ul>'


def _related_links(p: dict, story_index: dict) -> str:
    """Coverage links (matched by md filename) + county case links (only when
    the case page actually exists) + /development.html."""
    links = []
    for slug in p.get("stories", []):
        rec = story_index.get(slug)
        if rec:
            _fn, headline, date, url = rec
            links.append(f'<a href="{html.escape(url)}">{html.escape(headline)}</a>')
    for cid in p.get("case_ids", []):
        case_slug = cid.replace("-", "").lower()
        if (PUBLIC / "cases" / f"{case_slug}.html").exists():
            links.append(f'<a href="/cases/{case_slug}.html">County case {html.escape(cid)}</a>')
        else:
            links.append(f'<span class="dc-caseid">Case {html.escape(cid)}</span>')
    if not links:
        return ""
    return ('<div class="dc-rel"><strong>Related:</strong> '
            + " &middot; ".join(links) + '</div>')


def _project_card(p: dict, story_index: dict) -> str:
    name = html.escape(p["name"])
    op = html.escape(p.get("operator", ""))
    loc = html.escape(p.get("location", ""))
    acr = p.get("acreage")
    facts = []
    if op:
        facts.append(f"<strong>Operator:</strong> {op}")
    if isinstance(acr, (int, float)):
        facts.append(f"<strong>Size:</strong> ~{acr:,.0f} acres")
    if loc:
        facts.append(f"<strong>Where:</strong> {loc}")
    facts_html = "".join(f'<div class="dc-fact">{f}</div>' for f in facts)
    notes = (p.get("notes") or "").strip()
    notes_html = f'<p class="dc-notes">{html.escape(notes)}</p>' if notes else ""
    return (
        f'<article class="dc-card" id="dc-{html.escape(p["id"])}">'
        f'<div class="dc-card__head"><h3>{name}</h3>{_badge(p.get("status", ""))}</div>'
        f'<div class="dc-facts">{facts_html}</div>'
        + notes_html
        + _timeline(p.get("key_dates", []))
        + _related_links(p, story_index)
        + '</article>'
    )


def _news_list(stories: list) -> str:
    if not stories:
        return '<p class="ps-note">No data-center stories yet.</p>'
    items = "".join(
        f'<li><a href="{html.escape(url)}">{html.escape(headline)}</a>'
        f'<span class="dc-news__d">{html.escape(render._pretty_date(date))}</span></li>'
        for _fn, headline, date, url in stories
    )
    return f'<ul class="dc-news">{items}</ul>'


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
.pk-leg{display:inline-flex;align-items:center;gap:.4rem;font:var(--fs-3xs)/1.2 var(--font-sans);color:var(--text-secondary);text-transform:capitalize;}
.pk-leg i{width:11px;height:11px;border-radius:50%;border:1px solid #fff;box-shadow:0 0 0 1px var(--border);display:inline-block;}
.dc-card{border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface-card);padding:1.1rem 1.25rem;margin:0 0 1.1rem;}
.dc-card__head{display:flex;align-items:center;gap:.7rem;flex-wrap:wrap;margin:0 0 .55rem;}
.dc-card__head h3{font:var(--fw-bold) var(--fs-lg)/1.2 var(--font-display);color:var(--text-primary);margin:0;}
.dc-badge{display:inline-block;font:var(--fw-bold) var(--fs-4xs,10px)/1 var(--font-mono);letter-spacing:.05em;text-transform:uppercase;color:#fff;border-radius:3px;padding:.28rem .45rem;}
.dc-facts{display:flex;flex-wrap:wrap;gap:.25rem 1.4rem;margin:0 0 .5rem;}
.dc-fact{font:var(--fs-2xs)/1.5 var(--font-sans);color:var(--text-secondary);}
.dc-notes{font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);margin:.3rem 0 .6rem;max-width:66ch;}
.dc-tl{list-style:none;margin:.6rem 0;padding:0 0 0 .2rem;border-left:2px solid var(--border);}
.dc-tl li{display:flex;gap:.8rem;padding:.28rem 0 .28rem .8rem;font:var(--fs-2xs)/1.5 var(--font-sans);color:var(--text-secondary);}
.dc-tl__d{flex:0 0 6.2em;font-family:var(--font-mono);color:var(--text-tertiary);}
.dc-tl__e{flex:1;}
.dc-src{color:var(--accent);font-weight:600;}
.dc-rel{font:var(--fs-2xs)/1.7 var(--font-sans);color:var(--text-tertiary);margin:.5rem 0 0;padding-top:.5rem;border-top:1px dashed var(--border);}
.dc-rel a{color:var(--accent);font-weight:600;}
.dc-caseid{font-family:var(--font-mono);}
.dc-news{list-style:none;margin:.4rem 0 0;padding:0;}
.dc-news li{display:flex;align-items:baseline;gap:.9rem;justify-content:space-between;padding:.5rem 0;border-bottom:1px solid var(--border);font:var(--fs-sm)/1.45 var(--font-sans);}
.dc-news a{color:var(--text-primary);font-weight:var(--fw-semibold);}
.dc-news a:hover{color:var(--accent);}
.dc-news__d{flex:none;font:var(--fs-3xs)/1.3 var(--font-mono);color:var(--text-tertiary);white-space:nowrap;}
.ps-source{margin:2.4rem 0 0;padding:1rem 1.1rem;border-left:3px solid var(--accent);background:var(--surface-card);border-radius:var(--radius-xs);font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);}
.ps-source a{color:var(--accent);font-weight:600;}
.ps-xlinks{margin:1.6rem 0 0;font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);}
.ps-xlinks a{color:var(--accent);font-weight:600;}
@media(max-width:620px){
  .ps-stats{grid-template-columns:repeat(2,1fr);}
  .dc-news li{flex-direction:column;gap:.15rem;}
}
</style>"""


def _summary_stats(data: dict, projects: list) -> list:
    n = len(projects)
    approved = sum(1 for p in projects
                   if (p.get("status") or "").lower() in ("approved", "under construction"))
    acres = sum(p.get("acreage") or 0 for p in projects)
    invest = data.get("summary", {}).get("headline_investment", "")
    return [
        (str(n), "projects tracked"),
        (str(approved), "approved or building"),
        (f"~{acres:,.0f}", "acres involved"),
        (invest or "n/a", "announced investment"),
    ]


def _page(data: dict) -> str:
    projects = data.get("projects", [])
    # Newest development first: sort by most recent key date, descending.
    projects = sorted(
        projects,
        key=lambda p: max((kd.get("date", "") for kd in p.get("key_dates", [])),
                          default=""),
        reverse=True)
    stories = _dc_stories()
    story_index = {fn: rec for rec in stories for fn in [rec[0]]}
    lead = data.get("summary", {}).get("lead", "")
    updated = data.get("summary", {}).get("updated", "")
    cards = "".join(_project_card(p, story_index) for p in projects)
    src_comment = ("<!-- Sources: this tracker is compiled from The Chesterfield "
                   "Report's published stories (slugs: "
                   + ", ".join(sorted({s for p in projects for s in p.get("stories", [])}))
                   + ") and research/data-centers.md -->")
    return (
        _CSS
        + src_comment
        + '<div class="ps-wrap">'
        + '<h1 class="page-title">Data Center Tracker</h1>'
        + f'<div class="ps-meta">Chesterfield County, Virginia &middot; updated {html.escape(updated)}</div>'
        + f'<p class="ps-lead">{html.escape(lead)}</p>'
        + _stat_band(_summary_stats(data, projects))
        + '<div class="ps-sec"><h2>Where the projects are</h2>'
        + '<p class="ps-sec__dek">Every data-center campus we are tracking, colored by '
          'status. Tap a marker for details and jump to the full entry below.</p>'
        + _map_section(projects)
        + '<p class="ps-note">Markers show approximate site areas, not exact parcel '
          'boundaries. One project (WestDulles, James River Industrial Center) has no '
          'precise mappable location yet.</p>'
        + '</div>'
        + '<div class="ps-sec"><h2>Project by project</h2>'
        + '<p class="ps-sec__dek">Each entry shows the current status, a timeline of key '
          'dates, and links to our coverage and the county case file where one exists. '
          'Where a project’s current standing is not clearly documented we mark it '
          '“under review” and link the reporting we have.</p>'
        + cards
        + '</div>'
        + '<div class="ps-sec"><h2>Latest data-center news</h2>'
        + '<p class="ps-sec__dek">Every data-center story we have published, newest '
          'first. This list updates automatically as we publish.</p>'
        + _news_list(stories)
        + '</div>'
        + render._article_cta("en")
        + '<div class="ps-source">This tracker is compiled from The Chesterfield '
          'Report’s own published reporting (linked above) and public records: '
          'Chesterfield County planning and zoning files, Board of Supervisors actions, '
          'and U.S. Army Corps of Engineers permit filings. Statuses reflect the most '
          'recent documented action; see each project’s linked coverage. Spot an '
          'error or know something we don’t? '
          '<a href="/tip.html">Send a tip</a>.</div>'
        + '<div class="ps-xlinks">Related: '
          '<a href="/development.html">Development &amp; Zoning cases</a> &middot; '
          '<a href="/board.html">Board of Supervisors</a> &middot; '
          '<a href="/meetings.html">Meetings calendar</a></div>'
        + '</div>'
    )


def build_datacenters() -> Path:
    data = _load()
    body = _page(data)
    page = render._shell(body)
    page = render._inject_og(
        page,
        "Chesterfield Data Center Tracker",
        "Every data-center project in Chesterfield County, Virginia in one place: "
        "Google's $9 billion three-campus buildout, what's approved, denied, or under "
        "review, a map of the sites, key dates, and all of our coverage.",
        f"{render.SITE_URL}/data-centers.html", og_type="website")
    out = PUBLIC / "data-centers.html"
    out.write_text(page, encoding="utf-8")
    print(f"Built {out.name} ({len(data.get('projects', []))} projects)")
    return out
