"""Board of Supervisors tracker for Chesterfield County.

Builds public/board.html, a rich civic page that:
  * Profiles all five magisterial-district supervisors (bio, tenure, election
    history, committees, contact, and a neutral, sourced "top campaign donors"
    block via the Virginia Public Access Project / VPAP).
  * Aggregates Board / Government coverage from our published stories.
  * "Upcoming meetings & dates" parsed from any `## Key dates` sections.
  * "Watch the meetings" — county video stories embedded as thumbnails.
  * A prominent block of WORKING links to official county sources (Board page,
    Agenda Center / Legistar) plus each district's VPAP campaign-finance profile.

Membership verified from chesterfield.gov on 2026-06-08. The current four-year
term began Jan 1, 2024 (after the Nov 2023 election); the Dale seat is held by
an interim appointee following the Oct 2025 death of Supervisor Jim Holland,
with a special election scheduled for Nov 2026.

Campaign-finance figures are PUBLIC RECORD via vpap.org and are presented
factually and neutrally. Where detailed donor tables could not be machine-read
at build time, the profile links to the supervisor's VPAP page rather than
inventing figures.

Stdlib-only; reuses render._shell() for the cyberpunk chrome.
"""
from __future__ import annotations

import html
import re
from datetime import date, datetime, timezone

from . import render
from .render import (
    PUBLIC, _pretty_date, _primary_focus, _published_records,
    media_html, slugify, story_url,
)

# Keywords that flag a story as Board-of-Supervisors / civic-governance related,
# even when its primary focus isn't "Government".
_GOV_KEYWORDS = re.compile(
    r"\b(board of supervisors|supervisor|rezoning|rezone|budget|"
    r"public hearing|ordinance|referendum|comprehensive plan|"
    r"planning commission|county administrator)\b",
    re.IGNORECASE,
)

# County / government video channels (source names) worth featuring as
# "watch the meetings" embeds.
_COUNTY_VIDEO_HINTS = ("chesterfield county", "county (youtube)", "government", "sheriff", "police")

OFFICIAL_LINKS = [
    ("Board of Supervisors", "https://www.chesterfield.gov/1218/Board-of-Supervisors",
     "Members, districts, meeting schedule and contact info."),
    ("County Agenda Center / Legistar", "https://chesterfield.legistar.com/",
     "Official agendas, minutes, and the legislative record."),
    ("Board meetings & schedule", "https://www.chesterfield.gov/1231/Board-Meetings",
     "Meeting calendar, livestream and how to speak at a public hearing."),
]


# ---------------------------------------------------------------------------
# SUPERVISOR PROFILES
#
# Every fact below is attributed to a cited source listed in the profile's
# `sources` list. Photo URLs were verified to return image/jpeg from
# chesterfield.gov on 2026-06-08. Campaign-finance is labeled as public record
# via VPAP, with the cycle/date and a link to the VPAP profile.
# ---------------------------------------------------------------------------

CHESTERFIELD = "https://www.chesterfield.gov"

