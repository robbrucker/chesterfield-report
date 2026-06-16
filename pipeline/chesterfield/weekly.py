"""The Weekly Report — the on-site newsletter issue + archive.

A weekly roundup assembled from the past 7 days of published content, plus a
human "Front Porch" voice column. Each issue lives on the site at
/newsletter/<date>.html, with an archive index at /newsletter/.

Design principle: the machine assembles the roundup; a human owns the Voice.
The roundup sections are auto-built from real data (published stories, the
regional track, upcoming meetings and events). The Voice column is read from
content/newsletter/voice-<date>.md so a person writes it; if that file is
absent, the issue shows an editable placeholder.

This is the readable, on-site format. The separate `newsletter` module is the
email-client-safe renderer + Resend/SMTP send path; once this format is
approved we can point email rendering at the same assembled issue.
"""
from __future__ import annotations

import html
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import render
from . import meetings as meetings_mod
from . import events as events_mod

ROOT = render.ROOT
PUBLIC = render.PUBLIC
NL_DIR = PUBLIC / "newsletter"
VOICE_DIR = ROOT / "content" / "newsletter"

MASTHEAD = "The Weekly Report"
ALT_MASTHEAD = "The Chesterfield Report"
ROUNDUP_MAX = 6
ODDS_MAX = 3
REGIONAL_MAX = 2
AHEAD_DAYS = 10

_LIGHT_FOCUS = {"dining", "business", "schools", "community", "sports"}


# --- data gathering -------------------------------------------------------

def _esc(s: str) -> str:
    return html.escape((s or "").strip())


def _week_of(issue_date: datetime) -> str:
    monday = issue_date - timedelta(days=issue_date.weekday())
    return f"Week of {monday.strftime('%B')} {monday.day}, {monday.year}"


