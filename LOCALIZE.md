# LOCALIZE.md — Spin this up for your own town, city, or county

> **You are an AI coding agent (e.g. Claude Code) re-localizing this hyperlocal
> news system for a new place.** Read this whole file first, then work through
> the steps in order. Stop and ask the human at every line that says **ASK THE
> HUMAN**. Do not invent facts (feed URLs, API endpoints, zone codes); verify
> each one before you write it.

This project is "The Chesterfield Report," a hands-off hyperlocal news site for
Chesterfield County, Virginia. It ingests local sources every few hours, uses an
LLM to decide what is news and write plain-language summaries, builds a static
site, and deploys it. Your job is to turn it into the same thing for a different
place without breaking it.

---

## 0. Get the basics from the human (ASK THE HUMAN)

Before changing anything, collect:

- **Place**: name + type (county / city / town) + state. (e.g. "Travis County, Texas")
- **Short name** for the brand (e.g. "The Travis Report") and tagline.
- **Domain** they will use (or "decide later").
- **Time zone** (e.g. America/Chicago).
- **Their email** for tips/letters.
- **Neighborhoods / towns / regions** inside the locality (for the masthead ticker).
- Whether they already have: a Vercel account, a Web3Forms key, Claude Code installed.

Write these down. You will reuse them throughout.

---

## 1. Understand what transfers and what does not

This is the most important section. The site has grown well beyond the core news
feed — there are many feature pages now, and they transfer very differently. Sort
every feature into one of four buckets.

**A. Universal (works anywhere, just needs the new name).**
The core article pipeline (ingest -> triage -> QA -> enrich -> render -> deploy),
Google News sources, the **dining guide + map** (OpenStreetMap Overpass works for
any place name), the **weekly newsletter** (`weekly.py` -> `/newsletter/`, plus the
email-safe `newsletter.py`), the **Spanish edition** (`/es/`), RSS feed,
SEO/sitemap/Open Graph, the tip and opinion forms, light/dark theme, and the whole
design system.

**B. Locality data (must be edited — config-level).**
Brand/name, domain, geographic bounding box, map center, NWS weather zone, time
zone, editorial focus areas, contact email, and the masthead region list.

**C. Hand-curated data pages (REBUILD the dataset or DROP the page).**
These pages render from committed, human-researched data files, not a live feed.
The code is reusable but the data is 100% Chesterfield-specific. For each one you
keep, **research and rewrite the data for the new locality** (this is real work,
often best done with a research subagent); for each you drop, remove it cleanly
(see step 5). Do NOT ship these with Chesterfield data.

| Page | Module + data | What to do |
|---|---|---|
| **Schools** (`/schools.html`) | `schools.py` + `pipeline/schools_data.json` | Rebuild with the new district's schools (names, grades, contacts, coords) or drop. |
| **School Board** (`/school-board.html`) | `school_board.py` | Rebuild with local board members / campaign-finance data or drop. |
| **Taxes / budget** (`/taxes.html`) | `taxes.py` + `pipeline/budget_data.json` | Rebuild with the locality's budget figures or drop. |
| **Housing** (`/apartments.html`, `/affordable-housing.html`) | `housing.py` + `pipeline/apartments_data.json` + `pipeline/affordable_housing.json` | Rebuild the community directory + income-restricted list or drop. |
| **Farmers Markets** (`/farmers-markets.html`) | `farmers.py` (`MARKETS` list inline) | Rewrite the market list for the new area or drop. |
| **Board of Supervisors** (`/board.html`) | `board.py` (named supervisors, donor tables) | Rebuild for the local governing body or drop. |
| **Shoosmith investigation** (`/shoosmith.html`) | `render.build_shoosmith()` | Chesterfield-only investigative page — **drop it** (and the nav "Investigations" item) unless you have your own investigation. |

**D. Vendor-tech-dependent (AUDIT, then adapt or DISABLE).**
These rely on live APIs/vendors that Chesterfield happens to use. Other places use
a different vendor, or none. **If you cannot find a working equivalent, disable the
feature. A missing feature is fine; a broken one is not.**

