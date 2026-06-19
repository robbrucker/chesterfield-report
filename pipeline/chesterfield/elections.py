"""2026 Voter Guide for Chesterfield County -> /elections.html.

A nonpartisan civic page: an address lookup (where am I / what is on my ballot),
the election calendar, candidate profiles, statewide ballot questions, a voter
FAQ, plain-language "what this office does", and how to vote, all with prominent
links to OFFICIAL Virginia/Chesterfield sources.

Data is hand-curated from verified official + credible sources (VA Dept. of
Elections, Chesterfield General Registrar, VPAP, Ballotpedia, 2026 reporting).
Keep it neutral: party labels and incumbency are facts; bios are short and
factual; no characterizations, no endorsements, equal treatment. Where a fact is
unconfirmed, point readers to the official ballot.
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
VOTER_ID = "https://www.elections.virginia.gov/registration/voterid/"
AMEND_TEXT = "https://www.elections.virginia.gov"

REGISTRAR = {
    "name": "Chesterfield General Registrar and Director of Elections",
    "address": "9848 Lori Road, Chesterfield, VA 23832",
    "phone": "804-748-1471",
    "email": "Registrar@chesterfield.gov",
    "hours": "Monday to Friday, 8:30 a.m. to 5 p.m.",
    "url": "https://www.chesterfield.gov/689/Voter-Registrar",
}

# A candidate: n=name, party=D/R/I/"", inc=incumbent, bio, web, vpap, note.
ELECTIONS = [
    {
        "id": "primary", "name": "August 4 Primary", "date": date(2026, 8, 4),
        "ev_start": date(2026, 6, 18), "ev_end": date(2026, 8, 1),
        "intro": ("Virginia moved its 2026 primary from June to August 4 (House Bill 29). It is an "
                  "open primary, so you choose one party's ballot. What appears on your ballot depends "
                  "on where you live."),
        "timeline": [
            ("Early voting", "June 18 to August 1", "Central Library (7051 Lucy Corr Blvd) and the Registrar's Office. No satellite sites for this primary."),
            ("Register / update by", "Friday, July 24", "After this you can still register and vote a provisional ballot."),
            ("Request a mail ballot by", "Friday, July 24", ""),
            ("Return a mail ballot by", "Postmarked August 4, received by the registrar by noon August 7", ""),
            ("Election Day", "Tuesday, August 4, polls 6 a.m. to 7 p.m.", "In line by 7 p.m. you may vote."),
        ],
        "races": [
            {"office": "U.S. Senate: Republican primary", "scope": "All Chesterfield voters, Republican ballot",
             "note": "The winner faces Sen. Mark Warner (D) in November.",
             "candidates": [
                 {"n": "Kim Farington", "party": "R", "bio": "A CPA from Fairfax Station and a former federal chief financial officer.",
                  "web": "https://kimforvirginia.com/", "vpap": "https://www.vpap.org/candidates/532892-kim-farington/"},
                 {"n": "Bert Mizusawa", "party": "R", "bio": "A retired U.S. Army major general and attorney from McLean.",
                  "web": "https://bertforsenate.com/", "vpap": "https://www.vpap.org/candidates/20931-bert-k-mizusawa/"},
                 {"n": "David Williams", "party": "R", "bio": "A Marine Corps Reserve officer and former State Department and CIA officer from Reston.",
                  "web": "https://www.davidwilliamsforva.com/", "vpap": "https://www.vpap.org/candidates/federal/"},
             ]},
            {"office": "U.S. House, 1st District: Democratic primary", "scope": "1st District voters only, Democratic ballot",
             "map": "va01", "note": "Seven Democrats are running to challenge Rep. Rob Wittman (R). The winner advances to November.",
             "candidates": [
                 {"n": "Salaam Bhatti", "party": "D", "bio": "An attorney and former public-benefits and anti-poverty lawyer.",
                  "web": "https://salaamforva.com/", "vpap": "https://www.vpap.org/candidates/549197-salaam-bhatti/"},
                 {"n": "Tim Cywinski", "party": "D", "bio": "A Richmond community organizer and communications director for the Virginia Sierra Club.",
                  "web": "https://www.votetimva.com/", "vpap": "https://www.vpap.org/candidates/597948-tim-cywinski/"},
                 {"n": "Elizabeth Dempsey Beggs", "party": "D", "bio": "An Army veteran and former tank commander, and a foster parent.",
                  "web": "https://www.elizabethforvirginia.com/", "vpap": "https://www.vpap.org/candidates/609183-elizabeth-dempsey-beggs/"},
                 {"n": "Jason Knapp", "party": "D", "bio": "A Navy veteran and clean-energy consultant from Northumberland County.",
                  "web": "https://jasonknappforcongress.com/", "vpap": "https://www.vpap.org/candidates/597950-jason-knapp/"},
                 {"n": "Ericka Kopp", "party": "D", "bio": "A health-care attorney and former public defender.",
                  "web": "https://erickakopp.com/", "vpap": "https://www.vpap.org/candidates/549195-ericka-kopp/"},
                 {"n": "Shannon Taylor", "party": "D", "bio": "Henrico County's Commonwealth's Attorney since 2012.",
                  "web": "https://shannontaylorva.com/", "vpap": "https://www.vpap.org/candidates/77899-shannon-taylor/"},
                 {"n": "Mel Tull", "party": "D", "bio": "A business attorney and Army veteran from Henrico County.",
                  "web": "https://meltullforcongress.com/", "vpap": "https://www.vpap.org/candidates/343883-mel-tull/"},
             ]},
            {"office": "Dale District Supervisor: special Democratic primary", "scope": "Dale District voters only",
             "note": "A special election for the seat of the late Jim Holland. The primary winner advances to November.",
             "candidates": [
                 {"n": "Kathryn Crosby", "party": "D", "bio": "A longtime Dale District resident running on community accountability.",
                  "web": "https://secure.actblue.com/donate/crosbyfordale", "vpap": "https://www.vpap.org/offices/chesterfield-county-supervisor-dale/elections/"},
                 {"n": "LeQuan Hylton", "party": "D", "inc": True, "bio": "Appointed interim Dale supervisor in 2025; previously the district's planning commissioner, and an Army Reserve officer and Afghanistan veteran.",
                  "web": "https://www.chesterfield.gov/1244/Dale-District---Hylton", "vpap": "https://www.vpap.org/offices/chesterfield-county-supervisor-dale/elections/"},
             ]},
        ],
    },
    {
        "id": "general", "name": "November 3 General Election", "date": date(2026, 11, 3),
        "ev_start": date(2026, 9, 18), "ev_end": date(2026, 10, 31),
        "intro": "The general election. Some races are decided in the August 4 primaries above.",
        "timeline": [
            ("Early voting", "September 18 to October 31", "Chesterfield locations are posted closer to September; check the registrar."),
            ("Register / update by", "Friday, October 23", "After this you can still register and vote a provisional ballot."),
            ("Request a mail ballot by", "5 p.m. Friday, October 23", ""),
            ("Return a mail ballot by", "Postmarked November 3 (confirm the exact receipt deadline with the registrar)", ""),
            ("Election Day", "Tuesday, November 3, polls 6 a.m. to 7 p.m.", "In line by 7 p.m. you may vote."),
        ],
        "races": [
            {"office": "U.S. Senate", "scope": "All Chesterfield voters", "note": "",
             "candidates": [
                 {"n": "Mark Warner", "party": "D", "inc": True, "bio": "U.S. Senator from Virginia since 2009 and a former governor of Virginia.",
                  "web": "https://www.markwarner.com/", "vpap": "https://www.vpap.org/candidates/federal/5301-mark-warner/"},
                 {"n": "Republican nominee", "party": "R", "bio": "Decided in the August 4 Republican primary.", "web": "", "vpap": ""},
             ]},
            {"office": "U.S. House, 1st District", "scope": "1st District voters", "map": "va01", "note": "",
             "candidates": [
                 {"n": "Rob Wittman", "party": "R", "inc": True, "bio": "Has represented the 1st District since 2007.",
                  "web": "https://wittman.house.gov/", "vpap": "https://www.vpap.org/candidates/federal/"},
                 {"n": "Democratic nominee", "party": "D", "bio": "Decided in the August 4 Democratic primary (seven candidates).", "web": "", "vpap": ""},
             ]},
            {"office": "U.S. House, 4th District", "scope": "4th District voters (most of Chesterfield)", "map": "va04", "note": "",
             "candidates": [
                 {"n": "Jennifer McClellan", "party": "D", "inc": True, "bio": "Has represented the 4th District since 2023, after serving in the Virginia legislature.",
                  "web": "https://jennifermcclellan.com/", "vpap": "https://www.vpap.org/candidates/35804-jennifer-mcclellan/"},
                 {"n": "Jason Brown II", "party": "I", "bio": "A member of the Dinwiddie County School Board.",
                  "web": "https://jasonforcongress2026.com/", "vpap": "https://www.vpap.org/candidates/450887-jason-l-brown-ii/"},
                 {"n": "Andre Kersey", "party": "I", "bio": "A Richmond minister and teacher.",
                  "web": "https://kerseyforcongress.org/", "vpap": "https://www.vpap.org/offices/us-representative-4/elections/"},
             ]},
            {"office": "Dale District Supervisor (special)", "scope": "Dale District voters", "note": "Confirm the final ballot with the registrar.",
             "candidates": [
                 {"n": "Winner of the August 4 Democratic primary", "party": "", "bio": "Kathryn Crosby or LeQuan Hylton.", "web": "", "vpap": ""},
             ]},
            {"office": "Statewide ballot questions", "scope": "All Chesterfield voters",
             "note": "Read the exact wording of each amendment on your sample ballot or at the Virginia Department of Elections before you vote.",
             "questions": [
                 {"t": "Marriage", "d": "A proposed amendment on the right to marry regardless of sex or gender."},
                 {"t": "Voting rights restoration", "d": "A proposed amendment to automatically restore voting rights to people with felony convictions after they complete their sentence."},
                 {"t": "Reproductive rights", "d": "A proposed amendment on reproductive and abortion rights."},
             ]},
        ],
    },
]

CIVICS = [
    ("U.S. Senator", "Virginia elects two U.S. Senators, each to a six-year term, to represent the whole state. "
     "Senators write and vote on federal law, confirm judges and appointments, and help set the national budget. "
     "Their offices also help residents deal with federal agencies."),
    ("U.S. Representative", "A U.S. Representative serves a two-year term and represents one congressional district "
     "(Chesterfield is split among more than one). Representatives write federal law, control federal spending and "
     "taxes, and oversee the executive branch. This is your most local voice in Congress."),
    ("County Supervisor", "Chesterfield is governed by a five-member Board of Supervisors, each elected from a "
     "district to a four-year term. The Board adopts the county budget, sets local tax rates, makes zoning and "
     "land-use decisions, and funds schools, public safety, roads, parks, and libraries. These are the decisions "
     "that most directly shape your tax bill and your neighborhood."),
]

FAQ = [
    ("Do I need a photo ID to vote?",
     "No. Virginia does not require a photo ID. Show an acceptable ID, or sign an ID Confirmation Statement at the "
     "polls and still cast a regular ballot. Accepted IDs include a Virginia driver's license or DMV ID (expired is "
     "fine), a U.S. passport, a government or employer photo ID, a U.S. college student ID, your voter registration "
     "card, or a recent utility bill, bank statement, or paycheck with your name and address.", VOTER_ID),
    ("Can I register and vote on the same day?",
     "Yes. After the regular registration deadline (about three weeks before the election), you can still register "
     "in person and vote a provisional ballot, either during early voting or on Election Day. The electoral board "
     "reviews and approves it before it counts.", "https://www.elections.virginia.gov/registration/same-day-voter-registration/"),
    ("Is curbside or accessible voting available?",
     "Yes. Any voter who is 65 or older or who has a disability may vote curbside without leaving their vehicle. "
     "Every polling place is wheelchair accessible and has a ballot-marking device so voters with disabilities can "
     "vote privately. It helps to call your polling place ahead.", "https://www.elections.virginia.gov/casting-a-ballot/accessible-voting/"),
    ("Where can I drop off a mail ballot?",
     "Chesterfield offers ballot drop boxes during early voting and on Election Day, including at the Registrar's "
     "Office and the Central Library. Exact locations and hours are set per election, so confirm the current sites "
     "with the registrar.", REGISTRAR["url"]),
    ("What is a provisional ballot?",
     "It is used when there is a question about your eligibility, for example if your name is not on the pollbook, "
     "you registered same-day, or you lacked ID and did not sign the confirmation statement. It is not scanned at "
     "the polls; the electoral board reviews your eligibility and decides after the election.", "https://www.elections.virginia.gov/registration/same-day-voter-registration/"),
    ("I have a past felony conviction. Can I vote?",
     "In Virginia a felony conviction removes your right to vote, and the Governor restores it individually. Check "
     "your status or request restoration through the Secretary of the Commonwealth's process. Once restored, you "
     "can register.", "https://www.restore.virginia.gov/restoration-of-rights-process/"),
    ("I just moved here, or it is my first time. How do I register?",
     "You must be a U.S. citizen, a Virginia resident, and 18 by the next general election. Register online at the "
     "Virginia Citizen Portal, by mail, in person at the registrar, or at the DMV. The deadline for a regular ballot "
     "is about three weeks before the election; after that, same-day registration with a provisional ballot is "
     "available.", "https://www.elections.virginia.gov/registration/how-to-register/"),
    ("What should I bring, and can I take time off work?",
     "Polls are open 6 a.m. to 7 p.m.; anyone in line at 7 p.m. may vote. Bring an accepted ID if you have one, or "
     "be ready to sign the confirmation statement. You may bring a sample ballot and your phone, but do not "
     "photograph your ballot. Virginia has no general law requiring paid time off to vote, so use early voting if "
     "your hours conflict.", PORTAL),
]

_PNAME = {"D": "Democrat", "R": "Republican", "I": "Independent"}


def _esc(s) -> str:
    return html.escape(str(s or "").strip())


def _status_banner() -> str:
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


def _lookup_section() -> str:
    # The U.S. Census geocoder does not send CORS headers, so a browser fetch()
    # is blocked cross-origin. The endpoint does support JSONP (format=jsonp),
    # so we load it via a <script> tag with a unique callback instead.
    js = (
        "<script>(function(){"
        "var PORTAL=" + repr(PORTAL) + ",POLL=" + repr(POLL_LOOKUP) + ";"
        "var f=document.getElementById('el-lk-form'),i=document.getElementById('el-addr'),o=document.getElementById('el-result');"
        "if(!f)return;"
        "var R={senate:'U.S. Senate: Sen. Mark Warner (D) faces the Republican nominee chosen in the August 4 primary.',"
        "'01':'U.S. House, 1st District: Rep. Rob Wittman (R) faces the Democrat chosen in the August 4 primary (seven Democrats are running).',"
        "'04':'U.S. House, 4th District: Rep. Jennifer McClellan (D), Jason Brown II (Independent), and Andre Kersey (Independent).'};"
        "function esc(s){return (s||'').replace(/[&<>]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});}"
        "function fail(){o.innerHTML='<div class=\\\"el-res el-res-err\\\">Something went wrong. Look up your address at <a href=\\\"'+PORTAL+'\\\" target=\\\"_blank\\\" rel=\\\"noopener\\\">the official Virginia portal</a>.</div>';}"
        "function done(d,a){"
        "var m=(d&&d.result&&d.result.addressMatches)||[];"
        "if(!m.length){o.innerHTML='<div class=\\\"el-res el-res-err\\\">We could not find that address. Check the spelling, or use <a href=\\\"'+PORTAL+'\\\" target=\\\"_blank\\\" rel=\\\"noopener\\\">the official Virginia lookup</a>.</div>';return;}"
        "var g=m[0].geographies||{},co=(g['Counties']||[])[0]||{};"
        "if(co.GEOID!=='51041'){o.innerHTML='<div class=\\\"el-res el-res-err\\\"><strong>That address is in '+esc(co.NAME||'another county')+', not Chesterfield County.</strong> Find your races and polling place at <a href=\\\"'+PORTAL+'\\\" target=\\\"_blank\\\" rel=\\\"noopener\\\">vote.elections.virginia.gov</a>.</div>';return;}"
        "var cd=((g['119th Congressional Districts']||[])[0]||{}).CD119||'';"
        "var items=['<li>'+R.senate+'</li>'];"
        "if(cd==='01'||cd==='04'){items.push('<li>'+R[cd]+'</li>');}"
        "items.push('<li>Three proposed constitutional amendments (on marriage, voting-rights restoration, and reproductive rights) are on the November ballot for all voters.</li>');"
        "items.push('<li>If you live in the <strong>Dale magisterial district</strong>, the special election for Dale District Supervisor is also on your ballot.</li>');"
        "var lab=cd==='01'?'the 1st Congressional District (VA-01)':cd==='04'?'the 4th Congressional District (VA-04)':'Chesterfield County';"
        "o.innerHTML='<div class=\\\"el-res el-res-ok\\\"><div class=\\\"el-res-head\\\">You are in Chesterfield County, in '+lab+'.</div>'"
        "+'<div class=\\\"el-res-sub\\\">'+esc(m[0].matchedAddress||a)+'</div>'"
        "+'<p class=\\\"el-res-l\\\">On your ballot:</p><ul class=\\\"el-res-list\\\">'+items.join('')+'</ul>'"
        "+'<a class=\\\"el-btn\\\" href=\\\"'+POLL+'\\\" target=\\\"_blank\\\" rel=\\\"noopener\\\">Find your exact polling place and sample ballot &rarr;</a>'"
        "+'<p class=\\\"el-res-note\\\">Your district is computed from the U.S. Census Bureau. Always confirm your polling place and full ballot at the official lookup.</p></div>';"
        "}"
        "var seq=0;"
        "f.addEventListener('submit',function(e){e.preventDefault();var a=i.value.trim();if(!a){return;}"
        "o.innerHTML='<p class=\\\"el-loading\\\">Looking up your address...</p>';"
        "var cb='__elcb'+(++seq),s=document.createElement('script'),to;"
        "function cleanup(){clearTimeout(to);try{delete window[cb];}catch(_){window[cb]=undefined;}if(s.parentNode){s.parentNode.removeChild(s);}}"
        "window[cb]=function(d){cleanup();try{done(d,a);}catch(_){fail();}};"
        "s.onerror=function(){cleanup();fail();};"
        "to=setTimeout(function(){cleanup();fail();},15000);"
        "s.src='https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress?address='+encodeURIComponent(a)+'&benchmark=Public_AR_Current&vintage=Current_Current&layers=all&format=jsonp&callback='+cb;"
        "document.body.appendChild(s);"
        "});})();</script>"
    )
    return (
        '<section class="el-lookup">'
        '<h2>Find your races</h2>'
        '<p class="el-lookup-sub">Enter your address to see what is on your ballot in Chesterfield. '
        'It runs in your browser using the U.S. Census Bureau, and nothing is stored.</p>'
        '<form id="el-lk-form" class="el-lk-form">'
        '<input id="el-addr" type="text" placeholder="123 Main St, Midlothian, VA 23113" '
        'autocomplete="street-address" aria-label="Your street address">'
        '<button type="submit">Look it up</button>'
        '</form>'
        '<div id="el-result" aria-live="polite"></div>'
        '</section>' + js
    )


def _candidate(c: dict) -> str:
    party = c.get("party", "")
    tag = ""
    if party:
        lbl = _PNAME.get(party, party)
        if c.get("inc"):
            lbl += ", incumbent"
        tag = f'<span class="el-tag el-p-{party.lower()}">{_esc(lbl)}</span>'
    bio = f'<div class="el-c-bio">{_esc(c["bio"])}</div>' if c.get("bio") else ""
    links = []
    if c.get("web"):
        links.append(f'<a href="{_esc(c["web"])}" target="_blank" rel="noopener">Website</a>')
    if c.get("vpap"):
        links.append(f'<a href="{_esc(c["vpap"])}" target="_blank" rel="noopener">Campaign finance</a>')
    links_html = f'<div class="el-c-links">{" &middot; ".join(links)}</div>' if links else ""
    return (f'<div class="el-c"><div class="el-c-top"><span class="el-c-name">{_esc(c["n"])}</span>{tag}</div>'
            f'{bio}{links_html}</div>')


def _race_card(r: dict) -> str:
    if r.get("questions"):
        body = "".join(
            f'<div class="el-q"><div class="el-q-t">{_esc(q["t"])}</div>'
            f'<div class="el-q-d">{_esc(q["d"])}</div></div>'
            for q in r["questions"])
    else:
        body = "".join(_candidate(c) for c in r.get("candidates", []))
    note = f'<p class="el-race-note">{_esc(r["note"])}</p>' if r.get("note") else ""
    mp = r.get("map")
    mphtml = ""
    if mp:
        which = "1st (VA-01)" if mp == "va01" else "4th (VA-04)"
        mphtml = (f'<img class="el-race-map" src="/assets/elections-{mp}.svg" loading="lazy" '
                  f'alt="Map of Chesterfield County with the {which} congressional district shaded">')
    return (
        '<div class="el-race">'
        f'<div class="el-race-office">{_esc(r["office"])}</div>'
        f'<div class="el-race-scope">{_esc(r["scope"])}</div>'
        f'{mphtml}{body}{note}'
        '</div>'
    )


def _districts_section() -> str:
    return (
        '<section class="el-dist">'
        '<h2>Your districts, explained</h2>'
        '<p class="el-dist-lead">Chesterfield does not vote as one block. The county is split between '
        'two U.S. House districts and five local magisterial districts, so the ballot one neighbor sees '
        'is not always the ballot the next street over sees. Here is how the lines fall.</p>'
        '<figure class="el-dist-fig">'
        '<img class="el-dist-map" src="/assets/elections-districts.svg" loading="lazy" '
        'alt="Map of Chesterfield County divided between congressional districts VA-01 in the west and VA-04 in the east">'
        '<figcaption class="el-dist-cap">'
        '<span class="el-key"><span class="el-sw el-sw-01"></span>1st District (VA-01)</span>'
        '<span class="el-key"><span class="el-sw el-sw-04"></span>4th District (VA-04)</span>'
        '<span class="el-dist-src">County outline and district lines: U.S. Census Bureau (119th Congress).</span>'
        '</figcaption>'
        '</figure>'
        '<div class="el-dist-grid">'
        '<div class="el-dist-card">'
        '<div class="el-dist-h"><span class="el-sw el-sw-01"></span>1st District (VA-01)</div>'
        '<p>The <strong>western and southwestern</strong> county, including much of the Midlothian area and '
        'the Route 360 / Hull Street corridor out toward Moseley. Represented by '
        '<strong>Rep. Rob Wittman (R)</strong>, who has held the seat since 2007. In 2026 he faces the '
        'Democrat chosen in the August 4 primary, where seven candidates are running.</p>'
        '</div>'
        '<div class="el-dist-card">'
        '<div class="el-dist-h"><span class="el-sw el-sw-04"></span>4th District (VA-04)</div>'
        '<p>The <strong>central and eastern</strong> county, including the courthouse area, Chester, '
        'Bermuda Hundred, and the more densely populated communities toward Richmond and the rivers. This '
        'is where most Chesterfield voters live. Represented by <strong>Rep. Jennifer McClellan (D)</strong>, '
        'in office since 2023; in November she faces independents Jason Brown II and Andre Kersey.</p>'
        '</div>'
        '</div>'
        '<p class="el-dist-note"><strong>Local magisterial districts.</strong> For county government, '
        'Chesterfield is divided into five magisterial districts, Bermuda, Clover Hill, Dale, Matoaca, and '
        'Midlothian, each electing one member of the '
        '<a href="/board.html">Board of Supervisors</a> and one School Board member. In 2026 only the '
        '<strong>Dale District</strong> has a county race on the ballot, a special election for the late '
        'Jim Holland\'s seat. Not sure which district you are in? Use the address lookup above, or the '
        f'county\'s <a href="{PRECINCT_MAPS}" target="_blank" rel="noopener">precinct maps</a>.</p>'
        '</section>'
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


def _civics_section() -> str:
    items = "".join(
        f'<div class="el-civ"><div class="el-civ-t">{_esc(t)}</div>'
        f'<div class="el-civ-d">{_esc(d)}</div></div>'
        for t, d in CIVICS)
    return ('<section class="el-civics"><h2>What these offices do</h2>'
            f'<div class="el-civ-grid">{items}</div></section>')


def _faq_section() -> str:
    items = "".join(
        '<details class="el-faq">'
        f'<summary>{_esc(q)}</summary>'
        f'<div class="el-faq-a">{_esc(a)} '
        f'<a href="{_esc(src)}" target="_blank" rel="noopener">Official source &nearr;</a></div>'
        '</details>'
        for q, a, src in FAQ)
    return f'<section class="el-faqs"><h2>Voter FAQ</h2>{items}</section>'


_EL_CSS = """<style>
.el-wrap{max-width:820px;margin:0 auto;}
.el-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:64ch;margin:.4rem 0 1.2rem;}
.el-now{display:flex;align-items:center;gap:.6rem;background:var(--surface-card);border:1px solid var(--accent);border-radius:var(--radius-sm);padding:.7rem 1rem;font:var(--fw-semibold) var(--fs-md) var(--font-sans);color:var(--text-primary);margin:0 0 1.4rem;}
.el-now-dot{width:10px;height:10px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 4px rgba(154,50,34,.18);flex:none;}
.el-lookup{background:var(--surface-card);border:1px solid var(--border);border-radius:var(--radius-sm);padding:1.1rem 1.2rem;margin:0 0 1.8rem;}
.el-lookup h2{font:var(--fw-bold) var(--fs-xl)/1.15 var(--font-display);margin:0 0 .2rem;color:var(--text-primary);}
.el-lookup-sub{font:var(--fs-sm)/1.5 var(--font-sans);color:var(--text-tertiary);margin:0 0 .8rem;}
.el-lk-form{display:flex;flex-wrap:wrap;gap:8px;}
.el-lk-form input{flex:1 1 240px;background:var(--surface-raised,#fff);border:1px solid var(--border);border-radius:var(--radius-xs);padding:11px 13px;color:var(--text-primary);font:var(--fs-sm) var(--font-sans);}
.el-lk-form input:focus{outline:none;border-color:var(--accent);}
.el-lk-form button{background:var(--accent);color:#fff;border:none;border-radius:var(--radius-xs);padding:11px 22px;font:var(--fw-bold) var(--fs-sm) var(--font-sans);cursor:pointer;}
.el-loading{font:var(--fs-sm) var(--font-sans);color:var(--text-tertiary);margin:.8rem 0 0;}
.el-res{margin:1rem 0 0;border-radius:var(--radius-xs);padding:.9rem 1rem;font:var(--fs-sm)/1.55 var(--font-sans);}
.el-res-ok{border:1px solid var(--accent);background:var(--surface-sunken,rgba(154,50,34,.04));}
.el-res-err{border:1px solid var(--border);background:var(--surface-raised,#fff);color:var(--text-secondary);}
.el-res-err a,.el-res a{color:var(--accent);}
.el-res-head{font:var(--fw-bold) var(--fs-md)/1.25 var(--font-display);color:var(--text-primary);}
.el-res-sub{font:var(--fs-2xs) var(--font-mono);color:var(--text-tertiary);margin:.1rem 0 .5rem;}
.el-res-l{font:var(--fw-semibold) var(--fs-sm) var(--font-sans);margin:.4rem 0 .2rem;color:var(--text-primary);}
.el-res-list{margin:.2rem 0 .7rem;padding-left:1.2rem;color:var(--text-secondary);}
.el-res-list li{margin:.3rem 0;}
.el-res-note{font:var(--fs-3xs)/1.4 var(--font-sans);color:var(--text-tertiary);margin:.6rem 0 0;}
.el-cta{display:flex;flex-wrap:wrap;gap:.6rem;margin:0 0 1.8rem;}
.el-btn{display:inline-block;background:var(--accent);color:#fff;border-radius:var(--radius-xs);padding:11px 20px;font:var(--fw-bold) var(--fs-sm) var(--font-sans);text-decoration:none;}
.el-btn.sec{background:var(--surface-card);color:var(--accent);border:1px solid var(--accent);}
.el-block,.el-civics,.el-faqs{border-top:1px solid var(--border);margin-top:2rem;padding-top:.4rem;}
.el-block h2,.el-civics h2,.el-faqs h2{font:var(--fw-bold) var(--fs-2xl)/1.15 var(--font-display);color:var(--text-primary);margin:1rem 0 .3rem;}
.el-block h3{font:var(--fw-bold) var(--fs-2xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--accent);margin:1.6rem 0 .7rem;}
.el-intro{font:var(--fs-md)/1.6 var(--font-sans);color:var(--text-secondary);}
.el-dates{margin:.3rem 0 0;}
.el-date{border-top:1px solid var(--border);padding:.7rem 0;}
.el-date-top{display:flex;justify-content:space-between;align-items:baseline;gap:.6rem 1.2rem;flex-wrap:wrap;}
.el-date-lbl{font:var(--fw-bold) var(--fs-md)/1.25 var(--font-display);color:var(--text-primary);}
.el-date-when{font:var(--fw-semibold) var(--fs-sm)/1.3 var(--font-sans);color:var(--accent);text-align:right;}
.el-date-det{font:var(--fs-2xs)/1.5 var(--font-sans);color:var(--text-tertiary);margin-top:.25rem;max-width:64ch;}
.el-races{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px;}
.el-race{border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface-card);padding:.9rem 1.05rem;}
.el-race-office{font:var(--fw-bold) var(--fs-md)/1.2 var(--font-display);color:var(--text-primary);}
.el-race-scope{font:var(--fw-semibold) var(--fs-3xs) var(--font-mono);text-transform:uppercase;letter-spacing:var(--ls-wide);color:var(--text-tertiary);margin:.2rem 0 .6rem;}
.el-race-map{display:block;width:100%;max-width:200px;height:auto;margin:.2rem 0 .7rem;border:1px solid var(--border);border-radius:var(--radius-xs);background:#fff;}
.el-dist{border-top:1px solid var(--border);margin-top:2rem;padding-top:.4rem;}
.el-dist h2{font:var(--fw-bold) var(--fs-2xl)/1.15 var(--font-display);color:var(--text-primary);margin:1rem 0 .3rem;}
.el-dist-lead{font:var(--fs-md)/1.6 var(--font-sans);color:var(--text-secondary);max-width:64ch;margin:.2rem 0 1.1rem;}
.el-dist-fig{margin:0 0 1.2rem;}
.el-dist-map{display:block;width:100%;max-width:460px;height:auto;margin:0 auto;border:1px solid var(--border);border-radius:var(--radius-sm);background:#fff;padding:.4rem;}
.el-dist-cap{display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:.4rem 1.1rem;margin-top:.7rem;font:var(--fs-2xs) var(--font-sans);color:var(--text-secondary);}
.el-key{display:inline-flex;align-items:center;gap:.4rem;font-weight:600;}
.el-sw{display:inline-block;width:13px;height:13px;border-radius:3px;border:1px solid rgba(0,0,0,.2);flex:none;}
.el-sw-01{background:#3f6f86;}
.el-sw-04{background:#9a3322;}
.el-dist-src{flex-basis:100%;text-align:center;font:var(--fs-3xs) var(--font-mono);color:var(--text-tertiary);}
.el-dist-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;margin:0 0 1.1rem;}
.el-dist-card{border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface-card);padding:.9rem 1.05rem;}
.el-dist-h{display:flex;align-items:center;gap:.5rem;font:var(--fw-bold) var(--fs-md) var(--font-display);color:var(--text-primary);margin-bottom:.4rem;}
.el-dist-card p{font:var(--fs-2xs)/1.6 var(--font-sans);color:var(--text-secondary);margin:0;}
.el-dist-note{font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);background:var(--surface-card);border:1px solid var(--border);border-radius:var(--radius-xs);padding:.8rem 1rem;max-width:none;}
.el-dist-note a,.el-dist-card a{color:var(--accent);}
.el-c{border-top:1px solid var(--border);padding:.55rem 0;}
.el-c:first-of-type{border-top:none;}
.el-c-top{display:flex;flex-wrap:wrap;align-items:baseline;gap:.4rem;}
.el-c-name{font:var(--fw-bold) var(--fs-sm) var(--font-sans);color:var(--text-primary);}
.el-tag{font:var(--fw-semibold) var(--fs-3xs) var(--font-sans);border-radius:3px;padding:1px 6px;}
.el-p-d{color:#1c4e8a;background:rgba(28,78,138,.1);}
.el-p-r{color:#a02622;background:rgba(160,38,34,.1);}
.el-p-i{color:#555;background:rgba(85,85,85,.1);}
.el-c-bio{font:var(--fs-2xs)/1.5 var(--font-sans);color:var(--text-secondary);margin:.2rem 0;}
.el-c-links{font:var(--fw-semibold) var(--fs-3xs) var(--font-sans);}
.el-c-links a{color:var(--accent);}
.el-q{border-top:1px solid var(--border);padding:.5rem 0;}
.el-q:first-of-type{border-top:none;}
.el-q-t{font:var(--fw-bold) var(--fs-sm) var(--font-sans);color:var(--text-primary);}
.el-q-d{font:var(--fs-2xs)/1.5 var(--font-sans);color:var(--text-secondary);}
.el-race-note{font:var(--fs-2xs)/1.45 var(--font-sans);color:var(--text-tertiary);margin:.5rem 0 0;}
.el-civ-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px;margin-top:.6rem;}
.el-civ{border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface-card);padding:.9rem 1.05rem;}
.el-civ-t{font:var(--fw-bold) var(--fs-md) var(--font-display);color:var(--text-primary);margin-bottom:.2rem;}
.el-civ-d{font:var(--fs-2xs)/1.55 var(--font-sans);color:var(--text-secondary);}
.el-faq{border-top:1px solid var(--border);padding:.2rem 0;}
.el-faq summary{font:var(--fw-bold) var(--fs-md)/1.4 var(--font-sans);color:var(--text-primary);cursor:pointer;padding:.6rem 0;list-style:none;}
.el-faq summary::-webkit-details-marker{display:none;}
.el-faq summary::before{content:"+";color:var(--accent);font-weight:700;margin-right:.5rem;}
.el-faq[open] summary::before{content:"\\2013";}
.el-faq-a{font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);padding:0 0 .8rem;max-width:70ch;}
.el-faq-a a{color:var(--accent);}
.el-how{border-top:1px solid var(--border);margin-top:2rem;padding-top:.4rem;}
.el-how h2{font:var(--fw-bold) var(--fs-2xl) var(--font-display);margin:1rem 0 .6rem;}
.el-how ul{font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);}
.el-reg{border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:var(--radius-xs);background:var(--surface-card);padding:.9rem 1.1rem;margin:1rem 0;font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);}
.el-reg strong{color:var(--text-primary);}
.el-disc{margin-top:2rem;padding:1rem 1.1rem;border-left:3px solid var(--accent);background:var(--surface-card);border-radius:var(--radius-xs);font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);}
.el-disc a{color:var(--accent);}
</style>"""


def build_elections() -> Path:
    r = REGISTRAR
    how = (
        '<section class="el-how">'
        '<h2>How to vote in Chesterfield</h2>'
        '<ul>'
        f'<li><strong>Register or check your status:</strong> at the official portal, '
        f'<a href="{PORTAL}" target="_blank" rel="noopener">vote.elections.virginia.gov</a>, '
        'where you can also see your personalized sample ballot and districts.</li>'
        '<li><strong>Vote early, in person:</strong> at the Central Library (7051 Lucy Corr Blvd) or the '
        'Registrar\'s Office during the windows above. November locations post closer to September.</li>'
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
        + _lookup_section()
        + '<div class="el-cta">'
        + f'<a class="el-btn" href="{PORTAL}" target="_blank" rel="noopener">Register or check your status</a>'
        + f'<a class="el-btn sec" href="{POLL_LOOKUP}" target="_blank" rel="noopener">Find your polling place</a>'
        + '</div>'
        + _districts_section()
        + _election_block(ELECTIONS[0])
        + _election_block(ELECTIONS[1])
        + _civics_section()
        + _faq_section()
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
        "How and when to vote in Chesterfield County, Virginia in 2026: the August 4 primary and "
        "November 3 general election, who is on your ballot, statewide ballot questions, and how to register.",
        f"{render.SITE_URL}/elections.html", og_type="website")
    out = PUBLIC / "elections.html"
    out.write_text(page, encoding="utf-8")
    return out
