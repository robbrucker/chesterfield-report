"""Upcoming community events -> public/events.html.

Pulls Chesterfield County's official calendar via its iCal feeds (the RSS
versions are broken on this deployment, so we use iCal), parses the VEVENTs,
keeps only upcoming events, and renders them grouped by date with a category
filter. Past events fall off automatically, so the page never goes stale.

We use the community-facing categories (festivals, clinics, parks, health,
public-safety outreach, county dates) and leave the high-volume public-meetings
category to the Meetings page.

Stdlib only (a small hand-rolled iCal/VEVENT parser; no external deps). Network
fetch is best-effort: a failed category is skipped, and if nothing loads the
existing page is left in place. Reuses render._shell().
"""
from __future__ import annotations

import datetime
import html
import json
import re
import shutil
import ssl
import subprocess
import time
import urllib.request
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    _ET = ZoneInfo("America/New_York")
except Exception:                                # noqa: BLE001
    _ET = datetime.timezone(datetime.timedelta(hours=-4))

from . import render, geo
from . import things as _things
from . import farmers as _farmers
from .render import PUBLIC

MODEL = "claude-haiku-4-5"
CLI_TIMEOUT = 150
ENRICH_CAP = 8   # max event enrichments per build (cached after; backfill does all)
CACHE = Path(__file__).resolve().parents[1] / "events_enrich_cache.json"

_FEED = ("https://www.chesterfield.gov/common/modules/iCalendar/"
         "iCalendar.aspx?catID={cat}&feed=calendar")
EVENT_PAGE = "https://www.chesterfield.gov/calendar.aspx?EID={uid}"
COUNTY_CAL = "https://www.chesterfield.gov/calendar.aspx"
UA = "ChesterfieldReport/0.1 (+brucker.rob@gmail.com)"

# (catID, label, color) — the community-facing buckets. 113 (Public Meetings)
# is intentionally excluded; the Meetings page covers that.
CATS = [
    ("115", "Community", "#2f7d8f"),
    ("44", "Parks & Rec", "#3f8f5a"),
    ("112", "Health", "#c1820e"),
    ("114", "Public Safety", "#9a3322"),
    ("111", "County dates", "#6b6b6b"),
]
HORIZON_DAYS = 120   # only show events within this window


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=30,
                                  context=ssl.create_default_context()).read().decode("utf-8", "replace")


def _unescape(v: str) -> str:
    return (v.replace("\\n", " ").replace("\\N", " ").replace("\\,", ",")
            .replace("\\;", ";").replace("\\\\", "\\")).strip()


def _parse_dt(value: str):
    """iCal date/datetime value -> (datetime, all_day_bool) or (None, False)."""
    value = value.strip()
    try:
        if "T" in value:
            return datetime.datetime.strptime(value[:15], "%Y%m%dT%H%M%S"), False
        if len(value) >= 8 and value[:8].isdigit():
            return datetime.datetime.strptime(value[:8], "%Y%m%d"), True
    except ValueError:
        pass
    return None, False


def _parse_ical(text: str, label: str, color: str) -> list[dict]:
    # Unfold folded lines (continuation lines start with a space or tab).
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n[ \t]", "", text)
    events = []
    for block in re.findall(r"BEGIN:VEVENT\n(.*?)END:VEVENT", text, re.DOTALL):
        fields = {}
        for line in block.split("\n"):
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            name = key.split(";", 1)[0].upper()
            fields.setdefault(name, val)
        start, all_day = _parse_dt(fields.get("DTSTART", ""))
        if start is None:
            continue
        summary = _unescape(fields.get("SUMMARY", "")).strip()
        if not summary:
            continue
        location = re.sub(r"<[^>]+>", " ", _unescape(fields.get("LOCATION", "")))
        location = re.sub(r"\s{2,}", " ", location).strip(" -")
        uid = (fields.get("UID", "") or "").strip()
        # The public event page lives in DESCRIPTION (calendar.aspx?EID=...).
        m = re.search(r"https?://[^\s]*calendar\.aspx\?EID=(\d+)", fields.get("DESCRIPTION", ""))
        link = m.group(0) if m else (EVENT_PAGE.format(uid=uid) if uid.isdigit() else COUNTY_CAL)
        events.append({
            "summary": summary, "start": start, "all_day": all_day,
            "location": location, "uid": uid or summary, "link": link,
            "cat": label, "color": color,
        })
    return events