| Feature | What it depends on | What to do |
|---|---|---|
| **Live dispatch ticker** (top marquee: active police/fire calls) | Chesterfield's CivicEngage "active calls" JSON at `api.chesterfield.gov` | Most localities have no live CAD feed. If not, **remove the ticker script**; the static region ticker remains. |
| **County meetings** (`/meetings.html`) | `meetings.py` — CivicClerk OData API, tenant `chesterfieldcova` | Find the locality's agenda system (CivicClerk, Legistar, Granicus, PrimeGov, or none). Re-point or **disable**. |
| **Events calendar** (`/events.html`) | `events.py` — the county CivicPlus iCal feed + AI enrichment | Re-point to the locality's public iCal/calendar feed, or disable. Events with no description are auto-dropped. |
| **Development & Zoning cases** (`/development.html`) | `cases.py` + `laserfiche.py` — Chesterfield's ArcGIS + Laserfiche portals | Very Chesterfield-specific. Adapt to the locality's GIS/permit portal or **drop**. |
| **Things to Do** (`/things-to-do.html`) | `things.py` — Ticketmaster Discovery API | Works for any US locality: set `TICKETMASTER_API_KEY` in `.deploy.env` and re-center `LATLONG`/`RADIUS_MI` in `things.py`. No key -> the page falls back to cache/empty; drop it if you do not want it. |
| **Regional track** (`/virginia.html`) | regional sources in `sources.py` + the editor's regional judgment | Re-point to the new STATE's news (rename the page, swap the state feeds, update the "affects residents" prompt in `editor.py`). |
| **Restaurant inspections** lookup (on `/dining.html`) | Virginia "My Health Department" portal | Update the link to the locality's health-inspection portal, or remove the callout. |

Tell the human which Bucket C and D features you are keeping, adapting, or
dropping, **before** you build.

---

## 2. Mechanical re-brand (Bucket B)

Search the repo for these and replace with the new locality. Do NOT blind
find-and-replace; review each hit (some are structural).

- **Place name**: "Chesterfield County" / "Chesterfield" -> the new place. Appears
  in `pipeline/chesterfield/render.py` (site name, tagline, masthead, footer,
  About page), `sources.py`, `seo.py`, `meetings.py`, `dining.py`, `board.py`.
- **Domain**: `chesterfieldreport.com` -> the new domain. In `render.py`
  (`SITE_URL`, Open Graph URLs, canonical, form redirects) and `seo.py`.
- **Brand assets**: site name string, tagline, and the **logo** (`public/assets/`
  has SVG logo marks + `favicon.svg` + `og-default.png`). Regenerate the share
  card `og-default.png` and swap the logo if the human provides one.
- **Time zone**: `render._updated_stamp()` hardcodes `America/New_York`. Change it.
- **Email**: tip/letter destination in `letters.py` and the tip form.
- **Masthead region ticker**: the neighborhood list in `render.py` `_TEMPLATE`.
- **Editorial focus areas**: `pipeline/chesterfield/sources.py` `FOCUS_AREAS` (the
  beats: growth, schools, police, fire, business, government, community, weather).
  Adjust if the locality cares about different things.
- **Package path**: the code lives in `pipeline/chesterfield/`. You can leave the
  folder name as-is (it is just a Python package name) or rename it and update
  imports. Renaming is optional and noisy; leaving it is fine.

---

## 3. Geography

- **Bounding box**: `geo.py` and `maps.py` both define `_BBOX = (lat_min, lat_max,
  lon_min, lon_max)`. Set it to the new locality's bounds (look up the place on
  OpenStreetMap and read the bbox, or ask the human). This filter rejects
  out-of-area geocodes, which is what stops "a Chesterfield in another state"
  bugs. Get it right.
- **Map center/zoom**: `maps.py` (news map) and `dining.py` (`_MAP_JS` setView)
  center on Chesterfield. Re-center on the new locality.
- **Dining Overpass query**: `dining.py` `_QUERY` uses
  `area["name"="Chesterfield County"]["admin_level"="6"]`. Change the area name
  and, if the place is a city/town, the `admin_level` (6 = county, 8 = city/town
  in the US). Verify the query returns results before trusting it.
