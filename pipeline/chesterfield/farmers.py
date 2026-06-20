"""Farmers Markets: a 'support local' directory of farmers markets in and
around Chesterfield County, on /farmers-markets.html.

Data is hand-curated from researched, sourced entries (county pages, market
sites, official social pages) rather than a live feed: markets are seasonal and
their schedules live in too many scattered places to scrape reliably. Each entry
carries a confidence note where details were aggregator-sourced; the page tells
readers to confirm day/time before they go.
"""
from __future__ import annotations

import html
import json
import shutil
import subprocess
import time
from pathlib import Path

from . import render

PUBLIC = render.PUBLIC
CACHE = render.ROOT / "pipeline" / "farmers_cache.json"   # gitignored AI summaries
MODEL = "claude-haiku-4-5"
CLI_TIMEOUT = 120
_SUM_SCHEMA = {"type": "object", "properties": {"summary": {"type": "string"}},
               "required": ["summary"]}

# Curated market list. `verify` flags entries whose hours/season were not
# confirmed from an official source (shown with a soft "confirm ahead" note).
MARKETS = [
    {
        "name": "The Best of Virginia Farmers Market at RounTrey",
        "featured": True,
        "chesterfield": True,
        "address": "3800 Graythorne Drive, Midlothian, VA 23112",
        "schedule": "Last Friday of every month",
        "hours": "3:00 – 8:00 PM",
        "season": "Grand opening Friday, July 31, 2026",
        "offers": "Fresh produce, artisan goods, flowers and plants, baked goods, live music; family-friendly",
        "website": "", "facebook": "", "instagram": "",
        "qr": [
            {"label": "Facebook", "img": "/assets/rountrey-facebook-qr.png"},
            {"label": "Instagram", "img": "/assets/rountrey-instagram-qr.png"},
        ],
        "description": "A new monthly evening market in the RounTrey community of Midlothian, "
                       "pairing local produce and artisan makers with live music. Its grand opening is "
                       "Friday, July 31, 2026.",
        "verify": False,
    },
    {
        "name": "Chesterfield County Farmers Market",
        "chesterfield": True,
        "address": "6701 Mimms Loop, Chesterfield, VA 23832 (County Government Complex)",
        "schedule": "Wednesdays",
        "hours": "11:00 AM – 2:00 PM",
        "season": "May 6 – September 30, 2026",
        "offers": "Locally grown produce, eggs, cheese, poultry and seafood, baked goods, pickles, "
                  "salsa, kombucha and juices, plants; food trucks on site",
        "website": "https://www.chesterfield.gov/1100/Farmers-Market",
        "facebook": "https://www.facebook.com/ChesterfieldVAFarmersMarket", "instagram": "",
        "description": "The county's official midweek market at the Government Complex brings local "
                       "growers, artisans, and food trucks together every Wednesday from May through September.",
        "verify": False,
    },
    {
        "name": "Latino Farmers Market",
        "chesterfield": True,
        "address": "13900 Hull Street Road, Midlothian, VA 23112 (Chesterfield Technical Center)",
        "schedule": "Saturdays",
        "hours": "8:00 AM – 1:00 PM",
        "season": "April 4 – October 31, 2026",
        "offers": "Local food, unique vendor finds, culture and community",
        "website": "https://www.latinofarmersmarketva.com/", "facebook": "", "instagram": "",
        "description": "A Saturday market at the Chesterfield Technical Center on Hull Street, "
                       "celebrating Latino culture, flavor, and community alongside local food and finds.",
        "verify": False,
    },
    {
        "name": "Bon Air Farmers Market",
        "chesterfield": True,
        "address": "2040 McRae Road, North Chesterfield, VA 23235 (St. Michael's Episcopal Church)",
        "schedule": "Thursdays (summer) · Saturdays (winter)",
        "hours": "Apr–Oct: Thu 4:00–7:00 PM · Nov–Mar: Sat 10:00 AM–1:00 PM",
        "season": "Year-round",
        "offers": "Local produce, food trucks, live music; rain or shine",
        "website": "", "facebook": "https://www.facebook.com/p/Bon-Air-Farmers-Market-100075685608361/",
        "instagram": "",
        "description": "A year-round community market in the churchyard at St. Michael's, with local "
                       "produce, food trucks, and live music. Thursday evenings in summer, Saturday "
                       "mornings in winter.",
        "verify": False,
    },
    {
        "name": "Brandermill Green Market",
        "chesterfield": True,
        "address": "4900 Market Square Lane, Midlothian, VA 23112",
        "schedule": "Saturdays",
        "hours": "9:00 AM – 12:00 PM",
        "season": "First Saturday in May through last Saturday in October",
        "offers": "Local produce and neighborhood vendors",
        "website": "https://www.brandermill.com/", "facebook": "https://www.facebook.com/brandermillmarketsquare/",
        "instagram": "",
        "description": "A neighborhood Saturday market at Brandermill's Market Square offering local "
                       "produce and vendor goods through the warm-weather season.",
        "verify": False,
    },
    {
        "name": "Woodlake Maker's Market",
        "chesterfield": True,
        "address": "14710 Village Square Place, Midlothian, VA 23112",
        "schedule": "Tuesdays",
        "hours": "10:00 AM – 2:00 PM",
        "season": "Tuesdays, April 7 – July 7, 2026 (no market May 26)",
        "offers": "Handmade art, jewelry and home goods, artisanal and baked foods, local coffee, "
                  "plus a fresh-produce vendor",
        "website": "https://woodlakeva.org/events/", "facebook": "", "instagram": "",
        "description": "A Tuesday makers' market in the Woodlake community blending handmade goods and "
                       "artisanal food with fresh produce from a local farmer.",
        "verify": False,
    },
    {
        "name": "Chesterfield Berry Farm & Market",
        "chesterfield": True,
        "address": "26002 Pear Orchard Road, Moseley, VA 23120",
        "schedule": "Seasonal farm market",
        "hours": "",
        "season": "Berry season through fall agritourism",
        "offers": "Farm-fresh berries and produce, pick-your-own, farm goods; fall festival in season",
        "website": "https://chesterfieldberryfarm.com/", "facebook": "", "instagram": "",
        "description": "A working farm and market in Moseley with fresh berries, pick-your-own, and farm "
                       "goods, plus seasonal agritourism in the fall.",
        "verify": True,
    },
    {
        "name": "South of the James Market",
        "chesterfield": False,
        "address": "Forest Hill Park, Richmond, VA 23225",
        "schedule": "Sundays",
        "hours": "10:00 AM – 1:00 PM",
        "season": "Year-round (largest May–October)",
        "offers": "Dozens of farmers and artisan makers; one of the region's biggest markets",
        "website": "https://www.growrva.com/sojmarket", "facebook": "https://www.facebook.com/SOJmarket/",
        "instagram": "",
        "description": "One of Richmond's largest and most popular markets, in Forest Hill Park just "
                       "across the river from North Chesterfield.",
        "verify": False,
    },
    {
        "name": "RVA Big Market",
        "chesterfield": False,
        "address": "4308 Hermitage Road (Joseph Bryan Park), Richmond, VA 23227",
        "schedule": "Saturdays",
        "hours": "8:00 AM – 12:00 PM (May–Oct) · 9:00 AM – 12:00 PM (Nov–Apr)",
        "season": "Year-round",
        "offers": "Local produce, artisan makers, and food vendors; the sister market to South of the James",
        "website": "https://www.growrva.com/rvabigmkt",
        "facebook": "https://www.facebook.com/RVABIGMKT/", "instagram": "",
        "description": "GrowRVA's sister market to South of the James, held Saturdays at Joseph Bryan "
                       "Park with local farmers, makers, and food vendors.",
        "verify": False,
    },
    {
        "name": "Lakeside Farmers' Market",
        "chesterfield": False,
        "address": "6110 Lakeside Avenue, Henrico, VA 23228",
        "schedule": "Wednesdays & Saturdays",
        "hours": "Wed 9:00 AM–1:00 PM · Sat 9:00 AM–3:00 PM",
        "season": "Year-round",
        "offers": "Produce, bedding plants, local farm and vendor goods",
        "website": "http://www.lakesidefarmersmarket.net/", "facebook": "https://www.facebook.com/LakesideMarketRVA/",
        "instagram": "https://www.instagram.com/lakesidefarmersmarketrva/",
        "description": "A long-running year-round market in Henrico's Lakeside neighborhood, known for "
                       "fresh produce and bedding plants.",
        "verify": False,
    },
    {
        "name": "Birdhouse Farmers Market",
        "chesterfield": False,
        "address": "1507 Grayland Avenue, Richmond, VA 23220",
        "schedule": "Tuesdays",
        "hours": "3:00 – 6:30 PM",
        "season": "In person May – November",
        "offers": "Local produce, food, and artisan goods; community nonprofit market",
        "website": "https://birdhousefarmersmarket.org/", "facebook": "https://www.facebook.com/birdhousemarket/",
        "instagram": "https://www.instagram.com/birdhousefarmersmarket/",
        "description": "A community-focused Tuesday market in Richmond's Randolph neighborhood, with a "
                       "strong local-food-access mission. Winter (December to April) is online-only with "
                       "Tuesday curbside pickup.",
        "verify": False,
    },
]