def fetch_events() -> list[dict]:
    """All upcoming community events across the county categories, deduped by
    UID, sorted by start. Returns [] on total failure (build stays graceful)."""
    now = datetime.datetime.now(_ET).replace(tzinfo=None)
    today = now.date()
    horizon = today + datetime.timedelta(days=HORIZON_DAYS)
    seen, out = set(), []
    for cat, label, color in CATS:
        try:
            evs = _parse_ical(_get(_FEED.format(cat=cat)), label, color)
        except Exception as e:                   # noqa: BLE001
            print(f"  ! events: cat {cat} failed: {e}")
            continue
        for e in evs:
            d = e["start"].date()
            if d < today or d > horizon:
                continue              # past or beyond the horizon -> auto-expire
            if e["uid"] in seen:
                continue
            seen.add(e["uid"])
            out.append(e)
    out.sort(key=lambda e: e["start"])
    return out


# --------------------------------------------------------------------------- #
# Enrichment: read the county event page for a description, registration, contact
# --------------------------------------------------------------------------- #

_ENRICH_SCHEMA = {
    "type": "object",
    "properties": {
        "description": {"type": "string"},
        "registration_required": {"type": "boolean"},
        "registration_note": {"type": "string"},
        "cost": {"type": "string"},
        "contact_phone": {"type": "string"},
        "contact_name": {"type": "string"},
        "audience": {"type": "string"},
    },
    "required": ["description"],
}


def _cli_available() -> bool:
    return shutil.which("claude") is not None


def _detail_text(link: str) -> str:
    """Fetch a county event page and return the cleaned event-detail region."""
    try:
        raw = _get(link)
    except Exception:                            # noqa: BLE001
        return ""
    i = raw.find("eventDetails")
    seg = raw[i:i + 9000] if i != -1 else raw
    seg = re.sub(r"<script.*?</script>", " ", seg, flags=re.DOTALL)
    seg = re.sub(r"<[^>]+>", " ", seg)
    seg = html.unescape(seg)
    return re.sub(r"\s+", " ", seg).strip()[:6000]


def _clean_field(s):
    if not isinstance(s, str):
        return s
    for cut in ("</", "<parameter", "<function", "<antml", "```"):
        j = s.find(cut)
        if j != -1:
            s = s[:j]
    return s.strip()


def enrich_event(ev: dict, detail: str) -> dict | None:
    if not _cli_available() or not detail:
        return None
    prompt = (
        "You are a local-news editor writing a short, useful listing for a Chesterfield "
        "County, Virginia community event. Using ONLY the official event-page text below, "
        "fill the schema.\n\n"
        f"Event title: {ev['summary']}\n"
        f"When: {ev['start'].strftime('%A, %B %-d, %Y %-I:%M %p')}\n"
        f"Where: {ev['location']}\n\n"
        f"OFFICIAL EVENT PAGE TEXT:\n\"\"\"\n{detail}\n\"\"\"\n\n"
        "Rules: 'description' = 1 to 2 plain sentences on what the event is and who it is for. "
        "'registration_required' = true ONLY if the text says you must register/sign up/RSVP "
        "in advance; else false. 'registration_note' = how to register (and any link/phone) if "
        "required, else empty. 'cost' = 'Free' if free, or a brief note if there are fees, else "
        "empty. 'contact_phone' and 'contact_name' = from the page if present, else empty. "
        "'audience' = e.g. 'All ages', 'Adults', 'Kids', if stated, else empty. Use ONLY the "
        "text; never invent a phone number, link, or fee. "
        "STYLE: no em dashes or en dashes; use commas, periods, or colons."
    )
    cmd = ["claude", "-p", prompt, "--output-format", "json",
           "--json-schema", json.dumps(_ENRICH_SCHEMA), "--model", MODEL]
    for attempt in range(2):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=CLI_TIMEOUT)
            if proc.returncode != 0:
                if attempt == 0:
                    time.sleep(4)
                    continue
                return None
            data = json.loads(proc.stdout).get("structured_output")
            if not data or not data.get("description"):
                return None
            return {k: ([_clean_field(x) for x in v] if isinstance(v, list) else _clean_field(v))
                    for k, v in data.items()}
        except Exception:                        # noqa: BLE001
            if attempt == 0:
                time.sleep(4)
                continue
            return None
    return None