SUPERVISORS = [
    {
        "name": "Jim A. Ingle",
        "district": "Bermuda",
        "title": "Supervisor",
        "party": "Republican",
        "photo": CHESTERFIELD + "/ImageRepository/Document?documentId=14084",
        "page": CHESTERFIELD + "/1238/Bermuda-District---Ingle",
        "email": "IngleJ@chesterfield.gov",
        "phone": "804-768-7398",
        "bio": (
            "A local businessman, community volunteer and longtime Bermuda "
            "District resident who spent much of his youth in Woodbridge. He "
            "earned an associate degree in business from Richard Bland College "
            "and a bachelor's in economics from the College of William &amp; Mary, "
            "and worked as a senior project manager at construction firm RJ "
            "Smith. He spent roughly two decades volunteering as a missionary at "
            "the Bon Air Juvenile Correctional Center and served as a Cub Scout "
            "Cubmaster and Boy Scout troop committee member."
        ),
        "tenure": (
            "First elected in 2019; re-elected in November 2023 to a second "
            "four-year term that began Jan. 1, 2024. Served as Board Vice-Chair "
            "in 2023 and as Chair in 2025."
        ),
        "election": (
            "In the Nov. 7, 2023 general election he defeated Democrat Lindsey "
            "Dougherty, winning by fewer than 1,000 votes."
        ),
        "committees": [
            "County Audit and Finance Committee",
            "Capital Region Workforce Partnership (Chief Local Elected Officials Consortium)",
            "Crater Planning District Commission",
            "GRTC Transit System Board of Directors",
            "PlanRVA",
            "Richmond Region Tourism Board",
            "Social Services Board",
            "Henricus Foundation Board",
        ],
        "vpap": "https://www.vpap.org/candidates/331380-jim-ingle/",
        "finance": {
            "raised": "$121,126.54",
            "spent": "$89,020.68",
            "period": "2023 election cycle (cumulative)",
            "as_of": "as of the Oct. 2023 pre-election report",
            "committee": "Friends of Jim Ingle (CC-19-00297)",
            "source_label": "Va. Dept. of Elections — Friends of Jim Ingle, Schedule H",
            "source_url": "https://cfreports.elections.virginia.gov/Committee/Index/ac6d8a91-2436-e911-936e-984be103f032",
        },
        "vpap_note": (
            "Cycle totals and donors below are from the committee's official "
            "Schedule A/H filings with the Virginia Department of Elections "
            "(committee: Friends of Jim Ingle, CC-19-00297). Donors are the "
            "largest itemized contributions on the Sept. and Oct. 2023 "
            "pre-election reports."
        ),
        "donors": [
            ("Chesterfield Professional Firefighters Assn.", "$2,500"),
            ("Realtor PAC (RPAC)", "$2,250"),
            ("Chesterfield Small Business PAC", "$1,500"),
            ("Dennis Harrup", "$1,041"),
            ("Chesterfield County Republican Committee", "$1,000"),
            ("Francis G. Sloan III", "$750"),
            ("Brenda White", "$200"),
        ],
        "donor_sectors": (
            "Largest itemized 2023 donors span the local firefighters' "
            "association, the Realtor PAC, a small-business PAC and the county "
            "Republican committee, plus individual contributors."
        ),
        "sources": [
            ("Chesterfield County — Bermuda District (Ingle)", CHESTERFIELD + "/1238/Bermuda-District---Ingle"),
            ("VA Dept. of Elections — Friends of Jim Ingle (filings)", "https://cfreports.elections.virginia.gov/Committee/Index/ac6d8a91-2436-e911-936e-984be103f032"),
            ("VPAP — Jim Ingle", "https://www.vpap.org/candidates/331380-jim-ingle/"),
        ],
    },
    {
        "name": "Jessica L. Schneider",
        "district": "Clover Hill",
        "title": "Supervisor",
        "party": "Democrat",
        "photo": CHESTERFIELD + "/DocumentCenter/View/35319/Jessica-Schneider",
        "page": CHESTERFIELD + "/1246/Clover-Hill-District---Schneider",
        "email": "schneiderjes@chesterfield.gov",
        "phone": "804-768-7396",
        "bio": (
            "A community advocate raised in rural Wisconsin, Schneider spent the "
            "first decade of her career in the restaurant industry before earning "
            "a degree in interior design and working in freelance staging and "
            "design for commercial and residential clients. She served seven years "
            "with her homeowners association — on the architectural committee, as "
            "a board director and four years as board president — and sits on the "
            "Manchester YMCA board."
        ),
        "tenure": (
            "Elected in November 2023 and sworn into office Dec. 21, 2023; "
            "currently serving her first four-year term."
        ),
        "election": (
            "Won the open Clover Hill seat in the Nov. 7, 2023 general election. "
            "Itemized vote totals are available via VPAP and the Virginia "
            "Department of Elections (linked in Sources)."
        ),
        "committees": [
            "Capital Region Airport Commission",
            "Greater Richmond Partnership, Inc. Board of Directors",
            "Henricus Foundation Board",
            "Joint Subcommittee to Study the Consolidation and Scheduling of General Elections",
            "Manchester YMCA Board of Directors",
            "Maymont Foundation Board of Directors",
            "PlanRVA",
            "Richmond Metropolitan Transportation Authority",
            "Richmond Regional Transportation Planning Organization",
        ],
        "vpap": "https://www.vpap.org/candidates/449162-jessica-l-schneider/",
        "finance": {
            "raised": "$26,313.18",
            "spent": "$23,804.02",
            "period": "2023 election cycle (cumulative)",
            "as_of": "as of the final 2023 cycle reports",
            "committee": "Friends of Jessica L Schneider (CC-22-00741)",
            "source_label": "Va. Dept. of Elections — Friends of Jessica L Schneider, Schedule H",
            "source_url": "https://cfreports.elections.virginia.gov/Committee/Index/d5fc0614-c557-4bd5-b897-d2953d9044b7",
        },
        "vpap_note": (
            "Cycle totals and donors below are from the committee's official "
            "Schedule A/H filings with the Virginia Department of Elections "
            "(committee: Friends of Jessica L Schneider, CC-22-00741). Donors "
            "are the largest itemized contributions across the 2023 reports."
        ),
        "donors": [
            ("Micheal Jones for Delegate (PAC)", "$1,000"),
            ("Stuart Broth", "$700"),
            ("Everytown for Gun Safety Action Fund", "$500"),
            ("Elaine Fishman", "$250"),
            ("Susan Greene", "$250"),
            ("CEA Fund for Children &amp; Public Education (PAC)", "$250"),
            ("Glen Besa", "$250"),
            ("Mickael Broth", "$250"),
            ("Lance Goetz", "$250"),
            ("Cole Kawugule", "$200"),
        ],
        "donor_sectors": (
            "Schneider's largest itemized donors are mostly small individual "
            "contributions, alongside a Democratic delegate's PAC, an education "
            "PAC and Everytown for Gun Safety's action fund."
        ),
        "sources": [
            ("Chesterfield County — Clover Hill District (Schneider)", CHESTERFIELD + "/1246/Clover-Hill-District---Schneider"),
            ("VA Dept. of Elections — Friends of Jessica L Schneider (filings)", "https://cfreports.elections.virginia.gov/Committee/Index/d5fc0614-c557-4bd5-b897-d2953d9044b7"),
            ("VPAP — Jessica L. Schneider", "https://www.vpap.org/candidates/449162-jessica-l-schneider/"),
        ],
    },
    {
        "name": "LeQuan M. Hylton, Ph.D.",
        "district": "Dale",
        "title": "Interim Supervisor",
        "party": "Not publicly stated",
        "photo": CHESTERFIELD + "/ImageRepository/Document?documentId=45562",
        "page": CHESTERFIELD + "/1244/Dale-District---Hylton",
        "email": "HyltonL@chesterfield.gov",
        "phone": "804-768-7528",
        "bio": (
            "A licensed Realtor and builder, and a lieutenant colonel in the U.S. "
            "Army Reserve who is a combat veteran of Afghanistan with command "
            "experience in logistics, engineering, construction and acquisition. "
            "He holds a B.S. in business management from Virginia State "
            "University, an MBA from Averett University and a Ph.D. in public "
            "policy and administration from VCU, plus certificates from UVA's "
            "Sorensen Institute and Harvard Business School. He served on the "
            "Chesterfield Planning Commission (2019&ndash;2025), co-chaired the county's "
            "Affordable Housing Working Group, and is active with the Southside "
            "Virginia Association of Realtors and Saint Paul's Baptist Church."
        ),
        "tenure": (
            "Appointed interim Dale District supervisor by the Board on Nov. 12, "
            "2025 and sworn in the same day, succeeding the late James M. \"Jim\" "
            "Holland (who died Oct. 14, 2025 after 17+ years of service). Holland "
            "asked his colleagues to select Hylton on an interim basis."
        ),
        "election": (
            "Not elected — appointed to fill a vacancy. A special election in "
            "November 2026 will determine who serves the remainder of Holland's "
            "term."
        ),
        "committees": [
            "Capital Region Airport Commission",
            "Richmond Regional Transportation Planning Organization",
            "PlanRVA",
        ],
        "vpap": "https://www.vpap.org/localities/chesterfield-county-va/elections/",
        "finance": {
            "raised": "Not available",
            "spent": "Not available",
            "period": "appointed interim — no supervisor campaign committee",
            "as_of": "",
            "committee": "",
            "source_label": "VPAP — Chesterfield County elections",
            "source_url": "https://www.vpap.org/localities/chesterfield-county-va/elections/",
        },
        "vpap_note": (
            "As an appointed interim supervisor, Hylton had no Chesterfield "
            "Board of Supervisors campaign committee on file with the Virginia "
            "Department of Elections at build time, so no raised/spent or donor "
            "figures exist yet. Any campaign finance tied to the Nov. 2026 "
            "special election will appear on the VPAP and Department of "
            "Elections links below."
        ),
        "donors": None,
        "sources": [
            ("Chesterfield County — Dale District (Hylton)", CHESTERFIELD + "/1244/Dale-District---Hylton"),
            ("Chesterfield County — Hylton appointed interim Dale supervisor", CHESTERFIELD + "/m/NewsFlash/Home/Detail/6772"),
            ("WRIC — Interim Dale District supervisor appointed", "https://www.wric.com/news/local-news/chesterfield-county/interim-dale-district-supervisor-appointed/"),
        ],
    },
    {
        "name": "Kevin P. Carroll",
        "district": "Matoaca",
        "title": "Vice-Chair",
        "party": "Republican",
        "photo": CHESTERFIELD + "/ImageRepository/Document?documentId=14082",
        "page": CHESTERFIELD + "/1242/Matoaca-District---Carroll",
        "email": "CarrollKevin@chesterfield.gov",
        "phone": "804-768-7400",
        "bio": (
            "A retired law-enforcement officer who joined the Chesterfield County "
            "Police Department in 1986, was promoted to sergeant in 1999 and "
            "retired in October 2018 after 32 years of service. Before policing he "
            "was a volunteer firefighter in Rhode Island."
        ),
        "tenure": (
            "First elected in 2019; re-elected in November 2023 to a second "
            "four-year term that began Jan. 1, 2024. Served as Board Vice-Chair "
            "in 2020, Chair in 2023, and was elected Vice-Chair again for 2026."
        ),
        "election": (
            "In the Nov. 7, 2023 general election he won re-election with 61.87% "
            "of the vote, defeating independent W.A. \"Chip\" Carbiener (36.76%)."
        ),
        "committees": [
            "Capital Region Airport Commission",
            "County Audit and Finance Committee",
            "Central Virginia Transportation Authority",
            "Chesterfield Police Athletic League",
            "Crater Planning District Commission",
            "Eppington Foundation Board",
            "PlanRVA",
            "Richmond Regional Transportation Planning Organization",
            "State Executive Council for Children's Services",
            "Tri-Cities Area Metropolitan Planning Organization",
        ],
        "vpap": "https://www.vpap.org/candidates/94984-kevin-carroll/",
        "finance": {
            "raised": "$122,489.06",
            "spent": "$98,475.35",
            "period": "2023 election cycle (cumulative)",
            "as_of": "as of the Oct. 2023 pre-election report",
            "committee": "Friends of Kevin Carroll (CC-19-00056)",
            "source_label": "Va. Dept. of Elections — Friends of Kevin Carroll, Schedule H",
            "source_url": "https://cfreports.elections.virginia.gov/Committee/Index/2424590a-e214-e911-94e1-984be103f032",
        },
        "vpap_note": (
            "Raised/spent are the 2023 election-cycle totals from the "
            "committee's official Schedule H filing with the Virginia "
            "Department of Elections (Friends of Kevin Carroll, CC-19-00056). "
            "The donor table aggregates top contributors across the "
            "2019&ndash;2024 reporting cycles, as published by VPAP (public "
            "record). Retrieved 2026-06-09."
        ),
        "donors": [
            ("Republican Party of Virginia", "$22,535"),
            ("Camp, Scott W", "$13,099"),
            ("Outlook at Saddle Ridge", "$7,500"),
            ("Chesterfield County Small Business PAC", "$5,000"),
            ("Emerson Builders", "$4,400"),
            ("American Performance LLC", "$4,000"),
            ("John Radcliffe", "$4,000"),
            ("Firefighters &ndash; Chesterfield", "$3,720"),
            ("Home Builders Assn of Va &ndash; Richmond", "$3,000"),
            ("Richmond Assn of Realtors", "$2,750"),
        ],
        "donor_sectors": (
            "Notable donor sectors include the Republican Party of Virginia, "
            "real-estate and home-building interests (Outlook at Saddle Ridge, "
            "Emerson Builders, Home Builders Assn of Va, Richmond Assn of "
            "Realtors), a small-business PAC, and the local firefighters' "
            "association."
        ),
        "sources": [
            ("Chesterfield County — Matoaca District (Carroll)", CHESTERFIELD + "/1242/Matoaca-District---Carroll"),
            ("VA Dept. of Elections — Friends of Kevin Carroll (filings)", "https://cfreports.elections.virginia.gov/Committee/Index/2424590a-e214-e911-94e1-984be103f032"),
            ("VPAP — Top Donors, Carroll committee", "https://www.vpap.org/committees/331379/top_donors/"),
            ("Ballotpedia — Chesterfield County elections, 2023", "https://ballotpedia.org/Chesterfield_County,_Virginia,_elections,_2023"),
        ],
    },
    {
        "name": "Mark S. Miller, Ph.D.",
        "district": "Midlothian",
        "title": "Chair",
        "party": "Democrat",
        "photo": CHESTERFIELD + "/ImageRepository/Document?documentId=30737",
        "page": CHESTERFIELD + "/1240/Midlothian-District---Miller",
        "email": "MillerMark@chesterfield.gov",
        "phone": "804-768-7397",
        "bio": (
            "A licensed professional counselor (LPC) and certified substance "
            "abuse counselor (CSAC) who has lived in Midlothian for more than 27 "
            "years. He spent 13 years with Chesterfield Mental Health, rising from "
            "senior clinician to services supervisor, and has worked the past nine "
            "years as a professional counselor at Brightpoint Community College "
            "(formerly J. Sargeant Reynolds/JTCC). He holds a B.A. in secondary "
            "English education from the University of Pittsburgh, an M.S. in "
            "psychology from Shippensburg University and a Ph.D. in clinical "
            "psychology from the California Institute of Integral Studies."
        ),
        "tenure": (
            "First elected in a November 2022 special election (sworn in Nov. 16, "
            "2022); re-elected in November 2023 to a full four-year term that "
            "began Jan. 1, 2024. Elected Board Chair for 2026."
        ),
        "election": (
            "Won the Midlothian seat in the Nov. 7, 2023 general election, with "
            "Republican Jim Williams as his opponent. Itemized vote totals are "
            "available via VPAP and the Virginia Department of Elections."
        ),
        "committees": [
            "Capital Region Airport Commission",
            "Central Virginia Transportation Authority",
            "Crater Planning District Commission",
            "PlanRVA",
            "Richmond Region Tourism Board",
            "Richmond Regional Transportation Planning Organization",
            "Sports Backers Board of Directors",
            "Virginia Association of Counties (VACo) Board of Directors",
        ],
        "vpap": "https://www.vpap.org/candidates/341803-mark-miller/",
        "finance": {
            "raised": "$92,114.88",
            "spent": "$49,899.57",
            "period": "2023 election cycle (cumulative)",
            "as_of": "as of the Oct. 2023 pre-election report",
            "committee": "Friends of Mark Miller (CC-22-00547)",
            "source_label": "Va. Dept. of Elections — Friends of Mark Miller, Schedule H",
            "source_url": "https://cfreports.elections.virginia.gov/Committee/Index/bc0e4c6c-5987-488c-8e72-3c8f658a3f77",
        },
        "vpap_note": (
            "Cycle totals and donors below are from the committee's official "
            "Schedule A/H filings with the Virginia Department of Elections "
            "(committee: Friends of Mark Miller, CC-22-00547). Donors are the "
            "largest itemized contributions across the 2023 reports."
        ),
        "donors": [
            ("Mike Jones", "$10,000"),
            ("Robert Jones", "$5,500"),
            ("Chesterfield Professional Firefighters", "$2,500"),
            ("Jenefer Hughes", "$2,020"),
            ("Chesterfield Small Business PAC", "$1,500"),
            ("Vernon Taylor", "$1,250"),
            ("Glen Besa", "$1,010"),
            ("Frances Broaddus-Crutchfield", "$750"),
            ("Elaine Fishman", "$750"),
            ("Robert Miller", "$700"),
        ],
        "donor_sectors": (
            "Miller's largest 2023 donors are led by individual contributors "
            "Mike Jones ($10,000) and Robert Jones, with the local firefighters' "
            "association and a small-business PAC also among the top givers."
        ),
        "sources": [
            ("Chesterfield County — Midlothian District (Miller)", CHESTERFIELD + "/1240/Midlothian-District---Miller"),
            ("VA Dept. of Elections — Friends of Mark Miller (filings)", "https://cfreports.elections.virginia.gov/Committee/Index/bc0e4c6c-5987-488c-8e72-3c8f658a3f77"),
            ("VPAP — Mark Miller", "https://www.vpap.org/candidates/341803-mark-miller/"),
        ],
    },
]

