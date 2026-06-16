"""Source registry + focus-area definitions for the Chesterfield blog.

This is the one file you'll edit most often: add a source here and the
pipeline picks it up automatically. Keeping it as plain Python (not YAML)
means zero parsing dependencies and lets keyword lists live beside the
sources they describe.
"""

# --- Focus areas -----------------------------------------------------------
# These are the editorial buckets the user cares about. Each item the
# pipeline ingests gets tagged with zero or more of these, first from its
# source's default tags, then refined by keyword match (and the LLM step).
#
# key -> (human label, keyword triggers used for classification)
FOCUS_AREAS = {
    "growth": (
        "Growth & Development",
        ["development", "rezoning", "rezone", "construction", "groundbreaking",
         "project", "planning commission", "subdivision", "mixed-use", "site plan",
         "comprehensive plan", "permit", "expansion", "investment", "jobs"],
    ),
    "schools": (
        "Schools",
        ["school", "ccps", "student", "teacher", "education", "classroom",
         "graduation", "school board"],
    ),
    "police": (
        "Police",
        ["police", "arrest", "crime", "investigation", "officer", "suspect",
         "shooting", "robbery", "theft"],
    ),
    "fire": (
        "Fire & EMS",
        ["fire", "ems", "rescue", "paramedic", "firefighter", "blaze", "hazmat"],
    ),
    "business": (
        "Local Business",
        ["business", "store", "restaurant", "opening", "shop", "retail",
         "grand opening", "small business", "employer", "hiring"],
    ),
    "government": (
        "Government",
        ["board of supervisors", "supervisor", "budget", "county administrator",
         "ordinance", "meeting", "public hearing", "tax", "referendum", "vote"],
    ),
    "community": (
        "Community",
        ["volunteer", "event", "festival", "park", "library", "neighborhood",
         "resident", "community", "celebration"],
    ),
    "weather": (
        "Weather & Safety",
        ["warning", "watch", "advisory", "storm", "flood", "winter", "heat",
         "tornado", "severe"],
    ),
}

# --- Geographic relevance --------------------------------------------------
# For broad sources (regional news, social) we keep an item only if it
# mentions one of these. County-government sources are relevant by definition
# and skip this check (see `geo_filter: False`).
CHESTERFIELD_PLACES = [
    "chesterfield", "midlothian", "chester", "bon air", "ettrick",
    "matoaca", "moseley", "bermuda", "dale district", "clover hill",
    "enon", "winterpock", "hopewell road", "hull street", "iron bridge",
    "courthouse road", "robious", "brandermill", "woodlake", "salisbury",
]

