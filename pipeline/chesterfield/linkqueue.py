"""Bounded "link -> candidate article" engine.

Published full articles end with `## Related links` and `## Sources` sections
full of markdown bullet links. A handful of those links point at *stories* worth
covering in their own right (a TV-station article, a newsflash detail page, a
RichmondBizSense piece). This module harvests those links and turns the
*newsworthy* ones into fresh **draft** stubs the user can later deepen and
approve — building a self-linking web of local coverage.

Crucially it does NOT runaway-crawl:

  * **Depth 1.** Only links found inside *non-link-sourced* articles are
    considered. Every stub we create is stamped `ai_provider: linkqueue`, and we
    skip those files when harvesting — so a candidate can never spawn more
    candidates.
  * **Bounded output.** At most `limit` stubs per run.
  * **Idempotent.** A persistent seen-set (``pipeline/linkqueue_seen.json``)
    plus a check against every existing ``source_url`` means re-running never
    re-creates the same candidate.

Stdlib only. Works entirely from files on disk — it never imports render/enrich
and never touches the network. Importing ``sources`` (a plain-data registry) is
the one allowed import.

The drafts this writes are LOCAL only; they flow through the normal local
review/approve process and are never auto-published.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

# `sources` is the only package import the spec allows — it's pure data.
try:  # package-relative when imported as `chesterfield.linkqueue`
    from . import sources as _sources
except ImportError:  # pragma: no cover - fallback for odd import paths
    import sources as _sources  # type: ignore


# --- Paths -----------------------------------------------------------------
# This file lives at <root>/pipeline/chesterfield/linkqueue.py, so the project
# root is two parents up. Resolve everything from there so the module works
# regardless of the caller's cwd.
_HERE = Path(__file__).resolve()
_ROOT = _HERE.parents[2]
PUBLISHED_DIR = _ROOT / "content" / "published"
DRAFTS_DIR = _ROOT / "content" / "drafts"
SEEN_PATH = _HERE.parents[1] / "linkqueue_seen.json"  # pipeline/linkqueue_seen.json

# Filename date prefix for stubs created in this run.
TODAY = "2026-06-08"

# Stamp that marks a file as a linkqueue-generated candidate. We skip these when
# harvesting so candidates never spawn more candidates (depth-1 guarantee).
MARKER = "linkqueue"

# Chesterfield place list — reused from sources.py so it stays in sync.
PLACES = [p.lower() for p in getattr(_sources, "CHESTERFIELD_PLACES", [])]
if "chesterfield" not in PLACES:
    PLACES.append("chesterfield")


# --- URL helpers -----------------------------------------------------------
def _normalize_url(url: str) -> str:
    """Canonical form for dedup: lowercase scheme/host, strip fragment, drop a
    trailing slash, drop a leading ``www.``. Query is preserved (CivicAlerts
    distinguishes stories only by ``?aid=``)."""
    url = url.strip()
    parts = urlsplit(url)
    scheme = (parts.scheme or "https").lower()
    netloc = parts.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parts.path.rstrip("/")
    return urlunsplit((scheme, netloc, path, parts.query, ""))


def _domain(url: str) -> str:
    """Bare registrable host (no ``www.``) for the draft `source` field."""
    netloc = urlsplit(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


# Feed/registry "domain+path" prefixes already wired into sources.py. We key on
# host+path (NOT bare host) so a content page like
# chesterfield.gov/CivicAlerts.aspx?aid=7288 is NOT mistaken for the
# chesterfield.gov/RSSFeed.aspx feed that shares its host.
def _feed_keys() -> set[str]:
    keys = set()
    for s in getattr(_sources, "SOURCES", []):
        u = s.get("url", "")
        if not u:
            continue
        parts = urlsplit(u)
        host = parts.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        path = parts.path.rstrip("/")
        if path:
            keys.add(host + path)   # e.g. news.google.com/rss/search
        else:
            keys.add(host)          # bare-domain registry (none today, but safe)
    return keys


_FEED_KEYS = _feed_keys()


def _is_known_feed(url: str) -> bool:
    """True if the url shares a feed's host AND falls under its path prefix."""
    parts = urlsplit(url)
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = parts.path.rstrip("/")
    if host in _FEED_KEYS:               # bare-host registry
        return True
    hp = host + path
    for key in _FEED_KEYS:
        if "/" in key and (hp == key or hp.startswith(key + "/") or hp.startswith(key + ".")):
            return True
    return False


# --- Relevance + "is this a story?" heuristics -----------------------------
_PLACE_RE = re.compile("|".join(re.escape(p) for p in PLACES), re.I)


def _is_relevant(title: str, url: str) -> bool:
    """Chesterfield-relevant if the title OR the url mentions a known place."""
    blob = f"{title} {url}".lower()
    return bool(_PLACE_RE.search(blob))