# District ordering for the official-sources VPAP block (alphabetical = the five
# magisterial districts in canonical order).
DISTRICT_ORDER = ["Bermuda", "Clover Hill", "Dale", "Matoaca", "Midlothian"]


# ---------------------------------------------------------------------------
# Coverage / dates / video helpers (carried over + lightly cleaned).
# ---------------------------------------------------------------------------

def _is_board_story(meta: dict, body: str) -> bool:
    slug, _label = _primary_focus(meta)
    if slug == "government":
        return True
    focus = meta.get("focus", "")
    if "Government" in focus:
        return True
    haystack = " ".join([
        meta.get("headline", ""), meta.get("tags", ""), body[:600],
    ])
    return bool(_GOV_KEYWORDS.search(haystack))


def _parse_key_dates(body: str) -> list[tuple[str, str]]:
    """Pull `- **<date>** — <what>` rows out of a `## Key dates` section."""
    rows = []
    in_section = False
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("## "):
            in_section = s[3:].strip().lower() == "key dates"
            continue
        if not in_section:
            continue
        if not s.startswith("- "):
            if s.startswith("#"):
                break
            continue
        item = s[2:].strip()
        m = re.match(r"\*\*(.+?)\*\*\s*[—–-]?\s*(.*)", item)
        if m:
            rows.append((m.group(1).strip(), m.group(2).strip()))
        else:
            rows.append(("", item))
    return rows


