"""Community Resources hub: a practical guide to local help for Chesterfield
families, written for the county's Spanish-speaking residents.

Builds public/community-resources.html. The site auto-translates this page to
Spanish at /es/community-resources.html, and Spanish speakers are the primary
audience, so accuracy matters more than completeness: only details the research
(research/community-resources.md) marked verified/confirmed are published.

Anything the research flagged as unverified is omitted or softened:
- CCPS has no single county-wide registration desk number, so we say "register
  at your child's home school" and link the CCPS page rather than print a number.
- The El Salvador / Guatemala / Honduras consulate street numbers were flagged
  for confirmation, so we publish the verified phone + city/state and the
  appointments/website link, and omit the exact street address.
- 211 Virginia's Spanish availability was not confirmed, so it is not stated.
- Virginia Hispanic Foundation legal clinics are event-based, so we point to the
  calendar rather than imply a standing phone line.

Plain language throughout so it translates cleanly to Spanish. Every entry's
text is escaped with html.escape. Pure CSS/HTML, no JavaScript. Stdlib only;
reuses render._shell() / _inject_og.
"""
from __future__ import annotations

import html
from pathlib import Path

from . import render
from .render import PUBLIC

# ---------------------------------------------------------------------------
# Data. Sections of entries. Every contact detail below is drawn from the
# "Verified 2026-06" / confirmed items in research/community-resources.md.
# Unverified specifics are intentionally omitted (see module docstring).
#
# Each entry: name, what (one practical line), optional phone, optional
# website (url + label), optional note (a safe extra line), and area tag:
#   "chesterfield"  -> in Chesterfield
#   "richmond"      -> Richmond-metro (serves Chesterfield-area residents)
#   "statewide"     -> statewide / covers Chesterfield
#   "regional"      -> wider region (DC / MD / VA), nearest service
# ---------------------------------------------------------------------------

AREA_LABELS = {
    "chesterfield": "Chesterfield",
    "richmond": "Richmond area",
    "statewide": "Statewide",
    "regional": "Regional",
}

