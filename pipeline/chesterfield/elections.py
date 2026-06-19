"""2026 Voter Guide for Chesterfield County -> /elections.html.

A nonpartisan civic page: the election calendar, what is on the ballot, and how
to vote, with prominent links to the OFFICIAL Virginia/Chesterfield sources.
Data is hand-curated from verified official sources (VA Dept. of Elections,
Chesterfield General Registrar, VPAP, 2026 local reporting). Accuracy matters
more than completeness here: where a candidate field is large or unconfirmed we
point readers to their official ballot rather than publish a partial list.

Keep it neutral. Party labels are factual; incumbency is noted as fact; no
characterizations, no endorsements, equal treatment.
"""
from __future__ import annotations

import html
from datetime import datetime, date, timezone
from pathlib import Path

from . import render

PUBLIC = render.PUBLIC

PORTAL = "https://vote.elections.virginia.gov"
POLL_LOOKUP = "https://www.elections.virginia.gov/casting-a-ballot/polling-place-lookup/"
PRECINCT_MAPS = "https://www.chesterfield.gov/5826/Precinct-Lists-and-Maps"

REGISTRAR = {
    "name": "Chesterfield General Registrar and Director of Elections",
    "address": "9848 Lori Road, Chesterfield, VA 23832",
    "phone": "804-748-1471",
    "email": "Registrar@chesterfield.gov",
    "hours": "Monday to Friday, 8:30 a.m. to 5 p.m.",
    "url": "https://www.chesterfield.gov/689/Voter-Registrar",
}

# Each election: timeline rows = (label, when, detail).
ELECTIONS = [
    {
        "id": "primary",
        "name": "August 4 Primary",
        "date": date(2026, 8, 4),
        "date_label": "Tuesday, August 4, 2026",
        "ev_start": date(2026, 6, 18),
        "ev_end": date(2026, 8, 1),
        "intro": ("Virginia moved its 2026 primary from June to August 4 (House Bill 29). "
                  "This is an open primary, so you choose one party's ballot. What appears on "
                  "your ballot depends on where you live."),
        "timeline": [
            ("Early voting", "June 18 to August 1", "Central Library (7051 Lucy Corr Blvd) and the Registrar's Office. No satellite sites for this primary."),
            ("Register / update by", "Friday, July 24", "After this, you can register and vote a provisional ballot."),
            ("Request a mail ballot by", "Friday, July 24", ""),
            ("Return a mail ballot by", "Postmarked August 4, received by the registrar by noon August 7", ""),
            ("Election Day", "Tuesday, August 4, polls 6 a.m. to 7 p.m.", "In line by 7 p.m. you may vote."),
        ],
        "races": [
            {"office": "U.S. Senate: Republican primary", "scope": "All Chesterfield voters (Republican ballot)",
             "candidates": [{"n": "Kim Farington"}, {"n": "Bert Mizusawa"}, {"n": "David Williams"}],
             "note": "The winner faces Sen. Mark Warner (D) in November."},
            {"office": "U.S. House, 1st District: Democratic primary", "scope": "1st District voters only (Democratic ballot)",
             "candidates": [],
             "note": "Seven Democrats qualified to challenge Rep. Rob Wittman (R). See the full field on your "
                     "official ballot. (Reported candidates include Shannon Taylor and Salaam Bhatti.)"},
            {"office": "Dale District Supervisor: special Democratic primary", "scope": "Dale District voters only",
             "candidates": [{"n": "LeQuan Hylton", "tag": "interim incumbent"}, {"n": "Crosby", "tag": "confirm first name on your ballot"}],
             "note": "A special election to fill the seat of the late Jim Holland. The primary winner advances to November."},
        ],
    },
    {
        "id": "general",
        "name": "November 3 General Election",
        "date": date(2026, 11, 3),
        "date_label": "Tuesday, November 3, 2026",
        "ev_start": date(2026, 9, 18),
        "ev_end": date(2026, 10, 31),
        "intro": "The general election. Some races are decided in the August 4 primaries above.",
        "timeline": [
            ("Early voting", "September 18 to October 31", "Chesterfield locations are posted closer to September; check the registrar."),
            ("Register / update by", "Friday, October 23", "After this, you can register and vote a provisional ballot."),
            ("Request a mail ballot by", "5 p.m. Friday, October 23", ""),
            ("Return a mail ballot by", "Postmarked November 3 (confirm the exact receipt deadline with the registrar)", ""),
            ("Election Day", "Tuesday, November 3, polls 6 a.m. to 7 p.m.", "In line by 7 p.m. you may vote."),
        ],
        "races": [
            {"office": "U.S. Senate", "scope": "All Chesterfield voters",
             "candidates": [{"n": "Mark Warner", "tag": "Democratic incumbent"}, {"n": "Republican nominee", "tag": "decided August 4"}], "note": ""},
            {"office": "U.S. House, 1st District", "scope": "1st District voters",
             "candidates": [{"n": "Rob Wittman", "tag": "Republican incumbent"}, {"n": "Democratic nominee", "tag": "decided August 4"}], "note": ""},
            {"office": "U.S. House, 4th District", "scope": "4th District voters",
             "candidates": [{"n": "Jennifer McClellan", "tag": "Democratic incumbent"}, {"n": "Jason Brown II", "tag": "Independent"}, {"n": "Andre Kersey", "tag": "Independent"}], "note": ""},
            {"office": "Dale District Supervisor (special)", "scope": "Dale District voters",
             "candidates": [{"n": "Winner of the August 4 Democratic primary", "tag": ""}],
             "note": "Confirm the final ballot with the registrar."},
        ],
    },
]


