"""Elected Offices pages: Chesterfield County's five constitutional officers.

Builds a hub at public/elected-offices.html plus one page per constitutional
office (Clerk of the Circuit Court, Commissioner of the Revenue, Commonwealth's
Attorney, Sheriff, Treasurer). Each office page covers who holds it, a short
bio, what the office does in plain language, the services residents use it for,
contact details, and the term length / next election. The hub also points to
the existing Board of Supervisors and School Board pages.

All facts trace to official county sources (chesterfield.gov) linked at the
foot of each page. Pure CSS/HTML, no JavaScript. Stdlib only; reuses
render._shell() / _inject_og.
"""
from __future__ import annotations

import html
from pathlib import Path

from . import render
from .render import PUBLIC

# ---------------------------------------------------------------------------
# Data. One dict per constitutional office. Facts come straight from
# research/elected-offices.md and research/elected-officials-bios.md.
# Party affiliation is deliberately omitted for all five offices: the county
# does not publish it and the research could not confirm it. Barr's law degree
# is phrased generically ("law degree") because the exact title was uncertain.
# ---------------------------------------------------------------------------

SHARED_SOURCES = [
    {"label": "Elected Offices overview (chesterfield.gov)",
     "url": "https://www.chesterfield.gov/1259/Elected-Offices"},
    {"label": "2023 constitutional officers sworn in (terms)",
     "url": "https://www.chesterfield.gov/m/newsflash/home/detail/4253"},
]