SECTIONS = [
    {
        "id": "schools",
        "title": "Schools and children",
        "dek": "Enrolling a child, classes for English learners, interpreters, "
               "and school meals.",
        "entries": [
            {
                "name": "Chesterfield County Public Schools — enrolling your child",
                "what": "How to enroll a child in school. Registration starts "
                        "online, and you complete it at your child's home "
                        "school. Bring proof of Chesterfield residency, the "
                        "child's certified birth certificate, immunization "
                        "records, and a recent physical. There is no single "
                        "county registration number — register at your child's "
                        "home school, or call the main line and ask to be "
                        "routed to it.",
                "phone": "804-748-1405",
                "url": "https://www.oneccps.org/page/register-for-school",
                "url_label": "How to register (oneccps.org)",
                "area": "chesterfield",
            },
            {
                "name": "CCPS English as a Second Language (ESL)",
                "what": "Free support for students who are learning English. At "
                        "enrollment every family fills out a Home Language "
                        "Survey; if another language is spoken at home, the "
                        "child is screened and placed in ESL support, with "
                        "parent outreach.",
                "url": "https://www.oneccps.org/page/english-as-a-second-language",
                "url_label": "ESL program (oneccps.org)",
                "area": "chesterfield",
            },
            {
                "name": "CCPS interpreters and translation",
                "what": "Free interpreters and document translation for families "
                        "at CCPS schools. Ask the school's front office or the "
                        "ESL teacher to arrange an interpreter for meetings and "
                        "documents.",
                "url": "https://www.oneccps.org/page/english-as-a-second-language",
                "url_label": "Language support (oneccps.org)",
                "area": "chesterfield",
            },
            {
                "name": "CCPS school meals (free and reduced-price)",
                "what": "Free or reduced-price breakfast and lunch for eligible "
                        "families. For the 2025-26 school year CCPS is providing "
                        "breakfast and lunch at no charge to all enrolled "
                        "students, so most families do not need to apply. "
                        "Confirm the current year with your child's school.",
                "phone": "804-743-3717",
                "url": "https://mychesterfieldschools.com/food-and-nutrition-services/",
                "url_label": "Food & Nutrition Services",
                "area": "chesterfield",
            },
        ],
    },
    {
        "id": "county",
        "title": "County and government services",
        "dek": "Help with benefits, courts, and getting connected to county "
               "resources in Spanish.",
        "entries": [
            {
                "name": "Chesterfield-Colonial Heights Social Services",
                "what": "Help with basic needs: Medicaid and medical assistance, "
                        "SNAP (food stamps), TANF, child care assistance, energy "
                        "and fuel assistance, the Refugee Assistance Program, and "
                        "general relief.",
                "phone": "804-748-1100",
                "url": "https://www.chesterfield.gov/569/Social-Services",
                "url_label": "Social Services (chesterfield.gov)",
                "note": "Open Monday to Friday, 8:30 a.m. to 5 p.m.",
                "area": "chesterfield",
            },
            {
                "name": "CommonHelp (Virginia) — apply for benefits online",
                "what": "One website to apply for and renew Medicaid, SNAP, "
                        "TANF, child care, and energy assistance in Virginia. "
                        "Phone help is available in Spanish.",
                "phone": "1-855-635-4370",
                "url": "https://commonhelp.virginia.gov",
                "url_label": "commonhelp.virginia.gov",
                "area": "statewide",
            },
            {
                "name": "Chesterfield courts — interpreters",
                "what": "Free language interpretation for court business. The "
                        "court has a full-time Spanish interpreter on staff. "
                        "Request an interpreter through the Clerk's Office.",
                "phone": "804-748-1241",
                "url": "https://www.chesterfield.gov/1127/Circuit-Court",
                "url_label": "Circuit Court (chesterfield.gov)",
                "area": "chesterfield",
            },
            {
                "name": "Chesterfield County website in Spanish",
                "what": "The county website can be machine-translated into "
                        "Spanish and 100+ other languages using the site's "
                        "built-in translation tool.",
                "url": "https://www.chesterfield.gov",
                "url_label": "chesterfield.gov",
                "area": "chesterfield",
            },
            {
                "name": "Virginia DMV",
                "what": "Driver's licenses, ID cards, and vehicle registration "
                        "are handled by the state DMV. Spanish information is "
                        "available on the DMV website and customer line.",
                "phone": "804-497-7100",
                "url": "https://www.dmv.virginia.gov",
                "url_label": "dmv.virginia.gov",
                "note": "There is no single Spanish phone line for county "
                        "utilities or taxes; the Office of Multicultural "
                        "Engagement (804-796-7100) can help route Spanish "
                        "speakers to the right office.",
                "area": "statewide",
            },
        ],
    },
    {
        "id": "legal",
        "title": "Legal and immigration help",
        "dek": "Organizations that help residents directly with legal questions "
               "and the immigration system.",
        "entries": [
            {
                "name": "Sacred Heart Center — Immigration Legal Services",
                "what": "Low-cost immigration legal help for low-income "
                        "immigrants in central Virginia. As a DOJ-accredited "
                        "representative, it helps families with asylum, "
                        "temporary status, and navigating the immigration "
                        "system. Bilingual (Spanish and English).",
                "phone": "804-230-4399",
                "url": "https://shcrichmond.org/community-hub/",
                "url_label": "Sacred Heart Center",
                "area": "richmond",
            },
            {
                "name": "Commonwealth Catholic Charities — Immigration & Refugee Services",
                "what": "Affordable immigration legal services and refugee "
                        "resettlement, including case management, employment "
                        "help, ESL, and housing. Services available in Spanish.",
                "phone": "804-648-4177",
                "url": "https://www.cccofva.org/immigrationhelp",
                "url_label": "cccofva.org/immigrationhelp",
                "area": "richmond",
            },
            {
                "name": "Legal Aid Justice Center — Richmond",
                "what": "Free civil legal help for low-income families, "
                        "low-wage immigrant workers, and at-risk children, "
                        "including immigration consultations. Serves Chesterfield "
                        "County, with Spanish-speaking staff.",
                "phone": "804-643-1086",
                "url": "https://www.justice4all.org/what-we-do/immigration/",
                "url_label": "justice4all.org",
                "note": "Statewide legal aid intake: 1-866-534-5243.",
                "area": "richmond",
            },
            {
                "name": "Amica Center for Immigrant Rights",
                "what": "Free legal help for immigrants held in detention in "
                        "Virginia and Maryland, plus unaccompanied immigrant "
                        "children. Offers Know Your Rights presentations and "
                        "consultations. (Formerly the CAIR Coalition.)",
                "phone": "202-331-3329",
                "url": "https://amicacenter.org",
                "url_label": "amicacenter.org",
                "note": "Detention line: 202-331-3329. Family and friends of "
                        "people in detention: 202-331-3320.",
                "area": "regional",
            },
            {
                "name": "Virginia Hispanic Foundation — free legal clinics",
                "what": "Periodic free legal clinics for the Hispanic community. "
                        "These are scheduled events, not a standing phone line — "
                        "check the website for upcoming clinic dates.",
                "url": "https://www.vahf.org/legal-clinics",
                "url_label": "vahf.org/legal-clinics",
                "area": "richmond",
            },
        ],
    },
    {
        "id": "esl",
        "title": "English classes and adult education",
        "dek": "Free and low-cost English classes (ESL) and adult learning, "
               "including GED in Spanish.",
        "entries": [
            {
                "name": "Sacred Heart Center — ESL and GED in Spanish",
                "what": "Four levels of free ESL classes, with child care for "
                        "young children during class. The only Richmond location "
                        "offering GED preparation classes in Spanish (the GED "
                        "exam can be taken in Spanish).",
                "phone": "804-230-4399",
                "url": "https://shcrichmond.org/community-hub/",
                "url_label": "Sacred Heart Center",
                "area": "richmond",
            },
            {
                "name": "CCPS Adult & Continuing Education — English for adults",
                "what": "Classes for adults to improve English reading, writing, "
                        "listening, and speaking, plus computer skills. Offered "
                        "in person, online with a teacher, or self-paced.",
                "phone": "804-768-6140",
                "url": "https://www.oneccps.org/page/adult-continuing-education",
                "url_label": "Adult & Continuing Education",
                "area": "chesterfield",
            },
            {
                "name": "Brightpoint Community College — ESL",
                "what": "ESL coursework that prepares students for college-level "
                        "reading and writing in English. Campuses in Chester and "
                        "Midlothian, plus online.",
                "phone": "804-796-4000",
                "url": "https://www.brightpoint.edu/academics/beginning-coursework/esl/",
                "url_label": "brightpoint.edu",
                "note": "ESL is in the Department of English: Chester campus "
                        "804-706-5086, Midlothian campus 804-594-1509.",
                "area": "chesterfield",
            },
            {
                "name": "Chesterfield County Public Library — online learning",
                "what": "Free online learning tools, including language learning "
                        "and citizenship preparation, plus in-branch programs. "
                        "Staff can point you to local ESL and conversation "
                        "resources.",
                "url": "https://library.chesterfield.gov/416/Online-Learning",
                "url_label": "library.chesterfield.gov",
                "area": "chesterfield",
            },
        ],
    },
    {
        "id": "health",
        "title": "Health and clinics",
        "dek": "Low-cost and free care for people who are uninsured, and help "
               "applying for health coverage.",
        "entries": [
            {
                "name": "CrossOver Healthcare Ministry",
                "what": "Sliding-scale and free care for people who are "
                        "uninsured and for Medicaid patients: primary care, "
                        "pediatrics, dental, vision, pharmacy, mental health, "
                        "and women's health. Serves Spanish-speaking patients "
                        "with interpretation.",
                "phone": "804-655-2794",
                "url": "https://www.crossoverministry.org",
                "url_label": "crossoverministry.org",
                "area": "richmond",
            },
            {
                "name": "Daily Planet Health Services",
                "what": "Full health care (medical, dental, behavioral health) "
                        "for anyone, regardless of housing, income, citizenship, "
                        "or insurance status. Language assistance is provided.",
                "phone": "804-783-2505",
                "url": "https://dailyplanetva.org",
                "url_label": "dailyplanetva.org",
                "area": "richmond",
            },
            {
                "name": "Chesterfield Health District — free and low-cost clinics",
                "what": "The local health district keeps a list of free and "
                        "sliding-scale clinics serving Chesterfield-area "
                        "residents. A good place to start for low-cost care.",
                "url": "https://www.vdh.virginia.gov/chesterfield/community-needs/free-or-sliding-scale-clinics/",
                "url_label": "Clinic list (vdh.virginia.gov)",
                "area": "chesterfield",
            },
            {
                "name": "Cover Virginia — health coverage and Medicaid",
                "what": "Phone help to apply for Medicaid and FAMIS health "
                        "coverage in Virginia. Spanish-language assistance is "
                        "available.",
                "phone": "1-855-242-8282",
                "url": "https://www.coverva.org",
                "url_label": "coverva.org",
                "area": "statewide",
            },
        ],
    },
    {
        "id": "food",
        "title": "Food and emergency assistance",
        "dek": "Food pantries and help with utility and energy bills.",
        "entries": [
            {
                "name": "Chesterfield Food Bank Outreach Center",
                "what": "The largest food pantry in Chesterfield County. "
                        "Emergency food and resource services Monday to "
                        "Thursday, 10 a.m. to 2 p.m., plus regular "
                        "distributions. Main office: 12211 Iron Bridge Road, "
                        "Chester.",
                "phone": "804-414-8885",
                "url": "https://www.cfboc.org/getfood",
                "url_label": "cfboc.org/getfood",
                "note": "For one-time emergency food help, ask for extension "
                        "103 (Client Services).",
                "area": "chesterfield",
            },
            {
                "name": "Feed More — food pantry help line",
                "what": "A network of partner pantries across Central Virginia, "
                        "including Chesterfield. The help line connects you to "
                        "the nearest food pantry or meal program.",
                "phone": "804-237-8617",
                "url": "https://feedmore.org/store-locator/",
                "url_label": "Find a pantry (feedmore.org)",
                "note": "Help line open Monday to Friday, 9 a.m. to 4 p.m.",
                "area": "richmond",
            },
            {
                "name": "Chesterfield-Colonial Heights Social Services — energy and utility help",
                "what": "Help toward heating and cooling bills (Fuel, Cooling, "
                        "and Crisis programs), EnergyShare bill-payment help, "
                        "and referrals for rent and housing assistance. The "
                        "Fuel Assistance window usually opens the second Tuesday "
                        "in October.",
                "phone": "804-748-1100",
                "url": "https://www.chesterfield.gov/666/Financial-and-Basic-Needs-Assistance",
                "url_label": "Financial & Basic Needs Assistance",
                "area": "chesterfield",
            },
        ],
    },
    {
        "id": "voting",
        "title": "Voting",
        "dek": "How to register and vote. The Virginia registration application "
               "is available in Spanish.",
        "entries": [
            {
                "name": "Virginia Department of Elections",
                "what": "Register to vote, check your registration, find your "
                        "polling place, and request a mail ballot. The voter "
                        "registration application is available in Spanish.",
                "phone": "1-800-552-9745",
                "url": "https://www.elections.virginia.gov/registration/how-to-register/",
                "url_label": "How to register (elections.virginia.gov)",
                "area": "statewide",
            },
            {
                "name": "Chesterfield County General Registrar",
                "what": "The local elections office for Chesterfield. Register, "
                        "update your address, vote early, and ask local ballot "
                        "questions. Office at 9848 Lori Road, Chesterfield.",
                "phone": "804-748-1471",
                "url": "https://www.chesterfield.gov/registrar",
                "url_label": "chesterfield.gov/registrar",
                "area": "chesterfield",
            },
            {
                "name": "The Chesterfield Report — 2026 Voter Guide",
                "what": "Our own guide to how and when to vote in Chesterfield "
                        "in 2026, who is on the ballot, and how to register.",
                "url": "/elections.html",
                "url_label": "Our 2026 Voter Guide",
                "area": "chesterfield",
            },
        ],
    },
    {
        "id": "consulates",
        "title": "Consulates",
        "dek": "Nearest consulates serving Virginia residents. Call ahead and "
               "book an appointment before you travel.",
        "entries": [
            {
                "name": "Consular Section of the Embassy of Mexico — Washington, D.C.",
                "what": "Consular services for Mexican nationals in Virginia: "
                        "passports, the matrícula consular ID, birth "
                        "registration, powers of attorney, and protection "
                        "services. This office's jurisdiction covers Virginia.",
                "phone": "202-736-1000",
                "url": "https://consulmex.sre.gob.mx/washington",
                "url_label": "consulmex.sre.gob.mx/washington",
                "note": "Appointments: 1-424-309-0009 or citas.sre.gob.mx. "
                        "Mexico also holds mobile consulates in the Richmond "
                        "area; the county's Office of Multicultural Engagement "
                        "(804-796-7100) and Sacred Heart Center help publicize "
                        "them.",
                "area": "regional",
            },
            {
                "name": "Consulate General of El Salvador — Woodbridge, Virginia",
                "what": "Consular services for Salvadoran nationals: passports, "
                        "the DUI national ID, travel documents, and document "
                        "authentication. This is a full consulate inside "
                        "Virginia (Woodbridge), and it holds mobile visits to "
                        "other Virginia cities.",
                "phone": "703-490-4300",
                "url": "https://portalcitas.rree.gob.sv",
                "url_label": "Appointments (portalcitas.rree.gob.sv)",
                "note": "Call ahead to confirm the office address before you "
                        "travel.",
                "area": "regional",
            },
            {
                "name": "Consulate General of Guatemala — Rockville, Maryland",
                "what": "Consular services for Guatemalan nationals in Virginia: "
                        "passports, consular ID, and document services.",
                "phone": "240-485-5050",
                "note": "Emergencies: 240-535-3950. Call ahead to confirm the "
                        "office address before you travel.",
                "area": "regional",
            },
            {
                "name": "Consulate of Honduras — Washington, D.C.",
                "what": "Consular services for Honduran nationals in Virginia: "
                        "passports, consular ID, and document authentication.",
                "phone": "202-966-4596",
                "note": "Also reachable at 202-966-7702. Call ahead to confirm "
                        "the office address before you travel.",
                "area": "regional",
            },
        ],
    },
    {
        "id": "orgs",
        "title": "Latino-serving organizations",
        "dek": "Community organizations that bring many of these services "
               "together in one place.",
        "entries": [
            {
                "name": "Sacred Heart Center",
                "what": "The hub of Richmond's Latino community: free and "
                        "low-cost ESL and GED in Spanish, immigration legal "
                        "services, free bilingual tax preparation (February to "
                        "April), family case management, early childhood "
                        "education, support groups, and notary services.",
                "phone": "804-230-4399",
                "url": "https://shcrichmond.org",
                "url_label": "shcrichmond.org",
                "area": "richmond",
            },
            {
                "name": "Virginia Hispanic Chamber of Commerce and Foundation",
                "what": "Business counseling and workforce development for "
                        "Latino entrepreneurs (offered in Spanish), plus the "
                        "Passport to Education program that helps Latino "
                        "students and families navigate schools and college.",
                "phone": "804-378-4099",
                "url": "https://www.vahcc.com",
                "url_label": "vahcc.com",
                "note": "Office at 10700 Midlothian Turnpike, Suite 200, "
                        "Richmond.",
                "area": "richmond",
            },
            {
                "name": "Commonwealth Catholic Charities",
                "what": "Refugee resettlement, housing navigation, and case "
                        "management with Spanish-language support, alongside "
                        "its immigration legal services.",
                "phone": "804-648-4177",
                "url": "https://www.cccofva.org",
                "url_label": "cccofva.org",
                "area": "richmond",
            },
        ],
    },
]