- **Geocoder user-agent**: `geo.py` `USER_AGENT` has an email; update it.

---

## 4. Sources (Bucket A + research)

Edit `pipeline/chesterfield/sources.py`. This is where most of the value is.

- **Google News beats** (the biggest, most portable win): every `gnews-*` source
  is just a Google News RSS search URL with a place/topic query. Swap the place
  names (`Chesterfield`, `Midlothian`, `Hull Street Road`, etc.) for the new
  locality's name, neighborhoods, and major roads. These work anywhere with no
  API key. `geo_filter: True` keeps them on-topic.
- **Official local feeds (RESEARCH, verify each)**: Chesterfield publishes RSS
  from a CivicEngage/CivicPlus site (county news, police, fire, planning,
  transportation). Find the new locality's government site and its RSS feeds.
  Many city/county sites on CivicPlus, Granicus, or similar expose RSS at
  predictable paths. **Fetch each candidate URL and confirm it returns real,
  recent items before adding it.** Drop any that 404 or are empty.
- **NWS weather alerts**: the source uses a Virginia zone code (`VAC041`). Look up
  the new locality's NWS zone at weather.gov and replace it.
- **Local outlets + YouTube + Reddit**: replace the Richmond-area outlets, the
  county YouTube channel IDs, and the `r/ChesterfieldVA` subreddit with the new
  locality's equivalents, where they exist. Verify each feed.

After editing, run an ingest (see step 8) and confirm real local items come in.

---

## 5. Bucket C features (audit + adapt or remove)

For each feature in the section-1 table you decided to KEEP, do the work; for each
you decided to DROP, remove it cleanly (the code path AND the nav link in
`render.py` `_TEMPLATE` AND the `cmd_build` call in `pipeline/run.py` AND the
sitemap entry in `seo.py`). Leaving a dead nav link is worse than no feature.

- **Live dispatch ticker**: it is a `<script>` block in `render.py` `_TEMPLATE`
  (search "ACTIVE CALLS"). If the locality has no live CAD feed, delete that
  script; the static region ticker remains.
- **Meetings**: `meetings.py`. Re-point the CivicClerk tenant or swap the API.
- **Inspections**: the callout in `dining.py` (`INSPECTIONS_URL`).
- **Board**: `board.py` is heavily Chesterfield-specific (named supervisors, donor
  tables). Rebuild or remove.

---

## 6. AI backend

The pipeline shells out to the **Claude Code CLI** (`claude -p ... --json-schema`)
for triage, QA, and article writing, so it needs no API key. The human must have
Claude Code installed and authenticated. If they prefer the Anthropic API instead,
`enrich.py` supports an API backend via `ANTHROPIC_API_KEY`. Confirm which.

---

## 7. Forms (ASK THE HUMAN)

The tip and opinion forms post to **Web3Forms** (free, no backend). The human
needs their own key from web3forms.com (30 seconds). Put it in
`scripts/.deploy.env` as `WEB3FORMS_KEY=...`. The build bakes it into the form
pages, so it must be sourced at build time (the cron does `set -a; source
scripts/.deploy.env; set +a`).

---

## 8. Build and review locally

- Build with a Python that has a working `pyexpat` (XML). On the original Mac,
  system `/usr/bin/python3` works; a Homebrew 3.14 had broken pyexpat. Use
  whatever Python parses XML.
- From `pipeline/`: `python3 run.py ingest` then `triage`, `qa`, `expire`
  (auto-unpublishes stale weather alerts), then `build`. The cron runs this whole
  chain; `build` regenerates every feature page.
- Open `public/index.html` and click around. **Click every nav item** (the nav has
  dropdowns now: News, Community, Government, plus the Supervisors/Schools/Meetings
  pillars) and confirm no page still shows Chesterfield data or 404s.
- Fix anything locality-specific you missed (stray "Chesterfield" text, dead links,
  empty feature pages, hand-curated pages still showing Chesterfield data).
- Confirm the geo bbox is right (no out-of-area map pins) and sources produce
  real local stories.

---