def _esc(s) -> str:
    return html.escape(str(s or "").strip())


# --- AI "what you'll find" summaries (goods, not named vendors) ------------

def _cli_available() -> bool:
    return shutil.which("claude") is not None


def _load_cache() -> dict:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_cache(cache: dict) -> None:
    try:
        CACHE.write_text(json.dumps(cache, indent=0), encoding="utf-8")
    except OSError:
        pass


def _clean(s):
    if not isinstance(s, str):
        return s
    for cut in ("</", "<parameter", "<function", "<antml", "```"):
        j = s.find(cut)
        if j != -1:
            s = s[:j]
    return s.strip()


def _summarize(m: dict, model: str = MODEL) -> str:
    """Generate a short, factual, human-sounding 'what you'll find' summary,
    grounded strictly in the market's known offerings. No invented vendors."""
    if not _cli_available():
        return ""
    prompt = (
        "You are writing a short listing for a farmers market, for a Chesterfield County, "
        "Virginia community news site. Write two sentences telling a reader what they will find "
        "at this market.\n\n"
        f"Market: {m.get('name','')}\n"
        f"Location: {m.get('address','')}\n"
        f"When: {m.get('schedule','')}, {m.get('hours','')}\n"
        f"Known offerings: {m.get('offers','')}\n"
        f"Context: {m.get('description','')}\n\n"
        "RULES:\n"
        "- Base it ONLY on the offerings and context above. Do NOT invent vendor names, farm "
        "names, specific products, prices, or any detail not implied by the offerings.\n"
        "- Describe the TYPES of goods and the character of the market, not named vendors.\n"
        "- Sound warm and natural, the way a real local person would write it. Be specific to "
        "this market, not generic.\n"
        "- Exactly two sentences, roughly 30 to 45 words.\n"
        "BANNED, because it reads as AI filler: NO em dashes or en dashes (use commas and "
        "periods only). No exclamation points. No marketing hype. Do not use words and phrases "
        "like nestled, vibrant, bustling, hidden gem, in the heart of, whether you are, look no "
        "further, something for everyone, tapestry, feast for the senses, a wide array, "
        "elevate, curated, or rain or shine. Plain, concrete, friendly English only.\n"
        "Return just the summary."
    )
    cmd = ["claude", "-p", prompt, "--output-format", "json",
           "--json-schema", json.dumps(_SUM_SCHEMA), "--model", model]
    for attempt in range(2):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=CLI_TIMEOUT)
            if proc.returncode != 0:
                if attempt == 0:
                    time.sleep(4)
                    continue
                return ""
            data = json.loads(proc.stdout).get("structured_output") or {}
            return _clean(data.get("summary", "")) or ""
        except Exception:                            # noqa: BLE001
            if attempt == 0:
                time.sleep(4)
                continue
            return ""
    return ""