SOURCES = [
    {"label": "Office of Multicultural Engagement (chesterfield.gov)",
     "url": "https://www.chesterfield.gov/1165/Multicultural-Engagement"},
    {"label": "Chesterfield County Public Schools (oneccps.org)",
     "url": "https://www.oneccps.org/page/register-for-school"},
    {"label": "Chesterfield-Colonial Heights Social Services",
     "url": "https://www.chesterfield.gov/569/Social-Services"},
    {"label": "Sacred Heart Center",
     "url": "https://shcrichmond.org"},
    {"label": "Feed More",
     "url": "https://feedmore.org"},
    {"label": "Virginia Department of Elections",
     "url": "https://www.elections.virginia.gov"},
]


# ---------------------------------------------------------------------------
# CSS. Same design-token variables used by elected.py / safety.py
# (var(--accent), var(--text-secondary), var(--surface-card), var(--border),
# var(--font-display), etc.). No JavaScript.
# ---------------------------------------------------------------------------

_CSS = """<style>
.cr-wrap{max-width:820px;margin:0 auto;}
.cr-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:64ch;margin:.4rem 0 1rem;}
.cr-meta{font:var(--fw-medium) var(--fs-2xs)/1.4 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);margin-bottom:1.6rem;}
.cr-anchor{border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:var(--radius-sm);background:var(--surface-card);padding:1.1rem 1.25rem;margin:0 0 2rem;}
.cr-anchor__role{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--accent);}
.cr-anchor__name{font:var(--fw-bold) var(--fs-xl)/1.15 var(--font-display);color:var(--text-primary);margin:.3rem 0 .35rem;}
.cr-anchor p{font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);max-width:64ch;margin:0 0 .6rem;}
.cr-anchor__rows{display:grid;gap:.35rem;}
.cr-anchor__row{font:var(--fs-sm)/1.5 var(--font-sans);color:var(--text-secondary);}
.cr-anchor__row a{color:var(--accent);font-weight:600;word-break:break-word;}
.cr-anchor__k{font:var(--fw-bold) var(--fs-3xs) var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);margin-right:.5rem;}
.cr-toc{display:flex;flex-wrap:wrap;gap:.5rem;margin:0 0 2.2rem;}
.cr-toc a{font:var(--fw-semibold) var(--fs-2xs)/1 var(--font-sans);color:var(--text-secondary);text-decoration:none;border:1px solid var(--border);border-radius:999px;padding:.5rem .85rem;background:var(--surface-card);}
.cr-toc a:hover{border-color:var(--accent);color:var(--accent);}
.cr-sec{margin:2.6rem 0;scroll-margin-top:1.5rem;}
.cr-sec h2{font:var(--fw-bold) var(--fs-xl)/1.15 var(--font-display);margin:0 0 .3rem;}
.cr-sec__dek{font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);margin:0 0 1.2rem;max-width:64ch;}
.cr-list{display:grid;gap:14px;}
.cr-card{border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface-card);padding:1.05rem 1.2rem;}
.cr-card__head{display:flex;justify-content:space-between;align-items:baseline;gap:.75rem;flex-wrap:wrap;}
.cr-card__name{font:var(--fw-bold) var(--fs-md)/1.25 var(--font-display);color:var(--text-primary);}
.cr-tag{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);border:1px solid var(--border);border-radius:999px;padding:.3rem .55rem;white-space:nowrap;}
.cr-tag--chesterfield{color:var(--accent);border-color:var(--accent);}
.cr-card__what{font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);max-width:64ch;margin:.5rem 0 .65rem;}
.cr-card__meta{display:grid;gap:.3rem;}
.cr-card__row{font:var(--fs-sm)/1.5 var(--font-sans);color:var(--text-secondary);}
.cr-card__row a{color:var(--accent);font-weight:600;word-break:break-word;}
.cr-card__k{font:var(--fw-bold) var(--fs-3xs) var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);margin-right:.5rem;}
.cr-card__note{font:var(--fs-2xs)/1.55 var(--font-sans);color:var(--text-tertiary);margin:.55rem 0 0;max-width:64ch;}
.cr-fix{border:1px solid var(--border);border-left:3px solid var(--accent);border-radius:var(--radius-xs);background:var(--surface-card);padding:.95rem 1.1rem;margin:2.6rem 0 0;font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);max-width:64ch;}
.cr-fix a{color:var(--accent);font-weight:600;}
.cr-source{margin:1.6rem 0 0;padding:1rem 1.1rem;border-left:3px solid var(--accent);background:var(--surface-card);border-radius:var(--radius-xs);font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);}
.cr-source a{color:var(--accent);font-weight:600;}
.cr-xlinks{margin:1.6rem 0 0;font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);}
.cr-xlinks a{color:var(--accent);font-weight:600;}
@media(max-width:620px){
  .cr-card__head{flex-direction:column;gap:.25rem;}
}
</style>"""


