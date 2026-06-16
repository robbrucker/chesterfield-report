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


# Campaign finance, 2023 election cycle, from the Virginia Department of Elections
# official filings (cfreports.elections.virginia.gov), the authoritative source
# VPAP republishes. Figures reconcile to each committee's final 2023 report.
# Darby was appointed (no committee). Presented factually; donors link nowhere
# except the official committee report.
FINANCE = {
    "Lisa Martin Hudgins": {
        "committee": "Friends of Lisa Hudgins", "raised": "$18,199", "spent": "$17,193",
        "cash": "$1,006", "source": "https://cfreports.elections.virginia.gov/Committee/Index/7b5b58b8-c4ea-47a1-a2ab-314950246ec0",
        "donors": [("Emerson Ventures LLC", "$1,500"), ("Lisa Hudgins (self)", "$1,025"),
                   ("Charles Floyd", "$1,000"), ("Susan Cheatham", "$1,000"),
                   ("Chesterfield County Republican Committee", "$1,000"),
                   ("Kumareshan Ramanathan", "$1,000"), ("Friends of Jim Ingle", "$500"),
                   ("Robin Ross", "$500"), ("Chesterfield Forward PAC", "$450"),
                   ("Andy Anderson", "$400")],
    },
    "Steven A. Paranto": {
        "committee": "Friends of Steven Paranto", "raised": "$14,038", "spent": "$10,230",
        "cash": "$3,808", "source": "https://cfreports.elections.virginia.gov/Committee/Index/ec5350ac-8caa-42a5-b978-a5895e2d466e",
        "donors": [("Friends of Kevin Carroll", "$2,600"), ("Richmond Build PAC", "$1,500"),
                   ("William Baker", "$1,100"), ("Emerson Companies, LLC", "$1,000"),
                   ("Oakbridge Corporation", "$1,000"),
                   ("Chesterfield County Republican Committee", "$1,000"),
                   ("James Womack", "$500"), ("Friends of Amanda Chase", "$500"),
                   ("Friends of Mike Cherry", "$500"), ("Friends of Jim Ingle", "$500")],
    },
    "Ann Crawley Coker": {
        "committee": "Friends of Ann Coker", "raised": "$9,564", "spent": "$9,939",
        "cash": "$125", "source": "https://cfreports.elections.virginia.gov/Committee/Index/c03860e3-a728-e911-8236-984be103f032",
        "donors": [("Industrial TurnAround Corp. (ITAC)", "$2,000"),
                   ("George and Darlene Emerson", "$1,000"),
                   ("Chesterfield County Republican Committee", "$1,000"),
                   ("Realtors PAC of Virginia", "$750"), ("Patricia and James Crawley", "$500"),
                   ("Gib Sloan", "$500"), ("Friends of Jim Ingle", "$500"),
                   ("Huguenot Republican Woman's Club", "$375"),
                   ("Friends of Mike Cherry", "$250"), ("Megan Carson", "$103")],
    },
    "Dominique Renee Chatters": {
        "committee": "Friends of Dominique Chatters", "raised": "$29,955", "spent": "$24,672",
        "cash": "$5,282", "source": "https://cfreports.elections.virginia.gov/Committee/Index/2b7e673b-7872-4206-97d0-a83e35427f88",
        "note": "Some top contributions are in-kind (goods/services) rather than cash.",
        "donors": [("Rene Cross (Bronx, NY)", "$3,046"), ("Mollee Sullivan (in-kind)", "$3,000"),
                   ("Dominique Chatters (self)", "$2,815"), ("Vaughn Thompson", "$1,000"),
                   ("Pamela Johnson", "$1,000"), ("Sarah O'Neill", "$1,000"),
                   ("Barbara Favola (state senator)", "$1,000"), ("Glen Besa", "$675"),
                   ("Jennifer Wesley", "$500"), ("Chesterfield Education Association", "$500")],
    },
}