def _is_county_video(meta: dict) -> bool:
    if meta.get("media_kind", "") != "video":
        return False
    src = (meta.get("source", "") or "").lower()
    lic = (meta.get("license", "") or "").lower()
    if lic == "government":
        return True
    return any(h in src for h in _COUNTY_VIDEO_HINTS)


def _date_key(raw: str) -> tuple:
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw or "")
    if m:
        return (0, m.group(0))
    return (1, (raw or "").lower())


def _is_future(raw: str) -> bool:
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw or "")
    if not m:
        return True
    try:
        d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return True
    return d >= datetime.now(timezone.utc).date()


# ---------------------------------------------------------------------------
# Profile-card rendering.
# ---------------------------------------------------------------------------

def _party_class(party: str) -> str:
    p = (party or "").lower()
    if p.startswith("republican"):
        return "rep"
    if p.startswith("democrat"):
        return "dem"
    return "ind"


def _supervisor_card(s: dict) -> str:
    name = html.escape(s["name"])
    district = html.escape(s["district"])
    title = html.escape(s["title"])
    party = s.get("party", "")
    is_lead = s["title"] in ("Chair", "Vice-Chair")

    # Title badge (Chair / Vice-Chair) shown prominently when applicable.
    lead_badge = ""
    if is_lead:
        lead_badge = (f'<span class="sup-lead">{title} &middot; 2026</span>')
    elif s["title"] == "Interim Supervisor":
        lead_badge = '<span class="sup-lead sup-interim">Interim &middot; appointed 2025</span>'

    party_html = ""
    if party:
        party_html = (
            f'<span class="sup-party {_party_class(party)}">{html.escape(party)}</span>'
        )

    photo = ""
    if s.get("photo"):
        photo = (
            f'<img class="sup-photo" src="{html.escape(s["photo"])}" '
            f'alt="Portrait of {name}" loading="lazy" '
            f'width="120" height="150">'
        )
    else:
        photo = '<div class="sup-photo sup-photo-none" aria-hidden="true">No photo</div>'

    # Contact line.
    contact_bits = []
    if s.get("email"):
        contact_bits.append(
            f'<a href="mailto:{html.escape(s["email"])}">{html.escape(s["email"])}</a>')
    if s.get("phone"):
        contact_bits.append(
            f'<a href="tel:{html.escape(s["phone"].replace("-", ""))}">{html.escape(s["phone"])}</a>')
    if s.get("page"):
        contact_bits.append(
            f'<a href="{html.escape(s["page"])}" target="_blank" rel="noopener">'
            f'County page &nearr;</a>')
    contact_html = " &middot; ".join(contact_bits)

    # Committees.
    committees = s.get("committees") or []
    if committees:
        chips = "".join(
            f'<li>{html.escape(c)}</li>' for c in committees
        )
        committees_html = (
            '<div class="sup-block"><h4>Committees &amp; regional bodies</h4>'
            f'<ul class="sup-comm">{chips}</ul></div>'
        )
    else:
        committees_html = ""

    # Campaign finance / donors block.
    donors = s.get("donors")
    vpap = s.get("vpap", "")
    vpap_note = s.get("vpap_note", "")
    fin = s.get("finance") or {}

    # Raised / spent headline figures (with per-figure source link).
    raised_spent_html = ""
    if fin:
        raised = html.escape(str(fin.get("raised", "")))
        spent = html.escape(str(fin.get("spent", "")))
        period = html.escape(str(fin.get("period", "")))
        as_of = html.escape(str(fin.get("as_of", "")))
        src_url = fin.get("source_url", "")
        src_label = html.escape(str(fin.get("source_label", "Source")))
        committee = html.escape(str(fin.get("committee", "")))
        meta_bits = " &middot; ".join(b for b in (period, as_of) if b)
        src_html = ""
        if src_url:
            src_html = (
                f'<a class="sup-fin-src" href="{html.escape(src_url)}" '
                f'target="_blank" rel="noopener">{src_label} &nearr;</a>'
            )
        committee_html = (
            f'<div class="sup-fin-committee">{committee}</div>' if committee else ""
        )
        raised_spent_html = (
            '<div class="sup-fin-figures">'
            '<div class="sup-fin-fig"><span class="sup-fin-label">Raised</span>'
            f'<span class="sup-fin-val">{raised}</span></div>'
            '<div class="sup-fin-fig"><span class="sup-fin-label">Spent</span>'
            f'<span class="sup-fin-val">{spent}</span></div>'
            '</div>'
            + (f'<div class="sup-fin-meta">{meta_bits}</div>' if meta_bits else "")
            + committee_html
            + src_html
        )

    if donors:
        rows = "".join(
            f'<li><span class="don-name">{d}</span>'
            f'<span class="don-amt">{a}</span></li>'
            for (d, a) in donors
        )
        sectors = s.get("donor_sectors", "")
        sectors_html = f'<p class="sup-sectors">{sectors}</p>' if sectors else ""
        donor_inner = (
            f'<p class="sup-fin-note">{vpap_note}</p>'
            '<div class="sup-don-head">Top donors</div>'
            f'<ul class="sup-donors">{rows}</ul>'
            f'{sectors_html}'
        )
    else:
        donor_inner = f'<p class="sup-fin-note">{vpap_note}</p>'

    vpap_link = ""
    if vpap:
        vpap_link = (
            f'<a class="sup-vpap-link" href="{html.escape(vpap)}" '
            f'target="_blank" rel="noopener">View full donor record on VPAP &nearr;</a>'
        )
    finance_html = (
        '<div class="sup-block sup-finance">'
        '<h4>Campaign finance '
        '<span class="sup-fin-tag">public record</span></h4>'
        f'{raised_spent_html}'
        f'{donor_inner}{vpap_link}</div>'
    )

    # Sources line.
    srcs = s.get("sources") or []
    src_links = " &middot; ".join(
        f'<a href="{html.escape(u)}" target="_blank" rel="noopener">{html.escape(t)}</a>'
        for (t, u) in srcs
    )
    sources_html = (
        f'<div class="sup-sources"><span class="sup-src-label">Sources:</span> '
        f'{src_links}</div>'
    )

    lead_class = " is-lead" if is_lead else ""

    return (
        f'<article class="sup-card{lead_class}" id="sup-{slugify(s["name"])}">'
        '<header class="sup-head">'
        f'{photo}'
        '<div class="sup-id">'
        f'<span class="sup-district">{district} District</span>'
        f'<h3 class="sup-name">{name}</h3>'
        f'<div class="sup-badges">{party_html}{lead_badge}</div>'
        f'<div class="sup-contact">{contact_html}</div>'
        '</div></header>'
        f'<div class="sup-block"><h4>Background</h4><p>{s["bio"]}</p></div>'
        f'<div class="sup-block"><h4>Tenure</h4><p>{s["tenure"]}</p></div>'
        f'<div class="sup-block"><h4>Election history</h4><p>{s["election"]}</p></div>'
        f'{committees_html}'
        f'{finance_html}'
        f'{sources_html}'
        '</article>'
    )