def _load_cache() -> dict:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_cache(cache: dict) -> None:
    try:
        CACHE.write_text(json.dumps(cache, indent=0), encoding="utf-8")
    except OSError:
        pass


def _geocode(ev: dict) -> None:
    """Attach lat/lon from the event location (Nominatim, cached). Skips virtual."""
    loc = ev.get("location", "")
    if not loc or "virtual" in loc.lower():
        return
    r = geo.geocode(loc) or geo.geocode(loc + ", Chesterfield, VA")
    if r:
        ev["lat"], ev["lon"] = r["lat"], r["lon"]


def _apply(events: list[dict], cap: int = ENRICH_CAP) -> None:
    """Geocode every event; (re-)enrich up to `cap` un-cached events per run."""
    cache = _load_cache()
    n = 0
    for ev in events:
        _geocode(ev)
        key = str(ev["uid"])
        cached = cache.get(key)
        if cached:
            ev["ai"] = cached
            continue
        if n >= cap:
            continue
        data = enrich_event(ev, _detail_text(ev["link"]))
        n += 1
        if data:
            cache[key] = data
            ev["ai"] = data
    _save_cache(cache)
    if n:
        print(f"  events: enriched {n} this run")


def backfill_events() -> dict:
    """One-time: enrich every upcoming event (no cap)."""
    events = fetch_events()
    _apply(events, cap=10_000)
    return {"events": len(events)}


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

_CSS = """<style>
.ev-wrap{max-width:840px;margin:0 auto;}
.ev-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:64ch;margin:.4rem 0 1.2rem;}
.ev-filter{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 1.4rem;}
.ev-filter button{padding:.5rem .85rem;border:1px solid var(--border);background:var(--surface-card);
  color:var(--text-secondary);border-radius:999px;font:var(--fw-semibold) var(--fs-2xs) var(--font-sans);cursor:pointer;}
.ev-filter button.is-on{background:var(--accent);color:#fff;border-color:var(--accent);}
.ev-day{font:var(--fw-bold) var(--fs-sm)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;
  color:var(--accent);margin:1.6rem 0 .6rem;padding-bottom:.35rem;border-bottom:2px solid var(--border);}
.ev-row{display:flex;gap:14px;padding:.7rem 0;border-bottom:1px solid var(--border);align-items:baseline;}
.ev-time{flex:0 0 84px;font:var(--fw-bold) var(--fs-2xs) var(--font-mono);color:var(--text-tertiary);white-space:nowrap;}
.ev-body{flex:1;min-width:0;}
.ev-title{font:var(--fw-semibold) var(--fs-md)/1.25 var(--font-sans);}
.ev-title a{color:var(--text-primary);}
.ev-title a:hover{color:var(--accent);}
.ev-where{font:var(--fs-2xs)/1.4 var(--font-sans);color:var(--text-tertiary);margin-top:.15rem;}
.ev-cat{display:inline-block;color:#fff;font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);
  text-transform:uppercase;padding:.24rem .5rem;border-radius:4px;vertical-align:middle;margin-left:6px;}
.ev-summary{font:var(--fs-2xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);margin:0 0 .4rem;}
.ev-src{margin-top:2rem;padding:1rem 1.1rem;border-left:3px solid var(--accent);background:var(--surface-card);
  border-radius:var(--radius-xs);font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);}
.ev-src a{color:var(--accent);font-weight:600;}
.ev-empty{font:var(--fs-md) var(--font-sans);color:var(--text-secondary);margin:2rem 0;}
#ev-map{height:340px;border-radius:var(--radius-sm);overflow:hidden;border:1px solid var(--border);margin:0 0 1.2rem;}
.ev-desc{font:var(--fs-sm)/1.5 var(--font-sans);color:var(--text-secondary);margin:.3rem 0 .2rem;}
.ev-tags{display:flex;flex-wrap:wrap;gap:8px;margin:.3rem 0 .1rem;align-items:center;}
.ev-reg{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;
  color:var(--accent);border:1px solid var(--accent);border-radius:4px;padding:.22rem .5rem;}
.ev-cost,.ev-contact,.ev-aud{font:var(--fs-2xs)/1.4 var(--font-sans);color:var(--text-tertiary);}
.ev-contact a{color:var(--accent);}
@media(max-width:560px){#ev-map{height:260px;}.ev-time{flex-basis:64px;}}
</style>"""

