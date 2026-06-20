"""Render drafts (review queue) and build the HTML preview.

Draft markdown uses YAML-style frontmatter so it's drop-in compatible with
an Astro content collection later — but for now a zero-dependency Python
renderer turns the *published* files into a browsable index.html.
"""
from __future__ import annotations

import html
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from . import geo, media
from .models import Item
from .sources import FOCUS_AREAS


def _updated_stamp() -> str:
    """The masthead 'Updated' time, shown in Chesterfield local (Eastern) time."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M %Z")
    except Exception:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

ROOT = Path(__file__).resolve().parents[2]
DRAFTS = ROOT / "content" / "drafts"
PUBLISHED = ROOT / "content" / "published"
REGIONAL = ROOT / "content" / "regional"   # Virginia/regional track (separate page)
PUBLIC = ROOT / "public"


def _yaml_escape(s: str) -> str:
    return '"' + (s or "").replace('"', '\\"') + '"'


def write_draft(item: Item) -> Path:
    """Write one item as a draft markdown file. status: draft means it will
    NOT appear on the site until you change it to published (or move the file
    to content/published/)."""
    DRAFTS.mkdir(parents=True, exist_ok=True)
    date = (item.published or item.fetched_at)[:10]
    fname = f"{date}-{item.slug}.md"
    path = DRAFTS / fname
    if path.exists():
        return path
    labels = [FOCUS_AREAS[f][0] for f in item.focus if f in FOCUS_AREAS]
    fm = [
        "---",
        f"status: draft",
        f"headline: {_yaml_escape(item.ai_headline or item.title)}",
        f"source: {_yaml_escape(item.source_name)}",
        f"source_url: {_yaml_escape(item.url)}",
        f"license: {item.license}",
        f"track: {item.track}",
        f"published: {_yaml_escape(item.published)}",
        f"focus: [{', '.join(labels)}]",
        f"tags: [{', '.join(item.tags)}]",
        f"location: {_yaml_escape(item.location)}",
        f"image: {_yaml_escape(item.image)}",
        f"video_url: {_yaml_escape(item.video_url)}",
        f"media_kind: {item.media_kind}",
        f"ai_provider: {item.ai_provider}",
        "---",
        "",
        f"# {item.ai_headline or item.title}",
        "",
    ]
    if item.ai_tldr:
        fm += [f"**TL;DR:** {item.ai_tldr}", ""]
    fm += [item.ai_summary or "", ""]
    if item.ai_why:
        fm += ["**Why it matters:** " + item.ai_why, ""]
    fm += [f"[Read the source at {item.source_name} →]({item.url})", ""]
    path.write_text("\n".join(fm), encoding="utf-8")
    return path


TIMELINE_HEADER = "## Development timeline"


def format_timeline(data: dict) -> str:
    """Render a researched timeline dict into a markdown section."""
    lines = ["", TIMELINE_HEADER, ""]
    for ev in data.get("events", []):
        date = ev.get("date", "").strip()
        title = ev.get("title", "").strip()
        detail = ev.get("detail", "").strip()
        url = ev.get("source_url", "").strip()
        line = f"- **{date}** — {title}"
        if detail:
            line += f": {detail}"
        if url:
            line += f" [[source]]({url})"
        lines.append(line)
    summary = data.get("summary", "").strip()
    if summary:
        lines += ["", f"_{summary}_"]
    lines.append("")
    return "\n".join(lines)


def append_timeline(md_path: Path, data: dict) -> bool:
    """Append a timeline section to a draft/published markdown file.
    Returns False if one is already present (idempotent)."""
    text = md_path.read_text(encoding="utf-8")
    if TIMELINE_HEADER in text:
        return False
    md_path.write_text(text.rstrip() + "\n" + format_timeline(data), encoding="utf-8")
    return True


def _paragraphs(text: str) -> list[str]:
    """Split a block into paragraphs on blank lines / hard breaks."""
    text = (text or "").strip()
    parts = re.split(r"\n\s*\n", text) if "\n" in text else [text]
    return [p.strip().replace("\n", " ") for p in parts if p.strip()]


def format_article(headline: str, source_name: str, source_url: str, data: dict) -> str:
    """Build the full long-form article body markdown from a write_article dict."""
    out = [f"# {headline}", ""]
    if data.get("tldr"):
        out += [f"**TL;DR:** {data['tldr']}", ""]
    qf = data.get("quick_facts") or {}
    qf_rows = [(label, (qf.get(key) or "").strip())
               for key, label in (("who", "Who"), ("what", "What"),
                                  ("when", "When"), ("where", "Where"))]
    qf_rows = [(label, val) for label, val in qf_rows if val]
    if qf_rows:
        out += ["## Quick facts", ""]
        for label, val in qf_rows:
            out.append(f"- **{label}:** {val}")
        out.append("")
    if data.get("detail"):
        out += ["## The story", ""]
        out += [p for para in _paragraphs(data["detail"]) for p in (para, "")]
    if data.get("key_players"):
        players = [((p.get("name") or "").strip(), (p.get("role") or "").strip())
                   for p in data["key_players"]]
        players = [(n, r) for n, r in players if n]
        if players:
            out += ["## Key players", ""]
            for name, role in players:
                out.append(f"- **{name}:** {role}" if role else f"- **{name}**")
            out.append("")
    if data.get("key_dates"):
        out += ["## Key dates", ""]
        for kd in data["key_dates"]:
            d, w = kd.get("date", "").strip(), kd.get("what", "").strip()
            out.append(f"- **{d}:** {w}" if d else f"- {w}")
        out.append("")
    if data.get("case_for"):
        out += ["## The case for", "", data["case_for"].strip(), ""]
    if data.get("case_against"):
        out += ["## The case against", "", data["case_against"].strip(), ""]
    if data.get("why_it_matters"):
        out += [f"**Why it matters:** {data['why_it_matters'].strip()}", ""]
    if data.get("places"):
        out += ["## Places", ""]
        for pl in data["places"]:
            pl = pl.strip()
            if pl:
                q = pl.replace(" ", "+") + "+Chesterfield+VA"
                out.append(f"- [{pl}](https://www.openstreetmap.org/search?query={q})")
        out.append("")
    if data.get("events"):
        out.append(format_timeline({"events": data["events"], "summary": ""}).strip())
        out.append("")
    if data.get("related_links"):
        out += ["## Related links", ""]
        for s in data["related_links"]:
            title = (s.get("title") or s.get("url", "")).strip()
            url = s.get("url", "").strip()
            if url:
                out.append(f"- [{title}]({url})")
        out.append("")
    if source_url:
        out += [f"[Read the original at {source_name} →]({source_url})", ""]
    if data.get("sources"):
        out += ["## Sources", ""]
        for s in data["sources"]:
            title = (s.get("title") or s.get("url", "")).strip()
            url = s.get("url", "").strip()
            if url:
                out.append(f"- [{title}]({url})")
        out.append("")
    return "\n".join(out)


def write_full_article(md_path: Path, data: dict) -> None:
    """Replace a draft/published file's BODY with the full long-form article,
    preserving its frontmatter verbatim."""
    text = md_path.read_text(encoding="utf-8")
    meta, _ = _parse_frontmatter(text)
    # Preserve the exact frontmatter block (between the first two '---').
    fm_block = text.split("---", 2)[1] if text.startswith("---") else ""
    headline = meta.get("headline") or md_path.stem
    body = format_article(headline, meta.get("source", ""), meta.get("source_url", ""), data)
    md_path.write_text(f"---{fm_block}---\n\n{body}", encoding="utf-8")
    updates = {}
    if data.get("tags"):
        updates["tags"] = f"[{', '.join(data['tags'])}]"
    if data.get("location"):
        updates["location"] = _yaml_escape(data["location"])
    if updates:
        update_frontmatter(md_path, updates)


# --- Publishing -----------------------------------------------------------

def _parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    _, fm, body = text.split("---", 2)
    meta = {}
    for line in fm.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta, body.strip()


def update_frontmatter(md_path: Path, updates: dict) -> None:
    """Set/insert keys in a file's YAML frontmatter, preserving the body."""
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return
    _, fm, body = text.split("---", 2)
    lines = fm.strip("\n").splitlines()
    seen, out = set(), []
    for ln in lines:
        key = ln.split(":", 1)[0].strip() if ":" in ln else None
        if key in updates:
            out.append(f"{key}: {updates[key]}")
            seen.add(key)
        else:
            out.append(ln)
    for k, v in updates.items():
        if k not in seen:
            out.append(f"{k}: {v}")
    md_path.write_text(f"---\n" + "\n".join(out) + f"\n---{body}", encoding="utf-8")


# Map a human focus label ("Fire & EMS") to a CSS-safe category slug.
_LABEL_TO_SLUG = {label: key for key, (label, _kw) in FOCUS_AREAS.items()}


def _focus_slug(label: str) -> str:
    return _LABEL_TO_SLUG.get(label, re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-"))


# Neon focus-area colors shared by the map markers + board accents. Keyed by
# the focus slug; these match the glowing chip palette in _TEMPLATE.
FOCUS_COLORS = {
    "growth":     "#ffc94a",
    "schools":    "#5ec4ff",
    "police":     "#7c96ff",
    "fire":       "#ff5d72",
    "business":   "#8cf06a",
    "government": "#27e6c6",
    "community":  "#ff479e",
    "weather":    "#b08cff",
}
_DEFAULT_FOCUS_COLOR = "#27e6c6"


def _focus_color(slug: str) -> str:
    return FOCUS_COLORS.get(slug, _DEFAULT_FOCUS_COLOR)


def _primary_focus(meta: dict) -> tuple[str, str]:
    """Return (slug, label) for a story's primary focus area, defaulting to
    Community when none is set."""
    labels = [x.strip() for x in meta.get("focus", "").strip("[]").split(",") if x.strip()]
    if not labels:
        return "community", "Community"
    return _focus_slug(labels[0]), labels[0]


_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _pretty_date(iso: str) -> str:
    """'2026-05-22' -> 'May 22, 2026'. Falls back to the raw string."""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    if not m:
        return iso
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not 1 <= mo <= 12:
        return iso
    return f"{_MONTHS[mo - 1]} {d}, {y}"


def _inline(line: str) -> str:
    line = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', line)
    line = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", line)
    line = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"<em>\1</em>", line)
    return line


_TIMELINE_TITLE = "Development timeline"
_QUICKFACTS_TITLE = "Quick facts"


_CASE_HEADINGS = {"the case for": "case-for", "the case against": "case-against"}


def _md_to_html(body: str) -> str:
    """Convert a story body to HTML.

    Special sections get richer markup:
      * "Development timeline" -> an <ol class="timeline"> with dated nodes.
      * "The case for" / "The case against" -> styled perspective boxes.
      * a leading "**TL;DR:** ..." paragraph -> a callout.
    """
    html, in_list = [], False
    box = None  # None | "timeline" | "case-for" | "case-against" | "quick-facts"

    def close_list():
        nonlocal in_list
        if in_list:
            html.append("</ol>" if box == "timeline" else "</ul>")
            in_list = False

    def close_box():
        nonlocal box
        close_list()
        if box:
            html.append("</div></section>")
            box = None

    for line in body.splitlines():
        line = line.rstrip()
        if not line:
            continue

        if line.startswith("- "):
            if not in_list:
                if box == "timeline":
                    html.append('<ol class="timeline">')
                elif box == "quick-facts":
                    html.append('<ul class="qf-list">')
                else:
                    html.append("<ul>")
                in_list = True
            item = _inline(line[2:])
            if box == "timeline":
                m = re.match(r"\s*<strong>(.*?)</strong>\s*[—-]\s*(.*)", item, re.S)
                if m:
                    date, rest = m.group(1).strip(), m.group(2).strip()
                    html.append(
                        '<li class="tl-event">'
                        f'<span class="tl-date">{date}</span>'
                        f'<div class="tl-body">{rest}</div></li>'
                    )
                else:
                    html.append(f'<li class="tl-event"><div class="tl-body">{item}</div></li>')
            else:
                html.append(f"<li>{item}</li>")
            continue

        close_list()

        if line.startswith("## "):
            title = line[3:].strip()
            low = title.lower()
            close_box()
            if low == _TIMELINE_TITLE.lower():
                box = "timeline"
                html.append(
                    '<section class="timeline-section" aria-label="Development timeline">'
                    f'<h3 class="timeline-heading">{_inline(title)}</h3>'
                    '<div class="timeline-wrap">'
                )
            elif low in _CASE_HEADINGS:
                box = _CASE_HEADINGS[low]
                html.append(
                    f'<section class="case {box}" aria-label="{title}">'
                    f'<h3 class="case-heading">{_inline(title)}</h3>'
                    '<div class="case-body">'
                )
            elif low == _QUICKFACTS_TITLE.lower():
                box = "quick-facts"
                html.append(
                    '<section class="quick-facts" aria-label="Quick facts">'
                    f'<h3 class="qf-heading">{_inline(title)}</h3>'
                    '<div class="qf-wrap">'
                )
            else:
                html.append(f"<h3>{_inline(title)}</h3>")
        elif line.startswith("# "):
            close_box()
            html.append(f'<h2>{_inline(line[2:])}</h2>')
        else:
            text = _inline(line)
            if box == "timeline" and text.startswith("<em>") and text.endswith("</em>"):
                html.append(f'<p class="timeline-summary">{text}</p>')
            elif box is None and text.startswith("<strong>TL;DR"):
                html.append(f'<p class="tldr">{text}</p>')
            else:
                html.append(f"<p>{text}</p>")

    close_box()
    return "\n".join(html)


def _map_embed(lat: float, lon: float, label: str) -> str:
    """Keyless OpenStreetMap embed with a marker, plus a 'larger map' link."""
    d = 0.0045  # ~500m bounding box
    bbox = f"{lon - d}%2C{lat - d}%2C{lon + d}%2C{lat + d}"
    src = (f"https://www.openstreetmap.org/export/embed.html?"
           f"bbox={bbox}&layer=mapnik&marker={lat}%2C{lon}")
    big = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=16/{lat}/{lon}"
    cap = f'<figcaption class="map-cap">📍 {label}</figcaption>' if label else ""
    return (
        '<figure class="map-embed">'
        f'<iframe title="Map: {label}" loading="lazy" '
        f'src="{src}"></iframe>{cap}'
        f'<a class="map-link" href="{big}" target="_blank" rel="noopener">'
        'View larger map ↗</a></figure>'
    )


_VENUE_RE = re.compile(
    r"\b(park|sportsplex|center|centre|school|library|complex|stadium|arena|"
    r"museum|recreation|fairgrounds|campus|hall|courthouse)\b", re.IGNORECASE)


def _is_multi_location(loc: str) -> bool:
    """True if the location string names several distinct venues (e.g. a weekly
    events roundup) — a single map pin would be misleading, so skip the map."""
    parts = [p.strip() for p in loc.split(",") if p.strip()]
    return sum(1 for p in parts if _VENUE_RE.search(p)) >= 2


# Chesterfield County bounding box. Any pin outside it is a bad geocode (wrong
# state, or Nominatim's "center of the USA" fallback) and is never mapped.
_MAP_BBOX = (36.9, 37.8, -78.1, -77.2)  # lat_min, lat_max, lon_min, lon_max


def _in_chesterfield(lat, lon) -> bool:
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return False
    return _MAP_BBOX[0] <= lat <= _MAP_BBOX[1] and _MAP_BBOX[2] <= lon <= _MAP_BBOX[3]


def _resolve_map(meta: dict) -> str:
    """Return map HTML for a post, geocoding the location if needed (cached).
    Only renders for a single, specific location inside Chesterfield County."""
    label = meta.get("location", "").strip().strip('"\\ ')
    # Skip empty, multi-venue, or junk labels (no real letters, e.g. a stray quote).
    if not label or _is_multi_location(label) or not re.search(r"[A-Za-z]", label):
        return ""
    lat, lon = meta.get("lat", "").strip(), meta.get("lon", "").strip()
    if lat and lon and _in_chesterfield(lat, lon):
        try:
            return _map_embed(float(lat), float(lon), label)
        except ValueError:
            pass
    # Stored coords missing or outside the county: (re)geocode (geo.geocode itself
    # rejects out-of-bbox results, so a bad label simply yields no map).
    g = geo.geocode(label)
    if g and _in_chesterfield(g["lat"], g["lon"]):
        return _map_embed(g["lat"], g["lon"], label)
    return ""


