"""Chesterfield County School Board tracker -> public/school-board.html.

Profiles the five elected School Board members (one per magisterial district),
the superintendent, the meeting schedule and how to comment, official CCPS links,
and each member's public campaign-finance profile via the Virginia Public Access
Project (VPAP). Mirrors the Board of Supervisors tracker (board.py) but for the
body that governs Chesterfield County Public Schools.

Membership verified against the official CCPS board page (oneccps.org) on
2026-06-15: emails confirmed on the live roster; the four elected members' phones
confirmed. Campaign-finance figures are public record via VPAP and are presented
factually and neutrally (we link to each profile rather than restating figures).

Stdlib only; reuses render._shell().
"""
from __future__ import annotations

import html

from . import render
from .render import PUBLIC

CCPS_BOARD = "https://www.oneccps.org/page/school-board"

# Order: Chair, Vice-Chair, then remaining members by district.
MEMBERS = [
    {
        "name": "Lisa Martin Hudgins", "district": "Midlothian", "role": "Chair",
        "term": "2024–2027", "email": "lisa_hudgins@ccpsnet.net", "phone": "804-543-7948",
        "bio": ("Elected in 2023 and chosen board chair in January 2026. A retired, "
                "award-winning English and journalism teacher (Midlothian High and Hanover "
                "High) with a bachelor's in English and a master's in English education from VCU."),
        "vpap": "https://www.vpap.org/candidates/454989-lisa-martin-hudgins/",
    },
    {
        "name": "Steven A. Paranto", "district": "Matoaca", "role": "Vice-Chair",
        "term": "2024–2027", "email": "steven_paranto@ccpsnet.net", "phone": "804-543-7992",
        "bio": ("Elected in 2023 and chosen board vice-chair in January 2026. Spent nearly "
                "two decades in the logistics and supply-chain industry."),
        "vpap": "https://www.vpap.org/candidates/443295-steve-paranto/",
    },
    {
        "name": "Ann Crawley Coker", "district": "Bermuda", "role": "Member",
        "term": "2024–2027", "email": "ann_coker@ccpsnet.net", "phone": "804-543-7407",
        "bio": ("First elected in 2019 and now in her second term; she chaired the board in "
                "2025. A product of Chesterfield schools, she has worked at ITAC for more than "
                "20 years and holds a degree from Longwood University."),
        "vpap": "https://www.vpap.org/candidates/332234-ann-crawley-coker/",
    },
    {
        "name": "Dr. Jenna Darby", "district": "Clover Hill", "role": "Member (interim)",
        "term": "Appointed 2026", "email": "jenna_darby@ccpsnet.net", "phone": "",
        "bio": ("Appointed interim Clover Hill representative effective January 2026, after "
                "Dot Heffron resigned in September 2025. She has 21 years in education and is "
                "adjunct faculty at VCU and the University of Richmond, with a doctorate in "
                "educational psychology from VCU. A special election will fill the remainder of "
                "the term."),
        "vpap": "",
    },
    {
        "name": "Dominique Renee Chatters", "district": "Dale", "role": "Member",
        "term": "2024–2027", "email": "dominique_chatters@ccpsnet.net", "phone": "804-543-6780",
        "bio": ("Elected in 2023, reported as the first Black woman elected to local office in "
                "Chesterfield County. A retired U.S. Army major who works as an educator for the "
                "Army Sustainment University, with degrees from Morgan State and Southern New "
                "Hampshire University."),
        "vpap": "https://www.vpap.org/candidates/454473-dominique-renee-chatters/",
    },
]

SUPERINTENDENT = ("Dr. John Murray", "Superintendent of Chesterfield County Public Schools, "
                  "appointed effective January 2025")

LINKS = [
    ("Official CCPS School Board page", CCPS_BOARD,
     "Members, districts, policies and contact information."),
    ("Meeting agendas &amp; video (BoardDocs)", "https://go.boarddocs.com/vsba/chesterfield/Board.nsf/Public",
     "Official agendas, materials and the meeting record."),
    ("School Board F.A.Q.", "https://www.oneccps.org/page/school-board-faq",
     "Meeting schedule and how to speak at a meeting."),
    ("Superintendent's office", "https://www.oneccps.org/page/superintendent",
     "The division's chief executive, hired by the board."),
]


def _card(m: dict) -> str:
    role = m["role"]
    is_lead = role in ("Chair", "Vice-Chair")
    badge = f'<span class="sb-role{" sb-lead" if is_lead else ""}">{html.escape(role)}</span>'
    contact = []
    if m["email"]:
        contact.append(f'<a href="mailto:{html.escape(m["email"])}">{html.escape(m["email"])}</a>')
    if m["phone"]:
        contact.append(f'<a href="tel:{m["phone"].replace("-", "")}">{html.escape(m["phone"])}</a>')
    contact_html = f'<div class="sb-contact">{" &middot; ".join(contact)}</div>' if contact else ""
    vpap_html = ""
    if m["vpap"]:
        vpap_html = (f'<a class="sb-vpap" href="{html.escape(m["vpap"])}" target="_blank" '
                     f'rel="noopener">Campaign finance on VPAP &nearr;</a>')
    return (
        f'<article class="sb-card{" is-lead" if is_lead else ""}">'
        f'<div class="sb-head"><span class="sb-district">{html.escape(m["district"])} District</span>{badge}</div>'
        f'<h3 class="sb-name">{html.escape(m["name"])}</h3>'
        f'<p class="sb-term">Term: {html.escape(m["term"])}</p>'
        f'<p class="sb-bio">{m["bio"]}</p>'
        f'{contact_html}{vpap_html}'
        '</article>'
    )