OFFICES = [
    {
        "slug": "clerk-of-circuit-court",
        "office": "Clerk of the Circuit Court",
        "holder": "Amanda L. Pohl",
        "lead": "The administrative arm of the Circuit Court: keeper of the "
                "county's permanent court and land records, and the office that "
                "records deeds, probates wills, and issues marriage licenses.",
        "bio": "Amanda L. Pohl was elected Clerk of the Circuit Court in 2023 "
               "and took office in January 2024, beginning an eight-year term "
               "that runs through 2031. Before her election she worked as a "
               "social work educator who built and taught graduate-level "
               "courses, ran a consulting practice supporting businesses, "
               "nonprofits, and candidates, and served as Executive Director of "
               "Deliver My Vote, an organization focused on expanding ballot "
               "access. She holds three graduate degrees: a Master of Social "
               "Work, a Master of Divinity, and a Master of Science in patient "
               "counseling. She is a lifetime member of the Chesterfield NAACP "
               "and previously served on its executive board. In office she has "
               "described her priorities as modernizing court services, "
               "improving public access, and increasing transparency.",
        "does": "The Clerk's office is the administrative arm of the Circuit "
                "Court and carries out more than 800 statutory duties spanning "
                "judicial, non-judicial, and fiscal functions. It maintains the "
                "county's permanent court and land records, processes civil and "
                "criminal case filings, and serves as the official record-keeper "
                "for deeds, wills, and other public documents. The office also "
                "issues marriage licenses and concealed handgun permits.",
        "services": [
            "Recording deeds and land documents",
            "Marriage licenses (and courthouse wedding ceremonies)",
            "Concealed handgun permits",
            "Probate and estate administration (wills, qualifying executors)",
            "Civil and criminal court case records and copies",
            "Notary commissions",
            "Jury services coordination",
        ],
        "contact": {
            "address": "9500 Courthouse Road, Chesterfield, VA 23832",
            "mailing": "P.O. Box 125, Chesterfield, VA 23832-0909",
            "phone": "804-748-1241",
            "email": "circuitcourtclerk@chesterfield.gov",
            "website": "https://www.chesterfield.gov/1127/Circuit-Court",
            "hours": "Monday–Friday, 8 a.m.–4 p.m. (recording until "
                     "3:30 p.m.); closed holidays",
        },
        "term": "Elected countywide to an eight-year term, longer than the "
                "other constitutional offices. Amanda Pohl was elected in "
                "November 2023 and took office January 1, 2024; her term runs "
                "through the end of 2031.",
        "next_election": "November 2031",
        "sources": [
            {"label": "Clerk of the Circuit Court (chesterfield.gov)",
             "url": "https://www.chesterfield.gov/1127/Circuit-Court"},
            *SHARED_SOURCES,
        ],
    },
    {
        "slug": "commissioner-of-revenue",
        "office": "Commissioner of the Revenue",
        "holder": "Jenefer S. Hughes",
        "lead": "The county's chief assessing officer: the office that values "
                "personal property, handles business licenses, runs tax relief "
                "programs, and helps residents file their state income taxes.",
        "bio": "Jenefer S. Hughes has served as Chesterfield County's "
               "Commissioner of the Revenue since 2017, when she was first "
               "elected. She is a Chartered Accountant with roughly three "
               "decades of corporate finance experience at major companies "
               "including Ernst & Young, Hewlett-Packard, and McKesson, where "
               "she was Director of Accounting overseeing a team that processed "
               "billions of dollars in transactions annually. Born in England, "
               "Hughes worked in Europe before relocating to the United States "
               "in 1997 and becoming a U.S. citizen in 2008; she moved to the "
               "Bon Air area of Chesterfield in 2009. Her credentials are "
               "listed as MBA, ACA, and MCR.",
        "does": "The Commissioner of the Revenue is the county's chief "
                "assessing officer, responsible for fairly applying state and "
                "local tax codes to determine what taxpayers owe. The office "
                "administers local taxes (business and personal property), "
                "assists residents with state income tax filing, and oversees "
                "tax relief and exemption programs. It is required to protect "
                "taxpayer confidentiality.",
        "services": [
            "Business license applications and renewals",
            "Personal property tax assessment (vehicles, boats, mobile homes)",
            "Real estate tax relief and exemptions for qualified residents "
            "(elderly, disabled, and others)",
            "State income tax return filing assistance",
            "DMV Select services (by appointment)",
            "Tax appeals and relief applications",
        ],
        "contact": {
            "address": "9901 Lori Road, Building 38, Room 165, Chesterfield, "
                       "VA 23832",
            "mailing": "P.O. Box 124, Chesterfield, VA 23832",
            "phone": "804-748-1281",
            "email": "cor@chesterfield.gov",
            "website": "https://www.chesterfield.gov/310/"
                       "Commissioner-of-the-Revenue",
            "hours": "Monday–Friday, 8:30 a.m.–5 p.m.",
        },
        "term": "Elected countywide to a four-year term. Re-elected November "
                "2023, with the current term beginning January 1, 2024 and "
                "running through the end of 2027.",
        "next_election": "November 2027",
        "sources": [
            {"label": "Commissioner of the Revenue (chesterfield.gov)",
             "url": "https://www.chesterfield.gov/310/"
                    "Commissioner-of-the-Revenue"},
            *SHARED_SOURCES,
        ],
    },
    {
        "slug": "commonwealths-attorney",
        "office": "Commonwealth's Attorney",
        "holder": "Erin B. Barr",
        "lead": "The county's chief local prosecutor: the office that "
                "prosecutes felonies and serious misdemeanors, advises law "
                "enforcement around the clock, and runs victim and witness "
                "support programs.",
        "bio": "Erin B. (Bumgarner) Barr was elected Commonwealth's Attorney "
               "in November 2023 and took office in January 2024, becoming the "
               "first person in over 30 years to win the office in Chesterfield "
               "without a political party affiliation. She grew up in Amherst "
               "County, Virginia, the daughter of a state trooper and a "
               "critical care nurse. She earned a bachelor's degree in "
               "political science and sociology, magna cum laude, from "
               "Randolph-Macon College in 2006 and a law degree, magna cum "
               "laude, from the University of Richmond in 2009. After law "
               "school she clerked in Norfolk Circuit Court, then joined the "
               "Chesterfield Commonwealth's Attorney's Office in 2010, where "
               "she spent roughly a decade as an Assistant and later Deputy "
               "Commonwealth's Attorney. In 2020 she became a Senior Assistant "
               "Commonwealth's Attorney in Colonial Heights, focusing on "
               "domestic violence, sexual assault, and child abuse cases, and "
               "she also served briefly as Interim Commonwealth's Attorney for "
               "Dinwiddie County in 2022. She has publicly emphasized that "
               "prosecution should be guided by the law and the facts rather "
               "than political ideology.",
        "does": "The Commonwealth's Attorney is the county's chief local "
                "prosecutor, responsible for prosecuting all felonies and "
                "certain misdemeanors that occur in Chesterfield County. The "
                "office provides 24-hour legal advice to law enforcement and "
                "magistrates, runs victim and witness support programs, and "
                "participates in community crime-prevention and regional "
                "drug-task-force efforts.",
        "services": [
            "Prosecution of criminal cases",
            "Victim/Witness Assistance Program (including domestic violence "
            "and sexual assault support)",
            "Pretrial Services Program for non-violent offenders",
            "Bond hearing coordination",
            "Answering citizen questions about criminal law and the court "
            "process",
        ],
        "contact": {
            "address": "9500 Courthouse Road, Chesterfield, VA 23832",
            "phone": "804-748-1221 (Adult Criminal Division)",
            "email": "comatty1@chesterfield.gov",
            "website": "https://www.chesterfield.gov/1135/"
                       "Commonwealths-Attorney",
            "hours": "Monday–Friday, 8 a.m.–4 p.m.",
        },
        "term": "Elected countywide to a four-year term. Erin Barr was elected "
                "November 2023, with the term beginning January 1, 2024 and "
                "running through the end of 2027.",
        "next_election": "November 2027",
        "sources": [
            {"label": "Commonwealth's Attorney (chesterfield.gov)",
             "url": "https://www.chesterfield.gov/1135/Commonwealths-Attorney"},
            *SHARED_SOURCES,
        ],
    },
    {
        "slug": "sheriff",
        "office": "Sheriff",
        "holder": "Karl S. Leonard",
        "lead": "The office responsible for court security, the county jail, "
                "and service of legal documents. In Chesterfield, the separate "
                "County Police Department handles patrol and most criminal "
                "investigations.",
        "bio": "Karl S. Leonard has served as Sheriff of Chesterfield County "
               "since 2014. A native of New York City, he spent more than 30 "
               "years with the Chesterfield County Police Department, retiring "
               "at the rank of Major, and also served in the Chesterfield and "
               "Richmond sheriff's offices. In parallel he had a long military "
               "career in the U.S. Coast Guard, enlisting in 1985 and retiring "
               "as a Captain in 2015; from 2010 he returned to active duty for "
               "about three years at the Pentagon, working with returning "
               "service members on their transition to civilian life before "
               "coming back to Chesterfield to run for Sheriff in 2014. As "
               "Sheriff he leads roughly 300 sworn and civilian personnel and "
               "oversees the county jail and court security for a population of "
               "more than 320,000. He is known for jail-based rehabilitation "
               "and reentry programming aimed at reducing recidivism.",
        "does": "The Sheriff's Office is responsible for court security, "
                "operation of the county jail, service of legal documents "
                "(civil process), and care of offenders in custody. In "
                "Chesterfield, the separate Chesterfield County Police "
                "Department handles patrol and most criminal investigations, "
                "so the Sheriff's role centers on the courts, the jail, and "
                "process service rather than general policing.",
        "services": [
            "Court security and operations",
            "County jail management",
            "Service of legal and civil documents (subpoenas, summonses, "
            "evictions)",
            "Community outreach, volunteer programs, and youth summer camps",
        ],
        "contact": {
            "address": "9500 Courthouse Road, Chesterfield, VA 23832",
            "phone": "804-748-1261 (emergencies: 911)",
            "email": "ccso@chesterfield.gov",
            "website": "https://www.chesterfield.gov/765/Sheriff",
            "hours": "Monday–Friday, 8 a.m.–5 p.m.",
        },
        "note": "Scam note from the office: the Sheriff's Office will never "
                "call to demand money over missed jury duty, court actions, or "
                "warrants.",
        "term": "Elected countywide to a four-year term. Karl Leonard was "
                "re-elected November 2023, with the term beginning January 1, "
                "2024 and running through the end of 2027.",
        "next_election": "November 2027",
        "sources": [
            {"label": "Sheriff's Office (chesterfield.gov)",
             "url": "https://www.chesterfield.gov/765/Sheriff"},
            *SHARED_SOURCES,
        ],
    },
    {
        "slug": "treasurer",
        "office": "Treasurer",
        "holder": "Rebecca R. Longnaker, CPA",
        "lead": "The county's banker and chief investment officer: the office "
                "that bills and collects personal property and real estate "
                "taxes and safeguards, invests, and disburses county funds.",
        "bio": "Rebecca R. Longnaker was elected Treasurer of Chesterfield "
               "County in 2020. She is a Certified Public Accountant who "
               "graduated summa cum laude from the University of Baltimore in "
               "1990 and passed the CPA exam that same year; her county "
               "directory listing also notes a Master Governmental Treasurer "
               "(MGT) credential. Early in her career she worked as an external "
               "auditor at KPMG Peat Marwick and as an internal auditor at "
               "McCormick & Company before moving to Chesterfield in 1995. She "
               "joined Chesterfield County government in 2013 in the Central "
               "Accounting department, was named the county's Accounting "
               "Employee of the Year after her first year, and in 2017 moved to "
               "the Treasurer's Office as Deputy Treasurer, managing its "
               "accounting section and the county's investment portfolio. As "
               "Treasurer she has launched an online payment portal, installed "
               "payment kiosks across the county, and brought processing of "
               "mailed-in payments back in-house to county employees.",
        "does": "The Treasurer handles the billing and collection of personal "
                "property and real estate taxes and serves as the county's "
                "banker and chief investment officer. The office receives, "
                "safeguards, invests, and disburses county funds, and "
                "administers unclaimed property and the county's bonded debt.",
        "services": [
            "Paying personal property and real estate tax bills (online portal "
            "available 24/7)",
            "Tax billing questions and payment plans",
            "Other county fee and payment collection",
        ],
        "contact": {
            "address": "9901 Lori Road, Chesterfield, VA 23832",
            "mailing": "P.O. Box 70, Chesterfield, VA 23832",
            "phone": "804-748-1201 (fax 804-751-4993)",
            "email": "Treasurer@chesterfield.gov",
            "website": "https://www.chesterfield.gov/727/Treasurer",
            "portal": "https://chesterfield.virginiainteractive.org",
            "hours": "Monday–Friday, 8:30 a.m.–5 p.m.",
        },
        "term": "Elected countywide to a four-year term. Rebecca Longnaker was "
                "re-elected November 2023, with the term beginning January 1, "
                "2024 and running through the end of 2027.",
        "next_election": "November 2027",
        "sources": [
            {"label": "Treasurer (chesterfield.gov)",
             "url": "https://www.chesterfield.gov/727/Treasurer"},
            *SHARED_SOURCES,
        ],
    },
]