def _build_profiles_section() -> str:
    cards = "".join(_supervisor_card(s) for s in SUPERVISORS)
    return (
        '<section class="bos-sec" id="profiles" aria-label="Supervisor profiles">'
        '<h2 class="bos-h">The five supervisors</h2>'
        '<p class="bos-note">One card per magisterial district. Bios, tenure and '
        'committee roles are from each member\'s official county page and '
        'Ballotpedia; campaign-donor figures are public record via the Virginia '
        'Public Access Project (VPAP). Figures are current as of June 8, 2026; '
        'always confirm against the linked sources.</p>'
        f'<div class="sup-grid">{cards}</div></section>'
    )


def _build_official_block() -> str:
    links = "".join(
        f'<a class="bos-link" href="{url}" target="_blank" rel="noopener">'
        f'<span class="bos-link-t">{html.escape(title)} &nearr;</span>'
        f'<span class="bos-link-d">{html.escape(desc)}</span></a>'
        for title, url, desc in OFFICIAL_LINKS
    )
    # District VPAP profile links.
    by_district = {s["district"]: s for s in SUPERVISORS}
    vpap_rows = "".join(
        f'<a class="bos-vpap" href="{html.escape(by_district[d]["vpap"])}" '
        f'target="_blank" rel="noopener">'
        f'<span class="bos-vpap-d">{html.escape(d)}</span>'
        f'<span class="bos-vpap-n">{html.escape(by_district[d]["name"])} &nearr;</span></a>'
        for d in DISTRICT_ORDER if d in by_district
    )
    return (
        '<section class="bos-official" aria-label="Official county sources">'
        '<h2 class="bos-h">Official sources</h2>'
        f'<div class="bos-link-grid">{links}</div>'
        '<h3 class="bos-subh">Campaign finance by district (VPAP)</h3>'
        '<p class="bos-note">The Virginia Public Access Project tracks every '
        'Chesterfield supervisor\'s donors and spending. These are public records.</p>'
        f'<div class="bos-vpap-grid">{vpap_rows}</div>'
        '</section>'
    )