def _link(url: str, label: str) -> str:
    safe_url = html.escape(url)
    # External links open in a new tab; internal site links do not.
    if url.startswith("/"):
        return f'<a href="{safe_url}">{html.escape(label)}</a>'
    return (
        f'<a href="{safe_url}" target="_blank" rel="noopener">'
        f'{html.escape(label)}</a>'
    )


def _entry_card(e: dict) -> str:
    area = e.get("area", "")
    tag_cls = "cr-tag cr-tag--chesterfield" if area == "chesterfield" else "cr-tag"
    tag_label = AREA_LABELS.get(area, "")
    tag_html = (
        f'<span class="{tag_cls}">{html.escape(tag_label)}</span>'
        if tag_label else ""
    )

    rows = []
    if e.get("phone"):
        ph = e["phone"]
        digits = ph.replace("-", "").replace(" ", "")
        rows.append(
            '<div class="cr-card__row"><span class="cr-card__k">Phone</span>'
            f'<a href="tel:{html.escape(digits)}">{html.escape(ph)}</a></div>'
        )
    if e.get("url"):
        rows.append(
            '<div class="cr-card__row"><span class="cr-card__k">Online</span>'
            f'{_link(e["url"], e.get("url_label", e["url"]))}</div>'
        )
    rows_html = (
        f'<div class="cr-card__meta">{"".join(rows)}</div>' if rows else ""
    )
    note_html = (
        f'<div class="cr-card__note">{html.escape(e["note"])}</div>'
        if e.get("note") else ""
    )

    return (
        '<div class="cr-card">'
        '<div class="cr-card__head">'
        f'<span class="cr-card__name">{html.escape(e["name"])}</span>'
        f'{tag_html}'
        '</div>'
        f'<p class="cr-card__what">{html.escape(e["what"])}</p>'
        f'{rows_html}'
        f'{note_html}'
        '</div>'
    )