def _finance_block(m: dict) -> str:
    fin = FINANCE.get(m["name"])
    if not fin:
        if "interim" in m["role"].lower() or "appoint" in m.get("term", "").lower():
            return ('<div class="sb-fin"><h4>Campaign finance</h4>'
                    '<p class="sb-fin-note">Appointed to the seat, so there is no campaign '
                    'committee or donor record on file.</p></div>')
        return ""
    rows = "".join(f'<li><span class="sb-don-name">{html.escape(n)}</span>'
                   f'<span class="sb-don-amt">{html.escape(a)}</span></li>' for n, a in fin["donors"])
    note = f'<p class="sb-fin-note">{html.escape(fin["note"])}</p>' if fin.get("note") else ""
    return (
        '<div class="sb-fin"><h4>Campaign finance <span>2023 election cycle</span></h4>'
        '<div class="sb-fin-figs">'
        f'<div><b>{fin["raised"]}</b><span>Raised</span></div>'
        f'<div><b>{fin["spent"]}</b><span>Spent</span></div>'
        f'<div><b>{fin["cash"]}</b><span>Cash on hand</span></div>'
        '</div>'
        '<div class="sb-don-head">Top donors</div>'
        f'<ul class="sb-donors">{rows}</ul>'
        f'{note}'
        f'<a class="sb-fin-src" href="{html.escape(fin["source"])}" target="_blank" rel="noopener">'
        f'Full filing: {html.escape(fin["committee"])}, VA Dept. of Elections &nearr;</a>'
        '</div>'
    )


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
                     f'rel="noopener">Same record on VPAP &nearr;</a>')
    return (
        f'<article class="sb-card{" is-lead" if is_lead else ""}">'
        f'<div class="sb-head"><span class="sb-district">{html.escape(m["district"])} District</span>{badge}</div>'
        f'<h3 class="sb-name">{html.escape(m["name"])}</h3>'
        f'<p class="sb-term">Term: {html.escape(m["term"])}</p>'
        f'<p class="sb-bio">{m["bio"]}</p>'
        f'{contact_html}'
        f'{_finance_block(m)}{vpap_html}'
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
.sb-vpap{display:inline-block;margin-top:.5rem;font:var(--fw-semibold) var(--fs-3xs) var(--font-sans);color:var(--text-tertiary);}
.sb-fin{margin-top:.8rem;padding-top:.7rem;border-top:1px solid var(--border);}
.sb-fin h4{font:var(--fw-bold) var(--fs-2xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;
  color:var(--text-secondary);margin:0 0 .5rem;}
.sb-fin h4 span{color:var(--text-tertiary);font-weight:400;}
.sb-fin-figs{display:flex;gap:14px;margin:0 0 .6rem;}
.sb-fin-figs div{flex:1;}
.sb-fin-figs b{display:block;font:var(--fw-bold) var(--fs-md)/1 var(--font-display);color:var(--accent);}
.sb-fin-figs span{font:var(--fs-3xs)/1.3 var(--font-sans);color:var(--text-tertiary);}
.sb-don-head{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-sans);text-transform:uppercase;letter-spacing:var(--ls-wide);
  color:var(--text-tertiary);margin:.4rem 0 .3rem;}
.sb-donors{list-style:none;padding:0;margin:0 0 .5rem;}
.sb-donors li{display:flex;justify-content:space-between;gap:8px;padding:.22rem 0;border-bottom:1px solid var(--border);
  font:var(--fs-2xs)/1.3 var(--font-sans);}
.sb-don-name{color:var(--text-secondary);}
.sb-don-amt{color:var(--text-primary);font-weight:600;white-space:nowrap;}
.sb-fin-note{font:italic var(--fs-3xs)/1.4 var(--font-sans);color:var(--text-tertiary);margin:.3rem 0;}
.sb-fin-src{display:block;margin-top:.4rem;font:var(--fw-semibold) var(--fs-3xs) var(--font-sans);color:var(--accent);}
.sb-fin-flag{margin:1.2rem 0;padding:.7rem 1rem;background:var(--surface-card);border-left:3px solid var(--accent);
  border-radius:var(--radius-xs);font:var(--fs-2xs)/1.5 var(--font-sans);color:var(--text-secondary);}
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

        + '<p class="sb-fin-flag">Campaign-finance figures above are from the <strong>2023 '
          'election cycle</strong>, the last time these seats were on the ballot. The next '
          'regular School Board election is <strong>November 2027</strong>; a special election '
          'for the appointed Clover Hill seat is expected before then. Figures will be updated '
          'when new filings are reported.</p>'

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
          'Board page. Campaign-finance figures are from each candidate’s 2023-cycle filings with '
          'the Virginia Department of Elections (public record); the listed donors are the largest '
          'itemized contributors, and the full filing is linked on each card. Dr. Darby was '
          'appointed, so she has no campaign committee. Spotted something out of date? '
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