_DRAFT_BANNER = (
    '<div style="background:#b5462f;color:#fff;padding:.85rem 1.1rem;'
    'border-radius:10px;margin-bottom:1.4rem;font-weight:600;line-height:1.5">'
    'DRAFT PREVIEW &mdash; nothing here is published yet. Edit files in '
    '<code style="background:rgba(255,255,255,.2);padding:0 .3rem;border-radius:4px">'
    'content/drafts/</code>, then approve with '
    '<code style="background:rgba(255,255,255,.2);padding:0 .3rem;border-radius:4px">'
    'python run.py promote &lt;file&gt;</code> (or delete a file to reject it).'
    "</div>"
)


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-") or "x"


SITE_URL = "https://chesterfieldreport.com"


def story_url(headline: str) -> str:
    """Relative URL of a story's own page: /story/<slug>.html."""
    return f"/story/{slugify(headline)}.html"


def _focus_of(meta: dict) -> tuple[list, list]:
    """Return (labels, slugs) for a record's focus areas."""
    labels = [f.strip() for f in meta.get("focus", "").strip("[]").split(",") if f.strip()]
    return labels, [_focus_slug(l) for l in labels]


def _chips_html(meta: dict, link: bool) -> str:
    labels, slugs = _focus_of(meta)
    op = ('<span class="chip op-chip">Opinion</span>'
          if (meta.get("opinion", "") or "").strip().lower() in ("true", "1", "yes") else "")
    return op + "".join(
        (f'<a class="chip" data-cat="{s}" href="/topics/{s}.html">{l}</a>'
         if link else f'<span class="chip" data-cat="{s}">{l}</span>')
        for l, s in zip(labels, slugs)
    )


def _eligible_tag_slugs() -> set:
    """Slugs that have a real topic page: every focus slug (always built) plus
    any tag shared by >=2 published stories. Mirrors build_topics()'s threshold
    so tag chips never link to a page that wasn't generated."""
    from collections import Counter
    counts: Counter = Counter()
    focus: set = set()
    for meta, _body, _name in _published_records():
        # Count DISTINCT stories per slug (dedup tags within a story), exactly
        # like build_topics() dedups its recs by story name — otherwise a story
        # that repeats a tag inflates the count and links to a page that was
        # never built.
        seen: set = set()
        for t in [x.strip() for x in meta.get("tags", "").strip("[]").split(",") if x.strip()]:
            s = slugify(t)
            if s not in seen:
                seen.add(s)
                counts[s] += 1
        for l in [x.strip() for x in meta.get("focus", "").strip("[]").split(",") if x.strip()]:
            focus.add(_focus_slug(l))
    return focus | {s for s, n in counts.items() if n >= 2}


def _tagrow_html(meta: dict, link: bool) -> str:
    tags = [t.strip() for t in meta.get("tags", "").strip("[]").split(",") if t.strip()]
    if not tags:
        return ""
    eligible = _eligible_tag_slugs() if link else set()
    chips = []
    for t in tags:
        s = slugify(t)
        if link and s in eligible:
            chips.append(f'<a class="tag" href="/topics/{s}.html">#{t}</a>')
        else:
            chips.append(f'<span class="tag">#{t}</span>')
    return '<div class="tagrow">' + "".join(chips) + "</div>"


def _meta_line(meta: dict) -> str:
    src = meta.get("source", "")
    date_iso = meta.get("published", "")[:10]
    return (f'<div class="meta"><span class="meta-source">{src}</span>'
            f'<span class="meta-dot">&middot;</span>'
            f'<time datetime="{date_iso}">{_pretty_date(date_iso)}</time></div>')


def _full_card(meta: dict, body: str, name: str, draft_mode: bool) -> str:
    """A card that contains the FULL story body (used by the draft preview)."""
    link = not draft_mode
    data_focus = " ".join(_focus_of(meta)[1])
    story_html = _md_to_html(body)
    map_html = _resolve_map(meta)
    if map_html and "</h2>" in story_html:
        story_html = story_html.replace("</h2>", "</h2>" + map_html, 1)
    elif map_html:
        story_html += map_html
    fname = (f'<div style="font-family:ui-monospace,monospace;font-size:.74rem;'
             f'color:#b5462f;margin-bottom:.45rem">📝 {name}</div>'
             if draft_mode else "")
    hero = media_html(meta, big=True)
    hid = slugify(meta.get("headline", "") or name)
    return (
        f'<article class="card" id="{hid}" data-focus="{data_focus}">'
        f"{hero}{fname}"
        f'<div class="card-tags">{_chips_html(meta, link)}</div>'
        f"{_meta_line(meta)}"
        f"{story_html}{_tagrow_html(meta, link)}</article>"
    )


# ---------------------------------------------------------------------------
# Design-system (cr-*) presentational helpers — the "bioluminescent-cyberpunk"
# magazine layout: HUD cards with photo-frames, a hero, and a sidebar rail.
# ---------------------------------------------------------------------------

# Focus area -> design "tone" (drives accent rail, badge, and photo duotone).
_TONE_BY_SLUG = {
    "government": "civic", "police": "breaking", "fire": "breaking",
    "growth": "teal", "business": "teal", "schools": "teal",
    "community": "eco", "weather": "eco",
}
_TONE_VAR = {
    "teal": "var(--neon-teal)", "breaking": "var(--neon-magenta)",
    "civic": "var(--neon-amber)", "eco": "var(--river-green)",
}
_TONE_GRAD = {
    "teal": "linear-gradient(135deg,#0a2a30,#06141a 72%)",
    "breaking": "linear-gradient(135deg,#2a0a1e,#06141a 72%)",
    "civic": "linear-gradient(135deg,#2a2410,#06141a 72%)",
    "eco": "linear-gradient(135deg,#102612,#06141a 72%)",
}
_WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def _tone_of(meta: dict) -> str:
    return _TONE_BY_SLUG.get(_primary_focus(meta)[0], "teal")


def _story_image(meta: dict) -> str:
    img = (meta.get("image") or "").strip()
    if not img:
        img = media.og_image((meta.get("source_url") or "").strip())
    return img


def _photo_frame(meta: dict, tone: str, caption: str, ratio: str, overlay: str = "") -> str:
    """Photo-frame: a real og:image when the story has one, otherwise a duotone
    gradient with the heron logo mark centered as the brand fallback."""
    img = _story_image(meta)
    if img:
        bg = f"#06141a center/cover no-repeat url('{img}')"
        fallback = ""
        cls = "cr-photo"
    else:
        bg = _TONE_GRAD.get(tone, _TONE_GRAD["teal"])
        fallback = ('<img class="cr-photo__logo" src="/assets/logo-mark.svg" '
                    'alt="" aria-hidden="true" loading="lazy">')
        # Tag image-less frames so the light theme can lighten them (the tone
        # gradient is an inline style, so only an !important rule on this class
        # can override it — and real images stay untouched).
        cls = "cr-photo cr-photo--fallback"
    # Aspect-ratio is set via CSS (.cr-story/.cr-hero .cr-photo) so it can adapt
    # responsively — inline styles would beat the stylesheet on mobile.
    return (
        '<div class="' + cls + '" style="background:' + bg + '">'
        '<div class="cr-photo__grid"></div><div class="cr-photo__scan"></div>'
        '<span class="cr-photo__b cr-photo__b--tl"></span>'
        '<span class="cr-photo__b cr-photo__b--br"></span>'
        + fallback + overlay +
        '<span class="cr-photo__cap">' + caption + '</span></div>'
    )


def _cr_badge(text: str, tone: str, dot: bool = False) -> str:
    d = '<span class="cr-badge__dot" aria-hidden="true"></span>' if dot else ""
    return '<span class="cr-badge cr-badge--' + tone + '">' + d + text + '</span>'


def _cr_meta(meta: dict) -> str:
    date_iso = meta.get("published", "")[:10]
    src = meta.get("source", "")
    src_html = '<span class="cr-meta__by">' + src + '</span>' if src else ""
    return '<div class="cr-meta"><span>' + _pretty_date(date_iso) + '</span>' + src_html + '</div>'


def _weekday_abbr(iso: str) -> str:
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    if not m:
        return "—"
    try:
        wd = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).weekday()
    except ValueError:
        return "—"
    return _WEEKDAYS[wd]


def _summary_card(meta: dict, body: str, name: str) -> str:
    """A HUD story card (cr-story): photo-frame, beat badge, headline, dek, meta.
    The whole card links to the story page."""
    data_focus = " ".join(_focus_of(meta)[1])
    headline = meta.get("headline", "") or name
    url = story_url(headline)
    tone = _tone_of(meta)
    _slug, label = _primary_focus(meta)
    tldr = _tldr_from_body(body)
    dek = '<p class="cr-story__dek">' + _inline(tldr) + '</p>' if tldr else ""
    hid = slugify(headline)
    return (
        '<a class="cr-card cr-card--accent cr-card--interactive cr-card--bracket '
        'cr-story cr-story--md" id="' + hid + '" data-focus="' + data_focus + '" '
        'style="--accent-color:' + _TONE_VAR[tone] + ';display:flex;text-decoration:none" '
        'href="' + url + '">'
        + _photo_frame(meta, tone, "PHOTO · " + label.upper(), "16 / 9")
        + '<div class="cr-story__body">'
        + _cr_badge(label, tone, dot=(tone == "breaking"))
        + '<h3 class="cr-story__title">' + headline + '</h3>'
        + dek + _cr_meta(meta)
        + '</div></a>'
    )


# Impact weights for choosing the homepage lead, keyed by primary focus slug.
# Civic and public-safety news leads over softer community items.
_HERO_WEIGHT = {
    "government": 5, "police": 4, "fire": 4, "growth": 4,
    "schools": 4, "weather": 3, "business": 2, "community": 1,
}


def _hero_score(meta: dict, rank: int) -> float:
    """Impact score for the homepage lead (higher wins). Favors civic and
    public-safety beats, breaking tone, and stories with a real photo (the
    hero is a large image card), with a gentle recency penalty so the lead
    stays current. Uses the BEST beat among the story's focus tags, not just the
    first one the model listed, so a major story tagged e.g. [Local Business,
    Government] is scored as the government story it actually is."""
    _labels, slugs = _focus_of(meta)
    score = float(max((_HERO_WEIGHT.get(s, 2) for s in slugs), default=2))
    if _tone_of(meta) == "breaking":
        score += 2
    if _story_image(meta):
        score += 3
    return score - rank * 0.6


def _pick_hero_index(records: list, window: int = 8) -> int:
    """Index of the highest-impact recent story to feature as the lead, chosen
    from the most recent `window` records (they arrive newest-first)."""
    best, best_score = 0, None
    for i in range(min(window, len(records))):
        sc = _hero_score(records[i][0], i)
        if best_score is None or sc > best_score:
            best, best_score = i, sc
    return best


def _hero_card(meta: dict, body: str, name: str) -> str:
    """The lead story: a 21:9 photo-frame with an overlaid headline + dek."""
    headline = meta.get("headline", "") or name
    url = story_url(headline)
    tone = _tone_of(meta)
    _slug, label = _primary_focus(meta)
    tldr = _tldr_from_body(body)
    dek = '<p class="cr-hero__dek">' + _inline(tldr) + '</p>' if tldr else ""
    overlay = (
        '<div class="cr-hero__overlay">'
        + _cr_badge(label, tone, dot=(tone == "breaking"))
        + '<h1 class="cr-hero__title">' + headline + '</h1>'
        + dek + _cr_meta(meta)
        + '</div>'
    )
    return (
        '<a class="cr-card cr-card--accent cr-card--interactive cr-card--bracket cr-hero" '
        'style="--accent-color:' + _TONE_VAR[tone] + ';display:block;text-decoration:none" '
        'href="' + url + '">'
        + _photo_frame(meta, tone, "PHOTO · " + label.upper(), "21 / 9", overlay=overlay)
        + '</a>'
    )


def _sechead(kicker: str, title: str, action: str = "") -> str:
    return (
        '<div class="cr-sechead"><div>'
        '<div class="cr-sechead__kicker">' + kicker + '</div>'
        '<h2 class="cr-sechead__title">' + title + '</h2></div>'
        + action + '</div>'
    )


def _trending_tags(records: list, n: int = 8) -> list:
    from collections import Counter
    eligible = _eligible_tag_slugs()
    counts: Counter = Counter()
    label_for: dict = {}
    for meta, _body, _name in records:
        for t in [x.strip() for x in meta.get("tags", "").strip("[]").split(",") if x.strip()]:
            s = slugify(t)
            if s in eligible:
                counts[s] += 1
                label_for.setdefault(s, t)
    return [(label_for[s], s) for s, _c in counts.most_common(n)]


def _home_sidebar(records: list) -> str:
    """The sticky right rail: This Week digest, newsletter CTA, trending tags."""
    items = []
    for meta, _body, name in records[:7]:
        headline = meta.get("headline", "") or name
        url = story_url(headline)
        tone = _tone_of(meta)
        _slug, label = _primary_focus(meta)
        day = _weekday_abbr(meta.get("published", "")[:10])
        items.append(
            '<li class="cr-twrail__item">'
            '<span class="cr-twrail__day cr-twrail__day--' + tone + '">' + day + '</span>'
            '<div><div class="cr-twrail__label">' + label + '</div>'
            '<a class="cr-twrail__title" href="' + url + '" style="text-decoration:none">'
            + headline + '</a></div></li>'
        )
    twrail = (
        '<div class="cr-card cr-card--grad cr-twrail">'
        '<div class="cr-twrail__head">'
        '<span class="cr-twrail__kicker">// This Week in Chesterfield</span>'
        '<a class="cr-twrail__all" href="/digest.html" style="text-decoration:none">Full digest</a>'
        '</div><ul class="cr-twrail__list">' + "".join(items) + '</ul></div>'
    )
    chips = "".join(
        '<a class="cr-tag" href="/topics/' + s + '.html" style="text-decoration:none">'
        '<span class="cr-tag__hash">#</span>' + t + '</a>'
        for t, s in _trending_tags(records, 8)
    )
    trending = (
        '<div class="cr-card cr-card--grad cr-card--pad cr-trend">'
        '<span class="cr-twrail__kicker">// Trending tags</span>'
        '<div class="cr-trend__tags">' + chips + '</div></div>'
    ) if chips else ""
    return '<aside class="cr-home__side">' + twrail + trending + '</aside>'


def _filter_links(records: list) -> str:
    """Topic filter bar for published pages: links (not JS buttons) to topic
    pages, with per-focus story counts. 'All' -> homepage."""
    present, counts = {}, {}
    for meta, body, name in records:
        labels, slugs = _focus_of(meta)
        for l, s in zip(labels, slugs):
            present.setdefault(s, l)
        for s in set(slugs):
            counts[s] = counts.get(s, 0) + 1
    order = [v[0] for v in FOCUS_AREAS.values()]
    ordered = sorted(present.items(),
                     key=lambda kv: order.index(kv[1]) if kv[1] in order else 99)
    btns = [f'<a class="filter is-active" href="/">'
            f'All <span class="fcount">{len(records)}</span></a>']
    for slug, label in ordered:
        btns.append(
            f'<a class="filter" data-cat="{slug}" href="/topics/{slug}.html">'
            f'{label} <span class="fcount">{counts.get(slug, 0)}</span></a>'
        )
    return ('<nav class="filterbar" aria-label="Filter stories by topic">'
            + "".join(btns) + "</nav>")


def _pagination_nav(page: int, total_pages: int) -> str:
    """« Prev, numbered page links, Next » nav for the paginated index."""
    if total_pages <= 1:
        return ""

    def href(n: int) -> str:
        return "/" if n == 1 else f"/page/{n}.html"

    parts = ['<nav class="pagination" aria-label="Pagination">']
    if page > 1:
        parts.append(f'<a class="pg-prev" href="{href(page - 1)}">&laquo; Prev</a>')
    else:
        parts.append('<span class="pg-prev is-disabled">&laquo; Prev</span>')
    for n in range(1, total_pages + 1):
        if n == page:
            parts.append(f'<span class="pg-num is-current" aria-current="page">{n}</span>')
        else:
            parts.append(f'<a class="pg-num" href="{href(n)}">{n}</a>')
    if page < total_pages:
        parts.append(f'<a class="pg-next" href="{href(page + 1)}">Next &raquo;</a>')
    else:
        parts.append('<span class="pg-next is-disabled">Next &raquo;</span>')
    parts.append("</nav>")
    return "".join(parts)


