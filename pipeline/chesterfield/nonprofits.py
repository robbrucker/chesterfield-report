"""Local Nonprofits: a categorized, mappable directory of nonprofits and
charities that serve Chesterfield County.

Builds public/nonprofits.html from pipeline/nonprofits.json. Same Leaflet +
CARTO (theme-aware) stack as worship.py, with a category filter (chips) that
drives both the map and the grouped list at once.

Map convention (the hybrid the worship map already uses for adjacent sites):
  - SOLID accent pin  = a nonprofit based in Chesterfield / Colonial Heights.
  - HOLLOW accent pin  = a regional (greater-Richmond) nonprofit that serves
                         Chesterfield residents but is headquartered nearby.
  - SOLID slate pin    = a county government agency (the public front door for
                         the same needs); included for completeness, clearly not
                         a nonprofit.

Source list is curated from Chesterfield County's own Human Services Non-Profit
Collaborative plus established regional providers (research/local-nonprofits.md).
The list is explicitly not exhaustive: any org can ask to be added or corrected.
Stdlib only; reuses render._shell() / _inject_og.
"""
from __future__ import annotations

import html
import json
import json as _json
import os
from collections import Counter
from pathlib import Path

from . import render
from .render import PUBLIC

DATA = Path(__file__).resolve().parents[1] / "nonprofits.json"

# Display order + labels for the 12 categories (slugs match nonprofits.json).
CATEGORIES = [
    ("human-services", "Human Services & Housing"),
    ("food", "Food Assistance"),
    ("health", "Health & Free Clinics"),
    ("youth", "Youth & Education"),
    ("seniors", "Seniors"),
    ("animals", "Animal Welfare"),
    ("environment", "Environment"),
    ("arts", "Arts & Culture"),
    ("veterans", "Veterans"),
    ("crisis", "Domestic Violence & Crisis"),
    ("immigrant", "Immigrant & Latino Services"),
    ("other", "Other"),
]
CAT_LABEL = dict(CATEGORIES)

ACCENT = "#c0392b"   # nonprofit pins (overridden live by the CSS --accent var)
SLATE = "#6b7280"    # county-agency pins

_MAP_HEAD = (
    '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">'
    '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>'
)