def _enrich(markets: list) -> None:
    """Fill m['ai_summary'] from cache, generating any that are missing."""
    cache = _load_cache()
    changed = False
    for m in markets:
        key = m.get("name", "")
        if key and not cache.get(key):
            s = _summarize(m)
            if s:
                cache[key] = s
                changed = True
        m["ai_summary"] = cache.get(key, "")
    if changed:
        _save_cache(cache)


def _maps_link(address: str) -> str:
    import urllib.parse
    q = urllib.parse.quote_plus(address)
    return f"https://www.google.com/maps/search/?api=1&query={q}"


def _links(m: dict) -> str:
    out = []
    if m.get("website"):
        out.append(f'<a href="{_esc(m["website"])}" target="_blank" rel="noopener">Website</a>')
    if m.get("facebook"):
        out.append(f'<a href="{_esc(m["facebook"])}" target="_blank" rel="noopener">Facebook</a>')
    if m.get("instagram"):
        out.append(f'<a href="{_esc(m["instagram"])}" target="_blank" rel="noopener">Instagram</a>')
    out.append(f'<a href="{_maps_link(m["address"])}" target="_blank" rel="noopener">Map</a>')
    return '<div class="fm-links">' + " &middot; ".join(out) + '</div>'


def _card(m: dict) -> str:
    featured = m.get("featured")
    badge = ('<span class="fm-badge fm-new">Grand opening July 31</span>'
             if featured else "")
    when_bits = [b for b in (m.get("schedule"), m.get("hours")) if b]
    when = " &middot; ".join(_esc(b) for b in when_bits)
    season = f'<div class="fm-season">{_esc(m["season"])}</div>' if m.get("season") else ""
    confirm = ('<div class="fm-confirm">Days and hours can change with the season, so confirm before you go.</div>'
               if m.get("verify") else "")
    qr = ""
    if m.get("qr"):
        codes = "".join(
            f'<figure class="fm-qr"><img src="{_esc(q["img"])}" alt="{_esc(q["label"])} QR code" '
            f'width="92" height="92" loading="lazy"><figcaption>{_esc(q["label"])}</figcaption></figure>'
            for q in m["qr"])
        qr = ('<div class="fm-qrs"><span class="fm-qr-lbl">No website yet. Scan to follow:</span>'
              f'<div class="fm-qr-row">{codes}</div></div>')
    rows = [
        f'<div class="fm-when">{when}</div>' if when else "",
        season,
        f'<p class="fm-desc">{render._inline(_esc(m.get("ai_summary") or m.get("description")))}</p>'
        if (m.get("ai_summary") or m.get("description")) else "",
        f'<div class="fm-offers">{_esc(m["offers"])}</div>' if m.get("offers") else "",
        f'<div class="fm-addr">{_esc(m["address"])}</div>' if m.get("address") else "",
        _links(m),
        qr,
        confirm,
    ]
    return (
        f'<article class="fm-card{" fm-card--feat" if featured else ""}">'
        f'<div class="fm-top"><h3>{_esc(m["name"])}</h3>{badge}</div>'
        + "".join(r for r in rows if r)
        + '</article>'
    )