def _render_page(records: list, out_path: Path, draft_mode: bool = False,
                 heading: str = "", top_html: str = "") -> Path:
    """Draft-preview renderer: one page, full story bodies, JS topic filter.

    The PUBLISHED index and topic pages no longer use this — they render
    summary cards via build_site()/build_topics()."""
    cards = [_full_card(meta, body, name, draft_mode) for meta, body, name in records]

    # Filter bar — order by the canonical FOCUS_AREAS sequence.
    present, counts = {}, {}
    for meta, body, name in records:
        labels, slugs = _focus_of(meta)
        for l, s in zip(labels, slugs):
            present.setdefault(s, l)
        for s in set(slugs):
            counts[s] = counts.get(s, 0) + 1
    order = [v[0] for v in FOCUS_AREAS.values()]
    ordered = sorted(present.items(), key=lambda kv: order.index(kv[1]) if kv[1] in order else 99)
    filter_btns = [f'<button class="filter is-active" data-filter="all" aria-pressed="true">'
                   f'All <span class="fcount">{len(records)}</span></button>']
    for slug, label in ordered:
        filter_btns.append(
            f'<button class="filter" data-cat="{slug}" data-filter="{slug}" aria-pressed="false">'
            f'{label} <span class="fcount">{counts.get(slug, 0)}</span></button>'
        )
    filter_bar = (
        '<nav class="filterbar" aria-label="Filter stories by topic">'
        + "".join(filter_btns)
        + "</nav>"
    )

    generated = _updated_stamp()
    empty_msg = ('<p class="empty">No drafts right now.</p>' if draft_mode
                 else '<p class="empty">No published stories yet. Approve some drafts to see them here.</p>')
    feed = "\n".join(cards) or empty_msg
    banner = _DRAFT_BANNER if draft_mode else ""
    head_html = f'<h1 class="page-title">{heading}</h1>' if heading else ""
    jsonld = ""
    if not draft_mode:
        from . import seo  # lazy: seo imports render, avoid circular import
        jsonld = seo.jsonld_site() + "".join(
            seo.jsonld_newsarticle(m, b) for m, b, n in records)
    body_html = (jsonld + banner + head_html + top_html + filter_bar
                 + f'<div class="feed" id="feed">{feed}</div>')
    page = _TEMPLATE.format(body=body_html, generated=generated, count=len(records))
    out_path.write_text(page, encoding="utf-8")
    return out_path


PER_PAGE = 10


_PROMO_CSS = """<style>
.cr-promo{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:1.5rem 0 2rem;}
.cr-promo a{display:flex;flex-direction:column;border:1px solid var(--border);border-radius:var(--radius-sm);overflow:hidden;background:var(--surface-card);text-decoration:none;transition:transform .12s ease,box-shadow .12s ease,border-color .12s ease;}
.cr-promo a:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(0,0,0,.10);border-color:var(--accent);}
.cr-promo .cr-promo-img{display:block;width:100%;height:108px;object-fit:cover;background:var(--surface-sunken,#eee);}
.cr-promo .cr-promo-b{padding:.6rem .8rem .85rem;}
.cr-promo h3{font:var(--fw-bold) var(--fs-md)/1.15 var(--font-display);margin:0;color:var(--text-primary);}
.cr-promo p{font:var(--fs-2xs)/1.35 var(--font-sans);color:var(--text-tertiary);margin:.2rem 0 0;}
@media (max-width:860px){.cr-promo{grid-template-columns:repeat(2,1fr);gap:10px;margin:1.1rem 0 1.4rem;}.cr-promo .cr-promo-img{height:80px;}.cr-promo .cr-promo-b{padding:.45rem .6rem .55rem;}.cr-promo h3{font-size:var(--fs-sm);}.cr-promo p{display:none;}}
</style>"""

_PROMO = [
    ("/board.html", "box-supervisors.jpg", "Board of Supervisors", "Meet your district reps"),
    ("/development.html", "box-development.jpg", "Development & Zoning", "Track growth near you"),
    ("/elections.html", "box-elections.jpg", "2026 Elections", "What&rsquo;s on your ballot"),
    ("/schools.html", "box-schools.jpg", "Schools", "Grades, maps &amp; contacts"),
]


def _promo_boxes() -> str:
    """A four-box 'Explore Chesterfield' strip for the homepage, below the lead."""
    cards = "".join(
        f'<a href="{href}"><img class="cr-promo-img" src="/assets/{img}" alt="" '
        f'loading="lazy" width="500" height="200">'
        f'<div class="cr-promo-b"><h3>{html.escape(title)}</h3><p>{sub}</p></div></a>'
        for href, img, title, sub in _PROMO)
    return (_PROMO_CSS
            + '<nav class="cr-promo" aria-label="Explore Chesterfield">' + cards + '</nav>')


def _render_index_pages(records: list, top_html: str = "") -> int:
    """Render the paginated PUBLISHED homepage from summary cards. Page 1 is
    public/index.html (with the This Week band on top); pages 2..N are
    public/page/N.html. Returns the number of pages written."""
    from . import seo  # lazy: seo imports render, avoid circular import
    total = len(records)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    filter_bar = _filter_links(records)
    page_dir = PUBLIC / "page"
    if total_pages > 1:
        page_dir.mkdir(parents=True, exist_ok=True)
    generated = _updated_stamp()
    site_jsonld = seo.jsonld_site()

    sidebar = _home_sidebar(records)
    filter_action = ('<a class="cr-btn cr-btn--secondary cr-btn--sm" href="/topics/" '
                     'style="text-decoration:none">Filter beats &rarr;</a>')

    for page in range(1, total_pages + 1):
        chunk = records[(page - 1) * PER_PAGE: page * PER_PAGE]
        jsonld = site_jsonld + "".join(
            seo.jsonld_newsarticle(m, b) for m, b, n in chunk)
        # Page 1 leads with a hero; the rest fill the two-column card grid.
        if page == 1 and chunk:
            hi = _pick_hero_index(chunk)
            hero = _hero_card(*chunk[hi])
            grid_recs = chunk[:hi] + chunk[hi + 1:]
        else:
            hero = ""
            grid_recs = chunk
        cards = [_summary_card(meta, body, name) for meta, body, name in grid_recs]
        grid = ("\n".join(cards)
                or '<p class="cr-topics__empty">No published stories yet. Approve some drafts to see them here.</p>')
        main = (
            hero
            + (_promo_boxes() if page == 1 else "")
            + _sechead("// The feed", "Across the county", filter_action)
            + '<div class="cr-home__grid feed" id="feed">' + grid + '</div>'
            + (_regional_home_module() if page == 1 else "")
            + _pagination_nav(page, total_pages)
        )
        body_html = (jsonld
                     + '<div class="cr-home"><div class="cr-home__main">' + main + '</div>'
                     + sidebar + '</div>')
        out = PUBLIC / "index.html" if page == 1 else page_dir / f"{page}.html"
        html = _TEMPLATE.format(body=body_html, generated=generated, count=total)
        # EN homepage <-> ES homepage toggle (paginated EN pages map to /es/).
        html = _inject_toggle(html, en_path="/", es_path="/es/", current="en")
        out.write_text(html, encoding="utf-8")
    return total_pages


def _collect(md_paths, include_drafts: bool) -> list:
    recs = []
    for md in md_paths:
        meta, body = _parse_frontmatter(md.read_text(encoding="utf-8"))
        if not include_drafts and meta.get("status") == "draft":
            continue
        recs.append((meta, body, md.name))
    return recs


def media_html(meta: dict, big: bool = True) -> str:
    """Hero media for a post: video thumbnail (with play badge) -> image ->
    best-effort og:image from the source page. Returns '' if nothing found."""
    img = (meta.get("image") or "").strip()
    video = (meta.get("video_url") or "").strip()
    if not img:
        img = media.og_image((meta.get("source_url") or "").strip())
    if not img:
        return ""
    cls = "hero" if big else "thumb"
    if video:
        return (f'<a class="media {cls} is-video" href="{video}" target="_blank" '
                f'rel="noopener"><img src="{img}" alt="" loading="lazy">'
                f'<span class="playbadge" aria-hidden="true">▶</span></a>')
    return f'<figure class="media {cls}"><img src="{img}" alt="" loading="lazy"></figure>'


# --- Reader reactions (static site, shared counts via Abacus) -------------
#
# Abacus (https://abacus.jasoncameron.dev) is a free, no-auth, CORS-enabled
# hit counter. /hit/{ns}/{key} increments + returns {"value":N}; /get/{ns}/{key}
# reads without incrementing. We key each reaction as "<slug>__<emoji-id>" under
# the namespace below. The JS fails gracefully: if the service errors the
# buttons still render (counts hidden), and localStorage prevents one browser
# from double-counting and highlights the visitor's pick.

REACT_NAMESPACE = "chesterfieldreport"
REACT_API = "https://abacus.jasoncameron.dev"

# (id, emoji, EN label, ES label). The id is stable + URL/localStorage-safe.
REACTIONS = [
    ("helpful", "\U0001F44D", "Helpful", "Útil"),
    ("love",    "❤️", "Love",  "Me encanta"),
    ("wow",     "\U0001F62E", "Wow",     "Asombroso"),
    ("sad",     "\U0001F622", "Sad",     "Triste"),
    ("angry",   "\U0001F621", "Angry",   "Indigna"),
]


def _reactions_html(slug: str, lang: str = "en") -> str:
    """A reactions bar for the bottom of a story page. Shared counts come from
    Abacus; the page never breaks if the service is unavailable."""
    title = "Reacciones" if lang == "es" else "Reactions"
    btns = []
    for rid, emoji, en, es in REACTIONS:
        label = es if lang == "es" else en
        btns.append(
            f'<button type="button" class="react-btn" data-react="{rid}" '
            f'aria-label="{label}">'
            f'<span class="react-emoji" aria-hidden="true">{emoji}</span>'
            f'<span class="react-label">{label}</span>'
            f'<span class="react-count" aria-hidden="true"></span></button>'
        )
    # Self-contained JS. This markup is inserted as the *value* of the {body}
    # placeholder in _TEMPLATE.format(), so its braces are substituted verbatim
    # and must NOT be doubled (only the literal template body needs doubling).
    js = (
        "<script>(function(){"
        "var bar=document.currentScript.parentNode;"
        f"var SLUG={json.dumps(slug)};var NS={json.dumps(REACT_NAMESPACE)};"
        f"var API={json.dumps(REACT_API)};"
        "var picked={};try{picked=JSON.parse(localStorage.getItem('cr_react_'+SLUG)||'{}');}catch(e){}"
        "var btns=bar.querySelectorAll('.react-btn');"
        "function setCount(b,n){var c=b.querySelector('.react-count');"
        "if(n===null||n===undefined||isNaN(n)){c.textContent='';}"
        "else{c.textContent=n;c.setAttribute('aria-hidden','false');}}"
        "function key(id){return SLUG+'__'+id;}"
        "btns.forEach(function(b){var id=b.getAttribute('data-react');"
        "if(picked[id]){b.classList.add('is-picked');b.setAttribute('aria-pressed','true');}"
        "fetch(API+'/get/'+NS+'/'+encodeURIComponent(key(id))).then(function(r){"
        "return r.ok?r.json():null;}).then(function(j){"
        "if(j&&typeof j.value!=='undefined')setCount(b,j.value);}).catch(function(){});"
        "b.addEventListener('click',function(){"
        "if(picked[id])return;"  # one reaction-type per browser
        "picked[id]=1;b.classList.add('is-picked');b.setAttribute('aria-pressed','true');"
        "try{localStorage.setItem('cr_react_'+SLUG,JSON.stringify(picked));}catch(e){}"
        "fetch(API+'/hit/'+NS+'/'+encodeURIComponent(key(id))).then(function(r){"
        "return r.ok?r.json():null;}).then(function(j){"
        "if(j&&typeof j.value!=='undefined')setCount(b,j.value);}).catch(function(){});"
        "});});"
        "})();</script>"
    )
    return (
        '<section class="reactions" aria-label="' + title + '">'
        f'<div class="react-title">{title}</div>'
        f'<div class="react-row">{"".join(btns)}</div>'
        + js +
        "</section>"
    )


# --- Language toggle (EN <-> ES) ------------------------------------------

def _lang_toggle(en_path: str, es_path: str, current: str) -> str:
    """An EN / ES switch for the masthead nav. `current` is 'en' or 'es'."""
    en_cls = "lang-link is-current" if current == "en" else "lang-link"
    es_cls = "lang-link is-current" if current == "es" else "lang-link"
    return (
        '<span class="lang-toggle" aria-label="Language">'
        f'<a class="{en_cls}" href="{en_path}" hreflang="en">EN</a>'
        '<span class="lang-sep" aria-hidden="true">/</span>'
        f'<a class="{es_cls}" href="{es_path}" hreflang="es">ES</a>'
        '</span>'
    )


# Marker the templates emit; we splice the toggle + (for ES) localize the shell.
_TOPNAV_CLOSE = "</nav>\n  <div class=\"dateline\">"


# --- Per-page Open Graph / Twitter card overrides --------------------------
# These default strings must match _TEMPLATE exactly so we can swap them per page.
_OG_DEF_TITLE = '<meta property="og:title" content="The Chesterfield Report">'
_OG_DEF_DESC = ('<meta property="og:description" content="Hyperlocal news for Chesterfield County, '
                'Virginia. Growth, schools, public safety, government, and community. Free, no ads, '
                'with links back to the original sources.">')
_OG_DEF_URL = '<meta property="og:url" content="https://chesterfieldreport.com/">'
_OG_DEF_IMG = '<meta property="og:image" content="https://chesterfieldreport.com/assets/og-default.png">'
_OG_DEF_TYPE = '<meta property="og:type" content="website">'
_TW_DEF_TITLE = '<meta name="twitter:title" content="The Chesterfield Report">'
_TW_DEF_DESC = ('<meta name="twitter:description" content="Hyperlocal news for Chesterfield County, '
                'Virginia. Free, no ads, links to the original sources.">')
_TW_DEF_IMG = '<meta name="twitter:image" content="https://chesterfieldreport.com/assets/og-default.png">'


def _attr_escape(s: str) -> str:
    return ((s or "").replace("&", "&amp;").replace('"', "&quot;")
            .replace("<", "&lt;").replace(">", "&gt;"))


def _inject_og(page: str, title: str, description: str, url: str,
               image: str = "", og_type: str = "article") -> str:
    """Swap the template's default OG/Twitter tags for page-specific ones so a
    shared link shows this story's headline, summary, and photo."""
    t = _attr_escape(title)
    page = page.replace(_OG_DEF_TITLE, f'<meta property="og:title" content="{t}">', 1)
    page = page.replace(_TW_DEF_TITLE, f'<meta name="twitter:title" content="{t}">', 1)
    if description:
        d = _attr_escape(description)
        page = page.replace(_OG_DEF_DESC, f'<meta property="og:description" content="{d}">', 1)
        page = page.replace(_TW_DEF_DESC, f'<meta name="twitter:description" content="{d}">', 1)
    page = page.replace(_OG_DEF_URL, f'<meta property="og:url" content="{_attr_escape(url)}">', 1)
    page = page.replace(_OG_DEF_TYPE, f'<meta property="og:type" content="{og_type}">', 1)
    if image:
        img = image if image.startswith("http") else SITE_URL + image
        img = _attr_escape(img)
        page = page.replace(_OG_DEF_IMG, f'<meta property="og:image" content="{img}">', 1)
        page = page.replace(_TW_DEF_IMG, f'<meta name="twitter:image" content="{img}">', 1)
    return page