# --- Sources ---------------------------------------------------------------
# kind:
#   "rss" -> standard RSS/Atom feed (xml)
#   "nws" -> National Weather Service active alerts JSON API
# geo_filter: if True, drop items that don't mention a Chesterfield place.
# default_focus: focus tags applied to every item from this source.
SOURCES = [
    # --- Chesterfield County government (CivicEngage News Flash) ----------
    {
        "id": "county-news",
        "name": "Chesterfield County News",
        "kind": "rss",
        "url": "https://www.chesterfield.gov/RSSFeed.aspx?ModID=1&CID=Chesterfield-News-1",
        "geo_filter": False,
        "default_focus": ["government", "community"],
        "license": "government",  # public record — safe to summarize freely
    },
    {
        "id": "county-police",
        "name": "Chesterfield Police News",
        "kind": "rss",
        "url": "https://www.chesterfield.gov/RSSFeed.aspx?ModID=1&CID=Police-News-11",
        "geo_filter": False,
        "default_focus": ["police"],
        "license": "government",
    },
    {
        "id": "county-fire",
        "name": "Chesterfield Fire & EMS",
        "kind": "rss",
        "url": "https://www.chesterfield.gov/RSSFeed.aspx?ModID=1&CID=Fire-and-EMS-Notices-94",
        "geo_filter": False,
        "default_focus": ["fire"],
        "license": "government",
    },
    {
        "id": "county-development",
        "name": "Community Development News",
        "kind": "rss",
        "url": "https://www.chesterfield.gov/RSSFeed.aspx?ModID=1&CID=Community-Development-News-129",
        "geo_filter": False,
        "default_focus": ["growth", "business"],
        "license": "government",
    },
    {
        "id": "county-planning",
        "name": "Planning",
        "kind": "rss",
        "url": "https://www.chesterfield.gov/RSSFeed.aspx?ModID=1&CID=Planning-53",
        "geo_filter": False,
        "default_focus": ["growth", "government"],
        "license": "government",
    },
    {
        "id": "county-transportation",
        "name": "Transportation Projects",
        "kind": "rss",
        "url": "https://www.chesterfield.gov/RSSFeed.aspx?ModID=1&CID=Transportation-Projects-96",
        "geo_filter": False,
        "default_focus": ["growth", "community"],
        "license": "government",
    },
    # --- National Weather Service (free API, no key) ----------------------
    {
        "id": "nws-alerts",
        "name": "NWS Weather Alerts",
        "kind": "nws",
        # Chesterfield County, VA UGC zone code.
        "url": "https://api.weather.gov/alerts/active?zone=VAC041",
        "geo_filter": False,
        "default_focus": ["weather"],
        "license": "government",
    },
    # --- YouTube channels (keyless Atom feeds; video + thumbnail) --------
    # https://www.youtube.com/feeds/videos.xml?channel_id=UC...
    {
        "id": "yt-county",
        "name": "Chesterfield County (YouTube)",
        "kind": "youtube",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UC5280MG2tIH9zd1Kv-df0Lw",
        "geo_filter": False,
        "default_focus": ["community", "government"],
        "license": "government",
    },
    {
        "id": "yt-police",
        "name": "Chesterfield County Police (YouTube)",
        "kind": "youtube",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCV3R2lOmuciVNN2ojmq-MaQ",
        "geo_filter": False,
        "default_focus": ["police"],
        "license": "government",
    },
    {
        "id": "yt-sheriff",
        "name": "Chesterfield County Sheriff (YouTube)",
        "kind": "youtube",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UC84t-Kbu9ZU4TGMCKgJo4UQ",
        "geo_filter": False,
        "default_focus": ["police", "community"],
        "license": "government",
    },
    {
        "id": "yt-ccps",
        "name": "Chesterfield County Public Schools (YouTube)",
        "kind": "youtube",
        # @oneccps — channel_id resolved from the live channel page's
        # canonical link (verified 15 entries).
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UC0u1f-HaLsnUr6ya1vZgQ0w",
        "geo_filter": False,        # district channel is Chesterfield by definition
        "default_focus": ["schools"],
        "license": "government",
    },

    # --- Local TV stations (YouTube; keyless). Regional outlets, so
    # geo_filter=True keeps only videos that mention a Chesterfield place.
    # press license: headline + link + short summary only.
    {
        "id": "yt-wtvr",
        "name": "WTVR CBS 6 (YouTube)",
        "kind": "youtube",
        # @WTVRCBS6 — channel_id from canonical link (verified 15 entries).
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UC9ha3sh4YTCSK83dH6OlWTw",
        "geo_filter": True,
        "default_focus": [],
        "license": "press",
    },
    {
        "id": "yt-wric",
        "name": "WRIC 8News (YouTube)",
        "kind": "youtube",
        # @WRIC8News — channel_id confirmed via canonical link, but YouTube's
        # Atom feed for this channel returned 404/500 during verification.
        # Disabled until the feed is reachable; flip to True once it returns items.
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCauvD2vzSabgxSeA2wGipvQ",
        "geo_filter": True,
        "default_focus": [],
        "license": "press",
        "enabled": False,
    },

    # --- Google News (keyless RSS that searches ALL outlets) -------------
    # This is how we reach beyond county feeds: any outlet (RTD, WTVR, WRIC,
    # NBC12, Observer, etc.) that publishes a matching story shows up here.
    # press license: headline + link + short original summary only.
    {
        "id": "gnews-chesterfield",
        "name": "Google News: Chesterfield County",
        "kind": "rss",
        "url": ("https://news.google.com/rss/search?q=%22Chesterfield+County%22+"
                "Virginia&hl=en-US&gl=US&ceid=US:en"),
        "geo_filter": True,         # require a Chesterfield place name (drops other Chesterfields)
        "default_focus": [],
        "license": "press",
    },
    {
        "id": "gnews-schools",
        "name": "Google News: Chesterfield Schools",
        "kind": "rss",
        "url": ("https://news.google.com/rss/search?q=%22Chesterfield+County+"
                "Public+Schools%22&hl=en-US&gl=US&ceid=US:en"),
        "geo_filter": True,
        "default_focus": ["schools"],
        "license": "press",
    },
    # Beat-specific Google News queries for under-covered topics. Each is
    # URL-encoded; %22 wraps the phrase, OR broadens the second term.
    {
        "id": "gnews-growth",
        "name": "Google News: Chesterfield Development",
        "kind": "rss",
        "url": ("https://news.google.com/rss/search?q=%22Chesterfield+County%22+"
                "development+OR+rezoning&hl=en-US&gl=US&ceid=US:en"),
        "geo_filter": True,
        "default_focus": ["growth"],
        "license": "press",
    },
    {
        "id": "gnews-business",
        "name": "Google News: Chesterfield Business",
        "kind": "rss",
        "url": ("https://news.google.com/rss/search?q=%22Chesterfield+County%22+"
                "business+OR+restaurant+opening&hl=en-US&gl=US&ceid=US:en"),
        "geo_filter": True,
        "default_focus": ["business"],
        "license": "press",
    },
    {
        "id": "gnews-bos",
        "name": "Google News: Chesterfield Board of Supervisors",
        "kind": "rss",
        "url": ("https://news.google.com/rss/search?q=%22Chesterfield+County+"
                "Board+of+Supervisors%22&hl=en-US&gl=US&ceid=US:en"),
        "geo_filter": True,
        "default_focus": ["government"],
        "license": "press",
    },
    {
        "id": "gnews-schoolboard",
        "name": "Google News: Chesterfield School Board",
        "kind": "rss",
        "url": ("https://news.google.com/rss/search?q=%22Chesterfield+County%22+"
                "school+board&hl=en-US&gl=US&ceid=US:en"),
        "geo_filter": True,
        "default_focus": ["schools", "government"],
        "license": "press",
    },

    # --- More Chesterfield County dept feeds (CivicEngage News Flash, ModID=1)
    # Verified against the county RSS index (chesterfield.gov/rss.aspx) and a
    # live fetch. NOTE: there is NO dedicated News-Flash RSS for Economic
    # Development, Utilities, Sheriff, Commonwealth's Attorney, or Building
    # Inspection — the county directory lists those departments but publishes
    # no per-dept feed (a guessed CID just returns the county-wide aggregate,
    # so adding them would only duplicate content). The Courts Public
    # Advisories feed (CID 116) exists but returned 0 items, so it's omitted.
    {
        "id": "county-parks",
        "name": "Chesterfield Parks & Recreation",
        "kind": "rss",
        "url": "https://www.chesterfield.gov/RSSFeed.aspx?ModID=1&CID=Parks-and-Recreation-Highlights-8",
        "geo_filter": False,
        "default_focus": ["community"],
        "license": "government",
    },
    {
        "id": "county-parks-projects",
        "name": "Chesterfield Parks Projects",
        "kind": "rss",
        "url": "https://www.chesterfield.gov/RSSFeed.aspx?ModID=1&CID=Parks-and-Recreation-Current-Projects-168",
        "geo_filter": False,
        "default_focus": ["community", "growth"],
        "license": "government",
    },
    {
        "id": "county-library",
        "name": "Chesterfield Library News",
        "kind": "rss",
        "url": "https://www.chesterfield.gov/RSSFeed.aspx?ModID=1&CID=Library-News-171",
        "geo_filter": False,
        "default_focus": ["community"],
        "license": "government",
    },
    # Official county Alert Center feeds (ModID=63). Verified valid RSS 2.0 and
    # Chesterfield-scoped, but EMPTY most of the time — they populate during real
    # events (snow days, boil-water advisories, office closures), which is exactly
    # the timely, actionable info residents want. Government license.
    {
        "id": "county-closures",
        "name": "Chesterfield Office & Facility Closures",
        "kind": "rss",
        "url": "https://www.chesterfield.gov/RSSFeed.aspx?ModID=63&CID=Office-and-Facility-Closures-10",
        "geo_filter": False,
        "default_focus": ["community"],
        "license": "government",
    },
    {
        "id": "county-advisories",
        "name": "Chesterfield Announcements & Advisories",
        "kind": "rss",
        "url": "https://www.chesterfield.gov/RSSFeed.aspx?ModID=63&CID=Announcements-and-Advisories-16",
        "geo_filter": False,
        "default_focus": ["community", "weather"],
        "license": "government",
    },

    # --- Local / regional outlet RSS (press license; geo_filter on the
    # regional ones to keep only Chesterfield-area stories). Each verified to
    # return HTTP 200, parse via fetch_rss, and contain Chesterfield items.
    # press license: headline + link + short ORIGINAL summary only.
    {
        "id": "richmond-bizsense",
        "name": "Richmond BizSense",
        "kind": "rss",
        "url": "https://richmondbizsense.com/feed/",
        "geo_filter": True,          # regional business outlet; keep Chesterfield-area items
        "default_focus": ["business", "growth"],
        "license": "press",
    },
    {
        "id": "wtvr-local",
        "name": "WTVR CBS 6 Local",
        "kind": "rss",
        # Section feed (news/local-news.rss) — far more local volume than the
        # thin index.rss. Regional, so geo_filter keeps Chesterfield stories.
        "url": "https://www.wtvr.com/news/local-news.rss",
        "geo_filter": True,
        "default_focus": [],
        "license": "press",
    },
    {
        "id": "wric-local",
        "name": "WRIC 8News Local",
        "kind": "rss",
        # The old root WRIC feed 404'd; this local-news section feed works
        # (HTTP 200, ~50 items, Chesterfield content). geo_filter on.
        "url": "https://www.wric.com/news/local-news/feed/",
        "geo_filter": True,
        "default_focus": [],
        "license": "press",
    },
    {
        "id": "nbc12",
        "name": "NBC12 / WWBT News",
        "kind": "rss",
        # NBC12 (nbc12.com) redirects to 12onyourside.com (Gray/Arc CMS).
        # The legacy /arcio/rss/ path is dead (404); this Arc outbound feed
        # works (HTTP 200, 20 items, Chesterfield content).
        "url": "https://www.12onyourside.com/arc/outboundfeeds/rss/category/news/?outputType=xml",
        "geo_filter": True,
        "default_focus": [],
        "license": "press",
    },
    {
        "id": "wtvr-traffic",
        "name": "WTVR CBS 6 Traffic",
        "kind": "rss",
        # Central-VA traffic incidents; geo_filter keeps only the ones that name
        # a Chesterfield place (I-95 South, Hull Street, Iron Bridge, etc.).
        "url": "https://www.wtvr.com/traffic.rss",
        "geo_filter": True,
        "default_focus": [],
        "license": "press",
    },
    {
        "id": "vpm-news",
        "name": "VPM News",
        "kind": "rss",
        # Central Virginia public media. Low volume (~2 items) and statewide,
        # so geo_filter keeps only Chesterfield-area items, but high trust.
        "url": "https://www.vpm.org/news.rss",
        "geo_filter": True,
        "default_focus": [],
        "license": "press",
    },
    {
        "id": "richmonder",
        "name": "The Richmonder",
        "kind": "rss",
        # Nonprofit Richmond-area newsroom (richmonder.org) that expanded its
        # coverage into Chesterfield County government in 2025 — original local
        # reporting. Regional, so geo_filter keeps the Chesterfield-area items.
        "url": "https://www.richmonder.org/rss/",
        "geo_filter": True,
        "default_focus": [],
        "license": "press",
    },
    {
        "id": "rtd-local",
        "name": "Richmond Times-Dispatch",
        "kind": "rss",
        # The major regional daily (richmond.com). Category RSS for news/local
        # (~50 items). Regional, so geo_filter keeps the Chesterfield-area items.
        "url": "https://richmond.com/search/?f=rss&t=article&c=news/local&l=50",
        "geo_filter": True,
        "default_focus": [],
        "license": "press",
    },

    # --- Google News beat queries (keyless RSS, biggest volume win) -------
    # Same format as the gnews-* sources above. geo_filter=True is REQUIRED:
    # place/topic searches pull in non-Chesterfield noise (e.g. a "Midlothian"
    # real-estate listing, or "Chesterfield" results from PA/SC/UK), which the
    # CHESTERFIELD_PLACES filter drops. press license.
    # -- Place-based --
    {
        "id": "gnews-midlothian",
        "name": "Google News: Midlothian",
        "kind": "rss",
        "url": "https://news.google.com/rss/search?q=Midlothian+VA&hl=en-US&gl=US&ceid=US:en",
        "geo_filter": True,
        "default_focus": [],
        "license": "press",
    },
    {
        "id": "gnews-chester",
        "name": "Google News: Chester VA",
        "kind": "rss",
        "url": "https://news.google.com/rss/search?q=Chester+VA&hl=en-US&gl=US&ceid=US:en",
        "geo_filter": True,
        "default_focus": [],
        "license": "press",
    },
    {
        "id": "gnews-matoaca",
        "name": "Google News: Matoaca",
        "kind": "rss",
        "url": "https://news.google.com/rss/search?q=Matoaca&hl=en-US&gl=US&ceid=US:en",
        "geo_filter": True,
        "default_focus": [],
        "license": "press",
    },
    {
        "id": "gnews-moseley",
        "name": "Google News: Moseley VA",
        "kind": "rss",
        "url": "https://news.google.com/rss/search?q=Moseley+VA&hl=en-US&gl=US&ceid=US:en",
        "geo_filter": True,
        "default_focus": [],
        "license": "press",
    },
    {
        "id": "gnews-bonair",
        "name": "Google News: Bon Air",
        "kind": "rss",
        "url": "https://news.google.com/rss/search?q=Bon+Air+VA&hl=en-US&gl=US&ceid=US:en",
        "geo_filter": True,
        "default_focus": [],
        "license": "press",
    },
    {
        "id": "gnews-brandermill",
        "name": "Google News: Brandermill",
        "kind": "rss",
        "url": "https://news.google.com/rss/search?q=Brandermill&hl=en-US&gl=US&ceid=US:en",
        "geo_filter": True,
        "default_focus": [],
        "license": "press",
    },
    {
        "id": "gnews-hullstreet",
        "name": "Google News: Hull Street Road",
        "kind": "rss",
        "url": "https://news.google.com/rss/search?q=Hull+Street+Road+Chesterfield&hl=en-US&gl=US&ceid=US:en",
        "geo_filter": True,
        "default_focus": ["growth"],
        "license": "press",
    },
    {
        "id": "gnews-route288",
        "name": "Google News: Route 288",
        "kind": "rss",
        "url": "https://news.google.com/rss/search?q=Route+288+Chesterfield&hl=en-US&gl=US&ceid=US:en",
        "geo_filter": True,
        "default_focus": ["growth"],
        "license": "press",
    },
    {
        "id": "gnews-route10",
        "name": "Google News: Route 10",
        "kind": "rss",
        "url": "https://news.google.com/rss/search?q=Route+10+Chesterfield&hl=en-US&gl=US&ceid=US:en",
        "geo_filter": True,
        "default_focus": ["growth"],
        "license": "press",
    },
    # -- Topic-based --
    {
        "id": "gnews-rezoning",
        "name": "Google News: Chesterfield Rezoning",
        "kind": "rss",
        "url": "https://news.google.com/rss/search?q=Chesterfield+rezoning&hl=en-US&gl=US&ceid=US:en",
        "geo_filter": True,
        "default_focus": ["growth"],
        "license": "press",
    },
    {
        "id": "gnews-development2",
        "name": "Google News: Chesterfield Development",
        "kind": "rss",
        "url": "https://news.google.com/rss/search?q=Chesterfield+development&hl=en-US&gl=US&ceid=US:en",
        "geo_filter": True,
        "default_focus": ["growth"],
        "license": "press",
    },
    {
        "id": "gnews-datacenter",
        "name": "Google News: Chesterfield Data Center",
        "kind": "rss",
        "url": "https://news.google.com/rss/search?q=Chesterfield+data+center&hl=en-US&gl=US&ceid=US:en",
        "geo_filter": True,
        "default_focus": ["growth", "business"],
        "license": "press",
    },
    {
        "id": "gnews-restaurant",
        "name": "Google News: Chesterfield Restaurant",
        "kind": "rss",
        "url": "https://news.google.com/rss/search?q=Chesterfield+restaurant&hl=en-US&gl=US&ceid=US:en",
        "geo_filter": True,
        "default_focus": ["business"],
        "license": "press",
    },
    {
        "id": "gnews-crime",
        "name": "Google News: Chesterfield Crime",
        "kind": "rss",
        "url": "https://news.google.com/rss/search?q=Chesterfield+crime&hl=en-US&gl=US&ceid=US:en",
        "geo_filter": True,
        "default_focus": ["police"],
        "license": "press",
    },

    # --- Community signal (Reddit) ---------------------------------------
    # ENABLED 2026-06-15: fetch.py now has a generic `atom` fetcher (Reddit
    # emits Atom <entry> with a plain <link href>, which fetch_atom handles).
    # Verified: r/ChesterfieldVA returns 25 entries with the pipeline UA. The
    # autonomous editor filters non-newsworthy chatter; a genuinely local post
    # (road closure, outage, Shoosmith update) becomes real signal. At one fetch
    # per 2h the rate-limit (429) risk is negligible.
    {
        "id": "reddit-chesterfieldva",
        "name": "r/ChesterfieldVA",
        "kind": "atom",
        "url": "https://www.reddit.com/r/ChesterfieldVA/.rss",
        "geo_filter": False,         # subreddit is Chesterfield by definition
        "default_focus": [],
        "license": "press",
    },
    {
        "id": "reddit-rva",
        "name": "r/rva",
        "kind": "atom",
        "url": "https://www.reddit.com/r/rva/.rss",
        "geo_filter": True,          # regional subreddit; keep Chesterfield items
        "default_focus": [],
        "license": "press",
    },

    # --- Local newspaper (optional; enable once feed/cert verified) -------
    # The Observer is a copyrighted outlet: we only ever store headline +
    # link + a short ORIGINAL summary, never the full article text.
    {
        "id": "observer",
        "name": "Chesterfield Observer",
        "kind": "rss",
        "url": "https://www.chesterfieldobserver.com/feed/",
        "geo_filter": False,        # outlet is already Chesterfield-specific
        "default_focus": [],         # let classifier decide
        "license": "press",          # headline + link + short summary ONLY
        # Still unreachable (2026-06): not a cert-VERIFICATION issue (which
        # fetch.py's CERT_NONE fallback would handle) — the server aborts the
        # TLS handshake itself (SSL_ERROR_SYSCALL / "EOF occurred in violation
        # of protocol"). Homepage and feed both fail; nothing sources.py can
        # do. Leave disabled. (Google News still surfaces Observer stories.)
        "enabled": False,            # flip to True once the feed is reachable
    },

    # --- REGIONAL TRACK: Virginia / Richmond-area news that affects Chesterfield
    # residents but isn't Chesterfield-specific (state laws, the budget, Dominion
    # rates, regional transportation, courts, elections). track="regional" routes
    # these to a separate editorial pass and the /virginia.html page, NOT the local
    # feed. geo_filter is OFF (these are statewide by definition). press license.
    {
        "id": "va-mercury", "name": "Virginia Mercury", "kind": "rss",
        "url": "https://virginiamercury.com/feed/",
        "geo_filter": False, "default_focus": ["government"], "license": "press",
        "track": "regional",
    },
    {
        "id": "va-cardinal", "name": "Cardinal News", "kind": "rss",
        "url": "https://cardinalnews.org/feed/",
        "geo_filter": False, "default_focus": ["government"], "license": "press",
        "track": "regional",
    },
    {
        "id": "va-rtd-state", "name": "Richmond Times-Dispatch (State)", "kind": "rss",
        "url": "https://richmond.com/search/?f=rss&t=article&c=news/state-and-regional&l=30",
        "geo_filter": False, "default_focus": ["government"], "license": "press",
        "track": "regional",
    },
    {
        "id": "gnews-va-assembly", "name": "Google News: Virginia Government", "kind": "rss",
        "url": ("https://news.google.com/rss/search?q=%22Virginia+General+Assembly%22+OR+"
                "%22Virginia+law%22+OR+%22Gov.+of+Virginia%22&hl=en-US&gl=US&ceid=US:en"),
        "geo_filter": False, "default_focus": ["government"], "license": "press",
        "track": "regional",
    },
    {
        "id": "gnews-va-dominion", "name": "Google News: Dominion / VA Utilities", "kind": "rss",
        "url": ("https://news.google.com/rss/search?q=%22Dominion+Energy%22+Virginia+"
                "rate+OR+bill&hl=en-US&gl=US&ceid=US:en"),
        "geo_filter": False, "default_focus": ["government"], "license": "press",
        "track": "regional",
    },
]


def active_sources():
    """Sources not explicitly disabled."""
    return [s for s in SOURCES if s.get("enabled", True)]