def _section(sec: dict) -> str:
    cards = "".join(_entry_card(e) for e in sec["entries"])
    return (
        f'<div class="cr-sec" id="{html.escape(sec["id"])}">'
        f'<h2>{html.escape(sec["title"])}</h2>'
        f'<p class="cr-sec__dek">{html.escape(sec["dek"])}</p>'
        f'<div class="cr-list">{cards}</div>'
        '</div>'
    )


def _anchor() -> str:
    """The trustworthy anchor near the top: the county's bilingual coordinator."""
    return (
        '<div class="cr-anchor">'
        '<div class="cr-anchor__role">Start here</div>'
        '<div class="cr-anchor__name">Office of Multicultural Engagement</div>'
        '<p>Not sure where to begin? Chesterfield County has a bilingual '
        'coordinator, Dalila Medrano, who can help connect Spanish speakers '
        'to county services, job and health fairs, mobile consulates, and '
        'immigration events.</p>'
        '<div class="cr-anchor__rows">'
        '<div class="cr-anchor__row"><span class="cr-anchor__k">Office</span>'
        '<a href="tel:8047967100">804-796-7100</a></div>'
        '<div class="cr-anchor__row"><span class="cr-anchor__k">Coordinator</span>'
        'Dalila Medrano &middot; <a href="tel:8047967085">804-796-7085</a></div>'
        '<div class="cr-anchor__row"><span class="cr-anchor__k">Online</span>'
        '<a href="https://www.chesterfield.gov/1165/Multicultural-Engagement" '
        'target="_blank" rel="noopener">Multicultural Engagement '
        '(chesterfield.gov)</a></div>'
        '</div>'
        '</div>'
    )