def _share_row(url: str, title: str, lang: str = "en") -> str:
    """Share row: a native 'Share…' button (phone share sheet → Nextdoor, SMS,
    Messenger, etc.) plus Facebook / X / WhatsApp / Email / Copy link."""
    from urllib.parse import quote
    u = quote(url, safe=""); t = quote(title, safe="")
    # labels: (Share, native, Facebook, X, WhatsApp, Email, Copy, Copied)
    L = {"en": ("Share", "Share…", "Facebook", "X", "WhatsApp", "Email", "Copy link", "Copied!"),
         "es": ("Compartir", "Compartir…", "Facebook", "X", "WhatsApp", "Correo", "Copiar enlace", "¡Copiado!")}
    lab = L.get(lang, L["en"])
    fb = "https://www.facebook.com/sharer/sharer.php?u=" + u
    x = "https://twitter.com/intent/tweet?url=" + u + "&text=" + t
    wa = "https://wa.me/?text=" + t + "%20" + u
    em = "mailto:?subject=" + t + "&body=" + u
    eu, et = _attr_escape(url), _attr_escape(title)
    return (
        '<div class="share-row"><span class="share-lab">' + lab[0] + '</span>'
        '<button class="share-btn share-native" type="button" hidden '
        'data-url="' + eu + '" data-title="' + et + '">' + lab[1] + '</button>'
        '<a class="share-btn" href="' + fb + '" target="_blank" rel="noopener">' + lab[2] + '</a>'
        '<a class="share-btn" href="' + x + '" target="_blank" rel="noopener">' + lab[3] + '</a>'
        '<a class="share-btn" href="' + wa + '" target="_blank" rel="noopener">' + lab[4] + '</a>'
        '<a class="share-btn" href="' + em + '">' + lab[5] + '</a>'
        '<button class="share-btn share-copy" type="button" data-url="' + eu + '" '
        'data-done="' + lab[7] + '">' + lab[6] + '</button>'
        '<script>(function(){var r=document.currentScript.parentNode;'
        'var n=r.querySelector(".share-native");'
        'if(navigator.share&&n){n.hidden=false;n.addEventListener("click",function(){'
        'navigator.share({title:n.dataset.title,url:n.dataset.url}).catch(function(){});});}'
        'var c=r.querySelector(".share-copy");c.addEventListener("click",function(){'
        'navigator.clipboard.writeText(c.dataset.url).then(function(){var o=c.textContent;'
        'c.textContent=c.dataset.done;setTimeout(function(){c.textContent=o;},1500);});});'
        '})();</script></div>')


def _inject_toggle(page: str, en_path: str, es_path: str, current: str) -> str:
    """Insert the EN/ES toggle at the end of the .topnav in a rendered page."""
    toggle = _lang_toggle(en_path, es_path, current)
    return page.replace(
        _TOPNAV_CLOSE,
        toggle + _TOPNAV_CLOSE, 1)


def build_site() -> Path:
    """Render the published stories into a paginated summary-card homepage
    (public/index.html + public/page/N.html), one per-story page each, plus
    keep the homepage as the canonical entry point. Returns public/index.html."""
    PUBLIC.mkdir(parents=True, exist_ok=True)
    PUBLISHED.mkdir(parents=True, exist_ok=True)
    recs = _collect(sorted(PUBLISHED.glob("*.md"), reverse=True), include_drafts=False)
    build_articles()
    _render_index_pages(recs)  # This Week now lives in the homepage sidebar rail
    build_spanish()  # Spanish mirror at /es/ (cached; cheap on re-runs)
    return PUBLIC / "index.html"


def _live_story_slugs(recs: list) -> set:
    """The slugs of every currently-published story, derived the SAME way the
    story page filename is (slugify(headline)). This is the authoritative set of
    pages that SHOULD exist under public/story (and public/es/story)."""
    slugs = set()
    for meta, _body, name in recs:
        headline = meta.get("headline", "") or name
        slugs.add(slugify(headline))
    return slugs


def _prune_orphan_story_pages(story_dir: Path, live_slugs: set) -> int:
    """Delete <slug>.html files in story_dir whose slug is no longer published.

    When a story is superseded/deduped its content/published/*.md is removed, but
    the rendered public/story/<slug>.html (and its /es/ twin) used to LINGER. Those
    orphan pages carried stale tag chips pointing at /topics/<slug>.html pages that
    are no longer built (broken links), and dangled in the sitemap. They are NOT
    linked from any live page (home feed, pagination, digest, board, and topic
    cards all link by slugify(headline), which only yields live slugs), so removing
    them is safe. Mirrors build_topics()'s existing "clear stale pages" step.

    IMPORTANT: the slug is slugify(headline), NOT the md filename (which carries a
    YYYY-MM-DD- date prefix) — matching on the filename would nuke real pages."""
    if not story_dir.is_dir():
        return 0
    removed = 0
    for old in story_dir.glob("*.html"):
        if old.stem not in live_slugs:
            old.unlink()
            removed += 1
    return removed


def build_articles() -> int:
    """Write one full-article page per published story to public/story/<slug>.html.
    Returns the number of pages written."""
    from . import seo  # lazy: seo imports render, avoid circular import
    recs = _published_records()
    sdir = PUBLIC / "story"
    sdir.mkdir(parents=True, exist_ok=True)
    # Remove orphan pages for stories that are no longer published before (re)writing
    # the live ones, so superseded/deduped stories don't linger with broken /topics/ links.
    _prune_orphan_story_pages(sdir, _live_story_slugs(recs))
    n = 0
    for meta, body, name in recs:
        link = True
        headline = meta.get("headline", "") or name
        rel_url = story_url(headline)
        story_html = _md_to_html(body)
        map_html = _resolve_map(meta)
        if map_html and "</h2>" in story_html:
            story_html = story_html.replace("</h2>", "</h2>" + map_html, 1)
        elif map_html:
            story_html += map_html
        hero = media_html(meta, big=True)
        slug = slugify(headline)
        back = '<a class="story-back" href="/">&larr; Back to The Chesterfield Report</a>'
        article_html = (
            f'<article class="card story-page" id="{slug}">'
            f"{hero}"
            f'<div class="card-tags">{_chips_html(meta, link)}</div>'
            f"{_meta_line(meta)}"
            f"{story_html}{_tagrow_html(meta, link)}"
            f"{_share_row(SITE_URL + story_url(headline), headline, 'en')}"
            f"{_reactions_html(slug, 'en')}</article>"
            f'<div class="story-foot">{back}</div>'
        )
        jsonld = seo.jsonld_newsarticle(meta, body, rel_url)
        body_html = jsonld + article_html
        page = _shell(body_html, len(recs))
        # Best-effort: set the document <title> + canonical to this story, and
        # add hreflang alternates pointing at the EN <-> ES mirror.
        canonical = SITE_URL + rel_url
        es_rel = f"/es{rel_url}"
        title_tag = (f"{headline} | The Chesterfield Report")
        page = page.replace(
            "<title>The Chesterfield Report: Hyperlocal News for Chesterfield County, Virginia</title>",
            f'<title>{title_tag}</title>'
            f'<link rel="canonical" href="{canonical}">'
            f'<link rel="alternate" hreflang="en" href="{canonical}">'
            f'<link rel="alternate" hreflang="es" href="{SITE_URL}{es_rel}">',
            1)
        page = _inject_og(page, headline, _tldr_from_body(body), canonical,
                          image=_story_image(meta))
        page = _inject_toggle(page, en_path=rel_url, es_path=es_rel, current="en")
        (sdir / f"{slug}.html").write_text(page, encoding="utf-8")
        n += 1
    return n


# --- Virginia & Region (regional track) -----------------------------------

def _regional_records() -> list:
    """Published regional-track stories (content/regional/), newest first."""
    if not REGIONAL.is_dir():
        return []
    return _collect(sorted(REGIONAL.glob("*.md"), reverse=True), include_drafts=False)


_VA_CSS = """<style>
.va-wrap{max-width:820px;margin:0 auto;}
.va-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:64ch;margin:.4rem 0 1.4rem;}
.va-card{border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface-card);margin:0 0 18px;overflow:hidden;}
.va-img{display:block;}
.va-img img{display:block;width:100%;height:200px;object-fit:cover;}
.va-body{padding:1.1rem 1.25rem 1.2rem;}
.va-meta{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);margin-bottom:.45rem;}
.va-card h3{font:var(--fw-bold) var(--fs-xl)/1.2 var(--font-display);margin:0 0 .4rem;}
.va-card h3 a{color:var(--text-primary);}
.va-card h3 a:hover{color:var(--accent);}
.va-tldr{font:var(--fw-semibold) var(--fs-md)/1.45 var(--font-sans);color:var(--text-primary);margin:.3rem 0 .6rem;}
.va-sum{font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);margin:.3rem 0 .7rem;}
.va-why{border-left:3px solid var(--accent);background:var(--surface-sunken,rgba(154,50,34,.05));border-radius:0 var(--radius-xs) var(--radius-xs) 0;padding:.6rem .85rem;margin:.6rem 0 .8rem;}
.va-why-l{display:block;font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--accent);margin-bottom:.3rem;}
.va-why p{font:var(--fs-sm)/1.55 var(--font-sans);color:var(--text-secondary);margin:0;}
.va-src{font:var(--fw-semibold) var(--fs-2xs) var(--font-sans);}
.va-src a{color:var(--accent);}
.va-note{margin-top:2rem;padding:1rem 1.1rem;border-left:3px solid var(--accent);background:var(--surface-card);
  border-radius:var(--radius-xs);font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);}
.va-empty{font:var(--fs-md) var(--font-sans);color:var(--text-secondary);margin:2rem 0;}
</style>"""


def _summary_from_body(body: str) -> str:
    """The story summary paragraph(s): everything between the TL;DR and the
    'Why it matters' line / source link, with the headline and TL;DR removed."""
    text = re.split(r"\*\*Why it matters:\*\*|\n\[Read the source", body)[0]
    paras = []
    for raw in text.split("\n\n"):
        s = raw.strip()
        if not s or s.startswith("#") or s.startswith("**TL;DR:") or s.startswith("["):
            continue
        paras.append(re.sub(r"\s+", " ", s))
    return " ".join(paras).strip()