# Reference/index junk we never want as a story stub.
_SKIP_DOMAINS = {
    "openstreetmap.org",   # generated "Places" search links
    "x.com", "twitter.com", "facebook.com", "instagram.com",  # social
    "youtube.com", "youtu.be",  # videos are their own source kind
    "gofundme.com",        # donation pages, not coverage
}
# chesterfield.gov "section/department landing" path heads — these are evergreen
# index pages, not stories. (CivicAlerts/newsflash detail pages ARE stories.)
_GOV_SECTION_WORDS = {
    "parks", "police", "library", "sheriff", "transportation", "planning",
    "departments", "government", "government.aspx", "things-to-do",
}


def _is_reference_page(title: str, url: str) -> tuple[bool, str]:
    """Return (skip?, reason). Skip bare domains, section indexes, department
    landing pages, PDFs, logins — we want *story* links only."""
    parts = urlsplit(url)
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = parts.path.rstrip("/")
    low_path = path.lower()

    if host in _SKIP_DOMAINS:
        return True, "social/osm/video/donation"

    # PDFs and document-center file views are reference artifacts, not stories.
    if low_path.endswith(".pdf") or "/documentcenter/" in low_path:
        return True, "pdf/document"

    # login / account walls
    if any(seg in low_path for seg in ("/login", "/signin", "/account")):
        return True, "login"

    # Bare domain or single-segment root ("/", "/news", "/parks"): an index.
    segs = [s for s in path.split("/") if s]
    if not segs:
        return True, "bare-domain"
    if len(segs) == 1 and host not in {"chesterfield.gov"}:
        # one-segment non-gov path like /events, /news, /parks -> section index
        if segs[0].lower() in _GOV_SECTION_WORDS or len(segs[0]) <= 12:
            return True, "section-index"

    # chesterfield.gov specifics -------------------------------------------
    if host == "chesterfield.gov":
        first = segs[0].lower()
        # /<numeric-id>/Department-Name  -> department landing page.
        if first.isdigit():
            return True, "gov-department-landing"
        # /Parks, /police, /library, /DSVRC, /government/... -> section pages.
        if first in _GOV_SECTION_WORDS:
            return True, "gov-section"
        if first == "government":
            return True, "gov-section"
        if first == "library" or first.startswith("library"):
            return True, "gov-section"
        # CivicAlerts.aspx without an aid= is a generic alerts index.
        if first == "civicalerts.aspx" and "aid=" not in parts.query.lower():
            return True, "gov-alert-index"
        # newsflash detail / CivicAlerts?aid= / specific .aspx with query are
        # treated as STORIES (fall through, not skipped).

    return False, ""


# --- Frontmatter harvesting ------------------------------------------------
_FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
_BULLET_RE = re.compile(r"^\s*-\s+\[([^\]]+)\]\((https?://[^)\s]+)\)", re.M)
_SECTION_RE = re.compile(
    r"^##\s+(?:Related links|Sources)\s*$\n(.*?)(?=^##\s|\Z)", re.M | re.S
)


def _read_frontmatter(text: str) -> dict:
    """Minimal `key: value` frontmatter reader (mirrors render's parser but
    without importing it). Values get surrounding quotes stripped."""
    m = _FRONT_RE.match(text)
    meta: dict[str, str] = {}
    if not m:
        return meta
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta


def _existing_source_urls() -> set[str]:
    """Normalized `source_url` of every draft + published file (what's already
    covered or queued)."""
    seen = set()
    for d in (PUBLISHED_DIR, DRAFTS_DIR):
        if not d.is_dir():
            continue
        for f in d.glob("*.md"):
            meta = _read_frontmatter(f.read_text(encoding="utf-8"))
            u = meta.get("source_url", "")
            if u:
                seen.add(_normalize_url(u))
    return seen