_MAP_JS = """
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
<div id="ev-map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
(function(){
  if(!window.L) return;
  var pts=__DATA__;
  function tile(){var l=document.documentElement.getAttribute('data-theme')==='light';
    return l?'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png':'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';}
  var map=L.map('ev-map',{scrollWheelZoom:false}).setView([37.40,-77.58],11);
  var layer=L.tileLayer(tile(),{attribution:'&copy; OpenStreetMap &copy; CARTO',subdomains:'abcd',maxZoom:19}).addTo(map);
  var cl=L.markerClusterGroup({maxClusterRadius:38,showCoverageOnHover:false});
  pts.forEach(function(p){
    var h='<strong>'+p[0]+'</strong><br>'+p[3]+(p[4]?'<br><a href="'+p[4]+'" target="_blank" rel="noopener">Details</a>':'');
    L.circleMarker([p[1],p[2]],{radius:7,color:'#fff',weight:1.5,fillColor:'#9a3322',fillOpacity:.9}).bindPopup(h).addTo(cl);
  });
  map.addLayer(cl);
  new MutationObserver(function(){layer.setUrl(tile());}).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
})();
</script>
"""


def _map(events: list[dict]) -> str:
    pts = [[e["summary"], e["lat"], e["lon"], html.escape(e["cat"]), html.escape(e["link"])]
           for e in events if e.get("lat") and e.get("lon")]
    if not pts:
        return ""
    return _MAP_JS.replace("__DATA__", json.dumps(pts, separators=(",", ":")))

_FILTER_JS = """
<script>
(function(){
  var btns=[].slice.call(document.querySelectorAll('.ev-filter button')),
      rows=[].slice.call(document.querySelectorAll('.ev-row')),
      days=[].slice.call(document.querySelectorAll('.ev-day')),cat='all';
  function apply(){
    rows.forEach(function(r){r.style.display=(cat==='all'||r.getAttribute('data-cat')===cat)?'':'none';});
    days.forEach(function(d){var n=d.nextElementSibling,any=false;
      while(n&&n.classList.contains('ev-row')){if(n.style.display!=='none')any=true;n=n.nextElementSibling;}
      d.style.display=any?'':'none';});
  }
  btns.forEach(function(b){b.addEventListener('click',function(){btns.forEach(function(x){x.classList.remove('is-on');});
    b.classList.add('is-on');cat=b.getAttribute('data-cat');apply();});});
})();
</script>
"""


def _time_label(e: dict) -> str:
    if e["all_day"]:
        return "All day"
    t = e["start"].strftime("%-I:%M %p").replace(":00", "")
    return t