def _esc(s) -> str:
    return html.escape(str(s or "").strip())


def _status_banner() -> str:
    """A short, dated 'what is happening now' line so the page feels current."""
    today = datetime.now(timezone.utc).date()
    prim, gen = ELECTIONS[0], ELECTIONS[1]
    if today < prim["ev_start"]:
        msg = "Early voting for the August 4 primary begins June 18."
    elif today <= prim["ev_end"]:
        msg = "Early voting for the August 4 primary is open now through August 1."
    elif today < prim["date"]:
        msg = "The August 4 primary is this week. Polls are open 6 a.m. to 7 p.m. on Tuesday."
    elif today < gen["ev_start"]:
        msg = "The November 3 general election is next. Early voting starts September 18."
    elif today <= gen["ev_end"]:
        msg = "Early voting for the November 3 general election is open now through October 31."
    elif today < gen["date"]:
        msg = "The November 3 general election is almost here. Polls are open 6 a.m. to 7 p.m."
    else:
        msg = "Check vote.elections.virginia.gov for the next election."
    return f'<div class="el-now"><span class="el-now-dot"></span>{_esc(msg)}</div>'


_PARTY = {"Democratic incumbent": "d", "Republican incumbent": "r", "Independent": "i"}


def _race_card(r: dict) -> str:
    cands = []
    for c in r.get("candidates", []):
        tag = c.get("tag", "")
        cls = ""
        for k, v in _PARTY.items():
            if k.lower() in tag.lower():
                cls = f" el-p-{v}"
        tag_html = f'<span class="el-tag{cls}">{_esc(tag)}</span>' if tag else ""
        cands.append(f'<li>{_esc(c["n"])}{tag_html}</li>')
    cand_html = f'<ul class="el-cands">{"".join(cands)}</ul>' if cands else ""
    note = f'<p class="el-race-note">{_esc(r["note"])}</p>' if r.get("note") else ""
    return (
        '<div class="el-race">'
        f'<div class="el-race-office">{_esc(r["office"])}</div>'
        f'<div class="el-race-scope">{_esc(r["scope"])}</div>'
        f'{cand_html}{note}'
        '</div>'
    )


def _election_block(e: dict) -> str:
    rows = "".join(
        '<div class="el-date">'
        f'<div class="el-date-top"><span class="el-date-lbl">{_esc(lbl)}</span>'
        f'<span class="el-date-when">{_esc(w)}</span></div>'
        + (f'<div class="el-date-det">{_esc(det)}</div>' if det else "")
        + '</div>'
        for lbl, w, det in e["timeline"])
    races = "".join(_race_card(r) for r in e["races"])
    return (
        f'<section class="el-block" id="{e["id"]}">'
        f'<h2>{_esc(e["name"])}</h2>'
        f'<p class="el-intro">{_esc(e["intro"])}</p>'
        '<h3>Key dates</h3>'
        f'<div class="el-dates">{rows}</div>'
        '<h3>What is on your ballot</h3>'
        f'<div class="el-races">{races}</div>'
        '</section>'
    )