def _toc() -> str:
    links = "".join(
        f'<a href="#{html.escape(s["id"])}">{html.escape(s["title"])}</a>'
        for s in SECTIONS
    )
    return f'<nav class="cr-toc" aria-label="Sections">{links}</nav>'


def _sources_block() -> str:
    links = " &middot; ".join(
        f'<a href="{html.escape(s["url"])}" target="_blank" rel="noopener">'
        f'{html.escape(s["label"])}</a>'
        for s in SOURCES
    )
    return (
        '<div class="cr-source">The contacts on this page were checked against '
        f'official and organization sources: {links}. Phone numbers and hours '
        'sometimes change, so it is always worth calling ahead.</div>'
    )


def _fix_note() -> str:
    return (
        '<div class="cr-fix">'
        '<strong>Missing or wrong?</strong> Tell us so we can fix it. '
        'Send a correction or suggest a resource through our '
        '<a href="/tip.html">tip page</a>. We keep this list current and '
        'update it as services change.'
        '</div>'
    )


def _body() -> str:
    return (
        _CSS
        + '<div class="cr-wrap">'
        + '<h1 class="page-title">Community Resources</h1>'
        + '<div class="cr-meta">A guide for Chesterfield families</div>'
        + '<p class="cr-lead">A practical guide to local help for Chesterfield '
          'families: schools, health, legal aid, food, jobs, and county '
          'services. Every contact below was checked, and we link to each '
          'organization so you can confirm the details.</p>'
        + _anchor()
        + _toc()
        + "".join(_section(s) for s in SECTIONS)
        + _fix_note()
        + _sources_block()
        + '<div class="cr-xlinks">Related: '
          '<a href="/elections.html">2026 Voter Guide</a> '
          '&middot; <a href="/elected-offices.html">Elected offices</a> '
          '&middot; <a href="/tip.html">Send us a tip</a></div>'
        + '</div>'
    )


def build_recursos() -> Path:
    """Build the Community Resources hub at public/community-resources.html.

    Returns the Path to the page."""
    body = _body()
    page = render._shell(body)
    page = render._inject_og(
        page,
        "Community Resources: a guide for Chesterfield families",
        "A practical guide to local help for Chesterfield County families — "
        "schools, health, legal aid, food, jobs, voting, consulates, and "
        "county services, with phone numbers and links for each.",
        f"{render.SITE_URL}/community-resources.html",
        og_type="website",
    )
    out = PUBLIC / "community-resources.html"
    out.write_text(page, encoding="utf-8")
    return out