# Ticketmaster segment -> (events-page category label, color).
_TM_CAT = {
    "Music": ("Live Music", "#9a3322"),
    "Sports": ("Sports", "#1f6f54"),
    "Arts & Theatre": ("Arts & Theatre", "#5b4b8a"),
    "Family": ("Family", "#b5731f"),
}


def _chesterfield_ticketed() -> list[dict]:
    """Chesterfield-venue concerts/shows from Ticketmaster, shaped as events."""
    try:
        items = _things.fetch_things()
    except Exception:                            # noqa: BLE001
        return []
    out = []
    for e in items:
        if not e.get("chesterfield"):
            continue
        try:
            y, mo, d = (int(x) for x in e["date"].split("-"))
            t = (e.get("time") or "").split(":")
            hh, mm = (int(t[0]), int(t[1])) if len(t) >= 2 else (19, 0)
            start = datetime.datetime(y, mo, d, hh, mm)
        except Exception:                        # noqa: BLE001
            continue
        cat, color = _TM_CAT.get(e.get("segment", ""), ("Things to Do", "#33617a"))
        venue = e.get("venue", "")
        parts = [b for b in (e.get("genre"), venue) if b]
        desc = " at ".join(parts) if len(parts) == 2 else (parts[0] if parts else "")
        if desc and e.get("price"):
            desc = f"{desc}. Tickets {e['price']}."
        elif desc:
            desc = f"{desc}."
        out.append({
            "summary": e.get("name", ""), "start": start, "all_day": False,
            "location": ", ".join(b for b in (venue, e.get("city", "")) if b),
            "uid": e.get("url") or e.get("name", ""), "link": e.get("url", ""),
            "cat": cat, "color": color,
            "lat": e.get("lat", ""), "lon": e.get("lon", ""),
            "ai": {"description": desc} if desc else {},
        })
    return out


_FM_CSS = """<style>
.ev-fm{border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface-card);
 padding:.9rem 1.1rem;margin:0 0 1.4rem;}
.ev-fm-h{font:var(--fw-bold) var(--fs-2xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);
 text-transform:uppercase;color:var(--accent);margin-bottom:.5rem;}
.ev-fm ul{list-style:none;padding:0;margin:0;}
.ev-fm li{font:var(--fs-sm)/1.5 var(--font-sans);color:var(--text-secondary);padding:.25rem 0;}
.ev-fm li .ev-fm-when{display:inline-block;min-width:9.5rem;font-weight:600;color:var(--text-primary);}
.ev-fm-more{display:inline-block;margin-top:.5rem;font:var(--fw-semibold) var(--fs-2xs) var(--font-sans);color:var(--accent);text-decoration:none;}
</style>"""


def _farmers_block() -> str:
    """A compact recurring-markets block for the events page."""
    ms = [m for m in _farmers.MARKETS if m.get("chesterfield")]
    if not ms:
        return ""
    rows = "".join(
        f'<li><span class="ev-fm-when">{html.escape(m.get("schedule",""))}</span>'
        f'<strong>{html.escape(m.get("name",""))}</strong>'
        + (f' &middot; {html.escape(m["hours"])}' if m.get("hours") else "")
        + '</li>'
        for m in ms)
    return (
        _FM_CSS
        + '<div class="ev-fm"><div class="ev-fm-h">Farmers markets (recurring)</div>'
        + f'<ul>{rows}</ul>'
        + '<a class="ev-fm-more" href="/farmers-markets.html">All farmers markets &amp; details &rarr;</a>'
        + '</div>'
    )


