"""Development & Zoning Cases tracker.

Pulls Chesterfield County's live "Active Development and Zoning Cases" data from
the county ArcGIS feature service (Planning_ProdA/FeatureServer/21, ZoningCases),
decodes the coded fields, and builds:

  * /development.html  — a filterable index with a map of every current case.
  * /cases/<casenum>.html — a per-case page: what is proposed, where, the status
    pipeline (filed -> review -> community meeting -> staff report -> Planning
    Commission -> Board of Supervisors -> decision), acreage, proposed units,
    proffers/conditions, and links to the county record.

This is Tier 1 (structured data, no AI). A later pass adds the staff-report PDF
read for the deep "who / why" (applicant, proffers, conditions, narrative).

Stdlib only. Network fetch is best-effort: any failure leaves the existing pages
in place (build_cases returns gracefully). Reuses render._shell().
"""
from __future__ import annotations

import datetime
import html
import json
import ssl
import urllib.parse
import urllib.request
from pathlib import Path

from . import render
from .render import PUBLIC

SERVICE = ("https://services3.arcgis.com/TsynfzBSE6sXfoLq/arcgis/rest/services/"
           "Planning_ProdA/FeatureServer/21")
COUNTY_CASES_URL = "https://www.chesterfield.gov/982/Active-Development-and-Zoning-Cases"
UA = "ChesterfieldReport/0.1 (+brucker.rob@gmail.com)"

# Statuses that mean the case is still moving through the process (what the
# county's public "active cases" map shows). Final/closed states are excluded
# from the index but still get a per-case page.
_CLOSED = {"Approved", "Denied", "Withdrawn", "Voided", "Expired", "NotAvailable"}

# The review pipeline, in order. Each county status code maps to one stage so we
# can render a "where is it now" progress bar.
_PIPELINE = [
    ("Filed", {"Pending", "AppReview", "FeePayment", "FirstGlanceRev", "AdminRev"}),
    ("Review", {"TechReview", "Review", "StaffDevMtg"}),
    ("Community meeting", {"CommMeeting"}),
    ("Staff report", {"StaffReport"}),
    ("Planning Commission", {"CPCHearing", "CpcApproved", "CpcDenied"}),
    ("Board of Supervisors", {"BOSHearing", "BZAHearing"}),
    ("Decision", {"Approved", "Denied", "Deferred", "OnHold", "Recordation",
                  "Remanded", "Withdrawn", "Voided", "Expired"}),
]


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=45,
                                  context=ssl.create_default_context()).read()


def _domains() -> dict:
    meta = json.loads(_get(SERVICE + "?f=json"))
    out = {}
    for f in meta.get("fields", []):
        cv = (f.get("domain") or {}).get("codedValues")
        if cv:
            out[f["name"]] = {c["code"]: c["name"] for c in cv}
    return out


def _centroid(geom: dict | None):
    if not geom:
        return (None, None)
    t = geom.get("type")
    ring = (geom["coordinates"][0] if t == "Polygon"
            else geom["coordinates"][0][0] if t == "MultiPolygon" else None)
    if not ring:
        return (None, None)
    pts = ring[:-1] if ring[0] == ring[-1] else ring
    return (round(sum(p[1] for p in pts) / len(pts), 6),
            round(sum(p[0] for p in pts) / len(pts), 6))


def _date(ms) -> str:
    """Epoch-ms (ArcGIS date) -> 'Mon D, YYYY', or '' if absent."""
    if not ms:
        return ""
    try:
        return datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc).strftime("%b %-d, %Y")
    except (ValueError, OverflowError, OSError):
        return ""


def _stage_index(status_code: str) -> int:
    for i, (_, codes) in enumerate(_PIPELINE):
        if status_code in codes:
            return i
    return 0


def _slug(casenum: str) -> str:
    return casenum.lower().strip()