def build_board():
    """Render the Board of Supervisors tracker -> public/board.html."""
    PUBLIC.mkdir(parents=True, exist_ok=True)
    recs = _published_records()

    stories, dates, videos = [], [], []
    for meta, body, name in recs:
        if not _is_board_story(meta, body):
            continue
        headline = meta.get("headline", "") or name
        url = story_url(headline)
        for raw, what in _parse_key_dates(body):
            dates.append({
                "raw": raw,
                "pretty": _pretty_date(raw) if re.match(r"\d{4}-\d{2}-\d{2}", raw or "") else (raw or ""),
                "what": what,
                "anchor": url,
                "headline": meta.get("headline", ""),
            })
        if _is_county_video(meta):
            videos.append((meta, body, name))
        stories.append((meta, body, name, url))

    # --- Profiles (the centerpiece) ---------------------------------------
    profiles_html = _build_profiles_section()

    # --- Official sources + VPAP block ------------------------------------
    official = _build_official_block()

    # --- Upcoming meetings & dates ----------------------------------------
    upcoming = [d for d in dates if _is_future(d["raw"])]
    upcoming.sort(key=lambda d: _date_key(d["raw"]))
    if upcoming:
        rows = "".join(
            f'<li class="bos-date">'
            f'<span class="bos-date-when">{html.escape(d["pretty"]) or "TBD"}</span>'
            f'<span class="bos-date-what">{html.escape(d["what"])}'
            + (f' <a class="bos-date-src" href="{d["anchor"]}">{html.escape(d["headline"])}</a>'
               if d["headline"] else "")
            + '</span></li>'
            for d in upcoming
        )
        dates_html = (
            '<section class="bos-sec" aria-label="Upcoming meetings and dates">'
            '<h2 class="bos-h">Upcoming meetings &amp; dates</h2>'
            '<p class="bos-note">Pulled from key dates in our coverage &mdash; always '
            'confirm against the official agenda before attending.</p>'
            f'<ul class="bos-dates">{rows}</ul></section>'
        )
    else:
        dates_html = (
            '<section class="bos-sec"><h2 class="bos-h">Upcoming meetings &amp; dates</h2>'
            '<p class="bos-note">No upcoming dates flagged in current coverage. Check the '
            '<a href="https://chesterfield.legistar.com/" target="_blank" rel="noopener">'
            'Agenda Center</a> for the official schedule.</p></section>'
        )

    # --- Watch the meetings (county videos) -------------------------------
    if videos:
        cards = []
        for meta, body, name in videos:
            hero = media_html(meta, big=True)
            src = html.escape(meta.get("source", ""))
            date_iso = (meta.get("published", "") or "")[:10]
            head = html.escape(meta.get("headline", ""))
            url = (meta.get("video_url") or meta.get("source_url") or "").strip()
            cards.append(
                '<article class="bos-vid">'
                f'{hero}'
                f'<div class="bos-vid-meta">{src} &middot; {_pretty_date(date_iso)}</div>'
                f'<a class="bos-vid-h" href="{html.escape(url)}" target="_blank" rel="noopener">{head}</a>'
                '</article>'
            )
        watch_html = (
            '<section class="bos-sec" aria-label="Watch the meetings">'
            '<h2 class="bos-h">Watch the meetings</h2>'
            '<p class="bos-note">County video from Chesterfield\'s official channels.</p>'
            f'<div class="bos-vid-grid">{"".join(cards)}</div></section>'
        )
    else:
        watch_html = ""

    # --- Recent coverage list ---------------------------------------------
    if stories:
        cards = []
        for meta, body, name, url in stories:
            slug, label = _primary_focus(meta)
            color = render._focus_color(slug)
            src = html.escape(meta.get("source", ""))
            date_iso = (meta.get("published", "") or "")[:10]
            head = html.escape(meta.get("headline", ""))
            tldr = html.escape(render._tldr_from_body(body))
            cards.append(
                '<article class="bos-story" style="--accent:' + color + '">'
                f'<span class="bos-chip" style="background:{color}1f;color:{color};'
                f'border:1px solid {color}55">{html.escape(label)}</span>'
                f'<a class="bos-story-h" href="{html.escape(url)}">{head}</a>'
                f'<div class="bos-story-meta">{src} &middot; {_pretty_date(date_iso)}</div>'
                + (f'<p class="bos-story-tldr">{tldr}</p>' if tldr else "")
                + '</article>'
            )
        stories_html = (
            '<section class="bos-sec" aria-label="Recent Board and government coverage">'
            '<h2 class="bos-h">Recent coverage</h2>'
            '<p class="bos-note">Our published Board of Supervisors &amp; government '
            'stories. Each links into the homepage story.</p>'
            f'<div class="bos-story-grid">{"".join(cards)}</div></section>'
        )
    else:
        stories_html = (
            '<section class="bos-sec"><h2 class="bos-h">Recent coverage</h2>'
            '<p class="bos-note">No Board of Supervisors coverage published yet.</p></section>'
        )

    intro = (
        '<h1 class="page-title">Board of Supervisors Tracker</h1>'
        '<p class="lead">Chesterfield County is governed by a five-member Board of '
        'Supervisors &mdash; one elected from each magisterial district (Bermuda, '
        'Clover Hill, Dale, Matoaca and Midlothian). The Board sets the county '
        'budget, enacts ordinances, decides rezonings, and appoints the county '
        'administrator. The current four-year term began Jan. 1, 2024 after the '
        'November 2023 election. This page profiles all five members &mdash; their '
        'backgrounds, tenure, election history, committee roles and public '
        'campaign-finance records &mdash; and tracks our coverage, upcoming meetings '
        'and the county\'s own meeting video.</p>'
        '<p class="bos-disclaimer">The Dale District seat is currently held by an '
        'interim appointee following the October 2025 death of Supervisor Jim '
        'Holland; a special election is scheduled for November 2026.</p>'
    )

    body_html = (
        intro + profiles_html + official + dates_html + watch_html + stories_html
        + "<style>" + _BOARD_CSS + "</style>"
    )
    out = PUBLIC / "board.html"
    out.write_text(render._shell(body_html, len(stories)), encoding="utf-8")
    return out


