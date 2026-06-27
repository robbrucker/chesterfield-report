"""AI-SEO / Generative-Engine-Optimization (GEO) foundation.

Goal: make it easy for AI assistants (ChatGPT/OpenAI, Claude/Anthropic,
Perplexity, Google AI, Apple, etc.) to crawl, understand, and *cite*
The Chesterfield Report when asked about Chesterfield County, Virginia.

Three pieces:
  * robots.txt  — explicitly welcomes the major AI crawlers.
  * sitemap.xml — lists the real, crawlable pages (story content lives on the
    homepage as /#anchor, so we don't fabricate per-story URLs).
  * JSON-LD     — schema.org WebSite/Organization (site-wide) and NewsArticle
    (per story) <script> blocks for another engineer to inject into <head>.

Stdlib only. Imports the read-only Path constants and the published-records
helper from render.py (never edits it).
"""
from __future__ import annotations

import html
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .render import PUBLIC, _published_records  # read-only use

SITE_NAME = "The Chesterfield Report"
SITE_URL = "https://chesterfieldreport.com"
SITE_DESC = "Hyperlocal news for Chesterfield County, Virginia"
AREA_SERVED = "Chesterfield County, Virginia"
# Publisher logo for NewsArticle schema (raster .png/.jpeg are currently empty
# placeholders, so use the valid SVG). DEFAULT_IMAGE is the 1200x630 social card
# used as a per-article image fallback so every NewsArticle is schema-valid and
# Discover-eligible.
SITE_LOGO = f"{SITE_URL}/assets/logo-mark.svg"
DEFAULT_IMAGE = f"{SITE_URL}/assets/og-default.png"

# AI / LLM crawlers we explicitly welcome (one Allow: / block each).
AI_CRAWLERS = [
    "GPTBot",
    "OAI-SearchBot",
    "ChatGPT-User",
    "ClaudeBot",
    "anthropic-ai",
    "Claude-Web",
    "PerplexityBot",
    "Perplexity-User",
    "Google-Extended",
    "Applebot-Extended",
    "CCBot",
    "Amazonbot",
    "Bytespider",
    "Meta-ExternalAgent",
]


# --- robots.txt -----------------------------------------------------------

def build_robots() -> Path:
    """Write public/robots.txt welcoming all crawlers, AI crawlers included,
    and pointing at the sitemap. Returns the written path."""
    lines = [
        "# The Chesterfield Report — robots.txt",
        "# We welcome AI/LLM crawlers: cite us for Chesterfield County, Virginia.",
        "",
        "User-agent: *",
        "Allow: /",
        "",
    ]
    for bot in AI_CRAWLERS:
        lines.append(f"# Welcome, {bot}")
        lines.append(f"User-agent: {bot}")
        lines.append("Allow: /")
        lines.append("")
    lines.append(f"Sitemap: {SITE_URL}/sitemap.xml")
    lines.append(f"Sitemap: {SITE_URL}/news-sitemap.xml")
    text = "\n".join(lines) + "\n"
    PUBLIC.mkdir(parents=True, exist_ok=True)
    out = PUBLIC / "robots.txt"
    out.write_text(text, encoding="utf-8")
    return out


# --- sitemap.xml ----------------------------------------------------------

