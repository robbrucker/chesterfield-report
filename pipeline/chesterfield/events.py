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
import re
import ssl
import urllib.request
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    _ET = ZoneInfo("America/New_York")
except Exception:                                # noqa: BLE001
    _ET = datetime.timezone(datetime.timedelta(hours=-4))

from . import render
from .render import PUBLIC

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
</style>"""

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


def build_events() -> Path | None:
    events = fetch_events()
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
        rows_html.append(
            f'<div class="ev-row" data-cat="{html.escape(e["cat"])}">'
            f'<div class="ev-time">{html.escape(_time_label(e))}</div>'
            '<div class="ev-body">'
            f'<div class="ev-title"><a href="{html.escape(e["link"])}" target="_blank" rel="noopener">'
            f'{html.escape(e["summary"])}</a>{cat_badge}</div>'
            f'{where}</div></div>'
        )

    body = (
        _CSS
        + '<div class="ev-wrap">'
        + '<h1 class="page-title">Events in Chesterfield</h1>'
        + '<p class="ev-lead">Upcoming public events across Chesterfield County: festivals, '
          'parks programs, clinics, classes, and county happenings. Updated daily; past events '
          'drop off automatically.</p>'
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