def _harvest_links() -> list[tuple[str, str]]:
    """Collect (title, url) from `## Related links` / `## Sources` across all
    published articles, SKIPPING any file already stamped `ai_provider:
    linkqueue` (depth-1 guard)."""
    out: list[tuple[str, str]] = []
    if not PUBLISHED_DIR.is_dir():
        return out
    for f in sorted(PUBLISHED_DIR.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        meta = _read_frontmatter(text)
        if meta.get("ai_provider", "") == MARKER:
            continue  # don't let candidates spawn candidates
        for sec in _SECTION_RE.finditer(text):
            for bm in _BULLET_RE.finditer(sec.group(1)):
                title = bm.group(1).strip()
                url = bm.group(2).strip()
                out.append((title, url))
    return out


# --- Seen-set persistence --------------------------------------------------
def _load_seen() -> set[str]:
    if SEEN_PATH.exists():
        try:
            data = json.loads(SEEN_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return set(data.get("seen", []))
            if isinstance(data, list):
                return set(data)
        except (json.JSONDecodeError, OSError):
            pass
    return set()


def _save_seen(seen: set[str]) -> None:
    SEEN_PATH.write_text(
        json.dumps({"seen": sorted(seen)}, indent=2) + "\n", encoding="utf-8"
    )


# --- Stub writing ----------------------------------------------------------
def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:60].rstrip("-") or "candidate"


def _unique_path(slug: str) -> Path:
    """`content/drafts/2026-06-08-<slug>.md`, suffixing -2, -3 ... on collision
    so two different links with the same slug don't clobber each other."""
    base = f"{TODAY}-{slug}"
    candidate = DRAFTS_DIR / f"{base}.md"
    n = 2
    while candidate.exists():
        candidate = DRAFTS_DIR / f"{base}-{n}.md"
        n += 1
    return candidate


def _write_stub(title: str, url: str) -> Path:
    """Write one draft stub matching the existing draft frontmatter format.
    Keys mirror the documented schema; unknown fields are left blank."""
    headline = title.replace('"', "'").strip()
    source = _domain(url)
    path = _unique_path(_slugify(headline))
    body = (
        "---\n"
        "status: draft\n"
        f'headline: "{headline}"\n'
        f'source: "{source}"\n'
        f'source_url: "{url}"\n'
        "license: press\n"
        f'published: "{TODAY}T00:00:00-05:00"\n'
        "focus: []\n"
        "tags: []\n"
        'location: ""\n'
        'image: ""\n'
        'video_url: ""\n'
        'media_kind: ""\n'
        f"ai_provider: {MARKER}\n"
        "---\n\n"
        f"# {headline}\n\n"
        "**TL;DR:** Candidate story surfaced from related coverage — "
        "review and deepen.\n\n"
        "Surfaced automatically from a `Related links` / `Sources` reference in "
        "an existing article. Run the article workflow to research and expand "
        "this stub before approving.\n\n"
        f"[Read the source at {source} →]({url})\n"
    )
    path.write_text(body, encoding="utf-8")
    return path


# --- Public entry point ----------------------------------------------------
def build_candidates(limit: int = 12) -> int:
    """Harvest newsworthy links from published articles and write up to `limit`
    new draft stubs. Returns the number of stubs written; prints skip counts so
    nothing is silently dropped. Idempotent across runs."""
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    seen = _load_seen()                 # persistent normalized-url set
    covered = _existing_source_urls()   # already a draft/published source_url

    skips = {
        "not_relevant": 0,
        "already_covered": 0,
        "known_feed": 0,
        "reference_page": 0,
        "seen_before": 0,
        "dup_in_run": 0,
    }

    raw = _harvest_links()
    candidates: list[tuple[str, str]] = []
    run_norms: set[str] = set()

    for title, url in raw:
        norm = _normalize_url(url)

        if norm in run_norms:
            skips["dup_in_run"] += 1
            continue
        if norm in covered:
            skips["already_covered"] += 1
            continue
        if _is_known_feed(url):
            skips["known_feed"] += 1
            continue
        if not _is_relevant(title, url):
            skips["not_relevant"] += 1
            continue
        is_ref, _reason = _is_reference_page(title, url)
        if is_ref:
            skips["reference_page"] += 1
            continue
        if norm in seen:
            skips["seen_before"] += 1
            continue

        run_norms.add(norm)
        candidates.append((title, url))

    written = 0
    written_paths: list[str] = []
    for title, url in candidates:
        if written >= limit:
            break
        path = _write_stub(title, url)
        seen.add(_normalize_url(url))
        written += 1
        written_paths.append(path.name)

    # Persist seen-set. Only the stubs we actually WROTE are marked seen; any
    # eligible candidate deferred over the limit stays unseen so the next run
    # picks it up. (Written stubs are also covered by the source_url check, so
    # this is belt-and-suspenders against duplicates.)
    _save_seen(seen)

    total_raw = len(raw)
    print(f"[linkqueue] harvested {total_raw} links from published articles")
    print(f"[linkqueue] wrote {written} new draft stub(s) (limit={limit})")
    print("[linkqueue] skipped:")
    for k, v in skips.items():
        print(f"    {k:16} {v}")
    over_limit = max(0, len(candidates) - written)
    if over_limit:
        print(f"    {'over_limit':16} {over_limit} (eligible, deferred to next run)")
    if written_paths:
        print("[linkqueue] new stubs:")
        for name in written_paths:
            print(f"    content/drafts/{name}")

    return written


if __name__ == "__main__":  # pragma: no cover
    import sys

    _lim = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    build_candidates(limit=_lim)