_BOARD_CSS = """
  .bos-sec { margin:0 0 2.4rem; }
  .bos-h { font-family:var(--serif); font-size:1.35rem; color:var(--ink);
    margin:0 0 .9rem; padding-bottom:.3rem; border-bottom:2px solid var(--neon);
    display:inline-block; text-shadow:0 0 18px rgba(39,230,198,.2); }
  .bos-subh { font-family:var(--serif); font-size:1.05rem; color:var(--ink);
    margin:1.6rem 0 .5rem; }
  .bos-note { color:var(--muted); font-size:.92rem; margin:0 0 1rem; max-width:48rem;
    line-height:1.55; }
  .bos-disclaimer { color:var(--gold); font-family:var(--mono); font-size:.82rem;
    line-height:1.5; max-width:48rem; margin:.4rem 0 0;
    border-left:3px solid var(--gold); padding-left:.85rem; opacity:.92; }

  /* --- Supervisor profile cards --- */
  .sup-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(330px,1fr));
    gap:1.4rem; }
  .sup-card { background:var(--surface); border:1px solid var(--line);
    border-radius:14px; padding:1.3rem 1.35rem 1.1rem;
    box-shadow:0 0 24px rgba(39,230,198,.05);
    display:flex; flex-direction:column; }
  .sup-card.is-lead { border-color:rgba(39,230,198,.5);
    box-shadow:0 0 28px rgba(39,230,198,.18); }
  .sup-head { display:flex; gap:1rem; align-items:flex-start; margin-bottom:1rem; }
  .sup-photo { flex:0 0 auto; width:96px; height:120px; object-fit:cover;
    border-radius:10px; border:1px solid var(--line);
    box-shadow:0 0 16px rgba(0,0,0,.4); background:var(--bg2); }
  .sup-photo-none { display:flex; align-items:center; justify-content:center;
    font-family:var(--mono); font-size:.6rem; color:var(--muted);
    text-transform:uppercase; letter-spacing:.05em; }
  .sup-id { flex:1 1 auto; min-width:0; }
  .sup-district { display:block; font-family:var(--mono); font-size:.68rem;
    font-weight:700; text-transform:uppercase; letter-spacing:.08em;
    color:var(--neon2); text-shadow:0 0 10px rgba(140,240,106,.35); }
  .sup-name { font-family:var(--serif); font-weight:800; font-size:1.18rem;
    line-height:1.18; color:var(--ink); margin:.18rem 0 .4rem; }
  .sup-badges { display:flex; flex-wrap:wrap; gap:.35rem; margin-bottom:.5rem; }
  .sup-party { font-family:var(--mono); font-size:.62rem; font-weight:700;
    text-transform:uppercase; letter-spacing:.05em; padding:.16rem .5rem;
    border-radius:5px; }
  .sup-party.rep { background:rgba(255,93,114,.14); color:#ff8a98;
    border:1px solid rgba(255,93,114,.45); }
  .sup-party.dem { background:rgba(39,230,198,.14); color:var(--neon);
    border:1px solid rgba(39,230,198,.45); }
  .sup-party.ind { background:rgba(143,180,175,.16); color:var(--muted);
    border:1px solid rgba(143,180,175,.4); }
  .sup-lead { font-family:var(--mono); font-size:.62rem; font-weight:700;
    text-transform:uppercase; letter-spacing:.05em; padding:.16rem .5rem;
    border-radius:5px; background:rgba(255,201,74,.16); color:var(--gold);
    border:1px solid rgba(255,201,74,.5); }
  .sup-lead.sup-interim { background:rgba(140,240,106,.14); color:var(--neon2);
    border-color:rgba(140,240,106,.45); }
  .sup-contact { font-size:.78rem; color:var(--muted); line-height:1.5;
    word-break:break-word; }
  .sup-contact a { color:var(--neon); }

  .sup-block { margin:0 0 .85rem; }
  .sup-block h4 { font-family:var(--mono); font-size:.68rem; font-weight:700;
    text-transform:uppercase; letter-spacing:.07em; color:var(--neon);
    margin:0 0 .35rem; }
  .sup-block p { font-size:.88rem; color:var(--ink); line-height:1.55; margin:0;
    opacity:.94; }
  .sup-comm { list-style:none; margin:.1rem 0 0; padding:0; display:flex;
    flex-wrap:wrap; gap:.3rem; }
  .sup-comm li { font-family:var(--mono); font-size:.66rem; color:var(--muted);
    background:var(--bg2); border:1px solid var(--line); border-radius:5px;
    padding:.18rem .45rem; line-height:1.3; }

  /* Finance / donors block */
  .sup-finance { margin-top:.4rem; padding:.9rem 1rem; background:var(--bg2);
    border:1px solid var(--line); border-left:3px solid var(--gold);
    border-radius:10px; }
  .sup-finance h4 { color:var(--gold); display:flex; flex-wrap:wrap;
    align-items:center; gap:.45rem; }
  .sup-fin-tag { font-size:.56rem; font-weight:700; letter-spacing:.04em;
    background:rgba(255,201,74,.14); color:var(--gold);
    border:1px solid rgba(255,201,74,.4); border-radius:4px; padding:.1rem .35rem;
    text-transform:uppercase; }
  .sup-fin-note { font-size:.8rem; color:var(--muted); line-height:1.5;
    margin:0 0 .55rem; }
  .sup-fin-figures { display:flex; gap:.6rem; margin:0 0 .45rem; }
  .sup-fin-fig { flex:1 1 0; display:flex; flex-direction:column;
    background:var(--surface); border:1px solid var(--line);
    border-radius:8px; padding:.5rem .65rem; }
  .sup-fin-label { font-family:var(--mono); font-size:.58rem; font-weight:700;
    text-transform:uppercase; letter-spacing:.07em; color:var(--muted); }
  .sup-fin-val { font-family:var(--mono); font-size:1.02rem; font-weight:700;
    color:var(--gold); margin-top:.12rem; text-shadow:0 0 10px rgba(255,201,74,.25); }
  .sup-fin-meta { font-size:.72rem; color:var(--muted); line-height:1.4;
    margin:0 0 .3rem; }
  .sup-fin-committee { font-family:var(--mono); font-size:.66rem; color:var(--muted);
    margin:0 0 .35rem; opacity:.9; }
  .sup-fin-src { display:block; font-family:var(--mono); font-size:.66rem;
    font-weight:700; color:var(--neon); margin:0 0 .6rem; word-break:break-word; }
  .sup-fin-src:hover { text-decoration:underline; }
  .sup-don-head { font-family:var(--mono); font-size:.62rem; font-weight:700;
    text-transform:uppercase; letter-spacing:.06em; color:var(--gold);
    margin:.25rem 0 .25rem; }
  .sup-donors { list-style:none; margin:0 0 .55rem; padding:0; }
  .sup-donors li { display:flex; justify-content:space-between; gap:.6rem;
    padding:.28rem 0; border-bottom:1px dashed rgba(143,180,175,.18);
    font-size:.82rem; }
  .sup-donors li:last-child { border-bottom:0; }
  .don-name { color:var(--ink); }
  .don-amt { font-family:var(--mono); font-weight:700; color:var(--gold);
    white-space:nowrap; }
  .sup-sectors { font-size:.78rem; color:var(--muted); line-height:1.5; margin:0; }
  .sup-vpap-link { display:inline-block; margin-top:.5rem; font-family:var(--mono);
    font-size:.7rem; font-weight:700; color:var(--gold); }
  .sup-vpap-link:hover { text-decoration:underline; }

  .sup-sources { margin-top:.7rem; padding-top:.65rem;
    border-top:1px solid var(--line); font-size:.72rem; color:var(--muted);
    line-height:1.6; }
  .sup-src-label { font-family:var(--mono); font-weight:700; text-transform:uppercase;
    letter-spacing:.05em; color:var(--muted); }
  .sup-sources a { color:var(--neon); }

  /* Official sources */
  .bos-official { margin:0 0 2.4rem; }
  .bos-link-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
    gap:.9rem; }
  .bos-link { display:block; background:var(--surface); border:1px solid var(--line);
    border-left:3px solid var(--neon); border-radius:12px; padding:1rem 1.15rem;
    text-decoration:none; box-shadow:0 0 22px rgba(39,230,198,.05);
    transition:border-color .15s ease, box-shadow .15s ease; }
  .bos-link:hover { border-color:var(--neon); text-decoration:none;
    box-shadow:0 0 24px rgba(39,230,198,.3); }
  .bos-link-t { display:block; font-family:var(--serif); font-weight:700;
    font-size:1.08rem; color:var(--ink); margin-bottom:.25rem; }
  .bos-link:hover .bos-link-t { color:var(--neon); }
  .bos-link-d { display:block; font-size:.85rem; color:var(--muted); line-height:1.4; }

  .bos-vpap-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
    gap:.7rem; }
  .bos-vpap { display:block; background:var(--surface); border:1px solid var(--line);
    border-left:3px solid var(--gold); border-radius:10px; padding:.7rem .85rem;
    text-decoration:none; transition:border-color .15s ease; }
  .bos-vpap:hover { border-color:var(--gold); text-decoration:none; }
  .bos-vpap-d { display:block; font-family:var(--mono); font-size:.62rem;
    font-weight:700; text-transform:uppercase; letter-spacing:.06em;
    color:var(--gold); }
  .bos-vpap-n { display:block; font-size:.82rem; color:var(--ink); margin-top:.15rem; }
  .bos-vpap:hover .bos-vpap-n { color:var(--neon); }

  /* Upcoming dates */
  .bos-dates { list-style:none; margin:0; padding:0;
    border:1px solid var(--line); border-radius:12px; overflow:hidden;
    background:var(--surface); }
  .bos-date { display:flex; gap:1rem; padding:.85rem 1.1rem;
    border-bottom:1px solid var(--line); align-items:baseline; flex-wrap:wrap; }
  .bos-date:last-child { border-bottom:0; }
  .bos-date-when { flex:0 0 auto; min-width:8.5rem; font-family:var(--mono);
    font-size:.78rem; font-weight:700; color:var(--gold);
    text-shadow:0 0 8px rgba(255,201,74,.35); }
  .bos-date-what { flex:1 1 14rem; font-size:.96rem; color:var(--ink); }
  .bos-date-src { display:block; font-family:var(--mono); font-size:.72rem;
    color:var(--neon); margin-top:.2rem; }

  /* Watch the meetings */
  .bos-vid-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr));
    gap:1.1rem; }
  .bos-vid { background:var(--surface); border:1px solid var(--line);
    border-radius:12px; overflow:hidden; box-shadow:0 0 22px rgba(39,230,198,.05); }
  .bos-vid:hover { border-color:rgba(39,230,198,.4); }
  .bos-vid .media { margin:0 0 .7rem; }
  .bos-vid .media.hero img { aspect-ratio:16/9; }
  .bos-vid-meta { font-family:var(--mono); font-size:.7rem; text-transform:uppercase;
    letter-spacing:.05em; color:var(--muted); padding:0 .95rem; }
  .bos-vid-h { display:block; font-family:var(--serif); font-weight:600; font-size:1rem;
    color:var(--ink); text-decoration:none; padding:.25rem .95rem 1rem; line-height:1.25; }
  .bos-vid-h:hover { color:var(--neon); }

  /* Coverage stories */
  .bos-story-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr));
    gap:1.1rem; }
  .bos-story { background:var(--surface); border:1px solid var(--line);
    border-left:3px solid var(--accent,#27e6c6); border-radius:12px;
    padding:1.1rem 1.2rem; }
  .bos-story:hover { border-color:rgba(39,230,198,.4); }
  .bos-chip { display:inline-block; font-family:var(--mono); font-size:.64rem;
    font-weight:700; text-transform:uppercase; letter-spacing:.06em;
    padding:.18rem .5rem; border-radius:5px; margin-bottom:.55rem; }
  .bos-story-h { display:block; font-family:var(--serif); font-weight:700;
    font-size:1.08rem; line-height:1.22; color:var(--ink); text-decoration:none;
    margin-bottom:.4rem; }
  .bos-story-h:hover { color:var(--neon); }
  .bos-story-meta { font-family:var(--mono); font-size:.7rem; text-transform:uppercase;
    letter-spacing:.05em; color:var(--muted); margin-bottom:.45rem; }
  .bos-story-tldr { font-size:.9rem; color:var(--muted); margin:0; line-height:1.5; }
"""