_EL_CSS = """<style>
.el-wrap{max-width:820px;margin:0 auto;}
.el-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:64ch;margin:.4rem 0 1.2rem;}
.el-now{display:flex;align-items:center;gap:.6rem;background:var(--surface-card);border:1px solid var(--accent);border-radius:var(--radius-sm);padding:.7rem 1rem;font:var(--fw-semibold) var(--fs-md) var(--font-sans);color:var(--text-primary);margin:0 0 1.4rem;}
.el-now-dot{width:10px;height:10px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 4px rgba(154,50,34,.18);flex:none;}
.el-cta{display:flex;flex-wrap:wrap;gap:.6rem;margin:0 0 1.8rem;}
.el-btn{display:inline-block;background:var(--accent);color:#fff;border-radius:var(--radius-xs);padding:11px 20px;font:var(--fw-bold) var(--fs-sm) var(--font-sans);text-decoration:none;}
.el-btn.sec{background:var(--surface-card);color:var(--accent);border:1px solid var(--accent);}
.el-block{border-top:1px solid var(--border);margin-top:2rem;padding-top:.4rem;}
.el-block h2{font:var(--fw-bold) var(--fs-2xl)/1.15 var(--font-display);color:var(--text-primary);margin:1rem 0 .3rem;}
.el-block h3{font:var(--fw-bold) var(--fs-2xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--accent);margin:1.6rem 0 .7rem;}
.el-intro{font:var(--fs-md)/1.6 var(--font-sans);color:var(--text-secondary);}
.el-dates{margin:.3rem 0 0;}
.el-date{border-top:1px solid var(--border);padding:.7rem 0;}
.el-date-top{display:flex;justify-content:space-between;align-items:baseline;gap:.6rem 1.2rem;flex-wrap:wrap;}
.el-date-lbl{font:var(--fw-bold) var(--fs-md)/1.25 var(--font-display);color:var(--text-primary);}
.el-date-when{font:var(--fw-semibold) var(--fs-sm)/1.3 var(--font-sans);color:var(--accent);text-align:right;}
.el-date-det{font:var(--fs-2xs)/1.5 var(--font-sans);color:var(--text-tertiary);margin-top:.25rem;max-width:64ch;}
.el-races{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;}
.el-race{border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface-card);padding:.9rem 1.05rem;}
.el-race-office{font:var(--fw-bold) var(--fs-md)/1.2 var(--font-display);color:var(--text-primary);}
.el-race-scope{font:var(--fw-semibold) var(--fs-3xs) var(--font-mono);text-transform:uppercase;letter-spacing:var(--ls-wide);color:var(--text-tertiary);margin:.2rem 0 .5rem;}
.el-cands{list-style:none;padding:0;margin:0;}
.el-cands li{font:var(--fs-sm)/1.5 var(--font-sans);color:var(--text-primary);padding:.2rem 0;display:flex;flex-wrap:wrap;align-items:baseline;gap:.4rem;}
.el-tag{font:var(--fw-semibold) var(--fs-3xs) var(--font-sans);color:var(--text-tertiary);background:var(--surface-sunken,rgba(0,0,0,.05));border-radius:3px;padding:1px 6px;}
.el-p-d{color:#1c4e8a;background:rgba(28,78,138,.1);}
.el-p-r{color:#a02622;background:rgba(160,38,34,.1);}
.el-p-i{color:#555;background:rgba(85,85,85,.1);}
.el-race-note{font:var(--fs-2xs)/1.45 var(--font-sans);color:var(--text-tertiary);margin:.5rem 0 0;}
.el-how{border-top:1px solid var(--border);margin-top:2rem;padding-top:.4rem;}
.el-how h2{font:var(--fw-bold) var(--fs-2xl) var(--font-display);margin:1rem 0 .6rem;}
.el-how ul{font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);}
.el-reg{border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:var(--radius-xs);background:var(--surface-card);padding:.9rem 1.1rem;margin:1rem 0;font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);}
.el-reg strong{color:var(--text-primary);}
.el-disc{margin-top:2rem;padding:1rem 1.1rem;border-left:3px solid var(--accent);background:var(--surface-card);border-radius:var(--radius-xs);font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);}
.el-disc a{color:var(--accent);}
</style>"""