# ---------------------------------------------------------------------------
# CSS. Same design-token variables as safety.py (var(--accent),
# var(--text-secondary), var(--surface-card), var(--border),
# var(--font-display), etc.).
# ---------------------------------------------------------------------------

_CSS = """<style>
.eo-wrap{max-width:820px;margin:0 auto;}
.eo-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:64ch;margin:.4rem 0 1rem;}
.eo-meta{font:var(--fw-medium) var(--fs-2xs)/1.4 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);margin-bottom:1.6rem;}
.eo-sec{margin:2.4rem 0;}
.eo-sec h2{font:var(--fw-bold) var(--fs-xl)/1.15 var(--font-display);margin:0 0 .3rem;}
.eo-sec__dek{font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);margin:0 0 1.2rem;max-width:64ch;}
.eo-sec p{font:var(--fs-md)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:64ch;margin:0 0 1rem;}
.eo-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin:1.4rem 0 2.2rem;}
.eo-card{display:block;border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:var(--radius-sm);background:var(--surface-card);padding:1.1rem 1.25rem;text-decoration:none;color:inherit;transition:border-color .15s ease;}
.eo-card:hover{border-color:var(--accent);}
.eo-card__office{font:var(--fw-bold) var(--fs-md)/1.2 var(--font-display);color:var(--text-primary);}
.eo-card__holder{font:var(--fw-semibold) var(--fs-sm) var(--font-sans);color:var(--accent);margin:.25rem 0 .4rem;}
.eo-card__lead{font:var(--fs-2xs)/1.5 var(--font-sans);color:var(--text-secondary);margin:0;}
.eo-holder{border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:var(--radius-sm);background:var(--surface-card);padding:1.1rem 1.25rem;margin:0 0 1rem;}
.eo-holder__role{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--accent);}
.eo-holder__name{font:var(--fw-bold) var(--fs-2xl)/1.15 var(--font-display);color:var(--text-primary);margin:.25rem 0 .1rem;}
.eo-bio{font:var(--fs-md)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:64ch;margin:0;}
.eo-services{list-style:none;padding:0;margin:0;display:grid;gap:.55rem;}
.eo-services li{position:relative;padding-left:1.4rem;font:var(--fs-sm)/1.5 var(--font-sans);color:var(--text-secondary);max-width:64ch;}
.eo-services li::before{content:"";position:absolute;left:0;top:.5rem;width:7px;height:7px;border-radius:2px;background:var(--accent);}
.eo-contact{border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface-card);padding:.4rem 1.1rem;margin:0;}
.eo-row{display:flex;gap:1rem;padding:.7rem 0;border-bottom:1px solid var(--border);}
.eo-row:last-child{border-bottom:none;}
.eo-row__k{flex:0 0 6.5rem;font:var(--fw-bold) var(--fs-3xs)/1.4 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);padding-top:.1rem;}
.eo-row__v{font:var(--fs-sm)/1.5 var(--font-sans);color:var(--text-secondary);}
.eo-row__v a{color:var(--accent);font-weight:600;word-break:break-word;}
.eo-term{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:.4rem 0 0;}
.eo-term__cell{border:1px solid var(--border);border-radius:var(--radius-xs);padding:.9rem 1rem;background:var(--surface-card);}
.eo-term__k{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);}
.eo-term__v{font:var(--fs-sm)/1.5 var(--font-sans);color:var(--text-secondary);margin-top:.4rem;}
.eo-term__v strong{color:var(--text-primary);}
.eo-flag{font:var(--fs-2xs)/1.55 var(--font-sans);color:var(--text-tertiary);margin:1rem 0 0;max-width:64ch;}
.eo-callout{border:1px solid var(--border);border-left:3px solid var(--accent);border-radius:var(--radius-xs);background:var(--surface-card);padding:.9rem 1.1rem;margin:1.2rem 0 0;font:var(--fs-sm)/1.55 var(--font-sans);color:var(--text-secondary);max-width:64ch;}
.eo-source{margin:2.4rem 0 0;padding:1rem 1.1rem;border-left:3px solid var(--accent);background:var(--surface-card);border-radius:var(--radius-xs);font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);}
.eo-source a{color:var(--accent);font-weight:600;}
.eo-xlinks{margin:1.6rem 0 0;font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);}
.eo-xlinks a{color:var(--accent);font-weight:600;}
.eo-back{display:inline-block;margin:0 0 1.2rem;font:var(--fw-semibold) var(--fs-2xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--accent);text-decoration:none;}
@media(max-width:620px){
  .eo-grid{grid-template-columns:1fr;}
  .eo-term{grid-template-columns:1fr;}
  .eo-row{flex-direction:column;gap:.2rem;}
  .eo-row__k{flex-basis:auto;}
}
</style>"""