_CSS = """<style>
.sb-wrap{max-width:900px;margin:0 auto;}
.sb-lead-p{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:64ch;margin:.4rem 0 1rem;}
.sb-super{margin:0 0 1.6rem;padding:.85rem 1.1rem;border-left:3px solid var(--accent);background:var(--surface-card);
  border-radius:var(--radius-xs);font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);}
.sb-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;}
.sb-card{border:1px solid var(--border);border-radius:var(--radius-sm);padding:1.1rem 1.2rem;background:var(--surface-card);}
.sb-card.is-lead{border-color:var(--accent);}
.sb-head{display:flex;justify-content:space-between;align-items:center;gap:8px;}
.sb-district{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);}
.sb-role{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;
  color:var(--text-secondary);border:1px solid var(--border);border-radius:999px;padding:.2rem .5rem;}
.sb-role.sb-lead{background:var(--accent);color:#fff;border-color:var(--accent);}
.sb-name{font:var(--fw-bold) var(--fs-lg)/1.15 var(--font-display);margin:.5rem 0 .2rem;}
.sb-term{font:var(--fs-2xs) var(--font-mono);color:var(--text-tertiary);margin:0 0 .5rem;}
.sb-bio{font:var(--fs-sm)/1.5 var(--font-sans);color:var(--text-secondary);margin:0 0 .6rem;}
.sb-contact{font:var(--fs-2xs)/1.5 var(--font-sans);margin:.2rem 0;}
.sb-contact a{color:var(--accent);font-weight:600;}
.sb-vpap{display:inline-block;margin-top:.4rem;font:var(--fw-semibold) var(--fs-2xs) var(--font-sans);color:var(--accent);}
.sb-sec{margin:2.2rem 0;}
.sb-sec h2{font:var(--fw-bold) var(--fs-xl)/1.15 var(--font-display);margin:0 0 .5rem;}
.sb-sec p{font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:66ch;}
.sb-links{list-style:none;padding:0;margin:.5rem 0;}
.sb-links li{padding:.5rem 0;border-top:1px solid var(--border);}
.sb-links a{color:var(--accent);font-weight:600;}
.sb-links span{display:block;font:var(--fs-2xs)/1.4 var(--font-sans);color:var(--text-tertiary);}
.sb-xlinks{margin:1.4rem 0 0;font:var(--fs-sm)/1.7 var(--font-sans);color:var(--text-secondary);}
.sb-xlinks a{color:var(--accent);font-weight:600;}
.sb-note{margin-top:2rem;font:var(--fs-2xs)/1.5 var(--font-sans);color:var(--text-tertiary);}
</style>"""


def build_school_board() -> str:
    cards = "".join(_card(m) for m in MEMBERS)
    links = "".join(
        f'<li><a href="{u}" target="_blank" rel="noopener">{t}</a><span>{d}</span></li>'
        for t, u, d in LINKS)
    body = (
        _CSS
        + '<div class="sb-wrap">'
        + '<h1 class="page-title">Chesterfield County School Board</h1>'
        + '<p class="sb-lead-p">The School Board is the five-member elected body that governs '
          'Chesterfield County Public Schools, one member from each magisterial district. It sets '
          'the school budget and policy and hires the superintendent. The current four-year term '
          'began January 2024.</p>'
        + f'<div class="sb-super"><strong>Superintendent:</strong> {html.escape(SUPERINTENDENT[0])}, '
          f'{SUPERINTENDENT[1]}. The superintendent runs the division day to day and is hired by '
          'and reports to the board.</div>'
        + f'<div class="sb-grid">{cards}</div>'

        + '<div class="sb-sec"><h2>Meetings &amp; how to weigh in</h2>'
          '<p>The board meets roughly monthly at the Public Meeting Room, 10001 Iron Bridge Road: '
          'work sessions around 4 p.m. and business meetings around 6:30 p.m. Meetings are carried '
          'on Comcast channel 98 and Verizon channel 28, livestreamed, and archived on the division '
          'YouTube channel. To speak, notify the School Board Clerk’s office by 2 p.m. on the day '
          'of the meeting; speakers are limited to four minutes (School Board Policy 1110). '
          'Clerk’s office: 804-348-8011.</p></div>'

        + '<div class="sb-sec"><h2>Official sources</h2>'
          f'<ul class="sb-links">{links}</ul></div>'

        + '<div class="sb-xlinks">Related: <a href="/schools.html">Chesterfield schools directory</a> '
          '&middot; <a href="/meetings.html">Meetings</a> &middot; '
          '<a href="/taxes.html">Where your taxes go</a> (schools are about 40% of the county budget) '
          '&middot; <a href="/board.html">Board of Supervisors</a></div>'

        + '<p class="sb-note">Membership and contacts verified against the official CCPS School '
          'Board page. Campaign-finance profiles are public record via the Virginia Public Access '
          'Project and are linked, not restated. Spotted something out of date? '
          '<a href="/tip.html">Let us know.</a></p>'
        + '</div>'
    )
    page = render._shell(body)
    page = render._inject_og(
        page, "Chesterfield County School Board",
        "The five elected members who govern Chesterfield County Public Schools, by district, "
        "with contact info, meeting schedule, and campaign-finance links.",
        "https://chesterfieldreport.com/school-board.html")
    out = PUBLIC / "school-board.html"
    out.write_text(page, encoding="utf-8")
    return out