def fetch_cases() -> list[dict]:
    """Fetch current-year zoning cases, decoded, with map coords. Returns []
    on any network/parse error (build stays graceful)."""
    try:
        dom = _domains()
        year2 = datetime.datetime.now(datetime.timezone.utc).strftime("%y")
        where = urllib.parse.quote(f"CaseNum LIKE '{year2}%'")
        q = (f"/query?where={where}&outFields=*&orderByFields=OBJECTID+DESC"
             "&returnGeometry=true&outSR=4326&f=geojson")
        gj = json.loads(_get(SERVICE + q))
    except Exception as e:  # noqa: BLE001 — best-effort ingest
        print(f"  ! cases fetch failed: {e}")
        return []

    cases = []
    for ft in gj.get("features", []):
        p = ft.get("properties", {})
        casenum = (p.get("CaseNum") or "").strip()
        if not casenum:
            continue
        lat, lon = _centroid(ft.get("geometry"))
        status_code = p.get("Status") or ""
        units = {
            "Single-family": p.get("SingleFamilyUnits") or 0,
            "Townhouse": p.get("TownhouseUnits") or 0,
            "Condo": p.get("CondoUnits") or 0,
            "Apartment": p.get("ApartmentUnits") or 0,
        }
        cases.append({
            "casenum": casenum,
            "slug": _slug(casenum),
            "name": (p.get("CaseName") or casenum).strip().title(),
            "request": dom.get("RequestType", {}).get(p.get("RequestType"), p.get("RequestType") or ""),
            "review_body": dom.get("CaseType", {}).get(p.get("CaseType"), p.get("CaseType") or ""),
            "status": dom.get("Status", {}).get(status_code, status_code),
            "status_code": status_code,
            "stage": _stage_index(status_code),
            "description": (p.get("CaseDescription") or "").strip(),
            "acres": p.get("Acres"),
            "units": {k: v for k, v in units.items() if v},
            "total_units": sum(units.values()),
            "proffers": bool(p.get("Proffers")),
            "conditions": bool(p.get("Conditions")),
            "cash_proffer": bool(p.get("CashProffer")),
            "anticipated": _date(p.get("AnticipatedDate")),
            "final": _date(p.get("FinalDate")),
            "lat": lat, "lon": lon,
            "closed": status_code in _CLOSED,
        })
    return cases


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

