"""Things to Do — ticketed live events (Ticketmaster Discovery API).

Concerts, sports, theatre, comedy, and family shows across Chesterfield County
and the Richmond region, on a dedicated /things-to-do.html page. Chesterfield
venues are flagged and can be isolated with a scope toggle; the civic Events
page is left untouched.

The Ticketmaster Consumer Key is read from the TICKETMASTER_API_KEY env var
(stored in scripts/.deploy.env, gitignored). On a fetch failure we fall back to
the last good cached response so a transient API hiccup never blanks the page.
Stdlib only.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from . import render

ROOT = render.ROOT
PUBLIC = render.PUBLIC
CACHE = ROOT / "pipeline" / "things_cache.json"   # gitignored last-good response

# Chesterfield County center; radius wide enough to catch county + Richmond metro.
LATLONG = "37.377,-77.505"
RADIUS_MI = 35
HORIZON_DAYS = 120
MAX_DISPLAY = 120
FETCH_SIZE = 199

# Places that sit inside Chesterfield County (lowercased venue-city match).
CHESTERFIELD_PLACES = {
    "chesterfield", "midlothian", "chester", "moseley", "bon air", "matoaca",
    "ettrick", "north chesterfield", "brandermill", "woodlake",
    "chesterfield courthouse", "bensley",
}

# Segment -> badge color (matches the editorial palette family).
SEG_COLOR = {
    "Music": "#9a3322",
    "Sports": "#1f6f54",
    "Arts & Theatre": "#5b4b8a",
    "Family": "#b5731f",
    "Film": "#33617a",
    "Miscellaneous": "#6b6b6b",
}


# --- fetch + normalize ----------------------------------------------------

def _api_key() -> str:
    return (os.environ.get("TICKETMASTER_API_KEY") or "").strip()


def _pick_image(images: list) -> str:
    if not images:
        return ""
    # Prefer a 16:9 image around 640px wide; fall back to the widest available.
    best = ""
    best_w = -1
    for im in images:
        u = im.get("url", "")
        if not u:
            continue
        w = im.get("width", 0) or 0
        if im.get("ratio") == "16_9" and 500 <= w <= 1100:
            return u
        if w > best_w:
            best_w, best = w, u
    return best


def _price(ev: dict) -> str:
    prs = ev.get("priceRanges") or []
    if not prs:
        return ""
    pr = prs[0]
    lo, hi = pr.get("min"), pr.get("max")
    if lo is None and hi is None:
        return ""
    sym = "$" if (pr.get("currency") == "USD") else ""
    if lo is not None and hi is not None and lo != hi:
        return f"{sym}{lo:.0f}–{sym}{hi:.0f}"
    val = lo if lo is not None else hi
    return f"{sym}{val:.0f}"


def _normalize(ev: dict) -> dict | None:
    start = ev.get("dates", {}).get("start", {})
    date = start.get("localDate")
    if not date:
        return None
    time = start.get("localTime", "") or ""
    ven = (ev.get("_embedded", {}).get("venues") or [{}])[0]
    city = (ven.get("city") or {}).get("name", "") or ""
    cls = (ev.get("classifications") or [{}])[0]
    segment = (cls.get("segment") or {}).get("name", "") or "Miscellaneous"
    genre = (cls.get("genre") or {}).get("name", "") or ""
    loc = ven.get("location") or {}
    return {
        "name": ev.get("name", "") or "",
        "date": date,
        "time": time,
        "venue": ven.get("name", "") or "",
        "city": city,
        "state": (ven.get("state") or {}).get("stateCode", "") or "",
        "segment": segment,
        "genre": genre,
        "price": _price(ev),
        "image": _pick_image(ev.get("images") or []),
        "url": ev.get("url", "") or "",
        "lat": loc.get("latitude", ""),
        "lon": loc.get("longitude", ""),
        "chesterfield": city.strip().lower() in CHESTERFIELD_PLACES,
    }


def fetch_things() -> list[dict]:
    """Pull upcoming ticketed events near Chesterfield. Falls back to the cached
    last-good response on any failure. Returns a normalized, de-duped list."""
    key = _api_key()
    if not key:
        return _load_cache()
    params = {
        "apikey": key,
        "latlong": LATLONG,
        "radius": str(RADIUS_MI), "unit": "miles",
        "sort": "date,asc", "size": str(FETCH_SIZE),
    }
    url = "https://app.ticketmaster.com/discovery/v2/events.json?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ChesterfieldReport/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except Exception as e:                       # noqa: BLE001
        print(f"  ! things: Ticketmaster fetch failed ({e}); using cache")
        return _load_cache()
    raw = data.get("_embedded", {}).get("events", []) or []
    horizon = (datetime.now() + timedelta(days=HORIZON_DAYS)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    out, seen = [], set()
    for ev in raw:
        n = _normalize(ev)
        if not n or not (today <= n["date"] <= horizon):
            continue
        kkey = (n["name"], n["date"], n["venue"])
        if kkey in seen:
            continue
        seen.add(kkey)
        out.append(n)
    out.sort(key=lambda e: (e["date"], e["time"]))
    if out:
        _save_cache(out)
    return out[:MAX_DISPLAY]


def _load_cache() -> list[dict]:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))[:MAX_DISPLAY]
    except Exception:                            # noqa: BLE001
        return []


def _save_cache(items: list[dict]) -> None:
    try:
        CACHE.write_text(json.dumps(items), encoding="utf-8")
    except OSError:
        pass


# --- rendering ------------------------------------------------------------

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
_WK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _esc(s) -> str:
    import html
    return html.escape(str(s or "").strip())


def _fmt_day(date: str) -> str:
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return date
    return f"{_WK[dt.weekday()]}, {_MONTHS[dt.month - 1]} {dt.day}"


def _fmt_time(t: str) -> str:
    if not t:
        return ""
    try:
        hh, mm, *_ = t.split(":")
        h, m = int(hh), int(mm)
    except ValueError:
        return ""
    ap = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {ap}"


def _card(e: dict) -> str:
    seg = e.get("segment", "Miscellaneous")
    color = SEG_COLOR.get(seg, "#6b6b6b")
    img = e.get("image", "")
    img_html = (f'<div class="td-thumb"><img src="{_esc(img)}" alt="" loading="lazy"></div>'
                if img.startswith("http") else "")
    where = e.get("venue", "")
    citline = ", ".join(b for b in (e.get("city", ""), e.get("state", "")) if b)
    if citline:
        where = f"{where} &middot; {citline}" if where else citline
    ches = ('<span class="td-ches">In Chesterfield</span>' if e.get("chesterfield") else "")
    bits = []
    if e.get("genre"):
        bits.append(_esc(e["genre"]))
    if e.get("price"):
        bits.append(_esc(e["price"]))
    meta = " &middot; ".join(bits)
    meta_html = f'<div class="td-extra">{meta}</div>' if meta else ""
    tickets = (f'<a class="td-btn" href="{_esc(e["url"])}" target="_blank" rel="noopener">Tickets &nearr;</a>'
               if e.get("url") else "")
    return (
        f'<article class="td-card" data-seg="{_esc(seg)}" data-ches="{"1" if e.get("chesterfield") else "0"}">'
        f'{img_html}'
        '<div class="td-body">'
        f'<div class="td-top"><span class="td-seg" style="background:{color}">{_esc(seg)}</span>{ches}'
        f'<span class="td-time">{_esc(_fmt_time(e.get("time","")))}</span></div>'
        f'<h3 class="td-name">{_esc(e.get("name",""))}</h3>'
        f'<div class="td-where">{where}</div>'
        f'{meta_html}'
        f'{tickets}'
        '</div>'
        '</article>'
    )


_TD_CSS = """<style>
.td-wrap{max-width:880px;margin:0 auto;}
.td-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:62ch;margin:.4rem 0 1.3rem;}
.td-controls{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin:0 0 1.4rem;}
.td-filter{display:flex;flex-wrap:wrap;gap:.4rem;}
.td-filter button,.td-scope button{font:var(--fw-semibold) var(--fs-2xs) var(--font-sans);padding:.4rem .8rem;border:1px solid var(--border);background:var(--surface-card);color:var(--text-secondary);border-radius:999px;cursor:pointer;}
.td-filter button.is-on,.td-scope button.is-on{background:var(--accent);color:#fff;border-color:var(--accent);}
.td-scope{margin-left:auto;display:flex;gap:.4rem;}
.td-day{font:var(--fw-bold) var(--fs-2xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);border-top:1px solid var(--border);padding-top:.7rem;margin:1.4rem 0 .8rem;}
.td-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px;}
.td-card{border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface-card);overflow:hidden;display:flex;flex-direction:column;}
.td-thumb img{display:block;width:100%;height:140px;object-fit:cover;}
.td-body{padding:.8rem .9rem 1rem;display:flex;flex-direction:column;gap:.3rem;flex:1;}
.td-top{display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;}
.td-seg{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:#fff;padding:2px 6px;border-radius:3px;}
.td-ches{font:var(--fw-bold) var(--fs-3xs) var(--font-mono);text-transform:uppercase;letter-spacing:var(--ls-wide);color:var(--accent);border:1px solid var(--accent);border-radius:3px;padding:1px 5px;}
.td-time{margin-left:auto;font:var(--fs-3xs) var(--font-mono);color:var(--text-tertiary);}
.td-name{font:var(--fw-bold) var(--fs-md)/1.2 var(--font-display);margin:.1rem 0 0;color:var(--text-primary);}
.td-where{font:var(--fs-2xs)/1.4 var(--font-sans);color:var(--text-secondary);}
.td-extra{font:var(--fs-3xs) var(--font-mono);color:var(--text-tertiary);}
.td-btn{margin-top:auto;align-self:flex-start;font:var(--fw-semibold) var(--fs-2xs) var(--font-sans);color:var(--accent);text-decoration:none;padding-top:.3rem;}
.td-empty{font:var(--fs-md) var(--font-sans);color:var(--text-secondary);margin:2rem 0;}
.td-note{margin-top:2rem;font:var(--fs-2xs) var(--font-mono);color:var(--text-tertiary);}
.td-day.is-empty{display:none;}
</style>"""

_TD_JS = """<script>
(function(){
  var seg='all', ches=false;
  var cards=[].slice.call(document.querySelectorAll('.td-card'));
  function apply(){
    cards.forEach(function(c){
      var ok=(seg==='all'||c.dataset.seg===seg)&&(!ches||c.dataset.ches==='1');
      c.style.display=ok?'':'none';
    });
    [].forEach.call(document.querySelectorAll('.td-day'),function(d){
      var n=d.nextElementSibling, any=false;
      if(n&&n.classList.contains('td-grid')){
        [].forEach.call(n.children,function(c){if(c.style.display!=='none')any=true;});
      }
      d.classList.toggle('is-empty',!any);
    });
  }
  function wire(sel,set){[].forEach.call(document.querySelectorAll(sel+' button'),function(b){
    b.addEventListener('click',function(){
      [].forEach.call(document.querySelectorAll(sel+' button'),function(x){x.classList.remove('is-on');});
      b.classList.add('is-on');set(b.dataset.v);apply();
    });});}
  wire('.td-filter',function(v){seg=v;});
  wire('.td-scope',function(v){ches=(v==='ches');});
})();
</script>"""


def build_things() -> Path:
    """Render /things-to-do.html from Ticketmaster data."""
    items = fetch_things()
    segs = []
    for e in items:
        if e["segment"] not in segs:
            segs.append(e["segment"])
    seg_order = [s for s in ("Music", "Sports", "Arts & Theatre", "Family", "Film", "Miscellaneous") if s in segs]
    seg_order += [s for s in segs if s not in seg_order]
    filt = ('<div class="td-filter"><button class="is-on" data-v="all">All</button>'
            + "".join(f'<button data-v="{_esc(s)}">{_esc(s)}</button>' for s in seg_order)
            + '</div>')
    scope = ('<div class="td-scope"><button class="is-on" data-v="all">All areas</button>'
             '<button data-v="ches">Chesterfield only</button></div>')

    if items:
        rows = []
        cur = None
        for e in items:
            if e["date"] != cur:
                if cur is not None:
                    rows.append('</div>')
                cur = e["date"]
                rows.append(f'<div class="td-day">{_esc(_fmt_day(cur))}</div><div class="td-grid">')
            rows.append(_card(e))
        rows.append('</div>')
        body_inner = "".join(rows)
    else:
        body_inner = ('<p class="td-empty">No upcoming events found right now. '
                      'Check back soon.</p>')

    body = (
        _TD_CSS
        + '<div class="td-wrap">'
        + '<h1 class="page-title">Things to Do</h1>'
        + '<p class="td-lead">Concerts, sports, theatre, comedy, and family shows across '
          'Chesterfield County and the Richmond region. Pick a category, or switch to '
          '<em>Chesterfield only</em> to see what is in the county. Tickets and times via Ticketmaster.</p>'
        + '<div class="td-controls">' + filt + scope + '</div>'
        + body_inner
        + '<p class="td-note">Event data and ticketing via Ticketmaster. '
          'We list what is on sale near Chesterfield; we are not the seller.</p>'
        + '</div>'
        + _TD_JS
    )
    page = render._shell(body, len(items))
    page = render._inject_og(
        page, "Things to Do: The Chesterfield Report",
        "Concerts, sports, theatre, and family events across Chesterfield County "
        "and the Richmond region, with tickets and times.",
        f"{render.SITE_URL}/things-to-do.html", og_type="website")
    out = PUBLIC / "things-to-do.html"
    out.write_text(page, encoding="utf-8")
    return out
