"""Changelog: a public "what's new" page for The Chesterfield Report.

A reader-facing record of what we have shipped, newest first. It reinforces the
transparency angle (the site is actively built in the open) and gives returning
readers a reason to look around. Entries are hand-curated and written for
readers, not developers. Add a new entry near the top of CHANGELOG whenever we
ship something a reader would notice.
"""
from __future__ import annotations

import html
from pathlib import Path

from . import render

PUBLIC = render.PUBLIC

# Newest first. Each entry: (date_display, sort_key, title, body_html).
# sort_key is YYYY-MM-DD for ordering; date_display is what readers see.
CHANGELOG = [
    ("June 19, 2026", "2026-06-19", "2026 Voter Guide",
     "A nonpartisan <a href=\"/elections.html\">Voter Guide</a> for the 2026 elections: the calendar "
     "(early voting for the August 4 primary is open now), what's on your ballot, and how to register "
     "and vote, with links to the official sources."),

    ("June 20, 2026", "2026-06-20", "Police and Fire pages",
     "New pages for <a href=\"/police.html\">Chesterfield County Police</a> and "
     "<a href=\"/fire.html\">Chesterfield Fire &amp; EMS</a>: who runs each, where the "
     "stations are, what they cost and on what, how many officers and firefighters there "
     "are, and what the work looks like, all from official county figures."),

    ("June 19, 2026", "2026-06-19b", "District maps on the Voter Guide",
     "The <a href=\"/elections.html\">Voter Guide</a> now shows how Chesterfield is split between the "
     "1st and 4th congressional districts, with maps and a plain-language explainer, plus a fix so the "
     "address lookup works in every browser."),

    ("June 18, 2026", "2026-06-18", "A real contact address",
     "You can now reach us directly at "
     "<a href=\"mailto:info@chesterfieldreport.com\">info@chesterfieldreport.com</a>, "
     "in addition to the tip form. Email us a story, a correction, or a question."),

    ("June 18, 2026", "2026-06-18b", "The Weekly Report newsletter",
     "Sign up to get a free weekly roundup of the week's news and what's on the civic "
     "calendar, delivered to your inbox. Free to read. "
     "<a href=\"/subscribe.html\">Subscribe here.</a>"),

    ("June 17, 2026", "2026-06-17", "Farmers markets guide",
     "A new <a href=\"/farmers-markets.html\">Farmers Markets</a> page covering the markets "
     "in Chesterfield County and the Richmond area, with days, hours, locations, and what "
     "each one sells. Shop local."),

    ("June 17, 2026", "2026-06-17b", "Everything happening, in one place",
     "The <a href=\"/events.html\">Events</a> page now brings together county happenings, "
     "concerts and shows at Chesterfield venues, and the area farmers markets, so you can see "
     "what's going on this week at a glance."),

    ("June 16, 2026", "2026-06-16", "Things to Do",
     "A new <a href=\"/things-to-do.html\">Things to Do</a> page with concerts, shows, "
     "family events, and games across the county and the greater Richmond region, each with a "
     "link to tickets."),

    ("June 16, 2026", "2026-06-16b", "Quicker ways to explore",
     "The homepage now has shortcut tiles to the Board of Supervisors, Development &amp; "
     "Zoning, Events, and Schools, and the menu was reorganized so the sections you use most "
     "are easier to reach."),

    ("June 16, 2026", "2026-06-16c", "Virginia &amp; Region",
     "A new <a href=\"/virginia.html\">Virginia &amp; Region</a> section for statewide and "
     "regional news that affects Chesterfield residents, like state laws, the budget, and "
     "utility rates, kept separate from our local coverage."),

    ("June 2026", "2026-06-01", "The foundation",
     "The Chesterfield Report launched with the core that still drives it: local news gathered "
     "from official sources and outlets, written in plain language and linked back to the "
     "originals, plus dedicated pages for "
     "<a href=\"/board.html\">your Board of Supervisors</a> (including who funds them), "
     "<a href=\"/meetings.html\">meetings</a>, "
     "<a href=\"/taxes.html\">taxes and the budget</a>, "
     "<a href=\"/development.html\">development and zoning cases</a>, "
     "<a href=\"/schools.html\">schools</a>, "
     "<a href=\"/dining.html\">dining</a>, "
     "<a href=\"/neighborhoods.html\">neighborhoods</a>, housing, and the ongoing "
     "<a href=\"/shoosmith.html\">Shoosmith landfill</a> investigation."),
]

_CL_CSS = """<style>
.cl-wrap{max-width:720px;margin:0 auto;}
.cl-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:60ch;margin:.4rem 0 2rem;}
.cl-item{position:relative;padding:0 0 1.6rem 1.4rem;border-left:2px solid var(--border);}
.cl-item:last-child{border-left-color:transparent;}
.cl-item::before{content:"";position:absolute;left:-7px;top:.35rem;width:12px;height:12px;border-radius:50%;background:var(--accent);}
.cl-date{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);margin-bottom:.3rem;}
.cl-title{font:var(--fw-bold) var(--fs-lg)/1.2 var(--font-display);color:var(--text-primary);margin:0 0 .35rem;}
.cl-body{font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);margin:0;}
.cl-body a{color:var(--accent);}
.cl-note{margin-top:1.5rem;font:var(--fs-2xs) var(--font-mono);color:var(--text-tertiary);}
</style>"""


def build_changelog() -> Path:
    """Render /changelog.html."""
    items = sorted(CHANGELOG, key=lambda e: e[1], reverse=True)
    rows = []
    for date_display, _key, title, body in items:
        rows.append(
            '<div class="cl-item">'
            f'<div class="cl-date">{html.escape(date_display)}</div>'
            f'<h2 class="cl-title">{title}</h2>'
            f'<p class="cl-body">{body}</p>'
            '</div>')
    body = (
        _CL_CSS
        + '<div class="cl-wrap">'
        + '<h1 class="page-title">What’s New</h1>'
        + '<p class="cl-lead">The Chesterfield Report is built in the open and improved often. '
          'Here is what we have shipped lately. Have an idea for what we should build next? '
          '<a href="/tip.html">Tell us.</a></p>'
        + "".join(rows)
        + '<p class="cl-note">We update this page as we ship. '
          'Follow along, or <a href="/subscribe.html">get The Weekly Report</a>.</p>'
        + '</div>'
    )
    page = render._shell(body, len(items))
    page = render._inject_og(
        page, "What's New: The Chesterfield Report",
        "A running list of new features and updates to The Chesterfield Report, "
        "the hyperlocal news site for Chesterfield County, Virginia.",
        f"{render.SITE_URL}/changelog.html", og_type="website")
    out = PUBLIC / "changelog.html"
    out.write_text(page, encoding="utf-8")
    return out