_CSS = """<style>
.cz-wrap{max-width:1000px;margin:0 auto;}
.cz-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);
  max-width:64ch;margin:.4rem 0 1.2rem;}
#cz-map{height:420px;border-radius:var(--radius-sm);overflow:hidden;margin:0 0 1.2rem;
  border:1px solid var(--border);}
.cz-controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:0 0 1.2rem;}
#cz-search{flex:1;min-width:220px;padding:.6rem .8rem;border:1px solid var(--border);
  border-radius:var(--radius-xs);background:var(--surface-card);color:var(--text-primary);
  font:var(--fs-sm) var(--font-sans);}
.cz-filter{display:flex;flex-wrap:wrap;gap:6px;}
.cz-filter button{padding:.5rem .85rem;border:1px solid var(--border);background:var(--surface-card);
  color:var(--text-secondary);border-radius:999px;font:var(--fw-semibold) var(--fs-2xs) var(--font-sans);cursor:pointer;}
.cz-filter button.is-on{background:var(--accent);color:#fff;border-color:var(--accent);}
.cz-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px;}
.cz-card{border:1px solid var(--border);border-radius:var(--radius-sm);padding:1rem 1.1rem;
  background:var(--surface-card);display:block;color:inherit;text-decoration:none;}
.cz-card:hover{border-color:var(--accent);}
.cz-tag{display:inline-block;font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);
  text-transform:uppercase;color:var(--accent);}
.cz-name{font:var(--fw-bold) var(--fs-md)/1.2 var(--font-display);margin:.35rem 0 .3rem;}
.cz-meta{font:var(--fs-2xs)/1.5 var(--font-sans);color:var(--text-tertiary);}
.cz-status{display:inline-block;margin-top:.5rem;font:var(--fw-semibold) var(--fs-2xs) var(--font-sans);
  color:var(--text-secondary);border:1px solid var(--border);border-radius:999px;padding:.2rem .55rem;}
.cz-summary{font:var(--fs-2xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;
  color:var(--text-tertiary);margin:0 0 1rem;}
/* per-case page */
.cz-back{font:var(--fw-semibold) var(--fs-2xs) var(--font-sans);color:var(--accent);text-transform:uppercase;letter-spacing:var(--ls-wide);}
.cz-h1{font:var(--fw-bold) var(--fs-2xl)/1.1 var(--font-display);margin:.4rem 0 .2rem;}
.cz-sub{font:var(--fs-sm) var(--font-mono);color:var(--text-tertiary);margin:0 0 1rem;}
.cz-facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:1.2rem 0;}
.cz-fact{border:1px solid var(--border);border-radius:var(--radius-xs);padding:.7rem .85rem;background:var(--surface-card);}
.cz-fact b{display:block;font:var(--fw-bold) var(--fs-lg)/1 var(--font-display);color:var(--accent);}
.cz-fact span{font:var(--fs-2xs)/1.3 var(--font-sans);color:var(--text-secondary);}
.cz-pipe{display:flex;flex-wrap:wrap;gap:0;margin:1.4rem 0;}
.cz-step{flex:1;min-width:90px;text-align:center;padding:.5rem .3rem;border-top:3px solid var(--border);
  font:var(--fs-3xs)/1.3 var(--font-sans);color:var(--text-tertiary);}
.cz-step.done{border-top-color:var(--accent);color:var(--text-secondary);}
.cz-step.now{border-top-color:var(--accent);color:var(--accent);font-weight:700;}
#cz-onemap{height:300px;border-radius:var(--radius-sm);overflow:hidden;border:1px solid var(--border);margin:1rem 0;}
.cz-links{margin:1.4rem 0;font:var(--fs-sm)/1.7 var(--font-sans);}
.cz-links a{color:var(--accent);font-weight:600;}
.cz-src{margin-top:2rem;padding:1rem 1.1rem;border-left:3px solid var(--accent);background:var(--surface-card);
  border-radius:var(--radius-xs);font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);}
.cz-src a{color:var(--accent);font-weight:600;}
@media(max-width:560px){#cz-map{height:320px;}}
</style>"""

_MAP_JS = """
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
<div id="__MAPID__"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
(function(){
  if(!window.L) return;
  var pts=__DATA__, single=__SINGLE__;
  function tile(){var l=document.documentElement.getAttribute('data-theme')==='light';
    return l?'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png':'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';}
  var map=L.map('__MAPID__',{scrollWheelZoom:false}).setView([37.41,-77.59], single?14:11);
  var layer=L.tileLayer(tile(),{attribution:'&copy; OpenStreetMap &copy; CARTO',subdomains:'abcd',maxZoom:19}).addTo(map);
  var grp=single?L.layerGroup():L.markerClusterGroup({maxClusterRadius:40,showCoverageOnHover:false});
  pts.forEach(function(p){
    var h='<strong>'+p[0]+'</strong>'+(p[3]?'<br>'+p[3]:'')+(p[4]?'<br><a href="'+p[4]+'">View case</a>':'');
    L.circleMarker([p[1],p[2]],{radius:8,color:'#fff',weight:1.5,fillColor:'#9a3322',fillOpacity:.9}).bindPopup(h).addTo(grp);
  });
  map.addLayer(grp);
  if(single&&pts.length){map.setView([pts[0][1],pts[0][2]],15);}
  new MutationObserver(function(){layer.setUrl(tile());}).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
})();
</script>
"""


def _map(points: list, mapid: str, single: bool) -> str:
    if not points:
        return ""
    return (_MAP_JS.replace("__MAPID__", mapid)
            .replace("__DATA__", json.dumps(points, separators=(",", ":")))
            .replace("__SINGLE__", "true" if single else "false"))


def _pipeline_html(stage: int, closed: bool) -> str:
    out = []
    for i, (label, _) in enumerate(_PIPELINE):
        cls = "now" if i == stage else ("done" if i < stage else "")
        out.append(f'<div class="cz-step {cls}">{html.escape(label)}</div>')
    return f'<div class="cz-pipe">{"".join(out)}</div>'