def _sources(srcs: list) -> str:
    links = " &middot; ".join(
        f'<a href="{html.escape(s["url"])}" target="_blank" rel="noopener">'
        f'{html.escape(s["label"])}</a>'
        for s in srcs
    )
    return (
        '<div class="eo-source">The facts on this page come from official '
        f'sources: {links}. Office hours and phone numbers occasionally change; '
        'check the links to verify or for the most current details.</div>'
    )


def _contact_row(key: str, value_html: str) -> str:
    return (
        '<div class="eo-row">'
        f'<div class="eo-row__k">{html.escape(key)}</div>'
        f'<div class="eo-row__v">{value_html}</div>'
        '</div>'
    )


def _contact_block(c: dict) -> str:
    rows = []
    if c.get("address"):
        rows.append(_contact_row("Address", html.escape(c["address"])))
    if c.get("mailing"):
        rows.append(_contact_row("Mailing", html.escape(c["mailing"])))
    if c.get("phone"):
        rows.append(_contact_row("Phone", html.escape(c["phone"])))
    if c.get("email"):
        em = html.escape(c["email"])
        rows.append(_contact_row(
            "Email", f'<a href="mailto:{em}">{em}</a>'))
    if c.get("website"):
        url = html.escape(c["website"])
        rows.append(_contact_row(
            "Website",
            f'<a href="{url}" target="_blank" rel="noopener">{url}</a>'))
    if c.get("portal"):
        url = html.escape(c["portal"])
        rows.append(_contact_row(
            "Pay online",
            f'<a href="{url}" target="_blank" rel="noopener">{url}</a>'))
    if c.get("hours"):
        rows.append(_contact_row("Hours", html.escape(c["hours"])))
    return '<div class="eo-contact">' + "".join(rows) + '</div>'