def build_events() -> Path | None:
    events = fetch_events()
    if not events:
        return None

    _apply(events)   # geocode + AI enrichment (description, registration, contact)

    # A bare title/time row with no description reads as broken. Drop anything we
    # could not enrich with a real description; un-enriched events reappear on
    # later builds as the enrichment backfill catches up.
    events = [e for e in events if ((e.get("ai") or {}).get("description") or "").strip()]

    # Fold in Chesterfield-venue concerts/shows from Ticketmaster so the events
    # page is the single "everything happening in Chesterfield" hub.
    events += _chesterfield_ticketed()
    events.sort(key=lambda e: e["start"])
    if not events:
        return None

    cats_present = []
    seen_c = set()
    for e in events:
        if e["cat"] not in seen_c:
            seen_c.add(e["cat"])
            cats_present.append((e["cat"], e["color"]))
    filters = '<div class="ev-filter"><button class="is-on" data-cat="all">All</button>' + "".join(
        f'<button data-cat="{html.escape(c)}">{html.escape(c)}</button>' for c, _ in cats_present) + '</div>'

    # Group by date in chronological order.
    rows_html = []
    cur_day = None
    for e in events:
        d = e["start"].date()
        if d != cur_day:
            cur_day = d
            rows_html.append(f'<div class="ev-day">{d.strftime("%A, %B %-d")}</div>')
        cat_badge = f'<span class="ev-cat" style="background:{e["color"]}">{html.escape(e["cat"])}</span>'
        where = f'<div class="ev-where">{html.escape(e["location"])}</div>' if e["location"] else ""
        ai = e.get("ai") or {}
        extra = ""
        if ai.get("description"):
            extra += f'<div class="ev-desc">{html.escape(ai["description"])}</div>'
        tags = []
        if ai.get("registration_required"):
            tags.append('<span class="ev-reg">Registration required</span>')
        if (ai.get("cost") or "").strip():
            tags.append(f'<span class="ev-cost">{html.escape(ai["cost"])}</span>')
        if (ai.get("audience") or "").strip():
            tags.append(f'<span class="ev-aud">{html.escape(ai["audience"])}</span>')
        if tags:
            extra += '<div class="ev-tags">' + "".join(tags) + '</div>'
        cbits = [html.escape(ai[k]) for k in ("registration_note", "contact_phone", "contact_name")
                 if (ai.get(k) or "").strip()]
        if cbits:
            extra += f'<div class="ev-contact">{" &middot; ".join(cbits)}</div>'
        rows_html.append(
            f'<div class="ev-row" data-cat="{html.escape(e["cat"])}">'
            f'<div class="ev-time">{html.escape(_time_label(e))}</div>'
            '<div class="ev-body">'
            f'<div class="ev-title"><a href="{html.escape(e["link"])}" target="_blank" rel="noopener">'
            f'{html.escape(e["summary"])}</a>{cat_badge}</div>'
            f'{where}{extra}</div></div>'
        )

    body = (
        _CSS
        + '<div class="ev-wrap">'
        + '<h1 class="page-title">Events in Chesterfield</h1>'
        + '<p class="ev-lead">Everything happening across Chesterfield County: festivals, parks '
          'programs, classes, and county happenings, plus concerts and shows at Chesterfield venues '
          'and the area farmers markets. Updated daily; past events drop off automatically.</p>'
        + _farmers_block()
        + _map(events)
        + filters
        + f'<p class="ev-summary">{len(events)} upcoming events</p>'
        + "".join(rows_html)
        + '<div class="ev-src">Events are from the official '
          f'<a href="{COUNTY_CAL}" target="_blank" rel="noopener">Chesterfield County calendar</a>, '
          'updated daily. Always confirm the date, time, and any registration with the county before '
          'you go. Looking for government meetings? See the <a href="/meetings.html">Meetings</a> page.</div>'
        + '</div>'
        + _FILTER_JS
    )
    page = render._shell(body)
    page = render._inject_og(page, "Events in Chesterfield County",
                             f"{len(events)} upcoming public events in Chesterfield County: festivals, "
                             "parks programs, clinics, classes, and county happenings. Updated daily.",
                             "https://chesterfieldreport.com/events.html")
    out = PUBLIC / "events.html"
    out.write_text(page, encoding="utf-8")
    print(f"Built events.html ({len(events)} upcoming events)")
    return out