def _why_from_body(body: str) -> str:
    """The 'Why it matters' analysis (our Chesterfield angle), if present."""
    m = re.search(r"\*\*Why it matters:\*\*\s*(.+?)(?:\n\[Read the source|\Z)",
                  body, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def _regional_card(meta: dict, body: str) -> str:
    headline = html.escape(meta.get("headline", "") or "")
    src = html.escape(meta.get("source", "") or "the source")
    src_url = html.escape(meta.get("source_url", "") or "#")
    date = _pretty_date(meta.get("published", ""))
    _, flabel = _primary_focus(meta)
    tldr = _tldr_from_body(body)
    summary = _summary_from_body(body)
    why = _why_from_body(body)
    img = (meta.get("image") or "").strip()
    metabits = " &middot; ".join(b for b in (html.escape(flabel), date) if b)
    img_html = (
        f'<a class="va-img" href="{src_url}" target="_blank" rel="noopener">'
        f'<img src="{html.escape(img)}" alt="" loading="lazy"></a>'
    ) if img.startswith("http") else ""
    tldr_html = f'<p class="va-tldr">{_inline(html.escape(tldr))}</p>' if tldr else ""
    summary_html = f'<p class="va-sum">{_inline(html.escape(summary))}</p>' if summary else ""
    why_html = (
        '<div class="va-why"><span class="va-why-l">Why it matters to Chesterfield</span>'
        f'<p>{_inline(html.escape(why))}</p></div>'
    ) if why else ""
    return (
        '<article class="va-card">'
        f'{img_html}'
        '<div class="va-body">'
        f'<div class="va-meta">{metabits}</div>'
        f'<h3><a href="{src_url}" target="_blank" rel="noopener">{headline}</a></h3>'
        f'{tldr_html}'
        f'{summary_html}'
        f'{why_html}'
        f'<div class="va-src">Read the full story at <a href="{src_url}" target="_blank" rel="noopener">{src} &nearr;</a></div>'
        '</div>'
        '</article>'
    )


def build_virginia() -> Path:
    """Render /virginia.html: the regional track (statewide/regional news that
    affects Chesterfield residents), separate from the local feed."""
    recs = _regional_records()
    if recs:
        cards = "".join(_regional_card(m, b) for m, b, _ in recs)
    else:
        cards = ('<p class="va-empty">No regional stories yet. As Virginia and '
                 'Richmond-area news that affects Chesterfield residents comes in, it '
                 'will appear here.</p>')
    body = (
        _VA_CSS
        + '<div class="va-wrap">'
        + '<h1 class="page-title">Virginia &amp; Region</h1>'
        + '<p class="va-lead">State and regional news that affects Chesterfield County '
          'residents but isn’t local Chesterfield news: state laws and the budget, '
          'utility rates, regional transportation, courts, and elections. Each item links '
          'to the original reporting.</p>'
        + cards
        + '<div class="va-note">This section covers Virginia and Richmond-area news with '
          'a direct impact on Chesterfield residents. It is kept separate from our local '
          'Chesterfield coverage, and every item is summarized with a link back to the '
          'original source. Spotted something we should include? <a href="/tip.html">Let us know.</a></div>'
        + '</div>'
    )
    page = _shell(body, len(recs))
    page = _inject_og(page, "Virginia & Region — The Chesterfield Report",
                      "State and regional news that affects Chesterfield County residents: "
                      "laws, the budget, utility rates, transportation, courts, and elections.",
                      "https://chesterfieldreport.com/virginia.html")
    out = PUBLIC / "virginia.html"
    out.write_text(page, encoding="utf-8")
    return out


def _regional_home_module() -> str:
    """Compact 'Virginia & Region' block for the homepage (latest few items)."""
    recs = _regional_records()[:4]
    if not recs:
        return ""
    items = []
    for meta, _body, _name in recs:
        headline = html.escape(meta.get("headline", "") or "")
        src_url = html.escape(meta.get("source_url", "") or "/virginia.html")
        date = _pretty_date(meta.get("published", ""))
        items.append(
            f'<li><a href="{src_url}" target="_blank" rel="noopener">{headline}</a>'
            f'<span class="vahome-d">{html.escape(date)}</span></li>')
    more = '<a class="vahome-more" href="/virginia.html">All Virginia &amp; Region &rarr;</a>'
    return (
        '<style>.vahome{margin:1.6rem 0;border:1px solid var(--border);border-radius:var(--radius-sm);'
        'background:var(--surface-card);padding:1rem 1.2rem;}'
        '.vahome h2{font:var(--fw-bold) var(--fs-md)/1.1 var(--font-display);margin:0 0 .2rem;}'
        '.vahome .vahome-sub{font:var(--fs-2xs)/1.3 var(--font-sans);color:var(--text-tertiary);margin:0 0 .7rem;}'
        '.vahome ul{list-style:none;padding:0;margin:0;}'
        '.vahome li{padding:.45rem 0;border-top:1px solid var(--border);display:flex;justify-content:space-between;gap:10px;'
        'font:var(--fs-sm)/1.4 var(--font-sans);}'
        '.vahome li a{color:var(--text-primary);}.vahome li a:hover{color:var(--accent);}'
        '.vahome-d{font:var(--fs-3xs) var(--font-mono);color:var(--text-tertiary);white-space:nowrap;}'
        '.vahome-more{display:inline-block;margin-top:.6rem;font:var(--fw-semibold) var(--fs-2xs) var(--font-sans);color:var(--accent);}'
        '</style>'
        '<section class="vahome"><h2>Virginia &amp; Region</h2>'
        '<p class="vahome-sub">State and regional news that affects Chesterfield residents</p>'
        f'<ul>{"".join(items)}</ul>{more}</section>'
    )


# --- Spanish edition (/es/) -----------------------------------------------
#
# A lightweight Spanish mirror: each EN story gets an /es/story/<same-slug>.html
# with a translated headline + body (cached via translate.translate_story), plus
# an /es/index.html of summary cards. The shell chrome (nav, tagline, footer) is
# localized by post-processing the rendered EN template, and the home/brand links
# are repointed at /es/ so a Spanish reader stays in the Spanish edition.

# Localized standing UI strings emitted by the ES shell.
_ES_NAV = {
    ">Home<": ">Inicio<",
    ">Topics<": ">Temas<",
    ">This Week<": ">Esta Semana<",
    ">Map<": ">Mapa<",
    ">Board<": ">Pizarra<",
    ">Meetings<": ">Reuniones<",
    ">Opinion<": ">Opinión<",
    ">Send a tip<": ">Enviar un aviso<",
}
_ES_TAGLINE = "Noticias hiperlocales para el condado de Chesterfield, Virginia."
_ES_READ_ORIGINAL = "Lee el original en"
_ES_BACK = "&larr; Volver a The Chesterfield Report"
# Footer tagline / body, translated.
_EN_FOOTER_P1 = (
    "Independent, community-rooted coverage of Chesterfield County, Virginia:\n"
    "       growth &amp; development, schools, public safety, government and community life.")
_ES_FOOTER_P1 = (
    "Cobertura independiente y arraigada en la comunidad del condado de Chesterfield, "
    "Virginia: crecimiento y desarrollo, escuelas, seguridad pública, gobierno y "
    "vida comunitaria.")
_EN_FOOTER_P2 = (
    "Stories are aggregated and summarized with links back to the original reporting.\n"
    "       Please follow the <strong>[source]</strong> and &ldquo;Read the source&rdquo; links to support\n"
    "       the outlets and agencies that do the original work.")
_ES_FOOTER_P2 = (
    "Las historias se recopilan y resumen con enlaces al reportaje original. "
    "Sigue los enlaces <strong>[source]</strong> y &ldquo;Lee el original&rdquo; para apoyar "
    "a los medios y agencias que realizan el trabajo original.")


def _es_localize_shell(page: str) -> str:
    """Localize a rendered EN template page into Spanish: lang attr, nav labels,
    tagline, footer, and repoint the home/brand links at /es/."""
    page = page.replace('<html lang="en">', '<html lang="es">', 1)
    for en, es in _ES_NAV.items():
        page = page.replace(en, es, 1)
    page = page.replace(
        '<p class="tagline cr-header__tagline">Hyperlocal news for Chesterfield County, Virginia.</p>',
        f'<p class="tagline cr-header__tagline">{_ES_TAGLINE}</p>', 1)
    # Brand + Home links -> /es/ (keep other nav pointing at canonical EN pages).
    page = page.replace('<a class="brand" href="/"', '<a class="brand" href="/es/"', 1)
    page = page.replace('<a href="/">Inicio</a>', '<a href="/es/">Inicio</a>', 1)
    page = page.replace(_EN_FOOTER_P1, _ES_FOOTER_P1, 1)
    page = page.replace(_EN_FOOTER_P2, _ES_FOOTER_P2, 1)
    return page


def _es_translated_body(headline: str, body: str) -> tuple[str, str]:
    """Return (es_headline, es_body_md). Falls back to EN on translation error
    so the build never breaks."""
    from . import translate  # lazy: keep render importable without the CLI
    try:
        t = translate.translate_story(headline, body)
        return t["headline"], t["body_md"]
    except Exception as e:  # noqa: BLE001 — degrade gracefully, never break build
        print(f"  ! Spanish translation failed for {headline!r}: {e}")
        return headline, body


def _es_meta_line(meta: dict) -> str:
    """Meta line with a Spanish-formatted date."""
    src = meta.get("source", "")
    date_iso = meta.get("published", "")[:10]
    return (f'<div class="meta"><span class="meta-source">{src}</span>'
            f'<span class="meta-dot">&middot;</span>'
            f'<time datetime="{date_iso}">{_pretty_date_es(date_iso)}</time></div>')


_MONTHS_ES = ["ene", "feb", "mar", "abr", "may", "jun",
              "jul", "ago", "sep", "oct", "nov", "dic"]


def _pretty_date_es(iso: str) -> str:
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    if not m:
        return iso
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not 1 <= mo <= 12:
        return iso
    return f"{d} {_MONTHS_ES[mo - 1]} {y}"


def _es_cr_meta(meta: dict) -> str:
    date_iso = meta.get("published", "")[:10]
    src = meta.get("source", "")
    src_html = '<span class="cr-meta__by">' + src + '</span>' if src else ""
    return '<div class="cr-meta"><span>' + _pretty_date_es(date_iso) + '</span>' + src_html + '</div>'


def _es_summary_card(meta: dict, es_headline: str, es_body: str) -> str:
    """A HUD story card (cr-story) for the Spanish homepage; links to the ES
    story page (shares the EN slug)."""
    data_focus = " ".join(_focus_of(meta)[1])
    slug = slugify(meta.get("headline", ""))
    url = f"/es/story/{slug}.html"
    tone = _tone_of(meta)
    _s, label = _primary_focus(meta)
    tldr = _tldr_from_body(es_body)
    dek = '<p class="cr-story__dek">' + _inline(tldr) + '</p>' if tldr else ""
    return (
        '<a class="cr-card cr-card--accent cr-card--interactive cr-card--bracket '
        'cr-story cr-story--md" id="' + slug + '" data-focus="' + data_focus + '" '
        'style="--accent-color:' + _TONE_VAR[tone] + ';display:flex;text-decoration:none" '
        'href="' + url + '">'
        + _photo_frame(meta, tone, "FOTO · " + label.upper(), "16 / 9")
        + '<div class="cr-story__body">'
        + _cr_badge(label, tone, dot=(tone == "breaking"))
        + '<h3 class="cr-story__title">' + es_headline + '</h3>'
        + dek + _es_cr_meta(meta)
        + '</div></a>'
    )


def _es_hero_card(meta: dict, es_headline: str, es_body: str) -> str:
    slug = slugify(meta.get("headline", ""))
    url = f"/es/story/{slug}.html"
    tone = _tone_of(meta)
    _s, label = _primary_focus(meta)
    tldr = _tldr_from_body(es_body)
    dek = '<p class="cr-hero__dek">' + _inline(tldr) + '</p>' if tldr else ""
    overlay = (
        '<div class="cr-hero__overlay">'
        + _cr_badge(label, tone, dot=(tone == "breaking"))
        + '<h1 class="cr-hero__title">' + es_headline + '</h1>'
        + dek + _es_cr_meta(meta)
        + '</div>'
    )
    return (
        '<a class="cr-card cr-card--accent cr-card--interactive cr-card--bracket cr-hero" '
        'style="--accent-color:' + _TONE_VAR[tone] + ';display:block;text-decoration:none" '
        'href="' + url + '">'
        + _photo_frame(meta, tone, "FOTO · " + label.upper(), "21 / 9", overlay=overlay)
        + '</a>'
    )


def _es_home_sidebar(es_recs: list) -> str:
    """Spanish version of the homepage sidebar rail."""
    items = []
    for meta, es_headline, _es_body in es_recs[:7]:
        slug = slugify(meta.get("headline", ""))
        url = f"/es/story/{slug}.html"
        tone = _tone_of(meta)
        _s, label = _primary_focus(meta)
        day = _weekday_abbr(meta.get("published", "")[:10])
        items.append(
            '<li class="cr-twrail__item">'
            '<span class="cr-twrail__day cr-twrail__day--' + tone + '">' + day + '</span>'
            '<div><div class="cr-twrail__label">' + label + '</div>'
            '<a class="cr-twrail__title" href="' + url + '" style="text-decoration:none">'
            + es_headline + '</a></div></li>'
        )
    twrail = (
        '<div class="cr-card cr-card--grad cr-twrail">'
        '<div class="cr-twrail__head">'
        '<span class="cr-twrail__kicker">// Esta semana en Chesterfield</span>'
        '<a class="cr-twrail__all" href="/digest.html" style="text-decoration:none">Resumen completo</a>'
        '</div><ul class="cr-twrail__list">' + "".join(items) + '</ul></div>'
    )
    chips = "".join(
        '<a class="cr-tag" href="/topics/' + s + '.html" style="text-decoration:none">'
        '<span class="cr-tag__hash">#</span>' + t + '</a>'
        for t, s in _trending_tags([(m, "", "") for m, _h, _b in es_recs], 8)
    )
    trending = (
        '<div class="cr-card cr-card--grad cr-card--pad cr-trend">'
        '<span class="cr-twrail__kicker">// Tendencias</span>'
        '<div class="cr-trend__tags">' + chips + '</div></div>'
    ) if chips else ""
    return '<aside class="cr-home__side">' + twrail + trending + '</aside>'


def build_spanish() -> int:
    """Build the Spanish edition under public/es/: one story page per published
    story (translated, cached) plus a summary-card homepage. Returns the number
    of Spanish story pages written."""
    from . import seo  # lazy: seo imports render
    recs = _published_records()
    es_dir = PUBLIC / "es"
    es_story_dir = es_dir / "story"
    es_story_dir.mkdir(parents=True, exist_ok=True)
    # Same orphan cleanup as the EN edition: drop /es/story pages for stories that
    # are no longer published, otherwise an ES orphan links back to a now-deleted
    # EN /story/<slug>.html and creates a broken link.
    _prune_orphan_story_pages(es_story_dir, _live_story_slugs(recs))

    es_recs, n = [], 0
    for meta, body, name in recs:
        en_headline = meta.get("headline", "") or name
        es_headline, es_body = _es_translated_body(en_headline, body)
        slug = slugify(en_headline)
        en_rel = f"/story/{slug}.html"
        es_rel = f"/es/story/{slug}.html"

        story_html = _md_to_html(es_body)
        map_html = _resolve_map(meta)
        if map_html and "</h2>" in story_html:
            story_html = story_html.replace("</h2>", "</h2>" + map_html, 1)
        elif map_html:
            story_html += map_html
        hero = media_html(meta, big=True)
        back = f'<a class="story-back" href="/es/">{_ES_BACK}</a>'
        article_html = (
            f'<article class="card story-page" id="{slug}">'
            f"{hero}"
            f'<div class="card-tags">{_chips_html(meta, False)}</div>'
            f"{_es_meta_line(meta)}"
            f"{story_html}"
            f"{_share_row(SITE_URL + f'/es/story/{slug}.html', es_headline, 'es')}"
            f"{_reactions_html(slug, 'es')}</article>"
            f'<div class="story-foot">{back}</div>'
        )
        page = _shell(article_html, len(recs))
        page = _es_localize_shell(page)
        canonical = f"{SITE_URL}{es_rel}"
        title_tag = f"{es_headline} — The Chesterfield Report"
        page = page.replace(
            "<title>The Chesterfield Report: Hyperlocal News for Chesterfield County, Virginia</title>",
            f'<title>{title_tag}</title>'
            f'<link rel="canonical" href="{canonical}">'
            f'<link rel="alternate" hreflang="es" href="{canonical}">'
            f'<link rel="alternate" hreflang="en" href="{SITE_URL}{en_rel}">',
            1)
        page = _inject_og(page, es_headline, _tldr_from_body(es_body), canonical,
                          image=_story_image(meta))
        page = _inject_toggle(page, en_path=en_rel, es_path=es_rel, current="es")
        (es_story_dir / f"{slug}.html").write_text(page, encoding="utf-8")
        es_recs.append((meta, es_headline, es_body))
        n += 1

    # Spanish homepage — same hero + grid + sidebar layout as the EN home.
    if es_recs:
        hero = _es_hero_card(*es_recs[0])
        grid_cards = [_es_summary_card(*r) for r in es_recs[1:]]
    else:
        hero, grid_cards = "", []
    grid = ("\n".join(grid_cards)
            or '<p class="cr-topics__empty">Aún no hay historias publicadas.</p>')
    action = ('<a class="cr-btn cr-btn--secondary cr-btn--sm" href="/topics/" '
              'style="text-decoration:none">Filtrar temas &rarr;</a>')
    main = (hero
            + _sechead("// El feed", "En todo el condado", action)
            + '<div class="cr-home__grid feed" id="feed">' + grid + '</div>')
    body_html = ('<div class="cr-home"><div class="cr-home__main">' + main + '</div>'
                 + _es_home_sidebar(es_recs) + '</div>')
    page = _shell(body_html, len(recs))
    page = _es_localize_shell(page)
    canonical = f"{SITE_URL}/es/"
    page = page.replace(
        "<title>The Chesterfield Report: Hyperlocal News for Chesterfield County, Virginia</title>",
        '<title>The Chesterfield Report: Noticias hiperlocales del condado de Chesterfield, Virginia</title>'
        f'<link rel="canonical" href="{canonical}">'
        f'<link rel="alternate" hreflang="es" href="{canonical}">'
        f'<link rel="alternate" hreflang="en" href="{SITE_URL}/">',
        1)
    page = _inject_toggle(page, en_path="/", es_path="/es/", current="es")
    (es_dir / "index.html").write_text(page, encoding="utf-8")
    return n


def build_preview() -> Path:
    """Render the DRAFTS queue into public/drafts.html for review."""
    PUBLIC.mkdir(parents=True, exist_ok=True)
    DRAFTS.mkdir(parents=True, exist_ok=True)
    recs = _collect(sorted(DRAFTS.glob("*.md"), reverse=True), include_drafts=True)
    return _render_page(recs, PUBLIC / "drafts.html", draft_mode=True)


def _shell(body_html: str, count: int = 0) -> str:
    from . import seo  # lazy import (seo imports render)
    generated = _updated_stamp()
    return _TEMPLATE.format(body=seo.jsonld_site() + body_html,
                            generated=generated, count=count)


def _published_records() -> list:
    return _collect(sorted(PUBLISHED.glob("*.md"), reverse=True), include_drafts=False)


# --- Topic / neighborhood pages -------------------------------------------

def build_topics() -> int:
    """Generate one page per focus area and per tag, plus an index. Returns the
    number of topic pages written."""
    recs = _published_records()
    tdir = PUBLIC / "topics"
    tdir.mkdir(parents=True, exist_ok=True)
    # Clear stale topic pages so pages that drop below threshold (or whose tag
    # disappears) don't linger on disk / in the sitemap.
    for old in tdir.glob("*.html"):
        old.unlink()

    topics: dict[str, dict] = {}   # slug -> {label, recs, names, kind}

    def add(slug, label, rec, name, kind):
        t = topics.setdefault(
            slug, {"label": label, "recs": [], "names": set(), "kind": kind})
        if kind == "focus":           # focus always wins over a same-slug tag
            t["kind"] = "focus"
        if name not in t["names"]:
            t["names"].add(name)
            t["recs"].append(rec)

    for meta, body, name in recs:
        rec = (meta, body, name)
        for l in [x.strip() for x in meta.get("focus", "").strip("[]").split(",") if x.strip()]:
            add(_focus_slug(l), l, rec, name, "focus")
        for t in [x.strip() for x in meta.get("tags", "").strip("[]").split(",") if x.strip()]:
            add(slugify(t), t, rec, name, "tag")

    # Keep every focus-area page (canonical categories), but only build a tag
    # page once at least 2 stories share it — avoids thin single-story pages
    # that read as SEO filler.
    topics = {s: i for s, i in topics.items()
              if i["kind"] == "focus" or len(i["recs"]) >= 2}

    from . import seo  # lazy: seo imports render, avoid circular import
    for slug, info in topics.items():
        cards = [_summary_card(m, b, n) for m, b, n in info["recs"]]
        feed = ("\n".join(cards)
                or '<p class="empty">No stories in this topic yet.</p>')
        jsonld = seo.jsonld_site() + "".join(
            seo.jsonld_newsarticle(m, b) for m, b, n in info["recs"])
        body_html = (jsonld
                     + f'<h1 class="page-title">{info["label"]}</h1>'
                     + _filter_links(recs)
                     + f'<div class="feed" id="feed">{feed}</div>')
        generated = _updated_stamp()
        (tdir / f"{slug}.html").write_text(
            _TEMPLATE.format(body=body_html, generated=generated,
                             count=len(info["recs"])),
            encoding="utf-8")

    # Index, grouped for digestibility: BEATS (the canonical focus areas, as
    # prominent cards) first, then the long tail of entity TAGS as small chips.
    items = sorted(topics.items(), key=lambda kv: (-len(kv[1]["recs"]), kv[1]["label"].lower()))
    focus_order = [v[0] for v in FOCUS_AREAS.values()]
    beats = [(s, i) for s, i in items if i["kind"] == "focus"]
    beats.sort(key=lambda kv: focus_order.index(kv[1]["label"]) if kv[1]["label"] in focus_order else 99)
    tags = [(s, i) for s, i in items if i["kind"] != "focus"]

    def _beat_card(slug, info):
        n = len(info["recs"])
        tone = _TONE_BY_SLUG.get(slug, "teal")
        return (f'<a class="topic-beat" href="/topics/{slug}.html" '
                f'style="--accent-color:{_TONE_VAR[tone]}">'
                f'<span class="topic-beat__name">{info["label"]}</span>'
                f'<span class="topic-beat__count">{n} {"story" if n == 1 else "stories"}</span></a>')

    beats_html = "".join(_beat_card(s, i) for s, i in beats)
    tags_html = "".join(
        f'<a class="topic-tag" href="/topics/{slug}.html">'
        f'<span class="topic-tag__hash">#</span>{info["label"]}'
        f'<span class="topic-tag__count">{len(info["recs"])}</span></a>'
        for slug, info in tags)

    body = ('<h1 class="page-title">Topics</h1>'
            '<p class="lead">Browse Chesterfield coverage by beat, place, and tag.</p>'
            '<h2 class="topic-h">Beats</h2>'
            f'<div class="topic-beats">{beats_html or "<p>No beats yet.</p>"}</div>'
            + (f'<h2 class="topic-h">Browse by tag</h2>'
               f'<div class="topic-tags">{tags_html}</div>' if tags_html else ""))
    (tdir / "index.html").write_text(_shell(body, len(recs)), encoding="utf-8")
    return len(topics)


# --- Weekly digest ---------------------------------------------------------

def _digest_week(recs: list) -> tuple[list, list]:
    """Shared 'This Week' data: the last-7-days records (falling back to the 8
    most recent on a quiet week) and those records grouped by primary focus
    area in canonical order. Returns (week_records, ordered_groups)."""
    today = datetime.now(timezone.utc).date()

    def within7(meta):
        d = (meta.get("published", "") or "")[:10]
        try:
            return (today - datetime.fromisoformat(d).date()).days <= 7
        except ValueError:
            return False

    week = [r for r in recs if within7(r[0])] or recs[:8]
    groups: dict[str, list] = {}
    for meta, body, name in week:
        _, primary = _primary_focus(meta)
        groups.setdefault(primary, []).append((meta, body, name))
    order = [v[0] for v in FOCUS_AREAS.values()]
    ordered = sorted(groups.items(), key=lambda kv: order.index(kv[0]) if kv[0] in order else 99)
    return week, ordered


def _thisweek_band(recs: list) -> str:
    """Neon-accented 'This Week in Chesterfield' highlight module for the top of
    the homepage. Lists the week's stories with a topic filter (with per-topic
    story counts) and links to the full digest."""
    week, ordered = _digest_week(recs)
    if not week:
        return ""
    counts, present, items = {}, {}, []
    for meta, body, name in week:
        head = meta.get("headline", "") or name
        url = story_url(head)
        slug, label = _primary_focus(meta)
        counts[slug] = counts.get(slug, 0) + 1
        present.setdefault(slug, label)
        items.append((url, meta.get("headline", ""), slug, label))
    order = [v[0] for v in FOCUS_AREAS.values()]
    ordered_present = sorted(present.items(),
                             key=lambda kv: order.index(kv[1]) if kv[1] in order else 99)
    chips = [f'<button class="tw-filter is-active" data-twfilter="all" aria-pressed="true">'
             f'All <span class="fcount">{len(items)}</span></button>']
    for slug, label in ordered_present:
        chips.append(f'<button class="tw-filter" data-twfilter="{slug}" aria-pressed="false">'
                     f'{label} <span class="fcount">{counts[slug]}</span></button>')
    rows = "".join(
        f'<li data-cat="{slug}"><a href="{url}">'
        f'<span class="tw-cat" data-cat="{slug}">{label}</span>'
        f'<span class="tw-hl">{head}</span></a></li>'
        for url, head, slug, label in items
    )
    js = ("<script>(function(){var s=document.currentScript.parentNode;"
          "var b=s.querySelectorAll('.tw-filter');var l=s.querySelectorAll('.tw-list li');"
          "s.addEventListener('click',function(e){var t=e.target.closest('.tw-filter');if(!t)return;"
          "var f=t.getAttribute('data-twfilter');"
          "b.forEach(function(x){var o=x===t;x.classList.toggle('is-active',o);"
          "x.setAttribute('aria-pressed',o?'true':'false');});"
          "l.forEach(function(li){li.hidden=!(f==='all'||li.getAttribute('data-cat')===f);});});})();</script>")
    return (
        '<section class="thisweek" aria-label="This Week in Chesterfield">'
        '<div class="tw-head">'
        '<span class="tw-kicker">This Week in Chesterfield</span>'
        f'<h2 class="tw-title">{len(week)} stories that mattered this week</h2>'
        '</div>'
        f'<nav class="tw-filters" aria-label="Filter this week by topic">{"".join(chips)}</nav>'
        f'<ul class="tw-list">{rows}</ul>'
        '<a class="tw-more" href="/digest.html">See the full week &rarr;</a>'
        + js +
        '</section>'
    )


def build_digest() -> Path:
    """'This Week in Chesterfield' — a page + a newsletter-ready markdown file,
    grouped by focus area, covering the last 7 days (falling back to the most
    recent stories if it's a quiet week)."""
    recs = _published_records()
    today = datetime.now(timezone.utc).date()
    week, ordered = _digest_week(recs)

    span = f"{(today.replace(day=max(1, today.day))).strftime('%B %d')}"  # display only
    sections_html, md = [], [f"# This Week in Chesterfield\n",
                             f"_{len(week)} stories • generated {today.isoformat()}_\n"]
    for label, items in ordered:
        rows = []
        md.append(f"\n## {label}\n")
        for meta, body, name in items:
            head = meta.get("headline", "") or name
            url = story_url(head)
            tl = _tldr_from_body(body)
            rows.append(
                f'<li><a href="{url}">{head}</a>'
                f'<div class="dg-tldr">{tl}</div></li>')
            # Keep the headline plain so newsletter.parse_digest reads it
            # cleanly; append the canonical story URL on its own line.
            md.append(f"- **{head}** — {tl}")
            md.append(f"  {SITE_URL}{url}")
        sections_html.append(
            f'<section class="dg-sec"><h2>{label}</h2><ul class="dg-list">'
            + "".join(rows) + "</ul></section>")

    intro = (f'<p class="lead">{len(week)} stories across {len(ordered)} topics '
             f'this week in Chesterfield County. Here\'s what mattered.</p>')
    body_html = (f'<h1 class="page-title">This Week in Chesterfield</h1>{intro}'
                 + "".join(sections_html)
                 + '<p class="dg-foot">Have a tip or a correction? <a href="/tip.html">Let us know.</a></p>')
    out = PUBLIC / "digest.html"
    out.write_text(_shell(body_html, len(week)), encoding="utf-8")
    (PUBLIC / "digest.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return out


def _tldr_from_body(body: str) -> str:
    m = re.search(r"\*\*TL;DR:\*\*\s*(.+)", body)
    if m:
        return m.group(1).strip()
    for ln in body.splitlines():
        s = ln.strip()
        if s and not s.startswith(("#", "*", "[", "-")):
            return s
    return ""


# --- Tip / correction page -------------------------------------------------

_SITE_FORM_CSS = """<style>
.tipwrap{max-width:640px}
.form-notice{background:rgba(255,210,63,.12);border:1px solid var(--neon-amber);
 border-radius:8px;padding:.85rem 1.1rem;margin:0 0 1.3rem;color:var(--text-body);font-size:.93rem}
.site-form label{display:block;font-family:var(--font-mono);font-size:.72rem;font-weight:700;
 text-transform:uppercase;letter-spacing:.06em;color:var(--neon-teal);margin:1.1rem 0 .35rem}
.site-form .opt{color:var(--text-faint);font-weight:400;text-transform:none;letter-spacing:0}
.site-form input[type=text],.site-form input[type=email],.site-form textarea{
 width:100%;font:inherit;padding:.65rem .75rem;background:var(--surface-raised);
 color:var(--text-strong);border:1px solid var(--ink-400);border-radius:6px}
.site-form input:focus,.site-form textarea:focus{outline:none;border-color:var(--neon-teal);
 box-shadow:var(--glow-sm-teal)}
.site-form textarea{resize:vertical;min-height:9rem}
.site-form .hp{position:absolute;left:-9999px}
.thanks{background:rgba(34,245,212,.08);border:1px solid var(--neon-teal);
 border-radius:10px;padding:1.1rem 1.3rem}
.thanks h2{font-family:var(--font-display);color:var(--neon-teal);margin:.2rem 0 .5rem}
</style>"""


def build_feed() -> Path:
    """RSS 2.0 feed of the latest published stories — a zero-maintenance way for
    readers to follow the site without email."""
    from email.utils import format_datetime
    recs = sorted(_published_records(),
                  key=lambda r: (r[0].get("published", "") or "")[:10], reverse=True)[:30]
    items = []
    for meta, body, name in recs:
        headline = meta.get("headline", "") or name
        url = SITE_URL + story_url(headline)
        tldr = _tldr_from_body(body) or ""
        _slug, label = _primary_focus(meta)
        date_iso = (meta.get("published", "") or "")[:10]
        pub = ""
        try:
            pub = format_datetime(datetime.fromisoformat(date_iso + "T12:00:00+00:00"))
        except ValueError:
            pass
        items.append(
            "<item>"
            f"<title>{_attr_escape(headline)}</title>"
            f"<link>{url}</link>"
            f'<guid isPermaLink="true">{url}</guid>'
            + (f"<pubDate>{pub}</pubDate>" if pub else "")
            + f"<category>{_attr_escape(label)}</category>"
            f"<description>{_attr_escape(tldr)}</description>"
            "</item>")
    now = format_datetime(datetime.now(timezone.utc))
    feed = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
        '<title>The Chesterfield Report</title>'
        f'<link>{SITE_URL}/</link>'
        f'<atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>'
        '<description>Hyperlocal news for Chesterfield County, Virginia '
        '&#8212; growth, schools, public safety, government and community.</description>'
        '<language>en-us</language>'
        f'<lastBuildDate>{now}</lastBuildDate>'
        + "".join(items) +
        '</channel></rss>')
    out = PUBLIC / "feed.xml"
    out.write_text(feed, encoding="utf-8")
    return out


def build_about() -> Path:
    """A plain-language 'how this works' page — transparency about sourcing,
    AI summarization + human review, and independence."""
    body = (
        '<h1 class="page-title">About The Chesterfield Report</h1>'
        '<div class="prose-page">'
        '<p class="lead">An independent, community-powered news roundup for '
        'Chesterfield County, Virginia. Free, no ads, no paywall, no login.</p>'

        '<h2>How it works</h2>'
        '<p>The Report pulls from <strong>official county sources</strong> '
        '(the county government, police, fire/EMS, schools, planning and '
        'transportation) and <strong>local news outlets</strong>, then writes a '
        'plain-language summary of each story. We use <strong>AI to draft those '
        'summaries, and a human reviews them before anything is published.</strong> '
        'Every story links back to the original reporting, so you can always read '
        'the full thing at the source.</p>'
        '<p>The goal is simple: one place to see what actually happened in '
        'Chesterfield this week, with the receipts.</p>'

        '<h2>What it is not</h2>'
        '<ul>'
        '<li><strong>Not affiliated with Chesterfield County government.</strong> '
        'This is an independent project.</li>'
        '<li><strong>Not a replacement for local outlets.</strong> We link back to '
        'them and encourage you to follow and support their original work.</li>'
        '<li><strong>Opinion is kept separate.</strong> Reader letters and editorials '
        'run clearly labeled as <a href="/letters.html">Opinion</a>, never mixed in '
        'with the news coverage.</li>'
        '</ul>'

        '<h2>Who is behind it</h2>'
        '<p>The Chesterfield Report is an independent project published by '
        '<a href="https://www.commonwealth-systems.com/" target="_blank" rel="noopener">'
        'Commonwealth Business Systems</a>, a Chesterfield, Virginia company that focuses on AI '
        'consulting for small businesses. Coverage decisions are made independently and are not influenced '
        'by its business, and the Report is not affiliated with or endorsed by Chesterfield '
        'County government.</p>'

        '<h2>Get involved</h2>'
        '<p>This is built for the community, with the community.</p>'
        '<ul>'
        '<li><strong>See something we should cover, or got wrong?</strong> '
        '<a href="/tip.html">Send a tip or correction.</a></li>'
        '<li><strong>Got a take on a local issue?</strong> '
        '<a href="/letters.html">Submit an opinion piece</a> (with your name or anonymously).</li>'
        '<li><strong>Just want to reach us?</strong> Email '
        '<a href="mailto:info@chesterfieldreport.com">info@chesterfieldreport.com</a>.</li>'
        '</ul>'
        '</div>')
    out = PUBLIC / "about.html"
    out.write_text(_shell(body), encoding="utf-8")
    return out


_SHOOSMITH_CSS = """<style>
.sho-wrap{max-width:760px;margin:0 auto;}
.sho-kicker{font:var(--fw-bold) var(--fs-2xs)/1 var(--font-mono);letter-spacing:var(--ls-wider);
  text-transform:uppercase;color:var(--breaking);margin-bottom:10px;}
.sho-dek{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);
  max-width:62ch;margin:.6rem 0 1.4rem;}
.sho-note{border-left:3px solid var(--accent);background:var(--surface-card);
  padding:.85rem 1.1rem;border-radius:var(--radius-xs);font-size:.92rem;
  color:var(--text-secondary);margin:1.4rem 0;}
.sho-facts{display:grid;grid-template-columns:repeat(2,1fr);gap:1px;background:var(--border-hair);
  border:1px solid var(--border-hair);border-radius:var(--radius-sm);overflow:hidden;margin:1.6rem 0;}
.sho-facts div{background:var(--surface-card);padding:.9rem 1.05rem;}
.sho-facts dt{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);
  text-transform:uppercase;color:var(--text-secondary);margin-bottom:6px;}
.sho-facts dd{margin:0;font-size:.95rem;color:var(--text-default);}
.sho-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:1.6rem 0;}
.sho-stat{background:var(--surface-card);border:1px solid var(--border-hair);
  border-radius:var(--radius-sm);padding:1rem 1.1rem;}
.sho-stat b{display:block;font:var(--fw-bold) var(--fs-2xl)/1 var(--font-display);color:var(--breaking);margin-bottom:6px;}
.sho-stat span{font-size:.85rem;color:var(--text-secondary);line-height:1.4;}
.sho-alleg{border:1px solid var(--border-strong);border-radius:var(--radius-sm);
  background:var(--surface-card);padding:1.1rem 1.2rem;margin:1.1rem 0;}
.sho-alleg .claim{font-weight:600;color:var(--text-default);}
.sho-alleg .who{display:block;font:var(--fs-3xs)/1.4 var(--font-mono);text-transform:uppercase;
  letter-spacing:var(--ls-wide);color:var(--civic);margin-top:8px;}
.sho-deny{border-left:3px solid var(--positive);padding:.7rem 1rem;margin:1.2rem 0;
  background:var(--surface-card);border-radius:var(--radius-xs);font-size:.92rem;color:var(--text-secondary);}
.sho-time{list-style:none;padding:0;margin:1.4rem 0;border-left:2px solid var(--border-strong);}
.sho-time li{position:relative;padding:0 0 1.1rem 1.3rem;}
.sho-time li::before{content:"";position:absolute;left:-5px;top:6px;width:8px;height:8px;
  border-radius:50%;background:var(--accent);}
.sho-time b{color:var(--text-default);font-family:var(--font-mono);font-size:.8rem;}
.sho-src{font-size:.85rem;color:var(--text-secondary);}
.sho-src li{margin-bottom:7px;}
@media(max-width:560px){.sho-facts{grid-template-columns:1fr;}}
</style>"""


def build_shoosmith() -> Path:
    """Standing investigative feature on the closed, bankrupt Shoosmith landfill.
    Facts lead; every misconduct claim is attributed to the party that made it
    and paired with the owners' denial. Public/official information only."""
    headline = ("Chesterfield's Shoosmith landfill is closed and bankrupt — "
                "and the cleanup bill could top $170 million")
    dek = ("The municipal landfill off Lewis Road stopped taking waste in 2022 and its "
           "owners filed for bankruptcy in 2025. Now regulators, the county and a state "
           "senator are fighting over who pays to contain millions of gallons of leachate.")

    facts = (
        '<dl class="sho-facts">'
        '<div><dt>What</dt><dd>A closed municipal solid-waste landfill (DEQ Permit No. 587), '
        'now in bankruptcy with a multi-million-dollar cleanup shortfall.</dd></div>'
        '<div><dt>Where</dt><dd>11800 Lewis Road, Chester (Dale District), Chesterfield County, VA.</dd></div>'
        '<div><dt>Who</dt><dd>Operated by Shoosmith Bros., Inc. under parent VWS Holdco, Inc. '
        '(a Texas-based investor group that bought the site in 2008 — not the founding family, '
        'and not Allied Waste or Republic Services).</dd></div>'
        '<div><dt>When</dt><dd>Stopped accepting waste Dec. 30, 2022; owners filed Chapter 11 in '
        'June 2025, converted to Chapter 7 liquidation that July.</dd></div>'
        '</dl>')

    story = (
        '<h2>What happened</h2>'
        '<p>The Shoosmith Sanitary Landfill operated off Lewis Road from 1976. The founding '
        'Shoosmith family sold it in June 2008 to a Texas-based investor group that ran it as '
        '<strong>Shoosmith Bros., Inc.</strong>, under a Delaware parent, <strong>VWS Holdco, Inc.</strong> '
        'In 2018, Chesterfield’s Board of Supervisors denied a proposed expansion (Cells 27–28), '
        'limiting how much longer the site could take waste. It stopped accepting waste on '
        '<strong>December 30, 2022</strong>.</p>'
        '<p>A closed landfill is not a finished one. It keeps generating <em>leachate</em> — '
        'liquid that percolates through buried waste — which has to be collected and treated so it '
        'doesn’t reach groundwater or streams. According to court filings and reporting, Shoosmith’s '
        'leachate handling broke down: Chesterfield’s utilities department documented elevated ammonia '
        'at the Proctors Creek treatment plant between 2019 and 2023, and the county suspended the '
        'company’s discharge permit in 2024.</p>'
        '<p>On <strong>June 1, 2025</strong>, VWS Holdco and Shoosmith Bros. filed for Chapter 11 '
        'bankruptcy; within about 60 days the case converted to <strong>Chapter 7 liquidation</strong>. '
        'That left a closed, leaking landfill, an estimated <strong>$183 million</strong> in debt, '
        'almost no assets, and a court-appointed trustee in charge of a cleanup the company can no '
        'longer pay for.</p>')

    numbers = (
        '<h2>By the numbers</h2>'
        '<div class="sho-stats">'
        '<div class="sho-stat"><b>~$19M</b><span>Closure/post-closure bonds set aside.</span></div>'
        '<div class="sho-stat"><b>$172M+</b><span>Trustee engineer’s estimate to safely close and '
        'maintain the site for 30 years.</span></div>'
        '<div class="sho-stat"><b>~50–65k</b><span>Gallons of leachate generated per day '
        '(figures vary by source; approximate).</span></div>'
        '<div class="sho-stat"><b>~$90k</b><span>Reported weekly cost to haul leachate off-site.</span></div>'
        '<div class="sho-stat"><b>$183M</b><span>Estimated prepetition debt of the bankrupt owners.</span></div>'
        '<div class="sho-stat"><b>Aug.</b><span>Month lawmakers warn funds to maintain the site '
        'could run out (2026).</span></div>'
        '</div>'
        '<p class="sho-src">Figures from the bankruptcy trustee’s filings and local reporting '
        '(WTVR, WRIC, VPM); ranges are labeled approximate where sources differ.</p>')

    alleged = (
        '<h2>What’s alleged — and by whom</h2>'
        '<p>The following are <strong>allegations</strong> made by named parties, several of them in '
        'active litigation. They are not proven facts. We pair them with the owners’ response.</p>'

        '<div class="sho-alleg"><span class="claim">Owners “pocketed millions of dollars” '
        'instead of investing in the site’s infrastructure and remediation.</span>'
        '<span class="who">Alleged in court records filed by attorneys for Virginia DEQ</span></div>'

        '<div class="sho-alleg"><span class="claim">The company bypassed parts of its pretreatment '
        'system and submitted falsified records to conceal illegal discharges.</span>'
        '<span class="who">Alleged by Chesterfield County</span></div>'

        '<div class="sho-alleg"><span class="claim">Insiders “may have criminal liability under '
        'Virginia law for abandoning the landfill without proper closure or adequate financial '
        'assurance.” <em>(As of mid-2026, no source confirms a criminal investigation has been '
        'opened.)</em></span>'
        '<span class="who">Argued in a filing by Chesterfield County’s lawyers</span></div>'

        '<div class="sho-alleg"><span class="claim">A potential “environmental catastrophe” '
        'driven by “years of extreme financial neglect.”</span>'
        '<span class="who">Chapter 7 trustee Lynn Tavenner</span></div>'

        '<div class="sho-alleg"><span class="claim">A “preventable disaster” that could cost '
        'taxpayers roughly $173 million, with concerns that ran “deeper than expected” after '
        'meeting the trustee.</span>'
        '<span class="who">Virginia state Sen. Glen Sturtevant, in a May 26, 2026 public letter</span></div>'

        '<div class="sho-deny"><strong>The owners deny wrongdoing.</strong> Their attorney, '
        'Christopher Jones, has said there was no breach of duty and “no proof or evidence of '
        'anything,” and the former owners dispute the allegations in court filings.</div>')

    leadership = (
        '<h2>Who ran Shoosmith — and who’s left to pay</h2>'
        '<p>According to the bankruptcy filings, two people are identified as running the '
        'companies: <strong>Fred G. Nichols</strong>, listed as <strong>president</strong> of both '
        'Shoosmith Bros., Inc. and its parent, VWS Holdco, Inc., and <strong>Paul Lawrence '
        '“Larry” McGee</strong>, listed as <strong>vice president</strong>. Nichols is named as the '
        'companies’ “debtor designee” in the Chapter 7 case. The record shows <strong>no public '
        'chief executive, chief financial officer or independent board of directors.</strong> The '
        'operating company sits beneath a chain of privately held holding companies (VWS Holdco and '
        'VWS Acquisitions, LLC); their other owners — Environmental Services Management of Virginia, '
        'LLC and Volunteer Enterprises, LLC — do not list public officers beyond Nichols and McGee, '
        'who is also reported as a part-owner of those upstream entities.</p>'

        '<h3>So can they pay for it?</h3>'
        '<p>On paper, the companies cannot. In their bankruptcy petitions the debtor entities '
        'reported roughly <strong>$0 to $100,000 in assets against about $183 million in debt</strong> — '
        'essentially empty shells. The only money set aside specifically for the landfill is about '
        '<strong>$19 million in closure bonds</strong>, against a cleanup estimated at more than '
        '<strong>$172 million</strong>.</p>'
        '<p>That leaves the question officials are actually fighting over: can anyone be made to pay '
        '<em>personally</em>? Virginia DEQ’s filings allege the owners “pocketed millions” instead of '
        'reinvesting — a claim the owners deny through their attorney. The Chapter 7 trustee, Lynn '
        'Tavenner, now controls the site and can pursue claims on creditors’ behalf, and the county '
        'has argued in a filing that the insiders could face liability for walking away. '
        '<strong>As of mid-2026 the public record shows no final answer</strong> — no confirmed '
        'recovery from the owners — and officials warn the shortfall could land on the '
        '<strong>state or taxpayers</strong>: the Commonwealth is weighing a takeover and roughly '
        '$50 million for an on-site treatment plant, while lawmakers warn the money to keep hauling '
        'leachate could run out as soon as August.</p>'
        '<p class="sho-src">Leadership titles and asset figures are drawn from the companies’ '
        'bankruptcy filings; the “pocketed millions” characterization is an allegation by Virginia '
        'DEQ’s attorneys, disputed by the owners. Individuals are named only in their roles as '
        'company officers.</p>')

    residents = (
        '<h2>What it means for residents</h2>'
        '<p>Leachate from the site has reached local waterways: a Virginia DEQ Notice of Violation '
        'dated <strong>February 9, 2026</strong> found a dark, leachate-like discharge into a channel '
        'leading to <strong>Swift Creek and Piney Branch</strong>, with outfall samples of suspended '
        'solids, ammonia and zinc above legal limits. Those creeks flow toward the Appomattox and '
        'James rivers.</p>'
        '<p>On the question of drinking water, accounts differ and we report both: DEQ documented the '
        'creek-outfall exceedances above, while Midlothian District Supervisor <strong>Mark Miller</strong> '
        'has said the county’s water sources are <em>not</em> contaminated. We have not found '
        'independent testing of downstream drinking-water intakes; that remains an open question.</p>'
        '<p>A structural issue runs underneath the story: in Virginia, <strong>DEQ alone</strong> has '
        'authority to inspect and enforce against landfills. The county says DEQ had just two inspectors '
        'for 80 facilities across the Piedmont region, and that when Chesterfield asked the state for '
        'joint enforcement authority in 2023, the Attorney General’s office declined. The state is now '
        'weighing whether to take over the site and build an on-site leachate treatment plant.</p>')

    timeline = (
        '<h2>Timeline</h2>'
        '<ul class="sho-time">'
        '<li><b>1976</b> — Landfill begins operating under the founding Shoosmith family.</li>'
        '<li><b>June 2008</b> — Family sells to a Texas-based investor group (Shoosmith Bros. / VWS Holdco).</li>'
        '<li><b>2018</b> — County denies the proposed Cells 27–28 expansion.</li>'
        '<li><b>2019–2023</b> — County records elevated ammonia at the Proctors Creek treatment plant.</li>'
        '<li><b>Dec. 30, 2022</b> — Landfill stops accepting waste.</li>'
        '<li><b>2023</b> — County’s request for joint enforcement authority is declined by the AG’s office.</li>'
        '<li><b>2024</b> — County suspends Shoosmith’s leachate discharge permit.</li>'
        '<li><b>June 1, 2025</b> — VWS Holdco &amp; Shoosmith Bros. file Chapter 11 (Case No. 25-10979).</li>'
        '<li><b>July 31, 2025</b> — Case converts to Chapter 7 liquidation; venue moves to E.D. Va.</li>'
        '<li><b>Dec. 2025</b> — Leachate-like discharge into Swift Creek / Piney Branch observed.</li>'
        '<li><b>Feb. 9, 2026</b> — DEQ issues a Notice of Violation (solids, ammonia, zinc exceedances).</li>'
        '<li><b>May 2026</b> — Sen. Sturtevant’s letter; Board of Supervisors discusses a possible state takeover.</li>'
        '</ul>')

    weigh_in = (
        '<h2>How to weigh in or report a concern</h2>'
        '<ul>'
        '<li><strong>Chesterfield County (Community Enhancement):</strong> '
        '<a href="mailto:SWcompliance@chesterfield.gov">SWcompliance@chesterfield.gov</a> · 804-748-1500.</li>'
        '<li><strong>Virginia DEQ</strong> holds enforcement authority over the site — report an '
        'environmental problem via <a href="https://www.deq.virginia.gov" rel="nofollow">deq.virginia.gov</a> '
        '(Piedmont Regional Office).</li>'
        '<li><strong>Board of Supervisors:</strong> the landfill has been on the agenda — see meeting '
        'agendas and video on the county’s <a href="/meetings.html">meetings page</a>.</li>'
        '<li><strong>Got information we should see?</strong> <a href="/tip.html">Send a confidential tip.</a></li>'
        '</ul>')

    sources = (
        '<h2>Sources</h2>'
        '<ul class="sho-src">'
        '<li>Virginia DEQ — Notice of Violation (Feb. 9, 2026), and the Solid Waste Permit No. 587 records '
        '(official enforcement and permit documents).</li>'
        '<li>Chesterfield County — official news release on the Shoosmith failures and the county’s '
        'enforcement-authority request.</li>'
        '<li>U.S. Bankruptcy Court filings — <em>In re VWS Holdco, Inc., et al.</em>, Case No. 25-10979 '
        '(D. Del. → E.D. Va.).</li>'
        '<li>Local reporting — WTVR CBS 6, WRIC ABC 8News, and VPM News (June 2026 coverage).</li>'
        '</ul>'
        '<p class="sho-src" style="margin-top:1rem">This is an evolving story. Spotted an error or have '
        'documents? <a href="/tip.html">Tell us.</a></p>')

    body = (
        _SHOOSMITH_CSS
        + '<div class="sho-wrap">'
        + '<div class="sho-kicker">Investigation · Shoosmith Landfill</div>'
        + '<h1 class="page-title">' + headline + '</h1>'
        + '<p class="sho-dek">' + dek + '</p>'
        + '<div class="sho-note">How we report this: the basic facts below — the closure, the '
        'bankruptcy, the DEQ violation, the dollar figures — are documented. Claims of misconduct are '
        'clearly labeled as allegations and attributed to the party that made them, alongside the owners’ '
        'denial. We name individuals only in their roles as company officers.</div>'
        + '<div class="prose-page">'
        + facts + story + numbers + alleged + leadership + residents + timeline + weigh_in + sources
        + '</div></div>')

    page = _shell(body)
    page = _inject_og(page, headline, dek, "https://chesterfieldreport.com/shoosmith.html")
    out = PUBLIC / "shoosmith.html"
    out.write_text(page, encoding="utf-8")
    return out


def build_tip() -> Path:
    import os
    key = os.environ.get("WEB3FORMS_KEY", "").strip()
    notice = "" if key else (
        '<div class="form-notice">⚠️ The tip form isn\'t active yet — add a '
        'free Web3Forms key (WEB3FORMS_KEY in scripts/.deploy.env, get one in 30s at '
        'web3forms.com) and rebuild.</div>')
    form = (
        '<form class="site-form" action="https://api.web3forms.com/submit" method="POST">'
        f'<input type="hidden" name="access_key" value="{key or "MISSING_WEB3FORMS_KEY"}">'
        '<input type="hidden" name="subject" value="New tip or correction for The Chesterfield Report">'
        '<input type="hidden" name="from_name" value="Chesterfield Report Tips">'
        '<input type="hidden" name="redirect" value="https://chesterfieldreport.com/tip.html?ok=1">'
        '<input type="checkbox" name="botcheck" class="hp" tabindex="-1" autocomplete="off">'
        '<label>Your tip or correction</label>'
        '<textarea name="Tip" rows="7" required placeholder="What should we look into? '
        'Include a location, date, or a link if you have one…"></textarea>'
        '<label>Email <span class="opt">(optional, only if you want a reply; never published)</span></label>'
        '<input type="email" name="email" autocomplete="email">'
        '<label>Name <span class="opt">(optional)</span></label>'
        '<input type="text" name="Name" autocomplete="name">'
        '<button type="submit" class="cr-btn cr-btn--primary" style="margin-top:1.3rem">Send tip</button>'
        '</form>')
    thanks_js = (
        "<script>if(location.search.indexOf('ok=1')>-1){"
        "var f=document.querySelector('.site-form');"
        "if(f){f.outerHTML='<div class=\\\"thanks\\\"><h2>Thank you. Your tip is in.</h2>'"
        "+'<p>We read every one. <a href=\\\"/\\\">← Back to The Chesterfield Report</a></p></div>';}}</script>")
    body = (
        _SITE_FORM_CSS
        + '<h1 class="page-title">Send a tip or correction</h1>'
        '<p class="lead">The Chesterfield Report is community-powered. See something we '
        'should cover, or something we got wrong? Tell us, confidentially.</p>'
        '<div class="tipwrap">' + notice + form +
        '<p class="tip-note" style="color:var(--text-faint);font-size:.85rem;margin-top:1rem">'
        'Tips are confidential. We never publish your name without permission. '
        'Prefer email? Reach us at <a href="mailto:info@chesterfieldreport.com">'
        'info@chesterfieldreport.com</a>.</p></div>'
        + thanks_js)
    out = PUBLIC / "tip.html"
    out.write_text(_shell(body), encoding="utf-8")
    return out


def build_subscribe() -> Path:
    """A dedicated newsletter signup page (email only). Submissions email the
    operator via Web3Forms, like the tip/letters forms."""
    # The Weekly Report signups are managed and sent through beehiiv. The embed
    # below renders beehiiv's hosted form (it handles confirmation + unsubscribe).
    embed = (
        '<div class="bh-embed">'
        '<script async src="https://subscribe-forms.beehiiv.com/v3/loader.js" '
        'data-beehiiv-form="40c9394d-8ca1-4272-ae7f-4e2762729620"></script>'
        '<noscript><a class="cr-btn cr-btn--primary" '
        'href="https://subscribe-forms.beehiiv.com/40c9394d-8ca1-4272-ae7f-4e2762729620" '
        'target="_blank" rel="noopener">Subscribe by email</a></noscript>'
        '</div>')
    body = (
        _SITE_FORM_CSS
        + '<h1 class="page-title">Subscribe</h1>'
        '<p class="lead">Get <strong>The Weekly Report</strong>, our free Chesterfield '
        'County roundup, in your inbox. Free to read, unsubscribe anytime.</p>'
        '<div class="tipwrap">' + embed +
        '<p class="tip-note" style="color:var(--text-faint);font-size:.85rem;margin-top:1rem">'
        'We only email you Chesterfield news and never share your address.</p></div>')
    out = PUBLIC / "subscribe.html"
    out.write_text(_shell(body), encoding="utf-8")
    return out


_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
/* Resolve theme before paint (no flash): saved choice -> device preference -> dark. */
(function() {{
  try {{
    var t = localStorage.getItem('cr-theme');
    if (t !== 'light' && t !== 'dark') {{ t = 'light'; }}   /* default everyone to light */
    document.documentElement.setAttribute('data-theme', t);
  }} catch (e) {{}}
}})();
</script>
<title>The Chesterfield Report: Hyperlocal News for Chesterfield County, Virginia</title>
<meta name="description" content="The Chesterfield Report delivers hyperlocal news for Chesterfield County, Virginia. AI-assembled from official county sources, local outlets, and public records, then human-reviewed, with links to the originals. Growth & development, schools, public safety, government, and community.">
<meta name="theme-color" content="#06141a">
<meta property="og:type" content="website">
<meta property="og:site_name" content="The Chesterfield Report">
<meta property="og:title" content="The Chesterfield Report">
<meta property="og:description" content="Hyperlocal news for Chesterfield County, Virginia. Growth, schools, public safety, government, and community. Free, no ads, with links back to the original sources.">
<meta property="og:url" content="https://chesterfieldreport.com/">
<meta property="og:image" content="https://chesterfieldreport.com/assets/og-default.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="The Chesterfield Report">
<meta name="twitter:description" content="Hyperlocal news for Chesterfield County, Virginia. Free, no ads, links to the original sources.">
<meta name="twitter:image" content="https://chesterfieldreport.com/assets/og-default.png">
<link rel="icon" href="/assets/favicon.svg">
<link rel="alternate" type="application/rss+xml" title="The Chesterfield Report" href="/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Chakra+Petch:wght@400;500;600;700&family=Public+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/report-ds.css">
</head>
<body>
<div class="cr-app">
<header class="cr-header masthead">
  <div class="cr-header__bar masthead-inner">
    <a class="brand cr-header__brand cr-wm" href="/" aria-label="The Chesterfield Report home">
      <img src="/assets/logo-mark.svg" alt="The Chesterfield Report heron emblem" class="cr-wm__mark">
      <span class="cr-wm__text">
        <span class="cr-wm__top">The</span>
        <span class="cr-wm__main">Chesterfield Report</span>
      </span>
    </a>
    <p class="tagline cr-header__tagline">Hyperlocal news for Chesterfield County, Virginia.</p>
    <button type="button" class="cr-themetoggle" id="cr-theme-toggle" aria-label="Switch theme" title="Light / dark theme">&#9728;</button>
  </div>
  <div class="cr-ticker" role="marquee" aria-label="Chesterfield County dispatch">
    <span class="cr-ticker__tag"><span class="cr-ticker__dot"></span>LIVE</span>
    <div class="cr-ticker__viewport"><div class="cr-ticker__track">
      <span class="cr-ticker__item"><span class="cr-ticker__sep">//</span>Midlothian &middot; Chester &middot; Bon Air &middot; Matoaca &middot; Moseley &middot; Ettrick &middot; Enon</span>
      <span class="cr-ticker__item"><span class="cr-ticker__sep">//</span>Chesterfield Courthouse &middot; Bermuda &middot; Clover Hill &middot; Dale &middot; Midlothian</span>
      <span class="cr-ticker__item"><span class="cr-ticker__sep">//</span>Growth &middot; Schools &middot; Public safety &middot; Government &middot; Community</span>
      <span class="cr-ticker__item"><span class="cr-ticker__sep">//</span>Midlothian &middot; Chester &middot; Bon Air &middot; Matoaca &middot; Moseley &middot; Ettrick &middot; Enon</span>
      <span class="cr-ticker__item"><span class="cr-ticker__sep">//</span>Chesterfield Courthouse &middot; Bermuda &middot; Clover Hill &middot; Dale &middot; Midlothian</span>
      <span class="cr-ticker__item"><span class="cr-ticker__sep">//</span>Growth &middot; Schools &middot; Public safety &middot; Government &middot; Community</span>
    </div></div>
  </div>
  <nav class="topnav cr-header__nav nav-desktop" aria-label="Main navigation">
    <a class="nav-x" href="/">Home</a>
    <div class="nav-g"><button class="nav-t" type="button">News <span class="nav-c">&#9662;</span></button><div class="nav-d"><a href="/topics/">Topics</a><a href="/digest.html">This Week</a><a href="/map.html">News map</a><a href="/virginia.html">Virginia &amp; Region</a></div></div>
    <a class="nav-x" href="/events.html">Events</a>
    <div class="nav-g"><button class="nav-t" type="button">Community <span class="nav-c">&#9662;</span></button><div class="nav-d"><a href="/neighborhoods.html">Neighborhoods</a><a href="/schools.html">Schools</a><a href="/apartments.html">Housing</a><a href="/affordable-housing.html">Affordable Housing</a><a href="/dining.html">Dining</a><a href="/things-to-do.html">Things to Do</a><a href="/farmers-markets.html">Farmers Markets</a><a href="/business.html">Business</a></div></div>
    <a class="nav-x" href="/schools.html">Schools</a>
    <a class="nav-x" href="/board.html">Supervisors</a>
    <a class="nav-x" href="/meetings.html">Meetings</a>
    <div class="nav-g"><button class="nav-t" type="button">Government <span class="nav-c">&#9662;</span></button><div class="nav-d"><a href="/elections.html">Elections</a><a href="/board.html">Board of Supervisors</a><a href="/school-board.html">School Board</a><a href="/meetings.html">Meetings</a><a href="/taxes.html">Taxes</a><a href="/development.html">Development &amp; Zoning</a></div></div>
    <div class="nav-g"><button class="nav-t" type="button">Investigations <span class="nav-c">&#9662;</span></button><div class="nav-d"><a href="/shoosmith.html">Shoosmith landfill</a></div></div>
    <a class="nav-x nav-cta" href="/subscribe.html">Subscribe</a>
  </nav>
  <nav class="topnav cr-header__nav nav-mobile" aria-label="Sections">
    <a href="/">Home</a><a href="/topics/">Topics</a><a href="/digest.html">This Week</a><a href="/map.html">News map</a><a href="/virginia.html">Virginia</a><a href="/elections.html">Elections</a><a href="/board.html">Supervisors</a><a href="/school-board.html">School Board</a><a href="/meetings.html">Meetings</a><a href="/taxes.html">Taxes</a><a href="/development.html">Development</a><a href="/dining.html">Dining</a><a href="/farmers-markets.html">Farmers Markets</a><a href="/events.html">Events</a><a href="/things-to-do.html">Things to Do</a><a href="/neighborhoods.html">Neighborhoods</a><a href="/schools.html">Schools</a><a href="/apartments.html">Housing</a><a href="/affordable-housing.html">Affordable</a><a href="/business.html">Business</a><a href="/shoosmith.html">Shoosmith</a>
  </nav>
  <div class="dateline">
    <span class="place">Chesterfield County &middot; Virginia</span>
    <span>Updated {generated}</span>
  </div>
  <a class="cr-subscribe-strip" href="/subscribe.html">Subscribe to free Chesterfield news &rarr;</a>
</header>
<main class="cr-main"><div class="cr-main__inner">
{body}
</div></main>
<footer>
  <div class="footer-inner">
    <div class="footer-brand"><img src="/assets/logo-mark.svg" alt="">The Chesterfield Report</div>
    <p>Independent, community-rooted coverage of Chesterfield County, Virginia:
       growth &amp; development, schools, public safety, government and community life.</p>
    <div class="footer-signup">
      <strong>Get The Weekly Report in your inbox.</strong>
      <p class="footer-signup-sub">A free weekly Chesterfield County roundup. Unsubscribe anytime.</p>
      <a class="footer-cta" href="/subscribe.html">Subscribe &rarr;</a>
    </div>
    <div class="footer-social">
      <a href="https://www.facebook.com/profile.php?id=61591128744204" target="_blank" rel="noopener" aria-label="Follow The Chesterfield Report on Facebook">
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="currentColor"><path d="M24 12.07C24 5.4 18.63 0 12 0S0 5.4 0 12.07c0 6.03 4.39 11.03 10.13 11.93v-8.44H7.08v-3.49h3.05V9.41c0-3.02 1.79-4.69 4.53-4.69 1.31 0 2.68.24 2.68.24v2.97h-1.51c-1.49 0-1.96.93-1.96 1.89v2.25h3.33l-.53 3.49h-2.8v8.44C19.61 23.1 24 18.1 24 12.07z"/></svg>
        Follow us on Facebook
      </a>
    </div>
    <nav class="footer-nav" aria-label="All sections">
      <div class="footer-col">
        <h3>News</h3>
        <a href="/">Home</a>
        <a href="/topics/">Topics</a>
        <a href="/digest.html">This Week</a>
        <a href="/map.html">News map</a>
        <a href="/virginia.html">Virginia &amp; Region</a>
      </div>
      <div class="footer-col">
        <h3>Community</h3>
        <a href="/events.html">Events</a>
        <a href="/things-to-do.html">Things to Do</a>
        <a href="/farmers-markets.html">Farmers Markets</a>
        <a href="/neighborhoods.html">Neighborhoods</a>
        <a href="/schools.html">Schools</a>
        <a href="/apartments.html">Apartments</a>
        <a href="/affordable-housing.html">Affordable Housing</a>
        <a href="/dining.html">Dining</a>
        <a href="/business.html">Business</a>
      </div>
      <div class="footer-col">
        <h3>Government</h3>
        <a href="/elections.html">Elections</a>
        <a href="/board.html">Board of Supervisors</a>
        <a href="/school-board.html">School Board</a>
        <a href="/meetings.html">Meetings</a>
        <a href="/taxes.html">Taxes</a>
        <a href="/development.html">Development &amp; Zoning</a>
      </div>
      <div class="footer-col">
        <h3>More</h3>
        <a href="/shoosmith.html">Shoosmith investigation</a>
        <a href="/letters.html">Opinion</a>
        <a href="/tip.html">Send a tip</a>
        <a href="/subscribe.html">Subscribe</a>
        <a href="/newsletter/">Newsletter</a>
        <a href="/about.html">About</a>
        <a href="/changelog.html">What's New</a>
        <a href="mailto:info@chesterfieldreport.com">Contact</a>
        <a href="/feed.xml">RSS</a>
      </div>
    </nav>
    <p>Stories are aggregated and summarized with links back to the original reporting.
       Please follow the <strong>[source]</strong> and &ldquo;Read the source&rdquo; links to support
       the outlets and agencies that do the original work.</p>
    <div class="footer-meta">
      {count} stories &middot; Updated {generated} &middot;
      <span class="footer-domain">chesterfieldreport.com</span>
    </div>
  </div>
</footer>
</div>
<script>
(function() {{
  var bar = document.querySelector('.filterbar');
  if (!bar) return;
  var cards = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var buttons = Array.prototype.slice.call(bar.querySelectorAll('.filter'));
  bar.addEventListener('click', function(e) {{
    var btn = e.target.closest('.filter');
    if (!btn) return;
    var filter = btn.getAttribute('data-filter');
    buttons.forEach(function(b) {{
      var on = b === btn;
      b.classList.toggle('is-active', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    }});
    cards.forEach(function(card) {{
      var cats = (card.getAttribute('data-focus') || '').split(/\s+/);
      card.hidden = !(filter === 'all' || cats.indexOf(filter) !== -1);
    }});
  }});
}})();
</script>
<script>
/* Theme toggle: flip light/dark, remember the choice, keep following the
   device while no explicit choice is stored. */
(function() {{
  var btn = document.getElementById('cr-theme-toggle');
  var root = document.documentElement;
  var meta = document.querySelector('meta[name=theme-color]');
  function cur() {{ return root.getAttribute('data-theme') === 'light' ? 'light' : 'dark'; }}
  function paint() {{
    var t = cur();
    if (meta) meta.setAttribute('content', t === 'light' ? '#f6f8f9' : '#06141a');
    if (btn) {{
      btn.innerHTML = t === 'light' ? '&#9790;' : '&#9728;';   /* moon when light, sun when dark */
      btn.setAttribute('aria-label', t === 'light' ? 'Switch to dark theme' : 'Switch to light theme');
    }}
  }}
  paint();
  if (btn) btn.addEventListener('click', function() {{
    var t = cur() === 'light' ? 'dark' : 'light';
    root.setAttribute('data-theme', t);
    try {{ localStorage.setItem('cr-theme', t); }} catch (e) {{}}
    paint();
  }});
}})();
</script>
<script>
/* Live ticker: Chesterfield active dispatch (public county feeds for Police,
   Fire/EMS, and Traffic), refreshed every 5 minutes, client-side. Each item
   links to its county source page. Falls back to the static ticker on error. */
(function() {{
  var BASE = 'https://api.chesterfield.gov/api/';
  var FEEDS = [
    {{ label:'PD',      path:'Police/V1.1/Calls/CallsForService', key:'9f42e1e5-200a-4540-86de-74b8c2a11670', src:'https://www.chesterfield.gov/3999/Active-Police-Calls' }},
    {{ label:'FIRE',    path:'Fire/V1.0/Calls/CallsForService',   key:'609a086d-2012-4229-9f06-294c893d34e1', src:'https://www.chesterfield.gov/3913/Active-FireEMS-Calls' }},
    {{ label:'TRAFFIC', path:'Police/V1.0/Traffic',               key:'5d1385e8-cd37-4906-8b64-3bf8e8527267', src:'https://www.chesterfield.gov/1454/Active-Traffic-Incidents' }}
  ];
  var track = document.querySelector('.cr-ticker__track');
  var tag = document.querySelector('.cr-ticker__tag');
  if (!track) return;
  function esc(s) {{
    return String(s).replace(/[&<>]/g, function(c) {{ return {{ '&':'&amp;','<':'&lt;','>':'&gt;' }}[c]; }});
  }}
  function listOf(d) {{ return Array.isArray(d) ? d : ((d && (d.data || d.calls || d.value)) || []); }}
  function clockTime(s) {{
    if (!s) return '';
    var p = String(s).split(' ');            // "6/13/2026 9:12:21 PM"
    if (p.length < 2) return '';
    var hm = p[1].split(':');
    return hm[0] + ':' + (hm[1] || '00') + (p[2] ? ' ' + p[2] : '');   // "9:12 PM"
  }}
  function fetchFeed(f) {{
    return fetch(BASE + f.path, {{ headers: {{ 'X-ApiKey': f.key, 'Accept':'application/json' }} }})
      .then(function(r) {{ return r.ok ? r.json() : null; }})
      .then(function(d) {{
        return listOf(d).filter(function(c) {{ return c && c.type; }})
          .map(function(c) {{ return {{ label:f.label, src:f.src, type:(c.type||'').trim(),
            loc:(c.location||'').trim(), status:(c.currentStatus||c.status||'').trim(),
            time:clockTime(c.callReceived) }}; }});
      }})
      .catch(function() {{ return []; }});
  }}
  function render(calls) {{
    if (!calls.length) return;
    var items = calls.map(function(c) {{
      var txt = c.label + ' · ' + c.type + (c.loc ? ' · ' + c.loc : '') + (c.status ? ' · ' + c.status : '') + (c.time ? ' · ' + c.time : '');
      return '<a class="cr-ticker__item" href="' + esc(c.src) + '" target="_blank" rel="noopener"><span class="cr-ticker__sep">//</span>' + esc(txt) + '</a>';
    }});
    track.innerHTML = items.join('') + items.join('');
    track.style.animationDuration = Math.max(28, calls.length * 5) + 's';
    if (tag) tag.innerHTML = '<span class="cr-ticker__dot"></span>ACTIVE CALLS';
  }}
  function load() {{
    Promise.all(FEEDS.map(fetchFeed)).then(function(results) {{
      render([].concat.apply([], results));
    }});
  }}
  load();
  setInterval(load, 300000);
}})();
</script>
<script>window.va=window.va||function(){{(window.vaq=window.vaq||[]).push(arguments);}};</script>
<script defer src="/_vercel/insights/script.js"></script>
</body></html>
"""


# Cache-bust the stylesheet: append ?v=<content-hash> so browsers always fetch
# the latest CSS after a deploy (the filename is otherwise stable and cached
# hard). Computed once at import from the current report-ds.css contents.
def _css_version() -> str:
    try:
        import hashlib
        data = (PUBLIC / "assets" / "report-ds.css").read_bytes()
        return hashlib.md5(data).hexdigest()[:10]
    except Exception:
        return "1"


_TEMPLATE = _TEMPLATE.replace(
    '/assets/report-ds.css"',
    '/assets/report-ds.css?v=' + _css_version() + '"', 1)

# Bake the Web3Forms key into the footer newsletter signup at build time (the
# cron sources scripts/.deploy.env before building, so it's in os.environ).
_TEMPLATE = _TEMPLATE.replace(
    '__W3FKEY__', os.environ.get("WEB3FORMS_KEY", "").strip() or "MISSING_WEB3FORMS_KEY")