def _office_page(o: dict) -> str:
    services = "".join(
        f'<li>{html.escape(s)}</li>' for s in o["services"]
    )
    note_html = (
        f'<div class="eo-callout">{html.escape(o["note"])}</div>'
        if o.get("note") else ""
    )
    body = (
        _CSS
        + '<div class="eo-wrap">'
        + '<a class="eo-back" href="/elected-offices.html">'
          '&larr; All elected offices</a>'
        + f'<h1 class="page-title">{html.escape(o["office"])}</h1>'
        + '<div class="eo-meta">Chesterfield County constitutional office</div>'
        + f'<p class="eo-lead">{html.escape(o["lead"])}</p>'
        + '<div class="eo-sec"><h2>Who holds it</h2>'
        + '<div class="eo-holder">'
        + f'<div class="eo-holder__role">{html.escape(o["office"])}</div>'
        + f'<div class="eo-holder__name">{html.escape(o["holder"])}</div>'
        + '</div>'
        + f'<p class="eo-bio">{html.escape(o["bio"])}</p>'
        + '</div>'
        + '<div class="eo-sec"><h2>What this office does</h2>'
        + f'<p>{html.escape(o["does"])}</p>'
        + '</div>'
        + '<div class="eo-sec"><h2>Services residents use it for</h2>'
        + f'<ul class="eo-services">{services}</ul>'
        + '</div>'
        + '<div class="eo-sec"><h2>Contact</h2>'
        + _contact_block(o["contact"])
        + note_html
        + '</div>'
        + '<div class="eo-sec"><h2>Term and next election</h2>'
        + '<div class="eo-term">'
        + '<div class="eo-term__cell">'
          '<div class="eo-term__k">Term</div>'
        + f'<div class="eo-term__v">{html.escape(o["term"])}</div></div>'
        + '<div class="eo-term__cell">'
          '<div class="eo-term__k">Next on the ballot</div>'
        + '<div class="eo-term__v"><strong>'
        + html.escape(o["next_election"]) + '</strong></div></div>'
        + '</div>'
        + '<p class="eo-flag">Virginia constitutional offices appear on the '
          'ballot as partisan races, but the county does not publish current '
          'officeholders’ party affiliations on its official pages, so we '
          'do not list one here.</p>'
        + '</div>'
        + _sources(o["sources"])
        + '<div class="eo-xlinks">Related: '
          '<a href="/elected-offices.html">All elected offices</a> '
          '&middot; <a href="/board.html">Board of Supervisors</a> '
          '&middot; <a href="/school-board.html">School Board</a></div>'
        + '</div>'
    )
    return body