def _case_page(c: dict) -> str:
    facts = []
    if c["request"]:
        facts.append(f'<div class="cz-fact"><b>{html.escape(c["request"])}</b><span>Request type</span></div>')
    if c["acres"]:
        facts.append(f'<div class="cz-fact"><b>{c["acres"]:g}</b><span>Acres</span></div>')
    if c["total_units"]:
        facts.append(f'<div class="cz-fact"><b>{c["total_units"]}</b><span>Proposed homes</span></div>')
    if c["anticipated"]:
        facts.append(f'<div class="cz-fact"><b>{html.escape(c["anticipated"])}</b><span>Next hearing</span></div>')

    unit_lines = ""
    if c["units"]:
        unit_lines = "<p>" + " · ".join(f"{v} {k.lower()}" for k, v in c["units"].items()) + "</p>"
    flags = []
    if c["proffers"]:
        flags.append("proffers")
    if c["conditions"]:
        flags.append("conditions")
    if c["cash_proffer"]:
        flags.append("cash proffer")
    flags_html = f'<p class="cz-meta">Includes: {", ".join(flags)}.</p>' if flags else ""

    pts = [[c["name"], c["lat"], c["lon"], html.escape(c["request"]), ""]] if c["lat"] else []

    body = (
        _CSS
        + '<div class="cz-wrap">'
        + '<a class="cz-back" href="/development.html">&larr; All cases</a>'
        + f'<h1 class="cz-h1">{html.escape(c["name"])}</h1>'
        + f'<p class="cz-sub">Case {html.escape(c["casenum"])} &middot; {html.escape(c["review_body"])}</p>'
        + (f'<p class="cz-lead">Proposed: {html.escape(c["description"])}.</p>' if c["description"] else "")
        + (f'<div class="cz-facts">{"".join(facts)}</div>' if facts else "")
        + unit_lines + flags_html
        + '<h2 style="font-family:var(--font-display);margin-top:1.6rem;">Where it is in the process</h2>'
        + f'<p class="cz-meta">Current status: <strong>{html.escape(c["status"])}</strong></p>'
        + _pipeline_html(c["stage"], c["closed"])
        + (_map(pts, "cz-onemap", True) if pts else "")
        + '<div class="cz-links">'
          f'<a href="{COUNTY_CASES_URL}" target="_blank" rel="noopener">County case viewer ↗</a><br>'
          '<a href="https://www.chesterfield.gov/list.aspx?ListID=399" target="_blank" rel="noopener">'
          'Get planning email alerts ↗</a>'
          '</div>'
        + '<div class="cz-src">Case data is from Chesterfield County&rsquo;s '
          f'<a href="{COUNTY_CASES_URL}" target="_blank" rel="noopener">Active Development and Zoning Cases</a> '
          'and updates daily. Figures are the county&rsquo;s official record. Always confirm details and '
          'hearing dates with the county before acting.</div>'
        + '</div>'
    )
    page = render._shell(body)
    page = render._inject_og(page, f"{c['name']} ({c['casenum']})",
                             f"{c['request']} on {c['acres']:g} acres in Chesterfield County. Status: {c['status']}."
                             if c["acres"] else f"{c['request']} in Chesterfield County. Status: {c['status']}.",
                             f"https://chesterfieldreport.com/cases/{c['slug']}.html")
    return page


def _index_card(c: dict) -> str:
    bits = []
    if c["acres"]:
        bits.append(f"{c['acres']:g} ac")
    if c["total_units"]:
        bits.append(f"{c['total_units']} homes")
    if c["anticipated"]:
        bits.append(f"hearing {c['anticipated']}")
    key = html.escape(f'{c["name"]} {c["casenum"]} {c["request"]} {c["description"]}'.lower(), quote=True)
    return (
        f'<a class="cz-card" href="/cases/{c["slug"]}.html" data-stage="{c["stage"]}" data-search="{key}">'
        f'<span class="cz-tag">{html.escape(c["request"] or "Case")}</span>'
        f'<div class="cz-name">{html.escape(c["name"])}</div>'
        f'<div class="cz-meta">{html.escape(" · ".join(bits)) if bits else html.escape(c["casenum"])}</div>'
        f'<span class="cz-status">{html.escape(c["status"])}</span>'
        '</a>'
    )


