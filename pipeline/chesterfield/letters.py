"""Letters to the Editor — consented community opinion.

Two pieces:
  * build_form() -> public/letters.html: a public submission form you can share
    (e.g. in Facebook community groups). It posts to Web3Forms (free, no
    backend) which emails each submission to you. No scraping, full consent.
  * create_draft(): turn a received submission into a clearly-labeled OPINION
    draft in your review queue. You approve it like anything else; it publishes
    as an Opinion (badge + byline + disclaimer), kept separate from news. The AI
    editor never auto-publishes opinions (ai_provider 'letter' fails the belt).
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path

from . import render

DISCLAIMER = ("This is a reader-submitted opinion, not reporting by The "
              "Chesterfield Report. Letters reflect the views of their authors "
              "and may be edited for length and clarity.")


def create_draft(subject: str, body: str, name: str = "",
                 anonymous: bool = False, neighborhood: str = "") -> Path:
    """Write a received letter as an OPINION draft for review."""
    byline = "Anonymous" if anonymous or not name.strip() else name.strip()
    if neighborhood.strip():
        byline += f", {neighborhood.strip()}"
    date = datetime.now(timezone.utc).date().isoformat()
    slug = (re.sub(r"[^a-z0-9]+", "-", subject.lower()).strip("-")[:55] or "letter")
    render.DRAFTS.mkdir(parents=True, exist_ok=True)
    path = render.DRAFTS / f"{date}-opinion-{slug}.md"
    fm = [
        "---", "status: draft",
        f"headline: {render._yaml_escape(subject)}",
        'source: "Letter to the Editor"', 'source_url: ""', "license: opinion",
        "focus: [Community]", "tags: [Opinion, Letter to the Editor]",
        'location: ""', 'image: ""', 'video_url: ""', "media_kind: ",
        "opinion: true",
        f"byline: {render._yaml_escape('By ' + byline)}",
        "ai_provider: letter", "---", "",
        f"# {subject}", "",
        f"_Letter to the Editor — {byline}_", "",
    ]
    for para in re.split(r"\n\s*\n", body.strip()):
        p = para.strip().replace("\n", " ")
        if p:
            fm += [p, ""]
    fm += [f"_{DISCLAIMER}_", ""]
    path.write_text("\n".join(fm), encoding="utf-8")
    return path


_FORM = """
<h1 class="page-title">Letter to the Editor</h1>
<p class="lead">Have something to say about Chesterfield County? Share your view.
Selected letters run as <strong>Opinion</strong> on The Chesterfield Report &mdash;
with your name or anonymously, your call.</p>

<div class="letter-guidelines">
  <strong>A few guidelines:</strong> keep it civil and roughly under 400 words,
  about Chesterfield County, and your own words. We verify and may edit for
  length/clarity. Not every letter runs &mdash; the editor decides. No personal
  attacks, no unverified accusations.
</div>

{notice}

<form class="letter-form" action="https://api.web3forms.com/submit" method="POST">
  <input type="hidden" name="access_key" value="{key}">
  <input type="hidden" name="subject" value="New Letter to the Editor — The Chesterfield Report">
  <input type="hidden" name="from_name" value="Chesterfield Report — Letters">
  <input type="hidden" name="redirect" value="https://chesterfieldreport.com/letters.html?ok=1">
  <input type="checkbox" name="botcheck" class="hp" tabindex="-1" autocomplete="off">

  <label>Your name <span class="opt">(or check anonymous below)</span></label>
  <input type="text" name="Name" autocomplete="name">

  <label class="check"><input type="checkbox" name="Publish anonymously" value="yes"> Publish my letter anonymously</label>

  <label>Email <span class="opt">(required &mdash; for verification only, never published)</span></label>
  <input type="email" name="email" required autocomplete="email">

  <label>Neighborhood / district <span class="opt">(optional)</span></label>
  <input type="text" name="Neighborhood" placeholder="e.g. Midlothian, Chester, Matoaca…">

  <label>What is your letter about?</label>
  <input type="text" name="Topic" required placeholder="A short subject line">

  <label>Your letter</label>
  <textarea name="Letter" rows="9" required placeholder="Write your opinion here…"></textarea>

  <label class="check"><input type="checkbox" name="Consent" value="yes" required>
    This is my own opinion and I consent to it being published (with my name or
    anonymously as I chose), possibly edited for length and clarity.</label>

  <button type="submit" class="letter-btn">Submit your letter</button>