## 9. Deploy (ASK THE HUMAN — this is the Vercel step)

The site is static and deploys to **Vercel**. Each operator uses their own free
Vercel account.

**STOP and prompt the human to do this once, then continue:**
1. Make a free account at vercel.com.
2. Create a project (or just deploy the `public/` directory with the CLI).
3. Create a token at vercel.com/account/tokens and give it to you.
4. Put it in `scripts/.deploy.env` as `VERCEL_TOKEN=...` and set
   `VERCEL_SCOPE=<their-team-slug>`.
5. If they have a domain, they add it in the Vercel dashboard and point DNS.

Then deploy: `npx vercel deploy public --prod --yes --token "$VERCEL_TOKEN"
--scope "$VERCEL_SCOPE"`. (`scripts/deploy.sh` wraps this.)

> Never commit `scripts/.deploy.env`. It is gitignored. The Vercel token is a
> secret.

---

## 10. Schedule it (make it autonomous)

`scripts/ingest-cron.sh` runs the full pipeline (ingest -> triage -> qa -> build
-> deploy). Schedule it however the human wants it to run:
- **A Linux server / VPS**: a cron entry (e.g. `0 */2 * * *` for every 2 hours).
- **A always-on Mac**: a launchd agent.
- **No server**: a GitHub Actions workflow on a schedule (it needs the Claude
  credentials and the Vercel token as encrypted secrets).

The cron only deploys when `VERCEL_TOKEN` is set, so it is safe to schedule before
the human finishes the Vercel step.

---

## Locality data quick-reference (files to touch)

- `pipeline/chesterfield/render.py` — name, tagline, domain/`SITE_URL`, masthead
  regions, footer, About page, time zone, the live-dispatch ticker script, OG tags.
- `pipeline/chesterfield/sources.py` — `FOCUS_AREAS` + every source feed.
- `pipeline/chesterfield/geo.py` — `_BBOX`, user-agent email.
- `pipeline/chesterfield/maps.py` — `_BBOX`, map center.
- `pipeline/chesterfield/dining.py` — Overpass area, map center, inspections link.
- `pipeline/chesterfield/meetings.py` — CivicClerk tenant + body names.
- `pipeline/chesterfield/events.py` — county iCal calendar URL, map center.
- `pipeline/chesterfield/things.py` — `LATLONG`, `RADIUS_MI`, Chesterfield place list (Things to Do).
- `pipeline/chesterfield/cases.py` + `laserfiche.py` — county GIS/permit portals (Development).
- `pipeline/chesterfield/board.py` — local governing body (or remove).
- `pipeline/chesterfield/school_board.py` — local school board (or remove).
- `pipeline/chesterfield/farmers.py` — the `MARKETS` list (or remove).
- Hand-curated datasets (rebuild for the locality or drop the page): `pipeline/schools_data.json`,
  `pipeline/budget_data.json`, `pipeline/apartments_data.json`, `pipeline/affordable_housing.json`.
- `pipeline/chesterfield/seo.py` — `SITE_URL`, static page list.
- `pipeline/chesterfield/letters.py` + tip form — destination email.
- `pipeline/run.py` — `cmd_build` calls every `build_*` (drop the call for any page you remove).
- `public/assets/` — logo SVGs, favicon, `og-default.png`, `report-ds.css` (brand
  colors live in the `:root` tokens at the top).
- `scripts/.deploy.env` — `VERCEL_TOKEN`, `VERCEL_SCOPE`, `WEB3FORMS_KEY`, and
  (optional) `TICKETMASTER_API_KEY` for Things to Do — all secrets, gitignored.

When you ADD a feature page, wire it in all four places or it half-exists: the
`build_*` call in `pipeline/run.py`, the nav link(s) in `render.py` `_TEMPLATE`
(desktop dropdown + mobile + footer), and the page name in `seo.py`'s sitemap list.

## Definition of done

A first-time visitor sees a clean local news site with the right name, real local
stories, a working map inside the correct area, no stray "Chesterfield" text, no
dead nav links, and no broken feature pages. It rebuilds and redeploys on a
schedule without a human in the loop.