def _hub() -> str:
    cards = "".join(
        f'<a class="eo-card" href="/{html.escape(o["slug"])}.html">'
        f'<div class="eo-card__office">{html.escape(o["office"])}</div>'
        f'<div class="eo-card__holder">{html.escape(o["holder"])}</div>'
        f'<p class="eo-card__lead">{html.escape(o["lead"])}</p>'
        '</a>'
        for o in OFFICES
    )
    body = (
        _CSS
        + '<div class="eo-wrap">'
        + '<h1 class="page-title">Elected Offices</h1>'
        + '<div class="eo-meta">Who runs Chesterfield County</div>'
        + '<p class="eo-lead">Beyond the Board of Supervisors, Chesterfield '
          'voters elect five constitutional officers countywide. These are '
          'independent offices established under the Virginia Constitution, '
          'each run by an official answerable directly to voters rather than to '
          'the county administration. They handle the everyday business of '
          'records, taxes, courts, and public safety.</p>'
        + '<div class="eo-sec"><h2>The five constitutional officers</h2>'
        + '<p class="eo-sec__dek">Each office below has its own page with the '
          'current officeholder, what the office does, the services residents '
          'use it for, contact details, and when the seat is next on the '
          'ballot.</p>'
        + f'<div class="eo-grid">{cards}</div>'
        + '</div>'
        + '<div class="eo-sec"><h2>Elected boards</h2>'
        + '<p>Two other elected bodies set policy for the county. The '
          '<a href="/board.html">Board of Supervisors</a> is five members, one '
          'from each magisterial district, who set the budget, tax rates, and '
          'land-use decisions. The <a href="/school-board.html">School '
          'Board</a> is five members, also one per district, who govern '
          'Chesterfield County Public Schools; those seats are nonpartisan '
          'under Virginia law.</p>'
        + '</div>'
        + '<div class="eo-source">Officeholders, responsibilities, terms, and '
          'contact details on these pages come from the county’s '
          '<a href="https://www.chesterfield.gov/1259/Elected-Offices" '
          'target="_blank" rel="noopener">Elected Offices</a> pages and each '
          'office’s own page on chesterfield.gov. Details occasionally '
          'change; check the links to verify.</div>'
        + '<div class="eo-xlinks">Related: '
          '<a href="/board.html">Board of Supervisors</a> '
          '&middot; <a href="/school-board.html">School Board</a> '
          '&middot; <a href="/taxes.html">Where your taxes go</a></div>'
        + '</div>'
    )
    return body