def _load() -> list:
    try:
        return json.loads(DATA.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return []


def _area_label(area: str) -> str:
    return {
        "chesterfield": "Chesterfield",
        "regional": "Serves Chesterfield",
        "county-agency": "County agency",
    }.get(area, "")


def _filter_chips(counts: Counter, total: int) -> str:
    chips = [
        '<button type="button" class="np-chip is-active" data-cat="All" '
        f'aria-pressed="true">All <span class="np-chip__n">{total}</span></button>'
    ]
    for slug, label in CATEGORIES:
        n = counts.get(slug, 0)
        if not n:
            continue
        chips.append(
            f'<button type="button" class="np-chip" data-cat="{slug}" aria-pressed="false">'
            f'{html.escape(label)} <span class="np-chip__n">{n}</span></button>'
        )
    return '<div class="np-chips" role="group" aria-label="Filter by category">' + "".join(chips) + "</div>"


def _legend() -> str:
    return (
        '<div class="np-legend">'
        '<span class="np-leg__item"><span class="np-leg__dot np-leg__dot--solid"></span>'
        'Based in Chesterfield</span>'
        '<span class="np-leg__item"><span class="np-leg__dot np-leg__dot--hollow"></span>'
        'Regional, serves Chesterfield (HQ nearby)</span>'
        '<span class="np-leg__item"><span class="np-leg__dot np-leg__dot--agency"></span>'
        'County agency (not a nonprofit)</span>'
        '</div>'
    )


def _map_section(orgs: list) -> str:
    # points: [name, lat, lon, category, area, desc, phone, web, address]
    pts = []
    for o in orgs:
        if o.get("lat") is None or o.get("lon") is None:
            continue
        pts.append([
            o.get("name", ""), o["lat"], o["lon"], o.get("category", "other"),
            o.get("area", "regional"), o.get("desc", ""), o.get("phone", ""),
            o.get("web", ""), o.get("address", ""),
        ])
    if not pts:
        return ""
    data = _json.dumps(pts, ensure_ascii=False)
    return (
        _MAP_HEAD
        + '<div id="np-map" class="np-map"></div>'
        '<div class="np-count" id="np-count" aria-live="polite"></div>'
        '<script>(function(){if(!window.L)return;'
        'var pts=' + data + ';var active="All";var SLATE="' + SLATE + '";'
        'var ACCENT=getComputedStyle(document.documentElement).getPropertyValue("--accent").trim()||"' + ACCENT + '";'
        'function esc(s){var d=document.createElement("div");d.textContent=s==null?"":s;return d.innerHTML;}'
        'function tileUrl(){var dark=document.documentElement.getAttribute("data-theme")==="dark";'
        'return dark?"https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"'
        ':"https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";}'
        'var map=L.map("np-map",{scrollWheelZoom:false}).setView([37.46,-77.55],10);'
        'var layer=L.tileLayer(tileUrl(),{attribution:"\\u00a9 OpenStreetMap \\u00a9 CARTO",'
        'subdomains:"abcd",maxZoom:19}).addTo(map);'
        'var all=L.featureGroup().addTo(map);var byCat={};'
        'pts.forEach(function(p){'
        'var name=p[0],lat=p[1],lon=p[2],cat=p[3],area=p[4],desc=p[5],phone=p[6],web=p[7],addr=p[8];'
        'var opts;'
        'if(area==="county-agency"){opts={radius:7,color:"#fff",weight:1.5,fillColor:SLATE,fillOpacity:0.95};}'
        'else if(area==="regional"){opts={radius:7,color:ACCENT,weight:2.5,fillColor:"#fff",fillOpacity:0.25,dashArray:"2,2"};}'
        'else{opts={radius:7,color:"#fff",weight:1.5,fillColor:ACCENT,fillOpacity:0.95};}'
        'var m=L.circleMarker([lat,lon],opts);'
        'var h="<strong>"+esc(name)+"</strong>";'
        'if(desc){h+="<br><span class=\\"np-pop-d\\">"+esc(desc)+"</span>";}'
        'if(addr){h+="<br>"+esc(addr);}'
        'if(area==="regional"){h+="<br><em>Serves Chesterfield, HQ nearby</em>";}'
        'if(phone){h+="<br><a href=\\"tel:"+esc(phone.replace(/[^0-9]/g,""))+"\\">"+esc(phone)+"</a>";}'
        'if(web){h+="<br><a href=\\""+esc(web)+"\\" target=\\"_blank\\" rel=\\"noopener\\">Website</a>";}'
        'm.bindPopup(h);(byCat[cat]=byCat[cat]||[]).push(m);m.addTo(all);});'
        'try{map.fitBounds(all.getBounds().pad(0.08));}catch(e){}'
        'var countEl=document.getElementById("np-count");'
        'function visible(){var n=0;Object.keys(byCat).forEach(function(c){'
        'var show=(active==="All"||active===c);'
        'byCat[c].forEach(function(m){if(show){if(!all.hasLayer(m))all.addLayer(m);n++;}'
        'else{if(all.hasLayer(m))all.removeLayer(m);}});});return n;}'
        'function update(){var n=visible();'
        'countEl.textContent=n+" mapped "+(n===1?"location":"locations");}'
        'window.__npSetCat=function(c){active=c;update();};'
        'update();'
        'new MutationObserver(function(){layer.setUrl(tileUrl());})'
        '.observe(document.documentElement,{attributes:true,attributeFilter:["data-theme"]});'
        '})();</script>'
    )


def _org_card(o: dict) -> str:
    name = html.escape(o.get("name", ""))
    web = o.get("web", "").strip()
    title = (f'<a href="{html.escape(web)}" target="_blank" rel="noopener">{name}</a>' if web else name)
    area = o.get("area", "")
    badge_cls = {"chesterfield": "np-badge--ch", "regional": "np-badge--reg", "county-agency": "np-badge--gov"}.get(area, "")
    badge = (f'<span class="np-badge {badge_cls}">{html.escape(_area_label(area))}</span>' if area else "")
    contact = []
    phone = o.get("phone", "").strip()
    if phone:
        tel = "".join(ch for ch in phone if ch.isdigit())
        contact.append(f'<a href="tel:{tel}">{html.escape(phone)}</a>')
    if web:
        contact.append(f'<a href="{html.escape(web)}" target="_blank" rel="noopener">Website</a>')
    contact_line = (' &middot; '.join(contact)) if contact else ""
    addr = html.escape(o.get("address", "").strip())
    return (
        '<article class="np-card">'
        + f'<h3 class="np-card__title">{title}{badge}</h3>'
        + (f'<p class="np-card__desc">{html.escape(o.get("desc",""))}</p>' if o.get("desc") else "")
        + (f'<p class="np-card__addr">{addr}</p>' if addr else "")
        + (f'<p class="np-card__contact">{contact_line}</p>' if contact_line else "")
        + '</article>'
    )


def _list(orgs: list) -> str:
    groups = []
    for slug, label in CATEGORIES:
        members = [o for o in orgs if o.get("category") == slug]
        if not members:
            continue
        cards = "".join(_org_card(o) for o in members)
        groups.append(
            f'<section class="np-group" data-cat="{slug}">'
            f'<h2 class="np-group__h">{html.escape(label)}</h2>'
            f'<div class="np-grid">{cards}</div>'
            '</section>'
        )
    return '<div class="np-list">' + "".join(groups) + "</div>"


def _filter_js() -> str:
    return (
        '<script>(function(){var chips=document.querySelectorAll(".np-chip");'
        'var groups=document.querySelectorAll(".np-group");'
        'chips.forEach(function(c){c.addEventListener("click",function(){'
        'var cat=c.getAttribute("data-cat");'
        'chips.forEach(function(o){var on=o===c;o.classList.toggle("is-active",on);'
        'o.setAttribute("aria-pressed",on?"true":"false");});'
        'groups.forEach(function(g){g.style.display=(cat==="All"||g.getAttribute("data-cat")===cat)?"":"none";});'
        'if(window.__npSetCat)window.__npSetCat(cat);'
        'window.scrollTo({top:0,behavior:"smooth"});'
        '});});})();</script>'
    )


def _form() -> str:
    key = os.environ.get("WEB3FORMS_KEY", "").strip()
    notice = "" if key else (
        '<div class="form-notice">⚠️ This form isn\'t active yet — add a '
        'free Web3Forms key (WEB3FORMS_KEY in scripts/.deploy.env) and rebuild.</div>')
    return (
        notice
        + '<form class="site-form" action="https://api.web3forms.com/submit" method="POST">'
        f'<input type="hidden" name="access_key" value="{html.escape(key or "MISSING_WEB3FORMS_KEY")}">'
        '<input type="hidden" name="subject" value="Add or correct a nonprofit">'
        '<input type="hidden" name="from_name" value="Chesterfield Report Nonprofits">'
        '<input type="hidden" name="redirect" value="https://chesterfieldreport.com/nonprofits.html?ok=1">'
        '<input type="checkbox" name="botcheck" class="hp" tabindex="-1" autocomplete="off">'
        '<label>Organization name</label>'
        '<input type="text" name="Organization" required autocomplete="organization" '
        'placeholder="e.g. Chesterfield Food Bank Outreach Center">'
        '<label>What it does <span class="opt">(one line)</span></label>'
        '<input type="text" name="What it does" placeholder="e.g. Emergency food pantry serving the county">'
        '<label>Address <span class="opt">(so we can map it)</span></label>'
        '<input type="text" name="Address" placeholder="Street, city, ZIP (or P.O. box)">'
        '<label>Phone / website</label>'
        '<input type="text" name="Phone or website" placeholder="804-... and/or https://...">'
        '<label>What needs adding or correcting? <span class="opt">(optional)</span></label>'
        '<textarea name="Details" rows="4" placeholder="New listing, wrong phone, closed, '
        'category, a website to link..."></textarea>'
        '<label>Email <span class="opt">(optional, only if you want a reply; never published)</span></label>'
        '<input type="email" name="email" autocomplete="email">'
        '<label>Your name <span class="opt">(optional)</span></label>'
        '<input type="text" name="Name" autocomplete="name">'
        '<button type="submit" class="cr-btn cr-btn--primary" style="margin-top:1.3rem">'
        'Submit for review</button>'
        '</form>'
    )


_CSS = """<style>
.np-wrap{max-width:880px;margin:0 auto;}
.np-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:64ch;margin:.4rem 0 1.3rem;}
.np-chips{display:flex;flex-wrap:wrap;gap:.5rem;margin:0 0 1rem;}
.np-chip{display:inline-flex;align-items:center;gap:.4rem;cursor:pointer;
 font:var(--fw-semibold) var(--fs-2xs)/1 var(--font-sans);color:var(--text-secondary);
 background:var(--surface-card);border:1px solid var(--border);border-radius:999px;padding:.5rem .85rem;}
.np-chip:hover{border-color:var(--accent);color:var(--text-primary);}
.np-chip.is-active{background:var(--accent);border-color:var(--accent);color:#fff;}
.np-chip__n{font:var(--fw-bold) var(--fs-3xs) var(--font-mono);opacity:.85;}
.np-map{height:440px;border:1px solid var(--border);border-radius:var(--radius-sm);margin:0 0 .5rem;background:var(--surface-sunken,#eee);z-index:0;}
.np-map .leaflet-popup-content{font:var(--fs-2xs)/1.4 var(--font-sans);}
.np-map .leaflet-popup-content .np-pop-d{color:var(--text-tertiary);}
.np-count{font:var(--fw-semibold) var(--fs-2xs)/1.4 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);margin:0 0 1rem;}
.np-legend{display:flex;flex-wrap:wrap;gap:.5rem 1.1rem;margin:0 0 1.6rem;padding:.85rem 1rem;border:1px solid var(--border);border-radius:var(--radius-xs);background:var(--surface-card);}
.np-leg__item{display:inline-flex;align-items:center;gap:.45rem;font:var(--fs-3xs)/1.3 var(--font-sans);color:var(--text-secondary);}
.np-leg__dot{width:.85rem;height:.85rem;border-radius:50%;}
.np-leg__dot--solid{background:var(--accent);border:1.5px solid #fff;box-shadow:0 0 0 1px var(--border);}
.np-leg__dot--hollow{background:transparent;border:2px dashed var(--accent);}
.np-leg__dot--agency{background:#6b7280;border:1.5px solid #fff;box-shadow:0 0 0 1px var(--border);}
.np-list{margin:0;}
.np-group{margin:0 0 2rem;}
.np-group__h{font:var(--fw-bold) var(--fs-xl)/1.15 var(--font-display);margin:0 0 1rem;padding-bottom:.4rem;border-bottom:2px solid var(--border);}
.np-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:.9rem;}
.np-card{border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface-card);padding:.95rem 1.1rem;}
.np-card__title{font:var(--fw-bold) var(--fs-sm)/1.25 var(--font-display);margin:0 0 .4rem;}
.np-card__title a{color:var(--text-primary);text-decoration:none;}
.np-card__title a:hover{color:var(--accent);}
.np-badge{display:inline-block;font:var(--fw-bold) var(--fs-4xs,9px)/1 var(--font-mono);text-transform:uppercase;letter-spacing:.05em;border-radius:999px;padding:.25em .55em;margin-left:.5em;vertical-align:middle;}
.np-badge--ch{background:rgba(192,57,43,.12);color:var(--accent);}
.np-badge--reg{background:transparent;border:1px solid var(--border);color:var(--text-tertiary);}
.np-badge--gov{background:rgba(107,114,128,.16);color:var(--text-secondary);}
.np-card__desc{font:var(--fs-2xs)/1.5 var(--font-sans);color:var(--text-secondary);margin:0 0 .5rem;}
.np-card__addr{font:var(--fs-3xs)/1.4 var(--font-sans);color:var(--text-tertiary);margin:0 0 .35rem;}
.np-card__contact{font:var(--fw-semibold) var(--fs-3xs)/1.5 var(--font-sans);margin:0;}
.np-card__contact a{color:var(--accent);}
.np-sec{margin:2.6rem 0;}
.np-sec h2{font:var(--fw-bold) var(--fs-xl)/1.15 var(--font-display);margin:0 0 .3rem;}
.np-sec__dek{font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);margin:0 0 1.2rem;max-width:66ch;}
.np-fair{border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:var(--radius-sm);background:var(--surface-card);padding:1.1rem 1.25rem;margin:0 0 1.6rem;}
.np-fair p{font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);margin:0 0 .6rem;}
.np-fair p:last-child{margin-bottom:0;}
.np-formwrap{max-width:640px;}
.form-notice{background:rgba(255,210,63,.12);border:1px solid var(--accent);border-radius:8px;padding:.85rem 1.1rem;margin:0 0 1.3rem;color:var(--text-secondary);font:var(--fs-sm)/1.5 var(--font-sans);}
.site-form label{display:block;font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);text-transform:uppercase;letter-spacing:var(--ls-wide);color:var(--accent);margin:1.1rem 0 .35rem;}
.site-form .opt{color:var(--text-tertiary);font-weight:400;text-transform:none;letter-spacing:0;}
.site-form input[type=text],.site-form input[type=email],.site-form textarea{width:100%;font:inherit;padding:.65rem .75rem;background:var(--surface-card);color:var(--text-primary);border:1px solid var(--border);border-radius:6px;}
.site-form input:focus,.site-form textarea:focus{outline:none;border-color:var(--accent);}
.site-form textarea{resize:vertical;min-height:6rem;}
.site-form .hp{position:absolute;left:-9999px;}
.np-thanks{border:1px solid var(--accent);border-radius:10px;padding:1.1rem 1.3rem;background:var(--surface-card);}
.np-thanks h2{font:var(--fw-bold) var(--fs-xl) var(--font-display);color:var(--accent);margin:.2rem 0 .5rem;}
@media(max-width:620px){.np-map{height:360px;}}
</style>"""


def build_nonprofits() -> Path:
    orgs = _load()
    total = len(orgs)
    counts = Counter(o.get("category", "other") for o in orgs)
    mapped = sum(1 for o in orgs if o.get("lat") is not None and o.get("lon") is not None)

    lead = (
        f'A directory of {total} nonprofits, charities, and public agencies that serve '
        'Chesterfield County, from food pantries and free clinics to senior, youth, and '
        'crisis help. It is a curated, verified set, not every group in the county, so any '
        'organization can ask to be added or corrected below.'
    )
    thanks_js = (
        "<script>if(location.search.indexOf('ok=1')>-1){"
        "var f=document.querySelector('.site-form');"
        "if(f){f.outerHTML='<div class=\\\"np-thanks\\\"><h2>Thank you.</h2>'"
        "+'<p>Your submission is in. We review every one before it goes on the page. "
        "<a href=\\\"/nonprofits.html\\\">\\u2190 Back to the directory</a></p></div>';}}</script>")

    body = (
        _CSS
        + '<div class="np-wrap">'
        + '<h1 class="page-title">Local Nonprofits</h1>'
        + f'<p class="np-lead">{html.escape(lead)}</p>'
        + _filter_chips(counts, total)
        + _map_section(orgs)
        + _legend()
        + _list(orgs)
        + '<div class="np-sec"><h2>How this list is kept</h2>'
        + '<div class="np-fair">'
        + '<p>This directory is built on Chesterfield County’s own Human Services '
          'Non-Profit Collaborative plus well-established regional providers that serve '
          'county residents. It is not exhaustive: there are hundreds of registered '
          'nonprofits in and around Chesterfield, and this is a verified starting set.</p>'
        + f'<p>Of the {total} listed, {mapped} have a location on the map. Groups based in '
          'Chesterfield show as solid pins, regional groups that serve the county show as '
          'hollow pins, and county agencies are marked separately. If something is wrong, '
          'missing, or out of date, tell us and we will fix it. Any organization can be '
          'added or corrected.</p>'
        + '</div></div>'
        + '<div class="np-sec"><h2>Add or correct a nonprofit</h2>'
        + '<p class="np-sec__dek">Is your organization missing or listed incorrectly? Send it '
          'here and we will review and update the directory.</p>'
        + '<div class="np-formwrap">' + _form() + '</div>'
        + '</div>'
        + thanks_js
        + _filter_js()
        + '</div>'
    )

    page = render._shell(body)
    page = render._inject_og(
        page,
        "Local Nonprofits serving Chesterfield County: a directory and map",
        "A categorized, mappable directory of nonprofits and charities that serve "
        "Chesterfield County, Virginia: food, housing, health, seniors, youth, veterans, "
        "and crisis help. Organizations can ask to be added or corrected.",
        f"{render.SITE_URL}/nonprofits.html", og_type="website",
        page_title="Nonprofits Directory | The Chesterfield Report")
    out = PUBLIC / "nonprofits.html"
    out.write_text(page, encoding="utf-8")
    return out