_FILTER_JS = """
<script>
(function(){
  var s=document.getElementById('cz-search'),btns=[].slice.call(document.querySelectorAll('.cz-filter button')),
      cards=[].slice.call(document.querySelectorAll('.cz-card')),stage='all';
  function apply(){var q=(s.value||'').trim().toLowerCase(),n=0;
    cards.forEach(function(c){var okS=stage==='all'||c.getAttribute('data-stage')===stage,
      okQ=!q||c.getAttribute('data-search').indexOf(q)!==-1,on=okS&&okQ;c.style.display=on?'':'none';if(on)n++;});
    document.getElementById('cz-count').textContent=n;}
  btns.forEach(function(b){b.addEventListener('click',function(){btns.forEach(function(x){x.classList.remove('is-on');});
    b.classList.add('is-on');stage=b.getAttribute('data-stage');apply();});});
  s.addEventListener('input',apply);
})();
</script>
"""


def build_cases() -> Path | None:
    """Build /development.html + per-case pages. Graceful: if the fetch returns
    nothing, leaves any existing pages untouched and returns None."""
    cases = fetch_cases()
    if not cases:
        return None

    # Per-case pages.
    cdir = PUBLIC / "cases"
    cdir.mkdir(parents=True, exist_ok=True)
    for c in cases:
        (cdir / f"{c['slug']}.html").write_text(_case_page(c), encoding="utf-8")

    # Index: active (non-closed) cases on the map + cards.
    active = [c for c in cases if not c["closed"]]
    pts = [[c["name"], c["lat"], c["lon"], html.escape(c["request"]),
            f"/cases/{c['slug']}.html"] for c in active if c["lat"]]

    # Filter buttons by pipeline stage (only stages that have cases).
    stages_present = sorted({c["stage"] for c in active})
    fbtns = '<button class="is-on" data-stage="all">All</button>' + "".join(
        f'<button data-stage="{i}">{html.escape(_PIPELINE[i][0])}</button>' for i in stages_present)

    cards = "".join(_index_card(c) for c in sorted(active, key=lambda c: (c["stage"], c["name"])))

    body = (
        _CSS
        + '<div class="cz-wrap">'
        + '<h1 class="page-title">Development & Zoning Cases</h1>'
        + f'<p class="cz-lead">Every active rezoning, conditional use, and development case in '
          f'Chesterfield County right now — {len(active)} of them — with what is proposed, where, '
          'and where each stands in the approval process. Updated daily from county records.</p>'
        + _map(pts, "cz-map", False)
        + '<div class="cz-controls">'
          '<input id="cz-search" type="search" placeholder="Search cases, streets, type…" aria-label="Search cases">'
          f'<div class="cz-filter">{fbtns}</div></div>'
        + f'<p class="cz-summary"><span id="cz-count">{len(active)}</span> active cases</p>'
        + f'<div class="cz-grid">{cards}</div>'
        + '<div class="cz-src">Data from the county&rsquo;s '
          f'<a href="{COUNTY_CASES_URL}" target="_blank" rel="noopener">Active Development and Zoning Cases</a>, '
          'updated daily. Track new filings with '
          '<a href="https://www.chesterfield.gov/list.aspx?ListID=399" target="_blank" rel="noopener">county planning alerts</a>.</div>'
        + '</div>'
        + _FILTER_JS
    )
    page = render._shell(body)
    page = render._inject_og(page, "Chesterfield Development & Zoning Cases",
                             f"{len(active)} active rezoning and development cases in Chesterfield County, "
                             "mapped, with status and details. Updated daily.",
                             "https://chesterfieldreport.com/development.html")
    out = PUBLIC / "development.html"
    out.write_text(page, encoding="utf-8")
    print(f"Built development.html + {len(cases)} case pages ({len(active)} active)")
    return out