</form>
"""

_NOTICE_OFF = ('<div class="letter-notice">⚠️ The submission form isn\'t active yet '
               '— add a free Web3Forms key (WEB3FORMS_KEY in scripts/.deploy.env, '
               'get one in 30s at web3forms.com) and rebuild.</div>')

_THANKS_JS = """
<script>if(location.search.indexOf('ok=1')>-1){var f=document.querySelector('.letter-form');
if(f){f.outerHTML='<div class=\\"letter-thanks\\"><h2>Thank you &mdash; your letter is in.</h2>'+
'<p>We read every submission. If it runs, it\\'ll appear in Opinion.</p>'+
'<p><a href=\\"/\\">&larr; Back to The Chesterfield Report</a></p></div>';}}</script>
"""

_CSS = """<style>
.letter-guidelines{background:rgba(39,230,198,.07);border:1px solid var(--line);
 border-left:3px solid var(--neon);border-radius:10px;padding:.9rem 1.1rem;margin:0 0 1.4rem;font-size:.95rem;color:var(--ink)}
.letter-notice,.letter-thanks{background:rgba(216,162,58,.12);border:1px solid var(--gold);
 border-radius:10px;padding:.9rem 1.1rem;margin:0 0 1.3rem;color:var(--ink)}
.letter-thanks h2{font-family:var(--serif);color:var(--neon);margin:.2rem 0 .5rem}
.letter-form{max-width:640px}
.letter-form label{display:block;font-family:var(--mono);font-size:.74rem;font-weight:700;
 text-transform:uppercase;letter-spacing:.06em;color:var(--neon);margin:1.1rem 0 .35rem}
.letter-form label.check{font-family:var(--sans);text-transform:none;letter-spacing:0;
 font-size:.92rem;font-weight:400;color:var(--ink);display:flex;gap:.5rem;align-items:flex-start;margin:.8rem 0}
.letter-form .opt{color:var(--muted);font-weight:400;text-transform:none;letter-spacing:0}
.letter-form input[type=text],.letter-form input[type=email],.letter-form textarea{
 width:100%;font:inherit;padding:.6rem .7rem;background:var(--bg2);color:var(--ink);
 border:1px solid var(--line);border-radius:8px}
.letter-form textarea{resize:vertical}
.letter-form .hp{position:absolute;left:-9999px}
.letter-btn{margin-top:1.3rem;background:var(--neon);color:#04141a;font-weight:800;
 border:0;border-radius:10px;padding:.8rem 1.4rem;font-size:1rem;cursor:pointer}
.letter-btn:hover{box-shadow:0 0 18px rgba(39,230,198,.5)}
.op-sep{border:0;border-top:1px solid var(--line);margin:2.4rem 0 1.8rem}
</style>"""


def _opinion_section() -> str:
    """Summary cards for every published Opinion piece, newest first. Shown
    above the submission form so the Opinion page is a real section, not just a
    form. Returns '' when nothing is published yet."""
    recs = [(m, b, n) for m, b, n in render._published_records()
            if (m.get("opinion", "") or "").strip().lower() in ("true", "1", "yes")]
    if not recs:
        return ""
    cards = "\n".join(render._summary_card(m, b, n) for m, b, n in recs)
    return ('<h1 class="page-title">Opinion</h1>'
            '<p class="lead">Reader letters and editorials on Chesterfield County. '
            'Opinion is kept separate from our news reporting. '
            '<a href="#submit">Send your own &darr;</a></p>'
            f'<div class="feed">{cards}</div>'
            '<hr class="op-sep" id="submit">')


def build_form(out: str = "public/letters.html") -> Path:
    key = os.environ.get("WEB3FORMS_KEY", "").strip()
    notice = "" if key else _NOTICE_OFF
    body = (_CSS
            + _opinion_section()
            + _FORM.format(key=key or "MISSING_WEB3FORMS_KEY", notice=notice)
            + _THANKS_JS)
    path = render.PUBLIC / "letters.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render._shell(body, 0), encoding="utf-8")
    return path
