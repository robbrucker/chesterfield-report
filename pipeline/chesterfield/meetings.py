"""
County Meetings — surface UPCOMING and RECENT Chesterfield County meetings
(Board of Supervisors, Planning Commission, and related bodies) with
plain-language, AI-generated summaries of their official agendas.

Data source (confirmed working 2026-06-12):
  The county runs **CivicClerk** (the Agenda Center on chesterfield.gov links to
  https://chesterfieldcova.portal.civicclerk.com/). That SPA is backed by a
  public OData API at  https://chesterfieldcova.api.civicclerk.com/v1 :

    * GET /Events?$orderby=startDateTime&$filter=...   -> meeting rows
        (id, eventName, startDateTime, hasAgenda, isPublished, mediaStreamPath)
    * GET /Events?$filter=id eq <id>   -> full record incl. `publishedFiles`
        [{fileId, type:"Agenda"|"Agenda Packet"|"Minutes", name}]
    * GET /Meetings/GetMeetingFileStream(fileId=<fileId>,plainText=false)
        -> the agenda PDF (use the "Agenda" fileId — small; NOT the packet).

  The Legistar JSON API (webapi.legistar.com) is DEAD for this client and the
  Legistar web Calendar.aspx requires POST/viewstate — both avoided.

Agenda summaries: we download the small "Agenda" PDF to a temp file and let the
Claude Code CLI Read it (exactly the enrich.py/editor.py shell-out pattern,
`claude -p ... --output-format json --json-schema ... --model claude-haiku-4-5`,
with `--allowedTools Read` so it can open the PDF). Results are cached by a
(eventId, agendaFileId) key in meetings_cache.json so unchanged agendas are not
re-summarized.

EVERYTHING here is best-effort: any network/parse/CLI failure returns [] (or a
meeting with no summary) and NEVER raises into the build. `run.py build` stays
exit 0 even when CivicClerk is down.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import render

ROOT = render.ROOT
PUBLIC = render.PUBLIC
CACHE = ROOT / "pipeline" / "meetings_cache.json"

API = "https://chesterfieldcova.api.civicclerk.com/v1"
PORTAL = "https://chesterfieldcova.portal.civicclerk.com"
AGENDA_CENTER = "https://www.chesterfield.gov/AgendaCenter"

MODEL = "claude-haiku-4-5"          # cheap default, per project convention
CLI_TIMEOUT = 240                    # seconds per agenda summary
HTTP_TIMEOUT = 30

# Bodies we care about, by the leading text of their CivicClerk eventName.
# `slug`/`label` drive the UI; `tone` maps to the design-system accent colors
# (civic=amber for government, teal for growth/planning).
BODIES = [
    {"slug": "board-of-supervisors", "label": "Board of Supervisors",
     "match": "Board of Supervisors", "tone": "civic"},
    {"slug": "planning-commission", "label": "Planning Commission",
     "match": "Planning Commission", "tone": "teal"},
    {"slug": "school-board", "label": "School Board",
     "match": "School Board", "tone": "teal"},
]

# How far forward / back to look, and a hard cap per bucket so a body with a
# decade of history can't blow up the page or the AI bill.
UPCOMING_DAYS = 75
RECENT_DAYS = 75
MAX_UPCOMING = 8
MAX_RECENT = 6
MAX_SUMMARIES = 10        # cap NEW AI summaries per build (cost guard)


# --------------------------------------------------------------------------- #
# HTTP helpers (graceful — return None / [] on any error)
# --------------------------------------------------------------------------- #

_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "ChesterfieldReport/1.0 (+https://chesterfieldreport.com)",
    "Referer": PORTAL + "/",
    "Origin": PORTAL,
}


def _http_get(url: str, binary: bool = False, timeout: int = HTTP_TIMEOUT):
    """GET via curl, falling back to urllib. Returns bytes/str or None.

    macOS system Python 3.9 ships LibreSSL 2.8.3, whose old TLS is rejected by
    CivicClerk's WAF (TLSV1_ALERT_PROTOCOL_VERSION) — but the system `curl`
    negotiates TLS 1.3 fine and the project's network already relies on it.
    So we prefer curl and only fall back to urllib if curl is unavailable."""
    curl = shutil.which("curl")
    if curl:
        cmd = [curl, "-s", "--fail", "-m", str(timeout),
               "-H", f"User-Agent: {_HEADERS['User-Agent']}",
               "-H", "Accept: application/json",
               "-H", f"Referer: {PORTAL}/",
               "-H", f"Origin: {PORTAL}", url]
        try:
            proc = subprocess.run(cmd, capture_output=True, timeout=timeout + 10)
            if proc.returncode == 0 and proc.stdout:
                return proc.stdout if binary else proc.stdout.decode("utf-8", "replace")
        except Exception:                         # noqa: BLE001 — fall through
            pass
    try:                                          # urllib fallback
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
        return raw if binary else raw.decode("utf-8", "replace")
    except Exception as e:                         # noqa: BLE001 — never raise
        print(f"  ! meetings: fetch failed ({type(e).__name__}: {e})")
        return None


def _get_json(url: str):
    txt = _http_get(url)
    if not txt:
        return None
    try:
        return json.loads(txt)
    except Exception as e:                         # noqa: BLE001 — never raise
        print(f"  ! meetings: bad JSON ({type(e).__name__}: {e})")
        return None


def _odata(filter_expr: str, order: str = "startDateTime asc",
           top: int = 25) -> list:
    """Query /Events with an OData $filter and return the value list (or [])."""
    q = urllib.parse.urlencode({
        "$filter": filter_expr,
        "$orderby": order,
        "$top": str(top),
    }, quote_via=urllib.parse.quote)
    data = _get_json(f"{API}/Events?{q}")
    if not isinstance(data, dict):
        return []
    val = data.get("value")
    return val if isinstance(val, list) else []


# --------------------------------------------------------------------------- #
# Date helpers
# --------------------------------------------------------------------------- #

def _parse_dt(s: str):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:                            # noqa: BLE001
        return None


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
# Fetch + shape meetings
# --------------------------------------------------------------------------- #

def _agenda_file_id(event_id: int):
    """Second call: pull the full event record and find the 'Agenda' fileId in
    publishedFiles (this is what GetMeetingFileStream needs — NOT the agendaId,
    NOT the eventId). Returns (fileId, agenda_name) or (None, None)."""
    rows = _odata(f"id eq {event_id}", order="id asc", top=1)
    if not rows:
        return None, None
    pf = rows[0].get("publishedFiles") or []
    agenda = next((f for f in pf if (f.get("type") or "").lower() == "agenda"), None)
    if not agenda:
        # fall back to a packet if no trimmed agenda was published
        agenda = next((f for f in pf
                       if "agenda" in (f.get("type") or "").lower()), None)
    if not agenda or not agenda.get("fileId"):
        return None, None
    return agenda["fileId"], agenda.get("name")


def _shape(ev: dict, body: dict, when: str) -> dict:
    """Normalize one CivicClerk event into our render dict."""
    eid = ev.get("id")
    return {
        "event_id": eid,
        "body": body["label"],
        "body_slug": body["slug"],
        "tone": body["tone"],
        "name": (ev.get("eventName") or body["label"]).strip(),
        "start": ev.get("startDateTime"),
        "has_agenda": bool(ev.get("hasAgenda")),
        "when": when,                            # "upcoming" | "recent"
        "portal_url": f"{PORTAL}/event/{eid}/overview" if eid else PORTAL,
        "video_url": (ev.get("mediaStreamPath") or "").strip(),
        "agenda_file_id": None,                  # filled lazily
        "summary": None,
        "key_items": [],
        "notable": "",
    }


def _collect() -> list:
    """Return upcoming + recent meetings for the target bodies. Never raises."""
    now = datetime.now(timezone.utc)
    up_cut = _iso(now)
    up_end = _iso(now + timedelta(days=UPCOMING_DAYS))
    rec_start = _iso(now - timedelta(days=RECENT_DAYS))
    out: list = []
    seen = set()

    for body in BODIES:
        m = body["match"].replace("'", "''")
        # UPCOMING: published, has start in window, soonest first.
        up = _odata(
            f"contains(eventName,'{m}') and startDateTime ge {up_cut} "
            f"and startDateTime le {up_end} and isPublished eq 'Published'",
            order="startDateTime asc", top=15)
        n = 0
        for ev in up:
            if ev.get("id") in seen:
                continue
            seen.add(ev.get("id"))
            out.append(_shape(ev, body, "upcoming"))
            n += 1
            if n >= MAX_UPCOMING:
                break

        # RECENT: most recent first, only those with an agenda to summarize.
        rec = _odata(
            f"contains(eventName,'{m}') and startDateTime lt {up_cut} "
            f"and startDateTime ge {rec_start} and isPublished eq 'Published'",
            order="startDateTime desc", top=15)
        n = 0
        for ev in rec:
            if ev.get("id") in seen:
                continue
            seen.add(ev.get("id"))
            out.append(_shape(ev, body, "recent"))
            n += 1
            if n >= MAX_RECENT:
                break

    return out


# --------------------------------------------------------------------------- #
# Agenda download + AI summary (Claude CLI, enrich.py pattern)
# --------------------------------------------------------------------------- #

_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": ("1-2 plain-language sentences on what this body is "
                            "deciding at this meeting, for a general newspaper "
                            "reader. No jargon."),
        },
        "key_items": {
            "type": "array",
            "items": {"type": "string"},
            "description": ("Up to 5 short plain-language agenda items, "
                            "favoring zoning, development, budget and anything "
                            "of public interest. Each a short phrase."),
            "maxItems": 5,
        },
        "notable": {
            "type": "string",
            "description": ("The single MOST consequential or easy-to-miss item a "
                            "resident would want flagged, even if it's buried deep in "
                            "routine agenda boilerplate: a significant rezoning or "
                            "development, a tax/fee/rate change, major spending, a "
                            "decision affecting a specific neighborhood or road, a "
                            "policy shift, or anything likely to be controversial. "
                            "ONE sentence, plain language, say why it matters. Empty "
                            "string if the agenda is genuinely routine with nothing "
                            "that stands out."),
        },
    },
    "required": ["summary", "key_items", "notable"],
}


def _cli_available() -> bool:
    return shutil.which("claude") is not None


def _download_agenda(file_id: int):
    """Download the agenda PDF to a temp file. Returns the path or None."""
    url = (f"{API}/Meetings/GetMeetingFileStream"
           f"(fileId={file_id},plainText=false)")
    data = _http_get(url, binary=True, timeout=HTTP_TIMEOUT * 2)
    if not data or data[:4] != b"%PDF":
        return None
    try:
        fd, path = tempfile.mkstemp(suffix=".pdf", prefix="cr_agenda_")
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        return path
    except Exception as e:                        # noqa: BLE001
        print(f"  ! meetings: agenda write failed ({type(e).__name__}: {e})")
        return None


def _summarize_agenda(pdf_path: str, body: str, name: str) -> dict | None:
    """Shell out to the Claude CLI to Read + summarize the agenda PDF.
    Returns {summary, key_items} or None. Never raises."""
    if not _cli_available():
        return None
    prompt = (
        f"Read the meeting agenda PDF at {pdf_path}. It is the official agenda "
        f"for a Chesterfield County, Virginia '{body}' meeting "
        f"({name}). Using ONLY the content of that agenda, write a plain-language "
        f"summary for a general newspaper reader: a 1-2 sentence 'summary' of "
        f"what this body is deciding, and up to 5 'key_items' as short plain "
        f"phrases (favor zoning, development, rezoning cases, budget, taxes, and "
        f"anything of clear public interest; name the place/applicant if shown). "
        f"Also set 'notable': scan the WHOLE agenda for the single most "
        f"consequential or easy-to-miss item a resident would want flagged "
        f"(a big rezoning/development, a tax/fee/rate change, major spending, a "
        f"decision affecting a specific neighborhood or road, a policy shift, or "
        f"anything likely controversial) and state it in one plain sentence with "
        f"why it matters; use an empty string only if the agenda is genuinely "
        f"routine. Do not invent anything not in the agenda. "
        f"STYLE: do not use em dashes or en dashes ('—' or '–') in any field; "
        f"use commas, periods, parentheses, or colons instead."
    )
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "json",
        "--json-schema", json.dumps(_SUMMARY_SCHEMA),
        "--allowedTools", "Read",
        "--model", MODEL,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=CLI_TIMEOUT)
        if proc.returncode != 0:
            print(f"  ! meetings: CLI failed ({proc.stderr.strip()[:160]})")
            return None
        env = json.loads(proc.stdout)
        if env.get("is_error"):
            return None
        data = env.get("structured_output")
        if not data or not data.get("summary"):
            return None
        items = [str(x).strip() for x in (data.get("key_items") or []) if str(x).strip()]
        return {"summary": str(data["summary"]).strip(), "key_items": items[:5],
                "notable": str(data.get("notable") or "").strip()}
    except Exception as e:                        # noqa: BLE001
        print(f"  ! meetings: summarize errored ({type(e).__name__}: {e})")
        return None


# --------------------------------------------------------------------------- #
# Cache
# --------------------------------------------------------------------------- #

def _load_cache() -> dict:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:                             # noqa: BLE001
        return {}


def _save_cache(cache: dict) -> None:
    try:
        CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    except Exception as e:                        # noqa: BLE001
        print(f"  ! meetings: cache write failed ({e})")


def _enrich_with_summaries(meetings: list) -> None:
    """Fill summary/key_items for meetings that have an agenda, using the cache;
    only summarize up to MAX_SUMMARIES NEW agendas per build. In-place."""
    cache = _load_cache()
    made = 0
    for mtg in meetings:
        if not mtg["has_agenda"] or mtg["event_id"] is None:
            continue
        fid, _aname = _agenda_file_id(mtg["event_id"])
        if not fid:
            continue
        mtg["agenda_file_id"] = fid
        mtg["agenda_url"] = (f"{API}/Meetings/GetMeetingFileStream"
                             f"(fileId={fid},plainText=false)")
        key = f"{mtg['event_id']}:{fid}"
        cached = cache.get(key)
        if cached and cached.get("summary"):
            mtg["summary"] = cached["summary"]
            mtg["key_items"] = cached.get("key_items", [])
            mtg["notable"] = cached.get("notable", "")
            continue
        if made >= MAX_SUMMARIES:
            continue                              # leave un-summarized this run
        pdf = _download_agenda(fid)
        if not pdf:
            continue
        try:
            res = _summarize_agenda(pdf, mtg["body"], mtg["name"])
        finally:
            try:
                os.unlink(pdf)
            except OSError:
                pass
        if res:
            mtg["summary"] = res["summary"]
            mtg["key_items"] = res["key_items"]
            mtg["notable"] = res.get("notable", "")
            cache[key] = res
            made += 1
    if made:
        _save_cache(cache)
    if made:
        print(f"  meetings: summarized {made} new agenda(s)")


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

_MONTHS = ["", "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
           "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _fmt_when(dt: datetime) -> str:
    # e.g. "Tue, Jun 16 · 3:00 PM"  (county times are local Eastern, stored as Z
    # but representing wall-clock county time, so render the stored fields as-is)
    wd = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]
    mon = _MONTHS[dt.month].title()
    hr = dt.hour % 12 or 12
    ap = "AM" if dt.hour < 12 else "PM"
    return f"{wd}, {mon} {dt.day} &middot; {hr}:{dt.minute:02d} {ap}"


def _date_badge(dt: datetime, tone: str) -> str:
    return (
        f'<div class="mtg-date mtg-date--{tone}">'
        f'<span class="mtg-date__mo">{_MONTHS[dt.month]}</span>'
        f'<span class="mtg-date__day">{dt.day}</span></div>'
    )


def _meeting_card(m: dict) -> str:
    dt = _parse_dt(m["start"])
    tone = m["tone"]
    badge = _date_badge(dt, tone) if dt else ""
    when = _fmt_when(dt) if dt else ""

    # Body badge + agenda state.
    body_badge = (f'<span class="cr-badge cr-badge--{tone}">'
                  f'{_esc(m["body"])}</span>')

    if m.get("summary"):
        summ = (f'<p class="mtg-summary">{_esc(m["summary"])}</p>')
        if m.get("notable"):
            summ += ('<div class="mtg-notable"><span class="mtg-notable__tag">'
                     '◉ Worth watching</span>'
                     f'<span class="mtg-notable__txt">{_esc(m["notable"])}</span></div>')
        if m.get("key_items"):
            lis = "".join(f"<li>{_esc(it)}</li>" for it in m["key_items"])
            summ += f'<ul class="mtg-items">{lis}</ul>'
        summ += ('<p class="mtg-aigen">AI summary of the official agenda '
                 '&mdash; <a href="' + _esc(m.get("agenda_url", m["portal_url"]))
                 + '" target="_blank" rel="noopener">read the source agenda</a> '
                 'before relying on it.</p>')
    elif m["has_agenda"]:
        summ = ('<p class="mtg-summary mtg-summary--pending">Agenda posted &mdash; '
                'summary pending. <a href="' + _esc(m.get("agenda_url", m["portal_url"]))
                + '" target="_blank" rel="noopener">View the agenda.</a></p>')
    else:
        summ = ('<p class="mtg-summary mtg-summary--pending">Agenda not yet '
                'posted. Check the official listing closer to the meeting.</p>')

    # Links row.
    links = []
    if m.get("agenda_file_id"):
        links.append('<a class="mtg-link" href="' + _esc(m["agenda_url"])
                     + '" target="_blank" rel="noopener">View agenda (PDF)</a>')
    links.append('<a class="mtg-link" href="' + _esc(m["portal_url"])
                 + '" target="_blank" rel="noopener">Meeting details</a>')
    if m.get("video_url"):
        links.append('<a class="mtg-link" href="' + _esc(m["video_url"])
                     + '" target="_blank" rel="noopener">Watch video</a>')
    links_html = '<div class="mtg-links">' + "".join(links) + '</div>'

    return (
        f'<article class="cr-card cr-card--accent cr-card--bracket mtg-card" '
        f'style="--accent-color:{render._TONE_VAR.get(tone, "var(--neon-teal)")}">'
        + badge
        + '<div class="mtg-body">'
        + '<div class="mtg-head">' + body_badge
        + (f'<span class="mtg-when">{when}</span>' if when else "")
        + '</div>'
        + f'<h3 class="mtg-title">{_esc(m["name"])}</h3>'
        + summ + links_html
        + '</div></article>'
    )


def _section(title: str, kicker: str, meetings: list, empty: str) -> str:
    if meetings:
        cards = "".join(_meeting_card(m) for m in meetings)
        grid = f'<div class="mtg-grid">{cards}</div>'
    else:
        grid = f'<p class="mtg-empty">{empty}</p>'
    return render._sechead(kicker, title) + grid


# Plain-language, county-verified explainer (sources: chesterfield.gov Procedures,
# Public-Comments, Zoning Process pages + Va. Code 15.2-2204). Facts checked
# 2026-06-15; deliberately avoids unverified specifics (room capacity, etc.).
_EXPLAINER = (
    '<section class="mtg-explainer">'
    '<style>'
    '.mtg-explainer{margin:2.2rem 0;padding:1.4rem 1.5rem;border:1px solid var(--border);'
    'border-radius:var(--radius-sm);background:var(--surface-card);}'
    '.mtg-explainer h2{margin:0 0 .6rem;}'
    '.mtg-explainer h3{font:var(--fw-bold) var(--fs-sm)/1.2 var(--font-sans);'
    'text-transform:uppercase;letter-spacing:var(--ls-wide);color:var(--accent);'
    'margin:1.2rem 0 .3rem;}'
    '.mtg-explainer p{font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);'
    'color:var(--text-secondary);margin:.2rem 0;max-width:68ch;}'
    '.mtg-explainer a{color:var(--accent);font-weight:600;}'
    '</style>'
    '<h2 class="mtg-h">How to weigh in on county decisions</h2>'
    '<p>Two bodies handle land use. The <strong>Planning Commission</strong> reviews '
    'zoning and development cases and makes recommendations; the <strong>Board of '
    'Supervisors</strong> makes the final call.</p>'
    '<h3>When they meet</h3>'
    '<p>The Planning Commission meets the third Tuesday of the month at 6 p.m. The '
    'Board of Supervisors meets at 2 p.m., with an evening session at 6 p.m., in the '
    'Public Meeting Room at 10001 Iron Bridge Road.</p>'
    '<h3>How to speak</h3>'
    '<p>At the Planning Commission, signing up is optional. You can sign up in the '
    'hallway beforehand or step to the podium when your item is called. At the Board '
    'of Supervisors, you must register with the Clerk; the window opens at 8:30 a.m. '
    'the first business day after the prior meeting and closes at noon the day of the '
    'meeting. In-person speakers get three minutes; a representative for a group of '
    'three or more gets five; each citizen comment period is capped at 15 minutes.</p>'
    '<h3>Comment without attending</h3>'
    '<p>The Board&rsquo;s online Citizen Comment Portal opens the Thursday before a '
    'meeting and closes at 5 p.m. the Tuesday before. Comments (up to 400 words) '
    'become part of the public record.</p>'
    '<h3>Notice rules</h3>'
    '<p>For zoning hearings, the county publishes notice in the newspaper twice (first '
    'no more than 28 days, second no less than five days before) and mails adjacent '
    'property owners at least 15 days ahead, more than the five-day state minimum.</p>'
    '<h3>Stay informed</h3>'
    '<p>Subscribe to <a href="https://www.chesterfield.gov/list.aspx?ListID=399" '
    'target="_blank" rel="noopener">Planning email alerts</a> and track pending cases '
    'on the county&rsquo;s <a href="https://www.chesterfield.gov/982/Active-Development-and-Zoning-Cases" '
    'target="_blank" rel="noopener">Active Development and Zoning Cases</a> page.</p>'
    '</section>'
)


def build_meetings():
    """Build public/meetings.html. NEVER raises — returns the path (page is
    still written, with a graceful 'unavailable' note, if the source is down)."""
    try:
        meetings = _collect()
    except Exception as e:                        # noqa: BLE001
        print(f"  ! meetings: collect failed ({type(e).__name__}: {e})")
        meetings = []

    if meetings:
        try:
            _enrich_with_summaries(meetings)
        except Exception as e:                    # noqa: BLE001
            print(f"  ! meetings: enrichment failed ({type(e).__name__}: {e})")

    upcoming = sorted(
        [m for m in meetings if m["when"] == "upcoming"],
        key=lambda m: m["start"] or "")
    recent = sorted(
        [m for m in meetings if m["when"] == "recent"],
        key=lambda m: m["start"] or "", reverse=True)

    intro = (
        '<h1 class="page-title">County Meetings</h1>'
        '<p class="lead">A low-friction way to keep an eye on county government '
        '&mdash; the Board of Supervisors, Planning Commission and related '
        'bodies. Below are upcoming and recent meetings with plain-language '
        'summaries of what&rsquo;s on the agenda, especially zoning, development '
        'and budget items. Every summary links to the county&rsquo;s official '
        'agenda so you can read the source.</p>'
        '<p class="mtg-disclaimer">Summaries are <strong>AI-generated from the '
        'official agenda</strong> and may miss nuance &mdash; always confirm '
        'against the county&rsquo;s agenda before attending or acting. Data comes '
        'from Chesterfield County&rsquo;s '
        '<a href="' + AGENDA_CENTER + '" target="_blank" rel="noopener">Agenda '
        'Center</a> (CivicClerk). The School Board listing reflects what the '
        'county portal publishes; for full CCPS School Board agendas see the '
        '<a href="https://www.ccpsnet.net/Page/School-Board" target="_blank" '
        'rel="noopener">school division&rsquo;s site</a>.</p>'
    )

    if not meetings:
        body = (
            intro
            + '<p class="mtg-empty">The county meeting feed is temporarily '
            'unavailable. Please check the '
            '<a href="' + AGENDA_CENTER + '" target="_blank" rel="noopener">'
            'official Agenda Center</a> directly.</p>'
            + _EXPLAINER
            + "<style>" + _MTG_CSS + "</style>"
        )
        out = PUBLIC / "meetings.html"
        out.write_text(render._shell(body, 0), encoding="utf-8")
        return out

    body = (
        intro
        + _section("Upcoming meetings", "// what&rsquo;s next", upcoming,
                   "No upcoming meetings are posted right now.")
        + _section("Recent meetings", "// just happened", recent,
                   "No recent meetings with posted agendas.")
        + '<section class="mtg-official"><h2 class="mtg-h">Official sources</h2>'
        '<ul class="mtg-srclist">'
        '<li><a href="' + AGENDA_CENTER + '" target="_blank" rel="noopener">'
        'Chesterfield County Agenda Center</a> &mdash; agendas, minutes &amp; '
        'meeting video.</li>'
        '<li><a href="' + PORTAL + '" target="_blank" rel="noopener">'
        'CivicClerk public portal</a> &mdash; full meeting calendar.</li>'
        '<li><a href="https://www.chesterfield.gov/1231/Board-Meetings" '
        'target="_blank" rel="noopener">Board of Supervisors meeting schedule</a>.'
        '</li></ul></section>'
        + _EXPLAINER
        + "<style>" + _MTG_CSS + "</style>"
    )

    out = PUBLIC / "meetings.html"
    out.write_text(render._shell(body, len(meetings)), encoding="utf-8")
    return out


# Page-local styles, using the design system's legacy alias vars (--neon, --ink,
# --panel, etc.) that board.py/maps.py also rely on so it reskins automatically.
_MTG_CSS = """
  .mtg-disclaimer { font-size:.82rem; line-height:1.5; color:var(--muted);
    background:rgba(255,210,63,.06); border-left:3px solid var(--neon-amber,#ffd23f);
    padding:.7rem .9rem; margin:.4rem 0 2rem; border-radius:0 4px 4px 0; }
  .mtg-disclaimer a { color:var(--ink); }
  .mtg-grid { display:grid; grid-template-columns:1fr 1fr; gap:1rem;
    margin:0 0 2.4rem; }
  .mtg-card { display:flex; gap:1rem; align-items:flex-start; padding:1.1rem; }
  .mtg-date { flex:0 0 auto; width:60px; text-align:center; padding:.45rem 0;
    border:1px solid var(--line,rgba(255,255,255,.14)); border-radius:4px;
    background:rgba(255,255,255,.03); }
  .mtg-date__mo { display:block; font-family:var(--mono,"Space Mono",monospace);
    font-size:.66rem; letter-spacing:.12em; color:var(--neon);
    text-shadow:0 0 12px rgba(39,230,198,.4); }
  .mtg-date__day { display:block; font-family:var(--serif); font-size:1.7rem;
    font-weight:700; line-height:1.05; color:var(--ink); }
  .mtg-date--civic .mtg-date__mo { color:var(--neon-amber,#ffd23f);
    text-shadow:0 0 12px rgba(255,210,63,.4); }
  .mtg-body { flex:1 1 auto; min-width:0; }
  .mtg-head { display:flex; flex-wrap:wrap; align-items:center; gap:.5rem .7rem;
    margin-bottom:.35rem; }
  .mtg-when { font-family:var(--mono,"Space Mono",monospace); font-size:.74rem;
    color:var(--muted); letter-spacing:.02em; }
  .mtg-title { font-family:var(--serif); font-size:1.05rem; line-height:1.25;
    color:var(--ink); margin:.1rem 0 .5rem; }
  .mtg-summary { font-size:.9rem; line-height:1.55; color:var(--ink-soft,var(--ink));
    margin:.2rem 0 .5rem; }
  .mtg-summary--pending { color:var(--muted); font-style:italic; }
  .mtg-summary a { color:var(--neon); }
  .mtg-notable { display:flex; gap:.6rem; align-items:flex-start;
    background:rgba(255,210,63,.10); border:1px solid rgba(255,210,63,.4);
    border-left:3px solid var(--neon-amber,#ffd23f); border-radius:6px;
    padding:.6rem .75rem; margin:.1rem 0 .6rem; }
  .mtg-notable__tag { flex:none; font-family:var(--font-mono,monospace); font-weight:700;
    font-size:.66rem; letter-spacing:.08em; text-transform:uppercase;
    color:var(--neon-amber,#ffd23f); margin-top:.12rem; white-space:nowrap; }
  .mtg-notable__txt { font-size:.88rem; line-height:1.5; color:var(--ink-soft,var(--ink)); }
  .mtg-items { margin:.2rem 0 .6rem 1.05rem; padding:0; font-size:.85rem;
    line-height:1.5; color:var(--ink-soft,var(--ink)); }
  .mtg-items li { margin:.12rem 0; }
  .mtg-aigen { font-size:.74rem; color:var(--muted); margin:.3rem 0 .2rem;
    font-style:italic; }
  .mtg-aigen a { color:var(--muted); text-decoration:underline; }
  .mtg-links { display:flex; flex-wrap:wrap; gap:.4rem .7rem; margin-top:.5rem; }
  .mtg-link { font-family:var(--mono,"Space Mono",monospace); font-size:.74rem;
    letter-spacing:.03em; color:var(--neon); text-decoration:none;
    border-bottom:1px solid rgba(39,230,198,.35); padding-bottom:1px; }
  .mtg-link:hover { border-bottom-color:var(--neon); }
  .mtg-empty { color:var(--muted); font-style:italic; margin:.4rem 0 2.4rem; }
  .mtg-official { margin:1rem 0 2rem; padding-top:1.2rem;
    border-top:1px solid var(--line,rgba(255,255,255,.12)); }
  .mtg-h { font-family:var(--serif); font-size:1.2rem; color:var(--ink);
    margin:0 0 .7rem; }
  .mtg-srclist { margin:0; padding-left:1.1rem; font-size:.9rem; line-height:1.7;
    color:var(--ink-soft,var(--ink)); }
  .mtg-srclist a { color:var(--neon); }
  @media (max-width:1080px){ .mtg-grid { grid-template-columns:1fr; } }
  @media (max-width:680px){
    .mtg-card { padding:.9rem; gap:.8rem; }
    .mtg-date { width:52px; }
    .mtg-date__day { font-size:1.45rem; }
  }
"""