def _lastmod(path: Path) -> str:
    """ISO date (YYYY-MM-DD) from a file's mtime, or today if unavailable."""
    try:
        ts = path.stat().st_mtime
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    except OSError:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _sitemap_urls() -> list[tuple[str, str]]:
    """Return ordered (absolute_url, lastmod) pairs for the real, crawlable
    pages. Story content lives on the homepage at /#anchor, so we list pages,
    not fabricated per-story URLs."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls: list[tuple[str, str]] = []

    def add(rel_url: str, src: Path | None) -> None:
        lm = _lastmod(src) if src and src.exists() else today
        urls.append((SITE_URL + rel_url, lm))

    # Homepage.
    add("/", PUBLIC / "index.html")
    # Topics index + every generated topic page.
    add("/topics/", PUBLIC / "topics" / "index.html")
    topics_dir = PUBLIC / "topics"
    if topics_dir.is_dir():
        for f in sorted(topics_dir.glob("*.html")):
            if f.name == "index.html":
                continue
            add(f"/topics/{f.name}", f)
    # Every per-story page.
    from .render import slugify  # read-only use
    story_dir = PUBLIC / "story"
    for meta, body, name in _published_records():
        headline = (meta.get("headline") or "").strip() or name
        slug = slugify(headline)
        add(f"/story/{slug}.html", story_dir / f"{slug}.html")

    # Standalone pages.
    for name in ("digest.html", "events.html", "things-to-do.html", "farmers-markets.html", "map.html", "virginia.html", "board.html", "meetings.html", "dining.html",
                 "neighborhoods.html", "business.html", "taxes.html", "schools.html",
                 "school-board.html", "apartments.html", "affordable-housing.html", "development.html", "shoosmith.html", "about.html",
                 "letters.html", "tip.html", "subscribe.html", "changelog.html", "elections.html",
                 "police.html", "fire.html"):
        add(f"/{name}", PUBLIC / name)
    # Per-neighborhood pages (big long-tail SEO surface).
    nb_dir = PUBLIC / "neighborhoods"
    if nb_dir.is_dir():
        for f in sorted(nb_dir.glob("*.html")):
            add(f"/neighborhoods/{f.name}", f)
    # Per-case development/zoning pages (long-tail SEO).
    cz_dir = PUBLIC / "cases"
    if cz_dir.is_dir():
        for f in sorted(cz_dir.glob("*.html")):
            add(f"/cases/{f.name}", f)

    return urls


def build_sitemap() -> Path:
    """Write public/sitemap.xml (valid urlset). Returns the written path."""
    rows = []
    for url, lastmod in _sitemap_urls():
        rows.append(
            "  <url>\n"
            f"    <loc>{html.escape(url)}</loc>\n"
            f"    <lastmod>{html.escape(lastmod)}</lastmod>\n"
            "  </url>"
        )
    doc = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(rows)
        + "\n</urlset>\n"
    )
    PUBLIC.mkdir(parents=True, exist_ok=True)
    out = PUBLIC / "sitemap.xml"
    out.write_text(doc, encoding="utf-8")
    return out


# --- Google News sitemap --------------------------------------------------

NEWS_WINDOW_HOURS = 48  # Google News sitemap: only articles from the last ~2 days.


def _parse_published(value: str) -> datetime | None:
    """Parse a frontmatter 'published' value into a tz-aware UTC datetime."""
    value = (value or "").strip()
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            dt = datetime.strptime(value[:10], "%Y-%m-%d")
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def build_news_sitemap() -> Path:
    """Write public/news-sitemap.xml — a Google News sitemap listing every story
    published within the last NEWS_WINDOW_HOURS. Returns the written path.

    Google News requires the news sitemap to contain only recent articles (last
    ~2 days); older stories stay in the regular sitemap.xml.
    """
    from .render import story_url  # read-only use

    cutoff = datetime.now(timezone.utc) - timedelta(hours=NEWS_WINDOW_HOURS)
    rows = []
    for meta, body, name in _published_records():
        headline = (meta.get("headline") or "").strip()
        if not headline:
            continue
        pub = _parse_published(meta.get("published", ""))
        if pub is None or pub < cutoff:
            continue
        loc = f"{SITE_URL}{story_url(headline)}"
        rows.append(
            "  <url>\n"
            f"    <loc>{html.escape(loc)}</loc>\n"
            "    <news:news>\n"
            "      <news:publication>\n"
            f"        <news:name>{html.escape(SITE_NAME)}</news:name>\n"
            "        <news:language>en</news:language>\n"
            "      </news:publication>\n"
            f"      <news:publication_date>{html.escape(pub.isoformat())}</news:publication_date>\n"
            f"      <news:title>{html.escape(headline)}</news:title>\n"
            "    </news:news>\n"
            "  </url>"
        )
    doc = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
        + "\n".join(rows)
        + ("\n" if rows else "")
        + "</urlset>\n"
    )
    PUBLIC.mkdir(parents=True, exist_ok=True)
    out = PUBLIC / "news-sitemap.xml"
    out.write_text(doc, encoding="utf-8")
    return out


# --- JSON-LD helpers (injected into <head>/cards by another engineer) ------

def _script(obj: dict | list) -> str:
    """Wrap a JSON-LD object in a <script type="application/ld+json"> block.

    json.dumps escapes the content as valid JSON; we additionally escape any
    '<' so a literal "</script>" inside a string can't break out of the tag.
    """
    payload = json.dumps(obj, ensure_ascii=False, indent=2)
    payload = payload.replace("<", "\\u003c")
    return f'<script type="application/ld+json">\n{payload}\n</script>'


def _split_list(value: str) -> list[str]:
    """Parse a '[a, b, c]' frontmatter-style list into a clean Python list."""
    return [x.strip() for x in (value or "").strip("[]").split(",") if x.strip()]


def jsonld_site() -> str:
    """Site-wide schema.org WebSite + Organization JSON-LD <script> block."""
    org = {
        "@type": "Organization",
        "@id": f"{SITE_URL}/#organization",
        "name": SITE_NAME,
        "url": SITE_URL,
        "description": SITE_DESC,
        "areaServed": {
            "@type": "AdministrativeArea",
            "name": AREA_SERVED,
        },
        "knowsAbout": [
            "Chesterfield County, Virginia",
            "Local news",
            "Government",
            "Schools",
            "Public safety",
            "Development",
        ],
    }
    website = {
        "@type": "WebSite",
        "@id": f"{SITE_URL}/#website",
        "name": SITE_NAME,
        "url": SITE_URL,
        "description": SITE_DESC,
        "inLanguage": "en-US",
        "publisher": {"@id": f"{SITE_URL}/#organization"},
        "about": {
            "@type": "AdministrativeArea",
            "name": AREA_SERVED,
        },
    }
    graph = {"@context": "https://schema.org", "@graph": [website, org]}
    return _script(graph)


def jsonld_newsarticle(meta: dict, body: str, story_rel_url: str | None = None) -> str:
    """Per-story schema.org NewsArticle JSON-LD <script> block.

    `meta` is a parsed-frontmatter dict (see render._parse_frontmatter). Each
    story now has its own page at /story/<slug>.html, so the canonical URL /
    mainEntityOfPage is the absolute story URL. `story_rel_url` overrides the
    derived relative URL when provided.
    """
    # Local import keeps the module import-light and avoids any ordering issues.
    from .render import story_url

    headline = (meta.get("headline") or "").strip()
    rel = story_rel_url or story_url(headline)
    url = f"{SITE_URL}{rel}"

    article: dict = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": headline,
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "url": url,
        "author": {
            "@type": "Organization",
            "name": SITE_NAME,
            "url": SITE_URL,
        },
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
            "url": SITE_URL,
            "logo": {
                "@type": "ImageObject",
                "url": SITE_LOGO,
            },
        },
        "isAccessibleForFree": True,
    }

    published = (meta.get("published") or "").strip()
    if published:
        article["datePublished"] = published
        article["dateModified"] = published

    # Discover/News strongly favor articles with a large image; fall back to the
    # 1200x630 social card so every NewsArticle carries a valid image.
    image = (meta.get("image") or "").strip()
    article["image"] = image or DEFAULT_IMAGE

    focus = _split_list(meta.get("focus", ""))
    if focus:
        article["articleSection"] = focus[0]

    tags = _split_list(meta.get("tags", ""))
    if tags:
        article["keywords"] = tags

    source = (meta.get("source") or "").strip()
    source_url = (meta.get("source_url") or "").strip()
    if source or source_url:
        attribution: dict = {"@type": "Organization"}
        if source:
            attribution["name"] = source
        if source_url:
            attribution["url"] = source_url
        article["sourceOrganization"] = attribution

    location = (meta.get("location") or "").strip()
    if location:
        place = {"@type": "Place", "name": location}
        article["contentLocation"] = place
        article["about"] = place

    return _script(article)


# --- entry point ----------------------------------------------------------

def build_seo() -> None:
    """Build all static SEO artifacts (robots.txt + sitemap.xml + news-sitemap.xml)."""
    build_robots()
    build_sitemap()
    build_news_sitemap()