def build_elected() -> Path:
    """Build the Elected Offices hub and one page per constitutional office.

    Returns the Path to the hub page (/elected-offices.html)."""
    # Per-office pages.
    for o in OFFICES:
        body = _office_page(o)
        page = render._shell(body)
        title = f"{o['office']}: {o['holder']} — Chesterfield County"
        desc = (
            f"What the Chesterfield County {o['office']} does, who holds it, "
            "the services residents use it for, contact details, and when the "
            "seat is next on the ballot."
        )
        url = f"{render.SITE_URL}/{o['slug']}.html"
        page = render._inject_og(page, title, desc, url, og_type="website")
        (PUBLIC / f"{o['slug']}.html").write_text(page, encoding="utf-8")

    # Hub.
    body = _hub()
    page = render._shell(body)
    page = render._inject_og(
        page,
        "Elected Offices: Chesterfield County's constitutional officers",
        "Chesterfield voters elect five constitutional officers countywide — "
        "Clerk of the Circuit Court, Commissioner of the Revenue, Commonwealth's "
        "Attorney, Sheriff, and Treasurer. Who they are and what each office does.",
        f"{render.SITE_URL}/elected-offices.html", og_type="website")
    out = PUBLIC / "elected-offices.html"
    out.write_text(page, encoding="utf-8")
    return out