def _recent_published(days: int = 7) -> list:
    """(meta, body, name) for stories published in the last `days`, newest first."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    recs = render._published_records()
    fresh = [r for r in recs
             if (r[0].get("published", "") or r[0].get("fetched_at", ""))[:10] >= cutoff]
    fresh.sort(key=lambda r: (r[0].get("published", "") or "")[:19], reverse=True)
    # If a quiet week leaves us thin, fall back to the most recent regardless of date.
    return fresh if len(fresh) >= 3 else recs[:ROUNDUP_MAX + ODDS_MAX]


def _read_voice(issue_date: datetime) -> tuple[dict, str]:
    """Frontmatter + body for the Voice column, or ({}, '') if none written."""
    fname = VOICE_DIR / f"voice-{issue_date.strftime('%Y-%m-%d')}.md"
    if not fname.exists():
        cands = sorted(VOICE_DIR.glob("voice-*.md"), reverse=True) if VOICE_DIR.is_dir() else []
        if not cands:
            return {}, ""
        fname = cands[0]
    meta, body = render._parse_frontmatter(fname.read_text(encoding="utf-8"))
    return meta, body.strip()


# --- section renderers ----------------------------------------------------

def _eyebrow(label: str) -> str:
    return f'<div class="nl-eyebrow">{label}</div>'


def _voice_section(issue_date: datetime) -> str:
    """The Front Porch column. Human-written; omitted entirely until one exists
    so a public issue never shows an empty slot."""
    meta, body = _read_voice(issue_date)
    if not body:
        return ""
    mode = _esc(meta.get("mode", "") or "From the Editor")
    byline = _esc(meta.get("byline", "") or "The Chesterfield Report")
    paras = "".join(
        f"<p>{render._inline(_esc(p.strip()))}</p>"
        for p in body.split("\n\n") if p.strip() and not p.strip().startswith("#")
    )
    return (
        '<section class="nl-voice">'
        + _eyebrow("The Front Porch &middot; " + mode)
        + paras
        + f'<div class="nl-sign">&mdash; {byline}</div>'
        + '</section>'
    )


def _story_item(meta: dict, body: str, light: bool = False) -> str:
    headline = meta.get("headline", "") or ""
    slug_url = render.story_url(headline)
    fslug, flabel = render._primary_focus(meta)
    tldr = render._tldr_from_body(body) or render._summary_from_body(body)
    if len(tldr) > 220:
        tldr = tldr[:220].rsplit(" ", 1)[0] + "…"
    chip = f'<span class="nl-chip">{_esc(flabel)}</span>'
    dek = f'<p class="nl-dek">{render._inline(_esc(tldr))}</p>' if tldr and not light else ""
    cls = " nl-item--light" if light else ""
    return (
        f'<div class="nl-item{cls}">'
        f'{chip}'
        f'<a class="nl-h" href="{render.SITE_URL}{slug_url}">{_esc(headline)}</a>'
        f'{dek}'
        '</div>'
    )


def _roundup_section(recs: list) -> tuple[str, list]:
    main = recs[:ROUNDUP_MAX]
    if not main:
        return "", recs
    items = "".join(_story_item(m, b) for m, b, _ in main)
    used = {m.get("headline", "") for m, _, _ in main}
    html_out = (
        '<section class="nl-sec">'
        + _eyebrow("The Week in Chesterfield")
        + items
        + '</section>'
    )
    return html_out, [r for r in recs if r[0].get("headline", "") not in used]


def _regional_section() -> str:
    try:
        recs = render._regional_records()[:REGIONAL_MAX]
    except Exception:
        recs = []
    if not recs:
        return ""
    rows = []
    for meta, body, _ in recs:
        headline = meta.get("headline", "") or ""
        src = _esc(meta.get("source", "") or "the source")
        src_url = _esc(meta.get("source_url", "") or "#")
        why = render._why_from_body(body) or render._tldr_from_body(body)
        if len(why) > 200:
            why = why[:200].rsplit(" ", 1)[0] + "…"
        rows.append(
            '<div class="nl-item">'
            f'<a class="nl-h" href="{src_url}">{_esc(headline)}</a>'
            f'<p class="nl-dek">{render._inline(_esc(why))}</p>'
            f'<div class="nl-src">Read it at {src} &nearr;</div>'
            '</div>'
        )
    return ('<section class="nl-sec">' + _eyebrow("Virginia &amp; Region")
            + "".join(rows)
            + f'<a class="nl-more" href="{render.SITE_URL}/virginia.html">All of Virginia &amp; Region &rarr;</a>'
            + '</section>')


def _week_ahead_section() -> str:
    rows = []
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    horizon = now + timedelta(days=AHEAD_DAYS)
    try:
        mtgs = [m for m in meetings_mod._collect() if m.get("when") == "upcoming"]
    except Exception:
        mtgs = []
    seen = 0
    for m in mtgs:
        try:
            dt = datetime.fromisoformat((m.get("start") or "").replace("Z", "+00:00"))
        except Exception:
            continue
        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)
        when = meetings_mod._fmt_when(dt)
        name = _esc(m.get("name") or m.get("body") or "Public meeting")
        url = _esc(m.get("portal_url") or "")
        link = f' <a href="{url}">details &nearr;</a>' if url else ""
        rows.append(f'<li><span class="nl-when">{when}</span> '
                    f'<span class="nl-tag">Meeting</span> {name}{link}</li>')
        seen += 1
        if seen >= 5:
            break
    try:
        evs = events_mod.fetch_events()
    except Exception:
        evs = []
    ecount = 0
    for e in evs:
        start = e.get("start")
        if not isinstance(start, datetime):
            continue
        sd = start.replace(tzinfo=None) if start.tzinfo else start
        if not (now <= sd <= horizon):
            continue
        wd = sd.strftime("%a, %b %-d")
        title = _esc(e.get("summary") or "")
        loc = f' &middot; {_esc(e["location"])}' if e.get("location") else ""
        link = f' <a href="{_esc(e["link"])}">details &nearr;</a>' if e.get("link") else ""
        rows.append(f'<li><span class="nl-when">{wd}</span> '
                    f'<span class="nl-tag nl-tag--ev">Event</span> {title}{loc}{link}</li>')
        ecount += 1
        if ecount >= 4:
            break
    if not rows:
        return ""
    return ('<section class="nl-sec nl-ahead">' + _eyebrow("The Week Ahead")
            + '<ul class="nl-ahead-list">' + "".join(rows) + '</ul>'
            + f'<a class="nl-more" href="{render.SITE_URL}/meetings.html">All meetings &rarr;</a> '
            + f'<a class="nl-more" href="{render.SITE_URL}/events.html">All events &rarr;</a>'
            + '</section>')


def _odds_section(leftover: list) -> str:
    light = [(m, b) for m, b, _ in leftover
             if render._primary_focus(m)[0] in _LIGHT_FOCUS][:ODDS_MAX]
    if not light:
        light = [(m, b) for m, b, _ in leftover[:ODDS_MAX]]
    if not light:
        return ""
    items = "".join(_story_item(m, b, light=True) for m, b in light)
    return ('<section class="nl-sec">' + _eyebrow("Odds &amp; Ends") + items + '</section>')


def _one_number_section(issue_date: datetime, recs: list) -> str:
    meta, _ = _read_voice(issue_date)
    number = (meta.get("number") or "").strip()
    caption = (meta.get("number_caption") or "").strip()
    if not number:
        number = str(len(recs))
        caption = "stories we gathered and summarized for you this week."
    return ('<section class="nl-number">' + _eyebrow("One Number")
            + f'<div class="nl-bignum">{_esc(number)}</div>'
            + f'<p class="nl-numcap">{render._inline(_esc(caption))}</p>'
            + '</section>')


def _cta() -> str:
    return (
        '<section class="nl-cta">'
        '<p><strong>Got a tip?</strong> Just reply, or '
        f'<a href="{render.SITE_URL}/tip.html">send it here</a>.</p>'
        f'<p>Forward this to a neighbor &middot; <a href="{render.SITE_URL}/subscribe.html">Subscribe</a> '
        f'&middot; <a href="{render.SITE_URL}/about.html">About</a></p>'
        '</section>'
    )


# --- styling --------------------------------------------------------------

_NL_CSS = """<style>
.nl{max-width:660px;margin:0 auto;}
.nl-mast{text-align:center;border-bottom:3px double var(--border);padding:0 0 1.1rem;margin:0 0 1.6rem;}
.nl-kicker{font:var(--fw-bold) var(--fs-2xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--accent);}
.nl-mast h1{font:var(--fw-bold) var(--fs-3xl)/1.05 var(--font-display);margin:.35rem 0 .15rem;color:var(--text-primary);}
.nl-mast .nl-when-of{font:var(--fs-sm) var(--font-mono);color:var(--text-tertiary);}
.nl-eyebrow{font:var(--fw-bold) var(--fs-2xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--accent);border-top:1px solid var(--border);padding-top:.8rem;margin:0 0 .9rem;}
.nl-sec,.nl-voice,.nl-number,.nl-ahead{margin:0 0 2rem;}
.nl-voice{background:var(--surface-card);border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:var(--radius-sm);padding:1.2rem 1.4rem;}
.nl-voice .nl-eyebrow{border-top:none;padding-top:0;}
.nl-voice p{font:var(--fs-md)/1.65 var(--font-serif,var(--font-sans));color:var(--text-secondary);margin:0 0 .8rem;}
.nl-placeholder{font-style:italic;color:var(--text-tertiary);}
.nl-voice code{font:var(--fs-2xs) var(--font-mono);background:var(--surface-sunken,rgba(0,0,0,.05));padding:1px 5px;border-radius:3px;}
.nl-sign{font:var(--fw-semibold) var(--fs-sm) var(--font-sans);color:var(--text-primary);margin-top:.4rem;}
.nl-item{padding:.55rem 0 .9rem;border-bottom:1px solid var(--border);}
.nl-item:last-child{border-bottom:none;}
.nl-item--light{padding:.4rem 0;}
.nl-chip{display:inline-block;font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--accent);margin:0 0 .25rem;}
.nl-h{display:block;font:var(--fw-bold) var(--fs-lg)/1.25 var(--font-display);color:var(--text-primary);text-decoration:none;}
.nl-h:hover{color:var(--accent);}
.nl-item--light .nl-h{font-size:var(--fs-md);}
.nl-dek{font:var(--fs-sm)/1.55 var(--font-sans);color:var(--text-secondary);margin:.25rem 0 0;}
.nl-src{font:var(--fw-semibold) var(--fs-2xs) var(--font-sans);color:var(--accent);margin-top:.3rem;}
.nl-more{display:inline-block;font:var(--fw-semibold) var(--fs-2xs) var(--font-sans);color:var(--accent);text-decoration:none;margin-top:.4rem;}
.nl-ahead-list{list-style:none;padding:0;margin:0;}
.nl-ahead-list li{font:var(--fs-sm)/1.5 var(--font-sans);color:var(--text-secondary);padding:.5rem 0;border-bottom:1px solid var(--border);}
.nl-ahead-list li:last-child{border-bottom:none;}
.nl-when{font:var(--fw-bold) var(--fs-2xs) var(--font-mono);color:var(--text-primary);}
.nl-tag{display:inline-block;font:var(--fw-bold) var(--fs-3xs) var(--font-mono);text-transform:uppercase;letter-spacing:var(--ls-wide);background:var(--accent);color:#fff;border-radius:3px;padding:1px 5px;margin:0 .2rem;}
.nl-tag--ev{background:var(--text-tertiary);}
.nl-number{text-align:center;background:var(--surface-card);border:1px solid var(--border);border-radius:var(--radius-sm);padding:1.3rem 1.4rem;}
.nl-number .nl-eyebrow{border-top:none;padding-top:0;}
.nl-bignum{font:var(--fw-bold) 3.4rem/1 var(--font-display);color:var(--accent);}
.nl-numcap{font:var(--fs-sm)/1.5 var(--font-sans);color:var(--text-secondary);max-width:46ch;margin:.5rem auto 0;}
.nl-cta{text-align:center;border-top:3px double var(--border);padding:1.4rem 0 .4rem;margin-top:1rem;}
.nl-cta p{font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);margin:.2rem 0;}
.nl-cta a{color:var(--accent);font-weight:600;text-decoration:none;}
.nl-archlink{text-align:center;margin:.4rem 0 1.4rem;font:var(--fs-2xs) var(--font-mono);color:var(--text-tertiary);}
.nl-archlink a{color:var(--accent);}
.nl-arch-issue{display:block;padding:.7rem 0;border-bottom:1px solid var(--border);}
.nl-arch-issue a{font:var(--fw-bold) var(--fs-lg) var(--font-display);color:var(--text-primary);text-decoration:none;}
.nl-arch-issue a:hover{color:var(--accent);}
.nl-arch-issue .d{display:block;font:var(--fs-2xs) var(--font-mono);color:var(--text-tertiary);}
</style>"""


# --- assembly -------------------------------------------------------------

def build_issue(issue_date: datetime | None = None) -> Path:
    """Assemble and write one newsletter issue page. Returns its path."""
    issue_date = issue_date or datetime.now(timezone.utc)
    recs = _recent_published()
    roundup_html, leftover = _roundup_section(recs)

    body = (
        _NL_CSS
        + '<div class="nl">'
        + '<div class="nl-mast">'
        + f'<div class="nl-kicker">{_esc(ALT_MASTHEAD)}</div>'
        + f'<h1>{_esc(MASTHEAD)}</h1>'
        + f'<div class="nl-when-of">{_esc(_week_of(issue_date))}</div>'
        + '</div>'
        + f'<div class="nl-archlink"><a href="{render.SITE_URL}/newsletter/">View past issues</a></div>'
        + _voice_section(issue_date)
        + roundup_html
        + _regional_section()
        + _week_ahead_section()
        + _odds_section(leftover)
        + _one_number_section(issue_date, recs)
        + _cta()
        + '</div>'
    )
    page = render._shell(body, len(recs))
    title = f"{MASTHEAD} — {_week_of(issue_date)}"
    page = render._inject_og(
        page, title,
        "Your weekly Chesterfield County roundup: the week's news, what's on the "
        "civic calendar, and a note from the Front Porch.",
        f"{render.SITE_URL}/newsletter/{issue_date.strftime('%Y-%m-%d')}.html",
        og_type="article")
    NL_DIR.mkdir(parents=True, exist_ok=True)
    out = NL_DIR / f"{issue_date.strftime('%Y-%m-%d')}.html"
    out.write_text(page, encoding="utf-8")
    build_archive()
    return out


def build_archive() -> Path:
    """Write /newsletter/ — the issue archive index."""
    NL_DIR.mkdir(parents=True, exist_ok=True)
    issues = sorted((p for p in NL_DIR.glob("*.html") if p.name != "index.html"),
                    reverse=True)
    rows = []
    for p in issues:
        d = p.stem
        try:
            dt = datetime.strptime(d, "%Y-%m-%d")
            label = _week_of(dt)
            pretty = dt.strftime("%B %-d, %Y")
        except ValueError:
            label, pretty = d, d
        rows.append(
            f'<div class="nl-arch-issue"><a href="{render.SITE_URL}/newsletter/{d}.html">'
            f'{_esc(MASTHEAD)} &mdash; {_esc(label)}</a>'
            f'<span class="d">{_esc(pretty)}</span></div>')
    inner = "".join(rows) or '<p>The first issue is on its way.</p>'
    body = (
        _NL_CSS
        + '<div class="nl">'
        + '<div class="nl-mast">'
        + f'<div class="nl-kicker">{_esc(ALT_MASTHEAD)}</div>'
        + f'<h1>{_esc(MASTHEAD)}</h1>'
        + '<div class="nl-when-of">A weekly roundup of Chesterfield County news, '
          'the civic calendar, and a note from the Front Porch.</div>'
        + '</div>'
        + f'<section class="nl-sec">{_eyebrow("Past issues")}{inner}</section>'
        + _cta()
        + '</div>'
    )
    page = render._shell(body, len(issues))
    page = render._inject_og(
        page, f"{MASTHEAD} — Newsletter archive",
        "Every issue of The Weekly Report: Chesterfield County news, the civic "
        "calendar, and a note from the Front Porch.",
        f"{render.SITE_URL}/newsletter/", og_type="website")
    out = NL_DIR / "index.html"
    out.write_text(page, encoding="utf-8")
    return out