def build_elections() -> Path:
    """Render /elections.html."""
    r = REGISTRAR
    how = (
        '<section class="el-how">'
        '<h2>How to vote in Chesterfield</h2>'
        '<ul>'
        f'<li><strong>Register or check your status:</strong> at the official portal, '
        f'<a href="{PORTAL}" target="_blank" rel="noopener">vote.elections.virginia.gov</a>. '
        'You can also see your personalized sample ballot and which districts you are in.</li>'
        '<li><strong>Vote early, in person:</strong> at the Central Library (7051 Lucy Corr Blvd) or the '
        'Registrar\'s Office during the windows above. November locations are posted closer to September.</li>'
        f'<li><strong>Vote by mail:</strong> request and track your ballot at '
        f'<a href="{PORTAL}" target="_blank" rel="noopener">vote.elections.virginia.gov</a>, or through the '
        'registrar. Return it by mail or to a drop box at the Central Library or Registrar\'s Office.</li>'
        f'<li><strong>Find your polling place and districts:</strong> '
        f'<a href="{POLL_LOOKUP}" target="_blank" rel="noopener">official lookup</a>, or the county\'s '
        f'<a href="{PRECINCT_MAPS}" target="_blank" rel="noopener">precinct maps</a>.</li>'
        '</ul>'
        '<div class="el-reg">'
        f'<strong>{_esc(r["name"])}</strong><br>'
        f'{_esc(r["address"])}<br>'
        f'Phone: {_esc(r["phone"])} &middot; Email: '
        f'<a href="mailto:{r["email"]}">{_esc(r["email"])}</a><br>'
        f'{_esc(r["hours"])} &middot; '
        f'<a href="{r["url"]}" target="_blank" rel="noopener">chesterfield.gov voter registrar</a>'
        '</div>'
        '</section>'
    )
    body = (
        _EL_CSS
        + '<div class="el-wrap">'
        + '<h1 class="page-title">2026 Voter Guide</h1>'
        + '<p class="el-lead">Everything you need to vote in Chesterfield County in 2026. '
          'Nonpartisan, with links to the official sources. Always confirm your ballot and status '
          'with the registrar.</p>'
        + _status_banner()
        + '<div class="el-cta">'
        + f'<a class="el-btn" href="{PORTAL}" target="_blank" rel="noopener">Register or check your status</a>'
        + f'<a class="el-btn sec" href="{POLL_LOOKUP}" target="_blank" rel="noopener">Find your polling place</a>'
        + '</div>'
        + _election_block(ELECTIONS[0])
        + _election_block(ELECTIONS[1])
        + how
        + '<div class="el-disc">This is a nonpartisan guide compiled from the Virginia Department of '
          'Elections, the Chesterfield General Registrar, and VPAP. Candidate fields and dates can change, '
          f'so confirm everything on your personalized ballot at <a href="{PORTAL}" target="_blank" '
          'rel="noopener">vote.elections.virginia.gov</a> or call the registrar at 804-748-1471. '
          'For campaign-finance records, see <a href="https://www.vpap.org" target="_blank" rel="noopener">'
          'the Virginia Public Access Project</a>.</div>'
        + '</div>'
    )
    page = render._shell(body, len(ELECTIONS))
    page = render._inject_og(
        page, "2026 Voter Guide: Chesterfield County",
        "How and when to vote in Chesterfield County, Virginia in 2026: the August 4 primary "
        "and November 3 general election, what is on your ballot, and how to register.",
        f"{render.SITE_URL}/elections.html", og_type="website")
    out = PUBLIC / "elections.html"
    out.write_text(page, encoding="utf-8")
    return out