_FM_CSS = """<style>
.fm-wrap{max-width:860px;margin:0 auto;}
.fm-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:62ch;margin:.4rem 0 1.4rem;}
.fm-sech{font:var(--fw-bold) var(--fs-2xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--accent);border-top:1px solid var(--border);padding-top:.8rem;margin:2rem 0 1rem;}
.fm-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;}
.fm-card{border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface-card);padding:1.1rem 1.2rem;display:flex;flex-direction:column;gap:.45rem;}
.fm-card--feat{grid-column:1/-1;border-left:4px solid var(--accent);background:var(--surface-sunken,rgba(154,50,34,.04));}
.fm-top{display:flex;align-items:baseline;gap:.6rem;flex-wrap:wrap;}
.fm-card h3{font:var(--fw-bold) var(--fs-lg)/1.2 var(--font-display);margin:0;color:var(--text-primary);}
.fm-card--feat h3{font-size:var(--fs-xl);}
.fm-badge{font:var(--fw-bold) var(--fs-3xs) var(--font-mono);text-transform:uppercase;letter-spacing:var(--ls-wide);padding:2px 7px;border-radius:3px;}
.fm-new{background:var(--accent);color:#fff;}
.fm-when{font:var(--fw-bold) var(--fs-sm) var(--font-sans);color:var(--text-primary);}
.fm-season{font:var(--fs-2xs) var(--font-mono);color:var(--text-tertiary);text-transform:uppercase;letter-spacing:var(--ls-wide);}
.fm-desc{font:var(--fs-sm)/1.55 var(--font-sans);color:var(--text-secondary);margin:.2rem 0;}
.fm-offers{font:var(--fs-2xs)/1.45 var(--font-sans);color:var(--text-tertiary);}
.fm-addr{font:var(--fs-2xs) var(--font-sans);color:var(--text-secondary);}
.fm-links{font:var(--fw-semibold) var(--fs-2xs) var(--font-sans);margin-top:.2rem;}
.fm-links a{color:var(--accent);}
.fm-confirm{font:var(--fs-3xs)/1.4 var(--font-sans);color:var(--text-tertiary);font-style:italic;margin-top:.2rem;}
.fm-qrs{margin-top:.5rem;}
.fm-qr-lbl{display:block;font:var(--fw-semibold) var(--fs-3xs) var(--font-mono);text-transform:uppercase;letter-spacing:var(--ls-wide);color:var(--text-tertiary);margin-bottom:.4rem;}
.fm-qr-row{display:flex;gap:1rem;}
.fm-qr{margin:0;text-align:center;}
.fm-qr img{display:block;border:1px solid var(--border);border-radius:4px;background:#fff;}
.fm-qr figcaption{font:var(--fw-semibold) var(--fs-3xs) var(--font-sans);color:var(--text-secondary);margin-top:.2rem;}
.fm-note{margin-top:2rem;padding:1rem 1.1rem;border-left:3px solid var(--accent);background:var(--surface-card);border-radius:var(--radius-xs);font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);}
</style>"""


def build_farmers() -> Path:
    """Render /farmers-markets.html."""
    _enrich(MARKETS)   # fill m['ai_summary'] (cached; generates any missing)
    ches = [m for m in MARKETS if m.get("chesterfield")]
    # Featured first, then the rest in listed order.
    ches.sort(key=lambda m: (not m.get("featured"),))
    regional = [m for m in MARKETS if not m.get("chesterfield")]

    body = (
        _FM_CSS
        + '<div class="fm-wrap">'
        + '<h1 class="page-title">Farmers Markets</h1>'
        + '<p class="fm-lead">Shop local, eat local, support local. Here are the farmers markets in '
          'Chesterfield County, plus a few favorites just across the line in the Richmond area. Fresh '
          'produce, artisan goods, baked treats, and live music from the people who live and grow here.</p>'
        + '<div class="fm-sech">In Chesterfield County</div>'
        + '<div class="fm-grid">' + "".join(_card(m) for m in ches) + '</div>'
        + '<div class="fm-sech">Nearby in the Richmond Area</div>'
        + '<div class="fm-grid">' + "".join(_card(m) for m in regional) + '</div>'
        + '<div class="fm-note">Hungry for a food truck? Chesterfield\'s food-truck scene lives on '
          'social media more than any one calendar, but '
          '<a href="https://streetfoodfinder.com/c/va/chesterfield" target="_blank" rel="noopener">'
          'StreetFoodFinder\'s Chesterfield page</a> is the best place to see who is parked where this '
          'week. Several of the markets above host food trucks on site, too.</div>'
        + '<div class="fm-note">Markets are seasonal and schedules shift, so always confirm the day and '
          'time before you head out. Run a market we missed, or see something that needs updating? '
          '<a href="/tip.html">Let us know</a> and we will add or fix it.</div>'
        + '</div>'
    )
    page = render._shell(body, len(MARKETS))
    page = render._inject_og(
        page, "Farmers Markets in Chesterfield County",
        "A guide to farmers markets in Chesterfield County and the Richmond area: days, hours, "
        "locations, and what each one offers. Shop local.",
        f"{render.SITE_URL}/farmers-markets.html", og_type="website")
    out = PUBLIC / "farmers-markets.html"
    out.write_text(page, encoding="utf-8")
    return out
